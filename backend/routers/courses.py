# routers/courses.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models.course import Course

from schemas.course import (
    CourseCreate,
    CourseResponse
)

from security.dependencies import require_admin


router = APIRouter(
    prefix="/courses",
    tags=["Courses"]
)


@router.get(
    "/",
    response_model=list[CourseResponse]
)
def get_courses(
    db: Session = Depends(get_db)
):
    return db.query(Course).all()


@router.get(
    "/{course_id}",
    response_model=CourseResponse
)
def get_course(
    course_id: int,
    db: Session = Depends(get_db)
):
    course = (
        db.query(Course)
        .filter(Course.id == course_id)
        .first()
    )

    if not course:
        raise HTTPException(
            status_code=404,
            detail="Course not found"
        )

    return course


@router.post(
    "/",
    response_model=CourseResponse,
    dependencies=[Depends(require_admin)]
)
def create_course(
    course_data: CourseCreate,
    db: Session = Depends(get_db)
):
    course = Course(
        title=course_data.title,
        description=course_data.description,
        skill_id=course_data.skill_id,
        difficulty=course_data.difficulty,
        duration=course_data.duration,
        source=course_data.source,
        igot_url=course_data.igot_url
    )

    db.add(course)
    db.commit()
    db.refresh(course)

    return course


@router.put(
    "/{course_id}",
    response_model=CourseResponse,
    dependencies=[Depends(require_admin)]
)
def update_course(
    course_id: int,
    course_data: CourseCreate,
    db: Session = Depends(get_db)
):
    course = (
        db.query(Course)
        .filter(Course.id == course_id)
        .first()
    )

    if not course:
        raise HTTPException(
            status_code=404,
            detail="Course not found"
        )

    course.title = course_data.title
    course.description = course_data.description
    course.skill_id = course_data.skill_id
    course.difficulty = course_data.difficulty
    course.duration = course_data.duration
    course.source = course_data.source
    course.igot_url = course_data.igot_url

    db.commit()
    db.refresh(course)

    return course


@router.delete(
    "/{course_id}",
    dependencies=[Depends(require_admin)]
)
def delete_course(
    course_id: int,
    db: Session = Depends(get_db)
):
    course = (
        db.query(Course)
        .filter(Course.id == course_id)
        .first()
    )

    if not course:
        raise HTTPException(
            status_code=404,
            detail="Course not found"
        )

    db.delete(course)
    db.commit()

    return {
        "message": "Course deleted successfully"
    }