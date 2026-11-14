# Urielle AIMS Audit Reliability

**When AI Auditors Get It Wrong: Evaluating Evidence Grounding and Unsupported Conclusions in Agentic AI Systems**

OdySEA Fall 2026 AI Safety Fellowship research on ISO/IEC 42001 Clause 4.3, C4-Q03. The system under study is the [Urielle ISO/IEC 42001 AIMS Toolkit](https://github.com/wholidi/Urielle-ISO42001-AIMS-Toolkit). This repository is a separate research record.

```text
MVP1_PROTOTYPE_CLOSURE=APPROVED_WITH_LIMITATIONS
MVP1_SCIENTIFIC_EVALUATION=NOT_COMPLETED
B0_SCIENTIFIC_ACCURACY=NOT_ESTABLISHED
REFERENCE_LABEL_FREEZE=PENDING
B0_EVALUATOR_ISOLATION=NOT_VERIFIED
B1_INTERVENTION=NOT_EVALUATED
G4_ACTUAL_SCIENTIFIC_SCORING=NOT_AUTHORIZED
```

The research-lead-reported disposition closes MVP1 as a **Baseline Research Prototype and Evidence-Grounding Case Study**. The local decision copy contains a conflicting draft header, and independent authentication or a corrected attributable record was not available for this publication review. See the [public closure summary](docs/MVP1_Research_Prototype_Closure_2026-11-14.md). The historical [Week 1 advisory closure](docs/WEEK1_CLOSURE.md) and [Week 2 scientific HOLD](docs/WEEK2_PROGRESS_2026-11-13.md) remain unchanged.

## Evidence-grounding mechanism

```text
Client AIMS document → scope claim → evidence reference → AI-assisted assessment → human oversight → claim-level conclusion
```

This is a proposed auditor working-paper workflow. The pinned B0 C4-Q03 implementation is deterministic; it does **not** perform an LLM semantic consistency check. It uses evidence identifiers, upstream integrity/reviewer acceptance, and an auditor flag. A reference can be the correct, hash-matched file while its passage fails to support the exact scope claim. Accepted references can lead to `EVIDENCED` without a semantic comparison. A positive C4-Q03 **report decision entry** differs from a native `Finding` object: the pinned generator skips `EVIDENCED` Findings. No authorized scientific result demonstrates or measures complete downstream error propagation. See the [source audit](docs/PHASE1_TECHNICAL_AUDIT.md) and [working paper](docs/MVP1_C4Q03_Auditor_Working_Paper_Case_Study.md).

## Research record

| Phase | Recorded status |
| --- | --- |
| Week 1 | Advisory design milestone closed; 20 synthetic cases, 23 hash-checked evidence files, and research-lead calibration. |
| Week 2 | Historical exploratory 20-case B0/R2 raw run and deterministic G4 reporting engineering; original scored-baseline exit criterion unmet. |
| MVP1-R engineering | 44 permitted staged evaluator files matched; pinned separate Toolkit checkout reported clean; prospective harness and reproducibility materials prepared. |
| Scientific evaluation | Reference freeze, actual evaluator isolation, authorized fresh B0 execution, and actual G4 scoring pending. |
| MVP2 | B1 consistency-check effectiveness untested. |

The synthetic benchmark contains five research-lead-calibrated scenarios each in `SUPPORTED`, `INSUFFICIENT`, `CONTRADICTED`, and `IRRELEVANT`. Calibration is **not independent blinded ground truth**. The historical exploratory run supplies raw operational decisions, not scientific accuracy. G4 reporting engineering passed 16 targeted dummy tests; later MVP1-R engineering verification reported 54 passed, six skipped, zero failures. These tests do not authorize label access or scientific scoring.

## Documents

- [Research methodology](docs/METHODOLOGY.md)
- [Benchmark publication boundary](benchmark/README.md)
- [Week 1 closure](docs/WEEK1_CLOSURE.md)
- [Week 2 progress](docs/WEEK2_PROGRESS_2026-11-13.md)
- [Week 3 controlled handover](docs/WEEK3_HANDOVER_2026-11-13.md)
- [MVP1 public closure summary](docs/MVP1_Research_Prototype_Closure_2026-11-14.md)
- [C4-Q03 auditor working paper](docs/MVP1_C4Q03_Auditor_Working_Paper_Case_Study.md)
- [Capstone presentation brief](docs/MVP1_Capstone_Presentation_Brief_2026-11-14.md)

## MVP2 hypothesis

**One additional claim–evidence consistency check may reduce incorrect acceptance of unsupported evidence and associated positive audit-report conclusions.** Test B0/B1 on the same approved 20 cases with approved reference-label identity, verified evaluator isolation, predeclared false acceptance and false rejection, withholding and decision coverage, technical failures, and verified downstream report-entry propagation traces. B1 effectiveness remains untested.

Restricted reference labels, mappings, reviewer logs, adjudication records, sealed exploratory outputs, and sensitive source documents are excluded from this public repository.
