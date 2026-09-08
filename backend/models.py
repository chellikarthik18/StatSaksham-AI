"""
SQLAlchemy ORM models for StatSaksham AI.
Covers all tables required by the project spec.
"""
import enum
from datetime import datetime

from sqlalchemy import (
    Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey,
    Enum, UniqueConstraint
)
from sqlalchemy.orm import relationship

from database import Base


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------
class UserRole(str, enum.Enum):
    employee = "employee"
    trainer = "trainer"
    admin = "admin"


class SelfLevel(str, enum.Enum):
    beginner = "beginner"
    intermediate = "intermediate"
    advanced = "advanced"


class SkillCategory(str, enum.Enum):
    statistical = "statistical"
    technical = "technical"
    digital_governance = "digital_governance"
    behavioural = "behavioural"


class CourseSource(str, enum.Enum):
    igot = "igot"
    nssta_tpac = "nssta_tpac"


class CourseLevel(str, enum.Enum):
    foundation = "foundation"
    intermediate = "intermediate"
    advanced = "advanced"


class EnrollmentStatus(str, enum.Enum):
    recommended = "recommended"
    in_progress = "in_progress"
    completed = "completed"


class DifficultyLevel(str, enum.Enum):
    easy = "easy"
    medium = "medium"
    hard = "hard"


# ---------------------------------------------------------------------------
# Users & Profiles
# ---------------------------------------------------------------------------
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(150), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.employee)
    full_name = Column(String(150), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    profile = relationship("EmployeeProfile", back_populates="user", uselist=False,
                            cascade="all, delete-orphan")
    materials = relationship("LearningMaterial", back_populates="trainer")
    audit_logs = relationship("AuditLog", back_populates="user")


class EmployeeProfile(Base):
    __tablename__ = "employee_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)

    employee_code = Column(String(50), unique=True, nullable=False)
    department = Column(String(150))
    organisation = Column(String(150))
    designation = Column(String(150))
    current_role_id = Column(Integer, ForeignKey("roles.id"), nullable=True)
    grade = Column(String(50))
    experience_years = Column(Float, default=0)
    qualification = Column(String(150))
    specialization = Column(String(150))
    previous_training = Column(Text)
    target_role_id = Column(Integer, ForeignKey("roles.id"), nullable=True)
    preferred_language = Column(String(50), default="English")
    weekly_learning_hours = Column(Float, default=2)
    self_assessed_level = Column(Enum(SelfLevel), default=SelfLevel.beginner)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="profile")
    current_role = relationship("Role", foreign_keys=[current_role_id])
    target_role = relationship("Role", foreign_keys=[target_role_id])
    employee_skills = relationship("EmployeeSkill", back_populates="profile",
                                    cascade="all, delete-orphan")


class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), unique=True, nullable=False)
    description = Column(Text)
    level_order = Column(Integer, default=1)  # 1=lowest, higher = senior

    requirements = relationship("RoleCompetencyRequirement", back_populates="role",
                                 cascade="all, delete-orphan")


# ---------------------------------------------------------------------------
# Skills & Competencies
# ---------------------------------------------------------------------------
class Skill(Base):
    __tablename__ = "skills"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), unique=True, nullable=False)
    category = Column(Enum(SkillCategory), nullable=False)
    description = Column(Text)

    employee_links = relationship("EmployeeSkill", back_populates="skill")
    competency = relationship("Competency", back_populates="skill", uselist=False)


class EmployeeSkill(Base):
    __tablename__ = "employee_skills"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("employee_profiles.id"), nullable=False)
    skill_id = Column(Integer, ForeignKey("skills.id"), nullable=False)
    self_rating = Column(Enum(SelfLevel), default=SelfLevel.beginner)
    diagnostic_score = Column(Float, default=0)   # 0-100, latest assessment score
    current_score = Column(Float, default=0)      # 0-100, updated after each assessment
    competency_achieved = Column(Boolean, default=False)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (UniqueConstraint("profile_id", "skill_id", name="uq_profile_skill"),)

    profile = relationship("EmployeeProfile", back_populates="employee_skills")
    skill = relationship("Skill", back_populates="employee_links")


class Competency(Base):
    __tablename__ = "competencies"

    id = Column(Integer, primary_key=True, index=True)
    skill_id = Column(Integer, ForeignKey("skills.id"), unique=True, nullable=False)
    name = Column(String(150), nullable=False)
    description = Column(Text)
    passing_score = Column(Float, default=70)

    skill = relationship("Skill", back_populates="competency")


class RoleCompetencyRequirement(Base):
    __tablename__ = "role_competency_requirements"

    id = Column(Integer, primary_key=True, index=True)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    skill_id = Column(Integer, ForeignKey("skills.id"), nullable=False)
    required_level = Column(Float, default=70)  # required score out of 100
    is_mandatory = Column(Boolean, default=True)

    __table_args__ = (UniqueConstraint("role_id", "skill_id", name="uq_role_skill"),)

    role = relationship("Role", back_populates="requirements")
    skill = relationship("Skill")


# ---------------------------------------------------------------------------
# Courses (iGOT Karmayogi + NSSTA/TPAC)
# ---------------------------------------------------------------------------
class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True)
    external_id = Column(String(100), unique=True, nullable=True)  # mock iGOT course id
    source = Column(Enum(CourseSource), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    provider = Column(String(150))
    level = Column(Enum(CourseLevel), nullable=False, default=CourseLevel.foundation)
    duration_hours = Column(Float, default=2)
    language = Column(String(50), default="English")
    url = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)

    skill_mappings = relationship("CourseSkillMapping", back_populates="course",
                                   cascade="all, delete-orphan")


class CourseSkillMapping(Base):
    __tablename__ = "course_skill_mapping"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    skill_id = Column(Integer, ForeignKey("skills.id"), nullable=False)

    __table_args__ = (UniqueConstraint("course_id", "skill_id", name="uq_course_skill"),)

    course = relationship("Course", back_populates="skill_mappings")
    skill = relationship("Skill")


class CourseRecommendation(Base):
    __tablename__ = "course_recommendations"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("employee_profiles.id"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    skill_id = Column(Integer, ForeignKey("skills.id"), nullable=False)
    reason = Column(String(255))
    recommended_at = Column(DateTime, default=datetime.utcnow)

    profile = relationship("EmployeeProfile")
    course = relationship("Course")
    skill = relationship("Skill")


class Enrollment(Base):
    __tablename__ = "enrollments"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("employee_profiles.id"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    status = Column(Enum(EnrollmentStatus), default=EnrollmentStatus.recommended)
    enrolled_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    __table_args__ = (UniqueConstraint("profile_id", "course_id", name="uq_profile_course"),)

    profile = relationship("EmployeeProfile")
    course = relationship("Course")


# ---------------------------------------------------------------------------
# Trainer content & quizzes
# ---------------------------------------------------------------------------
class LearningMaterial(Base):
    __tablename__ = "learning_materials"

    id = Column(Integer, primary_key=True, index=True)
    trainer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=False)
    file_name = Column(String(255))
    file_type = Column(String(20))
    extracted_text = Column(Text)
    skill_id = Column(Integer, ForeignKey("skills.id"), nullable=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    trainer = relationship("User", back_populates="materials")
    skill = relationship("Skill")
    quizzes = relationship("Quiz", back_populates="material")


class Quiz(Base):
    __tablename__ = "quizzes"

    id = Column(Integer, primary_key=True, index=True)
    material_id = Column(Integer, ForeignKey("learning_materials.id"), nullable=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=True)
    skill_id = Column(Integer, ForeignKey("skills.id"), nullable=True)
    title = Column(String(255), nullable=False)
    quiz_type = Column(String(30), default="diagnostic")  # diagnostic | final | practice
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    is_published = Column(Boolean, default=True)

    material = relationship("LearningMaterial", back_populates="quizzes")
    course = relationship("Course")
    skill = relationship("Skill")
    questions = relationship("QuizQuestion", back_populates="quiz",
                              cascade="all, delete-orphan")


class QuizQuestion(Base):
    __tablename__ = "quiz_questions"

    id = Column(Integer, primary_key=True, index=True)
    quiz_id = Column(Integer, ForeignKey("quizzes.id"), nullable=False)
    question_text = Column(Text, nullable=False)
    option_a = Column(String(500))
    option_b = Column(String(500))
    option_c = Column(String(500))
    option_d = Column(String(500))
    correct_option = Column(String(1))  # 'A','B','C','D'
    explanation = Column(Text)
    topic = Column(String(150))
    difficulty = Column(Enum(DifficultyLevel), default=DifficultyLevel.medium)

    quiz = relationship("Quiz", back_populates="questions")


class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"

    id = Column(Integer, primary_key=True, index=True)
    quiz_id = Column(Integer, ForeignKey("quizzes.id"), nullable=False)
    profile_id = Column(Integer, ForeignKey("employee_profiles.id"), nullable=False)
    answers_json = Column(Text)  # JSON string {question_id: selected_option}
    score_percent = Column(Float, default=0)
    total_questions = Column(Integer, default=0)
    correct_count = Column(Integer, default=0)
    attempted_at = Column(DateTime, default=datetime.utcnow)

    quiz = relationship("Quiz")
    profile = relationship("EmployeeProfile")


class AssessmentResult(Base):
    """Stores the outcome of diagnostic / final assessments per skill."""
    __tablename__ = "assessment_results"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("employee_profiles.id"), nullable=False)
    skill_id = Column(Integer, ForeignKey("skills.id"), nullable=False)
    quiz_attempt_id = Column(Integer, ForeignKey("quiz_attempts.id"), nullable=True)
    assessment_type = Column(String(30), default="diagnostic")  # diagnostic | final
    score_percent = Column(Float, default=0)
    competency_level = Column(String(30))  # beginner/intermediate/advanced/expert
    created_at = Column(DateTime, default=datetime.utcnow)

    profile = relationship("EmployeeProfile")
    skill = relationship("Skill")


# ---------------------------------------------------------------------------
# Progress & Promotion Readiness
# ---------------------------------------------------------------------------
class ProgressRecord(Base):
    __tablename__ = "progress_records"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("employee_profiles.id"), nullable=False)
    skill_id = Column(Integer, ForeignKey("skills.id"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=True)
    progress_percent = Column(Float, default=0)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    profile = relationship("EmployeeProfile")
    skill = relationship("Skill")
    course = relationship("Course")


class PromotionReadiness(Base):
    __tablename__ = "promotion_readiness"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("employee_profiles.id"), unique=True, nullable=False)
    target_role_id = Column(Integer, ForeignKey("roles.id"), nullable=True)
    readiness_percent = Column(Float, default=0)
    skills_met = Column(Integer, default=0)
    skills_required = Column(Integer, default=0)
    last_calculated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    profile = relationship("EmployeeProfile")
    target_role = relationship("Role")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String(150), nullable=False)
    details = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="audit_logs")
