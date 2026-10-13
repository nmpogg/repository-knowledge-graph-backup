"""Static pgx technology observation for adapter selection."""

from __future__ import annotations

from rkg.adapters import DetectionReport, ParseResult
from rkg.detection.contracts import FrameworkObservation
from rkg.ingestion import SourceManifest


class PgxDetector:
    """Surface pgx evidence so deep selection can run."""

    def detect(
        self, manifest: SourceManifest, parsed: ParseResult
    ) -> FrameworkObservation:
        from rkg.adapters.pgx_data import PgxDataAccessAdapter

        report: DetectionReport = PgxDataAccessAdapter().detect(manifest, parsed)
        return FrameworkObservation(report)
