# Soopi backend

Backend FastAPI độc lập: API → services → repositories → PostgreSQL.

Thiết kế chuẩn tắc nằm trong
[FR-SOOPI-001](docs/FR-SOOPI-001.md) và
[CMP-SOOPI-BACKEND](docs/CMP-SOOPI-BACKEND.md).
Trạng thái delivery: [TASK-SOOPI-001](docs/TASK-SOOPI-001.md).

Giá dùng VND nguyên; PostgreSQL là database mục tiêu. Tài khoản admin cần được
cấp ngoài các API công khai. MoMo/VNPAY cần merchant credentials và URL callback
đã đăng ký. Hoàn tiền thực tế, vận chuyển, coupon, VAT và email ngoài scope.

## Cấu trúc

`app/api/` nhận request và kiểm tra quyền; `schemas/` xác thực DTO; `services/`
điều phối nghiệp vụ và transaction; `repositories/` chứa truy vấn; `models/`
định nghĩa ORM. `core/` chứa settings, session, security và error handlers.
`alembic/` có migration schema độc lập. Toàn bộ cấu hình, test, cache và tài liệu
nằm trong thư mục này, không phụ thuộc ứng dụng ở thư mục cha.

## Quy tắc nghiệp vụ

- Access JWT tham chiếu refresh session; logout hoặc refresh làm access token
  của session cũ mất hiệu lực. Refresh token và guest token chỉ lưu SHA-256.
- Giỏ khách dùng `X-Guest-Token`. Đăng nhập có header này sẽ merge và tiêu thụ
  giỏ khách. Merge vượt tồn kho trả 409 và rollback, không mất giỏ nào.
- Checkout yêu cầu `Idempotency-Key`, chỉ nhận địa chỉ, phương thức thanh toán
  và ghi chú. Giá/phí lấy từ server. Retry cùng key và payload trả đơn cũ.
- Đặt hàng trừ available stock; hủy pending hoặc hết hạn hoàn tồn một lần.
  Đơn online paid tự chuyển confirmed. COD được admin xác nhận và ghi paid
  khi delivered. `stock` trên variant là lượng còn bán được sau reservation.
- Tạo payment link gọi API riêng sau checkout. Intent được commit trước gọi
  MoMo, timeout giữ cùng requestId để retry. Khi provider từ chối intent,
  người dùng có thể hủy pending và tạo đơn mới; không tự sinh payment thứ hai.
- Chỉ IPN được xác minh mới xác nhận thanh toán. Callback trùng không trừ tồn
  lại. Thanh toán thành công sau hủy/hết hạn ghi `refund_required` để đối soát.
- Chạy `python -m app.expire_orders` định kỳ để giải phóng đơn online pending
  quá hạn. Chưa có scheduler được khởi động tự động trong app.

## Cài đặt và kiểm tra

Python >= 3.12. Các lệnh dưới đây chạy từ chính thư mục `soopi/`:

```powershell
uv --no-config --cache-dir .cache/uv venv .venv
uv --no-config --cache-dir .cache/uv pip install --python .venv/Scripts/python.exe '.[test]'
Copy-Item .env.example .env
# Điền DATABASE_URL, JWT_SECRET và cấu hình merchant trong .env.
.venv/Scripts/alembic.exe upgrade head
.venv/Scripts/uvicorn.exe app.main:app --host 127.0.0.1 --port 8000 --no-access-log
.venv/Scripts/python.exe -m pytest -q
.venv/Scripts/ruff.exe check app tests alembic
```

[API contract](docs/API-SOOPI-001.md) mô tả route, headers và response.
Test dùng SQLite trong bộ nhớ và HTTP mock; không khẳng định row lock
PostgreSQL hoặc giao dịch merchant thật đã được kiểm tra. Bằng chứng kiểm tra
và hash revision nằm trong `evidence/`.
