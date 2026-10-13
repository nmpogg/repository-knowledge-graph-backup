import enum
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import (
    JSON,
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class OrderStatus(enum.StrEnum):
    pending = "pending"
    confirmed = "confirmed"
    shipped = "shipped"
    delivered = "delivered"
    cancelled = "cancelled"
    expired = "expired"


class PaymentMethod(enum.StrEnum):
    cod = "cod"
    momo = "momo"
    vnpay = "vnpay"


class PaymentStatus(enum.StrEnum):
    unpaid = "unpaid"
    paid = "paid"
    refund_required = "refund_required"


def enum_column(enum_cls):
    return Enum(
        enum_cls,
        native_enum=False,
        create_constraint=True,
        values_callable=lambda cls: [e.value for e in cls],
        name=enum_cls.__name__.lower(),
    )


class Order(BaseModel):
    __tablename__ = "orders"
    __table_args__ = (
        UniqueConstraint("user_id", "idempotency_key"),
        CheckConstraint("subtotal >= 0 AND shipping_fee >= 0", name="nonnegative_amounts"),
        CheckConstraint("total = subtotal + shipping_fee", name="correct_total"),
    )

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), index=True)
    idempotency_key: Mapped[str] = mapped_column(String(100))
    request_hash: Mapped[str] = mapped_column(String(64))
    status: Mapped[OrderStatus] = mapped_column(
        enum_column(OrderStatus), default=OrderStatus.pending
    )
    payment_method: Mapped[PaymentMethod] = mapped_column(enum_column(PaymentMethod))
    payment_status: Mapped[PaymentStatus] = mapped_column(
        enum_column(PaymentStatus),
        default=PaymentStatus.unpaid,
    )
    subtotal: Mapped[Decimal] = mapped_column(Numeric(14, 0))
    shipping_fee: Mapped[Decimal] = mapped_column(Numeric(14, 0))
    total: Mapped[Decimal] = mapped_column(Numeric(14, 0))
    shipping_address: Mapped[dict] = mapped_column(JSON)
    note: Mapped[str] = mapped_column(String(500), default="")
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    stock_released_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    items: Mapped[list["OrderItem"]] = relationship(lazy="raise", back_populates="order")


class OrderItem(BaseModel):
    __tablename__ = "order_items"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="positive_quantity"),
        CheckConstraint("unit_price >= 0", name="nonnegative_price"),
        CheckConstraint("line_total = unit_price * quantity", name="correct_total"),
    )

    order_id: Mapped[UUID] = mapped_column(ForeignKey("orders.id"), index=True)
    variant_id: Mapped[UUID] = mapped_column(ForeignKey("product_variants.id"))
    product_name: Mapped[str] = mapped_column(String(200))
    variant_name: Mapped[str] = mapped_column(String(120))
    sku: Mapped[str] = mapped_column(String(80))
    unit_price: Mapped[Decimal] = mapped_column(Numeric(14, 0))
    quantity: Mapped[int]
    line_total: Mapped[Decimal] = mapped_column(Numeric(14, 0))
    order: Mapped[Order] = relationship(lazy="raise", back_populates="items")


class PaymentAttempt(BaseModel):
    __tablename__ = "payment_attempts"
    __table_args__ = (
        UniqueConstraint("order_id"),
        UniqueConstraint("provider", "transaction_id"),
    )

    order_id: Mapped[UUID] = mapped_column(ForeignKey("orders.id"))
    provider: Mapped[PaymentMethod] = mapped_column(enum_column(PaymentMethod))
    request_id: Mapped[str] = mapped_column(String(50), unique=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 0))
    payment_url: Mapped[str | None] = mapped_column(String(4096))
    transaction_id: Mapped[str | None] = mapped_column(String(100))
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
