#!/usr/bin/env python3
"""Generate deterministic AR-P003 v0.3 reviewer-case assignments.

Case exposure is balanced first. Condition labels are then assigned with a
balanced bipartite edge-coloring procedure so every reviewer and every case is
split across control/receipt as evenly as mathematically possible.
"""

from __future__ import annotations

import argparse
import json
import random
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


VALID_CONDITIONS = ("control", "receipt")
ASSIGNMENT_VERSION = "AR-P003-v0.3-draft-assignment-v0.2"
BALANCE_METHOD = "balanced_bipartite_edge_coloring_v1"


def _validate_config(config: dict[str, Any]) -> tuple[list[str], list[dict[str, Any]], int, int]:
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

    return reviewers, cases, cases_per_reviewer, seed


def _select_reviewer_case_edges(
    reviewers: list[str],
    cases: list[dict[str, Any]],
    cases_per_reviewer: int,
    rng: random.Random,
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    """Select cases per reviewer while keeping case exposure nearly equal."""
    case_ids = [case["case_id"] for case in cases]
    reviewer_order = reviewers[:]
    rng.shuffle(reviewer_order)

    exposure = {case_id: 0 for case_id in case_ids}
    rows: list[dict[str, Any]] = []

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

        for order, case in enumerate(selected, start=1):
            case_id = case["case_id"]
            rows.append(
                {
                    "reviewer_id": reviewer,
                    "case_id": case_id,
                    "stratum": case["stratum"],
                    "order": order,
                }
            )
            exposure[case_id] += 1

    return rows, exposure


def _balanced_condition_labels(
    rows: list[dict[str, Any]],
    rng: random.Random,
) -> dict[int, str]:
    """2-color reviewer-case incidence edges with local imbalance <= 1.

    The reviewer/case incidence structure is a bipartite graph. To make every
    vertex even-degree, odd reviewer vertices are connected to one dummy case,
    odd case vertices are connected to one dummy reviewer, and (when needed)
    the two dummy vertices are connected to each other. Every resulting
    component is Eulerian and bipartite.

    Alternating control/receipt labels along each Euler circuit gives equal
    color degree at every even-degree vertex. Removing the one dummy edge from
    an originally odd-degree vertex leaves a real-edge imbalance of exactly
    one at most.

    This guarantees:
      - reviewer condition imbalance <= 1;
      - case condition imbalance <= 1.

    Dummy edges are never emitted as assignments.
    """

    edges: list[dict[str, Any]] = []
    adjacency: dict[tuple[str, str], list[int]] = defaultdict(list)
    degrees: Counter[tuple[str, str]] = Counter()

    def add_edge(
        u: tuple[str, str],
        v: tuple[str, str],
        *,
        row_index: int | None,
        dummy: bool,
    ) -> None:
        edge_id = len(edges)
        edges.append(
            {
                "u": u,
                "v": v,
                "row_index": row_index,
                "dummy": dummy,
            }
        )
        adjacency[u].append(edge_id)
        adjacency[v].append(edge_id)
        degrees[u] += 1
        degrees[v] += 1

    for row_index, row in enumerate(rows):
        add_edge(
            ("reviewer", row["reviewer_id"]),
            ("case", row["case_id"]),
            row_index=row_index,
            dummy=False,
        )

    reviewer_vertices = [
        vertex for vertex in degrees if vertex[0] == "reviewer"
    ]
    case_vertices = [vertex for vertex in degrees if vertex[0] == "case"]

    odd_reviewers = [
        vertex for vertex in reviewer_vertices if degrees[vertex] % 2 == 1
    ]
    odd_cases = [
        vertex for vertex in case_vertices if degrees[vertex] % 2 == 1
    ]

    dummy_case = ("dummy_case", "__condition_balance__")
    dummy_reviewer = ("dummy_reviewer", "__condition_balance__")

    for reviewer_vertex in odd_reviewers:
        add_edge(
            reviewer_vertex,
            dummy_case,
            row_index=None,
            dummy=True,
        )

    for case_vertex in odd_cases:
        add_edge(
            dummy_reviewer,
            case_vertex,
            row_index=None,
            dummy=True,
        )

    # The number of odd vertices in each bipartite partition has the same
    # parity as the number of real edges. If those counts are odd, the two
    # dummy vertices are also odd and one final dummy edge makes both even.
    if len(odd_reviewers) % 2 == 1:
        add_edge(
            dummy_reviewer,
            dummy_case,
            row_index=None,
            dummy=True,
        )

    odd_after = [
        (vertex, degree)
        for vertex, degree in degrees.items()
        if degree % 2 == 1
    ]
    if odd_after:
        raise AssertionError(
            f"internal error: Eulerized assignment graph still has odd degrees: "
            f"{odd_after!r}"
        )

    # Randomize adjacency and component order deterministically from the
    # assignment seed so there is no fixed lexical color preference.
    for edge_ids in adjacency.values():
        rng.shuffle(edge_ids)
    vertices = list(adjacency)
    rng.shuffle(vertices)

    used: set[int] = set()
    condition_by_row: dict[int, str] = {}

    for start in vertices:
        if not any(edge_id not in used for edge_id in adjacency[start]):
            continue

        # Hierholzer's algorithm. Each stack item stores the vertex and the
        # edge used to enter it. Backtracking yields the Euler circuit edges in
        # reverse order.
        stack: list[tuple[tuple[str, str], int | None]] = [(start, None)]
        reversed_circuit: list[int] = []

        while stack:
            vertex, _ = stack[-1]

            while adjacency[vertex] and adjacency[vertex][-1] in used:
                adjacency[vertex].pop()

            if adjacency[vertex]:
                edge_id = adjacency[vertex].pop()
                if edge_id in used:
                    continue
                used.add(edge_id)

                edge = edges[edge_id]
                next_vertex = (
                    edge["v"] if edge["u"] == vertex else edge["u"]
                )
                stack.append((next_vertex, edge_id))
            else:
                _, incoming_edge = stack.pop()
                if incoming_edge is not None:
                    reversed_circuit.append(incoming_edge)

        circuit = list(reversed(reversed_circuit))
        if len(circuit) % 2 != 0:
            raise AssertionError(
                "internal error: Euler circuit in bipartite graph has odd length"
            )

        start_offset = rng.randrange(2)
        for position, edge_id in enumerate(circuit):
            condition = VALID_CONDITIONS[(position + start_offset) % 2]
            edge = edges[edge_id]
            if edge["dummy"]:
                continue

            row_index = edge["row_index"]
            if not isinstance(row_index, int):
                raise AssertionError("real assignment edge has no row index")
            if row_index in condition_by_row:
                raise AssertionError("assignment edge received two conditions")
            condition_by_row[row_index] = condition

    if len(condition_by_row) != len(rows):
        missing = sorted(set(range(len(rows))) - set(condition_by_row))
        raise AssertionError(
            f"internal error: condition assignment missed rows {missing!r}"
        )

    return condition_by_row


def _diagnostics(
    assignments: list[dict[str, Any]],
    exposure: dict[str, int],
) -> dict[str, Any]:
    case_condition: dict[str, dict[str, int]] = {
        case_id: {"control": 0, "receipt": 0}
        for case_id in exposure
    }
    reviewer_condition: dict[str, dict[str, int]] = {}
    stratum_condition: dict[str, dict[str, int]] = {}

    for row in assignments:
        reviewer = row["reviewer_id"]
        case_id = row["case_id"]
        stratum = row["stratum"]
        condition = row["condition"]

        reviewer_condition.setdefault(
            reviewer, {"control": 0, "receipt": 0}
        )[condition] += 1
        case_condition[case_id][condition] += 1
        stratum_condition.setdefault(
            stratum, {"control": 0, "receipt": 0}
        )[condition] += 1

    reviewer_imbalances = {
        reviewer: abs(counts["control"] - counts["receipt"])
        for reviewer, counts in reviewer_condition.items()
    }
    case_imbalances = {
        case_id: abs(counts["control"] - counts["receipt"])
        for case_id, counts in case_condition.items()
    }

    return {
        "balance_method": BALANCE_METHOD,
        "case_exposure": exposure,
        "case_condition_counts": case_condition,
        "reviewer_condition_counts": reviewer_condition,
        "stratum_condition_counts": stratum_condition,
        "max_case_exposure_imbalance": (
            max(exposure.values()) - min(exposure.values())
            if exposure
            else 0
        ),
        "max_case_condition_imbalance": max(case_imbalances.values(), default=0),
        "max_reviewer_condition_imbalance": max(
            reviewer_imbalances.values(), default=0
        ),
    }


def generate(config: dict[str, Any]) -> dict[str, Any]:
    reviewers, cases, cases_per_reviewer, seed = _validate_config(config)

    rng = random.Random(seed)
    rows, exposure = _select_reviewer_case_edges(
        reviewers,
        cases,
        cases_per_reviewer,
        rng,
    )
    condition_by_row = _balanced_condition_labels(rows, rng)

    assignments: list[dict[str, Any]] = []
    for row_index, row in enumerate(rows):
        assignments.append(
            {
                **row,
                "condition": condition_by_row[row_index],
            }
        )

    assignments = sorted(
        assignments,
        key=lambda row: (row["reviewer_id"], row["order"]),
    )
    diagnostics = _diagnostics(assignments, exposure)

    if diagnostics["max_case_exposure_imbalance"] > 1:
        raise AssertionError("case exposure imbalance exceeded 1")
    if diagnostics["max_case_condition_imbalance"] > 1:
        raise AssertionError("case condition imbalance exceeded 1")
    if diagnostics["max_reviewer_condition_imbalance"] > 1:
        raise AssertionError("reviewer condition imbalance exceeded 1")

    return {
        "assignment_version": ASSIGNMENT_VERSION,
        "seed": seed,
        "cases_per_reviewer": cases_per_reviewer,
        "assignments": assignments,
        "diagnostics": diagnostics,
    }


def _assert_balance(result: dict[str, Any]) -> None:
    diagnostics = result["diagnostics"]
    assert diagnostics["max_case_exposure_imbalance"] <= 1
    assert diagnostics["max_case_condition_imbalance"] <= 1
    assert diagnostics["max_reviewer_condition_imbalance"] <= 1

    for counts in diagnostics["case_condition_counts"].values():
        assert abs(counts["control"] - counts["receipt"]) <= 1
    for counts in diagnostics["reviewer_condition_counts"].values():
        assert abs(counts["control"] - counts["receipt"]) <= 1


def run_self_test() -> int:
    # Even reviewer/case degrees: exact 50/50 balance is achievable.
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
        counts = Counter(row["condition"] for row in rows)
        assert counts["control"] == 2
        assert counts["receipt"] == 2

    _assert_balance(result)

    # Mixed ordinary/challenge strata with even degrees should still preserve
    # exact reviewer/case condition balance for this balanced incidence design.
    mixed_cases = [
        *[
            {"case_id": f"o{i}", "stratum": "ordinary"}
            for i in range(1, 7)
        ],
        *[
            {"case_id": f"s{i}", "stratum": "stale_receipt"}
            for i in range(1, 3)
        ],
        *[
            {"case_id": f"i{i}", "stratum": "incomplete_receipt"}
            for i in range(1, 3)
        ],
        *[
            {"case_id": f"x{i}", "stratum": "conflicting_receipt"}
            for i in range(1, 3)
        ],
    ]
    mixed = generate(
        {
            "reviewers": [f"m{i}" for i in range(1, 13)],
            "cases": mixed_cases,
            "cases_per_reviewer": 6,
            "seed": 73917,
        }
    )
    _assert_balance(mixed)
    assert mixed["diagnostics"]["max_reviewer_condition_imbalance"] == 0
    assert mixed["diagnostics"]["max_case_condition_imbalance"] == 0
    assert set(mixed["diagnostics"]["stratum_condition_counts"]) == {
        "ordinary",
        "stale_receipt",
        "incomplete_receipt",
        "conflicting_receipt",
    }

    # Odd degrees cannot be split exactly, but every reviewer and case must
    # remain within one observation of balance.
    odd = generate(
        {
            "reviewers": [f"q{i}" for i in range(1, 8)],
            "cases": [
                {"case_id": f"k{i}", "stratum": "ordinary"}
                for i in range(1, 8)
            ],
            "cases_per_reviewer": 3,
            "seed": 11,
        }
    )
    _assert_balance(odd)
    assert odd["diagnostics"]["max_reviewer_condition_imbalance"] == 1
    assert odd["diagnostics"]["max_case_condition_imbalance"] == 1

    assert result == generate(config)
    assert mixed == generate(
        {
            "reviewers": [f"m{i}" for i in range(1, 13)],
            "cases": mixed_cases,
            "cases_per_reviewer": 6,
            "seed": 73917,
        }
    )

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
