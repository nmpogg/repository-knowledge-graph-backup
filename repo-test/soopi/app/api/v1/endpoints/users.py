from uuid import UUID

from fastapi import APIRouter, Response

from app.api.deps import DB, CurrentIdentity
from app.schemas.user import AddressInput, AddressOut, UserOut, UserPatch
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserOut)
async def me(identity: CurrentIdentity):
    return identity.user


@router.patch("/me", response_model=UserOut)
async def update_me(data: UserPatch, db: DB, identity: CurrentIdentity):
    return await UserService(db).profile(identity.user, data)


@router.get("/me/addresses", response_model=list[AddressOut])
async def addresses(db: DB, identity: CurrentIdentity):
    return await UserService(db).list_addresses(identity.user.id)


@router.post("/me/addresses", response_model=AddressOut, status_code=201)
async def create_address(data: AddressInput, db: DB, identity: CurrentIdentity):
    return await UserService(db).create_address(identity.user.id, data)


@router.put("/me/addresses/{address_id}", response_model=AddressOut)
async def update_address(address_id: UUID, data: AddressInput, db: DB, identity: CurrentIdentity):
    return await UserService(db).update_address(identity.user.id, address_id, data)


@router.delete("/me/addresses/{address_id}", status_code=204)
async def delete_address(address_id: UUID, db: DB, identity: CurrentIdentity):
    await UserService(db).delete_address(identity.user.id, address_id)
    return Response(status_code=204)
