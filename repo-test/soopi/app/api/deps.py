from dataclasses import dataclass
from typing import Annotated
from uuid import UUID

from fastapi import Depends, Header
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session_factory
from app.core.exceptions import AppError
from app.core.security import aware, decode_access, now
from app.models.user import User
from app.repositories.user_repo import RefreshSessionRepository, UserRepository

bearer = HTTPBearer(auto_error=False)


async def get_db():
    async with get_session_factory()() as session:
        try:
            yield session
            await session.commit()
        except BaseException:
            await session.rollback()
            raise


# A function-scoped yield dependency commits before the response is sent.
DB = Annotated[AsyncSession, Depends(get_db, scope="function")]
Credentials = Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)]
GuestToken = Annotated[str | None, Header(alias="X-Guest-Token", min_length=40, max_length=200)]


@dataclass(frozen=True)
class Identity:
    user: User
    session_id: UUID


async def optional_identity(db: DB, credentials: Credentials) -> Identity | None:
    if credentials is None:
        return None
    user_id, session_id = decode_access(credentials.credentials)
    refresh = await RefreshSessionRepository(db).get(session_id)
    user = await UserRepository(db).get(user_id)
    if (
        not refresh
        or refresh.user_id != user_id
        or refresh.revoked_at
        or aware(refresh.expires_at) <= now()
        or not user
        or not user.is_active
    ):
        raise AppError(401, "invalid_session", "Invalid or expired session")
    return Identity(user=user, session_id=session_id)


OptionalIdentity = Annotated[Identity | None, Depends(optional_identity)]


async def require_identity(identity: OptionalIdentity) -> Identity:
    if identity is None:
        raise AppError(401, "authentication_required", "Authentication required")
    return identity


CurrentIdentity = Annotated[Identity, Depends(require_identity)]


async def require_admin(identity: CurrentIdentity) -> Identity:
    if not identity.user.is_admin:
        raise AppError(403, "forbidden", "Administrator permission required")
    return identity


AdminIdentity = Annotated[Identity, Depends(require_admin)]
