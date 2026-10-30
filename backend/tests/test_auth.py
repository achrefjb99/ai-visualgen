"""Tests unitaires et d'intégration pour l'authentification JWT (Module 1)."""

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from app.database import get_session
from app.main import app
from app.models.shared import User, UserRole
from app.services.security import hash_password


@pytest.fixture(name="session")
def session_fixture():
    """Crée une base SQLite éphémère isolée pour chaque test."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    SQLModel.metadata.drop_all(engine)


@pytest.fixture(name="client")
def client_fixture(session: Session):
    """Fournit un client de test FastAPI avec injection de la session SQLite en mémoire."""
    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


def test_auth_login_nominal_and_get_me(client: TestClient, session: Session):
    """Cas nominal : Connexion avec mot de passe valide -> Récupération du profil /me."""
    # [Arrange] Création d'un enseignant
    plain_password = "TeacherSecretPassword123!"
    teacher = User(
        username="professeur_antoine",
        email="antoine@edugenius.kids",
        hashed_password=hash_password(plain_password),
        role=UserRole.TEACHER,
    )
    session.add(teacher)
    session.commit()
    session.refresh(teacher)

    # [Act 1] Demande de jeton JWT via /api/v1/auth/token
    login_payload = {
        "username": "professeur_antoine",
        "password": plain_password,
    }
    response_token = client.post("/api/v1/auth/token", json=login_payload)

    # [Assert 1] Vérification du token émis
    assert response_token.status_code == status.HTTP_200_OK
    token_data = response_token.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"
    assert token_data["user"]["username"] == "professeur_antoine"
    assert token_data["user"]["role"] == "TEACHER"
    assert "password" not in token_data["user"]
    assert "hashed_password" not in token_data["user"]

    access_token = token_data["access_token"]

    # [Act 2] Consultation du profil connecté /api/v1/auth/me avec header Authorization
    headers = {"Authorization": f"Bearer {access_token}"}
    response_me = client.get("/api/v1/auth/me", headers=headers)

    # [Assert 2] Vérification de l'utilisateur retourné par la dépendance get_current_user
    assert response_me.status_code == status.HTTP_200_OK
    me_data = response_me.json()
    assert me_data["id"] == teacher.id
    assert me_data["username"] == "professeur_antoine"
    assert me_data["email"] == "antoine@edugenius.kids"


def test_auth_login_invalid_password_returns_401(client: TestClient, session: Session):
    """Tentative de connexion avec un mot de passe erroné (doit retourner 401)."""
    # [Arrange]
    teacher = User(
        username="marie_curie",
        email="marie@edugenius.kids",
        hashed_password=hash_password("BonMotDePasse!"),
        role=UserRole.TEACHER,
    )
    session.add(teacher)
    session.commit()

    # [Act]
    bad_payload = {
        "username": "marie_curie",
        "password": "MauvaisMotDePasse!",
    }
    response = client.post("/api/v1/auth/token", json=bad_payload)

    # [Assert]
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "incorrect" in response.json()["detail"].lower()


def test_auth_login_unknown_user_returns_401(client: TestClient):
    """Tentative de connexion avec un identifiant inexistant (doit retourner 401)."""
    # [Act]
    unknown_payload = {
        "username": "fantome_inconnu",
        "password": "QuelconquePassword123!",
    }
    response = client.post("/api/v1/auth/token", json=unknown_payload)

    # [Assert]
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_auth_me_without_token_returns_401(client: TestClient):
    """Accès à /api/v1/auth/me sans header Authorization (doit retourner 401)."""
    # [Act]
    response = client.get("/api/v1/auth/me")

    # [Assert]
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_auth_me_with_tampered_token_returns_401(client: TestClient):
    """Accès à /api/v1/auth/me avec un token corrompu (doit retourner 401)."""
    # [Act]
    headers = {"Authorization": "Bearer token_falsifie_invalide"}
    response = client.get("/api/v1/auth/me", headers=headers)

    # [Assert]
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_auth_register_parent_nominal_returns_token(client: TestClient, session: Session):
    """Inscription réussie d'un Parent -> retourne token JWT et profil créé."""
    payload = {
        "username": "maman_sophie",
        "email": "sophie@example.com",
        "password": "Password123!",
        "role": "PARENT",
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["username"] == "maman_sophie"
    assert data["user"]["email"] == "sophie@example.com"
    assert data["user"]["role"] == "PARENT"


def test_auth_register_teacher_nominal_returns_token(client: TestClient, session: Session):
    """Inscription réussie d'un Enseignant -> retourne token JWT."""
    payload = {
        "username": "prof_laurent",
        "email": "laurent@ecole.fr",
        "password": "LaurentPassword123!",
        "role": "TEACHER",
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["user"]["role"] == "TEACHER"
    assert data["user"]["username"] == "prof_laurent"


def test_auth_register_duplicate_email_returns_400(client: TestClient, session: Session):
    """Rejet d'une inscription si l'email existe déjà."""
    existing_user = User(
        username="utilisateur_existant",
        email="doublon@example.com",
        hashed_password=hash_password("Pass123!"),
        role=UserRole.PARENT,
    )
    session.add(existing_user)
    session.commit()

    payload = {
        "username": "nouveau_pseudo",
        "email": "doublon@example.com",
        "password": "Password123!",
        "role": "PARENT",
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "déjà associée" in response.json()["detail"]


def test_auth_register_duplicate_username_returns_400(client: TestClient, session: Session):
    """Rejet d'une inscription si le nom d'utilisateur existe déjà."""
    existing_user = User(
        username="pseudo_unique",
        email="original@example.com",
        hashed_password=hash_password("Pass123!"),
        role=UserRole.PARENT,
    )
    session.add(existing_user)
    session.commit()

    payload = {
        "username": "pseudo_unique",
        "email": "autre@example.com",
        "password": "Password123!",
        "role": "PARENT",
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "déjà utilisé" in response.json()["detail"]


def test_auth_register_unauthorized_role_returns_400(client: TestClient):
    """Rejet d'une inscription si le rôle demandé est CHILD ou ADMIN."""
    # Test rôle CHILD interdit en public
    child_payload = {
        "username": "petit_enfant",
        "email": "enfant@example.com",
        "password": "Password123!",
        "role": "CHILD",
    }
    resp_child = client.post("/api/v1/auth/register", json=child_payload)
    assert resp_child.status_code == status.HTTP_400_BAD_REQUEST
    assert "autorisée uniquement pour les rôles PARENT et TEACHER" in resp_child.json()["detail"]

    # Test rôle ADMIN interdit en public
    admin_payload = {
        "username": "faux_admin",
        "email": "admin@example.com",
        "password": "Password123!",
        "role": "ADMIN",
    }
    resp_admin = client.post("/api/v1/auth/register", json=admin_payload)
    assert resp_admin.status_code == status.HTTP_400_BAD_REQUEST

