---
key: PLAN-TASK-RKG-055
type: implementation-plan
group: evidence
scope: system
system: SYS-RKG
task_key: TASK-RKG-055
revision: 1
plan_date: '2026-10-09'
change_set: CHG-RKG-2026-022
provenance: lifecycle-backfill-after-code
---

# PLAN-TASK-RKG-055

Plan này ghi file đã có trên cây. Nó không phải cam kết viết trước lúc sửa code.

## File đã có

- `src/rkg/jobs/http_depends.py` — đã có trên cây trước lát hồ sơ này.
- `src/rkg/jobs/coordinator.py` — đã có trên cây trước lát hồ sơ này.
- `tests/unit/test_http_depends.py` — đã có trên cây trước lát hồ sơ này.

Oracle census: `none`. Bản sao `repo-test/` cùng tên, nếu còn, không phải oracle của census.

## Cách kiểm

1. `pytest tests/unit/test_http_depends.py -q` — chưa chạy trong lát hồ sơ này (`not_run`).
2. Đối chiếu assert của suite với `satisfies` của STORY-RKG-043. AC không có assert không được thêm vào `satisfies`.

## Không làm

- Sửa `src/`, `tests/`, `frontend/` hoặc `repo-test/` trong lát hồ sơ này.
- Thăng deep-supported.
- Ký gate hoặc đánh task `done`.
- Gắn CHG-RKG-2026-022 vào `adapter_scope` của CHG-RKG-2026-001.
- Bịa kết quả pytest.
