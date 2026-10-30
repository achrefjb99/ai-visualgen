"""Module 2 - Briques du RAG : découpage, embeddings, recherche par similarité."""

import hashlib
import logging
import re
import unicodedata

from google import genai
from google.genai import types

from app.config import settings

logger = logging.getLogger(__name__)

EMB_DIM = 768  # vecteurs plus légers à stocker en base
STOPWORDS = {"le", "la", "les", "un", "une", "des", "du", "de", "d", "et", "en", "a", "à", "the", "a", "an", "of", "and", "in", "on"}

def _tokens(text: str) -> list[str]:
    normalized = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().lower()
    return [word for word in re.findall(r"\w+", normalized) if word not in STOPWORDS]


def _local_embed(text: str) -> list[float]:
    """Stable feature-hash embedding generated entirely on this machine."""
    vector = [0.0] * EMB_DIM
    words = _tokens(text)
    for word in words:
        digest = hashlib.blake2b(word.encode(), digest_size=8).digest()
        index = int.from_bytes(digest[:4], "little") % EMB_DIM
        vector[index] += 1.0 if digest[4] % 2 else -1.0
    norm = sum(value * value for value in vector) ** 0.5 or 1.0
    # Extra dimension marks a local vector, so old/local indexes use lexical ranking.
    return [value / norm for value in vector] + [1.0]


def _lexical_retrieve(query: str, chunks: list, k: int) -> list[tuple[float, object]]:
    terms = set(_tokens(query))
    ranked = []
    for chunk in chunks:
        content = set(_tokens(chunk.content))
        score = len(terms & content) / max(1, len(terms))
        ranked.append((score, chunk))
    return sorted(ranked, key=lambda item: item[0], reverse=True)[:k]


def _is_local(vector: list[float]) -> bool:
    return len(vector) == EMB_DIM + 1 and vector[-1] == 1.0


_CLIENT: genai.Client | None = None
_CLIENT_KEY: str | None = None


def get_client() -> genai.Client:
    """Create a Gemini client only when a key is explicitly configured."""
    global _CLIENT, _CLIENT_KEY
    api_key = settings.google_api_key
    if not api_key:
        raise RuntimeError("No Gemini API key configured")
    if _CLIENT is None or _CLIENT_KEY != api_key:
        _CLIENT = genai.Client(api_key=api_key, http_options=types.HttpOptions(timeout=30_000))
        _CLIENT_KEY = api_key
    return _CLIENT


def _embed_remote(texts: list[str], task_type: str) -> list[list[float]]:
    result: list[list[float]] = []
    for offset in range(0, len(texts), 50):
        response = get_client().models.embed_content(
            model="gemini-embedding-001",
            contents=texts[offset:offset + 50],
            config=types.EmbedContentConfig(task_type=task_type, output_dimensionality=EMB_DIM),
        )
        result.extend([embedding.values for embedding in response.embeddings])
    return result


def chunk_text(text: str, size: int = 800, overlap: int = 120) -> list[str]:
    """Découpe le texte en morceaux d'environ `size` caractères, en coupant
    de préférence à la fin d'une phrase, avec un chevauchement `overlap`."""
    text = re.sub(r"\s+", " ", text).strip()
    chunks, start = [], 0
    while start < len(text):
        end = min(start + size, len(text))
        if end < len(text):
            cut = text.rfind(". ", start + size // 2, end)
            if cut != -1:
                end = cut + 1
        piece = text[start:end].strip()
        if piece:
            chunks.append(piece)
        if end >= len(text):
            break
        start = max(end - overlap, start + 1)
    return chunks


def embed_documents(texts: list[str]) -> list[list[float]]:
    """Use Gemini embeddings when configured; always fall back to deterministic local vectors."""
    if settings.google_api_key:
        try:
            vectors = _embed_remote(texts, "RETRIEVAL_DOCUMENT")
            if len(vectors) != len(texts) or any(len(vector) != EMB_DIM for vector in vectors):
                raise ValueError("Gemini returned an invalid document embedding batch")
            return vectors
        except Exception as error:
            logger.warning("Gemini embeddings unavailable; using local vectors: %s", error)
    return [_local_embed(text) for text in texts]


def embed_query(query: str) -> list[float]:
    """Use a remote query vector when configured, with a local fallback."""
    if settings.google_api_key:
        try:
            vector = _embed_remote([query], "RETRIEVAL_QUERY")[0]
            if len(vector) != EMB_DIM:
                raise ValueError("Gemini returned an invalid query embedding")
            return vector
        except Exception as error:
            logger.warning("Gemini query embedding unavailable; using local search: %s", error)
    return _local_embed(query)


def retrieve(query: str, chunks: list, k: int = 5) -> list[tuple[float, object]]:
    """Use semantic Gemini vectors when both sides have them; otherwise rank locally."""
    if not chunks:
        return []
    query_vector = embed_query(query)
    if _is_local(query_vector) or any(_is_local(chunk.embedding) for chunk in chunks):
        return _lexical_retrieve(query, chunks, k)
    if len(query_vector) != EMB_DIM or any(len(chunk.embedding) != EMB_DIM for chunk in chunks):
        return _lexical_retrieve(query, chunks, k)

    import numpy as np

    query_array = np.asarray(query_vector, dtype=float)
    matrix = np.asarray([chunk.embedding for chunk in chunks], dtype=float)
    scores = (matrix @ query_array) / (np.linalg.norm(matrix, axis=1) * np.linalg.norm(query_array) + 1e-9)
    order = np.argsort(scores)[::-1][:k]
    return [(float(scores[index]), chunks[index]) for index in order]
