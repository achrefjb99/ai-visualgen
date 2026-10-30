"""Tests unitaires pour les modèles SQLModel et schémas partagés EduGenius AI."""

from sqlmodel import Session, SQLModel, create_engine, select
from app.models.shared import (
    User,
    UserCreate,
    UserRead,
    UserUpdate,
    UserRole,
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
)


def test_user_schemas_and_crud():
    """Vérifie la création, lecture, validation et persistance d'un utilisateur."""
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)

    # 1. Validation UserCreate
    user_data = UserCreate(
        username="petit_astronaute",
        email="astronaute@edugenius.kids",
        password="supersecretpass",
        role=UserRole.CHILD,
        age=8,
        grade_level="CE2",
        favorite_theme="Espace & Fusées",
    )
    assert user_data.password == "supersecretpass"
    assert user_data.role == UserRole.CHILD

    # 2. Persistance dans la table User
    db_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password="hashed_" + user_data.password,
        role=user_data.role,
        age=user_data.age,
        grade_level=user_data.grade_level,
        favorite_theme=user_data.favorite_theme,
    )

    with Session(engine) as session:
        session.add(db_user)
        session.commit()
        session.refresh(db_user)

        assert db_user.id is not None
        assert db_user.created_at is not None

        # 3. Sérialisation UserRead (exclut le mot de passe)
        user_read = UserRead.model_validate(db_user)
        assert user_read.id == db_user.id
        assert not hasattr(user_read, "hashed_password")

        # 4. UserUpdate partiel
        update_data = UserUpdate(favorite_theme="Dinosaures")
        for key, value in update_data.model_dump(exclude_unset=True).items():
            setattr(db_user, key, value)
        session.add(db_user)
        session.commit()
        session.refresh(db_user)

        assert db_user.favorite_theme == "Dinosaures"


def test_relationships_cascade_and_nested_reads():
    """Vérifie les relations bidirectionnelles User <-> Course <-> Topic."""
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        # Enseignant
        teacher = User(
            username="prof_marie",
            email="marie@edugenius.kids",
            hashed_password="secure_teacher_hash",
            role=UserRole.TEACHER,
        )
        session.add(teacher)
        session.commit()
        session.refresh(teacher)

        # Cours
        course = Course(
            title="Les Mystères du Système Solaire",
            description="Découvrir les planètes de façon interactive et amusante.",
            subject="Sciences & Découverte",
            grade_level="CE1",
            teacher_id=teacher.id,
        )
        session.add(course)
        session.commit()
        session.refresh(course)

        # Sujets / Topics
        topic1 = Topic(
            course_id=course.id,
            name="La planète Mars",
            summary_kid="Mars est la planète rouge ! Elle a des volcans géants et des robots explorateurs.",
        )
        topic2 = Topic(
            course_id=course.id,
            name="La Lune et ses cratères",
            summary_kid="La Lune tourne autour de la Terre. Quand on la regarde, on voit de gros trous appelés cratères !",
        )
        session.add_all([topic1, topic2])
        session.commit()
        session.refresh(course)
        session.refresh(teacher)

        # Vérification relation Teacher -> Courses
        assert len(teacher.courses) == 1
        assert teacher.courses[0].title == "Les Mystères du Système Solaire"

        # Vérification relation Course -> Topics & Teacher
        assert course.teacher.username == "prof_marie"
        assert len(course.topics) == 2

        # Sérialisation enrichie CourseReadWithTopics
        course_read_nested = CourseReadWithTopics(
            id=course.id,
            title=course.title,
            description=course.description,
            subject=course.subject,
            grade_level=course.grade_level,
            teacher_id=course.teacher_id,
            created_at=course.created_at,
            teacher=UserRead.model_validate(teacher),
            topics=[TopicRead.model_validate(t) for t in course.topics],
        )
        assert len(course_read_nested.topics) == 2
        assert course_read_nested.teacher.username == "prof_marie"
