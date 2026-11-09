#!/usr/bin/env python3
"""Development-only safety-margin capacity screen for AR-P003 v0.3.

This is a simple independent-observation normal approximation for a one-sided
noninferiority-style upper-margin check on a difference in critical false
clearance proportions. It is NOT a confirmatory crossed reviewer×case power
calculation and it does not select the effect/precision target.
"""

from __future__ import annotations

import argparse
import json
import math
from statistics import NormalDist


def safety_margin_screen(
    *,
    baseline_rate: float,
    margin: float = 0.02,
    alpha_one_sided: float = 0.025,
    power: float = 0.80,
    design_effect: float = 1.5,
    unusable_fraction: float = 0.10,
    cases_per_reviewer: int = 24,
) -> dict:
    for name, value in (
        ("baseline_rate", baseline_rate),
        ("margin", margin),
        ("alpha_one_sided", alpha_one_sided),
        ("power", power),
        ("unusable_fraction", unusable_fraction),
    ):
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise ValueError(f"{name} must be numeric")
    if not 0 < baseline_rate < 1:
        raise ValueError("baseline_rate must be in (0, 1)")
    if not 0 < margin < 1:
        raise ValueError("margin must be in (0, 1)")
    if not 0 < alpha_one_sided < 0.5:
        raise ValueError("alpha_one_sided must be in (0, 0.5)")
    if not 0.5 < power < 1:
        raise ValueError("power must be in (0.5, 1)")
    if not design_effect > 0:
        raise ValueError("design_effect must be > 0")
    if not 0 <= unusable_fraction < 1:
        raise ValueError("unusable_fraction must be in [0, 1)")
    if not isinstance(cases_per_reviewer, int) or cases_per_reviewer < 1:
        raise ValueError("cases_per_reviewer must be a positive integer")

    z_alpha = NormalDist().inv_cdf(1.0 - alpha_one_sided)
    z_power = NormalDist().inv_cdf(power)

    # Screening approximation under true Receipt-vs-comparator difference = 0.
    raw_n = (
        (z_alpha + z_power) ** 2
        * (2.0 * baseline_rate * (1.0 - baseline_rate))
        / (margin**2)
    )
    adjusted_n = math.ceil(raw_n * design_effect / (1.0 - unusable_fraction))

    # Three-condition capacity translation only; not crossed-effects power.
    reviewer_equivalent = math.ceil(3 * adjusted_n / cases_per_reviewer)

    return {
        "method": "independent_normal_approx_one_sided_difference_margin_screen",
        "status": "development_only_not_frozen",
        "baseline_rate": baseline_rate,
        "assumed_true_difference": 0.0,
        "upper_margin": margin,
        "alpha_one_sided": alpha_one_sided,
        "power": power,
        "raw_n_per_condition": raw_n,
        "design_effect": design_effect,
        "unusable_fraction": unusable_fraction,
        "adjusted_n_per_condition": adjusted_n,
        "three_condition_reviewer_equivalent": reviewer_equivalent,
        "cases_per_reviewer": cases_per_reviewer,
        "warning": (
            "Rare-event normal approximations can be poor. AR-P003 is crossed by "
            "reviewer and case. This is a capacity screen only and cannot freeze "
            "sample size or the safety inferential rule."
        ),
    }


def run_grid(rates: list[float]) -> dict:
    return {
        "schema": "arp003.safety-margin-capacity-screen.v0.1",
        "effect_precision_target": "unresolved",
        "critical_false_clearance_margin_proposal": 0.02,
        "results": [safety_margin_screen(baseline_rate=p) for p in rates],
    }


def self_test() -> int:
    r = safety_margin_screen(baseline_rate=0.05)
    assert r["adjusted_n_per_condition"] == 3107
    assert r["three_condition_reviewer_equivalent"] == 389

    for bad in (
        lambda: safety_margin_screen(baseline_rate=0),
        lambda: safety_margin_screen(baseline_rate=1),
        lambda: safety_margin_screen(baseline_rate=0.05, margin=0),
        lambda: safety_margin_screen(baseline_rate=0.05, design_effect=0),
    ):
        try:
            bad()
        except ValueError:
            pass
        else:
            raise AssertionError("invalid input was not rejected")

    print("AR-P003 safety-margin capacity screen self-test passed.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--rates",
        default="0.005,0.01,0.02,0.05,0.10,0.20",
        help="comma-separated baseline critical-false-clearance rates",
    )
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        return self_test()

    rates = [float(x.strip()) for x in args.rates.split(",") if x.strip()]
    print(json.dumps(run_grid(rates), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
