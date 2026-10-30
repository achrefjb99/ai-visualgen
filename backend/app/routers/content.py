"""Router FastAPI pour la gestion des contenus pédagogiques (Cours et Chapitres/Topics).

Fournit les opérations CRUD complètes :
- Pour les cours (/courses) :
    - POST / : Création d'un cours avec validation de l'enseignant.
    - GET / : Liste paginée des cours avec filtres par matière, niveau et enseignant.
    - GET /{id} : Détail d'un cours avec ses chapitres associés (Topic).
    - PATCH /{id} : Mise à jour partielle d'un cours.
    - DELETE /{id} : Suppression d'un cours (avec suppression en cascade des chapitres).
    - GET /{id}/topics : Liste paginée des chapitres d'un cours donné.
- Pour les chapitres (/topics) :
    - POST / : Création d'un chapitre rattaché à un cours existant.
    - GET / : Liste paginée des chapitres avec filtre optionnel par cours.
    - GET /{id} : Détail d'un chapitre avec son cours parent.
    - PATCH /{id} : Mise à jour partielle d'un chapitre.
    - DELETE /{id} : Suppression d'un chapitre.
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlmodel import Session, select

from app.database import get_session
from app.models.shared import (
    Course,
    CourseCreate,
    CourseRead,
    CourseReadWithTopics,
    CourseUpdate,
    Topic,
    TopicCreate,
    TopicRead,
    TopicReadWithCourse,
    TopicUpdate,
    User,
    UserRole,
)
from app.routers.deps import get_current_user

logger = logging.getLogger(__name__)

# Sous-routeurs pour modulariser les chemins et tags OpenAPI
courses_router = APIRouter(prefix="/courses", tags=["Courses"])
topics_router = APIRouter(prefix="/topics", tags=["Topics"])


# ==============================================================================
# ENDPOINTS COURSES (/courses)
# ==============================================================================


@courses_router.post(
    "/",
    response_model=CourseRead,
    status_code=status.HTTP_201_CREATED,
    summary="Créer un nouveau cours",
    description="Enregistre un cours avec sa matière, son niveau scolaire et associe automatiquement l'enseignant connecté.",
)
def create_course(
    course_in: CourseCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> Course:
    """Crée un nouveau cours après validation du rôle enseignant ou admin."""
    if current_user.role not in (UserRole.TEACHER, UserRole.ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seuls les enseignants et les administrateurs peuvent créer un cours.",
        )

    # Si c'est un enseignant, le cours lui est systématiquement rattaché
    teacher_id = current_user.id
    if current_user.role == UserRole.ADMIN and course_in.teacher_id is not None:
        teacher = session.get(User, course_in.teacher_id)
        if not teacher:
            logger.warning("Enseignant avec l'ID %s non trouvé", course_in.teacher_id)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"L'enseignant avec l'identifiant {course_in.teacher_id} n'existe pas.",
            )
        teacher_id = course_in.teacher_id

    course_data = course_in.model_dump()
    course_data["teacher_id"] = teacher_id
    db_course = Course(**course_data)
    session.add(db_course)
    session.commit()
    session.refresh(db_course)
    return db_course


@courses_router.get(
    "/",
    response_model=List[CourseReadWithTopics],
    summary="Lister les cours avec pagination et filtres",
    description="Récupère la liste paginée des cours. Filtres disponibles : matière (subject), "
    "niveau scolaire (grade_level) et enseignant (teacher_id).",
)
def list_courses(
    offset: int = Query(default=0, ge=0, description="Index de début de pagination"),
    limit: int = Query(default=20, ge=1, le=100, description="Nombre de cours par page"),
    subject: Optional[str] = Query(default=None, description="Filtrer par matière"),
    grade_level: Optional[str] = Query(default=None, description="Filtrer par niveau scolaire"),
    teacher_id: Optional[int] = Query(default=None, description="Filtrer par identifiant enseignant"),
    session: Session = Depends(get_session),
) -> List[Course]:
    """Retourne la liste paginée des cours selon les critères."""
    query = select(Course)

    if subject is not None:
        query = query.where(Course.subject == subject)
    if grade_level is not None:
        query = query.where(Course.grade_level == grade_level)
    if teacher_id is not None:
        query = query.where(Course.teacher_id == teacher_id)

    query = query.offset(offset).limit(limit)
    return session.exec(query).all()


@courses_router.get(
    "/{id}",
    response_model=CourseReadWithTopics,
    summary="Obtenir les détails d'un cours",
    description="Récupère un cours par son identifiant, incluant la liste complète de ses chapitres (topics) et l'enseignant.",
)
def get_course(
    id: int,
    session: Session = Depends(get_session),
) -> Course:
    """Récupère un cours et ses chapitres associés."""
    course = session.get(Course, id)
    if not course:
        logger.info("Cours avec l'ID %s introuvable", id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cours avec l'identifiant {id} introuvable.",
        )
    return course


@courses_router.patch(
    "/{id}",
    response_model=CourseRead,
    summary="Mettre à jour partiellement un cours",
    description="Modifie un ou plusieurs attributs d'un cours existant.",
)
def update_course(
    id: int,
    course_update: CourseUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> Course:
    """Modifie partiellement les données d'un cours."""
    if current_user.role not in (UserRole.TEACHER, UserRole.ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seuls les enseignants et les administrateurs peuvent modifier un cours.",
        )

    db_course = session.get(Course, id)
    if not db_course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cours avec l'identifiant {id} introuvable.",
        )

    if current_user.role == UserRole.TEACHER and db_course.teacher_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous n'êtes pas autorisé à modifier ce cours car vous n'en êtes pas le créateur.",
        )

    # Validation du nouvel enseignant si renseigné
    if course_update.teacher_id is not None and course_update.teacher_id != db_course.teacher_id:
        if current_user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Seul un administrateur peut réassigner l'enseignant d'un cours.",
            )
        teacher = session.get(User, course_update.teacher_id)
        if not teacher:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"L'enseignant avec l'identifiant {course_update.teacher_id} n'existe pas.",
            )

    update_dict = course_update.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(db_course, key, value)

    session.add(db_course)
    session.commit()
    session.refresh(db_course)
    return db_course


@courses_router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Supprimer un cours",
    description="Supprime un cours de la base de données. Tous les chapitres associés sont également supprimés en cascade.",
)
def delete_course(
    id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> Response:
    """Supprime définitivement un cours et ses chapitres."""
    if current_user.role not in (UserRole.TEACHER, UserRole.ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seuls les enseignants et les administrateurs peuvent supprimer un cours.",
        )

    course = session.get(Course, id)
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cours avec l'identifiant {id} introuvable.",
        )

    if current_user.role == UserRole.TEACHER and course.teacher_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous n'êtes pas autorisé à supprimer ce cours car vous n'en êtes pas le créateur.",
        )

    session.delete(course)
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@courses_router.get(
    "/{id}/topics",
    response_model=List[TopicRead],
    summary="Lister tous les chapitres d'un cours",
    description="Récupère la liste ordonnée et paginée des chapitres appartenant au cours spécifié.",
)
def list_course_topics(
    id: int,
    offset: int = Query(default=0, ge=0, description="Index de départ"),
    limit: int = Query(default=20, ge=1, le=100, description="Nombre de chapitres par page"),
    session: Session = Depends(get_session),
) -> List[Topic]:
    """Retourne les chapitres d'un cours donné."""
    course = session.get(Course, id)
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cours avec l'identifiant {id} introuvable.",
        )

    query = select(Topic).where(Topic.course_id == id).offset(offset).limit(limit)
    return session.exec(query).all()


# ==============================================================================
# ENDPOINTS TOPICS (/topics)
# ==============================================================================


@topics_router.post(
    "/",
    response_model=TopicRead,
    status_code=status.HTTP_201_CREATED,
    summary="Créer un nouveau chapitre",
    description="Enregistre un chapitre pédagogique adapté aux enfants (summary_kid) "
    "rattaché à un cours parent existant.",
)
def create_topic(
    topic_in: TopicCreate,
    session: Session = Depends(get_session),
) -> Topic:
    """Crée un chapitre après avoir vérifié l'existence du cours parent."""
    parent_course = session.get(Course, topic_in.course_id)
    if not parent_course:
        logger.warning("Cours parent avec l'ID %s non trouvé", topic_in.course_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Le cours parent avec l'identifiant {topic_in.course_id} n'existe pas.",
        )

    db_topic = Topic.model_validate(topic_in)
    session.add(db_topic)
    session.commit()
    session.refresh(db_topic)
    return db_topic


@topics_router.get(
    "/",
    response_model=List[TopicRead],
    summary="Lister les chapitres avec pagination et filtre",
    description="Récupère la liste paginée des chapitres. Permet de filtrer par cours via course_id.",
)
def list_topics(
    offset: int = Query(default=0, ge=0, description="Index de début de pagination"),
    limit: int = Query(default=20, ge=1, le=100, description="Nombre d'éléments par page"),
    course_id: Optional[int] = Query(default=None, description="Filtrer par identifiant du cours"),
    session: Session = Depends(get_session),
) -> List[Topic]:
    """Retourne la liste paginée des chapitres."""
    query = select(Topic)
    if course_id is not None:
        query = query.where(Topic.course_id == course_id)

    query = query.offset(offset).limit(limit)
    return session.exec(query).all()


@topics_router.get(
    "/{id}",
    response_model=TopicReadWithCourse,
    summary="Obtenir les détails d'un chapitre",
    description="Récupère un chapitre par son identifiant unique avec les informations de son cours parent.",
)
def get_topic(
    id: int,
    session: Session = Depends(get_session),
) -> Topic:
    """Récupère un chapitre et son cours parent."""
    topic = session.get(Topic, id)
    if not topic:
        logger.info("Chapitre avec l'ID %s introuvable", id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chapitre avec l'identifiant {id} introuvable.",
        )
    return topic


@topics_router.patch(
    "/{id}",
    response_model=TopicRead,
    summary="Mettre à jour partiellement un chapitre",
    description="Modifie un ou plusieurs champs d'un chapitre (nom, résumé adapté aux enfants, cours de rattachement).",
)
def update_topic(
    id: int,
    topic_update: TopicUpdate,
    session: Session = Depends(get_session),
) -> Topic:
    """Met à jour partiellement les informations d'un chapitre."""
    db_topic = session.get(Topic, id)
    if not db_topic:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chapitre avec l'identifiant {id} introuvable.",
        )

    # Si le cours parent est modifié, vérifier qu'il existe
    if topic_update.course_id is not None and topic_update.course_id != db_topic.course_id:
        parent_course = session.get(Course, topic_update.course_id)
        if not parent_course:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Le nouveau cours parent avec l'identifiant {topic_update.course_id} n'existe pas.",
            )

    update_dict = topic_update.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(db_topic, key, value)

    session.add(db_topic)
    session.commit()
    session.refresh(db_topic)
    return db_topic


@topics_router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Supprimer un chapitre",
    description="Supprime définitivement un chapitre d'apprentissage.",
)
def delete_topic(
    id: int,
    session: Session = Depends(get_session),
) -> Response:
    """Supprime un chapitre par son identifiant."""
    topic = session.get(Topic, id)
    if not topic:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chapitre avec l'identifiant {id} introuvable.",
        )

    session.delete(topic)
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ==============================================================================
# ROUTEUR PRINCIPAL DU MODULE CONTENT
# ==============================================================================

router = APIRouter()
router.include_router(courses_router)
router.include_router(topics_router)

__all__ = ["router", "courses_router", "topics_router"]
