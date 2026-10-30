"""EduGenius AI (Kids Edition) - Modèles de données et schémas partagés.

Ce module définit l'ensemble des modèles relationnels SQLModel (tables MySQL)
et des schémas Pydantic v2 associés (Base, Create, Read, Update) pour la
gestion des utilisateurs, des cours et des matières/sujets.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional

from sqlmodel import Field, Relationship, SQLModel


# ==============================================================================
# ENUMS
# ==============================================================================


class UserRole(str, Enum):
    """Rôles disponibles pour les utilisateurs de la plateforme EduGenius."""

    CHILD = "CHILD"
    PARENT = "PARENT"
    TEACHER = "TEACHER"
    ADMIN = "ADMIN"


# ==============================================================================
# USER SCHEMAS & TABLE MODEL
# ==============================================================================


class UserBase(SQLModel):
    """Champs communs pour les entités Utilisateur."""

    username: str = Field(
        min_length=3,
        max_length=50,
        index=True,
        unique=True,
        description="Nom d'utilisateur unique pour l'authentification",
    )
    email: Optional[str] = Field(
        default=None,
        max_length=255,
        index=True,
        nullable=True,
        description="Adresse e-mail du compte (facultative pour les profils enfants)",
    )
    role: UserRole = Field(
        default=UserRole.CHILD,
        index=True,
        description="Rôle de l'utilisateur (CHILD, PARENT, TEACHER, ADMIN)",
    )
    age: Optional[int] = Field(
        default=None,
        ge=3,
        le=120,
        description="Âge de l'apprenant (pertinent pour la personnalisation enfant)",
    )
    grade_level: Optional[str] = Field(
        default=None,
        max_length=50,
        description="Niveau scolaire (ex: Maternelle, CP, CE1, CM2, 6ème)",
    )
    favorite_theme: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Thème d'intérêt préféré (ex: Espace, Dinosaures, Océan)",
    )
    parent_id: Optional[int] = Field(
        default=None,
        foreign_key="users.id",
        index=True,
        description="Identifiant du parent ou tuteur rattaché",
    )


class UserCreate(UserBase):
    """Schéma Pydantic pour la création d'un utilisateur (mot de passe en clair)."""

    password: Optional[str] = Field(
        default="kids1234",
        min_length=4,
        max_length=128,
        description="Mot de passe en clair fourni lors de l'inscription (sera hashé)",
    )


class UserRead(UserBase):
    """Schéma Pydantic pour la lecture d'un utilisateur (mot de passe exclu)."""

    id: int = Field(description="Identifiant unique de l'utilisateur")
    created_at: datetime = Field(description="Horodatage de création du compte (UTC)")


class UserUpdate(SQLModel):
    """Schéma Pydantic pour la mise à jour partielle d'un utilisateur."""

    username: Optional[str] = Field(
        default=None,
        min_length=3,
        max_length=50,
        description="Nouveau nom d'utilisateur",
    )
    email: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Nouvelle adresse e-mail",
    )
    password: Optional[str] = Field(
        default=None,
        min_length=4,
        max_length=128,
        description="Nouveau mot de passe en clair à hasher",
    )
    role: Optional[UserRole] = Field(
        default=None,
        description="Nouveau rôle attribué",
    )
    age: Optional[int] = Field(
        default=None,
        ge=3,
        le=120,
        description="Nouvel âge",
    )
    grade_level: Optional[str] = Field(
        default=None,
        max_length=50,
        description="Nouveau niveau scolaire",
    )
    favorite_theme: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Nouveau thème favori",
    )
    parent_id: Optional[int] = Field(
        default=None,
        description="Nouvel identifiant parent rattaché",
    )


class User(UserBase, table=True):
    """Table de base de données SQLModel pour les utilisateurs."""

    __tablename__: str = "users"

    id: Optional[int] = Field(
        default=None,
        primary_key=True,
        index=True,
        description="Clé primaire auto-incrémentée",
    )
    hashed_password: str = Field(
        max_length=255,
        nullable=False,
        description="Empreinte cryptographique (hash) du mot de passe",
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
        description="Date et heure de création enregistrées en base",
    )

    # Relation bidirectionnelle : un enseignant/utilisateur peut créer plusieurs cours
    courses: List["Course"] = Relationship(
        back_populates="teacher",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )


# ==============================================================================
# COURSE SCHEMAS & TABLE MODEL
# ==============================================================================


class CourseBase(SQLModel):
    """Champs communs pour les entités Cours."""

    title: str = Field(
        min_length=1,
        max_length=150,
        index=True,
        description="Titre du cours pédagogique",
    )
    description: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Description générale et objectifs d'apprentissage",
    )
    subject: str = Field(
        min_length=1,
        max_length=100,
        index=True,
        description="Matière scolaire (ex: Mathématiques, Français, Sciences)",
    )
    grade_level: str = Field(
        min_length=1,
        max_length=50,
        index=True,
        description="Niveau scolaire cible (ex: CP, CE1, CM2)",
    )
    teacher_id: Optional[int] = Field(
        default=None,
        foreign_key="users.id",
        index=True,
        ondelete="SET NULL",
        description="Identifiant de l'enseignant responsable du cours",
    )


class CourseCreate(CourseBase):
    """Schéma Pydantic pour la création d'un cours."""

    pass


class CourseRead(CourseBase):
    """Schéma Pydantic pour la lecture d'un cours."""

    id: int = Field(description="Identifiant unique du cours")
    created_at: datetime = Field(description="Horodatage de création du cours (UTC)")


class CourseUpdate(SQLModel):
    """Schéma Pydantic pour la mise à jour d'un cours (tous les champs optionnels)."""

    title: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=150,
        description="Nouveau titre du cours",
    )
    description: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Nouvelle description",
    )
    subject: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="Nouvelle matière",
    )
    grade_level: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=50,
        description="Nouveau niveau scolaire ciblé",
    )
    teacher_id: Optional[int] = Field(
        default=None,
        description="Nouvel identifiant de l'enseignant",
    )


class Course(CourseBase, table=True):
    """Table de base de données SQLModel pour les cours."""

    __tablename__: str = "courses"

    id: Optional[int] = Field(
        default=None,
        primary_key=True,
        index=True,
        description="Clé primaire auto-incrémentée",
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
        description="Date et heure de création enregistrées en base",
    )

    # Relations bidirectionnelles
    teacher: Optional[User] = Relationship(back_populates="courses")
    topics: List["Topic"] = Relationship(
        back_populates="course",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )


# ==============================================================================
# TOPIC SCHEMAS & TABLE MODEL
# ==============================================================================


class TopicBase(SQLModel):
    """Champs communs pour les entités Sujets / Matières / Chapitres."""

    course_id: int = Field(
        foreign_key="courses.id",
        index=True,
        ondelete="CASCADE",
        description="Identifiant du cours auquel est rattaché ce sujet",
    )
    name: str = Field(
        min_length=1,
        max_length=150,
        index=True,
        description="Nom du sujet / chapitre d'étude",
    )
    summary_kid: str = Field(
        min_length=1,
        description="Résumé vulgarisé, bienveillant et adapté aux enfants",
    )


class TopicCreate(TopicBase):
    """Schéma Pydantic pour la création d'un sujet."""

    pass


class TopicRead(TopicBase):
    """Schéma Pydantic pour la lecture d'un sujet."""

    id: int = Field(description="Identifiant unique du sujet")
    created_at: datetime = Field(description="Horodatage de création du sujet (UTC)")


class TopicUpdate(SQLModel):
    """Schéma Pydantic pour la mise à jour d'un sujet (tous les champs optionnels)."""

    course_id: Optional[int] = Field(
        default=None,
        description="Nouvel identifiant de cours de rattachement",
    )
    name: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=150,
        description="Nouveau nom du sujet",
    )
    summary_kid: Optional[str] = Field(
        default=None,
        min_length=1,
        description="Nouveau résumé adapté aux enfants",
    )


class Topic(TopicBase, table=True):
    """Table de base de données SQLModel pour les sujets / chapitres."""

    __tablename__: str = "topics"

    id: Optional[int] = Field(
        default=None,
        primary_key=True,
        index=True,
        description="Clé primaire auto-incrémentée",
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
        description="Date et heure de création enregistrées en base",
    )

    # Relation bidirectionnelle
    course: Optional[Course] = Relationship(back_populates="topics")


# ==============================================================================
# RELATIONAL / NESTED RESPONSE SCHEMAS
# ==============================================================================


class TopicReadWithCourse(TopicRead):
    """Schéma de réponse enrichi incluant les détails du cours parent."""

    course: Optional[CourseRead] = None


class CourseReadWithTopics(CourseRead):
    """Schéma de réponse enrichi incluant la liste des sujets et l'enseignant."""

    teacher: Optional[UserRead] = None
    topics: List[TopicRead] = []


class UserReadWithCourses(UserRead):
    """Schéma de réponse enrichi incluant la liste des cours créés."""

    courses: List[CourseRead] = []


# ==============================================================================
# EXPORTS
# ==============================================================================

__all__ = [
    # Enums
    "UserRole",
    # User
    "UserBase",
    "UserCreate",
    "UserRead",
    "UserUpdate",
    "User",
    "UserReadWithCourses",
    # Course
    "CourseBase",
    "CourseCreate",
    "CourseRead",
    "CourseUpdate",
    "Course",
    "CourseReadWithTopics",
    # Topic
    "TopicBase",
    "TopicCreate",
    "TopicRead",
    "TopicUpdate",
    "Topic",
    "TopicReadWithCourse",
]
