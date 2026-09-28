from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas, services
from app.deps import require_admin_or_trainer

router = APIRouter(tags=["learning-paths"])


def _serialize(lp: models.LearningPath) -> dict:
    assignments = lp.assignments
    avg_completion = round(sum(a.progress for a in assignments) / len(assignments), 1) if assignments else 0
    status = lp.status
    if assignments:
        status = "Completed" if all(a.progress >= 100 for a in assignments) else "Assigned"
    return {
        "id": lp.id, "title": lp.title, "description": lp.description,
        "modules": len(lp.items), "assignedEmployees": len(assignments),
        "completion": avg_completion, "status": status, "generatedByAi": lp.generated_by_ai,
        "items": [
            {"type": it.item_type, "id": it.course_id or it.program_id,
             "title": (it.course.title if it.course else (it.program.title if it.program else None))}
            for it in lp.items
        ],
    }


@router.get("/api/admin/learning-paths")
def list_learning_paths(search: str = "", db: Session = Depends(get_db), _user=Depends(require_admin_or_trainer)):
    q = db.query(models.LearningPath)
    if search:
        q = q.filter(models.LearningPath.title.ilike(f"%{search}%"))
    rows = q.order_by(models.LearningPath.id.desc()).all()
    return [_serialize(r) for r in rows]


@router.post("/api/admin/learning-paths")
def create_learning_path(payload: schemas.LearningPathIn, db: Session = Depends(get_db),
                          _user=Depends(require_admin_or_trainer)):
    lp = models.LearningPath(title=payload.title, description=payload.description, status="Draft")
    db.add(lp)
    db.flush()
    for i, item in enumerate(payload.items or []):
        if item.item_type == "course":
            db.add(models.LearningPathItem(learning_path_id=lp.id, item_type="course", course_id=item.id, sequence=i))
        else:
            db.add(models.LearningPathItem(learning_path_id=lp.id, item_type="program", program_id=item.id, sequence=i))
    for emp_id in payload.assign_employee_ids or []:
        db.add(models.LearningPathAssignment(learning_path_id=lp.id, employee_id=emp_id))
    db.commit()
    db.refresh(lp)
    return _serialize(lp)


@router.put("/api/admin/learning-paths/{lp_id}")
def update_learning_path(lp_id: int, payload: schemas.LearningPathIn, db: Session = Depends(get_db),
                          _user=Depends(require_admin_or_trainer)):
    lp = db.query(models.LearningPath).filter(models.LearningPath.id == lp_id).first()
    if not lp:
        raise HTTPException(status_code=404, detail="Learning path not found")
    lp.title = payload.title
    lp.description = payload.description
    if payload.items is not None:
        db.query(models.LearningPathItem).filter(models.LearningPathItem.learning_path_id == lp_id).delete()
        for i, item in enumerate(payload.items):
            if item.item_type == "course":
                db.add(models.LearningPathItem(learning_path_id=lp.id, item_type="course", course_id=item.id, sequence=i))
            else:
                db.add(models.LearningPathItem(learning_path_id=lp.id, item_type="program", program_id=item.id, sequence=i))
    for emp_id in payload.assign_employee_ids or []:
        if not db.query(models.LearningPathAssignment).filter(
            models.LearningPathAssignment.learning_path_id == lp_id,
            models.LearningPathAssignment.employee_id == emp_id,
        ).first():
            db.add(models.LearningPathAssignment(learning_path_id=lp.id, employee_id=emp_id))
    db.commit()
    db.refresh(lp)
    return _serialize(lp)


@router.delete("/api/admin/learning-paths/{lp_id}")
def delete_learning_path(lp_id: int, db: Session = Depends(get_db), _user=Depends(require_admin_or_trainer)):
    lp = db.query(models.LearningPath).filter(models.LearningPath.id == lp_id).first()
    if not lp:
        raise HTTPException(status_code=404, detail="Learning path not found")
    db.delete(lp)
    db.commit()
    return {"status": "deleted"}


@router.post("/api/ai/learning-path")
def ai_generate_learning_path(employee_id: Optional[int] = None, db: Session = Depends(get_db),
                               _user=Depends(require_admin_or_trainer)):
    """
    Deterministic recommendation: picks courses/programs that map to the
    employee's (or the workforce's) largest current skill gaps.
    """
    gap_query = db.query(models.SkillGapSnapshot).filter(models.SkillGapSnapshot.gap > 0)
    if employee_id:
        gap_query = gap_query.filter(models.SkillGapSnapshot.employee_id == employee_id)
    gaps = gap_query.order_by(models.SkillGapSnapshot.gap.desc()).limit(5).all()

    skill_ids = [g.skill_id for g in gaps] or [s.id for s in db.query(models.Skill).limit(3).all()]
    matched_courses = db.query(models.Course).filter(models.Course.skill_id.in_(skill_ids)).limit(4).all()

    title = f"AI Generated Path — Employee #{employee_id}" if employee_id else "AI Generated Path — Priority Skills"
    lp = models.LearningPath(title=title, description="Automatically generated from current skill-gap priorities.",
                              status="Draft", generated_by_ai=True)
    db.add(lp)
    db.flush()
    for i, course in enumerate(matched_courses):
        db.add(models.LearningPathItem(learning_path_id=lp.id, item_type="course", course_id=course.id, sequence=i))
    if employee_id:
        db.add(models.LearningPathAssignment(learning_path_id=lp.id, employee_id=employee_id))
        services.create_notification(db, "New AI-generated learning path assigned", title,
                                      type_="AI", audience="employee")
    db.commit()
    db.refresh(lp)
    return _serialize(lp)
