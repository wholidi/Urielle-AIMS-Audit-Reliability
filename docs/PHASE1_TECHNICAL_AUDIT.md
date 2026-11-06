# Phase 1 technical audit — Week 1 evidence

**Audit date:** 6 November 2026
**Scope:** ISO/IEC 42001 Clause 4.3, toolkit question `C4-Q03`
**Status:** Week 1 technical and design work complete; baseline experiment not run

## System inspected

The audit inspected the clean Urielle MVP1 source at commit
`a561e7d9f73cecb0ccd7d0823dfc481bc5a7ea37`. The commit matched the intended
baseline and its worktree was clean when verified on 6 November 2026. The
separate original working tree was not used as an execution source.

The relevant path is deterministic. The Clause 04 calculation entry point
scores response structure and extracts evidence references. The governed
`EvidenceAssessor._derive_decision` then derives its state from the presence of
evidence identifiers, evidence-integrity review states, and `auditor_flag`. It
does not inspect whether the evidence text semantically supports or contradicts
the target claim, and it invokes no LLM or external model.

The observed decision rule was:

- no extracted evidence identifiers → `NOT_EVIDENCED`;
- all referenced evidence accepted and no auditor flag → `EVIDENCED`;
- at least one accepted reference in other circumstances → `PARTIALLY_EVIDENCED`;
- otherwise → `REQUIRES_HUMAN_JUDGEMENT`.

This creates the research risk under study: an accepted upstream evidence
disposition can influence a positive downstream state without an independent
claim–evidence semantic consistency check. This is a code-path finding, not a
measured experimental error rate.

## Week 1 technical evidence

- A 20-case synthetic benchmark was structurally validated.
- All 23 declared evidence-file SHA-256 hashes matched.
- The benchmark contains five research-lead-calibrated cases in each of four
  semantic categories. The mappings and labels remain restricted and are not
  published here.
- The clean toolkit baseline commit and clean worktree were verified.
- Fail-closed staging, paired-input comparison, and calibration-log verification
  controls were implemented outside the protected toolkit.
- The internal operational-control suite passed 13 of 13 tests with zero
  failures, errors, or skips.

The reference judgments are research-lead calibration, not independently
blinded human ground truth. The benchmark remains
`RESEARCH_REVISION_NOT_FROZEN`. No complete 20-case baseline experiment and no
intervention experiment had been run at Week 1 closure.

## Publication boundary

The public `src/` controls are byte-for-byte copies of the internally tested
scripts. The public test harness preserves the original assertions but differs
only to locate imports under `src/`, accept an optional benchmark path through
`URIELLE_BENCHMARK_DIR`, and skip unreleasable benchmark-dependent tests when
that dataset is absent. See `validation/TEST_RESULTS.md` for both the recorded
internal run and the public rerun.

Not published: benchmark case/evidence bytes, restricted labels and category
mappings, reviewer calibration CSVs and rationales, adjudication mappings,
generated run reports containing local paths, the organizationally marked
project proposal, virtual environments, caches, or protected toolkit source.

## Completed work versus MVP1

Week 1 established the audit finding, benchmark integrity facts, candidate
protocol material, and operational controls. MVP1 remains future work: approve
the measured outcome and scoring protocol, resolve calibration-log provenance
and environment locking, formally freeze approved inputs, implement/approve the
research adapter, perform a content-neutral smoke test, and only then run and
score the 20-case unchanged baseline. No result in this repository should be
read as a baseline performance estimate or a claim of full reproducibility.
