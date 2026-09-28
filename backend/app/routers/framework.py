from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas, services
from app.deps import require_admin_or_trainer, require_admin

router = APIRouter(prefix="/api/admin/framework", tags=["framework"])


def _serialize(row: models.RoleCompetencyRequirement) -> dict:
    return {
        "id": row.id,
        "competency": row.skill.name if row.skill else None,
        "category": row.skill.category if row.skill else None,
        "requiredLevel": row.required_level,
        "jobRoles": row.job_role,
        "status": row.status,
    }


@router.get("")
def list_framework(search: str = "", db: Session = Depends(get_db), _user=Depends(require_admin_or_trainer)):
    q = db.query(models.RoleCompetencyRequirement).join(models.Skill)
    if search:
        like = f"%{search}%"
        q = q.filter(models.Skill.name.ilike(like))
    rows = q.order_by(models.RoleCompetencyRequirement.id.desc()).all()
    return [_serialize(r) for r in rows]


@router.post("")
def create_framework(payload: schemas.FrameworkIn, db: Session = Depends(get_db), _user=Depends(require_admin)):
    skill = services.get_or_create_skill(db, payload.name, payload.category)
    row = models.RoleCompetencyRequirement(
        job_role=payload.job_roles, skill_id=skill.id, required_level=payload.required_level,
        status=payload.status,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return _serialize(row)


@router.put("/{row_id}")
def update_framework(row_id: int, payload: schemas.FrameworkIn, db: Session = Depends(get_db),
                      _user=Depends(require_admin)):
    row = db.query(models.RoleCompetencyRequirement).filter(models.RoleCompetencyRequirement.id == row_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Framework entry not found")
    skill = services.get_or_create_skill(db, payload.name, payload.category)
    row.skill_id = skill.id
    row.required_level = payload.required_level
    row.job_role = payload.job_roles
    row.status = payload.status
    db.commit()
    db.refresh(row)
    return _serialize(row)


@router.delete("/{row_id}")
def delete_framework(row_id: int, db: Session = Depends(get_db), _user=Depends(require_admin)):
    row = db.query(models.RoleCompetencyRequirement).filter(models.RoleCompetencyRequirement.id == row_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Framework entry not found")
    db.delete(row)
    db.commit()
    return {"status": "deleted"}
