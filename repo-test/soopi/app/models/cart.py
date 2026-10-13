from datetime import datetime
from uuid import UUID

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class Cart(BaseModel):
    __tablename__ = "carts"
    __table_args__ = (
        CheckConstraint(
            "(user_id IS NOT NULL AND guest_token_hash IS NULL) OR "
            "(user_id IS NULL AND guest_token_hash IS NOT NULL AND expires_at IS NOT NULL)",
            name="single_owner",
        ),
    )

    user_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"), unique=True)
    guest_token_hash: Mapped[str | None] = mapped_column(String(64), unique=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    items: Mapped[list["CartItem"]] = relationship(
        lazy="raise",
        cascade="all, delete-orphan",
        back_populates="cart",
    )


class CartItem(BaseModel):
    __tablename__ = "cart_items"
    __table_args__ = (
        UniqueConstraint("cart_id", "variant_id"),
        CheckConstraint("quantity > 0 AND quantity <= 999", name="valid_quantity"),
    )

    cart_id: Mapped[UUID] = mapped_column(ForeignKey("carts.id", ondelete="CASCADE"), index=True)
    variant_id: Mapped[UUID] = mapped_column(ForeignKey("product_variants.id"))
    quantity: Mapped[int]
    cart: Mapped[Cart] = relationship(lazy="raise", back_populates="items")
