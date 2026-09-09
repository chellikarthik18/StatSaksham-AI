# routers/progress.py

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models.user import User
from models.progress import Progress

from schemas.progress import (
    ProgressCreate,
    ProgressResponse
)

from security.dependencies import get_current_user


router = APIRouter(
    prefix="/progress",
    tags=["Progress"]
)


@router.post(
    "/",
    response_model=ProgressResponse
)
def create_or_update_progress(
    progress_data: ProgressCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    progress = (
        db.query(Progress)
        .filter(
            Progress.user_id == current_user.id,
            Progress.course_id == progress_data.course_id
        )
        .first()
    )

    if progress:
        # Update existing progress
        progress.status = progress_data.status
        progress.percentage = progress_data.percentage
        progress.score = progress_data.score

        if progress_data.percentage >= 100:
            progress.completed_at = datetime.utcnow()

    else:
        # Create new progress
        progress = Progress(
            user_id=current_user.id,
            course_id=progress_data.course_id,
            status=progress_data.status,
            percentage=progress_data.percentage,
            score=progress_data.score
        )

        if progress_data.percentage >= 100:
            progress.completed_at = datetime.utcnow()

        db.add(progress)

    db.commit()
    db.refresh(progress)

    return progress


@router.get(
    "/me",
    response_model=list[ProgressResponse]
)
def get_my_progress(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    progress = (
        db.query(Progress)
        .filter(Progress.user_id == current_user.id)
        .all()
    )

    return progress


@router.get(
    "/course/{course_id}",
    response_model=ProgressResponse
)
def get_course_progress(
    course_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    progress = (
        db.query(Progress)
        .filter(
            Progress.user_id == current_user.id,
            Progress.course_id == course_id
        )
        .first()
    )

    if not progress:
        raise HTTPException(
            status_code=404,
            detail="Progress not found"
        )

    return progress