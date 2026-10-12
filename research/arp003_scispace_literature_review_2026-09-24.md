# AR-P003 SciSpace literature review and methodology implications

Date: 2026-09-24  
Status: DEVELOPMENT-ONLY RESEARCH NOTE  
Execution/recruitment authorization: NONE  
Protocol freeze effect: NONE

## Protected current methodology state

This note does not reopen or alter selected AR-P003 v0.3 decisions:

- comparison_conditions = three_condition_structured_control
- challenge_design = integrated_challenge_strata
- reviewer_population = relevant_professional_reviewers
- primary_endpoint = correct_completion_by_180s
- primary_timing_clock = wall_deadline_with_hidden_sensitivity
- effect_precision_target = unresolved
- recruitment remains unauthorized
- AR-P003 remains draft / not frozen / not executed

The three comparison conditions remain:
1. raw/underlying heterogeneous evidence;
2. neutral structured event table + the same underlying evidence;
3. AI Activity Receipt + the same underlying evidence.

The primary endpoint remains binary evidence-supported correct completion by 180 seconds. Component outcomes remain secondary diagnostics. Critical false clearance remains a separate safety endpoint.

## 1. Literature evidence matrix

| Evidence lane | Source | What it supports | Human outcome evidence? | Relevance to AR-P003 | Important limitation |
| --- | --- | --- | --- | --- | --- |
| Autonomous decision provenance | Lange (2022), *Autonomous decision provenance as a requirement for building trust*, DOI 10.1117/12.2622922 | Provenance can support transparency, accountability and explanation of autonomous decisions | No direct AR-P003-style controlled human comparison | Supports the problem premise for recording decision provenance | Does not establish that the AI Activity Receipt representation improves human review |
| AI auditing | Mökander (2023), *Auditing of AI: Legal, Ethical and Technical Approaches*, DOI 10.1007/s44206-023-00074-y | AI auditing should combine technical and process/governance evidence in structured procedures | Review/synthesis rather than AR-P003-style user experiment | Supports joining technical events with governance/authorization context | Does not validate any particular receipt schema or interface |
| Data provenance | Stahl et al. (2022), *Establishing Data Provenance for Responsible Artificial Intelligence Systems*, DOI 10.1145/3503488 | Provenance supports accountability, transparency and responsible-AI traceability | Primarily conceptual/review evidence | Supports provenance as a governance substrate | Focuses substantially on data provenance, not agent-action review |
| Structured log analysis | Locke et al. (2021/2022), *LogAssist: Assisting Log Analysis Through Log Summarization*, DOI 10.1109/TSE.2021.3083715 | Structured workflow-oriented log summaries can reduce analysis burden | Yes: user study; reported average 40% reduction in log-analysis task time, plus up to 99% event reduction | Strong adjacent evidence that organization/normalization of evidence can materially change reviewer performance | Software-log analysis is not AI-agent auditing; it does not establish accuracy or safety benefit for AIAR |
| Structured/visual logs | Liu et al. (2023), *Log-it: Supporting Programming with Interactive, Contextual, Structured, and Visual Logs*, DOI 10.1145/3544548.3581403 | Structure, context and visualization help programmers locate, synthesize and understand logs | Yes: user study with novice and expert programmers | Supports the neutral-structured-control condition: generic structuring itself may create benefit | Does not isolate an AI Activity Receipt-specific effect |
| Failure-reproduction timelines | Rößler et al. (2013), *Monitoring user interactions for supporting failure reproduction*, DOI 10.1109/ICPC.2013.6613835 | Visualized interaction traces can help derive failure reproduction steps | Yes, but benefits were heterogeneous and especially useful for some inexperienced developers | Reinforces that representation can alter audit/debug behavior | Not an AI audit task; some timed results did not favor the trace condition |
| Explanation / trust calibration | Zhang et al. (2020), *Effect of Confidence and Explanation on Accuracy and Trust Calibration in AI-Assisted Decision Making*, DOI 10.1145/3351095.3372852 | Confidence can improve trust calibration, while explanation/trust improvements need not improve decision accuracy | Yes | Supports objective performance endpoints rather than treating trust as a proxy | Different decision task and assistance design |
| Explanation effectiveness | Bansal et al. / related XAI comparison literature, *Are Explanations Helpful?*, DOI 10.1145/3397481.3450650 | Explanation effects vary by task and user expertise; explanations can fail to improve desired outcomes | Yes | Supports a controlled empirical test rather than assuming transparency causes benefit | XAI prediction explanations are not provenance receipts |
| Expertise effects | Zhao, Castelle & Turkay (2025), *Domain Experience and Expertise in Explainable AI Applications*, DOI 10.1145/3757583 | Practical experience and domain expertise change how professionals interpret and rely on AI explanations | Yes: task-led study with professionals | Direct support for defining and recording reviewer experience rather than assuming a homogeneous population | Small/context-specific professional sample; not an audit-receipt evaluation |
| LLM audit trails | Ojewale, Suresh & Venkatasubramanian (2026), *Audit Trails for Accountability in Large Language Models*, arXiv:2601.20727 | Context-rich audit trails can link technical provenance to approvals, waivers and attestations so events and authorization can be reconstructed | Architecture/framework paper, not a controlled AR-P003 human-benefit test | Very close conceptual prior art for lifecycle traceability and authorization reconstruction | Does not answer whether a compact Receipt improves professional reviewer accuracy or speed |

### Evidence classification

The literature strongly supports the *need* for provenance, audit trails, structured event records, and explicit governance/authorization context.

There is adjacent empirical evidence that structured or summarized logs can reduce reviewer effort or help understanding. However, those studies are primarily software-debugging/log-analysis studies rather than controlled evaluations of AI-agent audit records.

Within the search set reviewed here, no paper directly answers the AR-P003 confirmatory question: whether, with underlying evidence held symmetric, an AI Activity Receipt improves professional reviewers' evidence-supported correct audit completion by a fixed deadline relative to both raw evidence and a neutral structured representation.

This is a scoped literature-search finding, not a universal novelty or priority claim.

## 1A. 2024–2026 agent-trace search extension

A separate SciSpace search targeted recent human-subject work on reviewing or debugging LLM-agent trajectories, tool-use logs, provenance, and execution histories. It surfaced agent-evaluation and trace-diagnosis systems such as AgentAuditor (arXiv:2506.00641), AgentDiagnose (EMNLP 2025 demos, DOI 10.18653/v1/2025.emnlp-demos.15), structural trace-testing work, and human-oversight studies of GUI agents. These are relevant adjacent systems, but they do not duplicate the AR-P003 design of holding underlying evidence symmetric while comparing raw evidence, a neutral structured event table, and an AI Activity Receipt with professional reviewers on evidence-supported correct completion by a fixed deadline.

This further narrows the current literature finding: recent work is active on agent evaluation, trace diagnosis, and auditability, while the specific human-review representation question tested by AR-P003 remains unestablished in the reviewed search set. This is still not a universal novelty claim.

## 2. Effect / precision target research

### What the statistical literature supports

AR-P003's primary endpoint is binary and reviewers will make repeated judgments across cases. The repeated-binary-outcome literature consistently shows that sample-size requirements depend on:

- expected marginal success probabilities;
- the effect size the study is intended to distinguish;
- the number of repeated observations;
- within-reviewer / within-cluster correlation;
- allocation and missingness/attrition assumptions.

Relevant methods include:
- Rochon (1994), *Sample size for repeated measures studies with binary responses*, DOI 10.1002/SIM.4780131205;
- Hedeker et al. (2004), *Sample-Size Requirements for Comparisons of Two Groups on Repeated Observations of a Binary Outcome*, DOI 10.1177/0163278703261198;
- Jung & Ahn (2008), *Sample Size Requirements for Clinical Trials with Repeated Binary Outcomes*, DOI 10.1177/009286150804200202.

These papers support designing around an explicitly chosen practically meaningful effect and modeled repeated-measure correlation. They do not provide a universal percentage-point threshold that can simply be imported into AR-P003.

### Implication for the existing +5pp / 3pp / +2pp candidates

The existing candidate values should remain explicitly project-specific unless separately justified:

- +5 percentage points: candidate smallest worthwhile Receipt-vs-neutral-structured improvement on the primary endpoint;
- 3 percentage points: candidate accuracy non-inferiority margin only if a separately preregistered speed-efficiency claim is activated;
- +2 percentage points: candidate maximum acceptable increase in critical false clearance versus controls.

The literature search does **not** convert any of these values into an external norm.

### Recommended methodology refinement before numerical freeze

Do not keep effect size, safety margin and estimation precision bundled into one ambiguous concept. Before freeze, represent them as separate planned fields:

1. `minimum_practical_effect_receipt_vs_structured` — project-defined primary efficacy threshold;
2. `critical_false_clearance_margin` — separate safety guardrail;
3. `speed_claim_accuracy_noninferiority_margin` — dormant unless a speed-efficiency claim is explicitly activated;
4. `primary_effect_precision_rule` — confidence-interval / simulation-based planning rule for the primary Receipt-vs-structured risk difference.

Recommended planning method: simulation-based repeated-binary planning across plausible baseline success rates and within-reviewer/case correlations, with sensitivity analysis across those assumptions.

No final numerical effect threshold, confidence-interval width, sample size, allocation, or stopping rule is selected by this note.

## 3. Rationale for relevant professional reviewers

### Ready-to-use protocol rationale

AR-P003 targets relevant professional reviewers because the usefulness of an audit representation is not independent of reviewer knowledge and experience. Human-centered AI studies show that domain familiarity, expertise, and practical experience can materially change response time, perceived helpfulness, interpretation of AI explanations, and susceptibility to misleading recommendations. A professional-review population therefore provides a more ecologically relevant test of the intended audit task than an unrestricted convenience sample. The study will record experience bands rather than assume a homogeneous reviewer population, and any confirmatory claims will remain scoped to the population actually recruited.

This rationale is consistent with the selected population definition:
- at least 1 year of relevant professional experience;
- experience bands 1–2 years, 3–5 years, and 6+ years;
- English proficiency required;
- no specific degree, certification, or job title required;
- prior general AI Activity Receipt familiarity permitted and recorded;
- external assistance during study cases prohibited absent a pre-execution versioned amendment.

### Evidence basis

Zhao, Castelle & Turkay (2025), DOI 10.1145/3757583, report that highly experienced/knowledgeable practitioners, experienced but less expert practitioners, and highly expert but less experienced practitioners interacted with AI explanations differently.

The broader XAI user-study literature likewise reports substantial effects of domain familiarity and expertise on interpretation, response time, and calibrated use of explanations.

## 4. Claim boundary after this review

The literature review strengthens the following background claims:

- provenance and audit trails are established mechanisms for traceability and accountability;
- structured evidence presentation can alter human analysis burden and comprehension;
- reviewer expertise can materially affect human-AI evaluation behavior;
- repeated binary endpoints require correlation-aware planning.

It does **not** support claiming:

- that the AI Activity Receipt improves human audit accuracy;
- that it improves human productivity;
- that it is safer than raw or neutral structured evidence;
- that the +5pp, 3pp, or +2pp values are literature standards;
- that AR-P003 has established a final sample size;
- that recruitment or execution is authorized.

## 5. Next methodology action

The next defensible AR-P003 methodology action is not recruitment or execution. It is a development-only simulation grid for `effect_precision_target` that varies:

- baseline correct-completion probability;
- Receipt-vs-structured effect sizes around the candidate +5pp region;
- within-reviewer correlation;
- case difficulty / challenge stratum;
- number of cases per reviewer;
- attrition / unusable-session rate.

That simulation can then determine whether the project-defined thresholds are estimable with a practical reviewer count and can produce a precision rule without treating a literature-derived value as an external norm.

## References

1. Lange DS. Autonomous decision provenance as a requirement for building trust. 2022. DOI: 10.1117/12.2622922.
2. Mökander J. Auditing of AI: Legal, Ethical and Technical Approaches. 2023. DOI: 10.1007/s44206-023-00074-y.
3. Stahl BC et al. Establishing Data Provenance for Responsible Artificial Intelligence Systems. 2022. DOI: 10.1145/3503488.
4. Locke S et al. LogAssist: Assisting Log Analysis Through Log Summarization. DOI: 10.1109/TSE.2021.3083715.
5. Liu et al. Log-it: Supporting Programming with Interactive, Contextual, Structured, and Visual Logs. DOI: 10.1145/3544548.3581403.
6. Rößler et al. Monitoring user interactions for supporting failure reproduction. DOI: 10.1109/ICPC.2013.6613835.
7. Zhang Y et al. Effect of Confidence and Explanation on Accuracy and Trust Calibration in AI-Assisted Decision Making. DOI: 10.1145/3351095.3372852.
8. Are Explanations Helpful? A Comparative Study of the Effects of Explanations in AI-Assisted Decision-Making. DOI: 10.1145/3397481.3450650.
9. Zhao Z, Castelle M, Turkay C. Domain Experience and Expertise in Explainable AI Applications: A Bearing Fault Diagnosis Case Study. 2025. DOI: 10.1145/3757583.
10. Ojewale V, Suresh H, Venkatasubramanian S. Audit Trails for Accountability in Large Language Models. 2026. arXiv:2601.20727.
11. Rochon J. Sample size for repeated measures studies with binary responses. 1994. DOI: 10.1002/SIM.4780131205.
12. Sample-Size Requirements for Comparisons of Two Groups on Repeated Observations of a Binary Outcome. 2004. DOI: 10.1177/0163278703261198.
13. Sample Size Requirements for Clinical Trials with Repeated Binary Outcomes. 2008. DOI: 10.1177/009286150804200202.
