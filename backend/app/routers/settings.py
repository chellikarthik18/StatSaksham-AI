from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas
from app.deps import require_admin

router = APIRouter(prefix="/api/admin/settings", tags=["settings"])

DEFAULTS = {
    "platformName": "STATSAKHAM",
    "apiBaseUrl": "/api",
    "defaultLanguage": "English",
    "aiEnabled": "true",
}


@router.get("")
def get_settings(db: Session = Depends(get_db), _user=Depends(require_admin)):
    rows = {r.key: r.value for r in db.query(models.SettingRecord).all()}
    merged = {**DEFAULTS, **rows}
    merged["aiEnabled"] = str(merged["aiEnabled"]).lower() in ("1", "true", "yes")
    merged["integrationStatus"] = {
        "database": "Connected",
        "aiService": "Connected (local deterministic engine)",
        "igotIntegration": "Mock catalogue (no live API configured)",
        "nsstaTpac": "Mock catalogue (no live API configured)",
    }
    return merged


@router.put("")
def update_settings(payload: schemas.SettingsIn, db: Session = Depends(get_db), _user=Depends(require_admin)):
    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        row = db.query(models.SettingRecord).filter(models.SettingRecord.key == key).first()
        str_value = str(value)
        if row:
            row.value = str_value
        else:
            db.add(models.SettingRecord(key=key, value=str_value))
    db.commit()
    return get_settings(db=db, _user=_user)
