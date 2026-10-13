"""Static React Router technology observation for TypeScript adapter selection."""

from __future__ import annotations

from rkg.adapters import DetectionReport, ParseResult
from rkg.detection.contracts import FrameworkObservation
from rkg.ingestion import SourceManifest


class ReactRouterDetector:
    """Surface react-router-dom evidence so deep selection can run."""

    def detect(
        self, manifest: SourceManifest, parsed: ParseResult
    ) -> FrameworkObservation:
        from rkg.adapters.react_router_framework import ReactRouterFrameworkAdapter

        report: DetectionReport = ReactRouterFrameworkAdapter().detect(manifest, parsed)
        return FrameworkObservation(report)
