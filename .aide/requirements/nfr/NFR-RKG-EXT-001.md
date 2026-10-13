---
uid:
key: NFR-RKG-EXT-001
type: non-functional-requirement
group: normative
scope: system
system: SYS-RKG
status: approved
revision: 3
ownership:
  accountable_team: TEAM-RKG
  accountable_role: architect
relations:
  satisfies: [GOAL-RKG-004]
  constrains: [FR-RKG-002]
classification: internal
ai_assisted: true
---

# NFR-RKG-EXT-001 — Adapter extensibility

## Mô tả

Core indexing, graph storage và public API phải tiếp nhận language/framework adapter
mới qua contract version hóa mà không gắn nhánh xử lý vào một ngôn ngữ hoặc framework cụ thể.

## Yêu cầu (normative)

1. `LanguageAdapter` khai báo ID/version, language/grammar target, file patterns,
   ignore conventions, capabilities và các entrypoint detect/parse/extract/resolve.
2. `FrameworkAdapter` khai báo language compatibility, technology/version constraints,
   application-entrypoint detection và các extractor capability phụ thuộc framework.
3. Adapter chỉ nhận immutable source manifest/config và trả parsed units,
   `FactBatch`, diagnostics và capability report theo schema chung; adapter không ghi
   graph, gọi network hoặc thay đổi lifecycle state.
   Parsed unit có thể là AST, CST hoặc representation có cấu trúc tương đương phù hợp
   với ngôn ngữ; raw-source regex không phải representation chung giữa các adapter.
4. Core coordinator chọn adapter qua registry; core không chứa `if/switch` theo adapter
   ID, language hoặc framework cụ thể.
5. Thêm adapter conforming không yêu cầu migration graph schema hoặc thay đổi public
   API. Nếu cần semantic entity/edge mới, đó là schema change riêng có versioning.
6. Mọi adapter phải chạy chung conformance suite về deterministic ordering, evidence,
   diagnostics, path boundary, no-source-execution và `FactBatch` validation.
7. Python 3.12/FastAPI/SQLAlchemy 2.x/aiokafka là adapter set đầu tiên của MVP, không
   phải dependency của core contract.
8. LLM không được dùng để tạo entity/relationship normative. Nếu sau này dùng AI để
   gợi ý diagnostic hoặc candidate, output phải nằm ngoài graph chính cho tới khi được
   một deterministic rule xác minh và gắn evidence.

## Nghiệm thu

1. Chốt comparison revision chứa core adapter contract nhưng chưa có conformance
   fixture adapter.
2. Trong change riêng, thêm conformance adapter, registry entry, fixture source và
   test registration; chạy `TEST-RKG-ADAPTER-CONFORMANCE`.
3. `pass_rate = passed_contract_tests / total_contract_tests` phải bằng 100%.
4. Diff so với comparison revision chỉ được nằm trong adapter/registry/fixture/test
   registration; không sửa core coordinator, graph schema hoặc public API.
5. Static check phải cho kết quả 0 branch/lookup đặc biệt trong core theo adapter ID,
   language hoặc framework cụ thể.
6. Evidence lưu comparison revision, adapter contract version, per-test result,
   machine-readable changed-file list, allowlist result và static-check result.
