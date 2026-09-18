#!/usr/bin/env python3
"""Development-only sample-size / precision planning for AR-P003 v0.3.

These calculations are screening approximations for independent observations.
The real benchmark is crossed by reviewer and case, so a confirmatory design
must use a frozen primary endpoint plus a justified clustering/design-effect
assumption or a crossed-effects simulation/analysis plan before data collection.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from statistics import NormalDist
from typing import Any


PLANNER_VERSION = "AR-P003-v0.3-planning-v0.1"


def _probability(value: Any, name: str, *, open_interval: bool = False) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ValueError(f"{name} must be numeric")
    value = float(value)
    lo_ok = value > 0 if open_interval else value >= 0
    hi_ok = value < 1 if open_interval else value <= 1
    if not (lo_ok and hi_ok):
        interval = "(0, 1)" if open_interval else "[0, 1]"
        raise ValueError(f"{name} must be in {interval}")
    return value


def _positive(value: Any, name: str) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ValueError(f"{name} must be numeric")
    value = float(value)
    if not math.isfinite(value) or value <= 0:
        raise ValueError(f"{name} must be finite and > 0")
    return value


def _alpha_power(alpha: Any, power: Any) -> tuple[float, float]:
    alpha = _probability(alpha, "alpha", open_interval=True)
    power = _probability(power, "power", open_interval=True)
    if power <= 0.5:
        raise ValueError("power must be > 0.5 for this planning approximation")
    return alpha, power


def _inflate(
    raw_n: float,
    *,
    design_effect: Any,
    attrition: Any,
) -> tuple[int, float, float]:
    de = _positive(design_effect, "design_effect")
    attr = _probability(attrition, "attrition")
    if attr >= 1:
        raise ValueError("attrition must be < 1")
    adjusted = raw_n * de / (1.0 - attr)
    return math.ceil(adjusted), de, attr


def binary_two_group(
    *,
    p_control: Any,
    p_receipt: Any,
    alpha: Any = 0.05,
    power: Any = 0.80,
    design_effect: Any = 1.0,
    attrition: Any = 0.0,
) -> dict[str, Any]:
    """Approximate equal-allocation n/condition for two independent proportions."""
    p1 = _probability(p_control, "p_control")
    p2 = _probability(p_receipt, "p_receipt")
    if p1 == p2:
        raise ValueError("p_control and p_receipt must differ")
    alpha, power = _alpha_power(alpha, power)

    z_alpha = NormalDist().inv_cdf(1.0 - alpha / 2.0)
    z_beta = NormalDist().inv_cdf(power)
    p_bar = (p1 + p2) / 2.0

    raw_n = (
        (
            z_alpha * math.sqrt(2.0 * p_bar * (1.0 - p_bar))
            + z_beta
            * math.sqrt(p1 * (1.0 - p1) + p2 * (1.0 - p2))
        )
        ** 2
        / ((p2 - p1) ** 2)
    )

    adjusted_n, de, attr = _inflate(
        raw_n, design_effect=design_effect, attrition=attrition
    )
    return {
        "method": "normal_approx_two_independent_proportions",
        "p_control": p1,
        "p_receipt": p2,
        "absolute_difference": p2 - p1,
        "alpha_two_sided": alpha,
        "power": power,
        "raw_n_per_condition": raw_n,
        "design_effect": de,
        "attrition": attr,
        "adjusted_n_per_condition": adjusted_n,
        "adjusted_total_case_observations": 2 * adjusted_n,
    }


def continuous_standardized(
    *,
    effect_size_d: Any,
    alpha: Any = 0.05,
    power: Any = 0.80,
    design_effect: Any = 1.0,
    attrition: Any = 0.0,
) -> dict[str, Any]:
    """Approximate equal-allocation n/condition for a standardized mean difference."""
    d = _positive(effect_size_d, "effect_size_d")
    alpha, power = _alpha_power(alpha, power)

    z_alpha = NormalDist().inv_cdf(1.0 - alpha / 2.0)
    z_beta = NormalDist().inv_cdf(power)
    raw_n = 2.0 * ((z_alpha + z_beta) ** 2) / (d**2)

    adjusted_n, de, attr = _inflate(
        raw_n, design_effect=design_effect, attrition=attrition
    )
    return {
        "method": "normal_approx_standardized_mean_difference",
        "effect_size_d": d,
        "alpha_two_sided": alpha,
        "power": power,
        "raw_n_per_condition": raw_n,
        "design_effect": de,
        "attrition": attr,
        "adjusted_n_per_condition": adjusted_n,
        "adjusted_total_case_observations": 2 * adjusted_n,
    }


def proportion_precision(
    *,
    expected_proportion: Any,
    half_width: Any,
    confidence: Any = 0.95,
    design_effect: Any = 1.0,
    attrition: Any = 0.0,
) -> dict[str, Any]:
    """Approximate n for a single proportion confidence half-width."""
    p = _probability(expected_proportion, "expected_proportion")
    hw = _positive(half_width, "half_width")
    confidence = _probability(confidence, "confidence", open_interval=True)
    if confidence <= 0.5:
        raise ValueError("confidence must be > 0.5")

    z = NormalDist().inv_cdf((1.0 + confidence) / 2.0)
    raw_n = (z**2) * p * (1.0 - p) / (hw**2)

    adjusted_n, de, attr = _inflate(
        raw_n, design_effect=design_effect, attrition=attrition
    )
    return {
        "method": "normal_approx_single_proportion_precision",
        "expected_proportion": p,
        "confidence": confidence,
        "half_width": hw,
        "raw_n": raw_n,
        "design_effect": de,
        "attrition": attr,
        "adjusted_n": adjusted_n,
    }


def difference_precision(
    *,
    p_control: Any,
    p_receipt: Any,
    half_width: Any,
    confidence: Any = 0.95,
    design_effect: Any = 1.0,
    attrition: Any = 0.0,
) -> dict[str, Any]:
    """Approximate equal-allocation n/condition for difference-in-proportions precision."""
    p1 = _probability(p_control, "p_control")
    p2 = _probability(p_receipt, "p_receipt")
    hw = _positive(half_width, "half_width")
    confidence = _probability(confidence, "confidence", open_interval=True)
    if confidence <= 0.5:
        raise ValueError("confidence must be > 0.5")

    z = NormalDist().inv_cdf((1.0 + confidence) / 2.0)
    raw_n = (z**2) * (p1 * (1.0 - p1) + p2 * (1.0 - p2)) / (hw**2)

    adjusted_n, de, attr = _inflate(
        raw_n, design_effect=design_effect, attrition=attrition
    )
    return {
        "method": "normal_approx_difference_in_proportions_precision",
        "p_control": p1,
        "p_receipt": p2,
        "confidence": confidence,
        "half_width": hw,
        "raw_n_per_condition": raw_n,
        "design_effect": de,
        "attrition": attr,
        "adjusted_n_per_condition": adjusted_n,
        "adjusted_total_case_observations": 2 * adjusted_n,
    }


def reviewer_equivalent(
    total_case_observations: int,
    cases_per_reviewer: Any,
) -> int:
    if (
        not isinstance(cases_per_reviewer, int)
        or isinstance(cases_per_reviewer, bool)
        or cases_per_reviewer < 1
    ):
        raise ValueError("cases_per_reviewer must be a positive integer")
    return math.ceil(total_case_observations / cases_per_reviewer)


def evaluate_scenario(scenario: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(scenario, dict):
        raise ValueError("each scenario must be an object")

    kind = scenario.get("kind")
    scenario_id = scenario.get("scenario_id")
    if not isinstance(scenario_id, str) or not scenario_id:
        raise ValueError("scenario_id must be a non-empty string")

    args = dict(scenario)
    args.pop("scenario_id", None)
    args.pop("kind", None)
    cases_per_reviewer = args.pop("cases_per_reviewer", None)

    if kind == "binary_two_group":
        result = binary_two_group(**args)
    elif kind == "continuous_standardized":
        result = continuous_standardized(**args)
    elif kind == "proportion_precision":
        result = proportion_precision(**args)
    elif kind == "difference_precision":
        result = difference_precision(**args)
    else:
        raise ValueError(
            "kind must be one of binary_two_group, continuous_standardized, "
            "proportion_precision, difference_precision"
        )

    result = {"scenario_id": scenario_id, "kind": kind, **result}

    total = result.get("adjusted_total_case_observations")
    if cases_per_reviewer is not None and isinstance(total, int):
        result["cases_per_reviewer"] = cases_per_reviewer
        result["rough_reviewer_equivalent"] = reviewer_equivalent(
            total, cases_per_reviewer
        )
        result["reviewer_equivalent_warning"] = (
            "This divides planned case-observations by cases/reviewer only. "
            "It is not a crossed-effects power calculation."
        )

    return result


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
        results.append(evaluate_scenario(scenario))

    return {
        "planner_version": PLANNER_VERSION,
        "status": "development_only_not_frozen",
        "important_limit": (
            "AR-P003 is crossed by reviewer and case. These calculations are "
            "screening approximations and do not freeze a confirmatory sample size."
        ),
        "n_scenarios": len(results),
        "scenarios": results,
    }


def run_self_test() -> int:
    binary = binary_two_group(p_control=0.65, p_receipt=0.80)
    assert binary["adjusted_n_per_condition"] == 138

    adjusted = binary_two_group(
        p_control=0.65,
        p_receipt=0.80,
        design_effect=1.5,
        attrition=0.10,
    )
    assert adjusted["adjusted_n_per_condition"] == 230
    assert adjusted["adjusted_total_case_observations"] == 460
    assert reviewer_equivalent(460, 8) == 58

    continuous = continuous_standardized(effect_size_d=0.5)
    assert continuous["adjusted_n_per_condition"] == 63

    precision = proportion_precision(
        expected_proportion=0.75,
        half_width=0.05,
    )
    assert precision["adjusted_n"] == 289

    diff_precision = difference_precision(
        p_control=0.70,
        p_receipt=0.80,
        half_width=0.07,
    )
    assert diff_precision["adjusted_n_per_condition"] == 291

    plan = run_plan(
        {
            "scenarios": [
                {
                    "scenario_id": "binary-smoke",
                    "kind": "binary_two_group",
                    "p_control": 0.65,
                    "p_receipt": 0.80,
                    "design_effect": 1.5,
                    "attrition": 0.10,
                    "cases_per_reviewer": 8,
                },
                {
                    "scenario_id": "time-smoke",
                    "kind": "continuous_standardized",
                    "effect_size_d": 0.5,
                },
            ]
        }
    )
    assert plan["n_scenarios"] == 2
    assert plan["scenarios"][0]["rough_reviewer_equivalent"] == 58

    for bad in (
        lambda: binary_two_group(p_control=0.8, p_receipt=0.8),
        lambda: binary_two_group(p_control=0.7, p_receipt=0.8, design_effect=0),
        lambda: continuous_standardized(effect_size_d=0),
        lambda: proportion_precision(expected_proportion=0.5, half_width=0),
    ):
        try:
            bad()
        except ValueError:
            pass
        else:
            raise AssertionError("invalid planning input was not rejected")

    print("AR-P003 sample-size/precision planner self-test passed.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Development-only AR-P003 sample-size/precision screening "
            "approximations."
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
