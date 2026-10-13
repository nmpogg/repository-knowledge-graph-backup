---
uid:
key: OQ-RKG-005
type: open-question
group: normative
scope: lifecycle
system: SYS-RKG
status: resolved
revision: 2
ownership: {accountable_team: TEAM-RKG, accountable_role: product-owner}
relations: {blocks: [], resolved_by: [FR-RKG-001, ADR-2026-004, API-RKG-CORE-v1, REV-RKG-2026-003]}
classification: internal
ai_assisted: true
---

# Có cần RepositoryVersion giữa Repository và Snapshot không?

**Resolved:** không tạo RepositoryVersion. Domain dùng `Repository 1 — N Snapshot`;
Snapshot là phiên bản đã index và mang source revision/config/tool versions. Catalog
có thể đăng ký nhiều repository độc lập nhưng graph/query/conversation chỉ thuộc một
repository/snapshot. Quyết định này thay phần Repo History toàn cục cũ trong tài liệu
đối chiếu; `.aide/` là normative source cho baseline đang draft.
