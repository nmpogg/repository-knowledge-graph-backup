"""Static kafka-go technology observation for adapter selection."""

from __future__ import annotations

from rkg.adapters import DetectionReport, ParseResult
from rkg.detection.contracts import FrameworkObservation
from rkg.ingestion import SourceManifest


class KafkaGoDetector:
    """Surface kafka-go evidence so deep selection can run."""

    def detect(
        self, manifest: SourceManifest, parsed: ParseResult
    ) -> FrameworkObservation:
        from rkg.adapters.kafka_go_messaging import KafkaGoMessagingAdapter

        report: DetectionReport = KafkaGoMessagingAdapter().detect(manifest, parsed)
        return FrameworkObservation(report)
