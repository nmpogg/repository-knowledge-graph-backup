from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query

from app.api.deps import DB, AdminIdentity
from app.core.exceptions import missing
from app.models.product import Category
from app.repositories.base import Repository
from app.schemas.common import Page
from app.schemas.product import CategoryInput, CategoryOut

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("", response_model=Page[CategoryOut])
async def categories(
    db: DB,
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=100)] = 20,
):
    rows, total = await Repository(db, Category).get_multi(
        page=page,
        size=size,
        filters=(Category.is_active,),
    )
    return Page(
        items=[CategoryOut.model_validate(r) for r in rows], total=total, page=page, size=size
    )


@router.post("", response_model=CategoryOut, status_code=201)
async def create_category(data: CategoryInput, db: DB, admin: AdminIdentity):
    return await Repository(db, Category).create(data.model_dump())


@router.put("/{category_id}", response_model=CategoryOut)
async def update_category(category_id: UUID, data: CategoryInput, db: DB, admin: AdminIdentity):
    repository = Repository(db, Category)
    category = await repository.get(category_id, lock=True)
    if not category:
        raise missing("Category")
    return await repository.update(category, data.model_dump())


@router.delete("/{category_id}", response_model=CategoryOut)
async def deactivate_category(category_id: UUID, db: DB, admin: AdminIdentity):
    repository = Repository(db, Category)
    category = await repository.get(category_id, lock=True)
    if not category:
        raise missing("Category")
    return await repository.update(category, {"is_active": False})
