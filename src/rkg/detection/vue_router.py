"""Static Vue Router technology observation for adapter selection."""

from __future__ import annotations

from rkg.adapters import DetectionReport, ParseResult
from rkg.detection.contracts import FrameworkObservation
from rkg.ingestion import SourceManifest


class VueRouterDetector:
    """Surface vue-router evidence so deep selection can run with rkg.vue."""

    def detect(
        self, manifest: SourceManifest, parsed: ParseResult
    ) -> FrameworkObservation:
        from rkg.adapters.vue_router_framework import VueRouterFrameworkAdapter

        report: DetectionReport = VueRouterFrameworkAdapter().detect(manifest, parsed)
        return FrameworkObservation(report)
