from uuid import UUID

from fastapi import APIRouter, Response

from app.api.deps import DB, GuestToken, OptionalIdentity
from app.schemas.cart import CartAdd, CartOut, CartUpdate, GuestCart
from app.services.cart_service import CartService

router = APIRouter(prefix="/cart", tags=["cart"])


@router.post("/guest", response_model=GuestCart, status_code=201)
async def create_guest(db: DB):
    return GuestCart(guest_token=await CartService(db).create_guest())


async def owned(service, identity, guest_token):
    return await service.owned(
        user_id=identity.user.id if identity else None,
        guest_token=guest_token,
    )


@router.get("", response_model=CartOut)
async def cart(db: DB, identity: OptionalIdentity, guest_token: GuestToken = None):
    service = CartService(db)
    return await service.view(await owned(service, identity, guest_token))


@router.post("/items", response_model=CartOut)
async def add_item(
    data: CartAdd, db: DB, identity: OptionalIdentity, guest_token: GuestToken = None
):
    service = CartService(db)
    return await service.add(
        await owned(service, identity, guest_token), data.variant_id, data.quantity
    )


@router.patch("/items/{variant_id}", response_model=CartOut)
async def update_item(
    variant_id: UUID,
    data: CartUpdate,
    db: DB,
    identity: OptionalIdentity,
    guest_token: GuestToken = None,
):
    service = CartService(db)
    return await service.set_quantity(
        await owned(service, identity, guest_token),
        variant_id,
        data.quantity,
    )


@router.delete("/items/{variant_id}", status_code=204)
async def remove_item(
    variant_id: UUID,
    db: DB,
    identity: OptionalIdentity,
    guest_token: GuestToken = None,
):
    service = CartService(db)
    await service.remove(await owned(service, identity, guest_token), variant_id)
    return Response(status_code=204)


@router.delete("", status_code=204)
async def clear_cart(db: DB, identity: OptionalIdentity, guest_token: GuestToken = None):
    service = CartService(db)
    await service.clear(await owned(service, identity, guest_token))
    return Response(status_code=204)
