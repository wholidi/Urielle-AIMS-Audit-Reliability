# MVP1 research prototype closure — public summary

**Reporting date:** 14 November 2026
**Scope:** ISO/IEC 42001 Clause 4.3, C4-Q03
**Closure scope:** Baseline Research Prototype and Evidence-Grounding Case Study

```text
MVP1_PROTOTYPE_CLOSURE=APPROVED_WITH_LIMITATIONS
MVP1_SCIENTIFIC_EVALUATION=NOT_COMPLETED
B0_SCIENTIFIC_ACCURACY=NOT_ESTABLISHED
REFERENCE_LABEL_FREEZE=PENDING
B0_EVALUATOR_ISOLATION=NOT_VERIFIED
B1_INTERVENTION=NOT_EVALUATED
G4_ACTUAL_SCIENTIFIC_SCORING=NOT_AUTHORIZED
```

## Decision provenance

A local research-lead decision copy reports `APPROVE_WITH_LIMITATIONS`, an attestation at 14 November 2026, 16:24 Singapore time, and a current disposition of approved. Its header still says “DRAFT — RESEARCH-LEAD REVIEW PENDING.” No corrected, independently authenticated decision record was available for this publication review. This summary records the **research-lead-reported** disposition; it does not independently authenticate the typed attestation or reconcile the conflicting header. The original copy remains outside the proposed public commit. Documentary reconciliation is outstanding.

This narrow prototype closure leaves the historical [Week 1 advisory closure](WEEK1_CLOSURE.md) and [Week 2 scientific HOLD](WEEK2_PROGRESS_2026-11-13.md) intact. The original Week 2 exit criterion of a reproducible scored baseline remains unmet and has not been retrospectively changed. The [Week 3 handover](WEEK3_HANDOVER_2026-11-13.md) retains separate authorization gates.

## Verified work and boundaries

The [Week 1 record](WEEK1_CLOSURE.md) documents a 20-case synthetic C4-Q03 benchmark, with five calibrated cases each in `SUPPORTED`, `INSUFFICIENT`, `CONTRADICTED`, and `IRRELEVANT`, plus 23 evidence files checked against declared hashes. Research-lead calibration involved the author and is **not independent blinded ground truth**. Case payloads and case-to-label mappings are withheld.

The pinned deterministic Toolkit baseline was recorded at commit `a561e7d9f73cecb0ccd7d0823dfc481bc5a7ea37`. A separate 14 November read-only MVP1-R engineering verification matched 44 permitted staged evaluator files: 20 case JSON files, 23 evidence files, and one manifest. The separate Toolkit checkout was reported clean. These checks establish input and source identity within their recorded scope; they do not freeze reference labels or verify evaluator isolation.

The [Week 2 record](WEEK2_PROGRESS_2026-11-13.md) describes one historical exploratory 20-case B0/R2 raw-decision execution and deterministic G4 offline reporting engineering. The sealed exploratory artifacts were reported independently verified. G4 reporting engineering passed 16 targeted dummy tests. Later MVP1-R engineering verification reported 60 tests run, 54 passed, six skipped, zero failures, and prepared a gated harness, label-free trace capture, and reproducibility materials. These are engineering results. No fresh authorized isolated B0 scientific run, approved reference-label join, or actual G4 scientific scoring followed.

## Evidence-grounding finding

The [source audit](PHASE1_TECHNICAL_AUDIT.md) found that the pinned C4-Q03 decision path uses evidence identifiers, upstream integrity/reviewer acceptance, and an auditor flag. With accepted references and no flag, it can return `EVIDENCED` without comparing a scope claim to the cited passage. It invokes no LLM semantic consistency check. Reference identity and file integrity therefore can pass while semantic support remains insufficient, contradicted, or irrelevant.

A governed positive C4-Q03 **report decision entry** is the proposed downstream endpoint for later tracing. The pinned `FindingGenerator.generate()` skips `EVIDENCED`; this path does not establish a positive native `Finding` object. No authorized result demonstrates a complete negative-reference-to-positive-report propagation event or measures its frequency. See the [public working paper](MVP1_C4Q03_Auditor_Working_Paper_Case_Study.md).

## Scientific limits and MVP2 handover

There is no approved frozen reference-label identity, accepted actual evaluator isolation, fresh authorized B0 run, or authorized G4 scientific scoring. False acceptance, false rejection, withholding, decision coverage, technical failure rates, and downstream propagation rates have not been scientifically established. B1 effectiveness is untested. The 20 synthetic cases cover one audit question and do not demonstrate complete ISO/IEC 42001 conformity.

**Hypothesis:** One additional claim–evidence consistency check may reduce incorrect acceptance of unsupported evidence and associated positive audit-report conclusions.

A controlled B0/B1 comparison should use the same approved 20-case benchmark, an approved reference-label identity, verified evaluator isolation, predeclared false-acceptance and false-rejection metrics, withholding and decision coverage, technical failures, and verified downstream report-entry propagation traces. It requires separate protocol, execution, reference-freeze, and scoring decisions. The B1 intervention has not been evaluated. See the [presentation brief](MVP1_Capstone_Presentation_Brief_2026-11-14.md).
