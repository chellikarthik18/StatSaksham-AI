from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas
from app.security import verify_password, hash_password, create_access_token
from app.deps import get_current_user

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _user_out(user: models.User) -> schemas.UserOut:
    emp_id = user.employee.id if user.employee else None
    return schemas.UserOut(id=user.id, name=user.full_name, email=user.email,
                            role=user.role.value, employee_id=emp_id)


@router.post("/login", response_model=schemas.TokenResponse)
def login(payload: schemas.LoginRequest, db: Session = Depends(get_db)):
    identity = payload.username.strip()
    user = db.query(models.User).filter(models.User.email == identity).first()
    if not user:
        # allow employees to log in with their employee code
        emp = db.query(models.Employee).filter(models.Employee.employee_code == identity).first()
        if emp and emp.user_id:
            user = db.query(models.User).filter(models.User.id == emp.user_id).first()

    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is disabled")

    token = create_access_token({"sub": str(user.id), "role": user.role.value})
    return schemas.TokenResponse(token=token, user=_user_out(user))


@router.post("/signup", response_model=schemas.TokenResponse)
def signup(payload: schemas.SignupRequest, db: Session = Depends(get_db)):
    if db.query(models.User).filter(models.User.email == payload.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    if db.query(models.Employee).filter(models.Employee.employee_code == payload.employee_id).first():
        raise HTTPException(status_code=400, detail="Employee ID already in use")

    dept = db.query(models.Department).filter(models.Department.name == payload.department).first()
    if not dept:
        dept = models.Department(name=payload.department)
        db.add(dept)
        db.flush()

    user = models.User(
        email=payload.email, full_name=payload.name,
        hashed_password=hash_password(payload.password), role=models.RoleEnum.employee,
    )
    db.add(user)
    db.flush()

    employee = models.Employee(
        user_id=user.id, employee_code=payload.employee_id, name=payload.name,
        email=payload.email, department_id=dept.id, designation=payload.designation,
    )
    db.add(employee)
    db.commit()
    db.refresh(user)

    token = create_access_token({"sub": str(user.id), "role": user.role.value})
    return schemas.TokenResponse(token=token, user=_user_out(user))


@router.get("/me", response_model=schemas.UserOut)
def me(current_user: models.User = Depends(get_current_user)):
    return _user_out(current_user)


@router.post("/logout")
def logout():
    # Stateless JWTs: the frontend simply discards the token client-side.
    return {"status": "ok"}
