from datetime import datetime
from uuid import UUID

from pydantic import Field

from app.models.order import OrderStatus, PaymentMethod, PaymentStatus
from app.schemas.common import Input, Output


class Checkout(Input):
    address_id: UUID
    payment_method: PaymentMethod
    note: str = Field(default="", max_length=500)


class OrderItemOut(Output):
    variant_id: UUID
    product_name: str
    variant_name: str
    sku: str
    unit_price: int
    quantity: int
    line_total: int


class OrderOut(Output):
    status: OrderStatus
    payment_method: PaymentMethod
    payment_status: PaymentStatus
    subtotal: int
    shipping_fee: int
    total: int
    shipping_address: dict[str, str]
    note: str
    expires_at: datetime | None
    created_at: datetime
    items: list[OrderItemOut]


class OrderTransition(Input):
    status: OrderStatus


class PaymentLink(Input):
    payment_url: str | None
    payment_method: PaymentMethod


class MomoNotification(Input):
    # Provider may add fields; known signed fields must have strict types.
    model_config = {"extra": "ignore", "str_strip_whitespace": False}
    partnerCode: str
    orderId: str
    requestId: str
    amount: int = Field(strict=True, ge=0)
    orderInfo: str
    orderType: str
    transId: int = Field(strict=True, ge=0)
    resultCode: int = Field(strict=True)
    message: str
    payType: str
    responseTime: int = Field(strict=True)
    extraData: str
    signature: str = Field(pattern=r"^[A-Fa-f0-9]{64}$")
