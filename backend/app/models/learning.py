from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import JSON, Column, DateTime, Text
from sqlmodel import Field, SQLModel


class QuizAttempt(SQLModel, table=True):
    __tablename__ = "learning_quiz_attempts"

    id: Optional[int] = Field(default=None, primary_key=True)
    course_id: int = Field(foreign_key="courses.id", index=True)
    child_id: Optional[int] = Field(default=None, foreign_key="users.id", index=True)
    topic: str = Field(max_length=150, index=True)
    points: int = Field(default=0, ge=0)
    correct_count: int = Field(default=0, ge=0)
    question_count: int = Field(default=0, ge=0)
    weak_spots: list[str] = Field(default_factory=list, sa_column=Column(JSON, nullable=False))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), sa_column=Column(DateTime(timezone=True), nullable=False))


class VisualArtifact(SQLModel, table=True):
    __tablename__ = "learning_visual_artifacts"

    id: Optional[int] = Field(default=None, primary_key=True)
    course_id: int = Field(foreign_key="courses.id", index=True)
    topic: str = Field(max_length=150, index=True)
    title: str = Field(max_length=200)
    content: dict = Field(sa_column=Column(JSON, nullable=False))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), sa_column=Column(DateTime(timezone=True), nullable=False))
