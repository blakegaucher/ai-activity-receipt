#!/usr/bin/env python3
"""Crossed reviewer x case Monte Carlo planning for AR-P003 v0.3.

This is development-only design planning. It simulates a binary endpoint under
reviewer and case random intercepts using the repository's balanced assignment
generator, then evaluates a simple condition contrast with two-way cluster-
robust covariance (reviewer + case - reviewer/case intersection).

The output is sensitivity evidence, not a frozen confirmatory sample size.
"""

from __future__ import annotations

import argparse
import json
import math
import random
import statistics
import sys
from pathlib import Path
from statistics import NormalDist
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from benchmark.arp003_v0_3.generate_assignment import generate  # noqa: E402

PLANNER_VERSION = "AR-P003-v0.3-crossed-planning-v0.1"


def _positive_int(value: Any, name: str, minimum: int = 1) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < minimum:
        raise ValueError(f"{name} must be an integer >= {minimum}")
    return value


def _finite(value: Any, name: str) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ValueError(f"{name} must be numeric")
    value = float(value)
    if not math.isfinite(value):
        raise ValueError(f"{name} must be finite")
    return value


def _probability(value: Any, name: str, *, open_interval: bool = False) -> float:
    value = _finite(value, name)
    if open_interval:
        if not 0.0 < value < 1.0:
            raise ValueError(f"{name} must be in (0, 1)")
    elif not 0.0 <= value <= 1.0:
        raise ValueError(f"{name} must be in [0, 1]")
    return value


def logit(p: float) -> float:
    p = _probability(p, "p", open_interval=True)
    return math.log(p / (1.0 - p))


def logistic(x: float) -> float:
    if x >= 0:
        e = math.exp(-x)
        return 1.0 / (1.0 + e)
    e = math.exp(x)
    return e / (1.0 + e)


def _mat2_mul(a: list[list[float]], b: list[list[float]]) -> list[list[float]]:
    return [
        [
            a[0][0] * b[0][0] + a[0][1] * b[1][0],
            a[0][0] * b[0][1] + a[0][1] * b[1][1],
        ],
        [
            a[1][0] * b[0][0] + a[1][1] * b[1][0],
            a[1][0] * b[0][1] + a[1][1] * b[1][1],
        ],
    ]


def _mat2_add(a: list[list[float]], b: list[list[float]], scale: float = 1.0) -> list[list[float]]:
    return [
        [a[0][0] + scale * b[0][0], a[0][1] + scale * b[0][1]],
        [a[1][0] + scale * b[1][0], a[1][1] + scale * b[1][1]],
    ]


def _xtx_inverse(n0: int, n1: int) -> list[list[float]]:
    n = n0 + n1
    if n0 <= 0 or n1 <= 0:
        raise ValueError("both conditions require at least one observation")
    # X = [1, treatment], so X'X = [[n, n1], [n1, n1]]
    det = float(n1 * n0)
    return [
        [n1 / det, -n1 / det],
        [-n1 / det, n / det],
    ]


def _cluster_meat(
    rows: list[dict[str, Any]],
    residuals: list[float],
    group_key: str,
) -> list[list[float]]:
    groups: dict[Any, list[float]] = {}
    for row, resid in zip(rows, residuals):
        key = row[group_key]
        treatment = 1.0 if row["condition"] == "receipt" else 0.0
        score = groups.setdefault(key, [0.0, 0.0])
        score[0] += resid
        score[1] += treatment * resid

    meat = [[0.0, 0.0], [0.0, 0.0]]
    for s0, s1 in groups.values():
        meat[0][0] += s0 * s0
        meat[0][1] += s0 * s1
        meat[1][0] += s1 * s0
        meat[1][1] += s1 * s1

    g = len(groups)
    n = len(rows)
    k = 2
    if g <= 1 or n <= k:
        raise ValueError(f"too few clusters/observations for {group_key}")
    correction = (g / (g - 1.0)) * ((n - 1.0) / (n - k))
    return [[value * correction for value in row] for row in meat]


def _intersection_meat(
    rows: list[dict[str, Any]],
    residuals: list[float],
) -> list[list[float]]:
    groups: dict[tuple[str, str], list[float]] = {}
    for row, resid in zip(rows, residuals):
        key = (row["reviewer_id"], row["case_id"])
        treatment = 1.0 if row["condition"] == "receipt" else 0.0
        score = groups.setdefault(key, [0.0, 0.0])
        score[0] += resid
        score[1] += treatment * resid

    meat = [[0.0, 0.0], [0.0, 0.0]]
    for s0, s1 in groups.values():
        meat[0][0] += s0 * s0
        meat[0][1] += s0 * s1
        meat[1][0] += s1 * s0
        meat[1][1] += s1 * s1

    g = len(groups)
    n = len(rows)
    k = 2
    if g <= 1 or n <= k:
        raise ValueError("too few reviewer/case intersections")
    correction = (g / (g - 1.0)) * ((n - 1.0) / (n - k))
    return [[value * correction for value in row] for row in meat]


def two_way_cluster_contrast(
    rows: list[dict[str, Any]],
    outcomes: list[int],
) -> dict[str, float]:
    if len(rows) != len(outcomes) or not rows:
        raise ValueError("rows and outcomes must be same non-zero length")

    control = [y for row, y in zip(rows, outcomes) if row["condition"] == "control"]
    receipt = [y for row, y in zip(rows, outcomes) if row["condition"] == "receipt"]
    if not control or not receipt:
        raise ValueError("both conditions require observations")

    p0 = statistics.fmean(control)
    p1 = statistics.fmean(receipt)
    beta = p1 - p0

    fitted = [p1 if row["condition"] == "receipt" else p0 for row in rows]
    residuals = [float(y) - fit for y, fit in zip(outcomes, fitted)]

    bread = _xtx_inverse(len(control), len(receipt))
    reviewer_meat = _cluster_meat(rows, residuals, "reviewer_id")
    case_meat = _cluster_meat(rows, residuals, "case_id")
    intersection_meat = _intersection_meat(rows, residuals)

    meat = _mat2_add(reviewer_meat, case_meat)
    meat = _mat2_add(meat, intersection_meat, scale=-1.0)

    cov = _mat2_mul(_mat2_mul(bread, meat), bread)
    variance = cov[1][1]
    se = math.sqrt(variance) if variance > 0 else float("nan")

    return {
        "p_control": p0,
        "p_receipt": p1,
        "risk_difference": beta,
        "two_way_cluster_se": se,
        "variance": variance,
    }


def _assignment_rows(
    reviewers: int,
    cases: int,
    cases_per_reviewer: int,
    seed: int,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    reviewer_ids = [f"R{i:04d}" for i in range(1, reviewers + 1)]
    case_defs = [
        {"case_id": f"C{i:04d}", "stratum": "ordinary"}
        for i in range(1, cases + 1)
    ]
    assignment = generate(
        {
            "reviewers": reviewer_ids,
            "cases": case_defs,
            "cases_per_reviewer": cases_per_reviewer,
            "seed": seed,
        }
    )
    rows = assignment["assignments"]
    return rows, assignment["diagnostics"]


def _simulate_once(
    rows: list[dict[str, Any]],
    rng: random.Random,
    *,
    conditional_p_control: float,
    conditional_p_receipt: float,
    reviewer_sd_logit: float,
    case_sd_logit: float,
) -> tuple[list[int], float, float]:
    base = logit(conditional_p_control)
    delta = logit(conditional_p_receipt) - base

    reviewers = sorted({row["reviewer_id"] for row in rows})
    cases = sorted({row["case_id"] for row in rows})
    reviewer_effect = {
        reviewer: rng.gauss(0.0, reviewer_sd_logit) for reviewer in reviewers
    }
    case_effect = {
        case: rng.gauss(0.0, case_sd_logit) for case in cases
    }

    outcomes: list[int] = []
    p0_sum = 0.0
    p1_sum = 0.0
    n0 = 0
    n1 = 0

    for row in rows:
        treatment = 1.0 if row["condition"] == "receipt" else 0.0
        eta = (
            base
            + reviewer_effect[row["reviewer_id"]]
            + case_effect[row["case_id"]]
            + treatment * delta
        )
        p = logistic(eta)
        outcomes.append(1 if rng.random() < p else 0)
        if treatment:
            p1_sum += p
            n1 += 1
        else:
            p0_sum += p
            n0 += 1

    return outcomes, p0_sum / n0, p1_sum / n1


def simulate_scenario(scenario: dict[str, Any]) -> dict[str, Any]:
    scenario_id = scenario.get("scenario_id")
    if not isinstance(scenario_id, str) or not scenario_id:
        raise ValueError("scenario_id must be a non-empty string")

    reviewers = _positive_int(scenario.get("reviewers"), "reviewers", minimum=4)
    cases = _positive_int(scenario.get("cases"), "cases", minimum=4)
    cases_per_reviewer = _positive_int(
        scenario.get("cases_per_reviewer"),
        "cases_per_reviewer",
        minimum=2,
    )
    if cases_per_reviewer > cases:
        raise ValueError("cases_per_reviewer cannot exceed cases")

    assignment_seed = _positive_int(
        scenario.get("assignment_seed", 73917),
        "assignment_seed",
        minimum=0,
    )
    simulation_seed = _positive_int(
        scenario.get("simulation_seed", 20260919),
        "simulation_seed",
        minimum=0,
    )
    iterations = _positive_int(
        scenario.get("iterations", 1000),
        "iterations",
        minimum=20,
    )

    p0 = _probability(
        scenario.get("conditional_p_control"),
        "conditional_p_control",
        open_interval=True,
    )
    p1 = _probability(
        scenario.get("conditional_p_receipt"),
        "conditional_p_receipt",
        open_interval=True,
    )
    if p0 == p1:
        raise ValueError("conditional_p_control and conditional_p_receipt must differ")

    reviewer_sd = _finite(
        scenario.get("reviewer_sd_logit"),
        "reviewer_sd_logit",
    )
    case_sd = _finite(
        scenario.get("case_sd_logit"),
        "case_sd_logit",
    )
    if reviewer_sd < 0 or case_sd < 0:
        raise ValueError("random-effect standard deviations must be >= 0")

    alpha = _probability(
        scenario.get("alpha", 0.05),
        "alpha",
        open_interval=True,
    )
    zcrit = NormalDist().inv_cdf(1.0 - alpha / 2.0)

    rows, diagnostics = _assignment_rows(
        reviewers,
        cases,
        cases_per_reviewer,
        assignment_seed,
    )
    rng = random.Random(simulation_seed)

    estimates: list[float] = []
    ses: list[float] = []
    p0_marginal: list[float] = []
    p1_marginal: list[float] = []
    two_sided_rejections = 0
    directional_rejections = 0
    unusable = 0
    expected_sign = 1.0 if p1 > p0 else -1.0

    for _ in range(iterations):
        outcomes, m0, m1 = _simulate_once(
            rows,
            rng,
            conditional_p_control=p0,
            conditional_p_receipt=p1,
            reviewer_sd_logit=reviewer_sd,
            case_sd_logit=case_sd,
        )
        result = two_way_cluster_contrast(rows, outcomes)
        estimate = result["risk_difference"]
        se = result["two_way_cluster_se"]

        estimates.append(estimate)
        p0_marginal.append(m0)
        p1_marginal.append(m1)

        if not math.isfinite(se) or se <= 0:
            unusable += 1
            continue

        ses.append(se)
        z = estimate / se
        if abs(z) > zcrit:
            two_sided_rejections += 1
        if expected_sign * z > zcrit:
            directional_rejections += 1

    usable = iterations - unusable
    if usable <= 0:
        raise ValueError("all simulated cluster-robust standard errors were unusable")

    power = two_sided_rejections / usable
    directional_power = directional_rejections / usable
    mcse = math.sqrt(power * (1.0 - power) / usable)

    return {
        "scenario_id": scenario_id,
        "method": (
            "logistic_random_intercepts_plus_linear_probability_condition_contrast_"
            "with_two_way_cluster_robust_covariance"
        ),
        "design": {
            "reviewers": reviewers,
            "cases": cases,
            "cases_per_reviewer": cases_per_reviewer,
            "total_reviewer_case_observations": len(rows),
            "assignment_seed": assignment_seed,
            "assignment_diagnostics": diagnostics,
        },
        "assumptions": {
            "conditional_p_control_at_zero_random_effects": p0,
            "conditional_p_receipt_at_zero_random_effects": p1,
            "conditional_log_odds_ratio": math.exp(logit(p1) - logit(p0)),
            "reviewer_sd_logit": reviewer_sd,
            "case_sd_logit": case_sd,
            "alpha_two_sided": alpha,
            "iterations": iterations,
            "simulation_seed": simulation_seed,
        },
        "simulation": {
            "mean_simulated_marginal_p_control": statistics.fmean(p0_marginal),
            "mean_simulated_marginal_p_receipt": statistics.fmean(p1_marginal),
            "mean_risk_difference_estimate": statistics.fmean(estimates),
            "sd_risk_difference_estimate": statistics.stdev(estimates),
            "median_two_way_cluster_se": statistics.median(ses),
            "two_sided_rejection_rate": power,
            "directional_rejection_rate": directional_power,
            "monte_carlo_se_for_two_sided_rate": mcse,
            "usable_iterations": usable,
            "unusable_variance_iterations": unusable,
        },
        "interpretation_boundary": (
            "Development-only sensitivity analysis. Results depend on assumed "
            "baseline performance, condition effect, reviewer heterogeneity, case "
            "heterogeneity, assignment, and the simple linear-probability/two-way "
            "cluster-robust analysis approximation. They do not freeze sample size."
        ),
    }


def run_plan(config: dict[str, Any]) -> dict[str, Any]:
    scenarios = config.get("scenarios")
    if not isinstance(scenarios, list) or not scenarios:
        raise ValueError("config.scenarios must be a non-empty list")

    ids: set[str] = set()
    results: list[dict[str, Any]] = []
    for scenario in scenarios:
        if not isinstance(scenario, dict):
            raise ValueError("each scenario must be an object")
        sid = scenario.get("scenario_id")
        if sid in ids:
            raise ValueError(f"duplicate scenario_id {sid!r}")
        if isinstance(sid, str):
            ids.add(sid)
        results.append(simulate_scenario(scenario))

    return {
        "planner_version": PLANNER_VERSION,
        "status": "development_only_not_frozen",
        "method_note": (
            "Reviewer and case random intercepts are simulated explicitly. "
            "Inference uses an OLS condition contrast with additive two-way "
            "cluster covariance: reviewer + case - reviewer/case intersection."
        ),
        "n_scenarios": len(results),
        "scenarios": results,
    }


def run_self_test() -> int:
    base = {
        "scenario_id": "smoke",
        "reviewers": 12,
        "cases": 12,
        "cases_per_reviewer": 6,
        "assignment_seed": 123,
        "simulation_seed": 456,
        "iterations": 40,
        "conditional_p_control": 0.55,
        "conditional_p_receipt": 0.75,
        "reviewer_sd_logit": 0.4,
        "case_sd_logit": 0.5,
        "alpha": 0.05,
    }

    first = simulate_scenario(base)
    second = simulate_scenario(base)
    assert first == second
    assert first["design"]["total_reviewer_case_observations"] == 72
    assert first["simulation"]["usable_iterations"] > 0
    assert 0.0 <= first["simulation"]["two_sided_rejection_rate"] <= 1.0

    stronger = simulate_scenario(
        {
            **base,
            "scenario_id": "stronger",
            "conditional_p_receipt": 0.90,
        }
    )
    assert (
        stronger["simulation"]["mean_risk_difference_estimate"]
        > first["simulation"]["mean_risk_difference_estimate"]
    )

    rows, _ = _assignment_rows(8, 8, 4, 73917)
    outcomes = [
        1 if row["condition"] == "receipt" else 0
        for row in rows
    ]
    contrast = two_way_cluster_contrast(rows, outcomes)
    assert math.isclose(contrast["risk_difference"], 1.0)

    for bad in (
        {**base, "scenario_id": "", "iterations": 40},
        {**base, "scenario_id": "bad-p", "conditional_p_control": 1.0},
        {**base, "scenario_id": "bad-cases", "cases_per_reviewer": 20},
        {**base, "scenario_id": "bad-sd", "reviewer_sd_logit": -0.1},
        {**base, "scenario_id": "bad-iterations", "iterations": 5},
    ):
        try:
            simulate_scenario(bad)
        except ValueError:
            pass
        else:
            raise AssertionError(f"invalid scenario was accepted: {bad['scenario_id']}")

    plan = run_plan({"scenarios": [base, {**base, "scenario_id": "smoke-2"}]})
    assert plan["n_scenarios"] == 2

    print(
        "AR-P003 crossed-design planner self-test passed: deterministic "
        "reviewer x case simulation and two-way cluster variance."
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Development-only crossed reviewer x case Monte Carlo planning "
            "for AR-P003 v0.3."
        )
    )
    parser.add_argument("config", nargs="?", help="JSON planning-scenario file")
    parser.add_argument("--output", help="Optional JSON output path")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        return run_self_test()

    if not args.config:
        parser.error("provide a JSON config file or use --self-test")

    try:
        config = json.loads(Path(args.config).read_text(encoding="utf-8"))
        if not isinstance(config, dict):
            raise ValueError("config must be a JSON object")
        result = run_plan(config)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        Path(args.output).write_text(rendered, encoding="utf-8")
    else:
        sys.stdout.write(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
