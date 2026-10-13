"""Static Flask application candidate discovery.

The detector reads the parsed AST only. It does not import or execute source.
"""

from __future__ import annotations

import ast
from pathlib import PurePosixPath

from rkg.adapters import (
    DetectionEvidence,
    DetectionReport,
    ParseResult,
    TechnologyDetection,
)
from rkg.adapters.python_language import _module_name
from rkg.adapters.python_resolution import _bindings, _Module, _qualified
from rkg.detection.contracts import ApplicationCandidate, FrameworkObservation
from rkg.ingestion import SourceManifest

IMPORT_RULE = "RKG.flask.detect_import.v1"
APP_RULE = "RKG.flask.detect_app.v1"


class FlaskAppDetector:
    """Find direct module-level ``Flask()`` assignments without importing source."""

    def detect(
        self, manifest: SourceManifest, parsed: ParseResult
    ) -> FrameworkObservation:
        del manifest
        local_roots = set()
        for unit in parsed.units:
            if isinstance(unit.representation, ast.Module):
                pure = PurePosixPath(unit.relative_path)
                local_roots.add(pure.stem)
                local_roots.add(_module_name(unit.relative_path).split(".")[0])
                if pure.stem == "__init__" and len(pure.parts) > 1:
                    local_roots.add(pure.parts[-2])
        if "flask" in local_roots:
            return FrameworkObservation(DetectionReport())
        evidence: set[DetectionEvidence] = set()
        applications: set[ApplicationCandidate] = set()
        for unit in parsed.units:
            tree = unit.representation
            if not isinstance(tree, ast.Module):
                continue
            path = unit.relative_path
            module = _Module(path, _module_name(path), tree)
            frame = _bindings(module, tree.body, module.name)
            writes: dict[str, int] = {}
            for node in ast.walk(tree):
                if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
                    writes[node.id] = writes.get(node.id, 0) + 1
            saw_import = False
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    if any(alias.name.split(".")[0] == "flask" for alias in node.names):
                        saw_import = True
                elif isinstance(node, ast.ImportFrom) and node.level == 0:
                    if node.module and node.module.split(".")[0] == "flask":
                        saw_import = True
            if saw_import:
                evidence.add(DetectionEvidence(path, IMPORT_RULE))
            for statement in tree.body:
                target: str | None = None
                value: ast.expr | None = None
                if isinstance(statement, ast.Assign) and len(statement.targets) == 1:
                    if isinstance(statement.targets[0], ast.Name):
                        target = statement.targets[0].id
                        value = statement.value
                elif isinstance(statement, ast.AnnAssign) and isinstance(
                    statement.target, ast.Name
                ):
                    target = statement.target.id
                    value = statement.value
                if target and writes.get(target) == 1 and isinstance(value, ast.Call):
                    if _qualified(value.func, [frame]) == "flask.Flask":
                        applications.add(
                            ApplicationCandidate(
                                f"{module.name}:{target}",
                                path,
                                statement.lineno,
                                APP_RULE,
                            )
                        )
                        evidence.add(DetectionEvidence(path, APP_RULE))
        if not applications:
            return FrameworkObservation(DetectionReport())
        references = tuple(
            sorted(evidence, key=lambda item: (item.relative_path, item.rule_id))
        )
        return FrameworkObservation(
            DetectionReport((TechnologyDetection("flask", None, references),)),
            tuple(sorted(applications, key=lambda item: item.reference)),
        )
