"""Technology detection and registry-driven adapter selection."""

from rkg.detection.contracts import ApplicationCandidate
from rkg.detection.fastapi import FastAPIAppDetector
from rkg.detection.flask import FlaskAppDetector
from rkg.detection.python_imports import PythonImportDetector
from rkg.detection.selection import (
    DetectionState,
    SelectionResult,
    TechnologySupport,
    select_adapters,
)

__all__ = [
    "ApplicationCandidate",
    "DetectionState",
    "FastAPIAppDetector",
    "FlaskAppDetector",
    "PythonImportDetector",
    "SelectionResult",
    "TechnologySupport",
    "select_adapters",
]
