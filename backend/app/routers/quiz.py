from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas, services
from app.deps import require_admin_or_trainer
from app.utils.quiz_generator import generate_quiz_questions

router = APIRouter(tags=["quiz"])


def _question_out(q: models.QuizQuestion) -> dict:
    return {
        "id": q.id, "quizId": q.quiz_id, "question": q.question_text, "options": q.options,
        "correctIndex": q.correct_index, "explanation": q.explanation, "topic": q.topic,
        "difficulty": q.difficulty, "type": q.question_type, "status": q.status,
    }


def _quiz_out(quiz: models.Quiz) -> dict:
    return {
        "id": quiz.id, "title": quiz.title, "topic": quiz.topic, "difficulty": quiz.difficulty,
        "status": quiz.status, "materialId": quiz.material_id, "createdAt": quiz.created_at,
        "questions": [_question_out(q) for q in quiz.questions],
    }


@router.post("/api/ai/generate-quiz")
def ai_generate_quiz(payload: schemas.QuizGenerateRequest, db: Session = Depends(get_db),
                      user=Depends(require_admin_or_trainer)):
    material = None
    material_text = None
    if payload.material_id:
        material = db.query(models.Material).filter(models.Material.id == payload.material_id).first()
        if not material:
            raise HTTPException(status_code=404, detail="Learning material not found")
        material_text = material.extracted_text

    topic = payload.topic or (material.topic if material else None) or "General Skills"
    generated = generate_quiz_questions(material_text, topic, payload.count, payload.difficulty)
    if not generated:
        raise HTTPException(status_code=422, detail="Could not generate questions for this input")

    quiz = models.Quiz(
        title=f"{topic} — {payload.difficulty} Quiz", material_id=material.id if material else None,
        topic=topic, difficulty=payload.difficulty, status="Draft", generated_by_ai=True, created_by=user.id,
    )
    db.add(quiz)
    db.flush()
    for g in generated:
        db.add(models.QuizQuestion(
            quiz_id=quiz.id, question_text=g["question_text"], options=g["options"],
            correct_index=g["correct_index"], explanation=g.get("explanation", ""),
            topic=topic, difficulty=payload.difficulty, status="Draft",
        ))
    db.commit()
    db.refresh(quiz)
    return _quiz_out(quiz)


@router.get("/api/admin/quizzes")
def list_quizzes(db: Session = Depends(get_db), _user=Depends(require_admin_or_trainer)):
    rows = db.query(models.Quiz).order_by(models.Quiz.id.desc()).all()
    return [_quiz_out(q) for q in rows]


@router.put("/api/admin/quizzes/{quiz_id}/publish")
def publish_quiz(quiz_id: int, db: Session = Depends(get_db), _user=Depends(require_admin_or_trainer)):
    quiz = db.query(models.Quiz).filter(models.Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    quiz.status = "Published"
    for q in quiz.questions:
        q.status = "Published"
    db.commit()
    services.create_notification(db, f"Quiz published: {quiz.title}", type_="Training", audience="employee")
    db.refresh(quiz)
    return _quiz_out(quiz)


@router.delete("/api/admin/quizzes/{quiz_id}")
def delete_quiz(quiz_id: int, db: Session = Depends(get_db), _user=Depends(require_admin_or_trainer)):
    quiz = db.query(models.Quiz).filter(models.Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    db.delete(quiz)
    db.commit()
    return {"status": "deleted"}


# ---------- Question bank (flat view across all quizzes) ----------
@router.get("/api/admin/questions")
def list_question_bank(search: str = "", difficulty: str = "", db: Session = Depends(get_db),
                        _user=Depends(require_admin_or_trainer)):
    q = db.query(models.QuizQuestion)
    if search:
        q = q.filter(models.QuizQuestion.question_text.ilike(f"%{search}%"))
    if difficulty:
        q = q.filter(models.QuizQuestion.difficulty == difficulty)
    rows = q.order_by(models.QuizQuestion.id.desc()).limit(500).all()
    return [_question_out(r) for r in rows]


@router.put("/api/admin/questions/{question_id}")
def update_question(question_id: int, payload: schemas.QuizQuestionEdit, db: Session = Depends(get_db),
                     _user=Depends(require_admin_or_trainer)):
    q = db.query(models.QuizQuestion).filter(models.QuizQuestion.id == question_id).first()
    if not q:
        raise HTTPException(status_code=404, detail="Question not found")
    data = payload.model_dump(exclude_unset=True)
    for k, v in data.items():
        field_map = {"question_text": "question_text", "options": "options",
                     "correct_index": "correct_index", "explanation": "explanation", "status": "status"}
        setattr(q, field_map.get(k, k), v)
    db.commit()
    db.refresh(q)
    return _question_out(q)


@router.delete("/api/admin/questions/{question_id}")
def delete_question(question_id: int, db: Session = Depends(get_db), _user=Depends(require_admin_or_trainer)):
    q = db.query(models.QuizQuestion).filter(models.QuizQuestion.id == question_id).first()
    if not q:
        raise HTTPException(status_code=404, detail="Question not found")
    db.delete(q)
    db.commit()
    return {"status": "deleted"}
