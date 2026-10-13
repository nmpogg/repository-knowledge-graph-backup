"""Static Spring Web MVC technology observation for adapter selection."""

from __future__ import annotations

from rkg.adapters import DetectionReport, ParseResult
from rkg.detection.contracts import FrameworkObservation
from rkg.ingestion import SourceManifest


class SpringFrameworkDetector:
    """Surface spring-web evidence so deep selection can run."""

    def detect(
        self, manifest: SourceManifest, parsed: ParseResult
    ) -> FrameworkObservation:
        from rkg.adapters.spring_framework import SpringFrameworkAdapter

        report: DetectionReport = SpringFrameworkAdapter().detect(manifest, parsed)
        return FrameworkObservation(report)
