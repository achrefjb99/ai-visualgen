from typing import Literal
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlmodel import Session, select

from app.database import get_session
from app.models.learning import QuizAttempt
from app.models.shared import Course, User, UserRole
from app.modules.module3_tutor.service import quiz

router = APIRouter(prefix="/assessment", tags=["Module 4 - Quiz and progress"])


class QuizRequest(BaseModel):
    course_id: int
    topic: str = Field(min_length=1, max_length=150)
    difficulty: Literal["easy", "medium", "hard"] = "easy"
    count: int = Field(default=5, ge=1, le=10)


class QuizQuestion(BaseModel):
    type: Literal["mcq", "true_false", "short"]
    question: str
    options: list[str] = Field(default_factory=list)
    answer: str
    explanation: str = "Révise cette idée dans ta leçon."


class QuizSource(BaseModel):
    id: int
    label: str
    score: float
    text: str


class QuizResponse(BaseModel):
    topic: str
    questions: list[QuizQuestion]
    sources: list[QuizSource]
    generation_mode: Literal["ai", "local"]


class QuizGradeItem(BaseModel):
    correct: bool
    points: int
    feedback: str
    answer: str


class QuizGradeResponse(BaseModel):
    attempt_id: int
    points: int
    results: list[QuizGradeItem]
    weak_spots: list[str]
    boosters: list[str]
    badges: list[str]


class TopicMastery(BaseModel):
    topic: str
    accuracy: int


class RecentAttempt(BaseModel):
    id: int
    course_id: int
    child_id: int | None = None
    topic: str
    points: int
    correct_count: int
    question_count: int
    created_at: datetime


class ProgressResponse(BaseModel):
    course_id: int
    child_id: int | None = None
    attempts: int
    points: int
    accuracy: int
    encouragement: str
    recommendation: str
    superpowers: list[TopicMastery]
    needs_practice: list[TopicMastery]
    recent_attempts: list[RecentAttempt]


class GradeRequest(BaseModel):
    course_id: int
    child_id: int | None = None
    topic: str = Field(min_length=1, max_length=150)
    questions: list[QuizQuestion]
    answers: list[str]


@router.post("/quiz", response_model=QuizResponse)
def make_quiz(data: QuizRequest, session: Session = Depends(get_session)):
    if not session.get(Course, data.course_id):
        raise HTTPException(404, "Cours introuvable. Crée ou sélectionne d'abord un cours.")
    return quiz(session, data.course_id, data.topic, data.difficulty, data.count)


@router.post("/quiz/grade", response_model=QuizGradeResponse)
def grade(data: GradeRequest, session: Session = Depends(get_session)):
    if not session.get(Course, data.course_id):
        raise HTTPException(404, "Cours introuvable.")
    if data.child_id is not None:
        child = session.get(User, data.child_id)
        if not child or child.role != UserRole.CHILD:
            raise HTTPException(404, "Profil enfant introuvable.")
    results = []
    weak_spots = []
    for index, question in enumerate(data.questions):
        answer = data.answers[index] if index < len(data.answers) else ""
        correct = answer.strip().casefold() == question.answer.strip().casefold()
        results.append({
            "correct": correct,
            "points": 10 if correct else 0,
            "feedback": "Bravo, tu as compris !" if correct else question.explanation,
            "answer": question.answer,
        })
        if not correct:
            weak_spots.append(question.question)

    points = sum(row["points"] for row in results)
    attempt = QuizAttempt(
        course_id=data.course_id,
        child_id=data.child_id,
        topic=data.topic,
        points=points,
        correct_count=sum(row["correct"] for row in results),
        question_count=len(results),
        weak_spots=weak_spots,
    )
    session.add(attempt)
    session.commit()
    session.refresh(attempt)
    return {
        "attempt_id": attempt.id,
        "points": points,
        "results": results,
        "weak_spots": weak_spots,
        "boosters": [f"Réessaie : {item}" for item in weak_spots],
        "badges": ["Knowledge Star"] if results and len(weak_spots) == 0 else [],
    }


@router.get("/progress/{course_id}", response_model=ProgressResponse)
def get_progress(course_id: int, child_id: int | None = Query(default=None), session: Session = Depends(get_session)):
    if not session.get(Course, course_id):
        raise HTTPException(404, "Cours introuvable.")
    query = select(QuizAttempt).where(QuizAttempt.course_id == course_id)
    if child_id is not None:
        query = query.where(QuizAttempt.child_id == child_id)
    attempts = session.exec(query.order_by(QuizAttempt.created_at.desc())).all()
    topics: dict[str, list[int]] = {}
    total_questions = total_correct = total_points = 0
    for attempt in attempts:
        values = topics.setdefault(attempt.topic, [0, 0])
        values[0] += attempt.correct_count
        values[1] += attempt.question_count
        total_questions += attempt.question_count
        total_correct += attempt.correct_count
        total_points += attempt.points
    mastery = [
        {"topic": topic, "accuracy": round(100 * correct / max(1, count))}
        for topic, (correct, count) in topics.items()
    ]
    accuracy = round(100 * total_correct / max(1, total_questions))
    if not attempts:
        encouragement = "Prêt à jouer ? Fais un premier quiz pour découvrir tes super-pouvoirs !"
        recommendation = "Choisis un cours et essaie un petit quiz."
    elif accuracy >= 80:
        encouragement = "Incroyable travail ! Tes révisions portent leurs fruits."
        recommendation = "Essaie un quiz défi ou découvre un nouveau sujet."
    elif accuracy >= 60:
        encouragement = "Tu progresses à chaque essai. Continue comme ça !"
        recommendation = "Relis les cartes mémoire des sujets à renforcer."
    else:
        encouragement = "Chaque erreur t'aide à apprendre. Tu peux y arriver !"
        recommendation = "Revois une leçon avec ton Buddy, puis retente un quiz facile."
    return {
        "course_id": course_id,
        "child_id": child_id,
        "attempts": len(attempts),
        "points": total_points,
        "accuracy": accuracy,
        "encouragement": encouragement,
        "recommendation": recommendation,
        "superpowers": [item for item in mastery if item["accuracy"] >= 80],
        "needs_practice": [item for item in mastery if item["accuracy"] < 60],
        "recent_attempts": [attempt.model_dump(exclude={"weak_spots"}) for attempt in attempts[:10]],
    }
