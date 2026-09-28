from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas, services
from app.deps import require_admin_or_trainer, require_admin

router = APIRouter(prefix="/api/admin/departments", tags=["departments"])


def _serialize(db: Session, dept: models.Department) -> dict:
    officials = db.query(models.Employee).filter(models.Employee.department_id == dept.id).count()
    avg_comp = services.department_avg_competency(db, dept.id)
    training_completion = services.department_training_completion(db, dept.id)
    status = "Active" if officials > 0 else "No Staff"
    return {
        "id": dept.id, "name": dept.name, "description": dept.description,
        "officials": officials, "averageCompetency": avg_comp,
        "trainingCompletion": training_completion, "status": status,
    }


@router.get("")
def list_departments(search: str = "", db: Session = Depends(get_db), _user=Depends(require_admin_or_trainer)):
    q = db.query(models.Department)
    if search:
        q = q.filter(models.Department.name.ilike(f"%{search}%"))
    depts = q.order_by(models.Department.name).all()
    return [_serialize(db, d) for d in depts]


@router.post("")
def create_department(payload: schemas.DepartmentIn, db: Session = Depends(get_db),
                       _user=Depends(require_admin)):
    if db.query(models.Department).filter(models.Department.name == payload.name).first():
        raise HTTPException(status_code=400, detail="Department already exists")
    dept = models.Department(name=payload.name, description=payload.description)
    db.add(dept)
    db.commit()
    db.refresh(dept)
    return _serialize(db, dept)


@router.put("/{dept_id}")
def update_department(dept_id: int, payload: schemas.DepartmentIn, db: Session = Depends(get_db),
                       _user=Depends(require_admin)):
    dept = db.query(models.Department).filter(models.Department.id == dept_id).first()
    if not dept:
        raise HTTPException(status_code=404, detail="Department not found")
    dept.name = payload.name
    dept.description = payload.description
    db.commit()
    db.refresh(dept)
    return _serialize(db, dept)


@router.delete("/{dept_id}")
def delete_department(dept_id: int, db: Session = Depends(get_db), _user=Depends(require_admin)):
    dept = db.query(models.Department).filter(models.Department.id == dept_id).first()
    if not dept:
        raise HTTPException(status_code=404, detail="Department not found")
    staff_count = db.query(models.Employee).filter(models.Employee.department_id == dept_id).count()
    if staff_count:
        raise HTTPException(status_code=400, detail="Cannot delete a department with assigned employees")
    db.delete(dept)
    db.commit()
    return {"status": "deleted"}
