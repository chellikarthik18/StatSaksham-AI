from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.database import get_db
from app import models, schemas
from app.deps import require_admin_or_trainer, get_current_user

router = APIRouter(prefix="/api/admin/notifications", tags=["notifications"])


def _serialize(n: models.Notification) -> dict:
    return {
        "id": n.id, "date": n.created_at, "type": n.type, "title": n.title,
        "message": n.message, "status": "Read" if n.is_read else "Unread", "audience": n.audience,
    }


@router.get("")
def list_notifications(search: str = "", db: Session = Depends(get_db), _user=Depends(require_admin_or_trainer)):
    q = db.query(models.Notification).filter(models.Notification.audience.in_(["admin", "all"]))
    if search:
        like = f"%{search}%"
        q = q.filter(or_(models.Notification.title.ilike(like), models.Notification.message.ilike(like)))
    rows = q.order_by(models.Notification.created_at.desc()).limit(200).all()
    return [_serialize(r) for r in rows]


@router.post("")
def create_notification(payload: schemas.NotificationIn, db: Session = Depends(get_db),
                         _user=Depends(require_admin_or_trainer)):
    n = models.Notification(title=payload.title, message=payload.message, type=payload.type,
                             audience=payload.audience)
    db.add(n)
    db.commit()
    db.refresh(n)
    return _serialize(n)


@router.put("/{note_id}/read")
def mark_read(note_id: int, db: Session = Depends(get_db), _user=Depends(get_current_user)):
    n = db.query(models.Notification).filter(models.Notification.id == note_id).first()
    if not n:
        raise HTTPException(status_code=404, detail="Notification not found")
    n.is_read = True
    db.commit()
    return _serialize(n)


@router.delete("/{note_id}")
def delete_notification(note_id: int, db: Session = Depends(get_db), _user=Depends(require_admin_or_trainer)):
    n = db.query(models.Notification).filter(models.Notification.id == note_id).first()
    if not n:
        raise HTTPException(status_code=404, detail="Notification not found")
    db.delete(n)
    db.commit()
    return {"status": "deleted"}
