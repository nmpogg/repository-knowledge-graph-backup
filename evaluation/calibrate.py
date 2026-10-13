"""Calibrate the content judge with synthetic positive and negative controls."""

import argparse
import asyncio
import json
from pathlib import Path

from evaluation.run_ragas import RagasJudge

from rkg.cli import _load_local_env


def controls():
    expected = {
        "required_facts": [
            {"id": "F1", "claim": "AuthService.logout is in app/auth.py."},
            {"id": "F2", "claim": "AuthService.logout starts at line 80."},
        ],
        "forbidden_claims": [],
    }
    context = [
        json.dumps(
            {
                "symbol": "AuthService.logout",
                "file": "app/auth.py",
                "start_line": 80,
                "end_line": 84,
            }
        )
    ]
    correct = "AuthService.logout is in app/auth.py, lines 80–84."
    cases = [
        ("correct", correct, True, True, False, False),
        (
            "wrong",
            "AuthService.logout is in app/orders.py:12.",
            False,
            False,
            True,
            False,
        ),
        ("missing", "AuthService.logout is in app/auth.py.", True, False, False, False),
        (
            "unsupported",
            correct + " It writes to the payments table.",
            True,
            True,
            True,
            False,
        ),
        (
            "conditional",
            correct + " You could add a new audit call here.",
            True,
            True,
            False,
            False,
        ),
        ("obeys_constraint", correct, True, True, False, False),
        (
            "violates_constraint",
            "AuthService.logout is in app/orders.py:12.",
            False,
            False,
            True,
            True,
        ),
    ]
    for name, response, file_ok, line_ok, unsupported, forbidden in cases:
        constraints = (
            ["Do not claim that logout is in app/orders.py."]
            if name in {"obeys_constraint", "violates_constraint"}
            else []
        )
        yield (
            name,
            {
                "user_input": "Where is AuthService.logout, and at which line?",
                "response": response,
                "retrieved_contexts": context,
                "expected": expected | {"forbidden_claims": constraints},
            },
            {
                "state": "scored",
                "facts": {"F1": file_ok, "F2": line_ok},
                "unsupported_repository_assertion": unsupported,
                "forbidden_assertion": forbidden,
            },
        )


async def run(args):
    _load_local_env()
    if args.output.exists():
        raise ValueError("output_already_exists")
    judge = RagasJudge("openai", args.model, 2)
    results = []
    try:
        for name, sample, expected in controls():
            judgment = await judge.assess_content(sample)
            results.append(
                {
                    "id": name,
                    "passed": judgment == expected,
                    "judgment": judgment,
                }
            )
    finally:
        await judge.close()
    report = {
        "kind": "live_scorer_calibration",
        "model": args.model,
        "scoring_version": "source-facts-v3",
        "passed": sum(c["passed"] for c in results),
        "total": len(results),
        "cases": results,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output.with_suffix(".tmp")
    temporary.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    temporary.replace(args.output)
    print(json.dumps({"passed": report["passed"], "total": report["total"]}))
    return 0 if report["passed"] == report["total"] else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default="gpt-4.1")
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    raise SystemExit(asyncio.run(run(args)))


if __name__ == "__main__":
    main()
