"""Module 2 - Tables : flashcards, glossaire et morceaux de cours indexés (RAG)."""

from typing import Optional

from sqlalchemy import JSON, Column, Text
from sqlmodel import Field, SQLModel


class Flashcard(SQLModel, table=True):
    __tablename__ = "m2_flashcards"
    id: Optional[int] = Field(default=None, primary_key=True)
    topic_id: int = Field(foreign_key="topics.id", index=True, ondelete="CASCADE")
    question: str = Field(sa_column=Column(Text, nullable=False))
    answer: str = Field(sa_column=Column(Text, nullable=False))
    image_hint: Optional[str] = Field(default=None, max_length=255)


class GlossaryTerm(SQLModel, table=True):
    __tablename__ = "m2_glossary"
    id: Optional[int] = Field(default=None, primary_key=True)
    topic_id: int = Field(foreign_key="topics.id", index=True, ondelete="CASCADE")
    word: str = Field(max_length=100)
    definition: str = Field(sa_column=Column(Text, nullable=False))


class CourseChunk(SQLModel, table=True):
    """Morceau de cours + son embedding (vecteur), utilisé par le RAG."""

    __tablename__ = "m2_chunks"
    id: Optional[int] = Field(default=None, primary_key=True)
    course_id: int = Field(foreign_key="courses.id", index=True, ondelete="CASCADE")
    position: int = Field(default=0)
    content: str = Field(sa_column=Column(Text, nullable=False))
    embedding: list = Field(sa_column=Column(JSON, nullable=False))