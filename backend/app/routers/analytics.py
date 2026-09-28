from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, services
from app.deps import require_admin_or_trainer

router = APIRouter(prefix="/api/admin", tags=["analytics"])


@router.get("/analytics/training")
def training_analytics(db: Session = Depends(get_db), _user=Depends(require_admin_or_trainer)):
    total = db.query(models.Employee).count()
    not_started = db.query(models.Employee).filter(
        models.Employee.training_status == models.TrainingStatusEnum.pending).count()
    in_progress = db.query(models.Employee).filter(
        models.Employee.training_status == models.TrainingStatusEnum.in_progress).count()
    completed = db.query(models.Employee).filter(
        models.Employee.training_status == models.TrainingStatusEnum.completed).count()

    attempts = db.query(models.QuizAttempt).all()
    assessment_perf = round(sum(a.percentage for a in attempts) / len(attempts), 1) if attempts else 0.0

    before_after = []
    diag_attempts = db.query(models.DiagnosticAttempt).order_by(models.DiagnosticAttempt.attempted_at).all()
    competency_improvement = 0.0
    if len(diag_attempts) >= 2:
        by_emp = {}
        for a in diag_attempts:
            by_emp.setdefault(a.employee_id, []).append(a.percentage)
        deltas = [v[-1] - v[0] for v in by_emp.values() if len(v) >= 2]
        competency_improvement = round(sum(deltas) / len(deltas), 1) if deltas else 0.0

    return {
        "statusBreakdown": {"notStarted": not_started, "inProgress": in_progress, "completed": completed},
        "competencyImprovement": competency_improvement,
        "trainingCompletion": round(completed / total * 100, 1) if total else 0.0,
        "assessmentPerformance": assessment_perf,
        "totalEmployees": total,
    }


@router.get("/analytics/workforce")
def workforce_analytics(db: Session = Depends(get_db), _user=Depends(require_admin_or_trainer)):
    departments = db.query(models.Department).all()
    dept_comparison = [
        {"department": d.name, "averageCompetency": services.department_avg_competency(db, d.id)}
        for d in departments
    ]
    total = db.query(models.Employee).count()
    critical_gaps = db.query(models.SkillGapSnapshot).filter(
        models.SkillGapSnapshot.priority == models.PriorityEnum.critical).count()
    attempts = db.query(models.QuizAttempt).count()
    return {
        "departmentComparison": dept_comparison,
        "snapshot": {
            "officials": total,
            "averageCompetency": services.overall_avg_competency_pct(db),
            "criticalGaps": critical_gaps,
            "trainingCompletion": services.training_completion_pct(db),
            "assessmentCompletion": round(attempts / total * 100, 1) if total else 0.0,
        },
        "categoryAverages": services.category_avg_competency(db),
    }


@router.get("/analytics/assessment")
def assessment_analytics(db: Session = Depends(get_db), _user=Depends(require_admin_or_trainer)):
    quizzes_generated = db.query(models.Quiz).count()
    mcqs_generated = db.query(models.QuizQuestion).count()
    attempts = db.query(models.QuizAttempt).order_by(models.QuizAttempt.attempted_at.desc()).limit(50).all()
    avg_score = round(sum(a.percentage for a in attempts) / len(attempts), 1) if attempts else 0.0
    total_employees = db.query(models.Employee).count()
    distinct_attempted = db.query(models.QuizAttempt.employee_id).distinct().count()
    completion = round(distinct_attempted / total_employees * 100, 1) if total_employees else 0.0
    return {
        "quizzesGenerated": quizzes_generated, "mcqsGenerated": mcqs_generated,
        "averageQuizScore": avg_score, "assessmentCompletion": completion,
        "results": [
            {"employee": a.employee.name if a.employee else "Unknown", "quiz": a.quiz.title if a.quiz else "—",
             "score": a.score, "total": a.total, "percentage": a.percentage, "attemptedAt": a.attempted_at}
            for a in attempts
        ],
    }


@router.get("/reports/{report_type}")
def get_report(report_type: str, db: Session = Depends(get_db), _user=Depends(require_admin_or_trainer)):
    if report_type == "workforce-competency":
        return {"type": report_type, "categoryAverages": services.category_avg_competency(db),
                "overallAverage": services.overall_avg_competency_pct(db),
                "totalEmployees": db.query(models.Employee).count()}
    if report_type == "skill-gap":
        gaps = db.query(models.SkillGapSnapshot).filter(models.SkillGapSnapshot.gap > 0).all()
        by_priority = {}
        for g in gaps:
            by_priority[g.priority.value] = by_priority.get(g.priority.value, 0) + 1
        return {"type": report_type, "totalGaps": len(gaps), "byPriority": by_priority}
    if report_type == "training":
        total = db.query(models.Employee).count()
        completed = db.query(models.Employee).filter(
            models.Employee.training_status == models.TrainingStatusEnum.completed).count()
        return {"type": report_type, "totalEmployees": total, "completed": completed,
                "completionRate": round(completed / total * 100, 1) if total else 0.0}
    if report_type == "assessment":
        attempts = db.query(models.QuizAttempt).all()
        return {"type": report_type, "totalAttempts": len(attempts),
                "averageScore": round(sum(a.percentage for a in attempts) / len(attempts), 1) if attempts else 0.0}
    if report_type == "department":
        departments = db.query(models.Department).all()
        return {"type": report_type, "departments": [
            {"name": d.name, "officials": db.query(models.Employee).filter(
                models.Employee.department_id == d.id).count(),
             "averageCompetency": services.department_avg_competency(db, d.id)}
            for d in departments
        ]}
    if report_type == "ai-insights":
        from app.routers.ai import build_workforce_insights
        return {"type": report_type, "insights": build_workforce_insights(db)}
    raise HTTPException(status_code=404, detail="Unknown report type")
