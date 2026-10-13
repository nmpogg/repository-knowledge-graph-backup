from app.core.exceptions import missing
from app.repositories.user_repo import AddressRepository, UserRepository


class UserService:
    def __init__(self, session):
        self.session = session
        self.addresses = AddressRepository(session)
        self.users = UserRepository(session)

    async def profile(self, user, data):
        return await self.users.update(user, data.model_dump(exclude_unset=True))

    async def list_addresses(self, user_id):
        return await self.addresses.for_user(user_id)

    async def owned_address(self, user_id, address_id, *, lock=False):
        address = await self.addresses.owned(user_id, address_id, lock=lock)
        if not address:
            raise missing("Address")
        return address

    async def create_address(self, user_id, data):
        return await self.addresses.create({"user_id": user_id, **data.model_dump()})

    async def update_address(self, user_id, address_id, data):
        address = await self.owned_address(user_id, address_id, lock=True)
        return await self.addresses.update(address, data.model_dump())

    async def delete_address(self, user_id, address_id):
        await self.addresses.delete(await self.owned_address(user_id, address_id, lock=True))
