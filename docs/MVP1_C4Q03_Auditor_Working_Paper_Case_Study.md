# C4-Q03 auditor working paper — synthetic evidence-grounding case study

**Scope:** An individual ISO/IEC 42001 Clause 4.3 AIMS scope claim. This public model does not disclose synthetic case payloads or make a client conformity finding.

```text
Client AIMS document → scope claim → evidence reference → AI-assisted assessment → human oversight → claim-level conclusion
```

| Step | Working-paper question |
| --- | --- |
| Client AIMS document | Which controlled source states the proposed scope? |
| Scope claim | What exact inclusion, exclusion, or boundary assertion needs support? |
| Evidence reference | Which document and passage are cited, and do their identities and hashes match? |
| AI-assisted assessment | Does the passage support, leave open, contradict, or miss that assertion? |
| Human oversight | Has a reviewer checked the exact claim, passage, provenance, and uncertainty? |
| Claim-level conclusion | What conclusion does this evidence warrant for this claim alone? |

This is a proposed auditor workflow. The observed pinned B0 implementation is deterministic and does **not** itself perform an LLM semantic consistency check. Identity and integrity acceptance verifies the referenced file, not whether its content supports the scope claim. [Source audit](PHASE1_TECHNICAL_AUDIT.md).

The [20-case benchmark](WEEK1_CLOSURE.md) uses four research-lead-calibrated semantic categories, five cases per category:

| Category | Meaning for a claim–passage pair |
| --- | --- |
| `SUPPORTED` | The passage substantiates the material assertion. |
| `INSUFFICIENT` | A relevant passage leaves a material part unestablished. |
| `CONTRADICTED` | The passage materially conflicts with the assertion. |
| `IRRELEVANT` | The passage does not address the assertion. |

Calibration is not independent blinded ground truth. The categories are not native Toolkit decisions or public case-to-label mappings. The pinned rule can assign `EVIDENCED` from accepted references and no auditor flag without checking semantic support. A positive C4-Q03 report decision entry is distinct from a native `Finding` object, which this pinned path does not generate for `EVIDENCED`. The code establishes a plausible mechanism; no authorized scientific result measures downstream error propagation. [Closure summary](MVP1_Research_Prototype_Closure_2026-11-14.md).

```text
MVP1_SCIENTIFIC_EVALUATION=NOT_COMPLETED
B0_SCIENTIFIC_ACCURACY=NOT_ESTABLISHED
REFERENCE_LABEL_FREEZE=PENDING
B0_EVALUATOR_ISOLATION=NOT_VERIFIED
B1_INTERVENTION=NOT_EVALUATED
G4_ACTUAL_SCIENTIFIC_SCORING=NOT_AUTHORIZED
```
