import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from uuid import UUID

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

from app.core.config import get_settings
from app.core.exceptions import AppError

password_hasher = PasswordHasher()
_dummy_hash = password_hasher.hash("timing-equalization-only")


def now() -> datetime:
    return datetime.now(UTC)


def aware(value: datetime) -> datetime:
    """SQLite test rows may omit timezone; production columns are timestamptz."""
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(password: str, hashed: str | None) -> bool:
    try:
        valid = password_hasher.verify(hashed or _dummy_hash, password)
        return valid and hashed is not None
    except (VerificationError, InvalidHashError):
        return False


def opaque_token() -> str:
    return secrets.token_urlsafe(48)


def token_digest(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def access_token(user_id: UUID, session_id: UUID) -> str:
    settings = get_settings()
    issued = now()
    return jwt.encode(
        {
            "sub": str(user_id),
            "sid": str(session_id),
            "type": "access",
            "iat": issued,
            "exp": issued + timedelta(minutes=settings.access_token_minutes),
            "iss": settings.jwt_issuer,
            "aud": settings.jwt_audience,
        },
        settings.jwt_secret.get_secret_value(),
        algorithm="HS256",
    )


def decode_access(token: str) -> tuple[UUID, UUID]:
    settings = get_settings()
    try:
        claims = jwt.decode(
            token,
            settings.jwt_secret.get_secret_value(),
            algorithms=["HS256"],
            issuer=settings.jwt_issuer,
            audience=settings.jwt_audience,
            options={"require": ["sub", "sid", "type", "iat", "exp", "iss", "aud"]},
        )
        if claims["type"] != "access":
            raise ValueError("Invalid token type")
        return UUID(claims["sub"]), UUID(claims["sid"])
    except (jwt.PyJWTError, ValueError, TypeError, KeyError) as exc:
        raise AppError(401, "invalid_token", "Invalid or expired access token") from exc
