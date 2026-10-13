---
key: TASK-SOOPI-001
type: task
group: normative
system: SYS-SOOPI
status: done
revision: 2
relations:
  implements: [FR-SOOPI-001]
---
# TASK-SOOPI-001

Triển khai backend trong `soopi/` theo CMP-SOOPI-BACKEND revision 1 và
AC-SOOPI-001..008. Viết tài liệu trước, thông báo người dùng khi sẵn sàng code.
Không yêu cầu khởi động server, database thật hoặc provider thật. Xác minh logic,
syntax và ghi evidence với hash cây code trước khi đánh dấu done.

## Kết quả

Backend, migration, cấu hình, docs, dependencies và tests nằm hoàn toàn trong
`soopi/`. Hoàn thành AC-SOOPI-001..008 trong scope triển khai; current-tree
verification: 47 tests passed, lint sạch, 53 Python files đúng format, compileall
pass. Bằng chứng và SHA-256 manifest code revision:
[`VERIFY-SOOPI-001`](../evidence/VERIFY-SOOPI-001.json).

Verification dùng SQLite trong bộ nhớ và mock HTTP. PostgreSQL concurrency,
merchant callback thật và vận hành server không nằm trong kết quả kiểm tra.
