---
key: API-SOOPI-001
type: api-contract
system: SYS-SOOPI
status: draft
revision: 1
---
# API-SOOPI-001

Prefix `/api/v1`. JSON request và response. UUID dùng cho resource IDs.
Response phân trang: `{items, total, page, size}`; `size` tối đa 100.
Error: `{error: {code, message}}`; validation trả `fields` không chứa input.
Success không dùng wrapper mặc định; schema wrapper generic có sẵn để mở rộng.

| Method | Route | Quyền / ý nghĩa |
|---|---|---|
| POST | /auth/register | Công khai; email, password >= 10 ký tự, full_name; trả token pair |
| POST | /auth/login | Công khai; email, password; optional X-Guest-Token để merge |
| POST | /auth/refresh | refresh_token; luân chuyển, thu hồi session cũ |
| POST | /auth/logout | Bearer; thu hồi session hiện tại; 204 |
| GET, PATCH | /users/me | Bearer; profile; PATCH chỉ full_name/phone |
| GET, POST | /users/me/addresses | Bearer; địa chỉ của mình |
| PUT, DELETE | /users/me/addresses/{id} | Bearer; PUT đầy đủ địa chỉ, DELETE 204 |
| GET | /products | Công khai; page/size/q/category_id/min_price/max_price |
| GET | /products/{id} | Công khai; chỉ product/category active, variants active |
| POST | /products | Admin; category_id/name/slug/description/variants |
| PATCH | /products/{id} | Admin; cập nhật hoặc is_active=false để ngừng bán |
| POST | /products/{id}/variants | Admin; thêm SKU/name/price/stock/attributes |
| PATCH | /products/{id}/variants/{variant_id} | Admin; giá, available stock, attributes, active |
| GET | /categories | Công khai; phân trang, chỉ active |
| POST | /categories | Admin; name/slug |
| PUT | /categories/{id} | Admin; cập nhật name/slug |
| DELETE | /categories/{id} | Admin; soft deactivate, trả category |
| POST | /cart/guest | Công khai; phát guest_token một lần |
| GET, DELETE | /cart | Bearer hoặc X-Guest-Token; xem/xóa giỏ |
| POST | /cart/items | Bearer hoặc guest; variant_id/quantity; cộng số lượng |
| PATCH | /cart/items/{variant_id} | Bearer hoặc guest; quantity; đặt số lượng |
| DELETE | /cart/items/{variant_id} | Bearer hoặc guest; xóa item; 204 |
| POST | /orders | Bearer + Idempotency-Key; checkout atomic, trả order 201 |
| GET | /orders | Bearer; danh sách đơn của mình, phân trang |
| GET | /orders/{id} | Bearer; chi tiết đơn của mình |
| POST | /orders/{id}/cancel | Bearer; chỉ pending; retry hủy trả trạng thái hiện tại |
| POST | /orders/{id}/payment | Bearer; tạo URL MoMo/VNPAY; COD trả URL null |
| PATCH | /orders/{id}/status | Admin; confirmed → shipped → delivered |
| POST | /orders/webhooks/momo | IPN HMAC-SHA256; hợp lệ trả 204 |
| GET | /orders/webhooks/vnpay | IPN HMAC-SHA512; trả RspCode/Message |

Bearer có ưu tiên khi cả hai header giỏ hàng được gửi. Token Bearer không hợp lệ
không được chuyển sang quyền guest. Không có endpoint cấp admin công khai.
Địa chỉ gồm recipient, phone, line1, ward, district, province.

Checkout body:

```json
{"address_id":"<UUID>","payment_method":"cod","note":"Giao giờ hành chính"}
```

`payment_method`: cod/momo/vnpay. `Idempotency-Key` dài 8..100 ký tự, phạm vi
theo user; payload khác cùng key trả 409. Quantity nguyên 1..999; tối đa 100
variants trong giỏ; giá VND nguyên không âm. Thay giá và địa chỉ về sau không
đổi snapshot đơn đã tạo. API không nhận subtotal/total/role/user_id từ client.

VNPAY IPN xử lý duplicate query keys như dữ liệu không hợp lệ. Thành công yêu
cầu cả ResponseCode và TransactionStatus bằng 00. Mã IPN 97: sai signature;
01: thiếu intent; 04: sai amount; 02: đã settle; 00: đã xử lý.
MoMo resultCode=0 mới là paid; authorization khác không được ghi nhận paid.
Callback lỗi không xóa paid đã ghi nhận. Redirect URL chỉ phục vụ giao diện.

Nguồn protocol:
[MoMo wallet](https://developers.momo.vn/v3/vi/docs/payment/api/wallet/onetime/),
[MoMo IPN](https://developers.momo.vn/v3/vi/docs/payment/api/result-handling/notification/),
[VNPAY 2.1.0](https://sandbox.vnpayment.vn/apis/docs/chuyen-doi-thuat-toan/changeTypeHash.html).
