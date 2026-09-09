# routers/skills.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models.skill import Skill
from schemas.skill import SkillCreate, SkillResponse

from security.dependencies import get_current_user, require_admin


router = APIRouter(
    prefix="/skills",
    tags=["Skills"]
)


@router.get(
    "/",
    response_model=list[SkillResponse]
)
def get_skills(
    db: Session = Depends(get_db)
):
    return db.query(Skill).all()


@router.get(
    "/{skill_id}",
    response_model=SkillResponse
)
def get_skill(
    skill_id: int,
    db: Session = Depends(get_db)
):
    skill = (
        db.query(Skill)
        .filter(Skill.id == skill_id)
        .first()
    )

    if not skill:
        raise HTTPException(
            status_code=404,
            detail="Skill not found"
        )

    return skill


@router.post(
    "/",
    response_model=SkillResponse,
    dependencies=[Depends(require_admin)]
)
def create_skill(
    skill_data: SkillCreate,
    db: Session = Depends(get_db)
):
    existing_skill = (
        db.query(Skill)
        .filter(Skill.name == skill_data.name)
        .first()
    )

    if existing_skill:
        raise HTTPException(
            status_code=400,
            detail="Skill already exists"
        )

    skill = Skill(
        name=skill_data.name,
        category=skill_data.category,
        description=skill_data.description
    )

    db.add(skill)
    db.commit()
    db.refresh(skill)

    return skill


@router.put(
    "/{skill_id}",
    response_model=SkillResponse,
    dependencies=[Depends(require_admin)]
)
def update_skill(
    skill_id: int,
    skill_data: SkillCreate,
    db: Session = Depends(get_db)
):
    skill = (
        db.query(Skill)
        .filter(Skill.id == skill_id)
        .first()
    )

    if not skill:
        raise HTTPException(
            status_code=404,
            detail="Skill not found"
        )

    skill.name = skill_data.name
    skill.category = skill_data.category
    skill.description = skill_data.description

    db.commit()
    db.refresh(skill)

    return skill


@router.delete(
    "/{skill_id}",
    dependencies=[Depends(require_admin)]
)
def delete_skill(
    skill_id: int,
    db: Session = Depends(get_db)
):
    skill = (
        db.query(Skill)
        .filter(Skill.id == skill_id)
        .first()
    )

    if not skill:
        raise HTTPException(
            status_code=404,
            detail="Skill not found"
        )

    db.delete(skill)
    db.commit()

    return {
        "message": "Skill deleted successfully"
    }