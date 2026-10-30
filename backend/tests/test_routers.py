"""Tests d'intégration complets pour les routeurs users.py et content.py."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from app.database import get_session
from app.main import app
from app.models.shared import User, UserRole
from app.services.security import create_access_token, hash_password


@pytest.fixture(name="session")
def session_fixture():
    """Crée une base de données SQLite en mémoire pour chaque test."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture(session: Session):
    """Client de test FastAPI avec injection de la session de test."""
    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


# ==============================================================================
# TESTS ROUTER USERS
# ==============================================================================


def test_users_crud_flow(client: TestClient, session: Session):
    """Teste le cycle de vie complet d'un utilisateur (Create, Read, Update, Delete)."""
    # Création d'un parent pour autoriser la création et la gestion de l'enfant
    parent = User(
        username="parent_crud",
        email="parent_crud@edugenius.kids",
        hashed_password=hash_password("ParentPass123!"),
        role=UserRole.PARENT,
    )
    session.add(parent)
    session.commit()
    session.refresh(parent)

    token = create_access_token({"sub": str(parent.id), "username": parent.username, "role": parent.role.value})
    headers = {"Authorization": f"Bearer {token}"}

    # 1. POST /api/v1/users/ - Création d'un profil enfant
    child_payload = {
        "username": "leo_explorer",
        "email": "leo@edugenius.kids",
        "password": "MotDePasseSecret123",
        "role": "CHILD",
        "age": 7,
        "grade_level": "CP",
        "favorite_theme": "Dinosaures",
    }
    response = client.post("/api/v1/users/", json=child_payload, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "leo_explorer"
    assert data["email"] == "leo@edugenius.kids"
    assert data["role"] == "CHILD"
    assert data["age"] == 7
    assert data["favorite_theme"] == "Dinosaures"
    assert "id" in data
    assert "created_at" in data
    assert "password" not in data
    assert "hashed_password" not in data
    user_id = data["id"]

    # 2. POST /api/v1/users/ - Erreur d'unicité (doublon username)
    duplicate_payload = child_payload.copy()
    duplicate_payload["email"] = "autre_email@test.com"
    dup_res = client.post("/api/v1/users/", json=duplicate_payload, headers=headers)
    assert dup_res.status_code == 400
    assert "nom d'utilisateur est déjà utilisé" in dup_res.json()["detail"]

    # 3. GET /api/v1/users/ - Liste avec filtres et pagination
    list_res = client.get("/api/v1/users/?offset=0&limit=10&role=CHILD")
    assert list_res.status_code == 200
    users_list = list_res.json()
    assert len(users_list) == 1
    assert users_list[0]["id"] == user_id

    # 4. GET /api/v1/users/{id} - Récupération par ID
    detail_res = client.get(f"/api/v1/users/{user_id}")
    assert detail_res.status_code == 200
    assert detail_res.json()["username"] == "leo_explorer"

    # 4b. GET /api/v1/users/{id} - 404 si introuvable
    not_found_res = client.get("/api/v1/users/99999")
    assert not_found_res.status_code == 404

    # 5. PATCH /api/v1/users/{id} - Mise à jour partielle (thème et mot de passe)
    patch_payload = {
        "favorite_theme": "Robots & Espace",
        "age": 8,
        "password": "NouveauMotDePasse456",
    }
    patch_res = client.patch(f"/api/v1/users/{user_id}", json=patch_payload, headers=headers)
    assert patch_res.status_code == 200
    updated_data = patch_res.json()
    assert updated_data["favorite_theme"] == "Robots & Espace"
    assert updated_data["age"] == 8

    # 6. DELETE /api/v1/users/{id} - Suppression
    delete_res = client.delete(f"/api/v1/users/{user_id}", headers=headers)
    assert delete_res.status_code == 204

    # Vérification que l'utilisateur n'existe plus
    check_deleted = client.get(f"/api/v1/users/{user_id}")
    assert check_deleted.status_code == 404


# ==============================================================================
# TESTS ROUTER CONTENT (COURSES & TOPICS)
# ==============================================================================


def test_courses_and_topics_crud_flow(client: TestClient, session: Session):
    """Teste le cycle complet des cours et des chapitres."""
    # Création préalable d'un enseignant en base
    teacher = User(
        username="prof_albert",
        email="albert@edugenius.kids",
        hashed_password=hash_password("TeacherPassword789"),
        role=UserRole.TEACHER,
    )
    session.add(teacher)
    session.commit()
    session.refresh(teacher)
    teacher_id = teacher.id

    teacher_token = create_access_token({"sub": str(teacher.id), "username": teacher.username, "role": teacher.role.value})
    teacher_headers = {"Authorization": f"Bearer {teacher_token}"}

    # 1. POST /api/v1/courses/ - Création d'un cours
    course_payload = {
        "title": "Introduction à l'Astronomie",
        "description": "Voyage à travers les planètes et étoiles de notre galaxie.",
        "subject": "Sciences",
        "grade_level": "CE2",
        "teacher_id": teacher_id,
    }
    course_res = client.post("/api/v1/courses/", json=course_payload, headers=teacher_headers)
    assert course_res.status_code == 201
    course_data = course_res.json()
    assert course_data["title"] == "Introduction à l'Astronomie"
    assert course_data["teacher_id"] == teacher_id
    course_id = course_data["id"]

    # 2. GET /api/v1/courses/ - Liste des cours avec filtres
    courses_list_res = client.get("/api/v1/courses/?subject=Sciences&grade_level=CE2")
    assert courses_list_res.status_code == 200
    assert len(courses_list_res.json()) == 1

    # 3. GET /api/v1/courses/{id} - Détail avec relation topics
    course_detail_res = client.get(f"/api/v1/courses/{course_id}")
    assert course_detail_res.status_code == 200
    assert course_detail_res.json()["topics"] == []
    assert course_detail_res.json()["teacher"]["username"] == "prof_albert"

    # 4. POST /api/v1/topics/ - Création d'un chapitre
    topic_payload = {
        "course_id": course_id,
        "name": "Le Soleil, notre étoile brillante",
        "summary_kid": "Le Soleil est une énorme boule de feu et de lumière qui nous réchauffe tous les jours !",
    }
    topic_res = client.post("/api/v1/topics/", json=topic_payload)
    assert topic_res.status_code == 201
    topic_data = topic_res.json()
    assert topic_data["name"] == "Le Soleil, notre étoile brillante"
    topic_id = topic_data["id"]

    # 4b. POST /api/v1/topics/ - Erreur si course_id inexistant
    bad_topic_res = client.post("/api/v1/topics/", json={
        "course_id": 99999,
        "name": "Chapitre Invalide",
        "summary_kid": "Test",
    })
    assert bad_topic_res.status_code == 404

    # 5. GET /api/v1/courses/{id}/topics - Chapitres du cours
    course_topics_res = client.get(f"/api/v1/courses/{course_id}/topics")
    assert course_topics_res.status_code == 200
    assert len(course_topics_res.json()) == 1
    assert course_topics_res.json()[0]["id"] == topic_id

    # 6. GET /api/v1/topics/{id} - Détail chapitre avec son cours parent
    topic_detail_res = client.get(f"/api/v1/topics/{topic_id}")
    assert topic_detail_res.status_code == 200
    assert topic_detail_res.json()["course"]["id"] == course_id

    # 7. PATCH /api/v1/topics/{id} - Mise à jour du résumé
    patch_topic_res = client.patch(f"/api/v1/topics/{topic_id}", json={
        "summary_kid": "Le Soleil est une étoile formidable qui apporte la vie sur Terre !"
    })
    assert patch_topic_res.status_code == 200
    assert "formidable" in patch_topic_res.json()["summary_kid"]

    # 8. PATCH /api/v1/courses/{id} - Mise à jour du titre du cours
    patch_course_res = client.patch(
        f"/api/v1/courses/{course_id}",
        json={"title": "L'Espace et les Étoiles"},
        headers=teacher_headers,
    )
    assert patch_course_res.status_code == 200
    assert patch_course_res.json()["title"] == "L'Espace et les Étoiles"

    # 9. DELETE /api/v1/topics/{id} - Suppression du chapitre
    del_topic_res = client.delete(f"/api/v1/topics/{topic_id}")
    assert del_topic_res.status_code == 204

    # 10. DELETE /api/v1/courses/{id} - Suppression du cours
    del_course_res = client.delete(f"/api/v1/courses/{course_id}", headers=teacher_headers)
    assert del_course_res.status_code == 204
    assert client.get(f"/api/v1/courses/{course_id}").status_code == 404
