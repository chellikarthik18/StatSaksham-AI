from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas
from app.deps import require_admin_or_trainer, require_admin
from app.seed_data import MOCK_PROGRAMS

router = APIRouter(prefix="/api/admin/programs", tags=["programs"])


def _serialize(program: models.Program) -> dict:
    return {
        "id": program.id, "title": program.title, "venueMode": program.venue_mode,
        "scheduleStart": program.schedule_start, "scheduleEnd": program.schedule_end,
        "participants": program.participants_count, "completed": program.completed_count,
        "status": program.status, "description": program.description,
    }


@router.get("")
def list_programs(search: str = "", db: Session = Depends(get_db), _user=Depends(require_admin_or_trainer)):
    q = db.query(models.Program)
    if search:
        q = q.filter(models.Program.title.ilike(f"%{search}%"))
    rows = q.order_by(models.Program.id.desc()).all()
    return [_serialize(r) for r in rows]


@router.post("")
def create_program(payload: schemas.ProgramIn, db: Session = Depends(get_db),
                    _user=Depends(require_admin_or_trainer)):
    program = models.Program(**payload.model_dump())
    db.add(program)
    db.commit()
    db.refresh(program)
    return _serialize(program)


@router.put("/{program_id}")
def update_program(program_id: int, payload: schemas.ProgramIn, db: Session = Depends(get_db),
                    _user=Depends(require_admin_or_trainer)):
    program = db.query(models.Program).filter(models.Program.id == program_id).first()
    if not program:
        raise HTTPException(status_code=404, detail="Program not found")
    for k, v in payload.model_dump().items():
        setattr(program, k, v)
    db.commit()
    db.refresh(program)
    return _serialize(program)


@router.delete("/{program_id}")
def delete_program(program_id: int, db: Session = Depends(get_db), _user=Depends(require_admin)):
    program = db.query(models.Program).filter(models.Program.id == program_id).first()
    if not program:
        raise HTTPException(status_code=404, detail="Program not found")
    db.query(models.Enrollment).filter(models.Enrollment.program_id == program_id).delete()
    db.query(models.LearningPathItem).filter(models.LearningPathItem.program_id == program_id).delete()
    db.query(models.Recommendation).filter(models.Recommendation.program_id == program_id).delete()
    db.delete(program)
    db.commit()
    return {"status": "deleted"}


@router.post("/sync")
def sync_mock_programs(db: Session = Depends(get_db), _user=Depends(require_admin_or_trainer)):
    created = 0
    for item in MOCK_PROGRAMS:
        if db.query(models.Program).filter(models.Program.title == item["title"]).first():
            continue
        db.add(models.Program(**item))
        created += 1
    db.commit()
    return {"status": "ok", "created": created, "note": "Mock NSSTA/TPAC catalogue sync (demo data)."}
