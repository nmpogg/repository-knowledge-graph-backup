import hashlib
import hmac
from datetime import timedelta
from urllib.parse import parse_qs, urlsplit
from uuid import uuid4

import pytest
from sqlalchemy import func, select

from app.core.exceptions import AppError
from app.core.security import now
from app.models import PaymentAttempt
from app.models.order import OrderStatus, PaymentMethod, PaymentStatus
from app.schemas.order import Checkout, MomoNotification
from app.services.order_service import OrderService
from app.services.payment_service import PaymentService, momo_signature, vnpay_signature


async def online_order(db, seed, method=PaymentMethod.vnpay):
    return await OrderService(db).checkout(
        seed.user.id,
        Checkout(address_id=seed.address.id, payment_method=method),
        "checkout-001",
    )


async def attempt_for(db, order):
    attempt = PaymentAttempt(
        order_id=order.id,
        provider=order.payment_method,
        amount=order.total,
        request_id=str(uuid4()),
    )
    db.add(attempt)
    await db.flush()
    return attempt


async def test_vnpay_url_amount_signature_and_repeated_initiation(db, seed):
    order = await online_order(db, seed)
    service = PaymentService(db)
    first = await service.initiate(seed.user.id, order.id, "127.0.0.1")
    second = await service.initiate(seed.user.id, order.id, "127.0.0.1")
    assert first.payment_url == second.payment_url
    fields = {key: value[0] for key, value in parse_qs(urlsplit(first.payment_url).query).items()}
    actual = fields.pop("vnp_SecureHash")
    assert fields["vnp_Amount"] == "23000000"
    assert actual == vnpay_signature(fields, "test-vnpay-secret")
    assert await db.scalar(select(func.count()).select_from(PaymentAttempt)) == 1


async def test_callback_success_replay_and_late_failure(db, seed):
    order = await online_order(db, seed)
    attempt = await attempt_for(db, order)
    service = PaymentService(db)
    assert await service.apply_result("vnpay", str(attempt.id), 230000, "12345", True)
    assert order.status == OrderStatus.confirmed
    assert order.payment_status == PaymentStatus.paid
    assert seed.variant.stock == 8
    assert not await service.apply_result("vnpay", str(attempt.id), 230000, "12345", True)
    assert not await service.apply_result("vnpay", str(attempt.id), 230000, "0", False)
    assert order.payment_status == PaymentStatus.paid
    with pytest.raises(AppError):
        await service.apply_result("vnpay", str(attempt.id), 230000, "99999", True)


@pytest.mark.parametrize("closed", ["cancelled", "expired"])
async def test_late_success_requires_refund_and_does_not_retake_stock(db, seed, closed):
    order = await online_order(db, seed)
    attempt = await attempt_for(db, order)
    if closed == "cancelled":
        await OrderService(db).cancel(seed.user.id, order.id)
    else:
        order.expires_at = now() - timedelta(seconds=1)
        await db.flush()
    await PaymentService(db).apply_result("vnpay", str(attempt.id), 230000, "12345", True)
    assert order.status.value == closed
    assert order.payment_status == PaymentStatus.refund_required
    assert seed.variant.stock == 10
    await PaymentService(db).apply_result("vnpay", str(attempt.id), 230000, "12345", True)
    assert seed.variant.stock == 10


async def test_wrong_amount_provider_and_request_rejected(db, seed):
    order = await online_order(db, seed, PaymentMethod.momo)
    attempt = await attempt_for(db, order)
    service = PaymentService(db)
    with pytest.raises(AppError):
        await service.apply_result("momo", str(attempt.id), 1, "12345", True, attempt.request_id)
    with pytest.raises(AppError):
        await service.apply_result("vnpay", str(attempt.id), 230000, "12345", True)
    with pytest.raises(AppError):
        await service.apply_result("momo", str(attempt.id), 230000, "12345", True, "wrong")
    assert order.payment_status == PaymentStatus.unpaid
    assert seed.variant.stock == 8


def test_momo_signature_external_vector_and_tamper(settings):
    # Signature expected is independently computed over an explicit canonical string.
    fields = {
        "partnerCode": "TEST",
        "orderId": "intent",
        "requestId": "request",
        "amount": 230000,
        "orderInfo": "Payment",
        "orderType": "momo_wallet",
        "transId": 12345,
        "resultCode": 0,
        "message": "Successful.",
        "payType": "qr",
        "responseTime": 1700000000000,
        "extraData": "",
    }
    canonical = (
        "accessKey=test-access&amount=230000&extraData=&message=Successful.&orderId=intent"
        "&orderInfo=Payment&orderType=momo_wallet&partnerCode=TEST&payType=qr&requestId=request"
        "&responseTime=1700000000000&resultCode=0&transId=12345"
    )
    signature = hmac.new(b"test-momo-secret", canonical.encode(), hashlib.sha256).hexdigest()
    notification = MomoNotification(**fields, signature=signature)
    PaymentService(None).verify_momo(notification)
    notification.amount = 1
    with pytest.raises(AppError):
        PaymentService(None).verify_momo(notification)


def test_vnpay_signature_external_encoding_vector_and_tamper(settings):
    fields = {"vnp_Amount": "23000000", "vnp_OrderInfo": "Thanh toan / +", "vnp_TmnCode": "TEST"}
    canonical = "vnp_Amount=23000000&vnp_OrderInfo=Thanh+toan+%2F+%2B&vnp_TmnCode=TEST"
    signature = hmac.new(b"test-vnpay-secret", canonical.encode(), hashlib.sha512).hexdigest()
    assert signature == vnpay_signature(fields, "test-vnpay-secret")
    fields["vnp_SecureHash"] = signature
    PaymentService(None).verify_vnpay(fields)
    fields["vnp_Amount"] = "100"
    with pytest.raises(AppError):
        PaymentService(None).verify_vnpay(fields)


async def test_momo_timeout_keeps_durable_intent_for_retry(db, seed, monkeypatch):
    order = await online_order(db, seed, PaymentMethod.momo)
    seen = []

    async def timeout(self, attempt):
        seen.append((attempt.id, attempt.request_id))
        raise AppError(502, "payment_gateway_unavailable", "Uncertain")

    monkeypatch.setattr(PaymentService, "create_momo_url", timeout)
    for _ in range(2):
        with pytest.raises(AppError):
            await PaymentService(db).initiate(seed.user.id, order.id, "127.0.0.1")
        await db.rollback()
    assert len(seen) == 2
    assert seen[0] == seen[1]
    assert await db.scalar(select(func.count()).select_from(PaymentAttempt)) == 1


async def test_momo_create_payload_uses_expected_signature(db, seed, monkeypatch):
    import httpx

    order = await online_order(db, seed, PaymentMethod.momo)
    attempt = await attempt_for(db, order)

    async def fake_post(self, url, *, json):
        fields = {k: v for k, v in json.items() if k not in ("signature", "lang", "autoCapture")}
        assert json["requestType"] == "captureWallet"
        assert json["signature"] == momo_signature(
            {"accessKey": "test-access", **fields},
            "test-momo-secret",
        )
        return httpx.Response(
            200,
            request=httpx.Request("POST", url),
            json={
                "partnerCode": "TEST",
                "orderId": str(attempt.id),
                "requestId": attempt.request_id,
                "amount": 230000,
                "resultCode": 0,
                "payUrl": "https://test-payment.momo.vn/v2/gateway/pay?t=test",
            },
        )

    monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)
    assert (await PaymentService(db).create_momo_url(attempt)).startswith(
        "https://test-payment.momo.vn/"
    )
