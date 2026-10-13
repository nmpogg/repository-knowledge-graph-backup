---
key: PLAN-CHG-RKG-2026-002-r5
type: implementation-plan
group: evidence
revision: 1
captured_at: '2026-10-06T16:13:31+07:00'
change_set: CHG-RKG-2026-002
previous_plan: PLAN-CHG-RKG-2026-002-r4
captured_against:
  baseline: BL-CHG-RKG-2026-002-r8
  sha256: a2620db609df23ceb548f86c4b41cecc983a9e4d4f25c43322f663521240a61c
  contract_approval: approval-011
authorization: CR-RKG-010
classification: internal
ai_assisted: true
---
# PLAN-CHG-RKG-2026-002-r5 — Kế hoạch triển khai chatbot

Viết trước dòng production code đầu tiên. Signed FR/L2/UX/L3 giữ nguyên. Task theo thứ tự dưới; các file nằm trong context từng task.

1. TASK-RKG-030 — Migration v3 và lưu metadata/pending intent: Add guarded atomic 2→3 dispatcher; preserve old pins/rows/hash/state, verified no-op and rollback.; Persist typed bounded response metadata in the terminal transaction; legacy/future metadata maps to unknown.; Add explicit preserve/replace/clear pending-intent updates without losing original question or state on errors/restart.
2. TASK-RKG-031 — Language resolver, endpoint lookup và clarification: Resolve vi/en with identifier exclusion; default locale preserves legacy fingerprint.; Exact method/path/type before paging; collisions/overflow clarify.; Greeting guards with zero graph/model calls; ordinal/button resumes committed original intent, legacy asks restatement.
3. TASK-RKG-032 — Validate narrative references và render câu trả lời: Wire read-plan v2/narrative v1 provider schemas; budgets/input preflight remain fixed.; Validate root/anchor/direction/path/evidence/cycles in full; fail closed, no salvage/repair.; Render direct/indirect vi/en relations, Endpoint handler bridge and exact claim/citation bindings.
4. TASK-RKG-033 — Capabilities, locale/history và exact citation API: Expose coherent capability negotiation and optional ui_locale; old defaults/request identities retained.; Return stored metadata on POST/history; optional include_unavailable preserves old default 410.; Exact per-turn citation lookup verifies ownership/index/pinned evidence, no substitution or source excerpts.
5. TASK-RKG-034 — Cập nhật Ask hiện có: Negotiate backend features; bind metadata/legacy unknown and unavailable history correctly.; One primary answer with collapsed claims, clear ordered candidates, translated limitations and distinct errors.; Exact source disclosure with safe identity/path/lines and keyboard/focus behavior, reuse existing Ask.
6. TASK-RKG-035 — Kiểm chứng AC và hồi quy toàn luồng: Verify malicious/foreign/cyclic/direction/schema outputs, budgets, replay, restart, concurrency and exact sources with synthetic fixtures.; Run appropriate backend/frontend/build checks and browser interactions on the implemented Ask.; Record pass/fail/not_run per AC; live provider acceptance needs actual authorized checks and is not fabricated.

Mỗi task: RED kiểm tra hành vi còn thiếu → GREEN trong code scope → regression phù hợp → evidence current hashes → task done. Chỉ task đã có context và dependency pass được chạy. Không dùng fixtures/contract approval làm bằng chứng live-provider, UAT hay release. Task sau revalidate code hashes vì dependency thay code.
