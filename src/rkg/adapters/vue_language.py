"""Vue SFC language adapter over structured SFC blocks + TypeScript script CST.

Pipeline: detect → parse → extract → resolve. One `.vue` file is one SourceUnit
with structured template/script/style sections (never fabricated sibling source
files). Analyzed source is never imported or executed.
"""

from __future__ import annotations

import json
import re
from pathlib import PurePosixPath

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
    ParsedUnit,
    ParseResult,
    SupportState,
    TechnologyDetection,
)
from rkg.adapters.vue_parse import (
    REPRESENTATION_KIND,
    VueSfc,
    body_of_definition,
    child_named,
    identifier_name,
    is_vue_file,
    module_name,
    parse_unit,
    resolve_vue_specifier,
    symbol_refs,
    walk_named,
)
from rkg.domain import (
    Diagnostic,
    Edge,
    EdgeType,
    Entity,
    EntityType,
    Evidence,
    FactBatch,
    Severity,
    SourceScanConfig,
    diagnostic_id,
    edge_id,
    evidence_id,
    source_entity_id,
)
from rkg.ingestion import SourceManifest

DETECT_RULE = "RKG.vue.detect.v1"
STRUCTURE_RULE = "RKG.vue.structure.v1"
IMPORT_RULE = "RKG.vue.import.v1"
CALL_RULE = "RKG.vue.call.v1"
METADATA_RULE = "RKG.vue_metadata.declared.v1"
_PACKAGE_NAME = re.compile(r"^(@[a-z0-9._-]+/)?[a-z0-9._-]+$", re.IGNORECASE)
_SECRET = "RKG_TEST_SECRET_DO_NOT_PERSIST"

_MESSAGES = {
    "vue_syntax_error": "Vue SFC or script could not be parsed; file skipped.",
    "vue_duplicate_definition": "Duplicate lexical definition skipped.",
    "vue_import_unresolved": "Import target cannot be resolved uniquely.",
    "vue_import_dynamic": "Dynamic import cannot be resolved statically.",
    "vue_binding_ambiguous": "Binding is ambiguous or shadowed.",
    "vue_call_unresolved": "Call target cannot be resolved uniquely.",
    "vue_call_dynamic": "Dynamic call dispatch is unsupported.",
    "vue_metadata_invalid": "Dependency metadata could not be parsed.",
}


def _canonical_diagnostics(
    context: AdapterContext, diagnostics: tuple[AdapterDiagnostic, ...]
) -> tuple[Diagnostic, ...]:
    output = []
    for ordinal, item in enumerate(diagnostics):
        output.append(
            Diagnostic(
                diagnostic_id(
                    context.job_id, item.code, item.relative_path, item.line, ordinal
                ),
                context.job_id,
                Severity.ERROR if item.code == "vue_syntax_error" else Severity.WARNING,
                item.code,
                _MESSAGES.get(item.code, item.code),
                context.snapshot_id,
                item.relative_path,
                item.line,
            )
        )
    return tuple(output)


def _package_dependencies(
    manifest: SourceManifest,
) -> tuple[list[tuple[str, str | None, str]], list[AdapterDiagnostic]]:
    deps: list[tuple[str, str | None, str]] = []
    diagnostics: list[AdapterDiagnostic] = []
    for item in manifest.files:
        if PurePosixPath(item.relative_path).name != "package.json":
            continue
        try:
            data = json.loads(item.content.decode("utf-8"))
        except (UnicodeError, json.JSONDecodeError, ValueError):
            diagnostics.append(
                AdapterDiagnostic("vue_metadata_invalid", item.relative_path, 1)
            )
            continue
        for section in ("dependencies", "devDependencies", "peerDependencies"):
            block = data.get(section) or {}
            if not isinstance(block, dict):
                continue
            for name, version in block.items():
                if not isinstance(name, str) or not _PACKAGE_NAME.fullmatch(name):
                    continue
                ver = version if isinstance(version, str) else None
                deps.append((name, ver, item.relative_path))
    return deps, diagnostics


class VueLanguageAdapter:
    """Emit source-backed facts for Vue SFC structure, imports and calls."""

    descriptor = AdapterDescriptor(
        adapter_id="rkg.vue",
        adapter_version="0.1.0",
        contract_version=CONTRACT_VERSION,
        kind=AdapterKind.LANGUAGE,
        language="vue",
        grammar_or_target="Vue SFC blocks + tree-sitter TypeScript script",
        # package.json stays with rkg.typescript — shared basename would conflict
        # in language partition (language_extension_conflict).
        file_patterns=("*.vue", "**/*.vue"),
        ignore_patterns=(
            "**/node_modules/**",
            "**/.nuxt/**",
            "**/.output/**",
            "**/dist/**",
            "**/coverage/**",
        ),
        capabilities=("calls", "classes", "imports", "metadata", "structure"),
    )

    def technology_detectors(self) -> tuple[object, ...]:
        return ()

    def detect(self, manifest: SourceManifest) -> DetectionReport:
        evidence = tuple(
            DetectionEvidence(item.relative_path, DETECT_RULE)
            for item in manifest.files
            if is_vue_file(item.relative_path)
        )
        technologies: list[TechnologyDetection] = []
        if evidence:
            technologies.append(TechnologyDetection("vue", None, evidence))
        deps, _ = _package_dependencies(manifest)
        allowed = {"vue", "vue-router", "nuxt"}
        for name in sorted({item[0] for item in deps if item[0] in allowed}):
            declarations = [item for item in deps if item[0] == name]
            version = next((item[1] for item in declarations if item[1]), None)
            technologies.append(
                TechnologyDetection(
                    name,
                    version.lstrip("^~>=<") if version else None,
                    tuple(
                        DetectionEvidence(item[2], METADATA_RULE)
                        for item in declarations
                    ),
                )
            )
        return DetectionReport(
            tuple(sorted(technologies, key=lambda item: item.technology))
        )

    def parse(self, manifest: SourceManifest, config: SourceScanConfig) -> ParseResult:
        del config
        units: list[ParsedUnit] = []
        symbols = []
        diagnostics: list[AdapterDiagnostic] = []
        _, meta_diagnostics = _package_dependencies(manifest)
        diagnostics.extend(meta_diagnostics)
        for item in manifest.files:
            path = item.relative_path
            if not is_vue_file(path):
                continue
            sfc, issues = parse_unit(path, item.content)
            diagnostics.extend(issues)
            if sfc is None:
                continue
            units.append(
                ParsedUnit(
                    path,
                    "vue",
                    REPRESENTATION_KIND,
                    item.content_hash,
                    sfc,
                )
            )
            symbols.extend(symbol_refs(sfc))
        return ParseResult(
            tuple(sorted(units, key=lambda unit: unit.relative_path)),
            tuple(
                sorted(
                    symbols, key=lambda item: (item.qualified_name, item.relative_path)
                )
            ),
            tuple(
                sorted(
                    diagnostics,
                    key=lambda item: (
                        item.relative_path or "",
                        item.line or 0,
                        item.code,
                    ),
                )
            ),
        )

    def extract(self, context: AdapterContext, parsed: ParseResult) -> AdapterResult:
        entities: list[Entity] = []
        edges: list[Edge] = []
        evidence: dict[str, Evidence] = {}
        for unit in parsed.units:
            if unit.language != "vue" or not isinstance(unit.representation, VueSfc):
                raise ValueError("invalid Vue parsed unit")
            sfc: VueSfc = unit.representation
            path = unit.relative_path
            module_q = module_name(path)
            source_id = source_entity_id(
                context.repository_id, path, EntityType.SOURCE_UNIT, module_q
            )
            section_attrs: list[tuple[str, str]] = []
            if sfc.template is not None:
                section_attrs.append(("has_template", "true"))
            if sfc.scripts:
                langs = ",".join(sorted({(s.lang or "ts") for s in sfc.scripts}))
                section_attrs.append(("script_lang", langs))
                if any(s.is_setup for s in sfc.scripts):
                    section_attrs.append(("script_setup", "true"))
            if sfc.styles:
                section_attrs.append(("has_style", "true"))
            entities.append(
                Entity(
                    source_id,
                    context.repository_id,
                    context.snapshot_id,
                    EntityType.SOURCE_UNIT,
                    PurePosixPath(path).name,
                    module_q,
                    path,
                    language_kind="vue_source_unit",
                    attributes=(("module_name", module_q), *section_attrs),
                )
            )
            owners = {module_q: source_id}
            for item in sfc.definitions:
                entity_type = (
                    EntityType.TYPE
                    if item.kind == "vue_component"
                    else EntityType.CALLABLE
                )
                entity_id = source_entity_id(
                    context.repository_id, path, entity_type, item.qualified_name
                )
                parent_id = owners.get(item.owner, source_id)
                entities.append(
                    Entity(
                        entity_id,
                        context.repository_id,
                        context.snapshot_id,
                        entity_type,
                        item.name,
                        item.qualified_name,
                        path,
                        item.start_line,
                        item.end_line,
                        item.kind,
                    )
                )
                self._contains(
                    context,
                    path,
                    item.start_line,
                    parent_id,
                    entity_id,
                    edges,
                    evidence,
                )
                owners[item.qualified_name] = entity_id
        facts = FactBatch(
            context.repository_id,
            context.snapshot_id,
            tuple(sorted(entities, key=lambda item: item.id)),
            tuple(sorted(edges, key=lambda item: item.id)),
            tuple(evidence[key] for key in sorted(evidence)),
            _canonical_diagnostics(context, parsed.diagnostics),
        )
        return AdapterResult(facts, self._capabilities(), parsed.diagnostics)

    def resolve(
        self, context: AdapterContext, parsed: ParseResult, candidate: FactBatch
    ) -> AdapterResult:
        if (
            candidate.repository_id != context.repository_id
            or candidate.snapshot_id != context.snapshot_id
        ):
            raise ValueError("candidate ownership does not match adapter context")
        modules = {
            unit.relative_path: unit.representation
            for unit in parsed.units
            if isinstance(unit.representation, VueSfc)
        }
        files = set(modules)
        entities = {item.id: item for item in candidate.entities}
        by_qn = {item.qualified_name: item for item in entities.values()}
        edges = {item.id: item for item in candidate.edges}
        evidence = {item.id: item for item in candidate.evidence}
        diagnostics = list(parsed.diagnostics)

        def relate(
            kind: EdgeType,
            source: Entity,
            target: Entity,
            path: str,
            line: int,
            rule: str,
        ) -> None:
            ref = evidence_id(context.snapshot_id, path, line, line, rule)
            evidence[ref] = Evidence(ref, context.snapshot_id, path, line, line, rule)
            key = edge_id(context.snapshot_id, kind, source.id, target.id)
            existing = edges.get(key)
            refs = set(existing.evidence_ids) if existing else set()
            refs.add(ref)
            edges[key] = Edge(
                key,
                context.snapshot_id,
                kind,
                source.id,
                target.id,
                rule,
                tuple(sorted(refs)),
            )

        # Imports — relative .vue/.ts only. Bare npm packages stay with
        # rkg.typescript (same ExternalDependency IDs would collide on merge).
        # Nuxt `#` aliases are framework convention and are not guessed here.
        for sfc in modules.values():
            source = by_qn.get(sfc.name)
            if source is None:
                continue
            for item in sfc.imports:
                if item.is_type_only:
                    continue
                target_path = resolve_vue_specifier(sfc.path, item.specifier, files)
                if target_path is None:
                    if item.specifier.startswith(".") or item.specifier.startswith("#"):
                        diagnostics.append(
                            AdapterDiagnostic(
                                "vue_import_unresolved", sfc.path, item.line
                            )
                        )
                    continue
                target_module = modules.get(target_path)
                if target_module is None:
                    diagnostics.append(
                        AdapterDiagnostic(
                            "vue_import_unresolved", sfc.path, item.line
                        )
                    )
                    continue
                target = by_qn.get(target_module.name)
                if target is None:
                    diagnostics.append(
                        AdapterDiagnostic(
                            "vue_import_unresolved", sfc.path, item.line
                        )
                    )
                    continue
                # Prefer component Type when uniquely present for default import.
                if item.default_name and target_module.component_name:
                    type_qn = (
                        f"{target_module.name}.{target_module.component_name}"
                    )
                    type_entity = by_qn.get(type_qn)
                    if type_entity is not None and type_entity.type == EntityType.TYPE:
                        target = type_entity
                relate(
                    EdgeType.IMPORTS, source, target, sfc.path, item.line, IMPORT_RULE
                )

        # Calls — unique same-SFC / imported callables only.
        for sfc in modules.values():
            if sfc.script_tree is None:
                continue
            local_callables = {
                item.name: item
                for item in sfc.definitions
                if item.kind != "vue_component"
            }
            for definition in sfc.definitions:
                if definition.kind == "vue_component":
                    continue
                caller = by_qn.get(definition.qualified_name)
                if caller is None:
                    continue
                body = body_of_definition(definition)
                if body is None:
                    continue
                for node in walk_named(body):
                    if node.type != "call_expression":
                        continue
                    callee = child_named(node, "function")
                    line = node.start_point[0] + 1
                    name = identifier_name(sfc.script_source, callee)
                    if (
                        name is None
                        and callee is not None
                        and callee.type == "member_expression"
                    ):
                        # Skip member calls unless uniquely bound later.
                        continue
                    if name is None:
                        diagnostics.append(
                            AdapterDiagnostic("vue_call_unresolved", sfc.path, line)
                        )
                        continue
                    if name in {"emit", "$fetch", "useFetch", "useRuntimeConfig"}:
                        # Framework/runtime helpers — not guessed as graph callables.
                        continue
                    target_def = local_callables.get(name)
                    if target_def is None:
                        continue
                    if target_def.qualified_name == definition.qualified_name:
                        continue
                    target = by_qn.get(target_def.qualified_name)
                    if target is None:
                        continue
                    relate(
                        EdgeType.CALLS, caller, target, sfc.path, line, CALL_RULE
                    )

        adapter_diagnostics = tuple(
            sorted(
                diagnostics,
                key=lambda item: (item.relative_path or "", item.line or 0, item.code),
            )
        )
        facts = FactBatch(
            context.repository_id,
            context.snapshot_id,
            tuple(sorted(entities.values(), key=lambda item: item.id)),
            tuple(sorted(edges.values(), key=lambda item: item.id)),
            tuple(evidence[key] for key in sorted(evidence)),
            _canonical_diagnostics(context, adapter_diagnostics),
        )
        if any(_SECRET in (item.qualified_name or "") for item in facts.entities):
            raise ValueError("secret leaked into entity identity")
        if any(_SECRET in (item.message or "") for item in facts.diagnostics):
            raise ValueError("secret leaked into diagnostics")
        return AdapterResult(facts, self._capabilities(), adapter_diagnostics)

    @staticmethod
    def _capabilities() -> tuple[Capability, ...]:
        return tuple(
            Capability(name, SupportState.SUPPORTED)
            for name in VueLanguageAdapter.descriptor.capabilities
        )

    @staticmethod
    def _contains(
        context: AdapterContext,
        path: str,
        line: int,
        parent_id: str,
        child_id: str,
        edges: list[Edge],
        evidence: dict[str, Evidence],
    ) -> None:
        ref_id = evidence_id(context.snapshot_id, path, line, line, STRUCTURE_RULE)
        evidence[ref_id] = Evidence(
            ref_id, context.snapshot_id, path, line, line, STRUCTURE_RULE
        )
        edges.append(
            Edge(
                edge_id(context.snapshot_id, EdgeType.CONTAINS, parent_id, child_id),
                context.snapshot_id,
                EdgeType.CONTAINS,
                parent_id,
                child_id,
                STRUCTURE_RULE,
                (ref_id,),
            )
        )
