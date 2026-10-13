# LLM provider boundary

`StructuredProvider.complete(request, budget)` accepts redacted messages and a
JSON Schema. `MockProvider`, `OpenRouterProvider` and `OpenAIProvider` validate the
original request schema and share completion parsing, usage and budget handling.
The bundled `o200k_base` tokenizer is checked against its upstream SHA-256 on load.

`configured_provider()` reads server-only `RKG_LLM_PROVIDER`: `openrouter` is the
default; `openai` selects the fixed official OpenAI Chat Completions endpoint.
OpenRouter uses `OPENROUTER_API_KEY` / `OPENROUTER_MODEL` (default
`openai/gpt-4o-mini`); OpenAI uses `OPENAI_API_KEY` / `OPENAI_MODEL` (default
`gpt-4o-mini`). Restart backend after selecting a provider. An invalid selector
fails startup with `llm_invalid_request`. A missing selected key is `llm_disabled`;
there is no cross-provider fallback. Keys are read from the server environment per
call and never sent to the browser. Model must support strict Structured Outputs.

OpenAI omits OpenRouter routing/usage extensions and sends `store=false`.
Its wire projection removes artifact annotations, `uniqueItems` and string-length
constraints (conservative base-model wire compatibility),
and gives string enums an explicit string type. The original schema is unchanged:
local validation still rejects duplicate items, invalid string lengths and all
other constraint failures. Both transports reject redirects without forwarding
credentials; invalid CLI provider selection returns a safe code and exit1.
Graph, evidence and topology checks remain mandatory before rendering.

Transport, refusal, malformed output, budget and timeout failures raise `LLMError`
with safe codes. Neither adapter logs prompts, responses, credentials or raw
exception messages. Usage and optional cost remain available to the coordinator.

Create one `TurnBudget` for the whole turn and share it across all model calls
and graph operations. Defaults impose no model-call, graph-query, input/output-token or total-turn deadline ceiling. None means unlimited; optional finite internal budgets remain enforceable. The provider measures token usage and validates an explicitly configured input
ceiling before making a request and validates JSON output against the supplied
schema. Retrieval, answer grounding, citation checks, history window, and HTTP
mapping are performed by the conversation coordinator in Task RKG 020/021.

Run the local contract tests with `python -m pytest tests/unit/test_llm_provider.py tests/unit/test_openai_provider.py`.
With `OPENROUTER_API_KEY` set server-side, run
`python -m pytest tests/integration/test_openrouter_live.py` for live acceptance.

OpenAI adapter and real API/storage tests use synthetic HTTP responses; they do
not demonstrate live credential or selected-model availability.
