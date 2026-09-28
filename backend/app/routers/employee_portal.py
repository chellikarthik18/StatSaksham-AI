from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas, services
from app.deps import require_employee
from app.seed_data import DIAGNOSTIC_QUESTIONS
from app.utils.quiz_generator import generate_quiz_questions

router = APIRouter(prefix="/api/employee", tags=["employee-portal"])


def _get_employee(db: Session, user: models.User) -> models.Employee:
    emp = db.query(models.Employee).filter(models.Employee.user_id == user.id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="No employee profile linked to this account")
    return emp


# ---------- Profile ----------
@router.get("/profile")
def get_profile(db: Session = Depends(get_db), user=Depends(require_employee)):
    emp = _get_employee(db, user)
    return {
        "id": emp.id, "employeeId": emp.employee_code, "name": emp.name, "email": emp.email,
        "department": emp.department.name if emp.department else None,
        "designation": emp.designation, "phone": emp.phone, "education": emp.education,
        "experienceYears": emp.experience_years, "currentAssignment": emp.current_assignment,
        "previousTraining": emp.previous_training,
    }


@router.put("/profile")
def update_profile(payload: schemas.ProfileUpdate, db: Session = Depends(get_db), user=Depends(require_employee)):
    emp = _get_employee(db, user)
    data = payload.model_dump(exclude_unset=True)
    if "department" in data and data["department"]:
        dept = services.get_or_create_department(db, data.pop("department"))
        emp.department_id = dept.id
    for field in ["name", "designation", "email", "phone", "education", "experience_years",
                  "current_assignment", "previous_training"]:
        if field in data and data[field] is not None:
            setattr(emp, field, data[field])
    db.commit()
    return get_profile(db=db, user=user)


# ---------- Skills ----------
def _ensure_baseline_skills(db: Session, emp: models.Employee):
    if emp.skills:
        return
    for skill in db.query(models.Skill).all():
        db.add(models.EmployeeSkill(employee_id=emp.id, skill_id=skill.id, current_level=0, required_level=2))
    db.commit()


@router.get("/skills")
def get_skills(db: Session = Depends(get_db), user=Depends(require_employee)):
    emp = _get_employee(db, user)
    _ensure_baseline_skills(db, emp)
    db.refresh(emp)
    return [
        {"skillId": s.skill_id, "domain": s.skill.category, "name": s.skill.name,
         "currentLevel": s.current_level, "requiredLevel": s.required_level,
         "gap": max(0, s.required_level - s.current_level)}
        for s in emp.skills
    ]


@router.put("/skills")
def update_skills(payload: schemas.SkillsBulkUpdate, db: Session = Depends(get_db), user=Depends(require_employee)):
    emp = _get_employee(db, user)
    ids = {u.skill_id: u.current_level for u in payload.updates}
    rows = db.query(models.EmployeeSkill).filter(
        models.EmployeeSkill.employee_id == emp.id, models.EmployeeSkill.skill_id.in_(ids.keys())
    ).all()
    for row in rows:
        row.current_level = max(0, min(3, ids[row.skill_id]))
    db.commit()
    return get_skills(db=db, user=user)


@router.post("/skills/analyze")
def analyze_skills(db: Session = Depends(get_db), user=Depends(require_employee)):
    emp = _get_employee(db, user)
    _ensure_baseline_skills(db, emp)
    snapshots = services.run_skill_gap_analysis(db, employee_id=emp.id)
    gaps = [s for s in snapshots if s.gap > 0]
    return {
        "gapsIdentified": len(gaps),
        "topGapSkillIds": [s.skill_id for s in sorted(gaps, key=lambda x: -x.gap)[:4]],
        "items": [{"skill": s.skill.name, "gap": s.gap, "priority": s.priority.value} for s in gaps],
    }


# ---------- Diagnostic assessment ----------
def _ensure_diagnostic_bank(db: Session):
    if db.query(models.DiagnosticQuestion).count() > 0:
        return
    for q in DIAGNOSTIC_QUESTIONS:
        skill = db.query(models.Skill).filter(models.Skill.name == q["skill"]).first()
        db.add(models.DiagnosticQuestion(
            domain=q["domain"], skill_id=skill.id if skill else None,
            question_text=q["question_text"], options=q["options"], correct_index=q["correct_index"],
        ))
    db.commit()


@router.get("/diagnostic/questions")
def get_diagnostic_questions(db: Session = Depends(get_db), _user=Depends(require_employee)):
    _ensure_diagnostic_bank(db)
    rows = db.query(models.DiagnosticQuestion).order_by(models.DiagnosticQuestion.id).all()
    return [
        {"id": q.id, "domain": q.domain, "skill": q.skill.name if q.skill else None,
         "question": q.question_text, "options": q.options}
        for q in rows
    ]


@router.post("/diagnostic/submit")
def submit_diagnostic(payload: schemas.DiagnosticSubmit, db: Session = Depends(get_db), user=Depends(require_employee)):
    emp = _get_employee(db, user)
    _ensure_diagnostic_bank(db)
    questions = db.query(models.DiagnosticQuestion).order_by(models.DiagnosticQuestion.id).all()
    if len(payload.answers) != len(questions):
        raise HTTPException(status_code=400, detail="Answer count does not match question count")

    score = 0
    per_skill_correct = {}
    for q, ans in zip(questions, payload.answers):
        is_correct = ans is not None and int(ans) == q.correct_index
        if is_correct:
            score += 1
        if q.skill_id:
            per_skill_correct.setdefault(q.skill_id, []).append(is_correct)

    total = len(questions)
    percentage = round(score / total * 100, 1) if total else 0
    level = "Advanced" if percentage >= 80 else "Intermediate" if percentage >= 60 else "Developing" if percentage >= 35 else "Beginner"

    attempt = models.DiagnosticAttempt(
        employee_id=emp.id, score=score, total=total, percentage=percentage, level=level,
        answers=payload.answers, attempted_at=datetime.utcnow(),
    )
    db.add(attempt)

    # Feed results back into the employee's competency profile (current_level 0-3).
    _ensure_baseline_skills(db, emp)
    for skill_id, results in per_skill_correct.items():
        pct = sum(1 for r in results if r) / len(results)
        new_level = 3 if pct >= 0.8 else 2 if pct >= 0.5 else 1 if pct > 0 else 0
        row = db.query(models.EmployeeSkill).filter(
            models.EmployeeSkill.employee_id == emp.id, models.EmployeeSkill.skill_id == skill_id
        ).first()
        if row:
            row.current_level = max(row.current_level, new_level)

    services.create_notification(db, "Diagnostic assessment completed",
                                  f"{emp.name} scored {percentage}% ({level}).",
                                  type_="AI", audience="admin")
    db.commit()
    services.run_skill_gap_analysis(db, employee_id=emp.id)
    return {"score": score, "total": total, "percentage": percentage, "level": level}


@router.get("/diagnostic/result")
def latest_diagnostic_result(db: Session = Depends(get_db), user=Depends(require_employee)):
    emp = _get_employee(db, user)
    attempt = (
        db.query(models.DiagnosticAttempt)
        .filter(models.DiagnosticAttempt.employee_id == emp.id)
        .order_by(models.DiagnosticAttempt.attempted_at.desc())
        .first()
    )
    if not attempt:
        return None
    return {"score": attempt.score, "total": attempt.total, "percentage": attempt.percentage,
            "level": attempt.level, "attemptedAt": attempt.attempted_at}


# ---------- Recommendations & Learning Path ----------
@router.get("/recommendations")
def recommendations(db: Session = Depends(get_db), user=Depends(require_employee)):
    emp = _get_employee(db, user)
    gaps = (
        db.query(models.SkillGapSnapshot)
        .filter(models.SkillGapSnapshot.employee_id == emp.id, models.SkillGapSnapshot.gap > 0)
        .order_by(models.SkillGapSnapshot.gap.desc())
        .all()
    )
    skill_ids = [g.skill_id for g in gaps]
    if skill_ids:
        courses = db.query(models.Course).filter(models.Course.skill_id.in_(skill_ids)).all()
    else:
        courses = db.query(models.Course).limit(6).all()

    result = []
    for c in courses:
        enrollment = db.query(models.Enrollment).filter(
            models.Enrollment.employee_id == emp.id, models.Enrollment.course_id == c.id
        ).first()
        result.append({
            "id": c.id, "title": c.title, "provider": c.provider, "type": "IGOT_COURSE",
            "level": c.level, "durationHours": c.duration_hours, "description": c.description,
            "modules": c.modules or [], "skillId": c.skill_id,
            "progress": enrollment.progress if enrollment else 0,
            "status": enrollment.status if enrollment else "Not Started",
            "completedModules": enrollment.completed_modules if enrollment else [],
        })
    return {"hasDiagnostic": bool(gaps) or bool(emp.skills), "gapCount": len(gaps), "courses": result}


@router.get("/learning-path")
def learning_path(db: Session = Depends(get_db), user=Depends(require_employee)):
    emp = _get_employee(db, user)
    enrollments = db.query(models.Enrollment).filter(models.Enrollment.employee_id == emp.id).all()
    items = []
    for e in enrollments:
        title = e.course.title if e.course else (e.program.title if e.program else "—")
        provider = e.course.provider if e.course else (e.program.venue_mode if e.program else "—")
        duration = e.course.duration_hours if e.course else None
        items.append({
            "enrollmentId": e.id, "itemType": e.item_type, "itemId": e.course_id or e.program_id,
            "title": title, "provider": provider, "durationHours": duration,
            "status": e.status, "progress": e.progress, "completedModules": e.completed_modules or [],
        })
    total = len(items) or 1
    overall = round(sum(i["progress"] for i in items) / total, 1) if items else 0
    return {
        "overallProgress": overall,
        "completed": len([i for i in items if i["status"] == "Completed"]),
        "inProgress": len([i for i in items if i["status"] == "In Progress"]),
        "notStarted": len([i for i in items if i["status"] == "Not Started"]),
        "items": items,
    }


@router.post("/learning-path/enroll/{course_id}")
def enroll_course(course_id: int, db: Session = Depends(get_db), user=Depends(require_employee)):
    emp = _get_employee(db, user)
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    enrollment = db.query(models.Enrollment).filter(
        models.Enrollment.employee_id == emp.id, models.Enrollment.course_id == course_id
    ).first()
    if not enrollment:
        enrollment = models.Enrollment(employee_id=emp.id, item_type="course", course_id=course_id,
                                        status="In Progress", progress=0, completed_modules=[])
        db.add(enrollment)
        db.commit()
        db.refresh(enrollment)
    return {"enrollmentId": enrollment.id, "status": enrollment.status, "progress": enrollment.progress}


@router.post("/learning-path/{course_id}/complete-module")
def complete_module(course_id: int, payload: schemas.ModuleCompleteRequest, db: Session = Depends(get_db),
                     user=Depends(require_employee)):
    emp = _get_employee(db, user)
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    enrollment = db.query(models.Enrollment).filter(
        models.Enrollment.employee_id == emp.id, models.Enrollment.course_id == course_id
    ).first()
    if not enrollment:
        enrollment = models.Enrollment(employee_id=emp.id, item_type="course", course_id=course_id,
                                        status="In Progress", progress=0, completed_modules=[])
        db.add(enrollment)
        db.flush()

    completed = set(enrollment.completed_modules or [])
    completed.add(payload.module_index)
    enrollment.completed_modules = sorted(completed)
    total_modules = max(1, len(course.modules or []))
    enrollment.progress = round(len(completed) / total_modules * 100, 1)
    enrollment.status = "Completed" if enrollment.progress >= 100 else "In Progress"
    if enrollment.status == "Completed":
        enrollment.completed_at = datetime.utcnow()
        # Roll up: if all enrollments completed, mark employee's training status too.
        pending = db.query(models.Enrollment).filter(
            models.Enrollment.employee_id == emp.id, models.Enrollment.status != "Completed"
        ).count()
        if pending == 0:
            emp.training_status = models.TrainingStatusEnum.completed
    db.commit()
    return {"status": enrollment.status, "progress": enrollment.progress}


# ---------- Quiz & practice ----------
@router.post("/quiz/generate")
def employee_generate_quiz(payload: schemas.QuizGenerateRequest, db: Session = Depends(get_db),
                            user=Depends(require_employee)):
    emp = _get_employee(db, user)
    material_text = None
    if payload.material_id:
        material = db.query(models.Material).filter(models.Material.id == payload.material_id).first()
        material_text = material.extracted_text if material else None
    topic = payload.topic or "General Skills"
    generated = generate_quiz_questions(material_text, topic, payload.count, payload.difficulty)

    quiz = models.Quiz(title=f"{topic} — {payload.difficulty} Practice", topic=topic,
                        difficulty=payload.difficulty, status="Published", generated_by_ai=True,
                        created_by=user.id)
    db.add(quiz)
    db.flush()
    for g in generated:
        db.add(models.QuizQuestion(quiz_id=quiz.id, question_text=g["question_text"], options=g["options"],
                                    correct_index=g["correct_index"], explanation=g.get("explanation", ""),
                                    topic=topic, difficulty=payload.difficulty, status="Published"))
    db.commit()
    db.refresh(quiz)
    return {
        "quizId": quiz.id, "title": quiz.title,
        "questions": [
            {"id": q.id, "question": q.question_text, "options": q.options}
            for q in quiz.questions
        ],
    }


@router.post("/quiz/submit")
def employee_submit_quiz(payload: schemas.QuizAttemptSubmit, db: Session = Depends(get_db),
                          user=Depends(require_employee)):
    emp = _get_employee(db, user)
    quiz = db.query(models.Quiz).filter(models.Quiz.id == payload.quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    questions = quiz.questions
    if len(payload.answers) != len(questions):
        raise HTTPException(status_code=400, detail="Answer count does not match question count")
    score = sum(1 for q, a in zip(questions, payload.answers) if a is not None and int(a) == q.correct_index)
    total = len(questions)
    percentage = round(score / total * 100, 1) if total else 0

    attempt = models.QuizAttempt(quiz_id=quiz.id, employee_id=emp.id, score=score, total=total,
                                  percentage=percentage, answers=payload.answers)
    db.add(attempt)
    services.create_notification(db, f"{quiz.topic or 'Practice'} quiz completed — {percentage}%",
                                  type_="AI", audience="admin")
    db.commit()
    return {"score": score, "total": total, "percentage": percentage}


# ---------- Notifications & competency growth ----------
@router.get("/notifications")
def employee_notifications(db: Session = Depends(get_db), _user=Depends(require_employee)):
    rows = (
        db.query(models.Notification)
        .filter(models.Notification.audience.in_(["employee", "all"]))
        .order_by(models.Notification.created_at.desc())
        .limit(50)
        .all()
    )
    return [{"id": n.id, "title": n.title, "message": n.message, "type": n.type,
             "isRead": n.is_read, "createdAt": n.created_at} for n in rows]


@router.get("/competency-growth")
def competency_growth(db: Session = Depends(get_db), user=Depends(require_employee)):
    emp = _get_employee(db, user)
    attempts = (
        db.query(models.DiagnosticAttempt)
        .filter(models.DiagnosticAttempt.employee_id == emp.id)
        .order_by(models.DiagnosticAttempt.attempted_at)
        .all()
    )
    completed_courses = db.query(models.Enrollment).filter(
        models.Enrollment.employee_id == emp.id, models.Enrollment.status == "Completed"
    ).count()
    skills = [
        {"name": s.skill.name, "domain": s.skill.category, "currentLevel": s.current_level,
         "requiredLevel": s.required_level}
        for s in emp.skills
    ]
    future_skills = db.query(models.EmergingSkill).order_by(models.EmergingSkill.future_demand.desc()).limit(6).all()
    return {
        "history": [{"percentage": a.percentage, "level": a.level, "attemptedAt": a.attempted_at} for a in attempts],
        "completedCourses": completed_courses,
        "skills": skills,
        "futureSkills": [f.name for f in future_skills],
    }
