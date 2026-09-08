"""
Pydantic schemas (request/response models) for StatSaksham AI.
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, ConfigDict


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------
class UserRegister(BaseModel):
    full_name: str
    email: EmailStr
    password: str
    role: str = "employee"   # employee | trainer | admin (admin creation restricted in practice)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    full_name: str
    user_id: int


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: str
    full_name: str
    role: str
    is_active: bool


# ---------------------------------------------------------------------------
# Roles / Skills
# ---------------------------------------------------------------------------
class RoleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    description: Optional[str] = None
    level_order: int


class SkillOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    category: str
    description: Optional[str] = None


# ---------------------------------------------------------------------------
# Employee profile
# ---------------------------------------------------------------------------
class EmployeeProfileIn(BaseModel):
    employee_code: str
    department: str
    organisation: str
    designation: str
    current_role_id: Optional[int] = None
    grade: Optional[str] = None
    experience_years: Optional[float] = 0
    qualification: Optional[str] = None
    specialization: Optional[str] = None
    previous_training: Optional[str] = None
    target_role_id: Optional[int] = None
    preferred_language: Optional[str] = "English"
    weekly_learning_hours: Optional[float] = 2
    self_assessed_level: Optional[str] = "beginner"
    skill_ids: List[int] = []   # existing skills selected by employee


class EmployeeProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    employee_code: str
    department: Optional[str] = None
    organisation: Optional[str] = None
    designation: Optional[str] = None
    current_role_id: Optional[int] = None
    target_role_id: Optional[int] = None
    grade: Optional[str] = None
    experience_years: Optional[float] = None
    qualification: Optional[str] = None
    specialization: Optional[str] = None
    previous_training: Optional[str] = None
    preferred_language: Optional[str] = None
    weekly_learning_hours: Optional[float] = None
    self_assessed_level: Optional[str] = None


# ---------------------------------------------------------------------------
# Quiz / Assessment
# ---------------------------------------------------------------------------
class QuizQuestionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    question_text: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str
    topic: Optional[str] = None
    difficulty: Optional[str] = None
    # correct_option intentionally excluded from learner-facing output


class QuizQuestionAdminOut(QuizQuestionOut):
    correct_option: str
    explanation: Optional[str] = None


class QuizOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    quiz_type: str
    skill_id: Optional[int] = None
    questions: List[QuizQuestionOut] = []


class QuizSubmission(BaseModel):
    quiz_id: int
    answers: dict  # {question_id(str): "A"/"B"/"C"/"D"}


class QuizQuestionEdit(BaseModel):
    question_text: Optional[str] = None
    option_a: Optional[str] = None
    option_b: Optional[str] = None
    option_c: Optional[str] = None
    option_d: Optional[str] = None
    correct_option: Optional[str] = None
    explanation: Optional[str] = None
    topic: Optional[str] = None
    difficulty: Optional[str] = None


# ---------------------------------------------------------------------------
# Courses
# ---------------------------------------------------------------------------
class CourseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    external_id: Optional[str] = None
    source: str
    title: str
    description: Optional[str] = None
    provider: Optional[str] = None
    level: str
    duration_hours: Optional[float] = None
    language: Optional[str] = None
    url: Optional[str] = None


class CourseIn(BaseModel):
    source: str
    title: str
    description: Optional[str] = None
    provider: Optional[str] = None
    level: str
    duration_hours: Optional[float] = 2
    language: Optional[str] = "English"
    url: Optional[str] = None
    skill_ids: List[int] = []


class EnrollmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    course_id: int
    status: str
    enrolled_at: datetime
    completed_at: Optional[datetime] = None


# ---------------------------------------------------------------------------
# Trainer uploads
# ---------------------------------------------------------------------------
class GeneratedQuestion(BaseModel):
    question_text: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str
    correct_option: str
    explanation: str
    topic: str
    difficulty: str = "medium"


class MaterialOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    file_name: Optional[str] = None
    file_type: Optional[str] = None
    skill_id: Optional[int] = None
    uploaded_at: datetime


# ---------------------------------------------------------------------------
# Admin
# ---------------------------------------------------------------------------
class RoleCompetencyIn(BaseModel):
    role_id: int
    skill_id: int
    required_level: float = 70
    is_mandatory: bool = True


class SkillIn(BaseModel):
    name: str
    category: str
    description: Optional[str] = None


class RoleIn(BaseModel):
    name: str
    description: Optional[str] = None
    level_order: int = 1
