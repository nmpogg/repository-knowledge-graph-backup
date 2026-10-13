"""Static Nuxt framework extraction over Vue + TypeScript base facts.

UI pages reuse Endpoint with framework_kind=nuxt and kind=navigation
(OQ-RKG-007). Nitro server/api file routes emit HTTP Endpoints with method+path
and handled_by when a unique handler Callable exists in base facts. Auto-import
edges are convention-backed only when the simple name resolves uniquely.
Analyzed modules are never imported or executed.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import PurePosixPath
from urllib.parse import urlsplit

from tree_sitter import Node

from rkg.adapters.contracts import (
    CONTRACT_VERSION,
    AdapterContext,
    AdapterDescriptor,
    AdapterDiagnostic,
    AdapterKind,
    AdapterResult,
    Capability,
    DetectionEvidence,
    DetectionReport,
    ParseResult,
    SupportState,
    TechnologyConstraint,
    TechnologyDetection,
)
from rkg.adapters.route_flow import route_flow_attrs
from rkg.adapters.typescript_parse import (
    TsModule,
    child_named,
    identifier_name,
    named_children,
    string_literal,
    text_of,
    walk_named,
)
from rkg.adapters.vue_parse import VueSfc
from rkg.domain import (
    Diagnostic,
    Edge,
    EdgeType,
    Entity,
    EntityType,
    Evidence,
    FactBatch,
    Severity,
    configuration_id,
    diagnostic_id,
    edge_id,
    endpoint_id,
    evidence_id,
    source_entity_id,
)
from rkg.ingestion import SourceManifest

DETECT_RULE = "RKG.nuxt.detect.v1"
NAV_RULE = "RKG.nuxt.navigation.v1"
ROUTE_RULE = "RKG.nuxt.route.v1"
HANDLER_RULE = "RKG.nuxt.handler.v1"
PAGE_HANDLER_RULE = "RKG.nuxt.page_handler.v1"
AUTO_IMPORT_RULE = "RKG.nuxt.auto_import.v1"
CONFIG_RULE = "RKG.nuxt.runtime_config.v1"
HTTP_RULE = "RKG.nuxt.http_origin.v1"

_NUXT_HTTP_CALLEES = frozenset({"$fetch", "useFetch"})
_HTTP_METHODS = frozenset({"GET", "PUT", "POST", "PATCH", "DELETE", "HEAD", "OPTIONS"})

_MESSAGES = {
    "nuxt_route_dynamic": (
        "Nuxt page or API route path is not a unique static convention."
    ),
    "nuxt_handler_unresolved": "Nitro handler could not be resolved uniquely.",
    "nuxt_auto_import_ambiguous": "Auto-import simple name is ambiguous.",
    "nuxt_config_unresolved": "runtimeConfig key could not be resolved statically.",
}

_METHOD_SUFFIX = re.compile(
    r"\.(get|post|put|patch|delete|head|options)\.(ts|js|mjs)$", re.IGNORECASE
)
_HTTP_ORIGIN = re.compile(r"^https?://[^/\s]+", re.IGNORECASE)
_TAG = re.compile(r"</?([A-Z][A-Za-z0-9]*)\b")

_FRAMEWORK_NAMES = frozenset(
    {
        "definePageMeta",
        "defineNuxtConfig",
        "defineNuxtPlugin",
        "defineNuxtRouteMiddleware",
        "defineEventHandler",
        "defineComponent",
        "defineProps",
        "defineEmits",
        "defineExpose",
        "defineModel",
        "withDefaults",
        "useRoute",
        "useRouter",
        "useFetch",
        "useAsyncData",
        "useLazyFetch",
        "useLazyAsyncData",
        "useRuntimeConfig",
        "useHead",
        "useSeoMeta",
        "useState",
        "useCookie",
        "useRequestURL",
        "navigateTo",
        "computed",
        "ref",
        "reactive",
        "watch",
        "watchEffect",
        "onMounted",
        "onUnmounted",
        "onBeforeMount",
        "onBeforeUnmount",
        "onServerPrefetch",
        "nextTick",
        "toRef",
        "toRefs",
        "shallowRef",
        "NuxtLink",
        "NuxtPage",
        "NuxtLayout",
        "NuxtLoadingIndicator",
        "ClientOnly",
        "Teleport",
        "Suspense",
        "KeepAlive",
        "Transition",
        "TransitionGroup",
    }
)


@dataclass(frozen=True, slots=True)
class _Location:
    path: str
    line: int


def _posix(path: str) -> PurePosixPath:
    return PurePosixPath(path.replace("\\", "/"))


def _pages_segments(path: str) -> list[str] | None:
    parts = list(_posix(path).parts)
    if "pages" not in parts or not path.endswith(".vue"):
        return None
    index = parts.index("pages")
    if index == 0:
        rest = parts[1:]
    elif index == 1 and parts[0] == "app":
        rest = parts[2:]
    else:
        return None
    if not rest:
        return None
    return rest


def _segment_token(name: str) -> str | None:
    if name.startswith("(") and name.endswith(")"):
        return None
    if name.startswith("[") and name.endswith("]"):
        inner = name[1:-1]
        if inner.startswith("..."):
            return "*"
        if not inner or any(ch in inner for ch in "${}"):
            return None
        return f":{inner}"
    if not name or any(ch in name for ch in "${}"):
        return None
    return name


def page_file_to_route(path: str) -> str | None:
    """Map app/pages or pages file path to a UI navigation route."""
    rest = _pages_segments(path)
    if rest is None:
        return None
    segments: list[str] = []
    for ordinal, part in enumerate(rest):
        name = part[:-4] if part.endswith(".vue") else part
        if name == "index" and ordinal == len(rest) - 1:
            continue
        token = _segment_token(name)
        if token is None and name.startswith("["):
            return None
        if token is None:
            continue
        segments.append(token)
    return "/" + "/".join(segments) if segments else "/"


def api_file_to_endpoint(path: str) -> tuple[str, str] | None:
    """Map server/api/*.method.ts convention to HTTP method + path."""
    parts = list(_posix(path).parts)
    if len(parts) < 3 or parts[0] != "server" or parts[1] != "api":
        return None
    match = _METHOD_SUFFIX.search(parts[-1])
    if match is None:
        return None
    method = match.group(1).upper()
    rest = list(parts[2:])
    stem = _METHOD_SUFFIX.sub("", rest[-1])
    rest[-1] = stem
    segments: list[str] = []
    for ordinal, part in enumerate(rest):
        if part == "index" and ordinal == len(rest) - 1:
            continue
        token = _segment_token(part)
        if token is None and part.startswith("["):
            return None
        if token is None:
            continue
        segments.append(token)
    route = "/api" + (("/" + "/".join(segments)) if segments else "")
    return method, route


def _module_qn(path: str) -> str:
    return ".".join(_posix(path).with_suffix("").parts)


def _origin(url: str) -> str | None:
    if not _HTTP_ORIGIN.match(url):
        return None
    try:
        parsed = urlsplit(url)
    except ValueError:
        return None
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return None
    return f"{parsed.scheme}://{parsed.netloc}"


def _object_props(source: bytes, node: Node) -> dict[str, Node]:
    props: dict[str, Node] = {}
    if node.type != "object":
        return props
    for child in named_children(node):
        if child.type != "pair":
            continue
        key_node = child_named(child, "key")
        value = child_named(child, "value")
        if key_node is None or value is None:
            continue
        key = identifier_name(source, key_node) or string_literal(source, key_node)
        if key:
            props[key] = value
    return props


def _bound_object(module: TsModule, name: str) -> Node | None:
    matches: list[Node] = []
    for node in named_children(module.tree.root_node):
        stmt = node
        if node.type == "export_statement":
            decl = child_named(node, "declaration")
            if decl is None:
                continue
            stmt = decl
        if stmt.type not in {"lexical_declaration", "variable_declaration"}:
            continue
        for declarator in named_children(stmt):
            if declarator.type != "variable_declarator":
                continue
            bound = identifier_name(module.source, child_named(declarator, "name"))
            value = child_named(declarator, "value")
            if bound == name and value is not None and value.type == "object":
                matches.append(value)
    return matches[0] if len(matches) == 1 else None


def _runtime_keys(module: TsModule) -> list[tuple[str, str, int]]:
    """Return (qualified_key, boundary, line) for static runtimeConfig keys."""
    found: list[tuple[str, str, int]] = []

    def collect(object_node: Node, prefix: str, boundary: str) -> None:
        for key, value in _object_props(module.source, object_node).items():
            line = value.start_point[0] + 1
            qualified = f"{prefix}.{key}" if prefix else key
            if key == "public" and value.type == "object":
                collect(value, "public", "public")
                continue
            if value.type == "object":
                # Nested non-public objects are not flattened beyond one public level.
                continue
            found.append((qualified, boundary, line))

    for node in walk_named(module.tree.root_node):
        if node.type != "pair":
            continue
        key_node = child_named(node, "key")
        value = child_named(node, "value")
        key = identifier_name(module.source, key_node) or string_literal(
            module.source, key_node
        )
        if key != "runtimeConfig" or value is None:
            continue
        target = value
        if value.type == "identifier":
            bound = _bound_object(module, text_of(module.source, value))
            if bound is None:
                continue
            target = bound
        if target.type != "object":
            continue
        collect(target, "", "server")
    return found


def _unwrap_expr(node: Node | None) -> Node | None:
    current = node
    while current is not None and current.type in {
        "as_expression",
        "type_assertion",
        "parenthesized_expression",
        "non_null_expression",
        "satisfies_expression",
    }:
        inner = child_named(current, "expression") or next(
            (child for child in named_children(current) if child.is_named), None
        )
        if inner is None or inner == current:
            break
        current = inner
    return current


def _call_args(node: Node) -> list[Node]:
    args = child_named(node, "arguments")
    if args is None:
        return []
    return [child for child in named_children(args)]


def _fetch_method_literal(source: bytes, call: Node) -> str | None:
    """Literal method on $fetch(url, { method: 'POST' }) / useFetch options."""
    args = _call_args(call)
    if len(args) < 2:
        return None
    options = _unwrap_expr(args[1])
    if options is None or options.type != "object":
        return None
    for child in named_children(options):
        if child.type != "pair":
            continue
        key = child_named(child, "key")
        value = child_named(child, "value")
        key_name = identifier_name(source, key) or string_literal(source, key)
        if key_name != "method" or value is None:
            continue
        literal = string_literal(source, _unwrap_expr(value))
        if literal is None:
            return None
        method = literal.strip().upper()
        return method if method in _HTTP_METHODS else None
    return None


def _relative_http_path(literal: str) -> str | None:
    """Static relative request path; absolute origins stay on ExternalDependency."""
    if not literal or any(ch.isspace() for ch in literal):
        return None
    if "${" in literal or "://" in literal:
        return None
    if _HTTP_ORIGIN.match(literal):
        return None
    return literal


def _call_type_arg_text(source: bytes, call: Node) -> str | None:
    for child in named_children(call):
        if child.type != "type_arguments":
            continue
        raw = text_of(source, child).strip()
        if raw.startswith("<") and raw.endswith(">"):
            raw = raw[1:-1].strip()
        if not raw or len(raw) > 80:
            return None
        if any(token in raw for token in ("=>", "{", "extends", "infer", "?", ":")):
            return None
        return raw
    return None


def _is_locally_bound(source: bytes, call: Node, name: str) -> bool:
    """True when `name` is a local lexical/param binding shadowing the Nuxt helper."""
    current: Node | None = call.parent
    while current is not None:
        if current.type in {
            "function_declaration",
            "generator_function_declaration",
            "arrow_function",
            "function_expression",
            "method_definition",
        }:
            params = (
                child_named(current, "parameters")
                or child_named(current, "formal_parameters")
                or child_named(current, "parameter")
            )
            if params is not None:
                for param in walk_named(params):
                    if param.type in {
                        "required_parameter",
                        "optional_parameter",
                        "identifier",
                    }:
                        bound = identifier_name(
                            source, child_named(param, "pattern") or param
                        )
                        if bound == name:
                            return True
            body = child_named(current, "body")
            if body is not None:
                for stmt in named_children(body):
                    if stmt.start_byte >= call.start_byte:
                        break
                    if stmt.type not in {
                        "lexical_declaration",
                        "variable_declaration",
                        "function_declaration",
                    }:
                        continue
                    for node in walk_named(stmt):
                        if node.type == "variable_declarator":
                            bound = identifier_name(source, child_named(node, "name"))
                            if bound == name:
                                return True
                        if node.type in {
                            "function_declaration",
                            "generator_function_declaration",
                        }:
                            bound = identifier_name(source, child_named(node, "name"))
                            if bound == name:
                                return True
        current = current.parent
    return False


def _params_defaulting_to_fetch(source: bytes, func: Node) -> set[str]:
    """Parameter names whose default expression is the Nuxt `$fetch` helper."""
    names: set[str] = set()
    params = (
        child_named(func, "parameters")
        or child_named(func, "formal_parameters")
        or next(
            (
                child
                for child in named_children(func)
                if child.type in {"formal_parameters", "parameters"}
            ),
            None,
        )
    )
    if params is None:
        return names
    for param in named_children(params):
        if param.type not in {"required_parameter", "optional_parameter"}:
            continue
        pattern = child_named(param, "pattern") or child_named(param, "name")
        value = child_named(param, "value")
        bound = identifier_name(source, pattern)
        if bound is None or value is None:
            continue
        default = _unwrap_expr(value)
        if (
            default is not None
            and default.type == "identifier"
            and text_of(source, default) == "$fetch"
        ):
            names.add(bound)
    return names


def _callee_identifier(source: bytes, callee: Node | None) -> str | None:
    """Identifier for a call callee, unwrapping await/type-assertion wrappers."""
    node = _unwrap_expr(callee)
    if node is not None and node.type == "await_expression":
        node = _unwrap_expr(
            child_named(node, "argument")
            or child_named(node, "expression")
            or next(
                (child for child in named_children(node) if child.is_named),
                None,
            )
        )
    return identifier_name(source, node)


def _annotate_http_request(
    entities: dict[str, Entity],
    caller: Entity,
    *,
    method: str,
    path: str | None,
    response_type: str | None,
) -> None:
    current = entities.get(caller.id, caller)
    attrs = dict(current.attributes)
    request = f"{method} {path}" if path else method
    existing = attrs.get("http_requests")
    if isinstance(existing, str) and existing.strip():
        parts = [part.strip() for part in existing.split("|") if part.strip()]
        if request not in parts:
            parts.append(request)
        attrs["http_requests"] = " | ".join(parts)
    else:
        attrs["http_requests"] = request
    if response_type:
        existing_resp = attrs.get("http_response_types")
        if isinstance(existing_resp, str) and existing_resp.strip():
            resp_parts = [
                part.strip() for part in existing_resp.split("|") if part.strip()
            ]
            if response_type not in resp_parts:
                resp_parts.append(response_type)
            attrs["http_response_types"] = " | ".join(resp_parts)
        else:
            attrs["http_response_types"] = response_type
    entities[caller.id] = Entity(
        current.id,
        current.repository_id,
        current.snapshot_id,
        current.type,
        current.name,
        current.qualified_name,
        current.file_path,
        current.start_line,
        current.end_line,
        current.language_kind,
        current.framework_kind,
        tuple(attrs.items()),
    )


def _owners_for_line(entities: dict[str, Entity], path: str, line: int) -> list[Entity]:
    owners = [
        item
        for item in entities.values()
        if item.type == EntityType.CALLABLE
        and item.file_path
        and item.file_path.replace("\\", "/") == path
        and item.start_line
        and item.end_line
        and item.start_line <= line <= item.end_line
    ]
    if not owners:
        return []
    # Prefer the innermost (most specific) callable by span size.
    owners.sort(
        key=lambda item: (
            (item.end_line or 0) - (item.start_line or 0),
            item.qualified_name,
        )
    )
    return owners


def _static_request_from_call(
    source: bytes, call: Node
) -> tuple[str, str | None, str | None] | None:
    """Return (method, path|None, response_type|None) for a Nuxt HTTP call."""
    args = _call_args(call)
    if not args:
        return None
    first = _unwrap_expr(args[0])
    if first is None:
        return None
    # Dynamic URL factory / template — method may still be known; never invent path.
    path: str | None = None
    if first.type in {"arrow_function", "function_expression", "function_declaration"}:
        path = None
    elif first.type == "template_string" and any(
        child.type == "template_substitution" for child in first.children
    ):
        path = None
    else:
        literal = string_literal(source, first)
        if literal is not None:
            path = _relative_http_path(literal)
        else:
            return None
    method = _fetch_method_literal(source, call) or "GET"
    response_type = _call_type_arg_text(source, call)
    return method, path, response_type


def _index_nuxt_http_in_tree(
    *,
    path: str,
    source: bytes,
    root: Node,
    entities: dict[str, Entity],
) -> None:
    """Annotate http_requests for literal $fetch / useFetch / default-$fetch params."""
    if path.startswith("analysis-cases/"):
        return
    fetch_aliases: dict[str, set[str]] = {}
    for node in walk_named(root):
        if node.type in {
            "function_declaration",
            "generator_function_declaration",
            "function_expression",
            "arrow_function",
            "method_definition",
        }:
            aliases = _params_defaulting_to_fetch(source, node)
            if aliases:
                fetch_aliases[f"{node.start_byte}:{node.end_byte}"] = aliases

    for node in walk_named(root):
        if node.type != "call_expression":
            continue
        callee = child_named(node, "function")
        name = _callee_identifier(source, callee)
        if name is None:
            continue
        is_nuxt_helper = name in _NUXT_HTTP_CALLEES
        is_fetch_param = False
        if not is_nuxt_helper:
            # Parameter defaulting to $fetch (e.g. useOrders(fetcher = $fetch)).
            current: Node | None = node.parent
            while current is not None:
                key = f"{current.start_byte}:{current.end_byte}"
                if name in fetch_aliases.get(key, set()):
                    is_fetch_param = True
                    break
                current = current.parent
            if not is_fetch_param:
                continue
        if is_nuxt_helper and _is_locally_bound(source, node, name):
            continue
        parsed = _static_request_from_call(source, node)
        if parsed is None:
            continue
        method, req_path, response_type = parsed
        line = node.start_point[0] + 1
        owners = _owners_for_line(entities, path, line)
        if len(owners) < 1:
            continue
        _annotate_http_request(
            entities,
            owners[0],
            method=method,
            path=req_path,
            response_type=response_type,
        )
        current = entities[owners[0].id]
        attrs = dict(current.attributes)
        if is_fetch_param:
            attrs["http_default_fetcher"] = "$fetch"
        inner = node.parent
        while inner is not None and inner.start_point[0] + 1 >= current.start_line:
            if inner.type in {"function_declaration", "function_expression"}:
                inner_name = identifier_name(source, child_named(inner, "name"))
                if inner_name and inner_name != current.name:
                    nested = json.loads(attrs.get("nested_http_requests") or "{}")
                    nested[inner_name] = f"{method} {req_path}" if req_path else method
                    attrs["nested_http_requests"] = json.dumps(nested, sort_keys=True)
                    break
            inner = inner.parent
        entities[current.id] = Entity(
            current.id,
            current.repository_id,
            current.snapshot_id,
            current.type,
            current.name,
            current.qualified_name,
            current.file_path,
            current.start_line,
            current.end_line,
            current.language_kind,
            current.framework_kind,
            tuple(attrs.items()),
        )


def _page_source_unit(entities: dict[str, Entity], path: str) -> Entity | None:
    matches = [
        item
        for item in entities.values()
        if item.type == EntityType.SOURCE_UNIT
        and item.file_path
        and item.file_path.replace("\\", "/") == path
    ]
    return matches[0] if len(matches) == 1 else None


def _ensure_page_handler(
    context: AdapterContext,
    entities: dict[str, Entity],
    edges: dict[str, Edge],
    source: Entity,
    path: str,
) -> Entity:
    """Script-setup pages are SourceUnits; schema requires handled_by → Callable."""
    handler_qn = f"{source.qualified_name}.setup"
    existing = [
        item
        for item in entities.values()
        if item.type == EntityType.CALLABLE and item.qualified_name == handler_qn
    ]
    if len(existing) == 1:
        handler = existing[0]
    else:
        handler_id = source_entity_id(
            context.repository_id,
            path,
            EntityType.CALLABLE,
            handler_qn,
        )
        handler = Entity(
            handler_id,
            context.repository_id,
            context.snapshot_id,
            EntityType.CALLABLE,
            "setup",
            handler_qn,
            path,
            source.start_line or 1,
            source.end_line or 1,
            language_kind="vue",
            framework_kind="nuxt",
            attributes=(("kind", "page_setup"),),
        )
        entities[handler_id] = handler
    # Mirror page SourceUnit depends_on onto the setup Callable for UI→API walk.
    for edge in list(edges.values()):
        if edge.type != EdgeType.DEPENDS_ON or edge.source_id != source.id:
            continue
        key = edge_id(
            context.snapshot_id, EdgeType.DEPENDS_ON, handler.id, edge.target_id
        )
        if key in edges:
            continue
        edges[key] = Edge(
            key,
            context.snapshot_id,
            EdgeType.DEPENDS_ON,
            handler.id,
            edge.target_id,
            edge.rule,
            edge.evidence_ids,
        )
    return handler


class NuxtFrameworkAdapter:
    """Extract Nuxt pages, Nitro routes, auto-imports and runtimeConfig keys."""

    entrypoint_required = False
    allow_unverified_versions = True
    reviewed_deep_support = False

    descriptor = AdapterDescriptor(
        adapter_id="rkg.nuxt",
        adapter_version="0.1.0",
        contract_version=CONTRACT_VERSION,
        kind=AdapterKind.FRAMEWORK,
        language="vue",
        framework="nuxt",
        grammar_or_target="Nuxt pages + Nitro server/api conventions",
        file_patterns=(
            "*.vue",
            "**/*.vue",
            "nuxt.config.ts",
            "nuxt.config.js",
            "server/api/**/*.ts",
        ),
        ignore_patterns=(
            "**/node_modules/**",
            "**/.nuxt/**",
            "**/.output/**",
            "**/dist/**",
            "**/coverage/**",
        ),
        capabilities=("app", "routes"),
        technology_constraints=(TechnologyConstraint("nuxt", ">=3.0,<5.0"),),
    )

    def technology_detectors(self) -> tuple[object, ...]:
        from rkg.detection.nuxt import NuxtDetector

        return (NuxtDetector(),)

    def detect(self, manifest: SourceManifest, parsed: ParseResult) -> DetectionReport:
        del parsed
        evidence: list[DetectionEvidence] = []
        version: str | None = None
        for item in manifest.files:
            path = item.relative_path.replace("\\", "/")
            name = PurePosixPath(path).name
            if name in {"nuxt.config.ts", "nuxt.config.js", "nuxt.config.mjs"}:
                evidence.append(DetectionEvidence(path, DETECT_RULE))
            if _pages_segments(path) is not None:
                evidence.append(DetectionEvidence(path, DETECT_RULE))
            if path.startswith("server/api/") and _METHOD_SUFFIX.search(path):
                evidence.append(DetectionEvidence(path, DETECT_RULE))
            if name == "package.json":
                try:
                    data = json.loads(item.content.decode("utf-8"))
                except (UnicodeError, json.JSONDecodeError, ValueError):
                    continue
                for section in ("dependencies", "devDependencies"):
                    block = data.get(section) or {}
                    if not isinstance(block, dict) or "nuxt" not in block:
                        continue
                    evidence.append(DetectionEvidence(path, DETECT_RULE))
                    raw = block.get("nuxt")
                    if isinstance(raw, str) and raw:
                        version = raw.lstrip("^~>=<")
        if not evidence:
            return DetectionReport()
        unique = tuple(
            DetectionEvidence(path, rule)
            for path, rule in sorted(
                {(item.relative_path, item.rule_id) for item in evidence}
            )
        )
        return DetectionReport((TechnologyDetection("nuxt", version, unique),))

    def extract(
        self, context: AdapterContext, parsed: ParseResult, base: FactBatch
    ) -> AdapterResult:
        vue_modules = {
            unit.relative_path.replace("\\", "/"): unit.representation
            for unit in parsed.units
            if isinstance(unit.representation, VueSfc)
        }
        ts_modules = {
            unit.relative_path.replace("\\", "/"): unit.representation
            for unit in parsed.units
            if isinstance(unit.representation, TsModule)
        }
        entities = {item.id: item for item in base.entities}
        edges = {item.id: item for item in base.edges}
        evidence = {item.id: item for item in base.evidence}
        diagnostics = list(base.diagnostics)
        issues: list[AdapterDiagnostic] = []

        def emit_edge(
            kind: EdgeType,
            source: str,
            target: str,
            location: _Location,
            rule: str,
        ) -> None:
            ref = evidence_id(
                context.snapshot_id,
                location.path,
                location.line,
                location.line,
                rule,
            )
            evidence[ref] = Evidence(
                ref,
                context.snapshot_id,
                location.path,
                location.line,
                location.line,
                rule,
            )
            key = edge_id(context.snapshot_id, kind, source, target)
            current = edges.get(key)
            references = set(current.evidence_ids) if current else set()
            references.add(ref)
            edges[key] = Edge(
                key,
                context.snapshot_id,
                kind,
                source,
                target,
                rule,
                tuple(sorted(references)),
            )

        # --- UI navigation from pages convention ---
        page_paths = sorted(
            {
                path
                for path in list(vue_modules)
                + [
                    item.file_path.replace("\\", "/")
                    for item in entities.values()
                    if item.type == EntityType.SOURCE_UNIT
                    and item.file_path
                    and item.file_path.endswith(".vue")
                ]
                if _pages_segments(path) is not None
            }
        )
        for path in page_paths:
            route = page_file_to_route(path)
            line = 1
            if route is None:
                issues.append(AdapterDiagnostic("nuxt_route_dynamic", path, line))
                continue
            chain = (f"page:{path}:{route}",)
            identifier = endpoint_id(
                context.repository_id,
                path,
                "navigation",
                "",
                route,
                chain,
            )
            entities[identifier] = Entity(
                identifier,
                context.repository_id,
                context.snapshot_id,
                EntityType.ENDPOINT,
                route,
                f"navigation:{route}",
                path,
                line,
                line,
                framework_kind="nuxt",
                attributes=(
                    ("kind", "navigation"),
                    ("path", route),
                    ("route_path", route),
                    ("registration_chain", chain),
                ),
            )
            ref = evidence_id(context.snapshot_id, path, line, line, NAV_RULE)
            evidence[ref] = Evidence(
                ref, context.snapshot_id, path, line, line, NAV_RULE
            )

        # --- Nitro HTTP Endpoints from server/api naming ---
        api_paths = sorted(
            {
                path
                for path in list(ts_modules)
                + [
                    item.file_path.replace("\\", "/")
                    for item in entities.values()
                    if item.file_path
                    and item.file_path.replace("\\", "/").startswith("server/api/")
                ]
                if api_file_to_endpoint(path) is not None
            }
        )
        for path in api_paths:
            mapped = api_file_to_endpoint(path)
            if mapped is None:
                issues.append(AdapterDiagnostic("nuxt_route_dynamic", path, 1))
                continue
            method, route = mapped
            line = 1
            module = ts_modules.get(path)
            if module is not None:
                line = module.tree.root_node.start_point[0] + 1
            qn = _module_qn(path)
            chain = (f"nitro:{path}:{method}:{route}",)
            identifier = endpoint_id(
                context.repository_id, path, qn, method, route, chain
            )
            entities[identifier] = Entity(
                identifier,
                context.repository_id,
                context.snapshot_id,
                EntityType.ENDPOINT,
                PurePosixPath(path).name,
                qn,
                path,
                line,
                line,
                "http",
                framework_kind="nuxt",
                attributes=(("method", method), ("path", route)),
            )
            ref = evidence_id(context.snapshot_id, path, line, line, ROUTE_RULE)
            evidence[ref] = Evidence(
                ref, context.snapshot_id, path, line, line, ROUTE_RULE
            )
            handlers = [
                item
                for item in entities.values()
                if item.type == EntityType.CALLABLE
                and item.file_path
                and item.file_path.replace("\\", "/") == path
                and item.name.startswith("create")
                and item.name.endswith("Handler")
            ]
            if len(handlers) == 1:
                emit_edge(
                    EdgeType.HANDLED_BY,
                    identifier,
                    handlers[0].id,
                    _Location(path, handlers[0].start_line or line),
                    HANDLER_RULE,
                )
            elif handlers:
                issues.append(AdapterDiagnostic("nuxt_handler_unresolved", path, line))

        # --- runtimeConfig keys (no values) ---
        config_entities: dict[str, Entity] = {}
        for path, module in sorted(ts_modules.items()):
            if PurePosixPath(path).name not in {
                "nuxt.config.ts",
                "nuxt.config.js",
                "nuxt.config.mjs",
            }:
                continue
            for key, boundary, line in _runtime_keys(module):
                entity_id = configuration_id(context.repository_id, "runtime", "", key)
                entity = Entity(
                    entity_id,
                    context.repository_id,
                    context.snapshot_id,
                    EntityType.CONFIGURATION,
                    key,
                    f"runtime:{key}",
                    path,
                    line,
                    line,
                    "runtime",
                    attributes=(
                        ("kind", "runtime"),
                        ("owner", ""),
                        ("boundary", boundary),
                    ),
                )
                entities[entity_id] = entity
                config_entities[key] = entity
                ref = evidence_id(context.snapshot_id, path, line, line, CONFIG_RULE)
                evidence[ref] = Evidence(
                    ref, context.snapshot_id, path, line, line, CONFIG_RULE
                )

        # --- Absolute HTTP origins (skip if language already emitted) ---
        existing_origins = {
            dict(item.attributes).get("origin")
            for item in entities.values()
            if item.type == EntityType.EXTERNAL_DEPENDENCY
        }
        for path, module in sorted(ts_modules.items()):
            if path.startswith("analysis-cases/"):
                continue
            # runtimeConfig values are keys-only; do not promote config literals
            # to ExternalDependency (HTTP origins come from server call sites).
            if PurePosixPath(path).name.startswith("nuxt.config."):
                continue
            for node in walk_named(module.tree.root_node):
                if node.type not in {"string", "template_string"}:
                    continue
                literal = string_literal(module.source, node)
                if literal is None:
                    continue
                origin = _origin(literal)
                if origin is None:
                    continue
                line = node.start_point[0] + 1
                entity_id = source_entity_id(
                    context.repository_id,
                    "",
                    EntityType.EXTERNAL_DEPENDENCY,
                    f"http_service:{origin}",
                )
                if entity_id not in entities and origin not in existing_origins:
                    entities[entity_id] = Entity(
                        entity_id,
                        context.repository_id,
                        context.snapshot_id,
                        EntityType.EXTERNAL_DEPENDENCY,
                        origin,
                        origin,
                        language_kind="http_service",
                        attributes=(("kind", "http_service"), ("origin", origin)),
                    )
                    existing_origins.add(origin)
                # Link from a unique enclosing Callable even when language already
                # emitted the ExternalDependency entity.
                owners = [
                    item
                    for item in entities.values()
                    if item.type == EntityType.CALLABLE
                    and item.file_path
                    and item.file_path.replace("\\", "/") == path
                    and item.start_line
                    and item.end_line
                    and item.start_line <= line <= item.end_line
                ]
                if len(owners) == 1 and entity_id in entities:
                    emit_edge(
                        EdgeType.DEPENDS_ON,
                        owners[0].id,
                        entity_id,
                        _Location(path, line),
                        HTTP_RULE,
                    )

        # --- Convention auto-imports (unique simple name only) ---
        composable_index: dict[str, list[Entity]] = {}
        component_index: dict[str, list[Entity]] = {}
        for item in entities.values():
            if item.type == EntityType.CALLABLE and item.file_path:
                path = item.file_path.replace("\\", "/")
                if "/composables/" in f"/{path}" or path.startswith("app/composables/"):
                    if PurePosixPath(path).stem == item.name or item.name.startswith(
                        "use"
                    ):
                        composable_index.setdefault(item.name, []).append(item)
            if item.type == EntityType.SOURCE_UNIT and item.file_path:
                path = item.file_path.replace("\\", "/")
                if not path.endswith(".vue"):
                    continue
                if "/components/" not in f"/{path}" and not path.startswith(
                    "app/components/"
                ):
                    continue
                stem = PurePosixPath(path).name
                # ConnectionState.client.vue → ConnectionState
                simple = stem[: -len(".vue")].split(".")[0]
                component_index.setdefault(simple, []).append(item)
            if item.type == EntityType.TYPE and item.file_path:
                path = item.file_path.replace("\\", "/")
                if path.endswith(".vue") and (
                    "/components/" in f"/{path}" or path.startswith("app/components/")
                ):
                    component_index.setdefault(item.name, []).append(item)

        by_qn = {item.qualified_name: item for item in entities.values()}
        for path, sfc in sorted(vue_modules.items()):
            source = by_qn.get(sfc.name)
            if source is None or source.type != EntityType.SOURCE_UNIT:
                continue
            imported: set[str] = set()
            for item in sfc.imports:
                if item.default_name:
                    imported.add(item.default_name)
                for _remote, local in item.named:
                    imported.add(local)
                if item.namespace:
                    imported.add(item.namespace)

            # Script callables / identifiers (composables).
            if sfc.script_tree is not None:
                for node in walk_named(sfc.script_tree.root_node):
                    if node.type != "call_expression":
                        continue
                    name = identifier_name(
                        sfc.script_source, child_named(node, "function")
                    )
                    if (
                        name is None
                        or name in imported
                        or name in _FRAMEWORK_NAMES
                        or name in {item.name for item in sfc.definitions}
                    ):
                        continue
                    matches = composable_index.get(name, [])
                    if len(matches) == 1:
                        emit_edge(
                            EdgeType.DEPENDS_ON,
                            source.id,
                            matches[0].id,
                            _Location(path, node.start_point[0] + 1),
                            AUTO_IMPORT_RULE,
                        )
                    elif len(matches) > 1:
                        issues.append(
                            AdapterDiagnostic(
                                "nuxt_auto_import_ambiguous",
                                path,
                                node.start_point[0] + 1,
                            )
                        )
                # useRuntimeConfig → public.* keys referenced statically in
                # script and/or template (e.g. config.public.portalName).
                script_text = sfc.script_source.decode("utf-8", errors="replace")
                template_text = (
                    sfc.template.content.decode("utf-8", errors="replace")
                    if sfc.template is not None
                    else ""
                )
                surface = f"{script_text}\n{template_text}"
                if "useRuntimeConfig" in script_text:
                    for key, entity in config_entities.items():
                        if not key.startswith("public."):
                            continue
                        needle = key.split(".", 1)[1]
                        if f"public.{needle}" not in surface:
                            continue
                        emit_edge(
                            EdgeType.DEPENDS_ON,
                            source.id,
                            entity.id,
                            _Location(path, 1),
                            CONFIG_RULE,
                        )

            # Template component tags.
            if sfc.template is not None:
                text = sfc.template.content.decode("utf-8", errors="replace")
                for match in _TAG.finditer(text):
                    name = match.group(1)
                    if name in imported or name in _FRAMEWORK_NAMES:
                        continue
                    matches = component_index.get(name, [])
                    # Prefer SourceUnit over Type when both indexed.
                    units = [
                        item for item in matches if item.type == EntityType.SOURCE_UNIT
                    ]
                    targets = units if units else matches
                    unique = {item.id: item for item in targets}
                    if len(unique) == 1:
                        target = next(iter(unique.values()))
                        emit_edge(
                            EdgeType.DEPENDS_ON,
                            source.id,
                            target.id,
                            _Location(path, sfc.template.start_line),
                            AUTO_IMPORT_RULE,
                        )
                    elif len(unique) > 1:
                        issues.append(
                            AdapterDiagnostic(
                                "nuxt_auto_import_ambiguous",
                                path,
                                sfc.template.start_line,
                            )
                        )

        # --- Nuxt HTTP clients ($fetch / useFetch / default-$fetch params) ---
        for path, module in sorted(ts_modules.items()):
            _index_nuxt_http_in_tree(
                path=path,
                source=module.source,
                root=module.tree.root_node,
                entities=entities,
            )
        for path, sfc in sorted(vue_modules.items()):
            if sfc.script_tree is None:
                continue
            _index_nuxt_http_in_tree(
                path=path,
                source=sfc.script_source,
                root=sfc.script_tree.root_node,
                entities=entities,
            )

        # --- Navigation handled_by + List route-flow enrichment ---
        for path in page_paths:
            route = page_file_to_route(path)
            if route is None:
                continue
            chain = (f"page:{path}:{route}",)
            identifier = endpoint_id(
                context.repository_id,
                path,
                "navigation",
                "",
                route,
                chain,
            )
            endpoint = entities.get(identifier)
            if endpoint is None:
                continue
            source = _page_source_unit(entities, path)
            if source is None:
                continue
            handler = _ensure_page_handler(context, entities, edges, source, path)
            line = endpoint.start_line or 1
            base_attrs = [
                (key, value)
                for key, value in endpoint.attributes
                if key
                not in {
                    "page_handler",
                    "route_signal",
                    "outbound_requests",
                    "outbound_responses",
                }
            ]
            entities[identifier] = Entity(
                identifier,
                context.repository_id,
                context.snapshot_id,
                EntityType.ENDPOINT,
                endpoint.name,
                endpoint.qualified_name,
                endpoint.file_path,
                endpoint.start_line,
                endpoint.end_line,
                endpoint.language_kind,
                endpoint.framework_kind,
                tuple(base_attrs + list(route_flow_attrs(handler, entities, edges))),
            )
            emit_edge(
                EdgeType.HANDLED_BY,
                identifier,
                handler.id,
                _Location(path, line),
                PAGE_HANDLER_RULE,
            )

        for ordinal, item in enumerate(
            sorted(
                {(i.code, i.relative_path, i.line): i for i in issues}.values(),
                key=lambda item: (item.relative_path or "", item.line or 0, item.code),
            )
        ):
            diagnostics.append(
                Diagnostic(
                    diagnostic_id(
                        context.job_id,
                        item.code,
                        item.relative_path,
                        item.line,
                        ordinal,
                    ),
                    context.job_id,
                    Severity.WARNING,
                    item.code,
                    _MESSAGES[item.code],
                    context.snapshot_id,
                    item.relative_path,
                    item.line,
                )
            )

        facts = FactBatch(
            context.repository_id,
            context.snapshot_id,
            tuple(entities[key] for key in sorted(entities)),
            tuple(edges[key] for key in sorted(edges)),
            tuple(evidence[key] for key in sorted(evidence)),
            tuple(diagnostics),
        )
        adapter_issues = tuple(
            sorted(
                {(i.code, i.relative_path, i.line): i for i in issues}.values(),
                key=lambda item: (item.relative_path or "", item.line or 0, item.code),
            )
        )
        return AdapterResult(
            facts,
            tuple(
                Capability(name, SupportState.SUPPORTED)
                for name in self.descriptor.capabilities
            ),
            adapter_issues,
        )

    def resolve(
        self, context: AdapterContext, parsed: ParseResult, candidate: FactBatch
    ) -> AdapterResult:
        if (
            candidate.repository_id != context.repository_id
            or candidate.snapshot_id != context.snapshot_id
        ):
            raise ValueError("candidate ownership does not match adapter context")
        del parsed
        return AdapterResult(
            candidate,
            tuple(
                Capability(name, SupportState.SUPPORTED)
                for name in self.descriptor.capabilities
            ),
            (),
        )
