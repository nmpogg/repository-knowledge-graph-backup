"""CPython 3.12 structural adapter over immutable manifest bytes.

This module parses syntax only. Import/call/class relationship resolution belongs to
the next adapter task; no analyzed source is imported or executed here.
"""

from __future__ import annotations

import ast
from collections.abc import Iterator, Sequence
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
    SymbolRef,
    TechnologyDetection,
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

DETECT_RULE = "RKG.python.detect.v1"
STRUCTURE_RULE = "RKG.python.structure.v1"

type Definition = ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef


def _python_file(path: str) -> bool:
    return path.endswith(".py") and "__pycache__" not in PurePosixPath(path).parts


def _module_name(path: str) -> str:
    parts = list(PurePosixPath(path).with_suffix("").parts)
    if len(parts) > 1 and parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


def _nested_bodies(statement: ast.stmt) -> Iterator[Sequence[ast.stmt]]:
    """Find declaration blocks while preserving the enclosing lexical scope."""
    if isinstance(statement, (ast.If, ast.For, ast.AsyncFor, ast.While)):
        yield statement.body
        yield statement.orelse
    elif isinstance(statement, (ast.With, ast.AsyncWith)):
        yield statement.body
    elif isinstance(statement, (ast.Try, ast.TryStar)):
        yield statement.body
        for handler in statement.handlers:
            yield handler.body
        yield statement.orelse
        yield statement.finalbody
    elif isinstance(statement, ast.Match):
        for case in statement.cases:
            yield case.body


def _unique_definitions(
    tree: ast.Module, module_name: str, path: str
) -> tuple[list[tuple[str, str, Definition]], list[AdapterDiagnostic]]:
    seen: set[str] = set()
    definitions: list[tuple[str, str, Definition]] = []
    diagnostics: list[AdapterDiagnostic] = []

    def visit(body: Sequence[ast.stmt], owner: str) -> None:
        for statement in body:
            if isinstance(
                statement, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)
            ):
                qualified_name = f"{owner}.{statement.name}"
                if qualified_name in seen:
                    diagnostics.append(
                        AdapterDiagnostic(
                            "python_duplicate_definition", path, statement.lineno
                        )
                    )
                    continue
                seen.add(qualified_name)
                definitions.append((owner, qualified_name, statement))
                visit(statement.body, qualified_name)
            else:
                for nested in _nested_bodies(statement):
                    visit(nested, owner)

    visit(tree.body, module_name)
    return definitions, diagnostics


def _canonical_diagnostics(
    context: AdapterContext, diagnostics: tuple[AdapterDiagnostic, ...]
) -> tuple[Diagnostic, ...]:
    messages = {
        "python_syntax_error": "Python source could not be parsed; file skipped.",
        "python_duplicate_definition": "Duplicate lexical definition skipped.",
        "python_import_star": "Star import cannot be resolved statically.",
        "python_import_unresolved": "Import target cannot be resolved uniquely.",
        "python_binding_ambiguous": "Binding is ambiguous or shadowed.",
        "python_call_unresolved": "Call target cannot be resolved uniquely.",
        "python_call_dynamic": "Dynamic call dispatch is unsupported.",
        "python_base_unresolved": "Base type cannot be resolved uniquely.",
        "python_metadata_invalid": "Dependency metadata could not be parsed.",
        "python_metadata_dynamic": "Dynamic dependency metadata is unresolved.",
        "python_metadata_unsupported": "Dependency entry is unsupported.",
        "python_metadata_include_cycle": "Dependency include cycle was skipped.",
        "python_metadata_include_missing": "Dependency include target was unavailable.",
        "python_config_unresolved": "Configuration key is not a literal.",
        "python_http_unresolved": "HTTP URL is not a literal origin.",
    }
    output = []
    for ordinal, item in enumerate(diagnostics):
        output.append(
            Diagnostic(
                diagnostic_id(
                    context.job_id, item.code, item.relative_path, item.line, ordinal
                ),
                context.job_id,
                Severity.ERROR
                if item.code == "python_syntax_error"
                else Severity.WARNING,
                item.code,
                messages[item.code],
                context.snapshot_id,
                item.relative_path,
                item.line,
            )
        )
    return tuple(output)


class PythonLanguageAdapter:
    """Emit source-backed facts for structure, config keys and HTTP origins."""

    descriptor = AdapterDescriptor(
        adapter_id="rkg.python",
        adapter_version="2.1",
        contract_version=CONTRACT_VERSION,
        kind=AdapterKind.LANGUAGE,
        language="python",
        grammar_or_target="CPython 3.12 AST",
        file_patterns=(
            "*.py",
            "**/*.py",
            "pyproject.toml",
            "poetry.lock",
            "uv.lock",
            "requirements*.txt",
        ),
        ignore_patterns=("**/__pycache__/**",),
        capabilities=("calls", "classes", "imports", "metadata", "structure"),
    )

    def technology_detectors(self) -> tuple[object, ...]:
        """Import evidence for this language. Framework adapters add their own."""
        from rkg.detection.python_imports import PythonImportDetector

        return (PythonImportDetector(),)

    def detect(self, manifest: SourceManifest) -> DetectionReport:
        from rkg.adapters.python_metadata import read_inventory

        evidence = tuple(
            DetectionEvidence(item.relative_path, DETECT_RULE)
            for item in manifest.files
            if _python_file(item.relative_path)
        )
        technologies = (
            [TechnologyDetection("python", None, evidence)] if evidence else []
        )
        inventory = read_inventory(manifest)
        for name in sorted({item.name for item in inventory.dependencies}):
            declarations = [
                item for item in inventory.dependencies if item.name == name
            ]
            locked = next(
                (item.version for item in declarations if item.source == "lock"), None
            )
            technologies.append(
                TechnologyDetection(
                    name,
                    locked,
                    tuple(
                        DetectionEvidence(
                            item.path,
                            "RKG.python_metadata.lock.v1"
                            if item.source == "lock"
                            else "RKG.python_metadata.declared.v1",
                        )
                        for item in declarations
                    ),
                )
            )
        return DetectionReport(
            tuple(sorted(technologies, key=lambda item: item.technology))
        )

    def parse(self, manifest: SourceManifest, config: SourceScanConfig) -> ParseResult:
        del config  # The loader has already applied the effective scan config.
        from rkg.adapters.python_metadata import read_inventory

        inventory = read_inventory(manifest)
        units = []
        symbols = []
        diagnostics = list(inventory.diagnostics)
        for item in manifest.files:
            path = item.relative_path
            if not _python_file(path):
                continue
            try:
                tree = ast.parse(
                    item.content,
                    filename=path,
                    mode="exec",
                    feature_version=(3, 12),
                )
            except (SyntaxError, UnicodeError, ValueError) as exc:
                line = max(getattr(exc, "lineno", None) or 1, 1)
                diagnostics.append(AdapterDiagnostic("python_syntax_error", path, line))
                continue
            units.append(
                ParsedUnit(path, "python", "cpython-ast/3.12", item.content_hash, tree)
            )
            definitions, duplicates = _unique_definitions(
                tree, _module_name(path), path
            )
            diagnostics.extend(duplicates)
            symbols.extend(
                SymbolRef(qualified_name, path, owner)
                for owner, qualified_name, _ in definitions
            )
        if inventory.dependencies:
            metadata_path = inventory.dependencies[0].path
            metadata_hash = next(
                item.content_hash
                for item in manifest.files
                if item.relative_path == metadata_path
            )
            units.append(
                ParsedUnit(
                    metadata_path,
                    "python",
                    "python-metadata/v1",
                    metadata_hash,
                    inventory,
                )
            )
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
            if unit.representation_kind == "python-metadata/v1":
                continue
            if unit.language != "python" or not isinstance(
                unit.representation, ast.Module
            ):
                raise ValueError("invalid Python parsed unit")
            path = unit.relative_path
            module = _module_name(path)
            source_id = source_entity_id(
                context.repository_id, path, EntityType.SOURCE_UNIT, module
            )
            entities.append(
                Entity(
                    source_id,
                    context.repository_id,
                    context.snapshot_id,
                    EntityType.SOURCE_UNIT,
                    PurePosixPath(path).name,
                    module,
                    path,
                    language_kind="python_source_unit",
                    attributes=(("module_name", module),),
                )
            )
            if not unit.representation.body:
                continue
            owners = {module: source_id}
            owner_types = {module: EntityType.SOURCE_UNIT}
            definitions, _ = _unique_definitions(unit.representation, module, path)
            for owner, qualified_name, node in definitions:
                entity_type = (
                    EntityType.TYPE
                    if isinstance(node, ast.ClassDef)
                    else EntityType.CALLABLE
                )
                entity_id = source_entity_id(
                    context.repository_id, path, entity_type, qualified_name
                )
                parent_id = owners[owner]
                kind = (
                    "python_class"
                    if isinstance(node, ast.ClassDef)
                    else "python_async_method"
                    if isinstance(node, ast.AsyncFunctionDef)
                    and owner_types[owner] == EntityType.TYPE
                    else "python_async_function"
                    if isinstance(node, ast.AsyncFunctionDef)
                    else "python_method"
                    if owner_types[owner] == EntityType.TYPE
                    else "python_function"
                )
                entities.append(
                    Entity(
                        entity_id,
                        context.repository_id,
                        context.snapshot_id,
                        entity_type,
                        node.name,
                        qualified_name,
                        path,
                        node.lineno,
                        node.end_lineno or node.lineno,
                        kind,
                    )
                )
                self._contains(
                    context, path, node.lineno, parent_id, entity_id, edges, evidence
                )
                owners[qualified_name] = entity_id
                owner_types[qualified_name] = entity_type
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
        from rkg.adapters.python_config import add_config_http_facts
        from rkg.adapters.python_metadata import add_inventory_facts
        from rkg.adapters.python_resolution import resolve_python

        facts, diagnostics = resolve_python(context, parsed, candidate)
        facts = add_inventory_facts(context, parsed, facts)
        facts, config_diagnostics = add_config_http_facts(context, parsed, facts)
        return AdapterResult(
            facts,
            self._capabilities(),
            tuple(diagnostics) + config_diagnostics,
        )

    @staticmethod
    def _capabilities() -> tuple[Capability, ...]:
        return tuple(
            Capability(name, SupportState.SUPPORTED)
            for name in PythonLanguageAdapter.descriptor.capabilities
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
