import hashlib
import hmac
from urllib.parse import urlencode, urlsplit
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo

import httpx

from app.core.config import get_settings
from app.core.exceptions import AppError, conflict, missing
from app.core.security import aware, now
from app.models.order import OrderStatus, PaymentAttempt, PaymentMethod, PaymentStatus
from app.repositories.order_repo import OrderRepository
from app.repositories.payment_repo import PaymentRepository
from app.schemas.order import PaymentLink
from app.services.order_service import OrderService


def momo_signature(fields: dict, secret: str) -> str:
    raw = "&".join(f"{key}={value}" for key, value in sorted(fields.items()))
    return hmac.new(secret.encode(), raw.encode(), hashlib.sha256).hexdigest()


def vnpay_signature(fields: dict, secret: str) -> str:
    encoded = urlencode(sorted((key, str(value)) for key, value in fields.items() if value != ""))
    return hmac.new(secret.encode(), encoded.encode(), hashlib.sha512).hexdigest()


class PaymentService:
    def __init__(self, session):
        self.session = session
        self.settings = get_settings()
        self.orders = OrderRepository(session)
        self.payments = PaymentRepository(session)

    def ensure_config(self, method):
        if method == PaymentMethod.cod:
            return
        s = self.settings
        valid = (
            (
                s.momo_partner_code
                and s.momo_access_key.get_secret_value()
                and s.momo_secret_key.get_secret_value()
                and s.momo_redirect_url
                and s.momo_ipn_url
            )
            if method == PaymentMethod.momo
            else (
                s.vnpay_tmn_code and s.vnpay_hash_secret.get_secret_value() and s.vnpay_return_url
            )
        )
        if not valid:
            raise AppError(503, "payment_unconfigured", "Payment provider is not configured")

    async def initiate(self, user_id, order_id, ip_address):
        order = await self.orders.detail(order_id, user_id=user_id, lock=True)
        if not order:
            raise missing("Order")
        if await OrderService(self.session).expire(order):
            await self.session.commit()  # Persist release before reporting expiry.
            raise conflict("Order has expired")
        if order.status != OrderStatus.pending:
            raise conflict("Only pending orders can initiate payment")
        self.ensure_config(order.payment_method)
        if order.payment_method == PaymentMethod.cod:
            return PaymentLink(payment_method=PaymentMethod.cod, payment_url=None)
        attempt = await self.payments.by_order(order.id)
        if not attempt:
            attempt = PaymentAttempt(
                id=uuid4(),
                order_id=order.id,
                provider=order.payment_method,
                amount=order.total,
                request_id=str(uuid4()),
            )
            self.session.add(attempt)
        await self.session.flush()
        # Durable intent allows an IPN to arrive while the HTTP request is in flight.
        # It also makes retries reuse both reference and requestId after a timeout.
        await self.session.commit()
        if attempt.payment_url:
            return PaymentLink(payment_method=attempt.provider, payment_url=attempt.payment_url)
        if attempt.provider == PaymentMethod.vnpay:
            payment_url = self.create_vnpay_url(attempt, order, ip_address)
        else:
            payment_url = await self.create_momo_url(attempt)
        # Never overwrite payment/order state established by a concurrent callback.
        current = await self.orders.detail(order_id, user_id=user_id, lock=True)
        await self.payments.reload(attempt)
        if current.status != OrderStatus.pending:
            raise conflict("Order is no longer awaiting payment; reload its current status")
        if await OrderService(self.session).expire(current):
            await self.session.commit()
            raise conflict("Order has expired")
        attempt.payment_url = payment_url
        await self.session.flush()
        return PaymentLink(payment_method=attempt.provider, payment_url=payment_url)

    def create_vnpay_url(self, attempt, order, ip_address):
        s = self.settings
        local = ZoneInfo("Asia/Ho_Chi_Minh")
        fields = {
            "vnp_Version": "2.1.0",
            "vnp_Command": "pay",
            "vnp_TmnCode": s.vnpay_tmn_code,
            "vnp_Amount": str(int(attempt.amount) * 100),
            "vnp_CurrCode": "VND",
            "vnp_TxnRef": str(attempt.id),
            "vnp_OrderInfo": f"Thanh toan {attempt.id}",
            "vnp_OrderType": "other",
            "vnp_Locale": "vn",
            "vnp_ReturnUrl": s.vnpay_return_url,
            "vnp_IpAddr": ip_address,
            "vnp_CreateDate": aware(attempt.created_at).astimezone(local).strftime("%Y%m%d%H%M%S"),
            "vnp_ExpireDate": aware(order.expires_at).astimezone(local).strftime("%Y%m%d%H%M%S"),
        }
        signature = vnpay_signature(fields, s.vnpay_hash_secret.get_secret_value())
        return f"{s.vnpay_pay_url}?{urlencode(sorted(fields.items()))}&vnp_SecureHash={signature}"

    async def create_momo_url(self, attempt):
        s = self.settings
        fields = {
            "partnerCode": s.momo_partner_code,
            "amount": int(attempt.amount),
            "orderId": str(attempt.id),
            "orderInfo": f"Thanh toan {attempt.id}",
            "requestId": attempt.request_id,
            "redirectUrl": s.momo_redirect_url,
            "ipnUrl": s.momo_ipn_url,
            "extraData": "",
            "requestType": "captureWallet",
        }
        signature = momo_signature(
            {"accessKey": s.momo_access_key.get_secret_value(), **fields},
            s.momo_secret_key.get_secret_value(),
        )
        try:
            async with httpx.AsyncClient(timeout=35, follow_redirects=False) as client:
                response = await client.post(
                    s.momo_create_url,
                    json={**fields, "signature": signature, "lang": "vi", "autoCapture": True},
                )
                response.raise_for_status()
                result = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise AppError(
                502,
                "payment_gateway_unavailable",
                "Payment result uncertain; retry this order",
            ) from exc
        if not isinstance(result, dict):
            raise AppError(502, "invalid_gateway_response", "Invalid provider response")
        if (
            result.get("partnerCode") != s.momo_partner_code
            or result.get("orderId") != str(attempt.id)
            or result.get("requestId") != attempt.request_id
            or result.get("amount") != int(attempt.amount)
        ):
            raise AppError(
                502, "invalid_gateway_response", "Provider response does not match intent"
            )
        if result.get("signature"):
            keys = (
                "amount",
                "orderId",
                "partnerCode",
                "payUrl",
                "requestId",
                "responseTime",
                "resultCode",
            )
            signed = {key: result.get(key, "") for key in keys}
            expected = momo_signature(
                {"accessKey": s.momo_access_key.get_secret_value(), **signed},
                s.momo_secret_key.get_secret_value(),
            )
            if not hmac.compare_digest(expected, str(result["signature"]).lower()):
                raise AppError(502, "invalid_gateway_response", "Invalid provider signature")
        if result.get("resultCode") != 0:
            raise AppError(502, "payment_rejected", "Provider rejected this payment intent")
        payment_url = result.get("payUrl", "")
        if not isinstance(payment_url, str) or len(payment_url) > 4096:
            raise AppError(502, "invalid_gateway_response", "Invalid provider payment URL")
        parsed = urlsplit(payment_url)
        if parsed.scheme != "https" or not (parsed.hostname or "").endswith(".momo.vn"):
            raise AppError(502, "invalid_gateway_response", "Invalid provider payment URL")
        return payment_url

    def verify_momo(self, notification):
        self.ensure_config(PaymentMethod.momo)
        s = self.settings
        fields = notification.model_dump(exclude={"signature"})
        fields["accessKey"] = s.momo_access_key.get_secret_value()
        expected = momo_signature(fields, s.momo_secret_key.get_secret_value())
        if notification.partnerCode != s.momo_partner_code or not hmac.compare_digest(
            expected, notification.signature.lower()
        ):
            raise AppError(400, "invalid_signature", "Invalid payment signature or merchant")

    def verify_vnpay(self, fields):
        self.ensure_config(PaymentMethod.vnpay)
        s = self.settings
        signed = {
            k: v
            for k, v in fields.items()
            if k.startswith("vnp_") and k not in ("vnp_SecureHash", "vnp_SecureHashType")
        }
        expected = vnpay_signature(signed, s.vnpay_hash_secret.get_secret_value())
        if fields.get("vnp_TmnCode") != s.vnpay_tmn_code or not hmac.compare_digest(
            expected, fields.get("vnp_SecureHash", "").lower()
        ):
            raise AppError(400, "invalid_signature", "Invalid payment signature or merchant")

    async def apply_result(
        self, provider, reference, amount, transaction_id, success, request_id=None
    ):
        try:
            attempt_id = UUID(reference)
        except (ValueError, TypeError) as exc:
            raise missing("Payment intent") from exc
        attempt = await self.payments.get(attempt_id)
        if not attempt or attempt.provider != provider:
            raise missing("Payment intent")
        order = await self.orders.detail(attempt.order_id, lock=True)
        await self.payments.reload(attempt)
        if (
            amount != int(attempt.amount)
            or amount != int(order.total)
            or order.payment_method != provider
            or (request_id is not None and request_id != attempt.request_id)
        ):
            raise AppError(400, "payment_mismatch", "Payment does not match the order")
        if attempt.paid_at:
            if success and attempt.transaction_id != transaction_id:
                raise conflict("Payment intent already settled by another transaction")
            return False
        if not success:
            return True  # Failure does not erase a later success or release stock prematurely.
        if not transaction_id or transaction_id == "0" or len(transaction_id) > 100:
            raise AppError(400, "invalid_transaction", "Invalid payment transaction reference")
        await OrderService(self.session).expire(order)
        attempt.transaction_id, attempt.paid_at = transaction_id, now()
        if order.status in (OrderStatus.cancelled, OrderStatus.expired):
            order.payment_status = PaymentStatus.refund_required
        elif order.status == OrderStatus.pending:
            order.payment_status = PaymentStatus.paid
            order.status = OrderStatus.confirmed
        else:
            raise conflict("Order cannot accept this payment")
        await self.session.flush()
        return True
