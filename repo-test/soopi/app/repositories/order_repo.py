from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.models.order import Order
from app.repositories.base import Repository


class OrderRepository(Repository[Order]):
    def __init__(self, session):
        super().__init__(session, Order)

    async def detail(self, order_id: UUID, *, user_id=None, lock=False):
        query = select(Order).where(Order.id == order_id).options(selectinload(Order.items))
        if user_id:
            query = query.where(Order.user_id == user_id)
        if lock:
            query = query.with_for_update()
        return await self.session.scalar(query.execution_options(populate_existing=True))

    async def by_key(self, user_id, key):
        return await self.session.scalar(
            select(Order)
            .where(Order.user_id == user_id, Order.idempotency_key == key)
            .options(selectinload(Order.items)),
        )

    async def listing(self, user_id, page, size):
        total = await self.session.scalar(
            select(func.count()).select_from(Order).where(Order.user_id == user_id),
        )
        rows = await self.session.scalars(
            select(Order)
            .where(Order.user_id == user_id)
            .options(selectinload(Order.items))
            .order_by(Order.created_at.desc(), Order.id)
            .offset((page - 1) * size)
            .limit(size),
        )
        return list(rows), total
