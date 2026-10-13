"""Generic observations emitted by syntax-specific technology detectors."""

from __future__ import annotations

from dataclasses import dataclass

from rkg.adapters import DetectionReport


@dataclass(frozen=True, slots=True)
class ApplicationCandidate:
    reference: str
    relative_path: str
    line: int
    rule_id: str


@dataclass(frozen=True, slots=True)
class FrameworkObservation:
    report: DetectionReport
    applications: tuple[ApplicationCandidate, ...] = ()
