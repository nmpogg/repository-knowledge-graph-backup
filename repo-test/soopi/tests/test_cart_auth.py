from datetime import timedelta

import pytest
from sqlalchemy import select

from app.core.exceptions import AppError
from app.core.security import decode_access, now, token_digest
from app.models import Cart, RefreshSession, User
from app.schemas.user import Login, Register
from app.services.auth_service import AuthService
from app.services.cart_service import CartService


async def test_guest_merge_is_atomic_and_consumes_token(db, seed):
    service = CartService(db)
    token = await service.create_guest()
    guest = await service.owned(guest_token=token)
    await service.add(guest, seed.variant.id, 3)
    assert guest.guest_token_hash == token_digest(token)
    assert token != guest.guest_token_hash
    target = await service.merge(seed.user.id, token)
    assert target.items[0].quantity == 5
    assert seed.variant.stock == 10
    assert await db.scalar(select(Cart).where(Cart.guest_token_hash == token_digest(token))) is None
    with pytest.raises(AppError):
        await service.owned(guest_token=token)


async def test_merge_excess_stock_keeps_both_carts(db, seed):
    service = CartService(db)
    token = await service.create_guest()
    guest = await service.owned(guest_token=token)
    await service.add(guest, seed.variant.id, 9)
    await db.commit()
    user_id, variant_id = seed.user.id, seed.variant.id
    with pytest.raises(AppError):
        await service.merge(user_id, token)
    await db.rollback()
    assert (await service.owned(user_id=user_id)).items[0].quantity == 2
    assert (await service.owned(guest_token=token)).items[0].quantity == 9
    assert (await service.view(await service.owned(user_id=user_id))).items[
        0
    ].variant_id == variant_id


async def test_expired_guest_rejected(db):
    service = CartService(db)
    token = await service.create_guest()
    guest = await service.owned(guest_token=token)
    guest.expires_at = now() - timedelta(seconds=1)
    await db.flush()
    with pytest.raises(AppError) as error:
        await service.owned(guest_token=token)
    assert error.value.status == 401


async def test_cart_increases_quantity_but_does_not_reserve(db, seed):
    service = CartService(db)
    cart = await service.owned(user_id=seed.user.id)
    result = await service.add(cart, seed.variant.id, 1)
    assert result.items[0].quantity == 3
    assert result.subtotal == 300000
    assert seed.variant.stock == 10
    with pytest.raises(AppError):
        await service.set_quantity(cart, seed.variant.id, 11)
    assert cart.items[0].quantity == 3


async def test_refresh_rotation_and_logout(db):
    service = AuthService(db)
    pair = await service.register(
        Register(
            email="New@example.com",
            password="strong-password-123",
            full_name="New User",
        )
    )
    user_id, session_id = decode_access(pair.access_token)
    old = await db.get(RefreshSession, session_id)
    assert old.token_hash == token_digest(pair.refresh_token)
    user = await db.get(User, user_id)
    assert user.password_hash.startswith("$argon2")
    assert not user.is_admin
    rotated = await service.refresh(pair.refresh_token)
    assert old.revoked_at is not None
    assert rotated.refresh_token != pair.refresh_token
    with pytest.raises(AppError):
        await service.refresh(pair.refresh_token)
    _, current_id = decode_access(rotated.access_token)
    await service.logout(current_id)
    with pytest.raises(AppError):
        await service.refresh(rotated.refresh_token)


async def test_login_wrong_password_and_inactive_user(db):
    service = AuthService(db)
    pair = await service.register(
        Register(
            email="new@example.com",
            password="strong-password-123",
            full_name="New",
        )
    )
    with pytest.raises(AppError):
        await service.login(Login(email="new@example.com", password="incorrect"))
    user_id, _ = decode_access(pair.access_token)
    user = await db.get(User, user_id)
    user.is_active = False
    await db.flush()
    with pytest.raises(AppError):
        await service.login(Login(email="new@example.com", password="strong-password-123"))


async def test_expired_refresh_rejected(db):
    service = AuthService(db)
    pair = await service.register(
        Register(
            email="new@example.com",
            password="strong-password-123",
            full_name="New",
        )
    )
    _, session_id = decode_access(pair.access_token)
    row = await db.get(RefreshSession, session_id)
    row.expires_at = now() - timedelta(seconds=1)
    await db.flush()
    with pytest.raises(AppError):
        await service.refresh(pair.refresh_token)
