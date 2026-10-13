---
key: PROMPT-TASK-RKG-030-REVIEW-r2
type: reviewer-prompt
group: derived
revision: 1
non_normative: true
task: TASK-RKG-030
review_round: 2
classification: internal
ai_assisted: true
---
# PROMPT-TASK-RKG-030-REVIEW-r2 — Independent adversarial re-review

Bạn là reviewer độc lập vòng2 cho TASK-RKG-030. Tìm worktree branch feat/chatbot-storage-revision bằng git worktree list; review code ở đó. Nhánh fix/chatbot vẫn giữ checkpoint b91d8b7, không phải candidate đã sửa.

Đọc .aide/reviewer/packages/RVP-TASK-RKG-030-r2.yaml. Tự kiểm chứng baseline hash, 36 normative revision/hash pins và 10 candidate code/test hashes; mismatch thì báo stale và dừng readiness. So sánh với commit b91d8b7223cc968350fdf5b9ce7feb67506a2dbf. Đọc REV-RKG-2026-009 để giữ nguyên FND-TASK-RKG-030-001/002/003, attribution và fingerprints; không đổi ID.

Review theo Security/Operability/Completeness trong đúng storage scope. Đối chiếu TBL/DDL13/MIG1/API16/SCH/CON v1, FR005 AC077/080 và CMP/NFR được pin. TASK031–035 chưa triển khai không phải lỗi TASK030. Không đọc author plans/context/diaries/test evidence/approval/remediation rationale để hình thành kết luận; không lấy test tác giả làm independent proof.

Tự dựng ca âm/ca dương trên DB fixture tạm Kuzu0.11.3: (001) toàn physical shape và singleton trước mọi migration write, missing/wrong/extra table/column/type/PK/relationship/schema-meta; refusal giữ schema/data/version/applied_at, valid0/1/2→3 và3 no-op/rollback; (002) factual coverage unknown/not_applicable và clarification/insufficient facts phải fail trước persistence, còn complete/partial/guidance/legacy/replay hợp lệ; (003) greeting clear/replace/focus-changing/pending payload phải không đổi committed state, omitted/preserve action đúng vẫn preserve sau reload/replay. Kiểm regression atomicity/redaction/bounds/recovery/provider mutation isolation.

Không operator DB/.env/credentials/provider thật hoặc analyzed source execution. Không sửa code/spec/task/gate/approval/history. Ghi findings có stable ID, severity/perspective, bad_code/bad_spec, path/hash/line, trigger/impact/minimal fix. Các finding cũ chỉ resolved sau kiểm chứng độc lập, không suy từ author remediation claim.

Kết luận ready_for_component_merge_decision hoặc needs_revision, từng check passed/failed/not_run, append review record mới vào .aide/evidence/reviews/ với captured_against package hash/baseline/candidate hashes. Không ký gate thay người. Evidence không transcript/source/config/absolute host paths.
