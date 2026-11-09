"""Research-only agreement contract: declarations never establish independence."""
import unittest

from decision_effect_agreement import derive_agreement


class AgreementTests(unittest.TestCase):
    def test_boolean_compatibility_matrix(self):
        # Expected outcomes for (attributable, independent): TT, FT, TF, FF.
        rows = [
            ("permit", "occurred", ("agree", "indeterminate", "indeterminate", "indeterminate")),
            ("deny", "occurred", ("disagree", "indeterminate", "indeterminate", "indeterminate")),
            ("permit", "none", ("not-exercised", "not-exercised", "indeterminate", "indeterminate")),
            ("deny", "none", ("agree", "agree", "indeterminate", "indeterminate")),
            ("unknown", "occurred", ("indeterminate",) * 4),
            ("unknown", "none", ("indeterminate",) * 4),
            ("permit", "unknown", ("indeterminate",) * 4),
            ("deny", "unknown", ("indeterminate",) * 4),
            ("unknown", "unknown", ("indeterminate",) * 4),
        ]
        for decision, effect, outcomes in rows:
            for (attributable, independent), expected in zip(
                    [(True, True), (False, True), (True, False), (False, False)], outcomes):
                with self.subTest(decision=decision, effect=effect,
                                  attributable=attributable, independent=independent):
                    self.assertEqual(derive_agreement(
                        decision, effect, attributable=attributable,
                        independent_observer=independent), expected)

    def test_malformed_flags_reject_before_outcome_derivation(self):
        for field in ("attributable", "independent_observer"):
            for bad in ("false", "true", "", 0, 1, -1, 0.0, 1.0, None, [], [False], {}, {"value": False}):
                for decision in ("permit", "deny", "unknown"):
                    for effect in ("occurred", "none", "unknown"):
                        for other in (False, True):
                            flags = {"attributable": other, "independent_observer": other}
                            flags[field] = bad
                            with self.subTest(field=field, bad=bad, decision=decision,
                                              effect=effect, other=other):
                                with self.assertRaisesRegex(ValueError, field + " must be a boolean"):
                                    derive_agreement(decision, effect, **flags)


if __name__ == "__main__":
    unittest.main()
