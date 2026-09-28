from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, services
from app.deps import require_admin_or_trainer

router = APIRouter(prefix="/api/ai", tags=["ai"])


def build_workforce_insights(db: Session) -> dict:
    """
    Deterministic, data-grounded 'AI insight' summary computed directly from
    the MySQL data (no external AI API required for the demo to work).
    """
    total = db.query(models.Employee).count()
    avg_competency = services.overall_avg_competency_pct(db)
    category_avgs = services.category_avg_competency(db)
    weakest_category = min(category_avgs, key=category_avgs.get) if category_avgs else None

    top_gaps = (
        db.query(models.SkillGapSnapshot)
        .filter(models.SkillGapSnapshot.gap > 0)
        .order_by(models.SkillGapSnapshot.gap.desc())
        .limit(5)
        .all()
    )
    gap_skill_names = list({g.skill.name for g in top_gaps if g.skill})

    emerging = db.query(models.EmergingSkill).order_by(models.EmergingSkill.future_demand.desc()).limit(3).all()

    recommendations = []
    if weakest_category:
        recommendations.append(
            f"Prioritise training investment in {weakest_category} competencies "
            f"(current average {category_avgs[weakest_category]}%)."
        )
    if gap_skill_names:
        recommendations.append(
            f"Highest-priority skill gaps across the workforce: {', '.join(gap_skill_names)}."
        )
    if emerging:
        recommendations.append(
            "Emerging skills to prepare for: " + ", ".join(e.name for e in emerging) + "."
        )
    if not recommendations:
        recommendations.append("No workforce data available yet — add employees and run a skill-gap analysis first.")

    return {
        "totalEmployees": total,
        "averageCompetency": avg_competency,
        "categoryAverages": category_avgs,
        "weakestCategory": weakest_category,
        "priorityGapSkills": gap_skill_names,
        "emergingSkills": [e.name for e in emerging],
        "recommendations": recommendations,
    }


@router.post("/workforce-insights")
def workforce_insights(db: Session = Depends(get_db), _user=Depends(require_admin_or_trainer)):
    return build_workforce_insights(db)
