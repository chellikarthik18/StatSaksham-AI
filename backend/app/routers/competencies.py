from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.database import get_db
from app import models, schemas, services
from app.deps import require_admin_or_trainer

router = APIRouter(prefix="/api/admin/competencies", tags=["competencies"])


def _serialize(row: models.EmployeeSkill) -> dict:
    gap = max(0, (row.required_level or 0) - (row.current_level or 0))
    return {
        "id": row.id,
        "employeeId": row.employee_id,
        "employee": row.employee.name if row.employee else None,
        "category": row.skill.category if row.skill else None,
        "skill": row.skill.name if row.skill else None,
        "currentLevel": row.current_level,
        "requiredLevel": row.required_level,
        "currentPct": services.level_pct(row.current_level),
        "requiredPct": services.level_pct(row.required_level),
        "gap": gap,
    }


@router.get("")
def list_competencies(search: str = "", category: str = "", db: Session = Depends(get_db),
                       _user=Depends(require_admin_or_trainer)):
    q = db.query(models.EmployeeSkill).join(models.Employee).join(models.Skill)
    if search:
        like = f"%{search}%"
        q = q.filter(or_(models.Employee.name.ilike(like), models.Skill.name.ilike(like)))
    if category:
        q = q.filter(models.Skill.category == category)
    rows = q.order_by(models.EmployeeSkill.id.desc()).limit(1000).all()
    return [_serialize(r) for r in rows]


@router.post("")
def upsert_competency(payload: schemas.CompetencyIn, db: Session = Depends(get_db),
                       _user=Depends(require_admin_or_trainer)):
    employee = None
    if payload.employee_id:
        employee = db.query(models.Employee).filter(models.Employee.id == payload.employee_id).first()
    elif payload.employee_name:
        employee = db.query(models.Employee).filter(models.Employee.name == payload.employee_name).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found. Provide employee_id or an existing employee_name.")

    skill = services.get_or_create_skill(db, payload.skill_name, payload.category)
    row = db.query(models.EmployeeSkill).filter(
        models.EmployeeSkill.employee_id == employee.id, models.EmployeeSkill.skill_id == skill.id
    ).first()
    if row:
        row.current_level = payload.current_level
        row.required_level = payload.required_level
    else:
        row = models.EmployeeSkill(employee_id=employee.id, skill_id=skill.id,
                                    current_level=payload.current_level, required_level=payload.required_level)
        db.add(row)
    db.commit()
    db.refresh(row)
    return _serialize(row)


@router.put("/{row_id}")
def update_competency(row_id: int, payload: schemas.CompetencyIn, db: Session = Depends(get_db),
                       _user=Depends(require_admin_or_trainer)):
    row = db.query(models.EmployeeSkill).filter(models.EmployeeSkill.id == row_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Competency record not found")
    row.current_level = payload.current_level
    row.required_level = payload.required_level
    db.commit()
    db.refresh(row)
    return _serialize(row)


@router.delete("/{row_id}")
def delete_competency(row_id: int, db: Session = Depends(get_db), _user=Depends(require_admin_or_trainer)):
    row = db.query(models.EmployeeSkill).filter(models.EmployeeSkill.id == row_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Competency record not found")
    db.delete(row)
    db.commit()
    return {"status": "deleted"}
