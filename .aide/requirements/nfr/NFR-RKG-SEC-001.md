---
uid:
key: NFR-RKG-SEC-001
type: non-functional-requirement
group: normative
scope: system
system: SYS-RKG
status: approved
revision: 7
ownership:
  accountable_team: TEAM-RKG
  accountable_role: architect
relations:
  constrains: [FR-RKG-001, FR-RKG-002, FR-RKG-004, FR-RKG-005]
classification: internal
ai_assisted: true
---

# NFR-RKG-SEC-001 — Security and privacy

## Mô tả
Bảo vệ máy host và dữ liệu nhạy cảm khi index/hỏi đáp local: giới hạn bề mặt tấn công,
không thực thi source đầu vào, không lưu secret.

## Yêu cầu (normative)

1. **Deployment surface:** chỉ loopback single-user; mutation/Q&A yêu cầu local session token và kiểm tra Origin/Host theo allowlist.
2. **Server-owned config:** `allowed_local_roots`, workspace root và LLM provider endpoint chỉ cấu hình phía server; client không đổi được.
3. **Local source boundary:** canonicalize path; từ chối path ngoài allowlist và symlink/junction escape; không lộ absolute host path trong error/log.
4. **Analyzer isolation:** không import/run source repo, không cài dependency, không gọi DB/broker/HTTP đích của ứng dụng đang phân tích.
5. **Data minimization:** không lưu hoặc log secret, configuration value, credential, message payload hay raw source. Operational log không chứa question/answer transcript. Conversation store chỉ được lưu turn/history đã redact theo định nghĩa canonical ở `DOM-RKG-CORE` và FR-RKG-005, không lưu chain-of-thought và không sao chép history sang operational log.
6. **LLM control plane:** chỉ thực thi plan qua schema + read-only query allowlist; citation phải thuộc context/snapshot trước khi publish answer; API key không trả về trình duyệt.
7. **Repository lifecycle:** create/update repository phải chạy lại canonical-path và symlink validation; source identity bất biến; canonical locator cần cho re-index chỉ được lưu server-side với host permissions, còn list/detail/error/log chỉ trả locator đã redact.
8. **Cross-repository isolation:** client đưa cặp repository/snapshot không cùng ownership nhận response không tiết lộ repository khác; delete/cascade phải scope bằng `repository_id` đã validate.
