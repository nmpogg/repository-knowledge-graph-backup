# Detection handoff for TASK-RKG-009 and TASK-RKG-015

Register the language adapter and every available deep adapter in `AdapterRegistry`.
Call `select_adapters(manifest, parsed, language_adapter, registry, detectors)` with
`(PythonImportDetector(), FastAPIAppDetector())` for the initial Python profile.
The caller supplies detectors; `selection.py` does not branch on language, framework
or adapter ID. The result contains ordered technology support, all compatible deep
adapters, application candidates and a stable status/error code.

An adapter that requires a module-level application sets
`entrypoint_required = True` on the adapter instance. Detection then returns
`app_selection_required` for multiple candidates or `app_unresolved` for none.
`application_override` selects an exact `module:symbol` candidate;
`prior_application` preserves a valid choice on re-index. Do not publish a candidate
snapshot unless status is `ready`. A single candidate is selected automatically.

`FastAPIAppDetector` recognizes direct module-level `FastAPI()` assignment through
static import aliases and unique local parameterless factories. T-009 owns route/DI extraction and its framework adapter; its
adapter can reuse this detector. `SQLAlchemyDataAccessAdapter` (`rkg.sqlalchemy`)
is a data-access adapter with `entrypoint_required = False`; register it with the
other deep adapters. It does not add an application candidate.
`AIOKafkaMessagingAdapter` (`rkg.aiokafka`) is a messaging adapter with
`entrypoint_required = False`. Register it the same way. A verified aiokafka
`>=0.8,<1.0` lock is required before selection reports `supported_patterns`.
`PythonImportDetector` uses the explicit import ownership profile from T-007. A declaration alone remains
`detected_only`; version-constrained adapters need a verified version to become
supported.

FastAPI explicitly opts into static extraction for unknown versions. Its state
stays `version_unverified`, with executed adapter/capabilities and a persisted
warning. Known incompatible versions remain blocked. Other adapters remain strict.
