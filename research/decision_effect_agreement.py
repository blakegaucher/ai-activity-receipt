#!/usr/bin/env python3
"""Research-only decision/effect agreement prototype for AIAR issue #108.

This module does not implement WIMSE conformance. It tests whether the semantic
gap identified by the standards watch is useful before any core-schema change.
"""

VALID_DECISIONS = {"permit", "deny", "unknown"}
VALID_EFFECTS = {"occurred", "none", "unknown"}


def derive_agreement(decision: str, effect: str, *, attributable: bool, independent_observer: bool) -> str:
    if decision not in VALID_DECISIONS:
        raise ValueError("invalid decision")
    if effect not in VALID_EFFECTS:
        raise ValueError("invalid effect")

    # Self/in-process observation cannot establish the independent effect side.
    if not independent_observer or decision == "unknown" or effect == "unknown":
        return "indeterminate"

    if effect == "occurred" and not attributable:
        return "indeterminate"

    if decision == "permit" and effect == "occurred":
        return "agree"
    if decision == "deny" and effect == "none":
        return "agree"
    if decision == "deny" and effect == "occurred":
        return "disagree"
    if decision == "permit" and effect == "none":
        return "not-exercised"

    return "indeterminate"


def self_test() -> None:
    vectors = [
        ("permit", "occurred", True, True, "agree"),
        ("deny", "none", True, True, "agree"),
        ("deny", "occurred", True, True, "disagree"),
        ("permit", "none", True, True, "not-exercised"),
        ("permit", "occurred", False, True, "indeterminate"),
        ("permit", "occurred", True, False, "indeterminate"),
        ("unknown", "occurred", True, True, "indeterminate"),
        ("permit", "unknown", True, True, "indeterminate"),
    ]
    for decision, effect, attributable, independent, expected in vectors:
        actual = derive_agreement(
            decision, effect,
            attributable=attributable,
            independent_observer=independent,
        )
        assert actual == expected, (decision, effect, actual, expected)

    for bad in ("approved", "", None):
        try:
            derive_agreement(bad, "none", attributable=True, independent_observer=True)
        except ValueError:
            pass
        else:
            raise AssertionError("invalid decision accepted")

    print(f"decision/effect prototype: {len(vectors)} vectors passed")


if __name__ == "__main__":
    self_test()
