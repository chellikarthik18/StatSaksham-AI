from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.database import get_db
from app import models, services
from app.deps import require_admin_or_trainer

router = APIRouter(prefix="/api/admin/skill-gaps", tags=["skill-gaps"])


def _serialize(row: models.SkillGapSnapshot) -> dict:
    return {
        "id": row.id,
        "employee": row.employee.name if row.employee else None,
        "department": row.employee.department.name if row.employee and row.employee.department else None,
        "skill": row.skill.name if row.skill else None,
        "current": services.level_pct(row.current_level),
        "required": services.level_pct(row.required_level),
        "gap": row.gap,
        "priority": row.priority.value if row.priority else "Medium",
    }


@router.get("")
def list_skill_gaps(search: str = "", priority: str = "", department: str = "",
                     db: Session = Depends(get_db), _user=Depends(require_admin_or_trainer)):
    q = (
        db.query(models.SkillGapSnapshot)
        .join(models.Employee, models.SkillGapSnapshot.employee_id == models.Employee.id)
        .join(models.Skill, models.SkillGapSnapshot.skill_id == models.Skill.id)
        .filter(models.SkillGapSnapshot.gap > 0)
    )
    if search:
        like = f"%{search}%"
        q = q.filter(or_(models.Employee.name.ilike(like), models.Skill.name.ilike(like)))
    if priority:
        q = q.filter(models.SkillGapSnapshot.priority == priority)
    if department:
        q = q.join(models.Department).filter(models.Department.name == department)
    rows = q.order_by(models.SkillGapSnapshot.gap.desc()).limit(1000).all()
    return [_serialize(r) for r in rows]


@router.post("/run")
def run_analysis(db: Session = Depends(get_db), _user=Depends(require_admin_or_trainer)):
    snapshots = services.run_skill_gap_analysis(db)
    services.create_notification(db, "Skill-gap analysis completed",
                                  f"{len([s for s in snapshots if s.gap > 0])} gaps identified across the workforce.",
                                  type_="System")
    return {"total": len(snapshots), "gaps": len([s for s in snapshots if s.gap > 0]),
            "items": [_serialize(s) for s in snapshots if s.gap > 0]}
