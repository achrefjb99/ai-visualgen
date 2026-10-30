"""Module 2 - Génération (RAG) : résumé, flashcards et glossaire ancrés dans le cours."""

import logging
import re

from app.services.gemini import generate_json

logger = logging.getLogger(__name__)

def generate_lesson_material(topic: str, context: str, age: int) -> dict:
    """Create curriculum-grounded material, with an extractive local fallback."""
    prompt = (
        "Tu es un tuteur scolaire bienveillant pour enfants. Utilise uniquement le contexte fourni; "
        "n'invente aucune information. R?ponds en JSON avec summary (string), flashcards "
        "(liste d'objets question/answer/image_hint/source) et glossary (liste word/definition). "
        f"Adapte les mots ? un enfant de {age} ans. Sujet: {topic}. Contexte du cours:\n{context[:12000]}"
    )
    result = _normalize_material(generate_json(prompt))
    if result:
        return {**result, "generation_mode": "ai"}
    logger.info("G?n?ration locale de secours pour le chapitre %s (?ge %s)", topic, age)
    return _local_lesson_material(topic, context)


def _normalize_material(value: object) -> dict | None:
    if not isinstance(value, dict) or not isinstance(value.get("summary"), str):
        return None
    flashcards, glossary = value.get("flashcards"), value.get("glossary", [])
    if not isinstance(flashcards, list) or not isinstance(glossary, list):
        return None
    cards = [
        {"question": item["question"], "answer": item["answer"], "image_hint": str(item.get("image_hint", "")), "source": index + 1}
        for index, item in enumerate(flashcards[:12])
        if isinstance(item, dict) and isinstance(item.get("question"), str) and isinstance(item.get("answer"), str)
    ]
    words = [
        {"word": item["word"], "definition": item["definition"]}
        for item in glossary[:20]
        if isinstance(item, dict) and isinstance(item.get("word"), str) and isinstance(item.get("definition"), str)
    ]
    summary = value["summary"].strip()[:3000]
    return {"insufficient": False, "summary": summary, "flashcards": cards, "glossary": words} if summary else None

def _local_lesson_material(topic: str, context: str) -> dict:
    """Build a small, extractive lesson directly from the indexed curriculum."""
    text = re.sub(r"\[\d+\]\s*", "", context)
    sentences = [
        sentence.strip(" \t\r\n-•")
        for sentence in re.split(r"(?<=[.!?])\s+|\n+", text)
        if len(sentence.strip()) >= 24
    ]
    if not sentences and text.strip():
        sentences = [text.strip()]

    selected = sentences[:6]
    summary = " ".join(sentences[:5])
    summary_words = summary.split()
    if len(summary_words) > 200:
        summary = " ".join(summary_words[:200]).rstrip(" ,;:") + "…"
    if not summary:
        summary = f"Relis les extraits du cours sur « {topic} » avec un adulte."

    flashcards = [
        {
            "question": f"Que faut-il retenir du passage {index + 1} sur « {topic} » ?",
            "answer": sentence,
            "image_hint": "",
            "source": index + 1,
        }
        for index, sentence in enumerate(selected)
    ]
    return {
        "insufficient": False,
        "summary": summary,
        "flashcards": flashcards,
        "glossary": [],
        "generation_mode": "local",
    }
