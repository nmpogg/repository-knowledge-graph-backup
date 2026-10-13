---
uid:
key: UIS-RKG-001
type: ui-specification
group: normative
scope: system
system: SYS-RKG
status: draft
revision: 14
ownership: {accountable_team: TEAM-RKG, accountable_role: design-owner}
relations:
  owned_by: [CMP-RKG-WEB]
  derived_from: [UXF-RKG-001, UXF-RKG-002, UXF-RKG-003, SCR-RKG-001]
  refines: [UID-RKG-001]
  satisfies: [AC-RKG-011, AC-RKG-018, AC-RKG-027, AC-RKG-041, AC-RKG-043, AC-RKG-046, AC-RKG-047, AC-RKG-054, AC-RKG-056, AC-RKG-057, AC-RKG-059, AC-RKG-061, AC-RKG-066, AC-RKG-067, AC-RKG-068, AC-RKG-069, AC-RKG-070, AC-RKG-071, AC-RKG-072, AC-RKG-073, AC-RKG-009, AC-RKG-074, AC-RKG-075, AC-RKG-076, AC-RKG-077, AC-RKG-078, AC-RKG-079, AC-RKG-080, AC-RKG-081]
  constrained_by: [API-RKG-CORE-v1, NFR-RKG-UX-001, NFR-RKG-SEC-001, NFR-RKG-REL-001]
classification: internal
ai_assisted: true
---
# UIS-RKG-001 — Machine-readable UI behavior

```yaml
app_shell:
  default_route: /repositories
  routes:
    - /repositories
    - /repositories/new
    - /repositories/:repositoryId
    - /repositories/:repositoryId/edit
    - /jobs/:jobId
    - /explorer
    - /conversations
    - /conversations/:conversationId
  data_source: RkgClient
  modes: [mock, live]
  authoritative_source: api
  navigation:
    primary: [repositories, explorer, ask]
    contextual_requires_snapshot: [explorer, ask]
    skip_link_target: main
  context_bar:
    fields: [repository_display_name, snapshot_id, snapshot_created_at, warning_count]
    required_on: [explorer, conversation]
repository_list:
  read: GET /api/v1/repositories
  delete: DELETE /api/v1/repositories/{repository_id}
  states: [loading, empty, ready, error, delete-confirm, delete-blocked]
  order: [updated_at_desc, repository_id_asc]
  paging: {default: 20, maximum: 100}
  row_fields: [display_name, source_locator_redacted, updated_at, active_snapshot_id]
  persist_view_state: [q, offset]
repository_form:
  create: POST /api/v1/repositories
  update: PATCH /api/v1/repositories/{repository_id}
  source_type: [local]
  local_create_fields: [display_name, path, source_root, app_module, app_symbol, scan_defaults]
  update_fields: [display_name, source_root, app_module, app_symbol, scan_defaults, expected_revision]
  immutable_after_create: [source_type, path]
  states: [initial, validating, submitting, invalid, conflict, saved]
  preserve_draft_on: [invalid, conflict, network_error]
  error_focus: summary_then_first_invalid_field
repository_detail:
  read: GET /api/v1/repositories/{repository_id}
  index: POST /api/v1/repositories/{repository_id}/index-jobs
  open_active: /explorer?snapshot_id={active_snapshot_id}
  states: [loading, ready, no-active-snapshot, job-conflict, delete-confirm, delete-blocked]
  regions: [identity, active_snapshot, index_action, snapshot_history, danger_zone]
  source_locator: redacted_only
snapshot:
  list: GET /api/v1/repositories/{repository_id}/snapshots
  detail: GET /api/v1/repositories/{repository_id}/snapshots/{snapshot_id}
  activate: POST /api/v1/repositories/{repository_id}/snapshots/{snapshot_id}/activate
  delete: DELETE /api/v1/repositories/{repository_id}/snapshots/{snapshot_id}
  order: [created_at_desc, snapshot_id_asc]
  states: [loading, empty, ready, active, unavailable, activate-error, delete-confirm, delete-blocked]
  on_activate_success: navigate /explorer?snapshot_id={snapshot_id}
  immutable_fields: [source_revision, manifest_hash, scan_config_digest, analyzer_version, schema_version, adapter_versions]
  blocked_delete_codes: [snapshot_active, snapshot_in_use]
job_monitor:
  read: GET /api/v1/index-jobs/{job_id}
  stages: [queued, detecting, indexing, succeeded, succeeded_with_warnings, failed]
  polling: {honor_retry_after: true, max_backoff_seconds: 5, stop_on_terminal: true, cancel_on_unmount: true}
  on_success: navigate /explorer?snapshot_id={snapshot_id}
  app_selection:
    blocking_when: multiple_app_candidates
    auto_select_when: exactly_one_app_candidate
    technology_adapter_list_is_blocking: false
    preserve_selection_on: [retry, reindex]
  terminal_actions:
    succeeded: open_snapshot
    succeeded_with_warnings: inspect_report_then_open_snapshot
    failed: review_error_and_retry
  invariant_on_failure: active_snapshot_unchanged
explorer:
  search: GET /api/v1/entities
  graph: GET /api/v1/subgraph
  detail: GET /api/v1/entities/{id}
  context_identity: [repository_id, snapshot_id]
  panels: [evidence, technologies, dependencies, diagnostics]
  defaults: {direction: both, depth: 1, max_nodes: 50}
  contract_limits: {max_depth: 6, max_nodes: 200, max_edges: 400, min_context_chars: 2000, max_context_chars: 50000}
  states: [no-active-snapshot, loading, empty, ready, truncated, stale-unavailable, error]
  search_order: [type, qualified_name, id]
  select_behavior: explicit_only
  views: [graph, accessible_list, structure]
  controls: [direction, edge_types, depth, max_nodes, zoom, fit_selection, view_toggle]
  view_toggle: [graph, accessible_list, structure]
  structure_tree:
    source: GET /api/v1/entities
    paging: exhaust_snapshot_pages
    not_source: GET /api/v1/subgraph
    shape: single_tree
    cut_by: file_path
    path_separator: "/"
    file_path_normalization: backslash_to_slash
    nested_symbol_separator: "."
    symbol_boundary: ":"
    init_file: canonical_source_file_in_new_snapshots
    legacy_init_file: not_a_segment
    directory_nodes: canonical_Directory_entities
    directory_identity: api_entity_id
    new_snapshot_namespace_nodes: absent
    legacy_namespace: preserve_id_and_merge_same_file_display
    structural_evidence: relative_path_provenance_without_source_excerpt
    pathless_entities: root_siblings_cut_by_qualified_name
    entity_type_label: leaf_and_selectable_directory
    empty_qualified_name: name
    collapsible: [directory, file, symbol]
    default_expanded: [root, first_directory]
    default_collapsed: [file]
    canvas_states: [loading, empty, error]
    empty_when: snapshot_has_no_entities
    error_reporting: same_as_entity_search
  presets:
    api_to_db:
      direction: outgoing
      edge_types: [handled_by, calls, depends_on, reads, writes]
      max_depth: 4
    event_participants:
      direction: both
      edge_types: [publishes, consumes]
      max_depth: 1
    config_users:
      direction: incoming
      edge_types: [depends_on]
      max_depth: 1
    interface_implementations:
      direction: incoming
      edge_types: [implements, inherits_from]
      max_depth: 1
  on_truncated: show_limit_badge_and_controls
  export: POST /api/v1/context
  export_states: [ready, generating, validation-error, complete, error]
  invalid_context_recovery:
    no_active_snapshot: repository_detail
    snapshot_unavailable: repository_detail_reindex
    identity_mismatch: generic_not_found
  selection:
    open_detail_on: [node, edge, accessible_list_item, structure_directory, structure_file, structure_leaf]
    close_focus: restore_to_selected_item
evidence:
  locator: relative_path_and_line_only
  actions: [copy_relative_location]
  states: [closed, loading, ready, unavailable]
technology_panel:
  read: GET /api/v1/technologies?snapshot_id={snapshot_id}
  support_states: [supported_patterns, detected_only, version_unverified, unsupported_version]
  required_fields: [technology, evidence, support_state, limitations]
dependency_panel:
  read: GET /api/v1/dependencies?snapshot_id={snapshot_id}
  filters: [subtype, q]
  provenance: [declared, imported, usage]
  paging: {default: 20, maximum: 100}
diagnostic_panel:
  read: GET /api/v1/diagnostics?snapshot_id={snapshot_id}
  paging: {default: 20, maximum: 100}
conversation:
  list: GET /api/v1/conversations?repository_id={repository_id}&snapshot_id={snapshot_id}
  create: POST /api/v1/conversations
  turns: GET /api/v1/conversations/{id}/turns
  submit: POST /api/v1/conversations/{id}/turns
  delete: DELETE /api/v1/conversations/{id}
  identity_display: [repository_id, snapshot_id]
  states: [disabled, idle, pending, answered, needs_clarification, insufficient_evidence, error, conflict]
  citation_action: open_evidence_drawer
  question_max_chars: null # No application character ceiling; nonblank validation remains.
  submit_requires: [client_request_id, expected_revision]
  pending_disables: [duplicate_submit, delete]
  pending_allows: [read_history, open_existing_citation]
  no_simulated_streaming: true
  clarification_selection: explicit_only
  preserve_on_provider_error: [history, committed_focus, draft_question]
  limitation_flags: [retrieval_truncated, history_truncated]
  snapshot_change_behavior: keep_pin_and_offer_new_conversation
  unavailable_snapshot_behavior: keep_transcript_disable_submit_mark_citations_unavailable
  blocked_delete_codes: [conversation_busy]
  conversational_contract:
    API: {key: API-RKG-CORE-v1, revision: 16}
    schema: SCH-RKG-CONVERSATION-v1
    capabilities: GET /api/v1/conversations/capabilities
    required_features: [ui_locale, response_metadata_v1, exact_citation_lookup, history_unavailable]
    on_capabilities_404: legacy_mode
    on_capabilities_other_error: show_retry_do_not_infer_legacy
    provider_enabled_source: capabilities.provider_enabled
    when_provider_disabled: disable_submit_show_provider_guidance_keep_draft
    submit_ui_locale: current_locale_only_when_supported
    unavailable_history_query: include_unavailable=true_only_when_supported
    response_metadata_source: persisted_turn.response_metadata
    missing_or_unknown_metadata: unknown_coverage
    answer_render: plain_text_one_main_answer
    answer_language: response_metadata.language
    interface_language: UI_locale
    insufficient_render: turn.answer_or_one_translated_fallback_never_both
    claims: {disclosure: native_details, default_open: false, source_indexes: citation_indexes}
    subject: response_metadata.subject
    candidate_label_fields: [type, name, qualified_name, attributes.method, attributes.path]
    candidate_ordinal: array_index_plus_1
    candidate_submit: {question: displayed_ordinal, root_id: selected_id, client_request_id: new, expected_revision: latest, ui_locale: current_UI_locale_when_supported}
    candidate_auto_select: false
    selection_effective_language: original_pending_intent_on_server
    citation_lookup: GET /api/v1/conversations/{conversation_id}/turns/{turn_id}/citations/{citation_index}
    citation_index_base: 0
    source_label: persisted_evidence_id_or_readable_source_ordinal
    exact_location: lookup_response.evidence
    entity_detail_as_citation_fallback: forbidden
    quote_or_excerpt_render: forbidden
    filesystem_line_marker: absent
    source_dialog: {loading: true, focus_trap: true, escape_closes: true, restore_trigger_focus: true, snapshot_visible: true}
    source_error_404: exact_evidence_unavailable
    source_error_410: pinned_snapshot_unavailable_never_repin
    source_error_401: reload_local_session_no_automatic_retry
    retrieval_note: translate_response_metadata.limitations_next_to_answer
    history_note: response_metadata.history_truncated
    legacy_top_level_false_flags_imply_full_coverage: false
    snapshot_unavailable: {transcript: readable_from_opt_in_history, submit: disabled, candidates: disabled, sources: unavailable, offer: repository_reindex}
    preserve_provider_error_banner_after_history_reload: true
    same_key_retry_body: exact_original_question_root_locale
    provider_failure_retry: new_request_id_after_review
error_mapping:
  unauthorized: {http: 401, action: reload_local_session, retry_automatically: false}
  generic_not_found: {http: 404, disclose_ownership: false}
  index_job_busy: {http: 409, action: open_running_job}
  repository_conflict: {http: 409, action: reload_review_retry}
  repository_busy: {http: 409, action: explain_running_job}
  repository_in_use: {http: 409, action: explain_references}
  snapshot_active: {http: 409, action: activate_another_snapshot_first}
  snapshot_in_use: {http: 409, action: explain_references}
  conversation_conflict: {http: 409, action: reload_review_retry}
  conversation_busy: {http: 409, action: wait_for_terminal_turn}
  no_active_snapshot: {http: 409, action: index_repository}
  snapshot_unavailable: {http: 410, action: repository_detail_reindex}
  invalid_input: {http: 422, action: focus_validation_summary}
  provider_error: {http: 502, action: retry_with_new_request_id}
  llm_disabled: {http: 503, action: use_search_or_explorer}
  llm_timeout: {http: 504, action: retry_with_new_request_id}
security:
  render_repository_text_as: text
  show_source_locator_as: redacted_text
  markdown: sanitized
  forbidden_browser_content: [absolute_host_path, credential, raw_source, provider_chain_of_thought]
  mutation_header: X-RKG-Session
  persist_session_token_in_browser_storage: false
  ownership_mismatch: generic_not_found
a11y:
  skip_link: true
  one_h1_per_screen: true
  heading_order: sequential
  focus_visible: true
  graph_has_list_fallback: true
  status_announcer: polite
  error_announcer: assertive
  dialogs: {trap_focus: true, restore_focus: true}
  destructive_confirm: explicit_scope
  status_not_color_only: true
  reduced_motion: honored
  touch_target_min_px: 44
  composer_supports_ime: true
responsive:
  checkpoints_px: [375, 768, 1024, 1440]
  horizontal_scroll_allowed: [graph_canvas]
  desktop: {navigation_px: 240, contextual_drawer_px: 360}
  mobile: {navigation: top_bar_menu, tables: card_stack, detail: route_or_bottom_sheet}
```

Mock client fixtures ở M0 phải có response shape giống `API-RKG-CORE-v1`. Không
component nào được phát minh enum thứ hai cho repository lifecycle, job, snapshot,
support hoặc conversation status.

Giá trị trong khối YAML là testable contract của presentation layer. Khi API contract
đổi enum/limit/error semantics, cập nhật API trước, sau đó tăng revision UIS; không
sửa UIS để hợp thức hóa fixture cũ.

## Directory snapshot contract

Structure reads all snapshot entity pages. New snapshots use canonical Directory
nodes with repository-relative POSIX paths and no duplicate selectable folder nodes.
Directory/file/symbol selection uses the same detail drawer and identity as Graph/List.
Module/package attributes are metadata, not Namespace nodes. API responses for
older snapshots still use type `Namespace`. The client maps that type to UI
`module` and maps a `module` search back to `Namespace`. Structure merges a
`Namespace` and a `SourceUnit` that share a file into one file node. Stored IDs
are not rewritten. Structural evidence is manifest/path provenance and is
displayed without source excerpts.

## Focused entity flow controls

Explorer uses Entity flow by default, with All relationships available in Graph options.
Semantic roots show calls/accesses without imports or containment fan-out. Show files
and folders and Show declared dependencies are independent accessible checkboxes, both
off initially. Ownership nodes provide location only. Direction is disabled in flow
because root policy determines it; depth still controls semantic hops. Initial depth
and the API-to-DB preset use six hops to include service/repository helper chains. Overview opens
All relationships. Endpoint opening explicitly switches to flow; interface inheritance
presets use neighborhood. Flow nodes are not dimmed just because they are several hops
from the root. Context export uses the same profile and overlay controls.

Flow presentation follows top-to-bottom call stages with terminal data resources
in the final row. Shared-resource shortcut edges must not place a table among
callables. Cycles are condensed for layout; upstream resource views retain the
caller-to-resource direction. All flow edge labels remain readable, including
reads/writes in graphs over twelve edges. Edges skipping rows route through gaps
between nodes; they must not appear to originate from an intervening helper.

Show files and folders renders repository-relative location breadcrumbs on flow
steps, without additional ownership boxes/edges. Turning it on preserves flow
step identities and positions; Type-qualified method names distinguish shared
names. Endpoint opening closes the results pane; Results can reopen it. Selecting
a step retains the overall flow viewport. Structural roots still use architecture
exploration. A backend that does not acknowledge flow produces a translated error
and clears the previous graph, rather than displaying a neighborhood as flow.

## Conversational usability binding — CHG-RKG-2026-002

Revision 13 is the level-4 candidate derived from approved UXF-RKG-002 r5,
SCR-RKG-001 r9 and UID-RKG-001 r8, governed by API r16/TBL r13. Contract Gate is
pending; neither production client nor backend implements these additions yet.
The source design hashes signed by approval-010 are unchanged. This binding
does not introduce another chat page, status enum or visual system.

| AC | Binding / assertion |
|---|---|
| AC-RKG-074 | Negotiated optional ui_locale, persisted metadata.language; UI copy stays in interface locale while answer uses effective language |
| AC-RKG-075 | Candidate type/qualified name and Endpoint attributes.method/path; no client-side guessing of backend subject |
| AC-RKG-076 | Render backend answer once; direct/indirect and connector semantics validated server-side; client never composes facts from IDs |
| AC-RKG-077 | Stable candidate array order; explicit button submits matching root ID and ordinal with current revision/new key; original intent/locale resumed server-side |
| AC-RKG-078 | kind=greeting, safe guidance without facts/sources; provider/session/snapshot guards still apply |
| AC-RKG-079 | Backend reason-specific answer, no second insufficient paragraph; provider/disabled/timeout separate banners, draft retained |
| AC-RKG-080 | Each GET turn.response_metadata supplies limitation/coverage; missing/null/unknown version shows unknown; collapsed claims and one answer |
| AC-RKG-081 | Turn-specific zero-based citation route verifies exact evidence ID and pin; safe relative location/provenance, loading/unavailable and keyboard dialog |

Turn arrays remain paged sequence-ascending; preserve previous pages when loading
more and deduplicate by turn ID, not text. Read metadata from each stored turn,
not a flags map populated only by submit. History's current candidate list/revision
is the selection state; old clarification turns do not create live selectable
buttons. Greeting history does not clear an active pending clarification.
Capability/cache and history requests must be tied to the current backend origin
and pinned conversation; never reuse one conversation's metadata for another.

Source buttons always have a nonempty visible/accessibility label (e.g. Source 1).
Exact path/line may be shown only after the dedicated lookup returns the matched
evidence. Do not guess location from entity_id, quote or entity detail. Use
encodeURIComponent for all IDs; citation index is the ordinal within the stored
citations array, unaffected by dialog opening order. Before showing the location,
check returned conversation/turn/pin/index and evidence ID equal the requested
stored citation. A mismatch becomes unavailable, not another source.

Unknown coverage is a distinct notice, not complete/no-truncation. Even complete
within-budget metadata does not license copy such as "all functions". New-client
legacy-server mode may display old safe answers and readable source ordinals, but
must explain exact source lookup/coverage is unavailable; it cannot pretend its
old adapter has provided the new contract. Mock fixtures use identical public
schema and version/capability transitions, replacing preview-only sidecars.

New error rendering must wait for/reconcile any required history reload before
setting the banner, so reload does not clear it. Stale revision preserves the
draft and offers reload/review/retry; it does not auto-resubmit. Keyboard, focus,
safe text, touch/long-name wrapping and reduced motion inherit approved UID.
No question/answer, tokens, credentials or raw source is added to telemetry.
