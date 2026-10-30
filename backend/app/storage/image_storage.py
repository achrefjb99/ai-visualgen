"""Image storage helpers for AI VisualGen.

Images are saved under OUTPUT_DIR (default: generated_images/).
Metadata is kept in a simple JSON index file inside the same directory.
The storage implementation is intentionally kept modular so it can be
replaced later with S3, a database, etc.
"""

import json
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from PIL import Image

_OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", "generated_images"))
_INDEX_FILE = _OUTPUT_DIR / "_index.json"


def _ensure_dir() -> None:
    _OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def _load_index() -> dict:
    _ensure_dir()
    if _INDEX_FILE.exists():
        try:
            return json.loads(_INDEX_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def _save_index(index: dict) -> None:
    _ensure_dir()
    _INDEX_FILE.write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")


def save_image(image: Image.Image, prompt: str, style: str, level: str) -> dict:
    """Save a PIL image to disk and record its metadata.

    Returns the metadata dict for this image.
    """
    _ensure_dir()
    image_id = str(uuid.uuid4())
    filename = f"{image_id}.png"
    filepath = _OUTPUT_DIR / filename
    image.save(filepath, format="PNG")

    meta = {
        "id": image_id,
        "filename": filename,
        "prompt": prompt,
        "style": style,
        "level": level,
        "created_at": datetime.utcnow().isoformat(),
        "url": f"/api/v1/visualgen/images/{image_id}",
    }

    index = _load_index()
    index[image_id] = meta
    _save_index(index)
    return meta


def get_image_meta(image_id: str) -> Optional[dict]:
    """Return metadata for a single image, or None if not found."""
    index = _load_index()
    return index.get(image_id)


def get_image_path(image_id: str) -> Optional[Path]:
    """Return the absolute Path to the PNG file, or None if not found."""
    meta = get_image_meta(image_id)
    if meta is None:
        return None
    path = _OUTPUT_DIR / meta["filename"]
    return path if path.exists() else None


def list_images() -> list[dict]:
    """Return all image metadata records, sorted newest first."""
    index = _load_index()
    return sorted(index.values(), key=lambda m: m["created_at"], reverse=True)


def delete_image(image_id: str) -> bool:
    """Delete the PNG file and its metadata. Returns True on success."""
    index = _load_index()
    meta = index.pop(image_id, None)
    if meta is None:
        return False
    path = _OUTPUT_DIR / meta["filename"]
    if path.exists():
        path.unlink()
    _save_index(index)
    return True
