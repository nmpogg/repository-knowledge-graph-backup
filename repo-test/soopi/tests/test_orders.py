from datetime import timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import func, select

from app.core.exceptions import AppError
from app.core.security import aware, now
from app.models import Cart, Order, ProductVariant
from app.models.order import OrderStatus, PaymentMethod, PaymentStatus
from app.repositories.cart_repo import CartRepository
from app.repositories.order_repo import OrderRepository
from app.schemas.order import Checkout, OrderOut
from app.services.order_service import OrderService


def payload(seed, method=PaymentMethod.cod, **overrides):
    return Checkout(address_id=seed.address.id, payment_method=method, **overrides)


async def test_checkout_snapshots_and_idempotency(db, seed):
    service = OrderService(db)
    data = payload(seed)
    order = await service.checkout(seed.user.id, data, "checkout-001")
    assert order.total == 230000
    assert order.subtotal == 200000
    assert seed.variant.stock == 8
    assert order.items[0].unit_price == 100000
    assert order.shipping_address["line1"] == "12 Example street"
    assert order.expires_at is None
    assert seed.cart.items == []
    duplicate = await service.checkout(seed.user.id, data, "checkout-001")
    assert duplicate.id == order.id
    assert seed.variant.stock == 8
    assert await db.scalar(select(func.count()).select_from(Order)) == 1
    seed.variant.price = Decimal(999999)
    seed.address.line1 = "Changed address"
    await db.flush()
    snapshot = OrderOut.model_validate(await service.orders.detail(order.id))
    assert snapshot.items[0].unit_price == 100000
    assert snapshot.shipping_address["line1"] == "12 Example street"


async def test_idempotency_rejects_different_payload(db, seed):
    service = OrderService(db)
    await service.checkout(seed.user.id, payload(seed), "checkout-001")
    with pytest.raises(AppError, match="different payload"):
        await service.checkout(seed.user.id, payload(seed, note="changed"), "checkout-001")


async def test_stock_failure_rolls_back_entire_checkout(db, seed):
    user_id, variant_id = seed.user.id, seed.variant.id
    data = payload(seed)
    seed.variant.stock = 1
    await db.commit()
    with pytest.raises(AppError, match="stock"):
        await OrderService(db).checkout(user_id, data, "checkout-001")
    await db.rollback()
    variant = await db.get(ProductVariant, variant_id)
    cart = await CartRepository(db).owned(user_id=user_id)
    assert variant.stock == 1
    assert cart.items[0].quantity == 2
    assert await db.scalar(select(func.count()).select_from(Order)) == 0


async def test_failure_after_stock_reservation_rolls_back(db, seed, monkeypatch):
    from app.services.cart_service import CartService

    user_id, variant_id = seed.user.id, seed.variant.id
    data = payload(seed)

    async def failing_clear(self, cart):
        cart.items.clear()
        await self.session.flush()
        raise RuntimeError("simulated persistence failure")

    monkeypatch.setattr(CartService, "clear", failing_clear)
    with pytest.raises(RuntimeError):
        await OrderService(db).checkout(user_id, data, "checkout-001")
    await db.rollback()
    assert (await db.get(ProductVariant, variant_id)).stock == 10
    assert len((await CartRepository(db).owned(user_id=user_id)).items) == 1
    assert await db.scalar(select(func.count()).select_from(Order)) == 0


@pytest.mark.parametrize("target", ["variant", "product", "category"])
async def test_inactive_catalog_cannot_checkout(db, seed, target):
    getattr(seed, target).is_active = False
    await db.flush()
    with pytest.raises(AppError, match="unavailable"):
        await OrderService(db).checkout(seed.user.id, payload(seed), "checkout-001")


async def test_address_and_order_ownership(db, seed):
    with pytest.raises(AppError) as error:
        await OrderService(db).checkout(seed.other.id, payload(seed), "checkout-001")
    assert error.value.status == 409  # Other user has an empty cart.
    order = await OrderService(db).checkout(seed.user.id, payload(seed), "checkout-001")
    with pytest.raises(AppError) as error:
        await OrderService(db).cancel(seed.other.id, order.id)
    assert error.value.status == 404
    assert await OrderRepository(db).detail(order.id, user_id=seed.other.id) is None


async def test_foreign_address_with_nonempty_cart_rejected(db, seed):
    from app.models import CartItem

    db.add(Cart(user_id=seed.other.id, items=[CartItem(variant_id=seed.variant.id, quantity=1)]))
    await db.flush()
    with pytest.raises(AppError) as error:
        await OrderService(db).checkout(seed.other.id, payload(seed), "checkout-001")
    assert error.value.status == 404


async def test_cancel_releases_stock_once(db, seed):
    service = OrderService(db)
    order = await service.checkout(seed.user.id, payload(seed), "checkout-001")
    assert seed.variant.stock == 8
    await service.cancel(seed.user.id, order.id)
    assert seed.variant.stock == 10
    assert order.status == OrderStatus.cancelled
    released = order.stock_released_at
    await service.cancel(seed.user.id, order.id)
    assert seed.variant.stock == 10
    assert aware(order.stock_released_at) == aware(released)


async def test_cod_fulfillment_requires_sequential_transitions(db, seed):
    service = OrderService(db)
    order = await service.checkout(seed.user.id, payload(seed), "checkout-001")
    with pytest.raises(AppError):
        await service.transition(order.id, OrderStatus.delivered)
    await service.transition(order.id, OrderStatus.confirmed)
    with pytest.raises(AppError):
        await service.cancel(seed.user.id, order.id)
    await service.transition(order.id, OrderStatus.shipped)
    await service.transition(order.id, OrderStatus.delivered)
    assert order.payment_status == PaymentStatus.paid
    assert seed.variant.stock == 8


async def test_online_expiry_restores_stock_once(db, seed):
    service = OrderService(db)
    order = await service.checkout(seed.user.id, payload(seed, PaymentMethod.vnpay), "checkout-001")
    order.expires_at = now() - timedelta(seconds=1)
    await db.flush()
    assert await service.expire(order)
    assert order.status == OrderStatus.expired
    assert seed.variant.stock == 10
    assert not await service.expire(order)


async def test_unpaid_online_order_cannot_confirm(db, seed):
    order = await OrderService(db).checkout(
        seed.user.id,
        payload(seed, PaymentMethod.vnpay),
        "checkout-001",
    )
    with pytest.raises(AppError) as error:
        await OrderService(db).transition(order.id, OrderStatus.confirmed)
    assert error.value.code == "payment_required"


async def test_unknown_address_rejected(db, seed):
    with pytest.raises(AppError) as error:
        await OrderService(db).checkout(
            seed.user.id,
            Checkout(address_id=uuid4(), payment_method="cod"),
            "checkout-001",
        )
    assert error.value.status == 404


async def test_expiry_worker_persists_release_and_is_repeatable(db, seed, factory, monkeypatch):
    from app import expire_orders

    order = await OrderService(db).checkout(
        seed.user.id,
        payload(seed, PaymentMethod.vnpay),
        "checkout-001",
    )
    order.expires_at = now() - timedelta(seconds=1)
    await db.commit()
    monkeypatch.setattr(expire_orders, "get_session_factory", lambda: factory)
    assert await expire_orders.expire_pending() == 1
    assert await expire_orders.expire_pending() == 0
    await db.refresh(order)
    await db.refresh(seed.variant)
    assert order.status == OrderStatus.expired
    assert seed.variant.stock == 10
