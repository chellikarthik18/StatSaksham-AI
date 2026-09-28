from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, services
from app.deps import require_admin_or_trainer

router = APIRouter(prefix="/api/admin", tags=["dashboard"])


@router.get("/dashboard")
def get_dashboard(db: Session = Depends(get_db), _user=Depends(require_admin_or_trainer)):
    total_officials = db.query(models.Employee).count()
    avg_competency = services.overall_avg_competency_pct(db)
    critical_gaps = db.query(models.SkillGapSnapshot).filter(
        models.SkillGapSnapshot.priority == models.PriorityEnum.critical
    ).count()
    skill_gaps_identified = db.query(models.SkillGapSnapshot).filter(
        models.SkillGapSnapshot.gap > 0
    ).count()
    training_completion = services.training_completion_pct(db)
    depts_needing_training = db.query(models.Department).join(
        models.Employee, models.Employee.department_id == models.Department.id
    ).filter(models.Employee.training_status != models.TrainingStatusEnum.completed).distinct().count()
    employees_needing_assessment = db.query(models.Employee).outerjoin(
        models.EmployeeSkill, models.EmployeeSkill.employee_id == models.Employee.id
    ).filter(models.EmployeeSkill.id.is_(None)).count()
    emerging_skills_detected = db.query(models.EmergingSkill).count()

    return {
        "totalOfficials": total_officials,
        "averageCompetency": avg_competency,
        "skillGapsIdentified": skill_gaps_identified,
        "trainingCompletion": training_completion,
        "competencyDistribution": services.category_avg_competency(db),
        "priorityActions": {
            "criticalSkillGaps": critical_gaps,
            "departmentsRequiringTraining": depts_needing_training,
            "employeesNeedingAssessment": employees_needing_assessment,
            "emergingSkillsDetected": emerging_skills_detected,
        },
    }
