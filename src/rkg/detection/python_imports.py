"""Explicit Python import evidence for registered technology profiles."""

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
from rkg.adapters.python_metadata import IMPORT_OWNERS
from rkg.detection.contracts import FrameworkObservation
from rkg.ingestion import SourceManifest

IMPORT_RULE = "RKG.python_technology.import.v1"


class PythonImportDetector:
    def detect(
        self, manifest: SourceManifest, parsed: ParseResult
    ) -> FrameworkObservation:
        del manifest
        roots = {root: name for name, names in IMPORT_OWNERS.items() for root in names}
        local = set()
        for unit in parsed.units:
            if isinstance(unit.representation, ast.Module):
                pure = PurePosixPath(unit.relative_path)
                local.add(pure.stem)
                local.add(_module_name(unit.relative_path).split(".")[0])
                if pure.stem == "__init__" and len(pure.parts) > 1:
                    local.add(pure.parts[-2])
        found: dict[str, set[DetectionEvidence]] = {}
        for unit in parsed.units:
            if not isinstance(unit.representation, ast.Module):
                continue
            for node in ast.walk(unit.representation):
                imports = ()
                if isinstance(node, ast.Import):
                    imports = tuple(alias.name.split(".")[0] for alias in node.names)
                elif (
                    isinstance(node, ast.ImportFrom) and node.level == 0 and node.module
                ):
                    imports = (node.module.split(".")[0],)
                for root in imports:
                    if root not in local and root in roots:
                        found.setdefault(roots[root], set()).add(
                            DetectionEvidence(unit.relative_path, IMPORT_RULE)
                        )
        return FrameworkObservation(
            DetectionReport(
                tuple(
                    TechnologyDetection(
                        name,
                        None,
                        tuple(
                            sorted(
                                references,
                                key=lambda item: (item.relative_path, item.rule_id),
                            )
                        ),
                    )
                    for name, references in sorted(found.items())
                )
            )
        )
