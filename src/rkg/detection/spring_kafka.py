"""Static Spring Kafka technology observation for adapter selection."""

from __future__ import annotations

from rkg.adapters import DetectionReport, ParseResult
from rkg.detection.contracts import FrameworkObservation
from rkg.ingestion import SourceManifest


class SpringKafkaDetector:
    """Surface spring-kafka evidence so deep selection can run."""

    def detect(
        self, manifest: SourceManifest, parsed: ParseResult
    ) -> FrameworkObservation:
        from rkg.adapters.spring_kafka_messaging import SpringKafkaMessagingAdapter

        report: DetectionReport = SpringKafkaMessagingAdapter().detect(manifest, parsed)
        return FrameworkObservation(report)
