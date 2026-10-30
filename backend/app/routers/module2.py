"""Module 2 - Routes : indexation du cours (RAG), génération, lecture."""

import logging
from datetime import datetime
from typing import List, Literal

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel, Field
from pypdf import PdfReader
from sqlmodel import Session, select

from app.database import get_session
from app.models.module2 import CourseChunk, Flashcard, GlossaryTerm
from app.models.shared import Course, Topic, User, UserRole
from app.routers.deps import get_current_user
from app.services.module2_ai import generate_lesson_material
from app.services.module2_rag import chunk_text, embed_documents, retrieve

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/module2", tags=["Module 2 - Résumés & Flashcards"])

MIN_SCORE = 0.45  # seuil de pertinence : en dessous, le chapitre est jugé absent du cours
TOP_K = 5         # nombre d'extraits donnés au LLM


class IngestResponse(BaseModel):
    chunks_indexed: int = Field(ge=0)


class IndexStatusResponse(BaseModel):
    course_id: int
    chunks: int = Field(ge=0)
    indexed: bool


class LessonTopicResponse(BaseModel):
    id: int
    course_id: int
    name: str
    summary_kid: str
    created_at: datetime


class LessonFlashcardResponse(BaseModel):
    id: int
    topic_id: int
    question: str
    answer: str
    image_hint: str | None = None


class LessonGlossaryResponse(BaseModel):
    id: int
    topic_id: int
    word: str
    definition: str


class LessonSourceResponse(BaseModel):
    id: int
    score: float
    extrait: str


class LessonGenerationResponse(BaseModel):
    topic: LessonTopicResponse
    flashcards: list[LessonFlashcardResponse]
    glossary: list[LessonGlossaryResponse]
    sources: list[LessonSourceResponse]
    generation_mode: Literal["ai", "local"]


@router.post("/ingest", status_code=status.HTTP_201_CREATED, response_model=IngestResponse,
             summary="Indexer un PDF de cours (RAG)")
def ingest(
    course_id: int = Form(...),
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Extrait le texte du PDF, le découpe, calcule les embeddings et les stocke.
    Ré-indexer un cours remplace son ancien index."""
    if current_user.role not in (UserRole.TEACHER, UserRole.ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seuls les enseignants et les administrateurs peuvent indexer un PDF de cours.",
        )

    course = session.get(Course, course_id)
    if not course:
        raise HTTPException(404, "Cours introuvable.")

    if current_user.role == UserRole.TEACHER and course.teacher_id and course.teacher_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous n'êtes pas autorisé à modifier l'index d'un cours créé par un autre enseignant.",
        )

    try:
        text = "\n".join((p.extract_text() or "") for p in PdfReader(file.file).pages)
    except Exception:
        raise HTTPException(400, "Fichier PDF illisible.")
    if not text.strip():
        raise HTTPException(400, "Impossible d'extraire du texte de ce PDF (scan ?).")

    chunks = chunk_text(text)
    try:
        vectors = embed_documents(chunks)
    except Exception as e:
        logger.error("Erreur embeddings : %s", e)
        raise HTTPException(502, "Le service d'embeddings est indisponible, réessaie.")

    for old in session.exec(select(CourseChunk).where(CourseChunk.course_id == course_id)).all():
        session.delete(old)
    session.add_all([
        CourseChunk(course_id=course_id, position=i, content=c, embedding=v)
        for i, (c, v) in enumerate(zip(chunks, vectors))
    ])
    session.commit()
    return {"chunks_indexed": len(chunks)}


@router.get("/courses/{course_id}/index", response_model=IndexStatusResponse, summary="État de l'index RAG d'un cours")
def index_status(course_id: int, session: Session = Depends(get_session)):
    if not session.get(Course, course_id):
        raise HTTPException(404, "Cours introuvable. Crée ou sélectionne d'abord un cours.")
    count = len(session.exec(select(CourseChunk.id).where(CourseChunk.course_id == course_id)).all())
    return {"course_id": course_id, "chunks": count, "indexed": count > 0}


@router.post("/generate", status_code=status.HTTP_201_CREATED, response_model=LessonGenerationResponse,
             summary="Générer résumé, flashcards et glossaire (RAG)")
def generate(
    course_id: int = Form(...),
    name: str | None = Form(default=None, min_length=1, max_length=150),
    chapter: str | None = Form(default=None, min_length=1, max_length=150),
    age: int = Form(default=8, ge=3, le=18),
    session: Session = Depends(get_session),
):
    """1) retrouve les extraits du cours liés au chapitre, 2) génère uniquement à partir d'eux."""
    topic_name = (chapter or name or "").strip()
    if not topic_name:
        raise HTTPException(422, "Le champ 'chapter' est obligatoire (ancien champ accepté : 'name').")
    chunks = session.exec(
        select(CourseChunk).where(CourseChunk.course_id == course_id).order_by(CourseChunk.position)
    ).all()
    if not chunks:
        raise HTTPException(400, "Aucun cours indexé. Utilise d'abord /module2/ingest.")

    try:
        top = retrieve(topic_name, chunks, k=TOP_K)
    except Exception as e:
        logger.error("Erreur recherche : %s", e)
        raise HTTPException(502, "La recherche locale dans le cours est indisponible.")

    if not top or top[0][0] < MIN_SCORE:
        raise HTTPException(422, "Ce chapitre n'apparaît pas dans le cours fourni.")

    context = "\n\n".join(f"[{i + 1}] {c.content}" for i, (_, c) in enumerate(top))
    try:
        data = generate_lesson_material(topic_name, context, age)
    except Exception as e:
        logger.exception("Erreur IA lors de la génération du cours")
        raise HTTPException(502, "La génération locale de la leçon a échoué.") from e
    if data.get("insufficient"):
        raise HTTPException(422, "Le cours ne contient pas assez d'informations sur ce chapitre.")

    topic = Topic(course_id=course_id, name=topic_name, summary_kid=data.get("summary", ""))
    session.add(topic)
    session.commit()
    session.refresh(topic)

    cards = [
        Flashcard(topic_id=topic.id, question=c["question"].strip(), answer=c["answer"].strip(),
                  image_hint=c.get("image_hint"))
        for c in data.get("flashcards", []) if c.get("question") and c.get("answer")
    ]
    terms = [
        GlossaryTerm(topic_id=topic.id, word=g["word"].strip(), definition=g["definition"].strip())
        for g in data.get("glossary", []) if g.get("word") and g.get("definition")
    ]
    session.add_all(cards + terms)
    session.commit()
    # Le 2e commit « expire » tous les objets : on recharge aussi le topic avant de le renvoyer
    for obj in [topic, *cards, *terms]:
        session.refresh(obj)

    sources = [
        {"id": i + 1, "score": round(s, 2), "extrait": c.content[:150]}
        for i, (s, c) in enumerate(top)
    ]
    return {
        "topic": topic.model_dump(),
        "flashcards": [c.model_dump() for c in cards],
        "glossary": [t.model_dump() for t in terms],
        "sources": sources,
        "generation_mode": data.get("generation_mode", "ai"),
    }


@router.get("/topics/{topic_id}/flashcards", response_model=List[Flashcard])
def get_flashcards(topic_id: int, session: Session = Depends(get_session)):
    return session.exec(select(Flashcard).where(Flashcard.topic_id == topic_id)).all()


@router.get("/topics/{topic_id}/glossary", response_model=List[GlossaryTerm])
def get_glossary(topic_id: int, session: Session = Depends(get_session)):
    return session.exec(select(GlossaryTerm).where(GlossaryTerm.topic_id == topic_id)).all()
