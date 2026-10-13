"""Static BullMQ technology observation for adapter selection."""

from __future__ import annotations

from rkg.adapters import DetectionReport, ParseResult
from rkg.detection.contracts import FrameworkObservation
from rkg.ingestion import SourceManifest


class BullMQDetector:
    """Surface bullmq evidence so deep selection can run."""

    def detect(
        self, manifest: SourceManifest, parsed: ParseResult
    ) -> FrameworkObservation:
        from rkg.adapters.bullmq_messaging import BullMQMessagingAdapter

        report: DetectionReport = BullMQMessagingAdapter().detect(manifest, parsed)
        return FrameworkObservation(report)
