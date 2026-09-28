"""
SQLAlchemy models for StatSaksham AI.

Covers: users/roles, departments, employees, skills/competencies,
role competency requirements, employee skills, skill-gap snapshots,
emerging skills, iGOT courses, NSSTA/TPAC programmes, learning paths
(+ items + assignments), enrolments, learning materials, quizzes
(+ questions + attempts), diagnostic questions/attempts, notifications,
settings and an audit log.
"""
import enum
from datetime import datetime

from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime, Float, ForeignKey,
    Enum, JSON, UniqueConstraint
)
from sqlalchemy.orm import relationship

from app.database import Base


class RoleEnum(str, enum.Enum):
    admin = "admin"
    trainer = "trainer"
    employee = "employee"


class TrainingStatusEnum(str, enum.Enum):
    pending = "Pending"
    in_progress = "In Progress"
    completed = "Completed"


class PriorityEnum(str, enum.Enum):
    critical = "Critical"
    high = "High"
    medium = "Medium"
    low = "Low"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(190), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(190), nullable=False)
    role = Column(Enum(RoleEnum), nullable=False, default=RoleEnum.employee)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    employee = relationship("Employee", back_populates="user", uselist=False)


class Department(Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(190), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    employees = relationship("Employee", back_populates="department")


class Employee(Base):
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=True)
    employee_code = Column(String(40), unique=True, index=True, nullable=False)
    name = Column(String(190), nullable=False)
    email = Column(String(190), nullable=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    designation = Column(String(190), nullable=True)
    experience_years = Column(Float, default=0)
    phone = Column(String(40), nullable=True)
    education = Column(String(255), nullable=True)
    current_assignment = Column(String(255), nullable=True)
    previous_training = Column(String(255), nullable=True)
    training_status = Column(Enum(TrainingStatusEnum), default=TrainingStatusEnum.pending)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="employee")
    department = relationship("Department", back_populates="employees")
    skills = relationship("EmployeeSkill", back_populates="employee", cascade="all, delete-orphan")
    enrollments = relationship("Enrollment", back_populates="employee", cascade="all, delete-orphan")


class Skill(Base):
    """Master list of skills / competencies (used by both admin framework and employee profile)."""
    __tablename__ = "skills"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(190), nullable=False)
    category = Column(String(80), nullable=False, default="Technical")  # Statistical/Technical/Digital Governance/Behavioural
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (UniqueConstraint("name", "category", name="uq_skill_name_category"),)


class RoleCompetencyRequirement(Base):
    """Competency framework: required proficiency level (0-3) for a given job role/skill."""
    __tablename__ = "role_competency_requirements"

    id = Column(Integer, primary_key=True, index=True)
    job_role = Column(String(190), nullable=False)
    skill_id = Column(Integer, ForeignKey("skills.id"), nullable=False)
    required_level = Column(Integer, default=2)
    status = Column(String(30), default="Active")
    created_at = Column(DateTime, default=datetime.utcnow)

    skill = relationship("Skill")


class EmployeeSkill(Base):
    """Current & target competency level of an employee for a given skill."""
    __tablename__ = "employee_skills"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    skill_id = Column(Integer, ForeignKey("skills.id"), nullable=False)
    current_level = Column(Integer, default=0)  # 0-3
    required_level = Column(Integer, default=2)  # 0-3
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    employee = relationship("Employee", back_populates="skills")
    skill = relationship("Skill")

    __table_args__ = (UniqueConstraint("employee_id", "skill_id", name="uq_employee_skill"),)


class SkillGapSnapshot(Base):
    """Stored result of a skill-gap analysis run (admin 'Run Analysis' / employee 'Analyze')."""
    __tablename__ = "skill_gap_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    skill_id = Column(Integer, ForeignKey("skills.id"), nullable=False)
    current_level = Column(Integer, default=0)
    required_level = Column(Integer, default=2)
    gap = Column(Integer, default=0)
    priority = Column(Enum(PriorityEnum), default=PriorityEnum.medium)
    computed_at = Column(DateTime, default=datetime.utcnow)

    employee = relationship("Employee")
    skill = relationship("Skill")


class EmergingSkill(Base):
    __tablename__ = "emerging_skills"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(190), unique=True, nullable=False)
    current_demand = Column(Float, default=0)
    future_demand = Column(Float, default=0)
    priority = Column(Enum(PriorityEnum), default=PriorityEnum.medium)
    affected_departments = Column(String(255), nullable=True)
    status = Column(String(40), default="Monitoring")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Course(Base):
    """iGOT Karmayogi course catalogue entry."""
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(220), nullable=False)
    provider = Column(String(120), default="iGOT Karmayogi")
    category = Column(String(80), default="Technical")
    duration_hours = Column(Float, default=1)
    level = Column(String(40), default="Beginner")
    description = Column(Text, nullable=True)
    skill_id = Column(Integer, ForeignKey("skills.id"), nullable=True)
    status = Column(String(30), default="Synced")
    modules = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)

    skill = relationship("Skill")


class Program(Base):
    """NSSTA / TPAC training programme."""
    __tablename__ = "programs"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(220), nullable=False)
    venue_mode = Column(String(120), default="Online")
    schedule_start = Column(DateTime, nullable=True)
    schedule_end = Column(DateTime, nullable=True)
    participants_count = Column(Integer, default=0)
    completed_count = Column(Integer, default=0)
    status = Column(String(30), default="Scheduled")
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class LearningPath(Base):
    __tablename__ = "learning_paths"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(220), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(30), default="Draft")
    generated_by_ai = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    items = relationship("LearningPathItem", back_populates="learning_path", cascade="all, delete-orphan")
    assignments = relationship("LearningPathAssignment", back_populates="learning_path", cascade="all, delete-orphan")


class LearningPathItem(Base):
    __tablename__ = "learning_path_items"

    id = Column(Integer, primary_key=True, index=True)
    learning_path_id = Column(Integer, ForeignKey("learning_paths.id"), nullable=False)
    item_type = Column(String(20), default="course")  # course | program
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=True)
    program_id = Column(Integer, ForeignKey("programs.id"), nullable=True)
    sequence = Column(Integer, default=0)

    learning_path = relationship("LearningPath", back_populates="items")
    course = relationship("Course")
    program = relationship("Program")


class LearningPathAssignment(Base):
    __tablename__ = "learning_path_assignments"

    id = Column(Integer, primary_key=True, index=True)
    learning_path_id = Column(Integer, ForeignKey("learning_paths.id"), nullable=False)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    progress = Column(Float, default=0)
    status = Column(String(30), default="Not Started")
    assigned_at = Column(DateTime, default=datetime.utcnow)

    learning_path = relationship("LearningPath", back_populates="assignments")
    employee = relationship("Employee")

    __table_args__ = (UniqueConstraint("learning_path_id", "employee_id", name="uq_path_employee"),)


class Enrollment(Base):
    """Employee enrolment/progress against a course or programme."""
    __tablename__ = "enrollments"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    item_type = Column(String(20), default="course")  # course | program
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=True)
    program_id = Column(Integer, ForeignKey("programs.id"), nullable=True)
    status = Column(String(30), default="Not Started")  # Not Started | In Progress | Completed
    progress = Column(Float, default=0)
    completed_modules = Column(JSON, default=list)
    enrolled_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    employee = relationship("Employee", back_populates="enrollments")
    course = relationship("Course")
    program = relationship("Program")


class Material(Base):
    __tablename__ = "materials"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    stored_path = Column(String(500), nullable=False)
    topic = Column(String(190), nullable=True)
    file_type = Column(String(20), nullable=True)
    extracted_text = Column(Text, nullable=True)
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow)


class Quiz(Base):
    __tablename__ = "quizzes"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(220), nullable=False)
    material_id = Column(Integer, ForeignKey("materials.id"), nullable=True)
    topic = Column(String(190), nullable=True)
    difficulty = Column(String(20), default="Medium")
    status = Column(String(20), default="Draft")  # Draft | Published
    generated_by_ai = Column(Boolean, default=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    questions = relationship("QuizQuestion", back_populates="quiz", cascade="all, delete-orphan")
    attempts = relationship("QuizAttempt", back_populates="quiz", cascade="all, delete-orphan")


class QuizQuestion(Base):
    __tablename__ = "quiz_questions"

    id = Column(Integer, primary_key=True, index=True)
    quiz_id = Column(Integer, ForeignKey("quizzes.id"), nullable=False)
    question_text = Column(Text, nullable=False)
    options = Column(JSON, default=list)  # list[str]
    correct_index = Column(Integer, default=0)
    explanation = Column(Text, nullable=True)
    topic = Column(String(190), nullable=True)
    difficulty = Column(String(20), default="Medium")
    question_type = Column(String(20), default="MCQ")
    status = Column(String(20), default="Draft")

    quiz = relationship("Quiz", back_populates="questions")


class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"

    id = Column(Integer, primary_key=True, index=True)
    quiz_id = Column(Integer, ForeignKey("quizzes.id"), nullable=False)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=True)
    score = Column(Integer, default=0)
    total = Column(Integer, default=0)
    percentage = Column(Float, default=0)
    answers = Column(JSON, default=list)
    attempted_at = Column(DateTime, default=datetime.utcnow)

    quiz = relationship("Quiz", back_populates="attempts")
    employee = relationship("Employee")


class DiagnosticQuestion(Base):
    """Fixed diagnostic-assessment question bank used by the employee portal."""
    __tablename__ = "diagnostic_questions"

    id = Column(Integer, primary_key=True, index=True)
    domain = Column(String(80), nullable=False)
    skill_id = Column(Integer, ForeignKey("skills.id"), nullable=True)
    question_text = Column(Text, nullable=False)
    options = Column(JSON, default=list)
    correct_index = Column(Integer, default=0)

    skill = relationship("Skill")


class DiagnosticAttempt(Base):
    __tablename__ = "diagnostic_attempts"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    score = Column(Integer, default=0)
    total = Column(Integer, default=0)
    percentage = Column(Float, default=0)
    level = Column(String(30), default="Beginner")
    answers = Column(JSON, default=list)
    attempted_at = Column(DateTime, default=datetime.utcnow)

    employee = relationship("Employee")


class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    skill_id = Column(Integer, ForeignKey("skills.id"), nullable=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=True)
    program_id = Column(Integer, ForeignKey("programs.id"), nullable=True)
    reason = Column(String(255), nullable=True)
    priority = Column(Enum(PriorityEnum), default=PriorityEnum.medium)
    created_at = Column(DateTime, default=datetime.utcnow)

    employee = relationship("Employee")
    skill = relationship("Skill")
    course = relationship("Course")
    program = relationship("Program")


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # null = broadcast to all admins
    audience = Column(String(20), default="admin")  # admin | employee | all
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=True)
    type = Column(String(30), default="System")  # System | Training | AI
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class SettingRecord(Base):
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, nullable=False)
    value = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String(120), nullable=False)
    entity = Column(String(80), nullable=True)
    entity_id = Column(Integer, nullable=True)
    details = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
