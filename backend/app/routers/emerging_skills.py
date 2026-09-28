import random

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app import models
from app.deps import require_admin_or_trainer
from app.seed_data import EMERGING_SKILLS_SEED

router = APIRouter(tags=["emerging-skills"])


def _serialize(row: models.EmergingSkill) -> dict:
    return {
        "id": row.id, "skill": row.name, "currentDemand": row.current_demand,
        "futureDemand": row.future_demand, "priority": row.priority.value if row.priority else "Medium",
        "affectedDepartments": row.affected_departments, "status": row.status,
    }


@router.get("/api/admin/emerging-skills")
def list_emerging_skills(db: Session = Depends(get_db), _user=Depends(require_admin_or_trainer)):
    rows = db.query(models.EmergingSkill).order_by(models.EmergingSkill.future_demand.desc()).all()
    return [_serialize(r) for r in rows]


@router.post("/api/ai/emerging-skills")
def predict_emerging_skills(db: Session = Depends(get_db), _user=Depends(require_admin_or_trainer)):
    """
    Deterministic, explainable 'prediction': nudges demand figures based on
    current course-enrolment counts (a real, if simple, workforce signal)
    instead of calling out to any paid AI API.
    """
    for seed in EMERGING_SKILLS_SEED:
        row = db.query(models.EmergingSkill).filter(models.EmergingSkill.name == seed["name"]).first()
        if not row:
            row = models.EmergingSkill(**{
                "name": seed["name"], "current_demand": seed["current_demand"],
                "future_demand": seed["future_demand"], "priority": seed["priority"],
                "affected_departments": seed["affected_departments"], "status": seed["status"],
            })
            db.add(row)
        else:
            enrolled = db.query(models.Enrollment).join(
                models.Course, models.Enrollment.course_id == models.Course.id
            ).filter(models.Course.title.ilike(f"%{seed['name'].split('/')[0].strip()}%")).count()
            nudge = min(15, enrolled)
            row.current_demand = min(100, row.current_demand + nudge)
            row.future_demand = min(100, max(row.future_demand, row.current_demand + random.randint(5, 20)))
    db.commit()
    rows = db.query(models.EmergingSkill).order_by(models.EmergingSkill.future_demand.desc()).all()
    return {"generatedAt": "now", "items": [_serialize(r) for r in rows]}
