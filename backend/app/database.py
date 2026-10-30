from sqlalchemy import inspect
from sqlmodel import SQLModel, create_engine, Session
from app.config import settings

engine_options = {"echo": False, "pool_pre_ping": True}
if settings.DATABASE_URL.startswith("sqlite"):
    engine_options["connect_args"] = {"check_same_thread": False}

engine = create_engine(settings.DATABASE_URL, **engine_options)


def init_db():
    SQLModel.metadata.create_all(engine)
    inspector = inspect(engine)
    tables = inspector.get_table_names()

    # Migration auto : users.parent_id et users.email
    if "users" in tables:
        user_columns = {column["name"]: column for column in inspector.get_columns("users")}
        if "parent_id" not in user_columns:
            with engine.begin() as connection:
                connection.exec_driver_sql("ALTER TABLE users ADD COLUMN parent_id INTEGER NULL")
                if engine.dialect.name != "sqlite":
                    try:
                        connection.exec_driver_sql(
                            "ALTER TABLE users ADD CONSTRAINT fk_users_parent_id FOREIGN KEY (parent_id) REFERENCES users(id) ON DELETE SET NULL"
                        )
                    except Exception:
                        pass
        if "email" in user_columns and not user_columns["email"]["nullable"]:
            if engine.dialect.name != "sqlite":
                with engine.begin() as connection:
                    connection.exec_driver_sql("ALTER TABLE users MODIFY COLUMN email VARCHAR(255) NULL")

    # Migration auto : learning_quiz_attempts.child_id
    if "learning_quiz_attempts" in tables:
        columns = {column["name"] for column in inspector.get_columns("learning_quiz_attempts")}
        if "child_id" not in columns:
            with engine.begin() as connection:
                connection.exec_driver_sql("ALTER TABLE learning_quiz_attempts ADD COLUMN child_id INTEGER NULL")


def get_session():
    with Session(engine) as session:
        yield session
