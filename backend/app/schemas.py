from datetime import datetime
from typing import Optional, List, Any

from pydantic import BaseModel, EmailStr, field_validator


# ---------- Auth ----------
class LoginRequest(BaseModel):
    username: str  # email OR employee code
    password: str


class SignupRequest(BaseModel):
    name: str
    employee_id: str
    email: EmailStr
    department: str
    designation: str
    password: str

    @field_validator("password")
    @classmethod
    def password_len(cls, v):
        if len(v) < 6:
            raise ValueError("Password must be at least 6 characters")
        return v


class UserOut(BaseModel):
    id: int
    name: str
    email: str
    role: str
    employee_id: Optional[int] = None


class TokenResponse(BaseModel):
    token: str
    token_type: str = "bearer"
    user: UserOut


# ---------- Department ----------
class DepartmentIn(BaseModel):
    name: str
    description: Optional[str] = None


# ---------- Skill / Framework ----------
class SkillIn(BaseModel):
    name: str
    category: str = "Technical"
    description: Optional[str] = None


class FrameworkIn(BaseModel):
    name: str  # skill/competency name
    category: str = "Technical"
    required_level: int = 2
    job_roles: str = "General"
    status: str = "Active"


# ---------- Employee ----------
class EmployeeIn(BaseModel):
    name: str
    email: Optional[EmailStr] = None
    department: Optional[str] = None  # department name (created if missing)
    designation: Optional[str] = None
    experience_years: Optional[float] = 0
    phone: Optional[str] = None
    notes: Optional[str] = None
    employee_code: Optional[str] = None
    password: Optional[str] = None  # if provided, also creates a login


class CompetencyIn(BaseModel):
    employee_id: Optional[int] = None
    employee_name: Optional[str] = None
    skill_name: str
    category: str = "Technical"
    current_level: int = 0
    required_level: int = 2


# ---------- Courses / Programs ----------
class CourseIn(BaseModel):
    title: str
    provider: str = "iGOT Karmayogi"
    category: str = "Technical"
    duration_hours: float = 1
    level: str = "Beginner"
    description: Optional[str] = None
    skill_name: Optional[str] = None
    modules: Optional[List[str]] = None


class ProgramIn(BaseModel):
    title: str
    venue_mode: str = "Online"
    schedule_start: Optional[datetime] = None
    schedule_end: Optional[datetime] = None
    participants_count: int = 0
    completed_count: int = 0
    status: str = "Scheduled"
    description: Optional[str] = None


# ---------- Learning Paths ----------
class LearningPathItemIn(BaseModel):
    item_type: str  # course | program
    id: int


class LearningPathIn(BaseModel):
    title: str
    description: Optional[str] = None
    items: Optional[List[LearningPathItemIn]] = None
    assign_employee_ids: Optional[List[int]] = None


# ---------- Quiz ----------
class QuizGenerateRequest(BaseModel):
    material_id: Optional[int] = None
    topic: Optional[str] = None
    count: int = 5
    difficulty: str = "Medium"


class QuizQuestionEdit(BaseModel):
    question_text: Optional[str] = None
    options: Optional[List[str]] = None
    correct_index: Optional[int] = None
    explanation: Optional[str] = None
    status: Optional[str] = None


class QuizAttemptSubmit(BaseModel):
    quiz_id: int
    answers: List[Optional[int]]


# ---------- Notifications ----------
class NotificationIn(BaseModel):
    title: str
    message: Optional[str] = None
    type: str = "System"
    audience: str = "admin"


# ---------- Settings ----------
class SettingsIn(BaseModel):
    platformName: Optional[str] = None
    apiBaseUrl: Optional[str] = None
    defaultLanguage: Optional[str] = None
    aiEnabled: Optional[bool] = None


# ---------- Employee self-service ----------
class ProfileUpdate(BaseModel):
    name: Optional[str] = None
    department: Optional[str] = None
    designation: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    education: Optional[str] = None
    experience_years: Optional[float] = None
    current_assignment: Optional[str] = None
    previous_training: Optional[str] = None


class SkillLevelUpdate(BaseModel):
    skill_id: int
    current_level: int


class SkillsBulkUpdate(BaseModel):
    updates: List[SkillLevelUpdate]


class DiagnosticSubmit(BaseModel):
    answers: List[Optional[int]]


class ModuleCompleteRequest(BaseModel):
    module_index: int


class AIActionRequest(BaseModel):
    payload: Optional[dict] = None
