from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlmodel import Session, select

from app.database import get_session
from app.models.learning import VisualArtifact
from app.models.shared import Course
from app.modules.module3_tutor.service import visuals

router = APIRouter(prefix="/visuals", tags=["Module 5 - Visual learning"])


class VisualRequest(BaseModel):
    course_id: int
    topic: str = Field(min_length=1, max_length=150)


class VisualStep(BaseModel):
    label: str
    detail: str


class MindMapNode(BaseModel):
    label: str
    children: list[str]


class VisualSource(BaseModel):
    id: int
    label: str
    score: float
    text: str


class VisualResponse(BaseModel):
    id: int
    title: str
    steps: list[VisualStep]
    mind_map: list[MindMapNode]
    sources: list[VisualSource]
    created_at: datetime
    generation_mode: str


class VisualGalleryItem(BaseModel):
    id: int
    topic: str
    title: str
    content: dict
    created_at: datetime


@router.post("/schema", response_model=VisualResponse)
def make_visual(data: VisualRequest, session: Session = Depends(get_session)):
    if not session.get(Course, data.course_id):
        raise HTTPException(404, "Cours introuvable.")
    generated = visuals(session, data.course_id, data.topic)
    artifact = VisualArtifact(
        course_id=data.course_id,
        topic=data.topic,
        title=str(generated.get("title", data.topic))[:200],
        content=generated,
    )
    session.add(artifact)
    session.commit()
    session.refresh(artifact)
    return {"id": artifact.id, **generated, "created_at": artifact.created_at}


@router.get("/gallery/{course_id}", response_model=list[VisualGalleryItem])
def visual_gallery(course_id: int, session: Session = Depends(get_session)):
    if not session.get(Course, course_id):
        raise HTTPException(404, "Cours introuvable.")
    rows = session.exec(
        select(VisualArtifact)
        .where(VisualArtifact.course_id == course_id)
        .order_by(VisualArtifact.created_at.desc())
    ).all()
    return [{"id": row.id, "topic": row.topic, "title": row.title, "content": row.content, "created_at": row.created_at} for row in rows]
