---
key: PLAN-TASK-RKG-030
type: implementation-plan
group: evidence
revision: 1
task_key: TASK-RKG-030
captured_at: '2026-10-06T16:13:31+07:00'
captured_against:
  baseline: BL-CHG-RKG-2026-002-r8
  context: CTX-TASK-RKG-030
  approval: approval-011
classification: internal
ai_assisted: true
---
# PLAN-TASK-RKG-030 — Migration v3 và durable conversation JSON

## Thứ tự và kiểm chứng

1. RED: thêm tests/integration/test_chatbot_storage.py và tests/unit/test_chatbot_metadata.py: fresh/current schema3, migration2 preservation/replay/shape refusal/fault rollback, metadata/pending state restart/replay/atomic failure/bounds. Chạy riêng để chứng minh fail do thiếu implementation.
2. GREEN: src/rkg/storage/_util.py và migrate.py: dispatch3 và guarded migration theo MIG r1; không đổi signed DDL/TBL. Test v0/v1 upgrade chain và failure paths.
3. GREEN: src/rkg/storage/conversation_json.py, records.py, turns.py và conversations.py: typed schema/semantic validation, UTF-8 bounds, persisted nullable metadata, unknown future read, structured pending intent. Kiểm malformed fields/bounds/no write.
4. GREEN: src/rkg/conversations/service.py: ProviderResult metadata + explicit pending action, TurnContext stored pending intent; terminal writes atomic and failure preserves committed focus/intent. Redact before storage, no metadata reconstruction on replay.
5. Update tests/integration/test_directory_entities.py physical-current assertions to exported counter; retain historical snapshot version assertions. Chạy affected storage/conversation/API/grounded regressions, Ruff and git diff --check.
6. Ghi TEST-RKG-CHATBOT-STORAGE-001 với code/artifact hashes, diary bốn heading và trạng thái subchecks; chỉ sau đó task done. Không tuyên bố AC077/080 end-to-end hoàn tất từ storage foundation.

Không gọi provider thật, migrate DB đang chạy, re-index hoặc thay UI trong task này.
