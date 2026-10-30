"""Module des modèles de données EduGenius AI.

Centralise l'accès à tous les modèles SQLModel et schémas Pydantic du backend :
- Module 1 (Auth / Base) : User, UserRole, Course, Topic
- Module 2 (Leçons & RAG) : Flashcard, GlossaryTerm, CourseChunk
- Modules 4 & 5 (Quiz & Visuels) : QuizAttempt, VisualArtifact
"""

from app.models.learning import QuizAttempt, VisualArtifact
from app.models.module2 import CourseChunk, Flashcard, GlossaryTerm
from app.models.shared import (
    Course,
    CourseBase,
    CourseCreate,
    CourseRead,
    CourseReadWithTopics,
    CourseUpdate,
    Topic,
    TopicBase,
    TopicCreate,
    TopicRead,
    TopicReadWithCourse,
    TopicUpdate,
    User,
    UserBase,
    UserCreate,
    UserRead,
    UserReadWithCourses,
    UserRole,
    UserUpdate,
)

__all__ = [
    # Module 1 : Auth & Base
    "UserRole",
    "UserBase",
    "UserCreate",
    "UserRead",
    "UserUpdate",
    "User",
    "UserReadWithCourses",
    "CourseBase",
    "CourseCreate",
    "CourseRead",
    "CourseUpdate",
    "Course",
    "CourseReadWithTopics",
    "TopicBase",
    "TopicCreate",
    "TopicRead",
    "TopicUpdate",
    "Topic",
    "TopicReadWithCourse",
    # Module 2 : RAG, Flashcards & Glossaire
    "Flashcard",
    "GlossaryTerm",
    "CourseChunk",
    # Modules 4 & 5 : Quiz, Progrès & Visuels
    "QuizAttempt",
    "VisualArtifact",
]
