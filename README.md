# Urielle AIMS Audit Reliability

**When AI Auditors Get It Wrong: Evaluating Evidence Grounding and Unsupported Conclusions in Agentic AI Systems**

AI safety research on evidence grounding, unsupported audit conclusions, and uncertainty, using the [Urielle ISO/IEC 42001 AIMS Toolkit](https://github.com/wholidi/Urielle-ISO42001-AIMS-Toolkit) as the system under test. Developed during the **OdySEA Fall 2026 AI Safety Fellowship — Technical Project Track**.

## Research question

Can a deterministic agentic AI assurance workflow propagate incorrectly accepted evidence into positive audit findings, and can one claim–evidence consistency check reduce such errors?

The experiment focuses on **Clause 4.3 (AIMS Scope), C4-Q03**. It examines whether evidence supports individual scope claims rather than testing full ISO/IEC 42001 conformity.

## Research milestones

| Phase | Work | Status (6 Nov 2026) |
| --- | --- | --- |
| Week 1 | Baseline technical audit, 20-case synthetic benchmark and reference calibration | **Closed — advisory milestone, 12/12 tasks** |
| Week 2 / MVP1 | Run unchanged baseline and score error rates | Planned |
| Week 3 / MVP2 | Add one isolated consistency check, rerun same inputs | Planned |
| Week 4 / MVP3 | Analyze results, limitations and publish findings | Planned |

## Documentation

- [Week 1 closure](docs/WEEK1_CLOSURE.md)
- [Research methodology](docs/METHODOLOGY.md)
- [Week 2 / MVP1 baseline plan](docs/WEEK2_MVP1_PLAN.md)

## Evidence and limitations

The benchmark contains **20 synthetic cases** and **23 hash-verified evidence files**. Reference judgments are research-lead calibrated, **not independently blinded human ground truth**. The benchmark is **not formally frozen**, and **no 20-case baseline run has yet been performed**. Outputs will be reported only after approval of a prospectively defined operational scoring protocol.

This research repository is separate from the underlying [Urielle Toolkit](https://github.com/wholidi/Urielle-ISO42001-AIMS-Toolkit). It does not modify the production application.

**Publication boundary:** Restricted reference labels, original reviewer logs, adjudication mappings, unreleased datasets, personal records, and local paths do not belong in this public repository.
