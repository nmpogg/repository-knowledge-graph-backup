"""Shared OBS-RKG-001 census helpers for static fixture evaluation.

Canonical compare drops generated IDs/timestamps. Reports carry counts and
semantic names only — never absolute host paths, config values, or secrets.
"""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from rkg.adapters import AdapterContext, ParseResult
from rkg.domain import FactBatch, SourceScanConfig, validate_fact_batch
from rkg.ingestion import LocalSourcePolicy, build_manifest, resolve_local_source
from rkg.jobs.http_depends import link_static_http_depends_on

SECRET = "RKG_TEST_SECRET_DO_NOT_PERSIST"
REPO_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True, slots=True)
class CensusReport:
    fixture_id: str
    tp: int
    fn: int
    fp: int
    coverage: float | None
    precision: float | None
    by_type: dict[str, dict[str, int]]
    missing: tuple[str, ...]
    unexpected: tuple[str, ...]
    prohibited_hits: tuple[str, ...]
    secret_leaked: bool
    outcome: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "fixture_id": self.fixture_id,
            "tp": self.tp,
            "fn": self.fn,
            "fp": self.fp,
            "coverage": self.coverage,
            "precision": self.precision,
            "by_type": self.by_type,
            "missing": list(self.missing),
            "unexpected": list(self.unexpected),
            "prohibited_hits": list(self.prohibited_hits),
            "secret_leaked": self.secret_leaked,
            "outcome": self.outcome,
        }


def load_expected(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected oracle must be an object: {path.name}")
    for key in ("fixture_id", "entities", "edges"):
        if key not in payload:
            raise ValueError(f"expected oracle missing {key}: {path.name}")
    if not isinstance(payload["entities"], list) or not isinstance(
        payload["edges"], list
    ):
        raise ValueError(f"entities/edges must be lists: {path.name}")
    return payload


def fixture_root(relative: str) -> Path:
    root = REPO_ROOT / relative
    if not root.is_dir():
        raise FileNotFoundError(f"fixture repository missing: {relative}")
    return root


def run_language_pipeline(
    *,
    repository_id: str,
    root: Path,
    include_patterns: tuple[str, ...],
    ignore_patterns: tuple[str, ...] = (),
    language_factory,
    deep_factories: tuple = (),
    max_files: int = 4000,
    max_file_bytes: int = 262144,
) -> FactBatch:
    """detect → parse → extract → resolve (language), then deep adapters."""
    language = language_factory()
    config = SourceScanConfig(
        max_files, max_file_bytes, include_patterns, ignore_patterns
    )
    manifest = build_manifest(
        resolve_local_source(repository_id, root, LocalSourcePolicy((root,))),
        config,
    )
    context = AdapterContext(
        repository_id, f"snap-{repository_id}", f"job-{repository_id}", config
    )
    assert language.detect(manifest).technologies
    parsed = language.parse(manifest, config)
    extracted = language.extract(context, parsed)
    resolved = language.resolve(context, parsed, extracted.facts)
    batch = resolved.facts
    validate_fact_batch(batch)
    for factory in deep_factories:
        adapter = factory()
        detect = getattr(adapter, "detect", None)
        if detect is not None:
            detect(manifest, parsed)
        batch = adapter.extract(context, parsed, batch).facts
        validate_fact_batch(batch)
        resolve = getattr(adapter, "resolve", None)
        if resolve is not None:
            batch = resolve(context, parsed, batch).facts
            validate_fact_batch(batch)
    batch = link_static_http_depends_on(batch, job_id=context.job_id)
    validate_fact_batch(batch)
    return batch


def run_polyglot_pipeline(
    *,
    repository_id: str,
    root: Path,
    language_specs: tuple[tuple[object, tuple[str, ...]], ...],
    ignore_patterns: tuple[str, ...] = (),
    deep_factories: tuple = (),
    max_files: int = 4000,
    max_file_bytes: int = 262144,
) -> FactBatch:
    """Run multiple language adapters, merge parse/facts, then deep adapters.

    Each language_specs entry is ``(factory, include_patterns)``. Deep adapters
    receive the merged ParseResult so framework extractors can see Vue SFCs and
    TypeScript modules together (Nuxt pages + Nitro server/api).
    """
    context: AdapterContext | None = None
    merged_units: list = []
    merged_diagnostics: list = []
    batches: list[FactBatch] = []
    full_manifest = None
    for factory, include_patterns in language_specs:
        language = factory()
        config = SourceScanConfig(
            max_files, max_file_bytes, include_patterns, ignore_patterns
        )
        manifest = build_manifest(
            resolve_local_source(repository_id, root, LocalSourcePolicy((root,))),
            config,
        )
        if full_manifest is None:
            full_manifest = manifest
        if context is None:
            context = AdapterContext(
                repository_id,
                f"snap-{repository_id}",
                f"job-{repository_id}",
                config,
            )
        assert language.detect(manifest).technologies
        parsed = language.parse(manifest, config)
        extracted = language.extract(context, parsed)
        resolved = language.resolve(context, parsed, extracted.facts)
        validate_fact_batch(resolved.facts)
        batches.append(resolved.facts)
        merged_units.extend(parsed.units)
        merged_diagnostics.extend(parsed.diagnostics)
    assert context is not None
    batch = FactBatch(
        context.repository_id,
        context.snapshot_id,
        tuple(
            sorted(
                (item for part in batches for item in part.entities),
                key=lambda item: item.id,
            )
        ),
        tuple(
            sorted(
                (item for part in batches for item in part.edges),
                key=lambda item: item.id,
            )
        ),
        tuple(
            sorted(
                (item for part in batches for item in part.evidence),
                key=lambda item: item.id,
            )
        ),
        tuple(item for part in batches for item in part.diagnostics),
    )
    validate_fact_batch(batch)
    parsed = ParseResult(
        tuple(
            sorted(
                merged_units,
                key=lambda unit: (unit.relative_path, unit.representation_kind),
            )
        ),
        (),
        tuple(
            sorted(
                merged_diagnostics,
                key=lambda item: (item.relative_path or "", item.line or 0, item.code),
            )
        ),
    )
    manifest = full_manifest or build_manifest(
        resolve_local_source(repository_id, root, LocalSourcePolicy((root,))),
        context.scan_config,
    )
    for factory in deep_factories:
        adapter = factory()
        detect = getattr(adapter, "detect", None)
        if detect is not None:
            detect(manifest, parsed)
        batch = adapter.extract(context, parsed, batch).facts
        validate_fact_batch(batch)
        resolve = getattr(adapter, "resolve", None)
        if resolve is not None:
            batch = resolve(context, parsed, batch).facts
            validate_fact_batch(batch)
    batch = link_static_http_depends_on(batch, job_id=context.job_id)
    validate_fact_batch(batch)
    return batch


def _attr_map(item: Any) -> dict[str, Any]:
    if isinstance(item, dict):
        attrs = item.get("attributes") or {}
        if isinstance(attrs, dict):
            return dict(attrs)
        if isinstance(attrs, list):
            return {str(k): v for k, v in attrs}
        return {}
    return dict(getattr(item, "attributes", ()) or ())


def _entity_key(item: dict[str, Any]) -> str:
    attrs = _attr_map(item)
    required = item.get("required_attributes") or {}
    if isinstance(required, dict):
        for key, value in required.items():
            attrs.setdefault(key, value)
    # Navigation routes (OQ-RKG-007): identity is path + kind, not HTTP method.
    path = attrs.get("path") or attrs.get("route_path")
    kind = attrs.get("kind")
    method = attrs.get("method")
    parts = [
        str(item.get("type") or item.get("semantic_kind") or ""),
        str(item.get("qualified_name") or ""),
    ]
    if kind:
        parts.append(f"kind={kind}")
    if path is not None:
        parts.append(f"path={path}")
    if method:
        parts.append(f"method={method}")
    for key in sorted(required):
        if key in {"kind", "path", "route_path", "method"}:
            continue
        parts.append(f"{key}={required[key]}")
    return "|".join(parts)


def _edge_key(item: dict[str, Any]) -> str:
    rule = item.get("rule_id")
    return "|".join(
        [
            str(item.get("type") or ""),
            str(item.get("source") or item.get("source_qualified_name") or ""),
            str(item.get("target") or item.get("target_qualified_name") or ""),
            "" if rule is None else str(rule),
        ]
    )


def _fact_label(kind: str, key: str) -> str:
    return f"{kind}:{key}"


def canonicalize_batch(batch: FactBatch) -> dict[str, list[dict[str, Any]]]:
    by_id = {item.id: item for item in batch.entities}
    evidence_by_id = {item.id: item for item in batch.evidence}
    entities: list[dict[str, Any]] = []
    attr_keys = (
        "kind",
        "path",
        "route_path",
        "method",
        "channel_kind",
        "name",
        "namespace",
        "origin",
    )
    for item in batch.entities:
        attrs = dict(item.attributes)
        entity_type = (
            item.type.value if hasattr(item.type, "value") else str(item.type)
        )
        entities.append(
            {
                "type": entity_type,
                "qualified_name": item.qualified_name,
                "language_kind": item.language_kind,
                "framework_kind": item.framework_kind,
                "attributes": attrs,
                "required_attributes": {
                    key: attrs[key] for key in attr_keys if key in attrs
                },
                "evidence": [
                    {
                        "file_path": item.file_path,
                        "start_line": item.start_line,
                    }
                ]
                if item.file_path
                else [],
            }
        )
    edges: list[dict[str, Any]] = []
    for edge in batch.edges:
        source = by_id.get(edge.source_id)
        target = by_id.get(edge.target_id)
        if source is None or target is None:
            continue
        ev = []
        for evidence_id in edge.evidence_ids:
            loc = evidence_by_id.get(evidence_id)
            if loc is None:
                continue
            ev.append(
                {
                    "file_path": loc.file_path,
                    "start_line": loc.start_line,
                    "rule_id": loc.rule,
                }
            )
        edge_type = (
            edge.type.value if hasattr(edge.type, "value") else str(edge.type)
        )
        edges.append(
            {
                "type": edge_type,
                "source": source.qualified_name,
                "target": target.qualified_name,
                "rule_id": edge.rule or None,
                "evidence": ev,
            }
        )
    entities.sort(key=_entity_key)
    edges.sort(key=_edge_key)
    return {"entities": entities, "edges": edges}


def _match_entity(expected: dict[str, Any], actual: dict[str, Any]) -> bool:
    exp_type = expected.get("type") or expected.get("semantic_kind")
    act_type = actual.get("type") or actual.get("semantic_kind")
    exp_attrs = _attr_map(expected)
    act_attrs = _attr_map(actual)
    # Navigation Endpoint match (OQ-RKG-007 resolved: kind=navigation).
    if exp_type in {"navigation_route", "NavigationRoute"} or exp_attrs.get(
        "kind"
    ) == "navigation":
        path = exp_attrs.get("path") or exp_attrs.get("route_path") or expected.get(
            "qualified_name"
        )
        act_path = act_attrs.get("path") or act_attrs.get("route_path")
        is_nav = (
            act_attrs.get("kind") == "navigation"
            or actual.get("framework_kind")
            in {"react-router", "nuxt", "vue-router"}
        )
        if not is_nav:
            return False
        path_ok = (path and act_path == path) or (
            actual.get("qualified_name") == expected.get("qualified_name")
        )
        if not path_ok:
            return False
        required = expected.get("required_attributes") or {}
        if isinstance(required, dict):
            for key, value in required.items():
                if act_attrs.get(key) != value:
                    return False
        return True
    if exp_type and act_type and exp_type != act_type:
        return False
    if expected.get("qualified_name") != actual.get("qualified_name"):
        return False
    required = expected.get("required_attributes") or {}
    if isinstance(required, dict):
        for key, value in required.items():
            if act_attrs.get(key) != value:
                return False
    return True


def _match_edge(expected: dict[str, Any], actual: dict[str, Any]) -> bool:
    if expected.get("type") != actual.get("type"):
        return False
    if (expected.get("source") or expected.get("source_qualified_name")) != (
        actual.get("source") or actual.get("source_qualified_name")
    ):
        return False
    if (expected.get("target") or expected.get("target_qualified_name")) != (
        actual.get("target") or actual.get("target_qualified_name")
    ):
        return False
    exp_rule = expected.get("rule_id")
    if exp_rule is not None and actual.get("rule_id") != exp_rule:
        return False
    return True


def _in_allowlist(
    kind: str, actual: dict[str, Any], allowlist: list[dict[str, Any]]
) -> bool:
    for item in allowlist:
        if item.get("fact_kind") not in {None, kind}:
            continue
        body = item.get("entity") if kind == "entity" else item.get("edge")
        if body is None and "type" in item:
            body = item
        if body is None:
            continue
        if kind == "entity" and _match_entity(body, actual):
            return True
        if kind == "edge" and _match_edge(body, actual):
            return True
    return False


def _prohibited_hit(
    batch: FactBatch, canonical: dict[str, list[dict[str, Any]]], rule: dict[str, Any]
) -> str | None:
    reason = str(rule.get("reason") or "prohibited")
    if "text_must_not_contain" in rule:
        needle = str(rule["text_must_not_contain"])
        blob = json.dumps(asdict(batch), default=str)
        if needle in blob:
            return reason
        return None
    entity_pat = rule.get("entity")
    if isinstance(entity_pat, dict):
        for item in canonical["entities"]:
            if entity_pat.get("type") and item.get("type") != entity_pat.get("type"):
                continue
            qn = entity_pat.get("qualified_name")
            if qn and item.get("qualified_name") == qn:
                return reason
            contains = entity_pat.get("qualified_name_contains")
            if contains and contains in str(item.get("qualified_name") or ""):
                return reason
            attrs = _attr_map(entity_pat)
            act = _attr_map(item)
            if attrs and all(act.get(k) == v for k, v in attrs.items()):
                return reason
    edge_pat = rule.get("edge")
    if isinstance(edge_pat, dict):
        for item in canonical["edges"]:
            if edge_pat.get("type") and item.get("type") != edge_pat.get("type"):
                continue
            src_c = edge_pat.get("source_qualified_name_contains")
            tgt_c = edge_pat.get("target_qualified_name_contains")
            src = str(item.get("source") or "")
            tgt = str(item.get("target") or "")
            if src_c and src_c not in src:
                continue
            if tgt_c and tgt_c not in tgt:
                continue
            if edge_pat.get("source") and edge_pat.get("source") != item.get("source"):
                continue
            if edge_pat.get("target") and edge_pat.get("target") != item.get("target"):
                continue
            if src_c or tgt_c or edge_pat.get("source") or edge_pat.get("target"):
                return reason
    return None


def compare_census(expected: dict[str, Any], batch: FactBatch) -> CensusReport:
    fixture_id = str(expected["fixture_id"])
    canonical = canonicalize_batch(batch)
    allowlist = list(expected.get("allowlist") or [])
    exp_entities = list(expected.get("entities") or [])
    exp_edges = list(expected.get("edges") or [])

    matched_entity_keys: set[str] = set()
    matched_edge_keys: set[str] = set()
    used_actual_entities: set[int] = set()
    used_actual_edges: set[int] = set()

    for exp in exp_entities:
        for index, act in enumerate(canonical["entities"]):
            if index in used_actual_entities:
                continue
            if _match_entity(exp, act):
                matched_entity_keys.add(_entity_key(exp))
                used_actual_entities.add(index)
                break
    for exp in exp_edges:
        for index, act in enumerate(canonical["edges"]):
            if index in used_actual_edges:
                continue
            if _match_edge(exp, act):
                matched_edge_keys.add(_edge_key(exp))
                used_actual_edges.add(index)
                break

    missing = [
        _fact_label("entity", _entity_key(item))
        for item in exp_entities
        if _entity_key(item) not in matched_entity_keys
    ] + [
        _fact_label("edge", _edge_key(item))
        for item in exp_edges
        if _edge_key(item) not in matched_edge_keys
    ]

    allow_unlisted = bool(
        (expected.get("match_policy") or {}).get("allow_unlisted_actual")
    )
    unexpected: list[str] = []
    if not allow_unlisted:
        for index, act in enumerate(canonical["entities"]):
            if index in used_actual_entities:
                continue
            if _in_allowlist("entity", act, allowlist):
                continue
            unexpected.append(_fact_label("entity", _entity_key(act)))
        for index, act in enumerate(canonical["edges"]):
            if index in used_actual_edges:
                continue
            if _in_allowlist("edge", act, allowlist):
                continue
            unexpected.append(_fact_label("edge", _edge_key(act)))

    prohibited_hits = []
    for rule in expected.get("prohibited") or []:
        if not isinstance(rule, dict):
            continue
        hit = _prohibited_hit(batch, canonical, rule)
        if hit:
            prohibited_hits.append(hit)

    blob = json.dumps(
        {
            "entities": [asdict(item) for item in batch.entities],
            "edges": [asdict(item) for item in batch.edges],
            "evidence": [asdict(item) for item in batch.evidence],
            "diagnostics": [asdict(item) for item in batch.diagnostics],
        },
        default=str,
    )
    secret_leaked = SECRET in blob

    tp = len(matched_entity_keys) + len(matched_edge_keys)
    fn = len(missing)
    fp = len(unexpected) + len(prohibited_hits) + (1 if secret_leaked else 0)
    coverage = (tp / (tp + fn)) if (tp + fn) else None
    precision = (tp / (tp + fp)) if (tp + fp) else None

    type_counter: Counter[str] = Counter()
    type_tp: Counter[str] = Counter()
    type_fn: Counter[str] = Counter()
    for item in exp_entities:
        key = str(item.get("type") or item.get("semantic_kind") or "entity")
        type_counter[key] += 1
        if _entity_key(item) in matched_entity_keys:
            type_tp[key] += 1
        else:
            type_fn[key] += 1
    for item in exp_edges:
        key = str(item.get("type") or "edge")
        type_counter[key] += 1
        if _edge_key(item) in matched_edge_keys:
            type_tp[key] += 1
        else:
            type_fn[key] += 1
    by_type = {
        name: {
            "expected": type_counter[name],
            "tp": type_tp[name],
            "fn": type_fn[name],
        }
        for name in sorted(type_counter)
    }

    outcome = "pass" if fn == 0 and fp == 0 and not secret_leaked else "fail"
    return CensusReport(
        fixture_id=fixture_id,
        tp=tp,
        fn=fn,
        fp=fp,
        coverage=coverage,
        precision=precision,
        by_type=by_type,
        missing=tuple(missing),
        unexpected=tuple(unexpected),
        prohibited_hits=tuple(prohibited_hits),
        secret_leaked=secret_leaked,
        outcome=outcome,
    )


def format_report(report: CensusReport) -> str:
    """Human-readable census summary without host paths or secret values."""
    lines = [
        f"fixture={report.fixture_id}",
        f"outcome={report.outcome}",
        f"tp={report.tp} fn={report.fn} fp={report.fp}",
        f"coverage={report.coverage}",
        f"precision={report.precision}",
        "by_type=" + json.dumps(report.by_type, sort_keys=True),
    ]
    if report.missing:
        lines.append("missing=" + ";".join(report.missing[:40]))
    if report.unexpected:
        lines.append("unexpected=" + ";".join(report.unexpected[:40]))
    if report.prohibited_hits:
        lines.append("prohibited=" + ";".join(report.prohibited_hits))
    if report.secret_leaked:
        lines.append("secret_leaked=true")
    return "\n".join(lines)
