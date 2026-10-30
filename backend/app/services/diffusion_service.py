import os
from pathlib import Path
from typing import Optional

from diffusers import StableDiffusionPipeline

_pipeline = None
_lora_loaded: bool = False


def get_pipeline(lora_path: Optional[str] = None):
    global _pipeline, _lora_loaded
    # pyrefly: ignore[missing-import]
    import torch
    if _pipeline is None:
        model_id = os.getenv("MODEL_ID", "stabilityai/sd-turbo")
        device = os.getenv("DEVICE", "cuda" if torch.cuda.is_available() else "cpu")
        if device == "cuda" and not torch.cuda.is_available():
            device = "cpu"
        dtype = torch.float16 if (device == "cuda" and torch.cuda.is_available()) else torch.float32
        _pipeline = StableDiffusionPipeline.from_pretrained(
            model_id, torch_dtype=dtype, safety_checker=None, requires_safety_checker=False
        )
        _pipeline = _pipeline.to(device)
        _lora_loaded = False

    lora = lora_path or os.getenv("LORA_PATH")
    if lora and Path(lora).exists() and not _lora_loaded:
        _pipeline.load_lora_weights(lora)
        _lora_loaded = True
    return _pipeline
