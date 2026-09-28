from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.database import get_db
from app import models, schemas, services
from app.deps import require_admin_or_trainer, require_admin
from app.security import hash_password

router = APIRouter(prefix="/api/admin/employees", tags=["employees"])


def _serialize(db: Session, emp: models.Employee) -> dict:
    return {
        "id": emp.id,
        "employeeId": emp.employee_code,
        "name": emp.name,
        "email": emp.email,
        "department": emp.department.name if emp.department else None,
        "departmentId": emp.department_id,
        "designation": emp.designation,
        "experience": emp.experience_years,
        "phone": emp.phone,
        "notes": emp.notes,
        "competency": services.employee_avg_competency_pct(db, emp.id),
        "trainingStatus": emp.training_status.value if emp.training_status else "Pending",
    }


@router.get("")
def list_employees(
    search: str = "", department: str = "", training_status: str = "",
    page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db), _user=Depends(require_admin_or_trainer),
):
    q = db.query(models.Employee)
    if search:
        like = f"%{search}%"
        q = q.filter(or_(models.Employee.name.ilike(like), models.Employee.employee_code.ilike(like),
                          models.Employee.email.ilike(like)))
    if department:
        q = q.join(models.Department).filter(models.Department.name == department)
    if training_status:
        q = q.filter(models.Employee.training_status == training_status)
    total = q.count()
    items = q.order_by(models.Employee.id).offset((page - 1) * page_size).limit(page_size).all()
    return {"total": total, "page": page, "pageSize": page_size,
            "items": [_serialize(db, e) for e in items]}


@router.get("/{emp_id}")
def get_employee(emp_id: int, db: Session = Depends(get_db), _user=Depends(require_admin_or_trainer)):
    emp = db.query(models.Employee).filter(models.Employee.id == emp_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    data = _serialize(db, emp)
    data["skills"] = [
        {"skillId": s.skill_id, "name": s.skill.name, "category": s.skill.category,
         "currentLevel": s.current_level, "requiredLevel": s.required_level}
        for s in emp.skills
    ]
    return data


@router.post("")
def create_employee(payload: schemas.EmployeeIn, db: Session = Depends(get_db),
                     _user=Depends(require_admin_or_trainer)):
    code = payload.employee_code or f"EMP{1000 + db.query(models.Employee).count() + 1}"
    if db.query(models.Employee).filter(models.Employee.employee_code == code).first():
        raise HTTPException(status_code=400, detail="Employee code already exists")

    dept = services.get_or_create_department(db, payload.department) if payload.department else None

    user_id = None
    if payload.email and payload.password:
        if db.query(models.User).filter(models.User.email == payload.email).first():
            raise HTTPException(status_code=400, detail="Email already registered as a user")
        user = models.User(email=payload.email, full_name=payload.name,
                            hashed_password=hash_password(payload.password), role=models.RoleEnum.employee)
        db.add(user)
        db.flush()
        user_id = user.id

    emp = models.Employee(
        user_id=user_id, employee_code=code, name=payload.name, email=payload.email,
        department_id=dept.id if dept else None, designation=payload.designation,
        experience_years=payload.experience_years or 0, phone=payload.phone, notes=payload.notes,
    )
    db.add(emp)
    db.commit()
    db.refresh(emp)
    services.create_notification(db, f"New employee added: {emp.name}", type_="System")
    return _serialize(db, emp)


@router.put("/{emp_id}")
def update_employee(emp_id: int, payload: schemas.EmployeeIn, db: Session = Depends(get_db),
                     _user=Depends(require_admin_or_trainer)):
    emp = db.query(models.Employee).filter(models.Employee.id == emp_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    if payload.department:
        dept = services.get_or_create_department(db, payload.department)
        emp.department_id = dept.id
    emp.name = payload.name
    emp.email = payload.email or emp.email
    emp.designation = payload.designation or emp.designation
    emp.experience_years = payload.experience_years if payload.experience_years is not None else emp.experience_years
    emp.phone = payload.phone or emp.phone
    emp.notes = payload.notes if payload.notes is not None else emp.notes
    db.commit()
    db.refresh(emp)
    return _serialize(db, emp)


@router.delete("/{emp_id}")
def delete_employee(emp_id: int, db: Session = Depends(get_db), _user=Depends(require_admin)):
    emp = db.query(models.Employee).filter(models.Employee.id == emp_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")

    # Manually clear dependent rows that don't cascade automatically via the
    # ORM relationship graph, so the delete never fails on a FK constraint.
    db.query(models.SkillGapSnapshot).filter(models.SkillGapSnapshot.employee_id == emp_id).delete()
    db.query(models.DiagnosticAttempt).filter(models.DiagnosticAttempt.employee_id == emp_id).delete()
    db.query(models.QuizAttempt).filter(models.QuizAttempt.employee_id == emp_id).delete()
    db.query(models.Recommendation).filter(models.Recommendation.employee_id == emp_id).delete()
    db.query(models.LearningPathAssignment).filter(models.LearningPathAssignment.employee_id == emp_id).delete()

    if emp.user_id:
        user = db.query(models.User).filter(models.User.id == emp.user_id).first()
        if user:
            db.delete(user)

    db.delete(emp)
    db.commit()
    return {"status": "deleted"}


@router.post("/{emp_id}/assess")
def assess_employee(emp_id: int, db: Session = Depends(get_db), _user=Depends(require_admin_or_trainer)):
    emp = db.query(models.Employee).filter(models.Employee.id == emp_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")

    # Ensure the employee has an EmployeeSkill row for every framework requirement
    # relevant to their designation (falls back to all skills if no role mapping exists).
    reqs = db.query(models.RoleCompetencyRequirement).filter(
        models.RoleCompetencyRequirement.job_role == (emp.designation or "")
    ).all()
    if not reqs:
        skills = db.query(models.Skill).all()
        for sk in skills:
            existing = db.query(models.EmployeeSkill).filter(
                models.EmployeeSkill.employee_id == emp.id, models.EmployeeSkill.skill_id == sk.id
            ).first()
            if not existing:
                db.add(models.EmployeeSkill(employee_id=emp.id, skill_id=sk.id, current_level=0, required_level=2))
    else:
        for req in reqs:
            existing = db.query(models.EmployeeSkill).filter(
                models.EmployeeSkill.employee_id == emp.id, models.EmployeeSkill.skill_id == req.skill_id
            ).first()
            if existing:
                existing.required_level = req.required_level
            else:
                db.add(models.EmployeeSkill(employee_id=emp.id, skill_id=req.skill_id,
                                             current_level=0, required_level=req.required_level))
    db.commit()

    snapshots = services.run_skill_gap_analysis(db, employee_id=emp.id)
    if emp.training_status == models.TrainingStatusEnum.pending:
        emp.training_status = models.TrainingStatusEnum.in_progress
        db.commit()

    return {
        "employeeId": emp.id,
        "gapsIdentified": len([s for s in snapshots if s.gap > 0]),
        "competency": services.employee_avg_competency_pct(db, emp.id),
        "snapshots": [
            {"skill": s.skill.name, "currentLevel": s.current_level, "requiredLevel": s.required_level,
             "gap": s.gap, "priority": s.priority.value}
            for s in snapshots
        ],
    }
