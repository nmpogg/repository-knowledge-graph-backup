from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query

from app.api.deps import DB, AdminIdentity
from app.core.exceptions import AppError, missing
from app.repositories.product_repo import ProductRepository
from app.schemas.common import Page
from app.schemas.product import (
    ProductInput,
    ProductOut,
    ProductPatch,
    VariantInput,
    VariantOut,
    VariantPatch,
)
from app.services.product_service import ProductService

router = APIRouter(prefix="/products", tags=["products"])


@router.get("", response_model=Page[ProductOut])
async def products(
    db: DB,
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=100)] = 20,
    q: Annotated[str | None, Query(min_length=1, max_length=200)] = None,
    category_id: UUID | None = None,
    min_price: Annotated[int | None, Query(ge=0)] = None,
    max_price: Annotated[int | None, Query(ge=0)] = None,
):
    if min_price is not None and max_price is not None and min_price > max_price:
        raise AppError(422, "invalid_price_range", "min_price must not exceed max_price")
    rows, total = await ProductRepository(db).search(
        page=page,
        size=size,
        q=q,
        category_id=category_id,
        min_price=min_price,
        max_price=max_price,
    )
    return Page(
        items=[ProductService.public(row) for row in rows], total=total, page=page, size=size
    )


@router.get("/{product_id}", response_model=ProductOut)
async def product(product_id: UUID, db: DB):
    entity = await ProductRepository(db).detail(product_id)
    if not entity:
        raise missing("Product")
    return ProductService.public(entity)


@router.post("", response_model=ProductOut, status_code=201)
async def create_product(data: ProductInput, db: DB, admin: AdminIdentity):
    return await ProductService(db).create(data)


@router.patch("/{product_id}", response_model=ProductOut)
async def update_product(product_id: UUID, data: ProductPatch, db: DB, admin: AdminIdentity):
    return await ProductService(db).update(product_id, data)


@router.post("/{product_id}/variants", response_model=VariantOut, status_code=201)
async def create_variant(product_id: UUID, data: VariantInput, db: DB, admin: AdminIdentity):
    return await ProductService(db).add_variant(product_id, data)


@router.patch("/{product_id}/variants/{variant_id}", response_model=VariantOut)
async def update_variant(
    product_id: UUID,
    variant_id: UUID,
    data: VariantPatch,
    db: DB,
    admin: AdminIdentity,
):
    return await ProductService(db).update_variant(product_id, variant_id, data)
