"""Image generation service for AI VisualGen.

This service coordinates:
1. Input validation
2. Prompt moderation
3. Educational prompt enrichment
4. Diffusion model inference (via diffusion_service)
5. Image persistence (via image_storage)

The diffusion pipeline is loaded lazily and kept in memory between requests.
If torch / diffusers are not installed, or the model download has not been
completed, the service raises a clear RuntimeError rather than returning a
fake image.
"""

import os
import time
import logging
from typing import Optional

logger = logging.getLogger(__name__)

MAX_PROMPT_LENGTH = int(os.getenv("MAX_PROMPT_LENGTH", "1000"))
IMAGE_WIDTH       = int(os.getenv("IMAGE_WIDTH",        "256"))
IMAGE_HEIGHT      = int(os.getenv("IMAGE_HEIGHT",       "256"))
NUM_STEPS         = int(os.getenv("NUM_INFERENCE_STEPS", "4"))
GUIDANCE_SCALE    = float(os.getenv("GUIDANCE_SCALE",    "7.0"))

# --- style conditioning text ---
STYLE_PROMPTS: dict[str, str] = {
    "cartoon":    "cartoon style, bright colors, fun, child-friendly illustration",
    "storybook":  "children's storybook illustration, warm colors, whimsical",
    "watercolor": "soft watercolor painting, pastel colors, educational",
    "comic":      "comic book illustration, bold outlines, vibrant colors",
    "diagram":    "simple educational diagram, clean lines, labeled, minimal",
}

LEVEL_PROMPTS: dict[str, str] = {
    "primary": "simple, colorful, age 6-10, easy to understand",
    "middle":  "detailed, educational, age 11-14, informative",
}


def _enrich_prompt(prompt: str, style: str, level: str) -> str:
    style_text = STYLE_PROMPTS.get(style, STYLE_PROMPTS["cartoon"])
    level_text = LEVEL_PROMPTS.get(level, LEVEL_PROMPTS["primary"])
    return (
        f"{prompt.strip()}, {style_text}, {level_text}, "
        "high quality, educational illustration, safe for kids"
    )


def generate_image(
    prompt: str,
    style: str = "cartoon",
    level: str = "primary",
    seed: Optional[int] = None,
) -> dict:
    """Run the full text-to-image pipeline.

    Returns a metadata dict on success (same shape as image_storage.save_image).
    Raises ValueError for bad input, RuntimeError for generation failures.
    """
    from app.services.moderation_service import is_safe
    from app.storage import image_storage

    # 1. Validate
    if not prompt or not prompt.strip():
        raise ValueError("Le prompt ne peut pas être vide.")
    if len(prompt) > MAX_PROMPT_LENGTH:
        raise ValueError(f"Le prompt est trop long (max {MAX_PROMPT_LENGTH} caractères).")

    # 2. Moderate
    safe, reason = is_safe(prompt)
    if not safe:
        raise ValueError(f"Contenu non autorisé : {reason}")

    # 3. Enrich prompt
    enriched = _enrich_prompt(prompt, style, level)
    logger.info("VisualGen: generating image — style=%s level=%s", style, level)

    # 4. Load pipeline & generate
    try:
        from app.services.diffusion_service import get_pipeline
        try:
            import torch
        except ImportError:
            torch = None

        pipeline = get_pipeline()

        generator = None
        if seed is not None and torch is not None:
            generator = torch.Generator(device=pipeline.device.type).manual_seed(seed)

        t0 = time.time()
        output = pipeline(
            prompt=enriched,
            width=IMAGE_WIDTH,
            height=IMAGE_HEIGHT,
            num_inference_steps=NUM_STEPS,
            guidance_scale=GUIDANCE_SCALE,
            generator=generator,
        )
        elapsed = round(time.time() - t0, 2)
        logger.info("VisualGen: generation took %ss", elapsed)

        pil_image = output.images[0]

    except ImportError as exc:
        raise RuntimeError(
            "Les dépendances de génération d'images (torch / diffusers) ne sont pas installées. "
            "Exécutez : pip install torch diffusers"
        ) from exc
    except Exception as exc:
        logger.exception("VisualGen: generation failed")
        raise RuntimeError(f"Échec de la génération : {exc}") from exc

    # 5. Save
    meta = image_storage.save_image(pil_image, prompt, style, level)
    meta["generation_time_s"] = elapsed
    return meta
