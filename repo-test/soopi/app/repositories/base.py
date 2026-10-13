from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import BaseModel


class Repository[Model: BaseModel]:
    def __init__(self, session: AsyncSession, model: type[Model]):
        self.session, self.model = session, model

    async def get(self, resource_id: UUID, *, lock: bool = False) -> Model | None:
        query = select(self.model).where(self.model.id == resource_id)
        if lock:
            query = query.with_for_update().execution_options(populate_existing=True)
        return await self.session.scalar(query)

    async def get_multi(self, *, page: int = 1, size: int = 20, filters=()):
        query = select(self.model).where(*filters)
        total = await self.session.scalar(select(func.count()).select_from(query.subquery()))
        rows = await self.session.scalars(
            query.order_by(self.model.created_at.desc(), self.model.id)
            .offset((page - 1) * size)
            .limit(size),
        )
        return list(rows), total

    async def create(self, data: dict) -> Model:
        entity = self.model(**data)
        self.session.add(entity)
        await self.session.flush()
        return entity

    async def update(self, entity: Model, data: dict) -> Model:
        # Callers supply an allowlisted schema, never arbitrary request JSON.
        for key, value in data.items():
            setattr(entity, key, value)
        await self.session.flush()
        return entity

    async def delete(self, entity: Model) -> None:
        await self.session.delete(entity)
        await self.session.flush()
