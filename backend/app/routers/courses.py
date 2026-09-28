from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas, services
from app.deps import require_admin_or_trainer, require_admin
from app.seed_data import MOCK_COURSES

router = APIRouter(prefix="/api/admin/courses", tags=["courses"])


def _serialize(db: Session, course: models.Course) -> dict:
    enrolled = db.query(models.Enrollment).filter(
        models.Enrollment.course_id == course.id, models.Enrollment.item_type == "course"
    ).count()
    return {
        "id": course.id, "title": course.title, "provider": course.provider,
        "category": course.category, "durationHours": course.duration_hours, "level": course.level,
        "description": course.description, "status": course.status, "enrolled": enrolled,
        "modules": course.modules or [],
    }


@router.get("")
def list_courses(search: str = "", category: str = "", db: Session = Depends(get_db),
                  _user=Depends(require_admin_or_trainer)):
    q = db.query(models.Course)
    if search:
        q = q.filter(models.Course.title.ilike(f"%{search}%"))
    if category:
        q = q.filter(models.Course.category == category)
    rows = q.order_by(models.Course.id.desc()).all()
    return [_serialize(db, r) for r in rows]


@router.post("")
def create_course(payload: schemas.CourseIn, db: Session = Depends(get_db),
                   _user=Depends(require_admin_or_trainer)):
    skill = services.get_or_create_skill(db, payload.skill_name, payload.category) if payload.skill_name else None
    course = models.Course(
        title=payload.title, provider=payload.provider, category=payload.category,
        duration_hours=payload.duration_hours, level=payload.level, description=payload.description,
        skill_id=skill.id if skill else None, modules=payload.modules or [], status="Synced",
    )
    db.add(course)
    db.commit()
    db.refresh(course)
    return _serialize(db, course)


@router.put("/{course_id}")
def update_course(course_id: int, payload: schemas.CourseIn, db: Session = Depends(get_db),
                   _user=Depends(require_admin_or_trainer)):
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    course.title = payload.title
    course.provider = payload.provider
    course.category = payload.category
    course.duration_hours = payload.duration_hours
    course.level = payload.level
    course.description = payload.description
    if payload.modules is not None:
        course.modules = payload.modules
    db.commit()
    db.refresh(course)
    return _serialize(db, course)


@router.delete("/{course_id}")
def delete_course(course_id: int, db: Session = Depends(get_db), _user=Depends(require_admin)):
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    db.query(models.Enrollment).filter(models.Enrollment.course_id == course_id).delete()
    db.query(models.LearningPathItem).filter(models.LearningPathItem.course_id == course_id).delete()
    db.query(models.Recommendation).filter(models.Recommendation.course_id == course_id).delete()
    db.delete(course)
    db.commit()
    return {"status": "deleted"}


@router.post("/sync")
def sync_mock_catalogue(db: Session = Depends(get_db), _user=Depends(require_admin_or_trainer)):
    """
    Upserts the bundled MOCK iGOT catalogue. This is explicitly demo/seed
    data - the project does not claim a live government API integration
    since no real credentials/API were supplied.
    """
    created = 0
    for item in MOCK_COURSES:
        existing = db.query(models.Course).filter(models.Course.title == item["title"]).first()
        if existing:
            continue
        skill = services.get_or_create_skill(db, item["skill"], item["category"])
        db.add(models.Course(
            title=item["title"], provider=item["provider"], category=item["category"],
            duration_hours=item["duration_hours"], level=item["level"], description=item["description"],
            skill_id=skill.id, modules=item["modules"], status="Synced",
        ))
        created += 1
    db.commit()
    return {"status": "ok", "created": created, "note": "Mock catalogue sync (no live iGOT API configured)."}
