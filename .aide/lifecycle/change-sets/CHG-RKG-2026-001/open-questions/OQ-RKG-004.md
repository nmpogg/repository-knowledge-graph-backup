---
uid:
key: OQ-RKG-004
type: open-question
group: normative
scope: lifecycle
system: SYS-RKG
status: resolved
revision: 2
ownership: {accountable_team: TEAM-RKG, accountable_role: product-owner}
relations: {blocks: [], resolved_by: [FR-RKG-001, API-RKG-CORE-v1, UXF-RKG-003]}
classification: internal
ai_assisted: true
---

# Snapshot đã xóa có còn xuất hiện trong history không?

**Resolved:** Snapshot DELETE thành công bị loại khỏi lifecycle list. `410
snapshot_unavailable` chỉ dùng khi metadata/reference còn biết nhưng graph payload bị
mất ngoài lifecycle API; UI đưa recovery về repository detail/re-index. Không duy trì
một “version” hoặc history row riêng sau khi snapshot đã được xóa hợp lệ.
