"""Router FastAPI pour l'authentification et l'émission de jetons JWT.

Endpoints :
- POST /token (ou /login) : Authentification par identifiant et mot de passe.
- GET /me : Consultation du profil de l'utilisateur actuellement connecté.
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlmodel import Session, select

from app.database import get_session
from app.models.shared import User, UserBase, UserRole
from app.routers.deps import get_current_user
from app.services.security import create_access_token, get_password_hash, verify_password

router = APIRouter(tags=["Auth"])


# ==============================================================================
# SCHÉMAS PYDANTIC AUTH
# ==============================================================================


class LoginRequest(BaseModel):
    """Corps de la requête de connexion."""

    username: str = Field(
        min_length=1,
        description="Nom d'utilisateur ou adresse email du compte",
    )
    password: str = Field(
        min_length=1,
        description="Mot de passe en clair",
    )


class RegisterRequest(BaseModel):
    """Corps de la requête d'inscription publique (Parent ou Enseignant)."""

    username: str = Field(
        min_length=3,
        max_length=50,
        description="Nom d'utilisateur unique",
    )
    email: EmailStr = Field(
        description="Adresse email valide du compte",
    )
    password: str = Field(
        min_length=6,
        description="Mot de passe en clair (minimum 6 caractères)",
    )
    role: UserRole = Field(
        description="Rôle souhaité (uniquement PARENT ou TEACHER)",
    )


class UserPublic(UserBase):
    """Profil public sécurisé de l'utilisateur (mot de passe exclu)."""

    id: int = Field(description="Identifiant unique de l'utilisateur")
    created_at: datetime = Field(description="Horodatage de création")


class TokenResponse(BaseModel):
    """Réponse contenant le jeton d'accès Bearer JWT et le profil de l'utilisateur."""

    access_token: str
    token_type: str = "bearer"
    user: UserPublic


# ==============================================================================
# ENDPOINTS AUTH
# ==============================================================================


@router.post(
    "/token",
    response_model=TokenResponse,
    summary="Obtenir un jeton d'accès JWT",
    description="Vérifie les identifiants d'un utilisateur et émet un jeton Bearer JWT signé contenant l'ID, le rôle et le username.",
)
def login(
    login_data: LoginRequest,
    session: Session = Depends(get_session),
) -> TokenResponse:
    """Authentifie un utilisateur et renvoie son token JWT."""
    identifier = login_data.username.strip()

    # Recherche par username ou email
    user = session.exec(
        select(User).where(
            (User.username == identifier) | (User.email == identifier)
        )
    ).first()

    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nom d'utilisateur ou mot de passe incorrect.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Génération du JWT avec les claims essentiels
    token_payload = {
        "sub": str(user.id),
        "username": user.username,
        "role": user.role.value if isinstance(user.role, UserRole) else str(user.role),
    }
    access_token = create_access_token(token_payload)

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserPublic.model_validate(user),
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    include_in_schema=False,
    summary="Alias pour /token",
)
def login_alias(
    login_data: LoginRequest,
    session: Session = Depends(get_session),
) -> TokenResponse:
    """Alias direct pour l'endpoint /token."""
    return login(login_data=login_data, session=session)


@router.get(
    "/me",
    response_model=UserPublic,
    summary="Profil de l'utilisateur connecté",
    description="Retourne les informations du compte associé au jeton Bearer JWT transmis dans le header Authorization.",
)
def read_current_user(
    current_user: User = Depends(get_current_user),
) -> UserPublic:
    """Renvoie le profil de l'utilisateur actuellement authentifié."""
    return UserPublic.model_validate(current_user)


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Inscription publique d'un parent ou enseignant",
    description="Permet à un parent ou enseignant de créer son compte en toute autonomie et retourne directement un jeton JWT.",
)
def register(
    register_data: RegisterRequest,
    session: Session = Depends(get_session),
) -> TokenResponse:
    """Inscrit un nouvel utilisateur (PARENT ou TEACHER) et renvoie son token JWT."""
    # Autoriser uniquement PARENT et TEACHER
    if register_data.role not in (UserRole.PARENT, UserRole.TEACHER):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="L'inscription publique est autorisée uniquement pour les rôles PARENT et TEACHER.",
        )

    username = register_data.username.strip()
    email = str(register_data.email).strip().lower()

    # Vérification de l'unicité du username
    existing_username = session.exec(
        select(User).where(User.username == username)
    ).first()
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Le nom d'utilisateur '{username}' est déjà utilisé.",
        )

    # Vérification de l'unicité de l'email
    existing_email = session.exec(
        select(User).where(User.email == email)
    ).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"L'adresse email '{email}' est déjà associée à un compte.",
        )

    # Hachage du mot de passe et création
    new_user = User(
        username=username,
        email=email,
        hashed_password=get_password_hash(register_data.password),
        role=register_data.role,
    )
    session.add(new_user)
    session.commit()
    session.refresh(new_user)

    # Émission immédiate du token JWT
    token_payload = {
        "sub": str(new_user.id),
        "username": new_user.username,
        "role": new_user.role.value if isinstance(new_user.role, UserRole) else str(new_user.role),
    }
    access_token = create_access_token(token_payload)

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserPublic.model_validate(new_user),
    )
