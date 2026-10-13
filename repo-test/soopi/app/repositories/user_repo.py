from sqlalchemy import select

from app.models.user import Address, RefreshSession, User
from app.repositories.base import Repository


class UserRepository(Repository[User]):
    def __init__(self, session):
        super().__init__(session, User)

    async def by_email(self, email):
        return await self.session.scalar(select(User).where(User.email == email.lower()))


class AddressRepository(Repository[Address]):
    def __init__(self, session):
        super().__init__(session, Address)

    async def for_user(self, user_id):
        return list(
            await self.session.scalars(
                select(Address)
                .where(Address.user_id == user_id)
                .order_by(Address.created_at, Address.id),
            )
        )

    async def owned(self, user_id, address_id, *, lock=False):
        query = select(Address).where(Address.id == address_id, Address.user_id == user_id)
        if lock:
            query = query.with_for_update().execution_options(populate_existing=True)
        return await self.session.scalar(query)


class RefreshSessionRepository(Repository[RefreshSession]):
    def __init__(self, session):
        super().__init__(session, RefreshSession)

    async def by_token_hash(self, digest):
        return await self.session.scalar(
            select(RefreshSession)
            .where(RefreshSession.token_hash == digest)
            .with_for_update()
            .execution_options(populate_existing=True),
        )
