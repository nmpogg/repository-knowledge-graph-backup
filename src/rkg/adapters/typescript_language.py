"""TypeScript/TSX language adapter over tree-sitter structured representations.

Pipeline: detect → parse → extract → resolve. Configuration keys and HTTP
origins are language outputs (same ownership pattern as rkg.python). Analyzed
source is never imported or executed.
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
from rkg.adapters.typescript_parse import (
    REPRESENTATION_KIND,
    TsModule,
    is_typescript_file,
    load_path_aliases,
    module_name,
    parse_unit,
    symbol_refs,
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

DETECT_RULE = "RKG.typescript.detect.v1"
STRUCTURE_RULE = "RKG.typescript.structure.v1"
METADATA_RULE = "RKG.typescript_metadata.declared.v1"
_PACKAGE_NAME = re.compile(r"^(@[a-z0-9._-]+/)?[a-z0-9._-]+$", re.IGNORECASE)

_MESSAGES = {
    "typescript_syntax_error": "TypeScript source could not be parsed; file skipped.",
    "typescript_duplicate_definition": "Duplicate lexical definition skipped.",
    "typescript_import_unresolved": "Import target cannot be resolved uniquely.",
    "typescript_import_dynamic": "Dynamic import cannot be resolved statically.",
    "typescript_binding_ambiguous": "Binding is ambiguous or shadowed.",
    "typescript_call_unresolved": "Call target cannot be resolved uniquely.",
    "typescript_call_dynamic": "Dynamic call dispatch is unsupported.",
    "typescript_config_unresolved": "Configuration key is not a literal.",
    "typescript_http_unresolved": "HTTP URL is not a literal origin.",
    "typescript_metadata_invalid": "Dependency metadata could not be parsed.",
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
                Severity.ERROR
                if item.code == "typescript_syntax_error"
                else Severity.WARNING,
                item.code,
                _MESSAGES[item.code],
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
                AdapterDiagnostic("typescript_metadata_invalid", item.relative_path, 1)
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


class TypeScriptLanguageAdapter:
    """Emit source-backed facts for structure, imports, calls, config and HTTP."""

    descriptor = AdapterDescriptor(
        adapter_id="rkg.typescript",
        adapter_version="0.1.0",
        contract_version=CONTRACT_VERSION,
        kind=AdapterKind.LANGUAGE,
        language="typescript",
        grammar_or_target="tree-sitter TypeScript/TSX",
        file_patterns=(
            "*.ts",
            "*.tsx",
            "**/*.ts",
            "**/*.tsx",
            "package.json",
            "tsconfig*.json",
        ),
        ignore_patterns=("**/node_modules/**", "**/*.d.ts"),
        capabilities=("calls", "classes", "imports", "metadata", "structure"),
    )

    def technology_detectors(self) -> tuple[object, ...]:
        return ()

    def detect(self, manifest: SourceManifest) -> DetectionReport:
        evidence = tuple(
            DetectionEvidence(item.relative_path, DETECT_RULE)
            for item in manifest.files
            if is_typescript_file(item.relative_path)
        )
        technologies: list[TechnologyDetection] = []
        if evidence:
            technologies.append(TechnologyDetection("typescript", None, evidence))
        deps, _ = _package_dependencies(manifest)
        allowed = {
            "react",
            "react-dom",
            "react-router",
            "react-router-dom",
            "typescript",
            "vite",
        }
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
        aliases = load_path_aliases(manifest)
        units: list[ParsedUnit] = []
        symbols = []
        diagnostics: list[AdapterDiagnostic] = []
        _, meta_diagnostics = _package_dependencies(manifest)
        diagnostics.extend(meta_diagnostics)
        for item in manifest.files:
            path = item.relative_path
            if not is_typescript_file(path):
                continue
            module, issues = parse_unit(path, item.content, aliases)
            diagnostics.extend(issues)
            if module is None:
                continue
            units.append(
                ParsedUnit(
                    path,
                    "typescript",
                    REPRESENTATION_KIND,
                    item.content_hash,
                    module,
                )
            )
            symbols.extend(symbol_refs(module))
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
            if unit.language != "typescript" or not isinstance(
                unit.representation, TsModule
            ):
                raise ValueError("invalid TypeScript parsed unit")
            module: TsModule = unit.representation
            path = unit.relative_path
            module_q = module_name(path)
            source_id = source_entity_id(
                context.repository_id, path, EntityType.SOURCE_UNIT, module_q
            )
            entities.append(
                Entity(
                    source_id,
                    context.repository_id,
                    context.snapshot_id,
                    EntityType.SOURCE_UNIT,
                    PurePosixPath(path).name,
                    module_q,
                    path,
                    language_kind="typescript_source_unit",
                    attributes=(("module_name", module_q),),
                )
            )
            owners = {module_q: source_id}
            owner_types = {module_q: EntityType.SOURCE_UNIT}
            for item in module.definitions:
                entity_type = (
                    EntityType.TYPE
                    if item.kind
                    in {
                        "typescript_class",
                        "typescript_interface",
                        "typescript_type_alias",
                        "typescript_object",
                    }
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
                owner_types[item.qualified_name] = entity_type
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
        from rkg.adapters.typescript_resolution import resolve_typescript

        facts, diagnostics = resolve_typescript(context, parsed, candidate)
        return AdapterResult(facts, self._capabilities(), diagnostics)

    @staticmethod
    def _capabilities() -> tuple[Capability, ...]:
        return tuple(
            Capability(name, SupportState.SUPPORTED)
            for name in TypeScriptLanguageAdapter.descriptor.capabilities
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
