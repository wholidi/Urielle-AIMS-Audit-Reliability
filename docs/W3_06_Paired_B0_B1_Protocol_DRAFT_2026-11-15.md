# W3-06 — Paired B0/B1 experimental protocol (draft)

**Date:** 15 November 2026 · **Status:** `DRAFT_NOT_APPROVED` · **Scope:** C4-Q03 · This draft authorizes nothing. It extends `MVP1R_Lean_Scientific_Protocol_PROPOSED_2026-11-14.md`; it does not replace B0 prerequisites.

## 1. Design
Same 20 ordered cases and same authorized evaluator inputs for both arms. Arm **B0** = pinned baseline unchanged. Arm **B1** = B0 outcome + one consistency check (`ADR-B1-001`). Paired unit = `(case_id, condition_id = R2)`.

## 2. Preconditions (all separate gates, none granted here)
Approved protocol and B1 design; verified inputs (44 files); `B0_ISOLATION=VERIFIED`; frozen reference identity (hash, custodian, decision time); pinned `b1_consistency_check.py` SHA-256 and `policy_sha256` recorded **before** the run; fresh authorized B0 run sealed before any join; separate scoring authorization. Reference labels are never given to B0 or B1.

## 3. Pairing identity
Run `paired_input_gate.compare` on B0 and B1 input records; any mismatch in canonical case payload or reviewer condition input is a hard stop. B1 consumes the captured B0 outcome of the same case; case-ID mismatch blocks release.

## 4. Per-case table
Controlled scoring area only. Columns: `case_id` · reference support (frozen label) · B0 disposition · B1 disposition · change (`UNCHANGED` / `DOWNGRADED` / `NO_DISPOSITION`) · B1 reason · check outcome · human-review flag · correctness of B0 · correctness of B1 · discordance. Label-free rows come from `paired_difference_rows`; the reference column is joined only inside the authorized scoring step.

## 5. Metrics (both arms; counts and exact fractions)
False acceptance = `ACCEPT` on `NEGATIVE` / 15 · false rejection = `WITHHOLD` on `SUPPORTED` / 5 · decision coverage = valid dispositions / 20 · withhold count / 20 · technical failures / 20 (separate, no disposition) · human-review count / 20 · positive report entries released.
**Paired comparison:** negatives downgraded by B1 (benefit) · supported cases downgraded by B1 (harm) · unchanged. Because B1 is downgrade-only, report these discordant counts, not a significance test; n = 20.
Semantic citation correctness stays `NOT_EVALUABLE` without an approved passage-level reference.

## 6. Outcome handling
Technical failures stay in the 20-slot denominators and are never counted as correct withholds. No silent retries, no post-hoc case replacement, no tuning after outcomes are seen. If B0 has **no** incorrect acceptance on the authorized run, state that B1 has nothing to reduce (RQ1 not demonstrated, RQ2 not testable) rather than reporting a benefit.

## 7. Research-lead predeclarations required
(a) tolerated number of supported cases downgraded by B1; (b) `AMBIGUOUS` treated as withhold with human review; (c) endpoint = positive report decision entry; (d) judge identity and `policy_sha256` frozen.

## 8. Reproducibility checklist
- [ ] B0 commit `a561e7d9f73cecb0ccd7d0823dfc481bc5a7ea37` and clean worktree verified
- [ ] `b1_consistency_check.py` SHA-256 and `policy_sha256` recorded pre-run
- [ ] Input manifest (44 files) match; paired-input gate PASS
- [ ] Isolation evidence under the actual evaluator identity
- [ ] Sealed B0 ledger and B1 result records with hashes
- [ ] Frozen reference identity; separate scoring authorization
- [ ] Per-case table and aggregates independently verified
- [ ] Limitations stated: 20 synthetic cases, one clause, research-lead-calibrated reference, lexical judge

## 9. Limitations
Twenty synthetic cases support descriptive counts only. Reference judgments are research-lead calibrated, not independent blinded ground truth. B1 `lexical-v1` is shallow (see design §8). Results do not imply ISO/IEC 42001 conformity.

```text
PAIRED_EXPERIMENT=NOT_AUTHORIZED
B1_INTERVENTION=NOT_EVALUATED
G4_ACTUAL_SCIENTIFIC_SCORING=NOT_AUTHORIZED
```
