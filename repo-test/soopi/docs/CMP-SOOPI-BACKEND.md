---
key: CMP-SOOPI-BACKEND
type: component
group: normative
system: SYS-SOOPI
status: draft
revision: 1
relations:
  implements: [FR-SOOPI-001]
---
# CMP-SOOPI-BACKEND

## Layer và transaction

API/controller -> service -> repository -> SQLAlchemy async -> PostgreSQL.
Schemas dùng Pydantic v2; settings dùng pydantic-settings; repositories flush
nhưng không commit. Dependency session commit trước khi response được gửi,
rollback khi lỗi. Services điều phối nghiệp vụ; không tin giá từ client.

Mọi thao tác giỏ user và checkout khóa user trước rồi cart, variant theo UUID.
Hủy, expiry và callback khóa order trước khi đổi trạng thái; hoàn tồn khóa
variant theo cùng thứ tự. PostgreSQL READ COMMITTED và SELECT FOR UPDATE là
yêu cầu concurrency. SQLite chỉ dành cho test logic, không chứng minh row lock.

Product luôn có variant bán được; tồn là available stock, reserve bằng giảm
stock lúc checkout. OrderItem snapshot giá; Order snapshot địa chỉ. Không hard
delete product/variant đã bán, dùng active flag. Cart item chưa reserve stock.

## Auth và ownership

RefreshSession lưu digest token ngẫu nhiên, thời hạn và revoked_at; refresh
khóa row, revoke cũ, cấp session mới. Access token tham chiếu session để logout
có hiệu lực tức thời. Guest token trong header X-Guest-Token; phát hành qua API,
không nhận cart ID để chứng minh ownership. Login merge guest cart trong cùng
transaction; token guest không được ghi log hoặc response ngoài lần tạo.

## Orders/payment

Order pending -> confirmed -> shipped -> delivered. Pending -> cancelled/expired
hoàn tồn. Online confirmed chỉ khi đã paid; COD paid khi delivered.
Callback lỗi thanh toán không ghi đè paid, không tự cancel đơn; user có thể
retry cùng payment attempt đến expiry. Late success ghi refund_required,
không giao hàng hoặc trừ tồn lại. Refund thực tế xử lý ngoài scope.

Checkout Idempotency-Key bắt buộc và unique theo user; hash payload kiểm tra
retry. Payment attempt duy nhất mỗi order/provider, UUID reference và requestId
bền vững. Commit intent trước gọi MoMo để callback tìm được attempt; timeout
giữ intent để retry cùng requestId, không tạo order hoặc attempt mới. Chữ ký
MoMo HMAC-SHA256, VNPAY HMAC-SHA512; số tiền VNPAY nhân 100.

Migration và tài liệu SOOPI nằm hoàn toàn trong `soopi/`. Backend độc lập,
không phụ thuộc code, cấu hình hoặc lifecycle của repository chứa nó.

## Nguồn kỹ thuật

- https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html
- https://developers.momo.vn/v3/vi/docs/payment/api/payment-api/init/
- https://developers.momo.vn/v3/vi/docs/payment/api/result-handling/notification/
- https://sandbox.vnpayment.vn/apis/docs/thanh-toan-pay/pay.html
