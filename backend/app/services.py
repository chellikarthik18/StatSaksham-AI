"""Shared aggregation / business-logic helpers used across routers."""
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import func

from app import models


def level_pct(level: Optional[float]) -> float:
    """Convert a 0-3 proficiency level into a 0-100% figure."""
    if not level:
        return 0.0
    return round(min(3, max(0, level)) / 3 * 100, 1)


def employee_avg_competency_pct(db: Session, employee_id: int) -> float:
    rows = db.query(models.EmployeeSkill).filter(models.EmployeeSkill.employee_id == employee_id).all()
    if not rows:
        return 0.0
    return round(sum(level_pct(r.current_level) for r in rows) / len(rows), 1)


def overall_avg_competency_pct(db: Session) -> float:
    rows = db.query(models.EmployeeSkill).all()
    if not rows:
        return 0.0
    return round(sum(level_pct(r.current_level) for r in rows) / len(rows), 1)


def category_avg_competency(db: Session) -> dict:
    result = {}
    for category in ["Statistical", "Technical", "Digital Governance", "Behavioural"]:
        rows = (
            db.query(models.EmployeeSkill)
            .join(models.Skill, models.EmployeeSkill.skill_id == models.Skill.id)
            .filter(models.Skill.category == category)
            .all()
        )
        result[category] = round(sum(level_pct(r.current_level) for r in rows) / len(rows), 1) if rows else 0.0
    return result


def department_avg_competency(db: Session, department_id: int) -> float:
    rows = (
        db.query(models.EmployeeSkill)
        .join(models.Employee, models.EmployeeSkill.employee_id == models.Employee.id)
        .filter(models.Employee.department_id == department_id)
        .all()
    )
    if not rows:
        return 0.0
    return round(sum(level_pct(r.current_level) for r in rows) / len(rows), 1)


def department_training_completion(db: Session, department_id: int) -> float:
    total = db.query(models.Employee).filter(models.Employee.department_id == department_id).count()
    if not total:
        return 0.0
    completed = (
        db.query(models.Employee)
        .filter(models.Employee.department_id == department_id,
                models.Employee.training_status == models.TrainingStatusEnum.completed)
        .count()
    )
    return round(completed / total * 100, 1)


def training_completion_pct(db: Session) -> float:
    total = db.query(models.Employee).count()
    if not total:
        return 0.0
    completed = db.query(models.Employee).filter(
        models.Employee.training_status == models.TrainingStatusEnum.completed
    ).count()
    return round(completed / total * 100, 1)


def compute_priority(gap: int) -> models.PriorityEnum:
    if gap >= 3:
        return models.PriorityEnum.critical
    if gap == 2:
        return models.PriorityEnum.high
    if gap == 1:
        return models.PriorityEnum.medium
    return models.PriorityEnum.low


def run_skill_gap_analysis(db: Session, employee_id: Optional[int] = None) -> list:
    """(Re)compute skill-gap snapshots for one employee, or all employees if None."""
    query = db.query(models.EmployeeSkill)
    if employee_id:
        query = query.filter(models.EmployeeSkill.employee_id == employee_id)
    rows = query.all()

    # clear old snapshots for the affected employees
    affected_ids = {r.employee_id for r in rows}
    if affected_ids:
        db.query(models.SkillGapSnapshot).filter(
            models.SkillGapSnapshot.employee_id.in_(affected_ids)
        ).delete(synchronize_session=False)

    created = []
    for r in rows:
        gap = max(0, (r.required_level or 0) - (r.current_level or 0))
        snap = models.SkillGapSnapshot(
            employee_id=r.employee_id, skill_id=r.skill_id,
            current_level=r.current_level, required_level=r.required_level,
            gap=gap, priority=compute_priority(gap), computed_at=datetime.utcnow(),
        )
        db.add(snap)
        created.append(snap)
    db.commit()
    for s in created:
        db.refresh(s)
    return created


def get_or_create_skill(db: Session, name: str, category: str = "Technical") -> models.Skill:
    skill = db.query(models.Skill).filter(func.lower(models.Skill.name) == name.lower()).first()
    if skill:
        return skill
    skill = models.Skill(name=name, category=category)
    db.add(skill)
    db.flush()
    return skill


def get_or_create_department(db: Session, name: str) -> models.Department:
    dept = db.query(models.Department).filter(func.lower(models.Department.name) == name.lower()).first()
    if dept:
        return dept
    dept = models.Department(name=name)
    db.add(dept)
    db.flush()
    return dept


def create_notification(db: Session, title: str, message: str = "", type_: str = "System",
                         audience: str = "admin", user_id: Optional[int] = None, commit: bool = True):
    note = models.Notification(title=title, message=message, type=type_, audience=audience, user_id=user_id)
    db.add(note)
    if commit:
        db.commit()
        db.refresh(note)
    return note
