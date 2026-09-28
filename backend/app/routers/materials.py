import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.database import get_db
from app import models
from app.deps import require_admin_or_trainer
from app.config import settings
from app.utils.file_parser import extract_text

router = APIRouter(prefix="/api/admin/materials", tags=["materials"])

ALLOWED_EXTENSIONS = {"pdf", "doc", "docx", "ppt", "pptx", "txt"}


def _serialize(m: models.Material) -> dict:
    return {
        "id": m.id, "filename": m.filename, "topic": m.topic, "fileType": m.file_type,
        "uploadedAt": m.uploaded_at,
        "hasExtractedText": bool(m.extracted_text and m.extracted_text.strip()),
        "preview": (m.extracted_text or "")[:280],
    }


@router.get("")
def list_materials(db: Session = Depends(get_db), _user=Depends(require_admin_or_trainer)):
    rows = db.query(models.Material).order_by(models.Material.id.desc()).all()
    return [_serialize(r) for r in rows]


@router.post("")
async def upload_material(
    file: UploadFile = File(...), topic: str = Form(""),
    db: Session = Depends(get_db), user=Depends(require_admin_or_trainer),
):
    ext = (file.filename.rsplit(".", 1)[-1] if "." in file.filename else "").lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: .{ext}")

    safe_name = f"{uuid.uuid4().hex}.{ext}"
    dest = Path(settings.UPLOAD_DIR) / safe_name
    contents = await file.read()
    if len(contents) > 25 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large (max 25MB)")
    dest.write_bytes(contents)

    extracted = extract_text(dest, ext)

    material = models.Material(
        filename=file.filename, stored_path=str(dest), topic=topic or None,
        file_type=ext, extracted_text=extracted[:20000], uploaded_by=user.id,
    )
    db.add(material)
    db.commit()
    db.refresh(material)
    return _serialize(material)


@router.delete("/{material_id}")
def delete_material(material_id: int, db: Session = Depends(get_db), _user=Depends(require_admin_or_trainer)):
    m = db.query(models.Material).filter(models.Material.id == material_id).first()
    if not m:
        raise HTTPException(status_code=404, detail="Material not found")
    try:
        Path(m.stored_path).unlink(missing_ok=True)
    except Exception:
        pass
    db.delete(m)
    db.commit()
    return {"status": "deleted"}
