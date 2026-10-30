"""Optional structured Gemini generation with an explicit no-key fast path."""

import json
import logging
from typing import Any

from google.genai import types

from app.config import settings
from app.services.module2_rag import get_client

logger = logging.getLogger(__name__)
MODELS = ("gemini-2.5-flash", "gemini-2.0-flash")


def generate_json(prompt: str, *, temperature: float = 0.25) -> Any | None:
    """Return a JSON object/list, or None when remote generation is unavailable."""
    if not settings.google_api_key:
        return None

    for model in MODELS:
        try:
            response = get_client().models.generate_content(
                model=model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=temperature,
                    http_options=types.HttpOptions(timeout=40_000),
                ),
            )
            raw = (response.text or "").strip()
            if raw.startswith("```json"):
                raw = raw[7:]
            if raw.endswith("```"):
                raw = raw[:-3]
            value = json.loads(raw.strip())
            if isinstance(value, (dict, list)):
                return value
            raise ValueError("Gemini returned a non-structured response")
        except Exception as error:
            logger.warning("Structured generation with %s failed: %s", model, error)
    return None


def generate_text(prompt: str, *, temperature: float = 0.25) -> str | None:
    """Return generated text or None when remote generation is unavailable."""
    if not settings.google_api_key:
        return None
    for model in MODELS:
        try:
            response = get_client().models.generate_content(
                model=model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=temperature,
                    http_options=types.HttpOptions(timeout=40_000),
                ),
            )
            text = (response.text or "").strip()
            if text:
                return text
        except Exception as error:
            logger.warning("Text generation with %s failed: %s", model, error)
    return None
