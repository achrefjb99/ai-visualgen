"""Suite de tests d'intégration CRUD et logique Parent-Enfant pour EduGenius AI.

Couvre :
- Création d'enfants par un parent connecté avec rattachement automatique parent_id (201).
- Création d'enfant sans email obligatoire.
- Rejet 401 si requête de création/modification non authentifiée.
- Rejet 403 si un profil enfant tente de créer un utilisateur.
- Isolation stricte des listes d'enfants via GET /api/v1/users/my-children.
- Filtrage par grade_level pour les enseignants sur GET /api/v1/users/my-children.
- Sécurisation PATCH et DELETE (200/204 pour le parent propriétaire, 403 pour un parent tiers).
- Conflits d'unicité (400) et ressources inexistantes (404).
- CRUD des cours et chapitres (cascade).
"""

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from app.database import get_session
from app.main import app
from app.models.shared import User, UserRole
from app.services.security import create_access_token, hash_password


# ==============================================================================
# FIXTURES DE TEST
# ==============================================================================


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
    """Fournit un TestClient FastAPI avec injection de la session de test."""
    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


def create_user_with_token(session: Session, username: str, role: UserRole = UserRole.PARENT) -> tuple[User, dict]:
    """Helper pour enregistrer un utilisateur et générer ses en-têtes d'authentification Bearer."""
    user = User(
        username=username,
        email=f"{username}@edugenius.kids",
        hashed_password=hash_password("SuperSecret123!"),
        role=role,
    )
    session.add(user)
    session.commit()
    session.refresh(user)

    token = create_access_token({
        "sub": str(user.id),
        "username": user.username,
        "role": user.role.value if isinstance(user.role, UserRole) else str(user.role),
    })
    return user, {"Authorization": f"Bearer {token}"}


# ==============================================================================
# TESTS LOGIQUE PARENT-ENFANT & AUTHENTIFICATION
# ==============================================================================


def test_create_and_get_child_user_nominal(client: TestClient, session: Session):
    """Cas nominal : Un parent connecté crée un profil enfant avec parent_id automatique."""
    parent, headers = create_user_with_token(session, "maman_claire", UserRole.PARENT)

    child_payload = {
        "username": "leo_astronaute",
        "email": "leo@edugenius.kids",
        "password": "SuperMotDePasse123!",
        "role": "CHILD",
        "age": 8,
        "grade_level": "CE1",
        "favorite_theme": "Espace & Galaxies",
    }

    create_response = client.post("/api/v1/users/", json=child_payload, headers=headers)
    assert create_response.status_code == status.HTTP_201_CREATED
    created_user = create_response.json()
    assert created_user["username"] == "leo_astronaute"
    assert created_user["parent_id"] == parent.id
    assert created_user["role"] == "CHILD"
    assert "password" not in created_user
    assert "hashed_password" not in created_user

    # Consultation par ID
    get_response = client.get(f"/api/v1/users/{created_user['id']}")
    assert get_response.status_code == status.HTTP_200_OK
    assert get_response.json()["parent_id"] == parent.id


def test_create_child_without_email_nominal(client: TestClient, session: Session):
    """L'enfant n'a pas besoin d'adresse email obligatoire."""
    parent, headers = create_user_with_token(session, "papa_thomas", UserRole.PARENT)

    child_payload = {
        "username": "maya_dinosaure",
        "role": "CHILD",
        "age": 7,
        "grade_level": "CP",
        "favorite_theme": "Dinosaures",
    }

    response = client.post("/api/v1/users/children", json=child_payload, headers=headers)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["username"] == "maya_dinosaure"
    assert data["email"] is None
    assert data["parent_id"] == parent.id


def test_create_child_unauthenticated_returns_401(client: TestClient):
    """Tentative de création d'un profil sans jeton d'authentification -> 401."""
    child_payload = {
        "username": "inconnu_sans_parent",
        "role": "CHILD",
        "age": 8,
    }
    response = client.post("/api/v1/users/", json=child_payload)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_child_cannot_create_profiles_returns_403(client: TestClient, session: Session):
    """Un profil enfant authentifié ne peut pas créer de nouveau profil -> 403."""
    child, headers = create_user_with_token(session, "enfant_hugo", UserRole.CHILD)

    new_payload = {
        "username": "autre_enfant",
        "role": "CHILD",
        "age": 6,
    }
    response = client.post("/api/v1/users/", json=new_payload, headers=headers)
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_get_my_children_isolation(client: TestClient, session: Session):
    """Vérifie l'isolation des listes : chaque parent ne voit que ses propres enfants."""
    parent_1, headers_1 = create_user_with_token(session, "parent_un", UserRole.PARENT)
    parent_2, headers_2 = create_user_with_token(session, "parent_deux", UserRole.PARENT)

    # Parent 1 crée 2 enfants
    client.post("/api/v1/users/children", json={"username": "enfant_1a", "role": "CHILD", "age": 7}, headers=headers_1)
    client.post("/api/v1/users/children", json={"username": "enfant_1b", "role": "CHILD", "age": 9}, headers=headers_1)

    # Parent 2 crée 1 enfant
    client.post("/api/v1/users/children", json={"username": "enfant_2a", "role": "CHILD", "age": 8}, headers=headers_2)

    # Parent 1 consulte my-children
    res_1 = client.get("/api/v1/users/my-children", headers=headers_1)
    assert res_1.status_code == status.HTTP_200_OK
    children_1 = res_1.json()
    assert len(children_1) == 2
    assert all(c["parent_id"] == parent_1.id for c in children_1)
    assert {c["username"] for c in children_1} == {"enfant_1a", "enfant_1b"}

    # Parent 2 consulte my-children
    res_2 = client.get("/api/v1/users/my-children", headers=headers_2)
    assert res_2.status_code == status.HTTP_200_OK
    children_2 = res_2.json()
    assert len(children_2) == 1
    assert children_2[0]["username"] == "enfant_2a"
    assert children_2[0]["parent_id"] == parent_2.id


def test_teacher_get_my_children_filter_by_grade_level(client: TestClient, session: Session):
    """Un enseignant peut filtrer les enfants par grade_level."""
    parent, parent_headers = create_user_with_token(session, "parent_groupe", UserRole.PARENT)
    teacher, teacher_headers = create_user_with_token(session, "prof_valerie", UserRole.TEACHER)

    client.post("/api/v1/users/children", json={"username": "eleve_ce1", "role": "CHILD", "grade_level": "CE1"}, headers=parent_headers)
    client.post("/api/v1/users/children", json={"username": "eleve_ce2", "role": "CHILD", "grade_level": "CE2"}, headers=parent_headers)

    res = client.get("/api/v1/users/my-children?grade_level=CE1", headers=teacher_headers)
    assert res.status_code == status.HTTP_200_OK
    results = res.json()
    assert len(results) == 1
    assert results[0]["username"] == "eleve_ce1"
    assert results[0]["grade_level"] == "CE1"


def test_update_child_by_owner_parent_nominal(client: TestClient, session: Session):
    """Le parent propriétaire peut modifier les informations de son enfant."""
    parent, headers = create_user_with_token(session, "parent_modificateur", UserRole.PARENT)

    child_res = client.post(
        "/api/v1/users/children",
        json={"username": "enfant_a_modifier", "role": "CHILD", "age": 7, "favorite_theme": "Dinos"},
        headers=headers,
    )
    child_id = child_res.json()["id"]

    patch_payload = {"age": 8, "favorite_theme": "Espace"}
    patch_res = client.patch(f"/api/v1/users/{child_id}", json=patch_payload, headers=headers)
    assert patch_res.status_code == status.HTTP_200_OK
    data = patch_res.json()
    assert data["age"] == 8
    assert data["favorite_theme"] == "Espace"


def test_update_child_by_another_parent_returns_403(client: TestClient, session: Session):
    """Un parent tiers ne peut pas modifier l'enfant d'un autre parent -> 403."""
    parent_1, headers_1 = create_user_with_token(session, "parent_proprietaire", UserRole.PARENT)
    parent_2, headers_2 = create_user_with_token(session, "parent_intrus", UserRole.PARENT)

    child_res = client.post(
        "/api/v1/users/children",
        json={"username": "enfant_protege", "role": "CHILD"},
        headers=headers_1,
    )
    child_id = child_res.json()["id"]

    patch_res = client.patch(f"/api/v1/users/{child_id}", json={"age": 10}, headers=headers_2)
    assert patch_res.status_code == status.HTTP_403_FORBIDDEN
    assert "Accès refusé" in patch_res.json()["detail"]


def test_delete_child_by_another_parent_returns_403(client: TestClient, session: Session):
    """Un parent tiers ne peut pas supprimer l'enfant d'un autre parent -> 403."""
    parent_1, headers_1 = create_user_with_token(session, "parent_owner", UserRole.PARENT)
    parent_2, headers_2 = create_user_with_token(session, "parent_voleur", UserRole.PARENT)

    child_res = client.post(
        "/api/v1/users/children",
        json={"username": "enfant_inattaquable", "role": "CHILD"},
        headers=headers_1,
    )
    child_id = child_res.json()["id"]

    delete_res = client.delete(f"/api/v1/users/{child_id}", headers=headers_2)
    assert delete_res.status_code == status.HTTP_403_FORBIDDEN


def test_delete_child_by_owner_parent_nominal(client: TestClient, session: Session):
    """Le parent propriétaire peut supprimer le profil de son enfant (204 -> 404)."""
    parent, headers = create_user_with_token(session, "parent_suppresseur", UserRole.PARENT)

    child_res = client.post(
        "/api/v1/users/children",
        json={"username": "enfant_a_supprimer", "role": "CHILD"},
        headers=headers,
    )
    child_id = child_res.json()["id"]

    delete_res = client.delete(f"/api/v1/users/{child_id}", headers=headers)
    assert delete_res.status_code == status.HTTP_204_NO_CONTENT

    get_res = client.get(f"/api/v1/users/{child_id}")
    assert get_res.status_code == status.HTTP_404_NOT_FOUND


def test_get_user_not_found_returns_404(client: TestClient):
    """Consultation d'un identifiant inexistant -> 404."""
    response = client.get("/api/v1/users/999999")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "introuvable" in response.json()["detail"].lower()


def test_create_user_duplicate_username_returns_400(client: TestClient, session: Session):
    """Conflit sur le nom d'utilisateur -> 400 Bad Request."""
    parent, headers = create_user_with_token(session, "parent_unique", UserRole.PARENT)

    client.post("/api/v1/users/children", json={"username": "emma_doublon", "role": "CHILD"}, headers=headers)
    conflict_res = client.post("/api/v1/users/children", json={"username": "emma_doublon", "role": "CHILD"}, headers=headers)

    assert conflict_res.status_code == status.HTTP_400_BAD_REQUEST
    assert "nom d'utilisateur est déjà utilisé" in conflict_res.json()["detail"]


# ==============================================================================
# TESTS CRUD : COURS & SUJETS (COURSES & TOPICS)
# ==============================================================================


def test_create_and_get_course_nominal(client: TestClient, session: Session):
    """Création d'un cours avec enseignant puis lecture (201 -> 200)."""
    teacher, teacher_headers = create_user_with_token(session, "prof_sophie", UserRole.TEACHER)

    course_payload = {
        "title": "Les secrets des océans",
        "description": "Découverte de la faune et de la flore sous-marine.",
        "subject": "Sciences & Nature",
        "grade_level": "CE2",
        "teacher_id": teacher.id,
    }

    create_course_res = client.post("/api/v1/courses/", json=course_payload, headers=teacher_headers)
    assert create_course_res.status_code == status.HTTP_201_CREATED
    course_data = create_course_res.json()
    course_id = course_data["id"]

    get_course_res = client.get(f"/api/v1/courses/{course_id}")
    assert get_course_res.status_code == status.HTTP_200_OK
    fetched_course = get_course_res.json()
    assert fetched_course["title"] == "Les secrets des océans"
    assert fetched_course["teacher_id"] == teacher.id
    assert fetched_course["teacher"]["username"] == "prof_sophie"


def test_get_course_not_found_returns_404(client: TestClient):
    """Tentative de consultation d'un cours inexistant (404)."""
    response = client.get("/api/v1/courses/77777")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "introuvable" in response.json()["detail"].lower()


def test_create_course_with_invalid_teacher_returns_400(client: TestClient, session: Session):
    """Création d'un cours par un admin avec teacher_id inexistant (400)."""
    _, admin_headers = create_user_with_token(session, "admin_math", UserRole.ADMIN)
    invalid_course_payload = {
        "title": "Mathématiques Magiques",
        "description": "Apprendre à compter en s'amusant",
        "subject": "Mathématiques",
        "grade_level": "CP",
        "teacher_id": 999999,
    }
    response = client.post("/api/v1/courses/", json=invalid_course_payload, headers=admin_headers)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "n'existe pas" in response.json()["detail"].lower()


def test_delete_course_and_cascade_topics(client: TestClient, session: Session):
    """Suppression d'un cours par son enseignant créateur et cascade sur ses chapitres."""
    teacher, teacher_headers = create_user_with_token(session, "prof_chateaux", UserRole.TEACHER)
    course_payload = {
        "title": "Histoire des Châteaux Forts",
        "description": "La vie au Moyen Âge racontée aux enfants.",
        "subject": "Histoire",
        "grade_level": "CM1",
    }
    course_id = client.post("/api/v1/courses/", json=course_payload, headers=teacher_headers).json()["id"]

    topic_payload = {
        "course_id": course_id,
        "name": "Les Chevaliers et leurs Armures",
        "summary_kid": "Les chevaliers portaient des armures en métal pour se protéger lors des tournois !",
    }
    topic_id = client.post("/api/v1/topics/", json=topic_payload).json()["id"]

    delete_course_res = client.delete(f"/api/v1/courses/{course_id}", headers=teacher_headers)
    assert delete_course_res.status_code == status.HTTP_204_NO_CONTENT

    assert client.get(f"/api/v1/courses/{course_id}").status_code == status.HTTP_404_NOT_FOUND
    assert client.get(f"/api/v1/topics/{topic_id}").status_code == status.HTTP_404_NOT_FOUND


def test_course_teacher_security_and_permissions(client: TestClient, session: Session):
    """Vérifie la restriction de création et suppression aux seuls enseignants / admin autorisés."""
    teacher_1, headers_teacher_1 = create_user_with_token(session, "prof_one", UserRole.TEACHER)
    teacher_2, headers_teacher_2 = create_user_with_token(session, "prof_two", UserRole.TEACHER)
    _, parent_headers = create_user_with_token(session, "parent_user", UserRole.PARENT)
    _, admin_headers = create_user_with_token(session, "admin_user", UserRole.ADMIN)

    course_data = {
        "title": "Botanique Enfantine",
        "subject": "SVT",
        "grade_level": "CE1",
    }

    # 1. Non authentifié -> 401
    assert client.post("/api/v1/courses/", json=course_data).status_code == status.HTTP_401_UNAUTHORIZED

    # 2. Rôle Parent -> 403 Forbidden
    parent_res = client.post("/api/v1/courses/", json=course_data, headers=parent_headers)
    assert parent_res.status_code == status.HTTP_403_FORBIDDEN

    # 3. Création par prof_one -> 201 avec teacher_id automatique
    create_res = client.post("/api/v1/courses/", json=course_data, headers=headers_teacher_1)
    assert create_res.status_code == status.HTTP_201_CREATED
    course_id = create_res.json()["id"]
    assert create_res.json()["teacher_id"] == teacher_1.id

    # 4. Suppression par un parent -> 403
    assert client.delete(f"/api/v1/courses/{course_id}", headers=parent_headers).status_code == status.HTTP_403_FORBIDDEN

    # 5. Suppression par un autre prof -> 403
    assert client.delete(f"/api/v1/courses/{course_id}", headers=headers_teacher_2).status_code == status.HTTP_403_FORBIDDEN

    # 6. Suppression par l'enseignant créateur -> 204
    assert client.delete(f"/api/v1/courses/{course_id}", headers=headers_teacher_1).status_code == status.HTTP_204_NO_CONTENT

    # 7. Un admin peut créer et supprimer n'importe quel cours
    admin_course_id = client.post("/api/v1/courses/", json=course_data, headers=admin_headers).json()["id"]
    assert client.delete(f"/api/v1/courses/{admin_course_id}", headers=admin_headers).status_code == status.HTTP_204_NO_CONTENT


def test_create_topic_with_invalid_course_returns_404(client: TestClient):
    """Rattachement d'un chapitre à un cours inexistant -> 404."""
    orphan_topic = {
        "course_id": 99999,
        "name": "Chapitre Fantôme",
        "summary_kid": "Ce chapitre ne doit pas pouvoir être créé.",
    }
    response = client.post("/api/v1/topics/", json=orphan_topic)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "n'existe pas" in response.json()["detail"].lower()


def test_update_child_by_owner_parent_nominal(client: TestClient, session: Session):
    """Le parent propriétaire peut mettre à jour les données de son enfant."""
    parent, parent_headers = create_user_with_token(session, "parent_julie", UserRole.PARENT)

    # Inscription de l'enfant
    child_payload = {
        "username": "leo_aventurier",
        "role": "CHILD",
        "age": 7,
        "grade_level": "2ème primaire (CE1)",
        "favorite_theme": "Dinosaures",
    }
    child_res = client.post("/api/v1/users/children", json=child_payload, headers=parent_headers)
    assert child_res.status_code == status.HTTP_201_CREATED
    child_id = child_res.json()["id"]

    # Modification de l'âge, de la classe et du thème
    update_payload = {
        "age": 8,
        "grade_level": "3ème primaire (CE2)",
        "favorite_theme": "Espace",
        "username": "leo_cosmonaute",
    }
    patch_res = client.patch(
        f"/api/v1/users/children/{child_id}",
        json=update_payload,
        headers=parent_headers,
    )
    assert patch_res.status_code == status.HTTP_200_OK
    data = patch_res.json()
    assert data["age"] == 8
    assert data["grade_level"] == "3ème primaire (CE2)"
    assert data["favorite_theme"] == "Espace"
    assert data["username"] == "leo_cosmonaute"


def test_update_child_by_other_parent_returns_403(client: TestClient, session: Session):
    """Un parent tiers ne peut pas modifier l'enfant d'un autre parent (403)."""
    parent_1, headers_1 = create_user_with_token(session, "parent_1", UserRole.PARENT)
    parent_2, headers_2 = create_user_with_token(session, "parent_2", UserRole.PARENT)

    # Parent 1 crée son enfant
    child_payload = {
        "username": "enfant_de_parent_1",
        "role": "CHILD",
        "age": 6,
        "grade_level": "CP",
        "favorite_theme": "Magie",
    }
    child_res = client.post("/api/v1/users/children", json=child_payload, headers=headers_1)
    child_id = child_res.json()["id"]

    # Parent 2 tente de modifier l'enfant de Parent 1
    update_payload = {"age": 9, "favorite_theme": "Animaux"}
    patch_res = client.patch(
        f"/api/v1/users/children/{child_id}",
        json=update_payload,
        headers=headers_2,
    )
    assert patch_res.status_code == status.HTTP_403_FORBIDDEN
    assert "Non autorisé" in patch_res.json()["detail"]


def test_update_child_non_existent_returns_404(client: TestClient, session: Session):
    """Tentative de modification d'un profil enfant inexistant -> 404."""
    parent, parent_headers = create_user_with_token(session, "parent_test_404", UserRole.PARENT)
    patch_res = client.patch(
        "/api/v1/users/children/99999",
        json={"age": 10},
        headers=parent_headers,
    )
    assert patch_res.status_code == status.HTTP_404_NOT_FOUND

