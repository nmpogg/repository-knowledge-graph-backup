---
key: FR-SOOPI-001
type: requirement
group: normative
system: SYS-SOOPI
status: draft
revision: 1
---
# FR-SOOPI-001

Backend thương mại điện tử độc lập trong `soopi/`, theo yêu cầu người dùng.
Không thay đổi sản phẩm RKG. Không yêu cầu triển khai hoặc xác nhận app chạy.

- AC-SOOPI-001: Đăng ký, đăng nhập, refresh luân chuyển và logout; mật khẩu
  Argon2, access JWT ngắn hạn, refresh token chỉ lưu hash; không tự cấp admin.
- AC-SOOPI-002: Profile và CRUD địa chỉ chỉ thuộc người dùng hiện tại.
- AC-SOOPI-003: Catalog phân trang, tìm kiếm, lọc category/giá và variant;
  chỉ admin được thay đổi catalog; SKU/slug duy nhất; giá VND nguyên không âm.
- AC-SOOPI-004: Giỏ khách dùng token ngẫu nhiên chỉ lưu hash; giỏ user riêng;
  merge khi login có khóa, cộng số lượng và chặn vượt tồn kho.
- AC-SOOPI-005: Checkout atomic với khóa variant theo UUID, tính giá server,
  snapshot tên/SKU/giá/địa chỉ, trừ tồn kho, dọn giỏ; idempotency key theo user
  có đối chiếu payload; lỗi bất kỳ rollback toàn bộ.
- AC-SOOPI-006: Đơn thuộc user; hủy/expiry chỉ từ pending, hoàn tồn đúng một
  lần; thanh toán đến muộn chuyển refund_required; admin quản lý fulfillment.
- AC-SOOPI-007: COD, tạo URL VNPAY và yêu cầu MoMo; callback có xác minh chữ ký,
  merchant, transaction reference, amount; callback trùng không đổi kết quả;
  redirect trình duyệt không xác nhận thanh toán; không lưu/log bí mật.
- AC-SOOPI-008: Alembic migration, settings mẫu, lỗi thống nhất và test logic.

Không nằm trong scope: vận chuyển bên thứ ba, coupon, VAT, hoàn tiền tự động,
OAuth/social login, email xác minh, frontend và deployment. Phí ship cố định
từ cấu hình. Online payment giữ tồn trong thời hạn cấu hình; expiry chạy bằng
CLI định kỳ. COD pending chờ admin xác nhận. Admin được cấp ngoài API công khai.
