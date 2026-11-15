# W3-04 — B1 claim–evidence consistency check: design specification

**Date:** 15 November 2026 · **Scope:** ISO/IEC 42001 Clause 4.3, C4-Q03 only · **Status:** `PROPOSED_NOT_APPROVED` (engineering design; research-lead decisions listed in §9)

B1 is exactly **one** intervention on top of the unchanged B0 baseline. It does not run B0, read reference labels, score anything or establish a scientific result.

## 1. Purpose

B0 can return `EVIDENCED` when evidence identifiers are accepted upstream and no auditor flag is raised, without comparing the scope claim to the cited passage (see `PHASE1_TECHNICAL_AUDIT.md`). B1 asks one additional question before a positive conclusion may be released: **does the cited evidence text support this specific claim?** The four reference categories are distinguished: `SUPPORTED`, `INSUFFICIENT`, `CONTRADICTED`, `IRRELEVANT`. A fifth outcome, `AMBIGUOUS`, routes to human review.

## 2. Position in the workflow

```text
paired authorized input (no labels) ─┬─► B0 (pinned a561e7d…, unchanged) ─► captured operational disposition
                                     └─► B1 check on the same claim + cited evidence text
                                                 │
 final disposition = ACCEPT only if  B0 = ACCEPT  AND  check = SUPPORTED  AND  no technical failure
```

B1 lives in `src/b1_consistency_check.py`. It consumes B0's already-captured outcome (`operational_disposition`, `technical_failure`); it never imports or patches the Toolkit.

## 3. Decision policy (explicit, hash-pinned)

| B0 result | B1 check | Final disposition | Positive report entry released | Notes |
| --- | --- | --- | --- | --- |
| ACCEPT | SUPPORTED | ACCEPT | yes | only path that releases |
| ACCEPT | INSUFFICIENT / CONTRADICTED / IRRELEVANT | WITHHOLD | no | `B1_DOWNGRADE_<outcome>` |
| ACCEPT | AMBIGUOUS | WITHHOLD | no | `human_review_required = true` |
| ACCEPT | technical failure | none | no | no disposition; counted as a technical failure, not a withhold |
| WITHHOLD | any | WITHHOLD | no | **never upgraded**; check recorded for information |
| technical failure / none | not applied | none | no | passed through |

Properties: **downgrade-only** (B1 false acceptance ≤ B0 false acceptance; B1 false rejection ≥ B0 false rejection, by construction) and **fail-safe** (every error path blocks the positive entry). `paired_difference_rows` raises if an upgrade ever appears.

## 4. Interfaces

Input to `check_claim_evidence(case)`: `case_id`, `claim_text`, `evidence_items=[{evidence_id, text}]`, `cited_evidence_ids`, optional `organization`. Any key in the repository's restricted-field list (reference/label/adjudication/…) at any depth is rejected (`RESTRICTED_FIELD_PRESENT`). Input is deep-copied; the caller's data is never modified.

Output record: `status` (`OK`/`TECHNICAL_FAILURE`), `outcome`, `reason_codes`, `claim_sha256`, `cited/resolved/unresolved_evidence_ids`, per-evidence `evidence_sha256`, matched sentences (`evidence_id`, `sentence_index`, overlap, polarity), `policy_id`, `policy_sha256`, `judge_id`, `b1_version`, `input_flags`.

Technical failure codes: `INPUT_MALFORMED`, `RESTRICTED_FIELD_PRESENT`, `DUPLICATE_EVIDENCE_ID_CONFLICT`, `JUDGE_OUTPUT_INVALID`, `UNEXPECTED_ERROR`. The function never raises; failure detail never echoes exception text.

Citation handling: duplicate cited IDs are de-duplicated and flagged; an ID that does not resolve is recorded, evaluated only on resolvable evidence, and **blocks automatic support** (`SUPPORTED` → `AMBIGUOUS`); if nothing resolves the outcome is `INSUFFICIENT`.

## 5. Judge

`ConsistencyJudge` is a small protocol, so the deterministic default and any later LLM judge are separate components with a recorded `judge_id`. Only the deterministic judge exists. Any judge output outside the five outcomes is a technical failure.

**`lexical-v1` (default).** Reproducible, no model, no network:
1. Material claim terms = stemmed content words minus stop words, negation cues, generic C4-Q03 boilerplate (`aims`, `scope`, `organization`, `management`, …) and the organisation's own name.
2. **Anchors** = numbers and names capitalised mid-sentence in the claim. Every anchor must appear in the evidence, or the outcome is at most `INSUFFICIENT` (`MISSING_ANCHOR_TERM`).
3. Polarity (inclusion vs exclusion) is detected from negation/exclusion cues. A sentence overlapping ≥ 0.50 of claim terms with opposite polarity → `CONTRADICTED`; with a supporting passage as well → `AMBIGUOUS`.
4. Coverage < 0.25 → `IRRELEVANT`. Coverage ≥ 0.85 with one same-polarity sentence covering ≥ 0.60 → `SUPPORTED`; ≥ 0.85 but scattered → `AMBIGUOUS`; 0.25–0.85 → `INSUFFICIENT`.

All thresholds live in `B1Policy`; any change changes `policy_sha256`.

## 6. Traceability and integrity
Every result carries claim/evidence hashes, resolved vs unresolved IDs, matched sentence indices, policy and judge identity. B1 does not rewrite evidence or reference labels, writes no files, and imports no scorer, adapter or Toolkit code (asserted by a test).

## 7. Human review
`AMBIGUOUS` is a non-positive operational outcome with `human_review_required = true`. It is reported as its own count, never silently treated as support.

## 8. Known limitations (engineering, measured on synthetic fixtures)
- Lexical matching cannot recognise paraphrase. Fixture `SYN-L01` (a wording a human would accept) is **not** supported → a **false-rejection risk** for B1.
- A contradiction with no negation cue (`SYN-L02`) is labelled `INSUFFICIENT`, not `CONTRADICTED`; it is still withheld, so the safety property holds but the category is wrong.
- Negation detection is cue-based; unusual constructions can be misread.
- The thresholds were set on synthetic fixtures authored for this module, not tuned on the 20 benchmark cases (which are not in this repository). They must be **frozen and hashed before any paired run**.
- B1 can only reduce positive conclusions. If B0 produces no incorrect acceptance on the authorized run, B1 shows no benefit.

## 9. Decisions needed from the research lead
1. Is `lexical-v1` the B1 for MVP2, or is a separately pinned LLM judge required (a second, separate design)?
2. Accept `AMBIGUOUS → WITHHOLD + human review` as an operational withhold, reported separately?
3. Accept the positive C4-Q03 **report decision entry** as the endpoint (not a native `Finding`)?
4. Predeclare the "unacceptable false rejection" limit and freeze `policy_sha256` before the paired run.
5. Integration item: confirm how the staged case's `evidence_items` map to B1's `{evidence_id, text}` shape (not verifiable here; no payloads in the repository).

```text
B1_DESIGN=PROPOSED_NOT_APPROVED
B1_IMPLEMENTATION=PROTOTYPE_ENGINEERING_ONLY
B1_INTERVENTION=NOT_EVALUATED
G4_ACTUAL_SCIENTIFIC_SCORING=NOT_AUTHORIZED
```
