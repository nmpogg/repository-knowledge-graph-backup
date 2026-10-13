import hashlib
import json
from datetime import timedelta
from decimal import Decimal

from app.core.config import get_settings
from app.core.exceptions import AppError, conflict, missing
from app.core.security import aware, now
from app.models.order import Order, OrderItem, OrderStatus, PaymentMethod, PaymentStatus
from app.repositories.order_repo import OrderRepository
from app.repositories.product_repo import ProductRepository
from app.services.cart_service import CartService
from app.services.user_service import UserService


class OrderService:
    def __init__(self, session):
        self.session = session
        self.orders = OrderRepository(session)

    async def checkout(self, user_id, data, key):
        cart_service = CartService(self.session)
        cart = await cart_service.owned(user_id=user_id)
        fingerprint = hashlib.sha256(
            json.dumps(
                data.model_dump(mode="json"), sort_keys=True, separators=(",", ":")
            ).encode(),
        ).hexdigest()
        previous = await self.orders.by_key(user_id, key)
        if previous:
            if previous.request_hash != fingerprint:
                raise conflict("Idempotency key was already used with a different payload")
            return previous
        if not cart.items:
            raise conflict("Cannot checkout an empty cart")
        address = await UserService(self.session).owned_address(user_id, data.address_id, lock=True)
        quantities = {item.variant_id: item.quantity for item in cart.items}
        variants, context = await cart_service.validate_quantities(quantities)
        subtotal = sum((variants[vid].price * qty for vid, qty in quantities.items()), Decimal(0))
        fee = Decimal(get_settings().shipping_fee)
        if subtotal + fee > Decimal("99999999999999"):
            raise conflict("Order total exceeds the supported amount")
        if data.payment_method == PaymentMethod.momo and not 10000 <= subtotal + fee <= 50000000:
            raise conflict("MoMo supports order totals from 10000 to 50000000 VND")
        expires = (
            None
            if data.payment_method == PaymentMethod.cod
            else (now() + timedelta(minutes=get_settings().order_hold_minutes))
        )
        order = Order(
            user_id=user_id,
            idempotency_key=key,
            request_hash=fingerprint,
            payment_method=data.payment_method,
            subtotal=subtotal,
            shipping_fee=fee,
            total=subtotal + fee,
            expires_at=expires,
            note=data.note,
            shipping_address={
                field: getattr(address, field)
                for field in ("recipient", "phone", "line1", "ward", "district", "province")
            },
            items=[],
        )
        self.session.add(order)
        for variant_id, quantity in quantities.items():
            variant = variants[variant_id]
            product, _ = context[variant.product_id]
            variant.stock -= quantity
            order.items.append(
                OrderItem(
                    variant_id=variant.id,
                    product_name=product.name,
                    variant_name=variant.name,
                    sku=variant.sku,
                    unit_price=variant.price,
                    quantity=quantity,
                    line_total=variant.price * quantity,
                )
            )
        await cart_service.clear(cart)
        await self.session.flush()
        return order

    async def release_stock(self, order):
        if order.stock_released_at:
            return
        variants = await ProductRepository(self.session).variants(
            [item.variant_id for item in order.items],
            lock=True,
        )
        for item in order.items:
            variants[item.variant_id].stock += item.quantity
        order.stock_released_at = now()

    async def cancel(self, user_id, order_id):
        order = await self.orders.detail(order_id, user_id=user_id, lock=True)
        if not order:
            raise missing("Order")
        if order.status in (OrderStatus.cancelled, OrderStatus.expired):
            return order
        if order.status != OrderStatus.pending:
            raise conflict("Only pending orders can be cancelled")
        await self.release_stock(order)
        order.status = OrderStatus.cancelled
        if order.payment_status == PaymentStatus.paid:
            order.payment_status = PaymentStatus.refund_required
        await self.session.flush()
        return order

    async def expire(self, order):
        # Caller must hold the order row lock, including CLI and callback callers.
        if (
            order.status == OrderStatus.pending
            and order.expires_at
            and aware(order.expires_at) <= now()
        ):
            await self.release_stock(order)
            order.status = OrderStatus.expired
            await self.session.flush()
            return True
        return False

    async def transition(self, order_id, target):
        order = await self.orders.detail(order_id, lock=True)
        if not order:
            raise missing("Order")
        await self.expire(order)
        if order.status == target:
            return order
        allowed = {
            OrderStatus.pending: OrderStatus.confirmed,
            OrderStatus.confirmed: OrderStatus.shipped,
            OrderStatus.shipped: OrderStatus.delivered,
        }
        if allowed.get(order.status) != target:
            raise conflict("Invalid order status transition")
        if order.payment_method != PaymentMethod.cod and order.payment_status != PaymentStatus.paid:
            raise AppError(409, "payment_required", "Online orders must be paid before fulfillment")
        order.status = target
        if target == OrderStatus.delivered and order.payment_method == PaymentMethod.cod:
            order.payment_status = PaymentStatus.paid
        await self.session.flush()
        return order
