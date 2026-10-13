---
key: PLAN-TASK-RKG-048
type: implementation-plan
group: evidence
scope: system
system: SYS-RKG
task_key: TASK-RKG-048
revision: 1
plan_date: '2026-10-09'
change_set: CHG-RKG-2026-015
provenance: lifecycle-backfill-after-code
---

# PLAN-TASK-RKG-048

Plan này ghi file đã có trên cây. Nó không phải cam kết viết trước lúc sửa code.

## File đã có

- `src/rkg/adapters/django_framework.py` — đã có trên cây trước lát hồ sơ này.
- `src/rkg/adapters/builtins.py` — đã có trên cây trước lát hồ sơ này.
- `tests/conformance/test_django_framework.py` — đã có trên cây trước lát hồ sơ này.
- `tests/evaluation/test_django_census.py` — đã có trên cây trước lát hồ sơ này.
- `tests/evaluation/fixtures/rkg-fixture-django` — đã có trên cây trước lát hồ sơ này.
- `tests/evaluation/expected_django.json` — đã có trên cây trước lát hồ sơ này.

Oracle census: `tests/evaluation/fixtures/rkg-fixture-django + tests/evaluation/expected_django.json`. Bản sao `repo-test/` cùng tên, nếu còn, không phải oracle của census.

## Cách kiểm

1. `pytest tests/conformance/test_django_framework.py tests/evaluation/test_django_census.py -q` — chưa chạy trong lát hồ sơ này (`not_run`).
2. Đối chiếu assert của suite với `satisfies` của STORY-RKG-036. AC không có assert không được thêm vào `satisfies`.

## Không làm

- Sửa `src/`, `tests/`, `frontend/` hoặc `repo-test/` trong lát hồ sơ này.
- Thăng deep-supported.
- Ký gate hoặc đánh task `done`.
- Gắn CHG-RKG-2026-015 vào `adapter_scope` của CHG-RKG-2026-001.
- Bịa kết quả pytest.
