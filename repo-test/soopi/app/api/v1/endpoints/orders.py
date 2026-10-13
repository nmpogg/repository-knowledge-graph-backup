from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Header, Query, Request, Response

from app.api.deps import DB, AdminIdentity, CurrentIdentity
from app.core.exceptions import AppError, missing
from app.models.order import PaymentMethod
from app.repositories.order_repo import OrderRepository
from app.schemas.common import Page
from app.schemas.order import Checkout, MomoNotification, OrderOut, OrderTransition, PaymentLink
from app.services.order_service import OrderService
from app.services.payment_service import PaymentService

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("/webhooks/momo", status_code=204)
async def momo_webhook(data: MomoNotification, db: DB):
    service = PaymentService(db)
    service.verify_momo(data)
    await service.apply_result(
        PaymentMethod.momo,
        data.orderId,
        data.amount,
        str(data.transId),
        success=data.resultCode == 0,
        request_id=data.requestId,
    )
    return Response(status_code=204)


@router.get("/webhooks/vnpay")
async def vnpay_webhook(request: Request, db: DB):
    pairs = request.query_params.multi_items()
    if len(pairs) != len(dict(pairs)):
        return {"RspCode": "97", "Message": "Invalid parameters"}
    fields = dict(pairs)
    service = PaymentService(db)
    try:
        service.verify_vnpay(fields)
        raw_amount = fields.get("vnp_Amount", "")
        if not raw_amount.isascii() or not raw_amount.isdigit() or int(raw_amount) % 100:
            raise AppError(400, "payment_mismatch", "Invalid amount")
        updated = await service.apply_result(
            PaymentMethod.vnpay,
            fields.get("vnp_TxnRef", ""),
            int(raw_amount) // 100,
            fields.get("vnp_TransactionNo", ""),
            success=fields.get("vnp_ResponseCode") == "00"
            and fields.get("vnp_TransactionStatus") == "00",
        )
    except AppError as exc:
        await db.rollback()
        codes = {"invalid_signature": "97", "not_found": "01", "payment_mismatch": "04"}
        return {"RspCode": codes.get(exc.code, "99"), "Message": "Confirmation rejected"}
    return {"RspCode": "00" if updated else "02", "Message": "Confirmed" if updated else "Settled"}


@router.post("", response_model=OrderOut, status_code=201)
async def checkout(
    data: Checkout,
    db: DB,
    identity: CurrentIdentity,
    key: Annotated[str, Header(alias="Idempotency-Key", min_length=8, max_length=100)],
):
    return await OrderService(db).checkout(identity.user.id, data, key)


@router.get("", response_model=Page[OrderOut])
async def orders(
    db: DB,
    identity: CurrentIdentity,
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=100)] = 20,
):
    rows, total = await OrderRepository(db).listing(identity.user.id, page, size)
    return Page(items=[OrderOut.model_validate(r) for r in rows], total=total, page=page, size=size)


@router.get("/{order_id}", response_model=OrderOut)
async def order(order_id: UUID, db: DB, identity: CurrentIdentity):
    entity = await OrderRepository(db).detail(order_id, user_id=identity.user.id)
    if not entity:
        raise missing("Order")
    return entity


@router.post("/{order_id}/cancel", response_model=OrderOut)
async def cancel_order(order_id: UUID, db: DB, identity: CurrentIdentity):
    return await OrderService(db).cancel(identity.user.id, order_id)


@router.post("/{order_id}/payment", response_model=PaymentLink)
async def initiate_payment(order_id: UUID, request: Request, db: DB, identity: CurrentIdentity):
    # Proxy headers are only trusted when the ASGI server is explicitly configured.
    ip = request.client.host if request.client else "127.0.0.1"
    return await PaymentService(db).initiate(identity.user.id, order_id, ip)


@router.patch("/{order_id}/status", response_model=OrderOut)
async def transition_order(order_id: UUID, data: OrderTransition, db: DB, admin: AdminIdentity):
    return await OrderService(db).transition(order_id, data.status)
