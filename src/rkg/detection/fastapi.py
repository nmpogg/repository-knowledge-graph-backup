"""Static FastAPI application candidate discovery for the initial Python profile."""

from __future__ import annotations

import ast
from pathlib import PurePosixPath

from rkg.adapters import (
    DetectionEvidence,
    DetectionReport,
    ParseResult,
    TechnologyDetection,
)
from rkg.adapters.fastapi_static import factory_view, module_writes
from rkg.adapters.python_language import _module_name
from rkg.adapters.python_resolution import _bindings, _Module, _qualified
from rkg.detection.contracts import ApplicationCandidate, FrameworkObservation
from rkg.ingestion import SourceManifest

IMPORT_RULE = "RKG.fastapi.detect_import.v1"
APP_RULE = "RKG.fastapi.detect_app.v1"


class FastAPIAppDetector:
    """Find direct assignments and static local app factories without execution."""

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
        if "fastapi" in local_roots:
            return FrameworkObservation(DetectionReport())
        evidence: set[DetectionEvidence] = set()
        applications: set[ApplicationCandidate] = set()
        for unit in parsed.units:
            tree = unit.representation
            if not isinstance(tree, ast.Module):
                continue
            path = unit.relative_path
            module = _Module(path, _module_name(path), tree)
            tree = factory_view(module)
            module = _Module(path, module.name, tree)
            frame = _bindings(module, tree.body, module.name)
            writes = module_writes(tree)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    if any(
                        alias.name.split(".")[0] == "fastapi" for alias in node.names
                    ):
                        evidence.add(DetectionEvidence(path, IMPORT_RULE))
                elif isinstance(node, ast.ImportFrom) and node.level == 0:
                    if node.module and node.module.split(".")[0] == "fastapi":
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
                    if _qualified(value.func, [frame]) == "fastapi.FastAPI":
                        applications.add(
                            ApplicationCandidate(
                                f"{module.name}:{target}",
                                path,
                                statement.lineno,
                                APP_RULE,
                            )
                        )
                        evidence.add(DetectionEvidence(path, APP_RULE))
        references = tuple(
            sorted(evidence, key=lambda item: (item.relative_path, item.rule_id))
        )
        report = (
            DetectionReport((TechnologyDetection("fastapi", None, references),))
            if references
            else DetectionReport()
        )
        return FrameworkObservation(
            report, tuple(sorted(applications, key=lambda item: item.reference))
        )
