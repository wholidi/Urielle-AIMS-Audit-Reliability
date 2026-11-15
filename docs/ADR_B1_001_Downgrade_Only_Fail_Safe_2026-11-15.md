# ADR-B1-001: B1 is downgrade-only and fails safe

**Date:** 2026-11-15 · **Status:** Proposed (research-lead decision pending) · **Scope:** C4-Q03, MVP2

## Context
MVP2 must test whether **one** claim–evidence consistency check reduces unsupported positive conclusions without unacceptable false rejection. Attribution fails if the intervention can also change B0's non-positive decisions or if errors silently become decisions.

## Decision
1. B1 may change a B0 `ACCEPT` to `WITHHOLD`. It may never change a B0 `WITHHOLD` or a technical failure into `ACCEPT`.
2. A positive report entry is released only if B0 = `ACCEPT`, the check = `SUPPORTED`, and no technical failure occurred.
3. Any input defect, restricted field, judge error or unexpected exception returns a typed technical failure; it is never raised and never counted as a withhold or as support.
4. B1 is implemented separately; B0 and the pinned Toolkit are not modified.

## Consequences
- Paired comparison is clean: B1 false acceptance ≤ B0; B1 false rejection ≥ B0. Gains and harms are the discordant pairs.
- B1 cannot recover a supported case that B0 withheld; that is outside MVP2's single-intervention scope.
- The 20-slot denominators remain intact because technical failures carry no disposition.
- Enforced by tests (`WrapperPolicy`, `PairedTable`) and a runtime invariant check in `paired_difference_rows`.
