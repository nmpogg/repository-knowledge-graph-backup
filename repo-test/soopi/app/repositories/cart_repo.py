from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.cart import Cart
from app.models.user import User
from app.repositories.base import Repository


class CartRepository(Repository[Cart]):
    def __init__(self, session):
        super().__init__(session, Cart)

    async def lock_user(self, user_id: UUID):
        return await self.session.scalar(
            select(User)
            .where(User.id == user_id)
            .with_for_update()
            .execution_options(populate_existing=True),
        )

    async def owned(self, *, user_id=None, guest_hash=None, lock=True):
        owner = Cart.user_id == user_id if user_id else Cart.guest_token_hash == guest_hash
        query = select(Cart).where(owner).options(selectinload(Cart.items))
        if lock:
            query = query.with_for_update()
        return await self.session.scalar(query.execution_options(populate_existing=True))
