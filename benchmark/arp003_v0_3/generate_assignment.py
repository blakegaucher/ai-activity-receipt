#!/usr/bin/env python3
"""Generate deterministic AR-P003 v0.3 three-condition reviewer-case assignments.

Case exposure is balanced first. Conditions are then assigned with a
deterministic equitable bipartite b-matching procedure so each reviewer and
case receives raw / structured / receipt conditions as evenly as possible.

This is development-only methodology infrastructure. It does not freeze the
final reviewer/case counts, assignment seed, or stopping rule.
"""

from __future__ import annotations

import argparse
import json
import random
from collections import Counter, defaultdict, deque
from pathlib import Path
from typing import Any


VALID_CONDITIONS = ("raw", "structured", "receipt")
ASSIGNMENT_VERSION = "AR-P003-v0.3-draft-assignment-v0.3"
BALANCE_METHOD = "equitable_three_condition_b_matching_v1"


def _validate_config(
    config: dict[str, Any],
) -> tuple[list[str], list[dict[str, Any]], int, int]:
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


class _Dinic:
    def __init__(self, n: int) -> None:
        self.graph: list[list[list[int]]] = [[] for _ in range(n)]

    def add_edge(self, u: int, v: int, cap: int) -> tuple[int, int]:
        forward = [v, cap, len(self.graph[v])]
        reverse = [u, 0, len(self.graph[u])]
        self.graph[u].append(forward)
        self.graph[v].append(reverse)
        return u, len(self.graph[u]) - 1

    def max_flow(self, source: int, sink: int) -> int:
        total = 0
        n = len(self.graph)
        while True:
            level = [-1] * n
            level[source] = 0
            queue: deque[int] = deque([source])
            while queue:
                u = queue.popleft()
                for v, cap, _ in self.graph[u]:
                    if cap > 0 and level[v] < 0:
                        level[v] = level[u] + 1
                        queue.append(v)
            if level[sink] < 0:
                return total

            it = [0] * n

            def dfs(u: int, pushed: int) -> int:
                if u == sink:
                    return pushed
                while it[u] < len(self.graph[u]):
                    edge = self.graph[u][it[u]]
                    v, cap, rev = edge
                    if cap > 0 and level[v] == level[u] + 1:
                        flow = dfs(v, min(pushed, cap))
                        if flow:
                            edge[1] -= flow
                            self.graph[v][rev][1] += flow
                            return flow
                    it[u] += 1
                return 0

            while True:
                pushed = dfs(source, 10**9)
                if not pushed:
                    break
                total += pushed


def _choose_equitable_subset(
    rows: list[dict[str, Any]],
    remaining: list[int],
    *,
    remaining_conditions: int,
    rng: random.Random,
) -> set[int]:
    """Choose one condition's edges with floor/ceil degree balance.

    This is a feasible lower/upper-bound bipartite b-matching. Each reviewer
    and case receives either floor(d/k) or ceil(d/k) selected edges when d
    incident edges remain and k conditions remain. The selected global count
    is similarly constrained to floor(E/k) or ceil(E/k).
    """

    reviewer_degree: Counter[str] = Counter()
    case_degree: Counter[str] = Counter()
    for index in remaining:
        reviewer_degree[rows[index]["reviewer_id"]] += 1
        case_degree[rows[index]["case_id"]] += 1

    reviewers = sorted(reviewer_degree)
    cases = sorted(case_degree)

    # Shuffle insertion order deterministically so no lexical condition bias is
    # baked into otherwise equivalent feasible solutions.
    edge_order = remaining[:]
    rng.shuffle(edge_order)

    node_names = (
        ["__source__"]
        + [f"r:{x}" for x in reviewers]
        + [f"c:{x}" for x in cases]
        + ["__sink__"]
    )
    node_index = {name: i for i, name in enumerate(node_names)}
    source = node_index["__source__"]
    sink = node_index["__sink__"]

    base_n = len(node_names)
    super_source = base_n
    super_sink = base_n + 1
    flow = _Dinic(base_n + 2)
    demand = [0] * base_n

    edge_refs: dict[int, tuple[int, int]] = {}

    def add_lower_edge(u: int, v: int, low: int, high: int) -> tuple[int, int]:
        if low < 0 or high < low:
            raise AssertionError("invalid lower/upper capacity")
        ref = flow.add_edge(u, v, high - low)
        demand[u] -= low
        demand[v] += low
        return ref

    for reviewer in reviewers:
        degree = reviewer_degree[reviewer]
        low = degree // remaining_conditions
        high = (degree + remaining_conditions - 1) // remaining_conditions
        add_lower_edge(source, node_index[f"r:{reviewer}"], low, high)

    for index in edge_order:
        row = rows[index]
        ref = add_lower_edge(
            node_index[f"r:{row['reviewer_id']}"],
            node_index[f"c:{row['case_id']}"],
            0,
            1,
        )
        edge_refs[index] = ref

    for case_id in cases:
        degree = case_degree[case_id]
        low = degree // remaining_conditions
        high = (degree + remaining_conditions - 1) // remaining_conditions
        add_lower_edge(node_index[f"c:{case_id}"], sink, low, high)

    total_edges = len(remaining)
    total_low = total_edges // remaining_conditions
    total_high = (total_edges + remaining_conditions - 1) // remaining_conditions
    add_lower_edge(sink, source, total_low, total_high)

    required = 0
    for node, value in enumerate(demand):
        if value > 0:
            flow.add_edge(super_source, node, value)
            required += value
        elif value < 0:
            flow.add_edge(node, super_sink, -value)

    if flow.max_flow(super_source, super_sink) != required:
        raise AssertionError(
            "internal error: equitable three-condition b-matching was infeasible"
        )

    selected: set[int] = set()
    for row_index, (u, edge_pos) in edge_refs.items():
        # Capacity started at 1. Residual 0 means one unit was selected.
        if flow.graph[u][edge_pos][1] == 0:
            selected.add(row_index)

    if not total_low <= len(selected) <= total_high:
        raise AssertionError("internal error: selected condition size is imbalanced")
    return selected


def _balanced_condition_labels(
    rows: list[dict[str, Any]],
    rng: random.Random,
) -> dict[int, str]:
    condition_order = list(VALID_CONDITIONS)
    rng.shuffle(condition_order)

    remaining = list(range(len(rows)))
    assignment: dict[int, str] = {}

    for offset, condition in enumerate(condition_order[:-1]):
        remaining_conditions = len(condition_order) - offset
        selected = _choose_equitable_subset(
            rows,
            remaining,
            remaining_conditions=remaining_conditions,
            rng=rng,
        )
        for index in selected:
            assignment[index] = condition
        remaining = [index for index in remaining if index not in selected]

    last = condition_order[-1]
    for index in remaining:
        assignment[index] = last

    if len(assignment) != len(rows):
        raise AssertionError("internal error: not every row received a condition")
    return assignment


def _diagnostics(
    assignments: list[dict[str, Any]],
    exposure: dict[str, int],
) -> dict[str, Any]:
    zero_counts = {condition: 0 for condition in VALID_CONDITIONS}
    case_condition: dict[str, dict[str, int]] = {
        case_id: dict(zero_counts) for case_id in exposure
    }
    reviewer_condition: dict[str, dict[str, int]] = {}
    stratum_condition: dict[str, dict[str, int]] = {}

    for row in assignments:
        reviewer = row["reviewer_id"]
        case_id = row["case_id"]
        stratum = row["stratum"]
        condition = row["condition"]

        reviewer_condition.setdefault(reviewer, dict(zero_counts))[condition] += 1
        case_condition[case_id][condition] += 1
        stratum_condition.setdefault(stratum, dict(zero_counts))[condition] += 1

    def imbalance(counts: dict[str, int]) -> int:
        values = [counts[c] for c in VALID_CONDITIONS]
        return max(values) - min(values)

    reviewer_imbalances = {
        reviewer: imbalance(counts)
        for reviewer, counts in reviewer_condition.items()
    }
    case_imbalances = {
        case_id: imbalance(counts)
        for case_id, counts in case_condition.items()
    }
    overall = Counter(row["condition"] for row in assignments)

    return {
        "balance_method": BALANCE_METHOD,
        "conditions": list(VALID_CONDITIONS),
        "condition_counts": {
            condition: overall.get(condition, 0) for condition in VALID_CONDITIONS
        },
        "case_exposure": exposure,
        "case_condition_counts": case_condition,
        "reviewer_condition_counts": reviewer_condition,
        "stratum_condition_counts": stratum_condition,
        "max_case_exposure_imbalance": (
            max(exposure.values()) - min(exposure.values()) if exposure else 0
        ),
        "max_case_condition_imbalance": max(case_imbalances.values(), default=0),
        "max_reviewer_condition_imbalance": max(
            reviewer_imbalances.values(), default=0
        ),
        "max_overall_condition_imbalance": (
            max(overall.values()) - min(overall.values()) if overall else 0
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

    assignments = [
        {**row, "condition": condition_by_row[index]}
        for index, row in enumerate(rows)
    ]
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
    if diagnostics["max_overall_condition_imbalance"] > 1:
        raise AssertionError("overall condition imbalance exceeded 1")

    return {
        "assignment_version": ASSIGNMENT_VERSION,
        "seed": seed,
        "cases_per_reviewer": cases_per_reviewer,
        "conditions": list(VALID_CONDITIONS),
        "assignments": assignments,
        "diagnostics": diagnostics,
    }


def _assert_balance(result: dict[str, Any]) -> None:
    diagnostics = result["diagnostics"]
    assert diagnostics["max_case_exposure_imbalance"] <= 1
    assert diagnostics["max_case_condition_imbalance"] <= 1
    assert diagnostics["max_reviewer_condition_imbalance"] <= 1
    assert diagnostics["max_overall_condition_imbalance"] <= 1

    for counts in diagnostics["case_condition_counts"].values():
        values = [counts[c] for c in VALID_CONDITIONS]
        assert max(values) - min(values) <= 1
    for counts in diagnostics["reviewer_condition_counts"].values():
        values = [counts[c] for c in VALID_CONDITIONS]
        assert max(values) - min(values) <= 1


def run_self_test() -> int:
    # Degrees divisible by three: exact 1/3 balance is achievable.
    config = {
        "reviewers": [f"r{i}" for i in range(1, 10)],
        "cases": [
            {"case_id": f"c{i}", "stratum": "ordinary"}
            for i in range(1, 10)
        ],
        "cases_per_reviewer": 6,
        "seed": 73917,
    }
    result = generate(config)
    assignments = result["assignments"]
    assert result["assignment_version"] == ASSIGNMENT_VERSION
    assert result["conditions"] == list(VALID_CONDITIONS)
    assert len(assignments) == 54
    _assert_balance(result)

    for reviewer in config["reviewers"]:
        rows = [row for row in assignments if row["reviewer_id"] == reviewer]
        counts = Counter(row["condition"] for row in rows)
        assert [counts[c] for c in VALID_CONDITIONS] == [2, 2, 2]

    # Mixed strata remain balanced at reviewer/case level.
    mixed_cases = [
        *[
            {"case_id": f"o{i}", "stratum": "ordinary"}
            for i in range(1, 7)
        ],
        *[
            {"case_id": f"s{i}", "stratum": "stale_receipt"}
            for i in range(1, 4)
        ],
        *[
            {"case_id": f"i{i}", "stratum": "incomplete_receipt"}
            for i in range(1, 4)
        ],
        *[
            {"case_id": f"c{i}", "stratum": "conflicting_receipt"}
            for i in range(1, 4)
        ],
    ]
    mixed = generate(
        {
            "reviewers": [f"m{i}" for i in range(1, 16)],
            "cases": mixed_cases,
            "cases_per_reviewer": 6,
            "seed": 73917,
        }
    )
    _assert_balance(mixed)
    assert set(mixed["diagnostics"]["stratum_condition_counts"]) == {
        "ordinary",
        "stale_receipt",
        "incomplete_receipt",
        "conflicting_receipt",
    }
    for stratum_counts in mixed["diagnostics"]["stratum_condition_counts"].values():
        assert set(stratum_counts) == set(VALID_CONDITIONS)

    # Non-divisible degrees still differ by at most one per condition.
    odd = generate(
        {
            "reviewers": [f"q{i}" for i in range(1, 8)],
            "cases": [
                {"case_id": f"k{i}", "stratum": "ordinary"}
                for i in range(1, 8)
            ],
            "cases_per_reviewer": 4,
            "seed": 11,
        }
    )
    _assert_balance(odd)
    assert odd["diagnostics"]["max_reviewer_condition_imbalance"] == 1
    assert odd["diagnostics"]["max_case_condition_imbalance"] <= 1

    assert result == generate(config)
    print(
        "AR-P003 three-condition assignment-generator self-test passed: "
        "raw/structured/receipt balance is deterministic and equitable."
    )
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
