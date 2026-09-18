#!/usr/bin/env python3
"""Generate deterministic AR-P003 v0.3 reviewer-case assignments."""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path
from typing import Any


VALID_CONDITIONS = ("control", "receipt")


def generate(config: dict[str, Any]) -> dict[str, Any]:
    reviewers = config.get("reviewers")
    cases = config.get("cases")
    cases_per_reviewer = config.get("cases_per_reviewer")
    seed = config.get("seed")

    if (
        not isinstance(reviewers, list)
        or not reviewers
        or not all(isinstance(item, str) and item for item in reviewers)
    ):
        raise ValueError("reviewers must be a non-empty list of strings")
    if len(set(reviewers)) != len(reviewers):
        raise ValueError("reviewer IDs must be unique")

    if not isinstance(cases, list) or not cases:
        raise ValueError("cases must be a non-empty list")

    case_ids: list[str] = []
    for case in cases:
        if (
            not isinstance(case, dict)
            or not isinstance(case.get("case_id"), str)
            or not case["case_id"]
        ):
            raise ValueError("each case must contain a non-empty case_id")
        if not isinstance(case.get("stratum"), str) or not case["stratum"]:
            raise ValueError("each case must contain a non-empty stratum")
        case_ids.append(case["case_id"])

    if len(set(case_ids)) != len(case_ids):
        raise ValueError("case IDs must be unique")

    if (
        not isinstance(cases_per_reviewer, int)
        or isinstance(cases_per_reviewer, bool)
        or cases_per_reviewer < 1
        or cases_per_reviewer > len(cases)
    ):
        raise ValueError(
            "cases_per_reviewer must be an integer between 1 and number of cases"
        )

    if not isinstance(seed, int) or isinstance(seed, bool):
        raise ValueError("seed must be an integer")

    rng = random.Random(seed)
    reviewer_order = reviewers[:]
    rng.shuffle(reviewer_order)

    exposure = {case_id: 0 for case_id in case_ids}
    case_condition = {
        case_id: {"control": 0, "receipt": 0}
        for case_id in case_ids
    }
    assignments: list[dict[str, Any]] = []

    for reviewer in reviewer_order:
        tie_break = {case_id: rng.random() for case_id in case_ids}

        selected = sorted(
            cases,
            key=lambda case: (
                exposure[case["case_id"]],
                tie_break[case["case_id"]],
            ),
        )[:cases_per_reviewer]
        rng.shuffle(selected)

        reviewer_counts = {"control": 0, "receipt": 0}
        rows: list[dict[str, Any]] = []

        for order, case in enumerate(selected, start=1):
            case_id = case["case_id"]
            global_counts = {
                condition: sum(
                    case_condition[item][condition] for item in case_ids
                )
                for condition in VALID_CONDITIONS
            }

            options = list(VALID_CONDITIONS)
            rng.shuffle(options)
            condition = min(
                options,
                key=lambda candidate: (
                    case_condition[case_id][candidate],
                    reviewer_counts[candidate],
                    global_counts[candidate],
                ),
            )

            rows.append(
                {
                    "reviewer_id": reviewer,
                    "case_id": case_id,
                    "stratum": case["stratum"],
                    "condition": condition,
                    "order": order,
                }
            )

            exposure[case_id] += 1
            case_condition[case_id][condition] += 1
            reviewer_counts[condition] += 1

        assignments.extend(rows)

    return {
        "assignment_version": "AR-P003-v0.3-draft",
        "seed": seed,
        "cases_per_reviewer": cases_per_reviewer,
        "assignments": sorted(
            assignments,
            key=lambda row: (row["reviewer_id"], row["order"]),
        ),
        "diagnostics": {
            "case_exposure": exposure,
            "case_condition_counts": case_condition,
        },
    }


def run_self_test() -> int:
    config = {
        "reviewers": [f"r{i}" for i in range(1, 9)],
        "cases": [
            {"case_id": f"c{i}", "stratum": "ordinary"}
            for i in range(1, 9)
        ],
        "cases_per_reviewer": 4,
        "seed": 73917,
    }

    result = generate(config)
    assignments = result["assignments"]
    assert len(assignments) == 32

    for reviewer in config["reviewers"]:
        rows = [row for row in assignments if row["reviewer_id"] == reviewer]
        assert len(rows) == 4
        assert len({row["case_id"] for row in rows}) == 4
        assert [row["order"] for row in rows] == [1, 2, 3, 4]

    exposures = list(result["diagnostics"]["case_exposure"].values())
    assert max(exposures) - min(exposures) <= 1

    for counts in result["diagnostics"]["case_condition_counts"].values():
        assert abs(counts["control"] - counts["receipt"]) <= 1

    assert result == generate(config)
    print("AR-P003 assignment-generator self-test passed.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate deterministic AR-P003 reviewer/case assignments."
    )
    parser.add_argument("config", nargs="?", help="JSON configuration file")
    parser.add_argument("--output", help="Write assignments to this JSON file")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        return run_self_test()

    if not args.config:
        parser.error("provide a config JSON file or use --self-test")

    try:
        config = json.loads(Path(args.config).read_text(encoding="utf-8"))
        if not isinstance(config, dict):
            raise ValueError("config must contain a JSON object")
        result = generate(config)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        parser.error(str(exc))

    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        Path(args.output).write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
