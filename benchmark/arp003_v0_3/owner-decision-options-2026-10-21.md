# Four numerical owner decisions — development screen, 2026-10-21

No option is selected. This prepares the existing PR #96 / BLA-11 decision;
it changes no protocol, frozen result, recruitment permission or execution gate.
The selected endpoint remains evidence-supported correct completion by 180
seconds under `wall_deadline_with_hidden_sensitivity`, with three conditions.

All counts below are **approximate observations per condition**, followed by
three-condition reviewer-capacity equivalents in parentheses. They reuse the
existing independent-observation planners with 80% power, two-sided alpha .05
or one-sided .025, illustrative design effect 1.5, 10% uniformly unusable
observations and 24 cases/reviewer. The actual reviewer/case design is crossed;
these are feasibility screens, not a sample-size commitment, dropout model or
confirmatory power analysis. Neither multiple comparisons nor two separate
safety contrasts are accounted for in this screen.

| Owner decision | Illustrative options and capacity | What the choice would allow | What it would not allow |
| --- | --- | --- | --- |
| Smallest worthwhile Receipt-vs-structured benefit | +3pp: 5,922 (741); +5pp: 2,085 (261); +10pp: 489 (62), assuming control .70 and true improvements equal to those values | State which improvement is worth pursuing; plan to detect a departure from zero under the assumed true effect | These power counts do **not** show the lower confidence bound will exceed that practical threshold. A true effect exactly at the threshold cannot give 80% power to prove it exceeds the threshold. The inferential rule must be explicit before freeze. |
| Maximum acceptable critical false-clearance increase | 1pp: 12,428 (1,554); 2pp: 3,107 (389); 3pp: 1,381 (173), assuming baseline .05 and true difference zero | Define a separate upper safety/noninferiority margin | No absolute safety guarantee, rare-harm bound or proof from a nonsignificant difference; normal approximations are fragile for rare events. |
| Dormant speed-claim accuracy margin | Keep dormant: no confirmatory speed claim; if separately activated, 2pp: 13,736 (1,717), 3pp: 6,105 (764), 5pp: 2,198 (275), assuming success .70 and true difference zero | Predeclare tolerated loss of accuracy for a later, explicitly activated speed claim | No speed superiority, safe tradeoff or timing validity follows from choosing an accuracy margin. Keeping it dormant does not silently select a number. |
| Receipt-vs-structured risk-difference precision | 95% half-width ±2pp: 6,363 (796); ±3pp: 2,828 (354); ±5pp: 1,018 (128), assuming .70 vs .75 | Set desired estimation resolution in a specified analysis model | Precision alone does not establish benefit, safety or sufficient power for every contrast. |

Safety is highly baseline-sensitive: at a 2pp margin the screen is 648 per
condition (81 reviewer equivalents) at .01 false-clearance probability, 3,107
(389) at .05, and 5,887 (736) at .10. At .005 it is 326 (41), where rare-event
normal approximation is especially questionable. Halving a margin or target
half-width roughly quadruples capacity. The illustrative inflation factor is
1.5/.9; actual crossed dependence, allocation, missingness and case difficulty
can change that substantially.

The [machine-readable grid](owner-decision-options-2026-10-21.json) retains
baseline sensitivity, exact source hashes, formulas' source files and every
assumption. It is computed preparation, not external scientific validation.
The methods literature does not select any of these values.

Smallest owner input: provide (1) practical benefit in percentage points and
whether the claim is detection above zero or proof above that threshold;
(2) maximum critical false-clearance increase; (3) keep speed dormant or specify
an accuracy margin for later activation; (4) desired precision half-width.
After those substantive choices, use the existing crossed-design simulator to
plan a model/allocation grid and at least 1,000 replicates per final scenario,
then review all remaining freeze gates. No human study starts from this table.
