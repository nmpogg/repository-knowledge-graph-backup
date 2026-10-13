"""Evaluation integrity checks; no provider calls or analyzed-source execution."""

import asyncio
import json
from types import SimpleNamespace

import pytest
from evaluation.run_ragas import (
    METRIC_NAMES,
    RagasJudge,
    citation_checks,
    persisted_report,
    summarize,
    trace_contexts,
    verdict,
)

from rkg.domain.models import Entity, EntityType
from rkg.graph.observation import collect_retrieval, observation_enabled, observe_entity


def row():
    return {
        "checks_pass": True,
        "status": "answered",
        "ragas": {
            name: {
                "state": "scored",
                "value": 5 if name in {"case_rubric", "readability"} else 1,
            }
            for name in METRIC_NAMES
        },
    }


def test_observation_nested_scopes_and_exception_cleanup():
    entity = Entity("id", "repo", "snap", EntityType.CALLABLE, "f", "module.f")
    assert not observation_enabled()
    with collect_retrieval() as outer:
        observe_entity(entity)
        try:
            with collect_retrieval() as inner:
                assert not inner.entities
                raise RuntimeError
        except RuntimeError:
            pass
        assert outer.entities == {"id": entity}
        assert "module.f" in trace_contexts(outer)[0]
    assert not observation_enabled()


def test_report_omits_samples_and_transcripts():
    sample = row() | {"_sample": {"response": "private transcript"}}
    report = {"cases": [{"turns": [sample]}]}
    saved = persisted_report(report)
    assert "_sample" not in saved["cases"][0]["turns"][0]
    assert "_sample" in sample


def test_calibration_saves_controls_without_turns_or_transcripts(monkeypatch, tmp_path):
    from evaluation import calibrate

    controls = iter(calibrate.controls())

    class Judge:
        def __init__(self, *args):
            pass

        async def assess_content(self, sample):
            _, expected_sample, judgment = next(controls)
            assert sample == expected_sample
            return judgment

        async def close(self):
            pass

    monkeypatch.setattr(calibrate, "RagasJudge", Judge)
    monkeypatch.setattr(calibrate, "_load_local_env", lambda: None)
    output = tmp_path / "results" / "calibration.json"
    args = SimpleNamespace(output=output, model="test-model")
    assert asyncio.run(calibrate.run(args)) == 0
    report = json.loads(output.read_text())
    assert report["passed"] == report["total"] == 7
    assert all(set(case) == {"id", "passed", "judgment"} for case in report["cases"])
    assert not output.with_suffix(".tmp").exists()
    with pytest.raises(ValueError, match="output_already_exists"):
        asyncio.run(calibrate.run(args))


def test_missing_fact_and_unsupported_claim_cannot_pass():
    sample = row()
    assert verdict(sample) == "pass"
    sample["ragas"]["required_fact_recall"]["value"] = 0.9
    assert verdict(sample) == "fail"
    sample = row()
    sample["ragas"]["faithfulness"]["value"] = 0.99
    assert verdict(sample) == "fail"


def test_metric_error_is_unscored_and_readability_is_separate():
    sample = row()
    sample["ragas"]["readability"]["value"] = 1
    assert verdict(sample) == "pass"
    sample["ragas"]["case_rubric"] = {"state": "error", "value": None}
    assert verdict(sample) == "unscored"


def test_denominator_includes_unscored_cases_and_graph_mutation_fails():
    good = {
        "category": "answerable",
        "repository": "repo",
        "graph_unchanged": True,
        "turns": [row()],
    }
    bad = {
        "category": "answerable",
        "repository": "repo",
        "graph_unchanged": False,
        "turns": [row()],
    }
    unknown = {
        "category": "answerable",
        "repository": "repo",
        "graph_unchanged": True,
        "turns": [{"checks_pass": True, "status": "answered"}],
    }
    result = summarize([good, bad, unknown])
    assert result["answerable_denominator"] == 3
    assert result["answerable_judged"] == 2
    assert result["estimated_answerable_accuracy"] == 1 / 3


def test_no_judge_scores_does_not_report_zero_accuracy():
    case = {
        "category": "answerable",
        "repository": "repo",
        "graph_unchanged": True,
        "turns": [{"checks_pass": False, "status": "failed"}],
    }
    result = summarize([case])
    assert result["observed_answerable_pass_rate"] == 0
    assert result["estimated_answerable_accuracy"] is None
    assert result["quality_assessment"] == "unavailable"


def test_metric_receives_only_observed_context_and_returns_safe_error():
    class BrokenMetric:
        async def ascore(self, **kwargs):
            assert kwargs["retrieved_contexts"] == ["observed"]
            assert "reference" not in kwargs
            raise RuntimeError("private response")

    judge = object.__new__(RagasJudge)
    judge.metrics = {"faithfulness": BrokenMetric()}
    judge.semaphore = asyncio.Semaphore(1)
    sample = {
        "user_input": "q",
        "response": "a",
        "reference": "gold",
        "retrieved_contexts": ["observed"],
    }
    result = asyncio.run(judge.score("faithfulness", sample))
    assert result == {"state": "error", "value": None, "reason_code": "RuntimeError"}


def test_empty_context_is_not_a_perfect_faithfulness_score():
    judge = object.__new__(RagasJudge)
    result = asyncio.run(judge.score("faithfulness", {"retrieved_contexts": []}))
    assert result["state"] == "not_applicable"
    assert result["value"] is None


def test_score_row_removes_transcript_after_scoring():
    judge = object.__new__(RagasJudge)

    async def score(name, sample):
        return {"state": "scored", "value": 1}

    async def assess(sample):
        return {
            "state": "scored",
            "facts": {"f": True},
            "unsupported_repository_assertion": False,
            "forbidden_assertion": False,
        }

    judge.score = score
    judge.assess_content = assess
    sample = {"status": "answered", "_sample": {"response": "private"}}
    asyncio.run(judge.score_row(sample))
    assert "_sample" not in sample
    assert set(sample["ragas"]) == set(METRIC_NAMES)


def test_optional_ragas_dependencies_construct_real_metrics(monkeypatch):
    monkeypatch.setenv("RAGAS_DO_NOT_TRACK", "true")
    pytest.importorskip("ragas")
    monkeypatch.setenv("OPENAI_API_KEY", "synthetic-evaluation-key")
    judge = RagasJudge("openai", "gpt-4o-mini")
    assert set(judge.metrics) == set(METRIC_NAMES)
    assert all(callable(metric.ascore) for metric in judge.metrics.values())
    asyncio.run(judge.close())


@pytest.mark.parametrize(
    "field,value",
    [
        ("entity_id", "wrong-target"),
        ("edge_id", "unobserved-edge"),
        ("evidence_id", "unobserved-evidence"),
    ],
)
def test_unobserved_or_wrong_direction_citation_fails(monkeypatch, field, value):
    monkeypatch.setattr(
        "evaluation.run_ragas.exact_citation", lambda *args: {"snapshot_id": "snap"}
    )
    conversation = SimpleNamespace(id="conv", snapshot_id="snap")
    citation = {"edge_id": "edge", "entity_id": "target", "evidence_id": "ev"}
    turn = SimpleNamespace(
        id="turn",
        citations=[citation],
        claims=[{"edge_id": "edge", "citation_indexes": [0]}],
    )
    trace = SimpleNamespace(
        contexts=[
            SimpleNamespace(
                edges=[
                    SimpleNamespace(id="edge", target_id="target", evidence_ids=("ev",))
                ],
                evidence=[SimpleNamespace(id="ev")],
            )
        ]
    )
    assert citation_checks(None, conversation, turn, trace)["pass"]
    citation[field] = value
    assert not citation_checks(None, conversation, turn, trace)["pass"]


@pytest.mark.parametrize(
    "change,expected",
    [
        ({}, "pass"),
        ({"facts": {"file": True, "line": False}}, "fail"),
        ({"unsupported_repository_assertion": True}, "fail"),
        ({"forbidden_assertion": True}, "fail"),
        ({"state": "error", "reason_code": "AuthenticationError"}, "unscored"),
    ],
)
def test_source_fact_verdict_rejects_partial_or_invented_answers(change, expected):
    sample = row()
    sample["content_judgment"] = {
        "state": "scored",
        "facts": {"file": True, "line": True},
        "unsupported_repository_assertion": False,
        "forbidden_assertion": False,
    } | change
    assert verdict(sample) == expected
    sample["checks_pass"] = False
    assert verdict(sample) == "fail"


@pytest.mark.parametrize("ids", [["F1"], ["F1", "F1"], ["F1", "F2", "invented"]])
def test_judge_rejects_missing_duplicate_or_unknown_fact_ids(ids):
    class StubLLM:
        async def agenerate(self, prompt, model):
            return model(
                facts=[{"fact_id": i, "correct": True} for i in ids],
                unsupported_repository_assertion=False,
                forbidden_assertion=False,
            )

    judge = object.__new__(RagasJudge)
    judge.llm = StubLLM()
    judge.semaphore = asyncio.Semaphore(1)
    sample = {
        "user_input": "Where is f?",
        "response": "app.py:3",
        "retrieved_contexts": ["f in app.py:3"],
        "expected": {
            "required_facts": [
                {"id": "F1", "claim": "f is in app.py"},
                {"id": "F2", "claim": "f starts at line 3"},
            ],
            "forbidden_claims": [],
        },
    }
    assert asyncio.run(judge.assess_content(sample)) == {
        "state": "error",
        "reason_code": "ValueError",
    }


@pytest.mark.parametrize(
    "passed,answerable,state",
    [(45, 27, "passed"), (44, 27, "failed"), (45, 26, "failed")],
)
def test_ninety_percent_target_requires_both_denominators(passed, answerable, state):
    from evaluation.run_ragas import target_assessment

    summary = {
        "case_count": 50,
        "verdicts": {"pass": passed},
        "content_judgment_errors": 0,
        "quality_assessment": "available",
        "estimated_answerable_accuracy": answerable / 29,
        "observed_answerable_pass_rate": answerable / 29,
    }
    assert target_assessment(summary)["state"] == state
    summary["content_judgment_errors"] = 1
    assert target_assessment(summary)["state"] == "unavailable"
