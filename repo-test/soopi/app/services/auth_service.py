from datetime import timedelta

from starlette.concurrency import run_in_threadpool

from app.core.config import get_settings
from app.core.exceptions import AppError, conflict
from app.core.security import (
    access_token,
    aware,
    hash_password,
    now,
    opaque_token,
    token_digest,
    verify_password,
)
from app.repositories.user_repo import RefreshSessionRepository, UserRepository
from app.schemas.user import TokenPair
from app.services.cart_service import CartService


class AuthService:
    def __init__(self, session):
        self.session = session
        self.users = UserRepository(session)
        self.refreshes = RefreshSessionRepository(session)

    async def issue(self, user):
        token = opaque_token()
        settings = get_settings()
        refresh = await self.refreshes.create(
            {
                "user_id": user.id,
                "token_hash": token_digest(token),
                "expires_at": now() + timedelta(days=settings.refresh_token_days),
            }
        )
        return TokenPair(
            access_token=access_token(user.id, refresh.id),
            refresh_token=token,
            expires_in=settings.access_token_minutes * 60,
        )

    async def register(self, data):
        if await self.users.by_email(str(data.email)):
            raise conflict("Email already registered")
        user = await self.users.create(
            {
                "email": str(data.email).lower(),
                "full_name": data.full_name,
                "password_hash": await run_in_threadpool(
                    hash_password, data.password.get_secret_value()
                ),
            }
        )
        return await self.issue(user)

    async def login(self, data, guest_token=None):
        user = await self.users.by_email(str(data.email))
        valid = await run_in_threadpool(
            verify_password,
            data.password.get_secret_value(),
            user.password_hash if user else None,
        )
        if not valid or not user.is_active:
            raise AppError(401, "invalid_credentials", "Invalid email or password")
        if guest_token:
            await CartService(self.session).merge(user.id, guest_token)
        return await self.issue(user)

    async def refresh(self, token):
        refresh = await self.refreshes.by_token_hash(token_digest(token))
        if not refresh or refresh.revoked_at or aware(refresh.expires_at) <= now():
            raise AppError(401, "invalid_refresh", "Invalid or expired refresh token")
        user = await self.users.get(refresh.user_id)
        if not user or not user.is_active:
            raise AppError(401, "inactive_user", "Account is unavailable")
        refresh.revoked_at = now()
        return await self.issue(user)

    async def logout(self, session_id):
        refresh = await self.refreshes.get(session_id, lock=True)
        if refresh and not refresh.revoked_at:
            refresh.revoked_at = now()
            await self.session.flush()
