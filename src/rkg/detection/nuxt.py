"""Static Nuxt technology observation for Vue adapter selection."""

from __future__ import annotations

from rkg.adapters import DetectionReport, ParseResult
from rkg.detection.contracts import FrameworkObservation
from rkg.ingestion import SourceManifest


class NuxtDetector:
    """Surface nuxt evidence so deep selection can run with rkg.vue."""

    def detect(
        self, manifest: SourceManifest, parsed: ParseResult
    ) -> FrameworkObservation:
        from rkg.adapters.nuxt_framework import NuxtFrameworkAdapter

        report: DetectionReport = NuxtFrameworkAdapter().detect(manifest, parsed)
        return FrameworkObservation(report)
