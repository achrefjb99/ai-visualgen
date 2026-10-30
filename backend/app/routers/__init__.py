"""Module des routeurs FastAPI pour EduGenius AI."""

from app.routers.auth import router as auth_router
from app.routers.content import courses_router, router as content_router, topics_router
from app.routers.users import router as users_router

__all__ = [
    "auth_router",
    "users_router",
    "content_router",
    "courses_router",
    "topics_router",
]
