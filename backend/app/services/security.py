"""Module de sécurité et cryptographie pour EduGenius AI.

Gère le hachage sécurisé des mots de passe (passlib / bcrypt)
et la génération/validation des jetons JWT (python-jose).
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import bcrypt

# Rétrocompatibilité passlib avec bcrypt >= 4.0 / 5.0
if not hasattr(bcrypt, "__about__"):
    class _About:
        __version__ = getattr(bcrypt, "__version__", "4.0.0")
    bcrypt.__about__ = _About()

_orig_hashpw = bcrypt.hashpw


def _safe_hashpw(password: bytes, salt: bytes) -> bytes:
    """Tronque à 72 octets max pour éviter l'exception ValueError de bcrypt >= 4.0."""
    if isinstance(password, (bytes, bytearray)) and len(password) > 72:
        password = password[:72]
    return _orig_hashpw(password, salt)


bcrypt.hashpw = _safe_hashpw

from jose import jwt
from passlib.context import CryptContext

from app.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Génère le hash sécurisé d'un mot de passe en clair."""
    return pwd_context.hash(password)


get_password_hash = hash_password


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Vérifie la correspondance entre un mot de passe en clair et son hash."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(
    data: dict[str, Any],
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Génère un jeton JWT d'accès avec horodatage d'expiration."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any]:
    """Décode et valide la signature cryptographique d'un jeton JWT."""
    return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])


__all__ = [
    "pwd_context",
    "hash_password",
    "verify_password",
    "create_access_token",
    "decode_access_token",
]
