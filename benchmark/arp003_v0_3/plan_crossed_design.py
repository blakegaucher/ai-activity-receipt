#!/usr/bin/env python3
"""Three-condition crossed reviewer x case planning for AR-P003 v0.3.

Development-only planning for the selected comparison design:
raw evidence, neutral structured event table + the same evidence, and
Activity Receipt + the same evidence.

The planner simulates the selected binary primary endpoint
correct_completion_by_180s under reviewer and case random intercepts and
reports prespecified development contrasts with two-way cluster-robust
covariance. The primary timing clock and effect/precision target remain
unresolved, so current probabilities are illustrative and no sample size,
allocation, stopping rule, or final analysis model is frozen.
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
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from benchmark.arp003_v0_3.generate_assignment import generate  # noqa: E402

PLANNER_VERSION = "AR-P003-v0.3-crossed-planning-v0.4"
CONDITIONS = ("raw", "structured", "receipt")
CONTRASTS = {
    "structured_vs_raw": (0.0, 1.0, 0.0),
    "receipt_vs_raw": (0.0, 0.0, 1.0),
    "receipt_vs_structured": (0.0, -1.0, 1.0),
}


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


def _x(condition: str) -> list[float]:
    if condition == "raw":
        return [1.0, 0.0, 0.0]
    if condition == "structured":
        return [1.0, 1.0, 0.0]
    if condition == "receipt":
        return [1.0, 0.0, 1.0]
    raise ValueError(f"unknown condition {condition!r}")


def _zeros(n: int) -> list[list[float]]:
    return [[0.0 for _ in range(n)] for _ in range(n)]


def _mat_mul(a: list[list[float]], b: list[list[float]]) -> list[list[float]]:
    if not a or not b or len(a[0]) != len(b):
        raise ValueError("incompatible matrix dimensions")
    return [
        [
            sum(a[i][k] * b[k][j] for k in range(len(b)))
            for j in range(len(b[0]))
        ]
        for i in range(len(a))
    ]


def _mat_add(
    a: list[list[float]],
    b: list[list[float]],
    *,
    scale: float = 1.0,
) -> list[list[float]]:
    return [
        [a[i][j] + scale * b[i][j] for j in range(len(a[0]))]
        for i in range(len(a))
    ]


def _inverse(matrix: list[list[float]]) -> list[list[float]]:
    n = len(matrix)
    aug = [
        [float(matrix[i][j]) for j in range(n)]
        + [1.0 if i == j else 0.0 for j in range(n)]
        for i in range(n)
    ]
    for col in range(n):
        pivot = max(range(col, n), key=lambda row: abs(aug[row][col]))
        if abs(aug[pivot][col]) < 1e-12:
            raise ValueError("design matrix is singular")
        aug[col], aug[pivot] = aug[pivot], aug[col]
        scale = aug[col][col]
        aug[col] = [value / scale for value in aug[col]]
        for row in range(n):
            if row == col:
                continue
            factor = aug[row][col]
            aug[row] = [
                aug[row][j] - factor * aug[col][j]
                for j in range(2 * n)
            ]
    return [row[n:] for row in aug]


def _xtx_inverse(rows: list[dict[str, Any]]) -> list[list[float]]:
    xtx = _zeros(3)
    for row in rows:
        x = _x(row["condition"])
        for i in range(3):
            for j in range(3):
                xtx[i][j] += x[i] * x[j]
    return _inverse(xtx)


def _cluster_meat(
    rows: list[dict[str, Any]],
    residuals: list[float],
    *,
    group_key: str | None = None,
    intersection: bool = False,
) -> list[list[float]]:
    groups: dict[Any, list[float]] = {}
    for row, resid in zip(rows, residuals, strict=True):
        if intersection:
            key: Any = (row["reviewer_id"], row["case_id"])
        else:
            if group_key is None:
                raise ValueError("group_key is required")
            key = row[group_key]
        x = _x(row["condition"])
        score = groups.setdefault(key, [0.0, 0.0, 0.0])
        for i in range(3):
            score[i] += x[i] * resid

    meat = _zeros(3)
    for score in groups.values():
        for i in range(3):
            for j in range(3):
                meat[i][j] += score[i] * score[j]

    g = len(groups)
    n = len(rows)
    k = 3
    if g <= 1 or n <= k:
        raise ValueError("too few clusters/observations for three-condition covariance")
    correction = (g / (g - 1.0)) * ((n - 1.0) / (n - k))
    return [[value * correction for value in row] for row in meat]


def _contrast_variance(
    covariance: list[list[float]],
    vector: tuple[float, float, float],
) -> float:
    return sum(
        vector[i] * covariance[i][j] * vector[j]
        for i in range(3)
        for j in range(3)
    )


def two_way_cluster_contrasts(
    rows: list[dict[str, Any]],
    outcomes: list[int],
) -> dict[str, Any]:
    if len(rows) != len(outcomes) or not rows:
        raise ValueError("rows and outcomes must be same non-zero length")

    groups = {
        condition: [
            float(y)
            for row, y in zip(rows, outcomes, strict=True)
            if row["condition"] == condition
        ]
        for condition in CONDITIONS
    }
    if any(not values for values in groups.values()):
        raise ValueError("all three comparison conditions require observations")

    means = {condition: statistics.fmean(values) for condition, values in groups.items()}
    beta = [
        means["raw"],
        means["structured"] - means["raw"],
        means["receipt"] - means["raw"],
    ]
    fitted = [
        means[row["condition"]]
        for row in rows
    ]
    residuals = [float(y) - fit for y, fit in zip(outcomes, fitted, strict=True)]

    bread = _xtx_inverse(rows)
    reviewer_meat = _cluster_meat(rows, residuals, group_key="reviewer_id")
    case_meat = _cluster_meat(rows, residuals, group_key="case_id")
    intersection_meat = _cluster_meat(rows, residuals, intersection=True)
    meat = _mat_add(_mat_add(reviewer_meat, case_meat), intersection_meat, scale=-1.0)
    covariance = _mat_mul(_mat_mul(bread, meat), bread)

    estimates: dict[str, dict[str, float]] = {}
    for name, vector in CONTRASTS.items():
        estimate = sum(vector[i] * beta[i] for i in range(3))
        variance = _contrast_variance(covariance, vector)
        estimates[name] = {
            "risk_difference": estimate,
            "two_way_cluster_se": math.sqrt(variance) if variance > 0 else float("nan"),
            "variance": variance,
        }

    return {
        "condition_means": means,
        "contrasts": estimates,
        "covariance": covariance,
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
    return assignment["assignments"], assignment["diagnostics"]


def _simulate_once(
    rows: list[dict[str, Any]],
    rng: random.Random,
    *,
    conditional_p_raw: float,
    conditional_p_structured: float,
    conditional_p_receipt: float,
    reviewer_sd_logit: float,
    case_sd_logit: float,
) -> tuple[list[int], dict[str, float]]:
    logits = {
        "raw": logit(conditional_p_raw),
        "structured": logit(conditional_p_structured),
        "receipt": logit(conditional_p_receipt),
    }
    reviewers = sorted({row["reviewer_id"] for row in rows})
    cases = sorted({row["case_id"] for row in rows})
    reviewer_effect = {
        reviewer: rng.gauss(0.0, reviewer_sd_logit) for reviewer in reviewers
    }
    case_effect = {
        case: rng.gauss(0.0, case_sd_logit) for case in cases
    }

    outcomes: list[int] = []
    marginal_sum = {condition: 0.0 for condition in CONDITIONS}
    marginal_n = {condition: 0 for condition in CONDITIONS}

    for row in rows:
        condition = row["condition"]
        eta = (
            logits[condition]
            + reviewer_effect[row["reviewer_id"]]
            + case_effect[row["case_id"]]
        )
        p = logistic(eta)
        outcomes.append(1 if rng.random() < p else 0)
        marginal_sum[condition] += p
        marginal_n[condition] += 1

    marginals = {
        condition: marginal_sum[condition] / marginal_n[condition]
        for condition in CONDITIONS
    }
    return outcomes, marginals


def simulate_scenario(scenario: dict[str, Any]) -> dict[str, Any]:
    scenario_id = scenario.get("scenario_id")
    if not isinstance(scenario_id, str) or not scenario_id:
        raise ValueError("scenario_id must be a non-empty string")

    reviewers = _positive_int(scenario.get("reviewers"), "reviewers", minimum=4)
    cases = _positive_int(scenario.get("cases"), "cases", minimum=4)
    cases_per_reviewer = _positive_int(
        scenario.get("cases_per_reviewer"),
        "cases_per_reviewer",
        minimum=3,
    )
    if cases_per_reviewer > cases:
        raise ValueError("cases_per_reviewer cannot exceed cases")

    assignment_seed = _positive_int(
        scenario.get("assignment_seed", 73917),
        "assignment_seed",
        minimum=0,
    )
    simulation_seed = _positive_int(
        scenario.get("simulation_seed", 20260920),
        "simulation_seed",
        minimum=0,
    )
    iterations = _positive_int(
        scenario.get("iterations", 1000),
        "iterations",
        minimum=20,
    )

    assumed = {
        condition: _probability(
            scenario.get(f"conditional_p_{condition}"),
            f"conditional_p_{condition}",
            open_interval=True,
        )
        for condition in CONDITIONS
    }
    reviewer_sd = _finite(scenario.get("reviewer_sd_logit"), "reviewer_sd_logit")
    case_sd = _finite(scenario.get("case_sd_logit"), "case_sd_logit")
    if reviewer_sd < 0 or case_sd < 0:
        raise ValueError("random-effect standard deviations must be >= 0")

    alpha = _probability(scenario.get("alpha", 0.05), "alpha", open_interval=True)
    zcrit = NormalDist().inv_cdf(1.0 - alpha / 2.0)

    rows, diagnostics = _assignment_rows(
        reviewers,
        cases,
        cases_per_reviewer,
        assignment_seed,
    )
    rng = random.Random(simulation_seed)

    estimates = {name: [] for name in CONTRASTS}
    ses = {name: [] for name in CONTRASTS}
    rejections = {name: 0 for name in CONTRASTS}
    directional = {name: 0 for name in CONTRASTS}
    unusable = {name: 0 for name in CONTRASTS}
    marginal = {condition: [] for condition in CONDITIONS}

    assumed_diff = {
        "structured_vs_raw": assumed["structured"] - assumed["raw"],
        "receipt_vs_raw": assumed["receipt"] - assumed["raw"],
        "receipt_vs_structured": assumed["receipt"] - assumed["structured"],
    }

    for _ in range(iterations):
        outcomes, marginals = _simulate_once(
            rows,
            rng,
            conditional_p_raw=assumed["raw"],
            conditional_p_structured=assumed["structured"],
            conditional_p_receipt=assumed["receipt"],
            reviewer_sd_logit=reviewer_sd,
            case_sd_logit=case_sd,
        )
        result = two_way_cluster_contrasts(rows, outcomes)
        for condition in CONDITIONS:
            marginal[condition].append(marginals[condition])
        for name in CONTRASTS:
            estimate = result["contrasts"][name]["risk_difference"]
            se = result["contrasts"][name]["two_way_cluster_se"]
            estimates[name].append(estimate)
            if not math.isfinite(se) or se <= 0:
                unusable[name] += 1
                continue
            ses[name].append(se)
            z = estimate / se
            if abs(z) > zcrit:
                rejections[name] += 1
            direction = 1.0 if assumed_diff[name] > 0 else -1.0 if assumed_diff[name] < 0 else 0.0
            if direction and direction * z > zcrit:
                directional[name] += 1

    contrast_output: dict[str, Any] = {}
    for name in CONTRASTS:
        usable = iterations - unusable[name]
        if usable <= 0:
            raise ValueError(f"all simulated standard errors unusable for {name}")
        rate = rejections[name] / usable
        contrast_output[name] = {
            "assumed_conditional_risk_difference": assumed_diff[name],
            "mean_estimated_risk_difference": statistics.fmean(estimates[name]),
            "sd_estimated_risk_difference": (
                statistics.stdev(estimates[name]) if len(estimates[name]) > 1 else 0.0
            ),
            "median_two_way_cluster_se": statistics.median(ses[name]) if ses[name] else None,
            "two_sided_rejection_rate": rate,
            "directional_rejection_rate": directional[name] / usable,
            "monte_carlo_se_for_two_sided_rate": math.sqrt(
                rate * (1.0 - rate) / usable
            ),
            "usable_iterations": usable,
            "unusable_variance_iterations": unusable[name],
        }

    return {
        "scenario_id": scenario_id,
        "method": (
            "three_condition_logistic_random_intercepts_plus_linear_probability_"
            "contrasts_with_two_way_cluster_robust_covariance"
        ),
        "primary_endpoint": "correct_completion_by_180s",
        "primary_timing_clock": "unresolved",
        "effect_precision_target": "unresolved",
        "design": {
            "comparison_design": "three_condition_structured_control",
            "challenge_design": "integrated_challenge_strata",
            "challenge_allocation_status": "not_frozen_not_modeled_in_example_scenario",
            "reviewers": reviewers,
            "cases": cases,
            "cases_per_reviewer": cases_per_reviewer,
            "total_reviewer_case_observations": len(rows),
            "assignment_seed": assignment_seed,
            "assignment_diagnostics": diagnostics,
        },
        "assumptions": {
            "conditional_p_raw_at_zero_random_effects": assumed["raw"],
            "conditional_p_structured_at_zero_random_effects": assumed["structured"],
            "conditional_p_receipt_at_zero_random_effects": assumed["receipt"],
            "reviewer_sd_logit": reviewer_sd,
            "case_sd_logit": case_sd,
            "alpha_two_sided": alpha,
            "iterations": iterations,
            "simulation_seed": simulation_seed,
        },
        "simulation": {
            "mean_simulated_marginal_p": {
                condition: statistics.fmean(marginal[condition])
                for condition in CONDITIONS
            },
            "contrasts": contrast_output,
        },
        "interpretation_boundary": (
            "Development-only sensitivity analysis for the selected binary primary "
            "endpoint and three-condition comparison architecture. Results depend on "
            "illustrative success probabilities, heterogeneity, assignment, and "
            "analysis assumptions. The primary timing clock and effect/precision "
            "target remain unresolved; this does not freeze reviewer count, case "
            "count, cases per reviewer, allocation, or stopping."
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
        "comparison_design": "three_condition_structured_control",
        "challenge_design": "integrated_challenge_strata",
        "primary_endpoint": "correct_completion_by_180s",
        "primary_timing_clock": "unresolved",
        "effect_precision_target": "unresolved",
        "final_sample_size_frozen": False,
        "challenge_allocation_status": "not_frozen_not_modeled_in_example_scenarios",
        "method_note": (
            "Reviewer and case random intercepts are simulated explicitly. "
            "Inference uses raw-baseline three-condition OLS contrasts with additive "
            "two-way cluster covariance: reviewer + case - reviewer/case intersection."
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
        "conditional_p_raw": 0.55,
        "conditional_p_structured": 0.65,
        "conditional_p_receipt": 0.75,
        "reviewer_sd_logit": 0.4,
        "case_sd_logit": 0.5,
        "alpha": 0.05,
    }

    first = simulate_scenario(base)
    second = simulate_scenario(base)
    assert first == second
    assert first["design"]["total_reviewer_case_observations"] == 72
    assert first["primary_endpoint"] == "correct_completion_by_180s"
    assert first["primary_timing_clock"] == "unresolved"
    assert first["effect_precision_target"] == "unresolved"
    assert set(first["simulation"]["contrasts"]) == set(CONTRASTS)

    stronger = simulate_scenario(
        {
            **base,
            "scenario_id": "stronger",
            "conditional_p_receipt": 0.90,
        }
    )
    assert (
        stronger["simulation"]["contrasts"]["receipt_vs_structured"][
            "mean_estimated_risk_difference"
        ]
        > first["simulation"]["contrasts"]["receipt_vs_structured"][
            "mean_estimated_risk_difference"
        ]
    )

    rows, _ = _assignment_rows(9, 9, 6, 73917)
    outcomes = [
        0 if row["condition"] == "raw" else 1
        for row in rows
    ]
    contrast = two_way_cluster_contrasts(rows, outcomes)
    assert math.isclose(
        contrast["contrasts"]["structured_vs_raw"]["risk_difference"], 1.0
    )
    assert math.isclose(
        contrast["contrasts"]["receipt_vs_structured"]["risk_difference"], 0.0
    )

    for bad in (
        {**base, "scenario_id": "", "iterations": 40},
        {**base, "scenario_id": "bad-p", "conditional_p_raw": 1.0},
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
    assert plan["comparison_design"] == "three_condition_structured_control"
    assert plan["challenge_design"] == "integrated_challenge_strata"
    assert plan["challenge_allocation_status"] == (
        "not_frozen_not_modeled_in_example_scenarios"
    )

    print(
        "AR-P003 crossed-design planner self-test passed: deterministic "
        "three-condition reviewer x case simulation and two-way clustered contrasts."
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Development-only three-condition crossed reviewer x case Monte Carlo "
            "planning for AR-P003 v0.3."
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
    except (OSError, json.JSONDecodeError, ValueError, AssertionError) as exc:
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
