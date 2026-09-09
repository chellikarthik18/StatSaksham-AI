# routers/auth.py

from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pwdlib import PasswordHash

from database import get_db
from models.user import User
from schemas.auth import UserRegister, UserLogin, Token
from security.jwt import create_access_token


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

password_hash = PasswordHash.recommended()


@router.post(
    "/register",
    response_model=Token,
    status_code=status.HTTP_201_CREATED
)
def register(
    user_data: UserRegister,
    db: Session = Depends(get_db)
):
    # Check whether email already exists
    existing_user = (
        db.query(User)
        .filter(User.email == user_data.email)
        .first()
    )

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )

    # Hash password
    hashed_password = password_hash.hash(user_data.password)

    # Create user
    new_user = User(
        name=user_data.name,
        email=user_data.email,
        password_hash=hashed_password,
        role="employee"
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Generate JWT
    access_token = create_access_token(
        data={
            "sub": str(new_user.id),
            "role": new_user.role
        },
        expires_delta=timedelta(minutes=30)
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


@router.post("/login", response_model=Token)
def login(
    user_data: UserLogin,
    db: Session = Depends(get_db)
):
    # Find user
    user = (
        db.query(User)
        .filter(User.email == user_data.email)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    # Verify password
    if not password_hash.verify(
        user_data.password,
        user.password_hash
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    # Generate token
    access_token = create_access_token(
        data={
            "sub": str(user.id),
            "role": user.role
        },
        expires_delta=timedelta(minutes=30)
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }