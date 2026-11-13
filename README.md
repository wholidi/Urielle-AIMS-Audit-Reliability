# Urielle AIMS Audit Reliability

**When AI Auditors Get It Wrong: Evaluating Evidence Grounding and Unsupported Conclusions in Agentic AI Systems**

AI safety research on evidence grounding, unsupported audit conclusions, and uncertainty, using the [Urielle ISO/IEC 42001 AIMS Toolkit](https://github.com/wholidi/Urielle-ISO42001-AIMS-Toolkit) as the system under test. Developed during the **OdySEA Fall 2026 AI Safety Fellowship — Technical Project Track**.

## Research question

Can a deterministic agentic AI assurance workflow propagate incorrectly accepted evidence into positive audit findings, and can one claim–evidence consistency check reduce such errors?

The experiment focuses on **Clause 4.3 (AIMS Scope), C4-Q03**. It examines whether evidence supports individual scope claims rather than testing full ISO/IEC 42001 conformity.

## Research milestones

| Phase | Work | Status (13 Nov 2026) |
| --- | --- | --- |
| Week 1 | Baseline technical audit, 20-case synthetic benchmark and reference calibration | **Closed — advisory milestone, 12/12 tasks** |
| Week 2 / MVP1 | Exploratory baseline run, offline reporting, and controlled scientific scoring | **Exploratory + engineering complete; scientific milestone HOLD** |
| Week 3 | Resolve provenance, isolation, label freeze and scoring authorization prerequisites | **Prioritized; not yet authorized to score** |
| Later / MVP2–MVP3 | Controlled intervention, comparative evaluation and findings | **Pending scientific baseline** |

## Documentation

- [Week 1 closure](docs/WEEK1_CLOSURE.md)
- [Phase 1 technical audit](docs/PHASE1_TECHNICAL_AUDIT.md)
- [Research methodology](docs/METHODOLOGY.md)
- [Benchmark publication boundary](benchmark/README.md)
- [Week 1 validation](validation/WEEK1_VALIDATION.md)
- [Public test results](validation/TEST_RESULTS.md)
- [Week 2 / MVP1 baseline plan](docs/WEEK2_MVP1_PLAN.md)
- [Week 2 progress (13 Nov 2026)](docs/WEEK2_PROGRESS_2026-11-13.md)
- [Week 3 handover and authorization gates](docs/WEEK3_HANDOVER_2026-11-13.md)

## Evidence and limitations

The benchmark contains **20 synthetic cases** and **23 hash-verified evidence files**. Reference judgments are research-lead calibrated, **not independently blinded human ground truth**. The benchmark is **not formally frozen**. One **20-case exploratory B0/R2 run** produced raw operational decisions; the experimental evidence was reported as sealed and independently verified in the 13 November Week 2 audit. This does **not** establish a formally isolated E4 run or scientific accuracy. Deterministic G4 reporting engineering passed **16/16 targeted tests**, but **no authorized comparison with a frozen reference set has been completed**. False-acceptance, false-rejection and other scientific baseline metrics remain unavailable. Actual G4 scoring is **not authorized**, and original Week 2/MVP1 exit criteria remain **unmet**.

This research repository is separate from the underlying [Urielle Toolkit](https://github.com/wholidi/Urielle-ISO42001-AIMS-Toolkit). It does not modify the production application.

**Publication boundary:** Restricted reference labels, original reviewer logs, adjudication mappings, label-bearing reports, unreleased datasets, private archive material, sealed exploratory outputs, personal records and local paths do not belong in this public repository. See the Week 2 progress record for public-safe status descriptions.

**Status terminology:** Week 1 design/advisory closure is historical and remains unchanged. Week 2 engineering completion is distinct from administrative-period closure (under review) and scientific milestone completion (**HOLD**).
