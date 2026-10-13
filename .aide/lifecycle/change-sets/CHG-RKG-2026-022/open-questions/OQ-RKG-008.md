---
uid:
key: OQ-RKG-008
type: open-question
group: normative
scope: lifecycle
system: SYS-RKG
status: open
revision: 1
ownership: {accountable_team: TEAM-RKG, accountable_role: product-owner}
relations:
  part_of: [CHG-RKG-2026-022]
  blocks: [TASK-RKG-055]
classification: internal
ai_assisted: true
---
# Chiều depends_on của liên kết HTTP tĩnh

## Câu hỏi

`AC-RKG-005` đã xuất bản then-clause `depends_on` theo chiều Callable→Callable hoặc Endpoint→Callable. `tests/unit/test_http_depends.py` assert Callable `depends_on` Endpoint. Chiều nào là hợp đồng hiện hành cho `TASK-RKG-055`?

## Trạng thái hiện tại

Câu hỏi còn mở. Then-clause `AC-RKG-005` không được sửa tại chỗ. Chưa có AC id mới.

Suite của `TASK-RKG-055` không được ghi là under test cho `AC-RKG-005` khi then-clause và assert lệch nhau.

OQ này chặn đóng `TASK-RKG-055` và chặn `component_merge` của `CHG-RKG-2026-022`. Gate của change set này giữ `pending`. OQ không đóng gate của change set khác và không đổi `approval-012` hay `approval-013`.

## Cách đóng

Một trong hai, do product owner chọn:

1. Giữ `AC-RKG-005` và thêm AC id mới cho Callable→Endpoint, rồi gắn AC đó vào story/task khi suite assert đúng id đó.
2. Quyết định suite không thỏa một AC đã xuất bản và giữ `AC-RKG-005` ngoài `satisfies` của `STORY-RKG-043`.

Đóng task hoặc ký gate trước khi OQ resolve là không hợp lệ.
