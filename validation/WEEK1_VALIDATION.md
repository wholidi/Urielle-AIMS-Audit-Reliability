# Week 1 validation record

**Validation date:** 6 November 2026

| Item | Actual Week 1 result | Publication status |
| --- | --- | --- |
| Synthetic cases | 20 structurally validated | Counts only; case content withheld |
| Evidence integrity | 23/23 declared SHA-256 hashes matched | Aggregate result only |
| Operational controls | 13/13 tests passed; 0 failures, 0 errors, 0 skips | Scripts and sanitized harness published |
| Clean toolkit baseline | Commit `a561e7d9f73cecb0ccd7d0823dfc481bc5a7ea37`; clean worktree | Commit identity published |
| Baseline behavior | Deterministic decision path; no LLM/external model in the assessed component | Audit description published |
| Reference judgments | Research-lead calibration | Labels and source records withheld |
| Benchmark freeze | Not frozen | Explicit limitation |
| Full baseline experiment | Not run | No performance results claimed |

## Operational controls validated internally

The recorded 13-test run covered:

- exact benchmark counts, evidence hashes, staged inventory, and uniform times;
- deterministic staging across two destinations;
- rejection of path traversal, absolute paths, links/reparse points, duplicate
  case paths, forbidden files, and structured label fields;
- paired baseline/intervention input equality after canonical JSON
  normalization, including fail-closed mismatches and duplicate/missing pairs;
- calibration-log checksum and 20-row completeness checks, including detection
  of a byte change.

These tests exercised controls and fixtures; they did not execute a baseline
study case, calculate error rates, or test the planned semantic intervention.

## Outstanding readiness limits

At Week 1 closure, the original completed calibration exports were unavailable
at the specified archive location, the execution environment was not
hash-locked, and the candidate protocol's semantic-outcome description did not
yet match the deterministic baseline implementation. Those issues block formal
freeze and experimental execution, but do not invalidate the recorded control
test result.
