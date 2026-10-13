from datetime import timedelta

from app.core.config import get_settings
from app.core.exceptions import AppError, conflict, missing
from app.core.security import aware, now, opaque_token, token_digest
from app.models.cart import Cart, CartItem
from app.repositories.cart_repo import CartRepository
from app.repositories.product_repo import ProductRepository
from app.schemas.cart import CartLine, CartOut


class CartService:
    def __init__(self, session):
        self.session = session
        self.carts = CartRepository(session)
        self.products = ProductRepository(session)

    async def create_guest(self):
        token = opaque_token()
        self.session.add(
            Cart(
                guest_token_hash=token_digest(token),
                expires_at=now() + timedelta(days=get_settings().guest_cart_days),
                items=[],
            )
        )
        await self.session.flush()
        return token

    async def owned(self, user_id=None, guest_token=None):
        if user_id:
            user = await self.carts.lock_user(user_id)
            if not user or not user.is_active:
                raise AppError(401, "inactive_user", "Account is unavailable")
            cart = await self.carts.owned(user_id=user_id)
            if not cart:
                cart = Cart(user_id=user_id, items=[])
                self.session.add(cart)
                await self.session.flush()
            return cart
        if not guest_token:
            raise AppError(401, "cart_auth_required", "Bearer token or X-Guest-Token required")
        cart = await self.carts.owned(guest_hash=token_digest(guest_token))
        if not cart or aware(cart.expires_at) <= now():
            raise AppError(401, "invalid_guest_token", "Invalid or expired guest cart token")
        return cart

    async def validate_quantities(self, quantities):
        variants = await self.products.variants(quantities, lock=True)
        context = await self.products.product_context(variants)
        for variant_id, quantity in quantities.items():
            variant = variants.get(variant_id)
            if not variant:
                raise missing("Variant")
            product, category = context[variant.product_id]
            if not (variant.is_active and product.is_active and category.is_active):
                raise conflict("An item is unavailable")
            if quantity > 999 or quantity > variant.stock:
                raise conflict("Requested quantity exceeds available stock or item limit")
        return variants, context

    async def view(self, cart):
        variants = await self.products.variants([item.variant_id for item in cart.items])
        context = await self.products.product_context(variants)
        items = []
        for item in sorted(cart.items, key=lambda i: str(i.variant_id)):
            variant = variants[item.variant_id]
            product, category = context[variant.product_id]
            items.append(
                CartLine(
                    variant_id=variant.id,
                    product_name=product.name,
                    variant_name=variant.name,
                    sku=variant.sku,
                    quantity=item.quantity,
                    unit_price=int(variant.price),
                    line_total=int(variant.price) * item.quantity,
                    available_stock=variant.stock,
                    available=bool(
                        variant.is_active
                        and product.is_active
                        and category.is_active
                        and variant.stock >= item.quantity
                    ),
                )
            )
        return CartOut(items=items, subtotal=sum(item.line_total for item in items))

    async def add(self, cart, variant_id, quantity):
        item = next((i for i in cart.items if i.variant_id == variant_id), None)
        if not item and len(cart.items) >= 100:
            raise conflict("Cart supports at most 100 distinct variants")
        desired = quantity + (item.quantity if item else 0)
        await self.validate_quantities({variant_id: desired})
        if item:
            item.quantity = desired
        else:
            cart.items.append(CartItem(variant_id=variant_id, quantity=desired))
        await self.session.flush()
        return await self.view(cart)

    async def set_quantity(self, cart, variant_id, quantity):
        item = next((i for i in cart.items if i.variant_id == variant_id), None)
        if not item:
            raise missing("Cart item")
        await self.validate_quantities({variant_id: quantity})
        item.quantity = quantity
        await self.session.flush()
        return await self.view(cart)

    async def remove(self, cart, variant_id):
        item = next((i for i in cart.items if i.variant_id == variant_id), None)
        if not item:
            raise missing("Cart item")
        cart.items.remove(item)
        await self.session.flush()

    async def clear(self, cart):
        cart.items.clear()
        await self.session.flush()

    async def merge(self, user_id, guest_token):
        # Lock user, user cart, guest cart, then sorted variants for every merge.
        target = await self.owned(user_id=user_id)
        guest = await self.owned(guest_token=guest_token)
        quantities = {item.variant_id: item.quantity for item in target.items}
        for item in guest.items:
            quantities[item.variant_id] = quantities.get(item.variant_id, 0) + item.quantity
        if len(quantities) > 100:
            raise conflict("Merged cart exceeds 100 distinct variants")
        await self.validate_quantities(quantities)
        existing = {item.variant_id: item for item in target.items}
        for variant_id, quantity in quantities.items():
            if variant_id in existing:
                existing[variant_id].quantity = quantity
            else:
                target.items.append(CartItem(variant_id=variant_id, quantity=quantity))
        await self.session.delete(guest)  # Consume guest capability on successful merge.
        await self.session.flush()
        return target
