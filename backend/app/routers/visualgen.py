"""FastAPI router for AI VisualGen — Text-to-Image module.

Endpoints:
  POST   /api/v1/visualgen/generate          → generate a new image
  GET    /api/v1/visualgen/images             → list gallery
  GET    /api/v1/visualgen/images/{image_id}  → stream PNG file
  DELETE /api/v1/visualgen/images/{image_id}  → delete image
  GET    /api/v1/visualgen/health             → service health
"""

import logging
import os
import re
from typing import Annotated, Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/visualgen", tags=["Module 6 - AI VisualGen"])

# ─── Pydantic schemas ──────────────────────────────────────────────────────────

VALID_STYLES = {"cartoon", "storybook", "watercolor", "comic", "diagram"}
VALID_LEVELS = {"primary", "middle"}

PROMPT_TEMPLATES = [
    {"id": "water_cycle",    "label": "Le cycle de l'eau",        "prompt": "Create a colorful cartoon showing the water cycle: sun heating the ocean, water evaporating, clouds forming, and rain falling over green mountains."},
    {"id": "solar_system",   "label": "Le système solaire",       "prompt": "Draw a fun educational illustration of the solar system with all planets labeled and the sun at the center, cartoon style for kids."},
    {"id": "photosynthesis", "label": "La photosynthèse",         "prompt": "Show how photosynthesis works in a simple diagram: a happy cartoon plant absorbing sunlight, water from roots, and releasing oxygen."},
    {"id": "human_body",     "label": "Le corps humain",          "prompt": "A friendly educational illustration of the human body showing the main organs labeled in a child-friendly way."},
    {"id": "animals",        "label": "Animaux et habitats",      "prompt": "Colorful illustration of different animal habitats: ocean, jungle, desert, and arctic, each with cute cartoon animals."},
    {"id": "fractions",      "label": "Les fractions",            "prompt": "Fun cartoon showing fractions using pizza slices, apples, and chocolate bars, colorful and easy to understand for children."},
    {"id": "food_chain",     "label": "La chaîne alimentaire",    "prompt": "Simple educational diagram of a food chain in a forest: grass, rabbit, fox, with arrows, cartoon style."},
    {"id": "volcanoes",      "label": "Les volcans",              "prompt": "Colorful cross-section diagram of a volcano showing magma, crater, and lava flow, educational and child-friendly."},
    {"id": "planets",        "label": "Les planètes",             "prompt": "Cute cartoon illustrations of each planet in the solar system with fun facts written around them."},
    {"id": "environment",    "label": "Protection de l'environnement", "prompt": "Happy cartoon children planting trees and recycling, colorful illustration about protecting the environment."},
]


class ImageGenRequest(BaseModel):
    prompt: str = Field(..., min_length=3, max_length=1000,
                        description="Description textuelle de l'image à générer.")
    style: str = Field("cartoon", description=f"Style visuel parmi : {VALID_STYLES}")
    educational_level: str = Field("primary",
                                   description=f"Niveau scolaire parmi : {VALID_LEVELS}")
    seed: Optional[int] = Field(None, ge=0, description="Graine aléatoire pour reproducibilité.")

    @field_validator("style")
    @classmethod
    def validate_style(cls, v: str) -> str:
        if v not in VALID_STYLES:
            raise ValueError(f"Style invalide. Choisissez parmi : {VALID_STYLES}")
        return v

    @field_validator("educational_level")
    @classmethod
    def validate_level(cls, v: str) -> str:
        if v not in VALID_LEVELS:
            raise ValueError(f"Niveau invalide. Choisissez parmi : {VALID_LEVELS}")
        return v


class ImageGenResponse(BaseModel):
    id: str
    status: str
    url: str
    prompt: str
    style: str
    level: str
    created_at: str
    generation_time_s: Optional[float] = None


# ─── Routes ───────────────────────────────────────────────────────────────────

@router.post("/generate", response_model=ImageGenResponse, status_code=201)
def generate_image(body: ImageGenRequest):
    """Generate an educational image from a text prompt using a diffusion model."""
    from app.services.image_service import generate_image as _generate

    try:
        meta = _generate(
            prompt=body.prompt,
            style=body.style,
            level=body.educational_level,
            seed=body.seed,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))

    return ImageGenResponse(
        id=meta["id"],
        status="completed",
        url=meta["url"],
        prompt=meta["prompt"],
        style=meta["style"],
        level=meta["level"],
        created_at=meta["created_at"],
        generation_time_s=meta.get("generation_time_s"),
    )


@router.get("/images", response_model=list[dict])
def list_images():
    """Return gallery metadata for all generated images."""
    from app.storage import image_storage
    return image_storage.list_images()


@router.get("/images/{image_id}")
def get_image(image_id: str):
    """Stream the generated PNG file.

    Path traversal is prevented by only allowing UUID-shaped identifiers.
    """
    if not re.fullmatch(r"[0-9a-f\-]{36}", image_id):
        raise HTTPException(status_code=400, detail="Identifiant invalide.")

    from app.storage import image_storage
    path = image_storage.get_image_path(image_id)
    if path is None:
        raise HTTPException(status_code=404, detail="Image introuvable.")

    return FileResponse(str(path), media_type="image/png")


@router.delete("/images/{image_id}", status_code=204)
def delete_image(image_id: str):
    """Delete a generated image and its metadata."""
    if not re.fullmatch(r"[0-9a-f\-]{36}", image_id):
        raise HTTPException(status_code=400, detail="Identifiant invalide.")

    from app.storage import image_storage
    deleted = image_storage.delete_image(image_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Image introuvable.")


@router.get("/health")
def health():
    """Return service health and model-load status."""
    try:
        from app.services import diffusion_service as ds
        model_loaded = ds._pipeline is not None
    except Exception:
        model_loaded = False

    cuda_available = os.getenv("DEVICE", "").lower() == "cuda"
    device = "cuda" if cuda_available else "cpu"

    return {
        "status": "ok",
        "model_loaded": model_loaded,
        "cuda_available": cuda_available,
        "device": device,
    }


@router.get("/templates")
def get_templates():
    """Return the list of educational prompt templates."""
    return PROMPT_TEMPLATES
