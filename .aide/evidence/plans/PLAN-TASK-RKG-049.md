---
key: PLAN-TASK-RKG-049
type: implementation-plan
group: evidence
scope: system
system: SYS-RKG
task_key: TASK-RKG-049
revision: 1
plan_date: '2026-10-09'
change_set: CHG-RKG-2026-016
provenance: lifecycle-backfill-after-code
---

# PLAN-TASK-RKG-049

Plan này ghi file đã có trên cây. Nó không phải cam kết viết trước lúc sửa code.

## File đã có

- `src/rkg/adapters/next_framework.py` — đã có trên cây trước lát hồ sơ này.
- `src/rkg/adapters/builtins.py` — đã có trên cây trước lát hồ sơ này.
- `tests/conformance/test_next_framework.py` — đã có trên cây trước lát hồ sơ này.
- `tests/evaluation/test_next_census.py` — đã có trên cây trước lát hồ sơ này.
- `tests/evaluation/fixtures/rkg-fixture-next` — đã có trên cây trước lát hồ sơ này.
- `tests/evaluation/expected_next.json` — đã có trên cây trước lát hồ sơ này.

Oracle census: `tests/evaluation/fixtures/rkg-fixture-next + tests/evaluation/expected_next.json`. Bản sao `repo-test/` cùng tên, nếu còn, không phải oracle của census.

## Cách kiểm

1. `pytest tests/conformance/test_next_framework.py tests/evaluation/test_next_census.py -q` — chưa chạy trong lát hồ sơ này (`not_run`).
2. Đối chiếu assert của suite với `satisfies` của STORY-RKG-037. AC không có assert không được thêm vào `satisfies`.

## Không làm

- Sửa `src/`, `tests/`, `frontend/` hoặc `repo-test/` trong lát hồ sơ này.
- Thăng deep-supported.
- Ký gate hoặc đánh task `done`.
- Gắn CHG-RKG-2026-016 vào `adapter_scope` của CHG-RKG-2026-001.
- Bịa kết quả pytest.
