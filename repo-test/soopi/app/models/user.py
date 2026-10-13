from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, String, text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class User(BaseModel):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(320), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(120))
    phone: Mapped[str | None] = mapped_column(String(20))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=text("true"))
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, server_default=text("false"))


class Address(BaseModel):
    __tablename__ = "addresses"

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), index=True)
    recipient: Mapped[str] = mapped_column(String(120))
    phone: Mapped[str] = mapped_column(String(20))
    line1: Mapped[str] = mapped_column(String(255))
    ward: Mapped[str] = mapped_column(String(120))
    district: Mapped[str] = mapped_column(String(120))
    province: Mapped[str] = mapped_column(String(120))


class RefreshSession(BaseModel):
    __tablename__ = "refresh_sessions"

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
