# routers/employees.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models.user import User
from models.employee import EmployeeProfile

from schemas.employee import (
    EmployeeProfileCreate,
    EmployeeProfileResponse
)

from security.dependencies import get_current_user


router = APIRouter(
    prefix="/employees",
    tags=["Employees"]
)


@router.get(
    "/me",
    response_model=EmployeeProfileResponse
)
def get_my_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    profile = (
        db.query(EmployeeProfile)
        .filter(EmployeeProfile.user_id == current_user.id)
        .first()
    )

    if not profile:
        raise HTTPException(
            status_code=404,
            detail="Employee profile not found"
        )

    return profile


@router.post(
    "/me",
    response_model=EmployeeProfileResponse
)
def create_my_profile(
    profile_data: EmployeeProfileCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Check existing profile
    existing_profile = (
        db.query(EmployeeProfile)
        .filter(EmployeeProfile.user_id == current_user.id)
        .first()
    )

    if existing_profile:
        raise HTTPException(
            status_code=400,
            detail="Profile already exists"
        )

    profile = EmployeeProfile(
        user_id=current_user.id,
        employee_id=profile_data.employee_id,
        department=profile_data.department,
        designation=profile_data.designation,
        experience=profile_data.experience
    )

    db.add(profile)
    db.commit()
    db.refresh(profile)

    return profile


@router.put(
    "/me",
    response_model=EmployeeProfileResponse
)
def update_my_profile(
    profile_data: EmployeeProfileCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    profile = (
        db.query(EmployeeProfile)
        .filter(EmployeeProfile.user_id == current_user.id)
        .first()
    )

    if not profile:
        raise HTTPException(
            status_code=404,
            detail="Employee profile not found"
        )

    profile.employee_id = profile_data.employee_id
    profile.department = profile_data.department
    profile.designation = profile_data.designation
    profile.experience = profile_data.experience

    db.commit()
    db.refresh(profile)

    return profile


@router.get(
    "/{employee_id}",
    response_model=EmployeeProfileResponse
)
def get_employee_profile(
    employee_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    profile = (
        db.query(EmployeeProfile)
        .filter(EmployeeProfile.id == employee_id)
        .first()
    )

    if not profile:
        raise HTTPException(
            status_code=404,
            detail="Employee not found"
        )

    return profile