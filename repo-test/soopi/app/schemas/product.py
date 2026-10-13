from typing import Annotated
from uuid import UUID

from pydantic import Field

from app.schemas.common import Input, Money, Name, NonNullPatch, Output

Slug = Annotated[str, Field(min_length=1, max_length=160, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")]


class CategoryInput(Input):
    name: Name
    slug: Slug


class CategoryOut(Output):
    name: str
    slug: str
    is_active: bool


class VariantInput(Input):
    sku: str = Field(min_length=1, max_length=80, pattern=r"^[A-Za-z0-9_-]+$")
    name: Name
    price: Money
    stock: int = Field(strict=True, ge=0, le=2147483647)
    attributes: dict[str, str] = Field(default_factory=dict, max_length=30)


class VariantPatch(NonNullPatch):
    name: Name | None = None
    price: Money | None = None
    stock: Annotated[int, Field(strict=True, ge=0, le=2147483647)] | None = None
    attributes: dict[str, str] | None = None
    is_active: bool | None = None


class VariantOut(Output):
    sku: str
    name: str
    price: int
    stock: int
    attributes: dict[str, str]
    is_active: bool


class ProductInput(Input):
    category_id: UUID
    name: str = Field(min_length=1, max_length=200)
    slug: Slug
    description: str = Field(default="", max_length=20000)
    variants: list[VariantInput] = Field(min_length=1, max_length=100)


class ProductPatch(NonNullPatch):
    category_id: UUID | None = None
    name: Annotated[str, Field(min_length=1, max_length=200)] | None = None
    description: Annotated[str, Field(max_length=20000)] | None = None
    is_active: bool | None = None


class ProductOut(Output):
    category_id: UUID
    name: str
    slug: str
    description: str
    is_active: bool
    variants: list[VariantOut]
