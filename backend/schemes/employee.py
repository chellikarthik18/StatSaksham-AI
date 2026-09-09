from pydantic import BaseModel


class EmployeeProfileCreate(BaseModel):
    employee_id: str
    department: str
    designation: str
    experience: int


class EmployeeProfileResponse(EmployeeProfileCreate):
    id: int
    user_id: int

    class Config:
        from_attributes = True