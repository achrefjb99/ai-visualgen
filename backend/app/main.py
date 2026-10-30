import logging
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response
from starlette.responses import JSONResponse
from app.config import settings
from app.database import init_db
from app.routers import auth_router, content_router, users_router
from app.routers.module2 import router as module2_router
from app.routers.tutor import router as tutor_router
from app.routers.assessment import router as assessment_router
from app.routers.visuals import router as visuals_router
from app.routers.visualgen import router as visualgen_router
app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
)

logger = logging.getLogger(__name__)

@app.middleware("http")
async def handle_unexpected_errors(request: Request, call_next: RequestResponseEndpoint) -> Response:
    try:
        return await call_next(request)
    except Exception:
        logger.exception("Unhandled API error for %s %s", request.method, request.url.path)
        return JSONResponse(status_code=500, content={"detail": "Une erreur interne est survenue. Réessaie ou consulte les journaux du backend."})

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(dict.fromkeys([
        "http://localhost:4200",
        "http://127.0.0.1:4200",
        *[origin.strip() for origin in os.getenv("CORS_ORIGINS", "").split(",") if origin.strip()],
    ])),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup_database():
    init_db()

# Enregistrement des routeurs d'API v1
app.include_router(auth_router, prefix=f"{settings.API_V1_STR}/auth")
app.include_router(users_router, prefix=settings.API_V1_STR)
app.include_router(content_router, prefix=settings.API_V1_STR)
app.include_router(module2_router, prefix=settings.API_V1_STR)
app.include_router(tutor_router, prefix=settings.API_V1_STR)
app.include_router(assessment_router, prefix=settings.API_V1_STR)
app.include_router(visuals_router, prefix=settings.API_V1_STR)
app.include_router(visualgen_router, prefix=settings.API_V1_STR)

@app.get("/")
def health_check():
    return {"status": "online", "project": settings.PROJECT_NAME}
