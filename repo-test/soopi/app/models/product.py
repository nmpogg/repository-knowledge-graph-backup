from decimal import Decimal
from uuid import UUID

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    CheckConstraint,
    ForeignKey,
    Numeric,
    String,
    Text,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class Category(BaseModel):
    __tablename__ = "categories"

    name: Mapped[str] = mapped_column(String(120))
    slug: Mapped[str] = mapped_column(String(160), unique=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=text("true"))


class Product(BaseModel):
    __tablename__ = "products"

    category_id: Mapped[UUID] = mapped_column(ForeignKey("categories.id"), index=True)
    name: Mapped[str] = mapped_column(String(200))
    slug: Mapped[str] = mapped_column(String(220), unique=True)
    description: Mapped[str] = mapped_column(Text, default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=text("true"))
    variants: Mapped[list["ProductVariant"]] = relationship(lazy="raise", back_populates="product")


class ProductVariant(BaseModel):
    __tablename__ = "product_variants"
    __table_args__ = (
        CheckConstraint("price >= 0", name="nonnegative_price"),
        CheckConstraint("stock >= 0", name="nonnegative_stock"),
    )

    product_id: Mapped[UUID] = mapped_column(ForeignKey("products.id"), index=True)
    sku: Mapped[str] = mapped_column(String(80), unique=True)
    name: Mapped[str] = mapped_column(String(120))
    price: Mapped[Decimal] = mapped_column(Numeric(14, 0))
    stock: Mapped[int] = mapped_column(BigInteger, default=0)
    attributes: Mapped[dict] = mapped_column(JSON, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=text("true"))
    product: Mapped[Product] = relationship(lazy="raise", back_populates="variants")
