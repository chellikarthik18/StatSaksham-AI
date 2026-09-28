"""
Idempotent seed script for StatSaksham AI.

Usage (from the backend/ directory, with the virtualenv activated and the
MySQL database already created — see README.md):

    python seed.py

Running it multiple times is safe: existing rows (matched by natural key)
are left untouched or simply not duplicated.
"""
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.database import Base, engine, SessionLocal
from app import models
from app.security import hash_password
from app.seed_data import (
    DEPARTMENTS, SKILLS, DESIGNATIONS, MOCK_COURSES, MOCK_PROGRAMS,
    DIAGNOSTIC_QUESTIONS, EMERGING_SKILLS_SEED,
)

random.seed(42)


def get_or_create(db, model, defaults=None, **kwargs):
    instance = db.query(model).filter_by(**kwargs).first()
    if instance:
        return instance, False
    params = {**kwargs, **(defaults or {})}
    instance = model(**params)
    db.add(instance)
    db.flush()
    return instance, True


def seed_departments(db):
    depts = {}
    for name in DEPARTMENTS:
        d, _ = get_or_create(db, models.Department, name=name)
        depts[name] = d
    db.commit()
    print(f"Departments: {len(depts)} ready")
    return depts


def seed_skills(db):
    skills = {}
    for s in SKILLS:
        sk, _ = get_or_create(db, models.Skill, name=s["name"], category=s["category"])
        skills[s["name"]] = sk
    db.commit()
    print(f"Skills: {len(skills)} ready")
    return skills


def seed_framework(db, skills):
    count = 0
    for designation in DESIGNATIONS:
        for skill_name, skill in list(skills.items())[:6]:
            existing = db.query(models.RoleCompetencyRequirement).filter_by(
                job_role=designation, skill_id=skill.id
            ).first()
            if existing:
                continue
            db.add(models.RoleCompetencyRequirement(
                job_role=designation, skill_id=skill.id,
                required_level=random.choice([2, 2, 3]), status="Active",
            ))
            count += 1
    db.commit()
    print(f"Competency framework requirements: +{count}")


def seed_users_and_employees(db, depts):
    demo_accounts = [
        {"email": "admin@statsaksham.gov.in", "password": "Admin@123", "name": "System Administrator",
         "role": models.RoleEnum.admin, "make_employee": False},
        {"email": "trainer@statsaksham.gov.in", "password": "Trainer@123", "name": "Lead Trainer",
         "role": models.RoleEnum.trainer, "make_employee": False},
        {"email": "employee@statsaksham.gov.in", "password": "Employee@123", "name": "Demo Employee",
         "role": models.RoleEnum.employee, "make_employee": True, "employee_code": "EMP00123",
         "department": "Economic Statistics", "designation": "Statistical Officer"},
    ]
    created_users = {}
    for acc in demo_accounts:
        user = db.query(models.User).filter(models.User.email == acc["email"]).first()
        if not user:
            user = models.User(email=acc["email"], full_name=acc["name"],
                                hashed_password=hash_password(acc["password"]), role=acc["role"])
            db.add(user)
            db.flush()
        created_users[acc["email"]] = user

        if acc.get("make_employee"):
            emp = db.query(models.Employee).filter(models.Employee.user_id == user.id).first()
            if not emp:
                emp = db.query(models.Employee).filter(
                    models.Employee.employee_code == acc["employee_code"]
                ).first()
            if not emp:
                dept = depts.get(acc["department"])
                emp = models.Employee(
                    user_id=user.id, employee_code=acc["employee_code"], name=acc["name"],
                    email=acc["email"], department_id=dept.id if dept else None,
                    designation=acc["designation"], experience_years=3,
                    training_status=models.TrainingStatusEnum.in_progress,
                )
                db.add(emp)
            elif not emp.user_id:
                emp.user_id = user.id
    db.commit()
    print("Demo accounts ready: admin@statsaksham.gov.in / trainer@statsaksham.gov.in / employee@statsaksham.gov.in")

    # A handful of extra employees (no login) for realistic workforce analytics.
    sample_names = [
        "Aarav Sharma", "Priya Nair", "Rohit Verma", "Ananya Iyer", "Karan Mehta",
        "Sneha Reddy", "Vikram Singh", "Neha Gupta", "Arjun Rao", "Divya Kulkarni",
    ]
    dept_list = list(depts.values())
    added = 0
    for i, name in enumerate(sample_names):
        code = f"EMP{2000 + i}"
        if db.query(models.Employee).filter(models.Employee.employee_code == code).first():
            continue
        dept = dept_list[i % len(dept_list)]
        emp = models.Employee(
            employee_code=code, name=name, email=f"{code.lower()}@statsaksham.gov.in",
            department_id=dept.id, designation=random.choice(DESIGNATIONS),
            experience_years=random.randint(1, 15),
            training_status=random.choice(list(models.TrainingStatusEnum)),
        )
        db.add(emp)
        added += 1
    db.commit()
    print(f"Sample workforce employees: +{added}")


def seed_employee_skills(db, skills):
    employees = db.query(models.Employee).all()
    skill_list = list(skills.values())
    count = 0
    for emp in employees:
        existing_ids = {s.skill_id for s in emp.skills}
        for sk in skill_list:
            if sk.id in existing_ids:
                continue
            db.add(models.EmployeeSkill(
                employee_id=emp.id, skill_id=sk.id,
                current_level=random.choice([0, 0, 1, 1, 2, 2, 3]),
                required_level=random.choice([2, 2, 3]),
            ))
            count += 1
    db.commit()
    print(f"Employee competency records: +{count}")


def seed_courses(db, skills):
    created = 0
    for item in MOCK_COURSES:
        if db.query(models.Course).filter(models.Course.title == item["title"]).first():
            continue
        skill = skills.get(item["skill"])
        db.add(models.Course(
            title=item["title"], provider=item["provider"], category=item["category"],
            duration_hours=item["duration_hours"], level=item["level"], description=item["description"],
            skill_id=skill.id if skill else None, modules=item["modules"], status="Synced",
        ))
        created += 1
    db.commit()
    print(f"iGOT courses: +{created}")


def seed_programs(db):
    created = 0
    for item in MOCK_PROGRAMS:
        if db.query(models.Program).filter(models.Program.title == item["title"]).first():
            continue
        db.add(models.Program(**item))
        created += 1
    db.commit()
    print(f"NSSTA/TPAC programmes: +{created}")


def seed_diagnostic_questions(db, skills):
    if db.query(models.DiagnosticQuestion).count() > 0:
        print("Diagnostic questions already present, skipping")
        return
    for q in DIAGNOSTIC_QUESTIONS:
        skill = skills.get(q["skill"])
        db.add(models.DiagnosticQuestion(
            domain=q["domain"], skill_id=skill.id if skill else None,
            question_text=q["question_text"], options=q["options"], correct_index=q["correct_index"],
        ))
    db.commit()
    print(f"Diagnostic questions: +{len(DIAGNOSTIC_QUESTIONS)}")


def seed_emerging_skills(db):
    created = 0
    for item in EMERGING_SKILLS_SEED:
        if db.query(models.EmergingSkill).filter(models.EmergingSkill.name == item["name"]).first():
            continue
        db.add(models.EmergingSkill(**item))
        created += 1
    db.commit()
    print(f"Emerging skills: +{created}")


def seed_learning_paths(db):
    if db.query(models.LearningPath).count() > 0:
        print("Learning paths already present, skipping")
        return
    courses = db.query(models.Course).limit(3).all()
    if not courses:
        return
    lp = models.LearningPath(title="Foundational Data Skills Path",
                              description="Core statistical + technical foundation for new officials.",
                              status="Draft")
    db.add(lp)
    db.flush()
    for i, c in enumerate(courses):
        db.add(models.LearningPathItem(learning_path_id=lp.id, item_type="course", course_id=c.id, sequence=i))
    demo_emp = db.query(models.Employee).filter(models.Employee.employee_code == "EMP00123").first()
    if demo_emp:
        db.add(models.LearningPathAssignment(learning_path_id=lp.id, employee_id=demo_emp.id, progress=20,
                                              status="In Progress"))
    db.commit()
    print("Learning path: +1 (Foundational Data Skills Path)")


def seed_sample_quiz(db):
    if db.query(models.Quiz).count() > 0:
        print("Quizzes already present, skipping")
        return
    quiz = models.Quiz(title="Data Quality — Medium Quiz", topic="Data Quality", difficulty="Medium",
                        status="Published", generated_by_ai=True)
    db.add(quiz)
    db.flush()
    db.add(models.QuizQuestion(
        quiz_id=quiz.id, question_text="Which is a core data-quality dimension?",
        options=["Accuracy", "Screen brightness", "CPU speed", "Font size"], correct_index=0,
        explanation="Accuracy, completeness, timeliness and consistency are core dimensions.",
        topic="Data Quality", difficulty="Medium", status="Published",
    ))
    db.commit()
    print("Sample quiz: +1")


def seed_notifications(db):
    if db.query(models.Notification).count() > 0:
        print("Notifications already present, skipping")
        return
    db.add_all([
        models.Notification(title="Welcome to STATSAKHAM AI", message="Platform seeded with demo data.",
                             type="System", audience="admin"),
        models.Notification(title="Diagnostic assessment available", message="Complete your diagnostic to unlock recommendations.",
                             type="Training", audience="employee"),
    ])
    db.commit()
    print("Notifications: +2")


def main():
    print("Creating tables (if not present)...")
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        depts = seed_departments(db)
        skills = seed_skills(db)
        seed_framework(db, skills)
        seed_users_and_employees(db, depts)
        seed_employee_skills(db, skills)
        seed_courses(db, skills)
        seed_programs(db)
        seed_diagnostic_questions(db, skills)
        seed_emerging_skills(db)
        seed_learning_paths(db)
        seed_sample_quiz(db)
        seed_notifications(db)
        print("\nSeed complete. You can re-run this script safely at any time.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
