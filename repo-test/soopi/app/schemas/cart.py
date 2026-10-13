from uuid import UUID

from app.schemas.common import Input, Quantity


class CartAdd(Input):
    variant_id: UUID
    quantity: Quantity


class CartUpdate(Input):
    quantity: Quantity


class CartLine(Input):
    variant_id: UUID
    product_name: str
    variant_name: str
    sku: str
    quantity: int
    unit_price: int
    line_total: int
    available_stock: int
    available: bool


class CartOut(Input):
    items: list[CartLine]
    subtotal: int


class GuestCart(Input):
    guest_token: str
