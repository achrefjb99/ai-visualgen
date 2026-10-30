"""Router FastAPI pour la gestion des utilisateurs et des profils enfants.

Fournit les opérations de gestion de compte et de rattachement parent-enfant :
- POST / : Création de profil rattaché au parent connecté.
- POST /children : Création explicite d'un profil enfant rattaché au parent connecté.
- GET /my-children : Récupération des enfants rattachés au parent (avec filtre grade_level pour enseignants/admins).
- GET / : Liste paginée des utilisateurs.
- GET /{id} : Consultation détaillée d'un profil.
- PATCH /{id} : Mise à jour partielle sécurisée (propriétaire, parent rattaché ou admin).
- DELETE /{id} : Suppression sécurisée (propriétaire, parent rattaché ou admin).
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from pydantic import BaseModel, Field
from sqlmodel import Session, select

from app.database import get_session
from app.models.shared import (
    User,
    UserCreate,
    UserRead,
    UserRole,
    UserUpdate,
)
from app.routers.deps import get_current_user
from app.services.security import hash_password

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["Users"])


class ChildUpdate(BaseModel):
    """Schéma Pydantic pour la mise à jour d'un profil enfant."""

    username: Optional[str] = Field(
        default=None,
        min_length=3,
        max_length=50,
        description="Nom d'utilisateur ou prénom de l'enfant",
    )
    age: Optional[int] = Field(
        default=None,
        ge=4,
        le=15,
        description="Âge de l'enfant (entre 4 et 15 ans)",
    )
    grade_level: Optional[str] = Field(
        default=None,
        max_length=50,
        description="Classe / Niveau scolaire (ex: CP, CE1, CE2, CM1, CM2, 6ème)",
    )
    favorite_theme: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Univers préféré (ex: Dinosaures, Espace, Animaux, Magie)",
    )


def _check_user_uniqueness(
    session: Session,
    username: str,
    email: Optional[str] = None,
    exclude_user_id: Optional[int] = None,
) -> None:
    """Vérifie l'unicité du username et de l'email (si fourni)."""
    # Vérification du nom d'utilisateur
    query_username = select(User).where(User.username == username)
    if exclude_user_id:
        query_username = query_username.where(User.id != exclude_user_id)
    if session.exec(query_username).first():
        logger.warning("Conflit: nom d'utilisateur déjà utilisé: %s", username)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ce nom d'utilisateur est déjà utilisé.",
        )

    # Vérification de l'e-mail uniquement s'il est renseigné
    if email:
        query_email = select(User).where(User.email == email)
        if exclude_user_id:
            query_email = query_email.where(User.id != exclude_user_id)
        if session.exec(query_email).first():
            logger.warning("Conflit: adresse e-mail déjà associée: %s", email)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cette adresse e-mail est déjà associée à un compte.",
            )


def _can_manage_target_user(current_user: User, target_user: User) -> bool:
    """Détermine si l'utilisateur connecté est autorisé à modifier ou supprimer target_user."""
    # 1. Un administrateur peut tout gérer
    if current_user.role == UserRole.ADMIN:
        return True

    # 2. L'utilisateur peut modifier son propre compte
    if current_user.id == target_user.id:
        return True

    # 3. Le parent propriétaire de l'enfant
    if target_user.parent_id == current_user.id:
        return True

    # 4. Un enseignant peut gérer les profils enfants de la plateforme
    if current_user.role == UserRole.TEACHER and target_user.role == UserRole.CHILD:
        return True

    return False


@router.post(
    "/",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Créer un utilisateur ou un profil enfant",
    description="Enregistre un nouvel utilisateur. Si le rôle est CHILD, le profil est automatiquement "
    "rattaché au parent connecté via parent_id. L'email est facultatif pour les enfants.",
)
@router.post(
    "/children",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Créer un profil enfant rattaché",
    description="Endpoint dédié à la création d'un profil enfant par le parent ou enseignant connecté.",
)
def create_user(
    user_in: UserCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> User:
    """Crée un utilisateur ou enfant rattaché au compte connecté."""
    # Un profil enfant ne peut pas inscrire d'autres comptes
    if current_user.role == UserRole.CHILD:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Un profil enfant n'est pas autorisé à créer de nouveaux comptes.",
        )

    # Détermination du rattachement parent
    is_child = user_in.role == UserRole.CHILD
    parent_id = current_user.id if is_child else user_in.parent_id

    # Normalisation de l'email (None si chaîne vide)
    normalized_email = user_in.email.strip() if user_in.email and user_in.email.strip() else None

    # Vérification d'unicité
    _check_user_uniqueness(session, username=user_in.username, email=normalized_email)

    raw_password = user_in.password if user_in.password else "kids1234"

    db_user = User(
        username=user_in.username,
        email=normalized_email,
        role=user_in.role,
        age=user_in.age,
        grade_level=user_in.grade_level,
        favorite_theme=user_in.favorite_theme,
        parent_id=parent_id,
        hashed_password=hash_password(raw_password),
    )

    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user


@router.get(
    "/my-children",
    response_model=List[UserRead],
    summary="Lister mes enfants rattachés",
    description="Retourne la liste des enfants rattachés au parent connecté. "
    "Les enseignants et administrateurs peuvent également filtrer les enfants par niveau scolaire (grade_level).",
)
def get_my_children(
    grade_level: Optional[str] = Query(default=None, description="Filtrer par niveau scolaire"),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> List[User]:
    """Retourne les profils enfants rattachés à l'utilisateur connecté."""
    query = select(User).where(User.role == UserRole.CHILD)

    if current_user.role == UserRole.PARENT:
        query = query.where(User.parent_id == current_user.id)
        if grade_level:
            query = query.where(User.grade_level == grade_level)
    elif current_user.role in [UserRole.TEACHER, UserRole.ADMIN]:
        if grade_level:
            query = query.where(User.grade_level == grade_level)
        else:
            query = query.where(User.parent_id == current_user.id)
    else:
        # Un enfant n'a pas d'enfants rattachés
        return []

    return session.exec(query).all()


@router.patch(
    "/children/{child_id}",
    response_model=UserRead,
    summary="Mettre à jour un profil enfant",
    description="Permet au parent rattaché (ou à un enseignant/admin) de modifier les informations d'un enfant.",
)
def update_child(
    child_id: int,
    child_update: ChildUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> User:
    """Met à jour les informations d'un profil enfant."""
    child = session.get(User, child_id)
    if not child or child.role != UserRole.CHILD:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Profil enfant avec l'identifiant {child_id} introuvable.",
        )

    # Contrôle d'accès strict : parent propriétaire ou rôle ADMIN/TEACHER autorisé
    is_owner_parent = child.parent_id == current_user.id
    is_admin = current_user.role == UserRole.ADMIN
    is_teacher = current_user.role == UserRole.TEACHER

    if not (is_owner_parent or is_admin or is_teacher):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Non autorisé à modifier cet enfant.",
        )

    update_dict = child_update.model_dump(exclude_unset=True)

    # Vérification d'unicité du nom d'utilisateur si modifié
    if "username" in update_dict and update_dict["username"]:
        new_username = update_dict["username"].strip()
        if new_username != child.username:
            _check_user_uniqueness(session, username=new_username, exclude_user_id=child.id)
            update_dict["username"] = new_username

    for field_name, value in update_dict.items():
        setattr(child, field_name, value)

    session.add(child)
    session.commit()
    session.refresh(child)
    return child


@router.get(
    "/",
    response_model=List[UserRead],
    summary="Lister les utilisateurs avec pagination et filtres",
    description="Récupère la liste paginée des utilisateurs.",
)
def list_users(
    offset: int = Query(default=0, ge=0, description="Index de départ de la pagination"),
    limit: int = Query(default=20, ge=1, le=100, description="Nombre d'éléments par page"),
    role: Optional[UserRole] = Query(default=None, description="Filtrer par rôle d'utilisateur"),
    grade_level: Optional[str] = Query(default=None, description="Filtrer par niveau scolaire"),
    session: Session = Depends(get_session),
) -> List[User]:
    """Retourne la liste paginée des utilisateurs selon les critères de recherche."""
    query = select(User)

    if role is not None:
        query = query.where(User.role == role)
    if grade_level is not None:
        query = query.where(User.grade_level == grade_level)

    query = query.offset(offset).limit(limit)
    return session.exec(query).all()


@router.get(
    "/{id}",
    response_model=UserRead,
    summary="Obtenir les détails d'un utilisateur",
    description="Récupère le profil complet d'un utilisateur par son ID.",
)
def get_user(
    id: int,
    session: Session = Depends(get_session),
) -> User:
    """Récupère un utilisateur par son identifiant unique."""
    user = session.get(User, id)
    if not user:
        logger.info("Utilisateur non trouvé avec l'id: %s", id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Utilisateur avec l'identifiant {id} introuvable.",
        )
    return user


@router.patch(
    "/{id}",
    response_model=UserRead,
    summary="Mettre à jour partiellement un profil utilisateur",
    description="Met à jour un profil. Exige d'être le propriétaire, le parent rattaché ou un administrateur.",
)
def update_user(
    id: int,
    user_update: UserUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> User:
    """Modifie partiellement les informations d'un utilisateur après vérification des droits."""
    db_user = session.get(User, id)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Utilisateur avec l'identifiant {id} introuvable.",
        )

    # Vérification des autorisations
    if not _can_manage_target_user(current_user, db_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès refusé. Vous n'êtes pas autorisé à modifier ce profil.",
        )

    # Vérification d'unicité en cas de modification username/email
    normalized_email = user_update.email.strip() if user_update.email and user_update.email.strip() else None
    if user_update.username and user_update.username != db_user.username:
        _check_user_uniqueness(session, username=user_update.username, exclude_user_id=db_user.id)
    if normalized_email and normalized_email != db_user.email:
        _check_user_uniqueness(session, username=db_user.username, email=normalized_email, exclude_user_id=db_user.id)

    update_dict = user_update.model_dump(exclude_unset=True)

    # Si un nouveau mot de passe est fourni, le hacher
    if "password" in update_dict:
        new_password = update_dict.pop("password")
        if new_password:
            db_user.hashed_password = hash_password(new_password)

    for field_name, value in update_dict.items():
        if field_name == "email":
            setattr(db_user, field_name, normalized_email)
        else:
            setattr(db_user, field_name, value)

    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Supprimer un utilisateur",
    description="Supprime un profil. Exige d'être le propriétaire, le parent rattaché ou un administrateur.",
)
def delete_user(
    id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> Response:
    """Supprime définitivement un utilisateur après vérification des permissions."""
    db_user = session.get(User, id)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Utilisateur avec l'identifiant {id} introuvable.",
        )

    # Vérification des autorisations
    if not _can_manage_target_user(current_user, db_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès refusé. Vous n'êtes pas autorisé à supprimer ce profil.",
        )

    session.delete(db_user)
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
