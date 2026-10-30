"""Moderation service for AI VisualGen.

This is a keyword-based safety filter. It blocks obviously inappropriate
prompts before sending them to the diffusion model.

NOTE: A keyword list alone is NOT a complete child-safety solution.
For production use, integrate a proper content-classification model
(e.g., a fine-tuned BERT/RoBERTa text classifier).
"""

import re

# Basic block-list – extend as needed
_BLOCKED_TERMS = [
    "nude", "naked", "sex", "porn", "violence", "gore", "blood",
    "kill", "death", "weapon", "gun", "drug", "alcohol", "cigarette",
    "hate", "racist", "sexist",
]

_COMPILED = re.compile(
    r"\b(" + "|".join(re.escape(t) for t in _BLOCKED_TERMS) + r")\b",
    re.IGNORECASE,
)


def is_safe(prompt: str) -> tuple[bool, str]:
    """Return (True, '') if the prompt is considered safe.
    Return (False, reason) when a problematic term is detected.
    """
    match = _COMPILED.search(prompt)
    if match:
        return False, f"Le contenu contient un terme non autorisé : '{match.group()}'"
    return True, ""
