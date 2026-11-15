# W3-05 — B1 engineering verification

**Date:** 15 November 2026 · **Scope:** C4-Q03 · **Nature:** engineering verification only. No benchmark case, reference label, B0 run or scoring was used.

## Result
- `src/b1_consistency_check.py` implements the single claim–evidence check, the downgrade-only B0 wrapper and a label-free paired difference table.
- **30 new tests pass** (`tests/test_b1_consistency_check.py`) covering supported, missing, contradictory and irrelevant evidence; unresolved, duplicate and malformed identifiers; restricted fields; judge errors and invalid judge output; B0-withhold-never-upgraded; entry release only on `SUPPORTED`; non-mutation; determinism; and compatibility with the existing `paired_input_gate`.
- **Tests can fail:** two deliberate mutants (allow an upgrade; stop unresolved IDs blocking support) each made the suite fail (3 and 5 failures).
- **No regression:** the existing suite shows the same 7 errors with and without B1 (all need the Windows toolkit path `C:\AI Project\OdySEA_Capstone\W1\toolkit_baseline_clean`, which is absent in the sandbox), going from 50 to 80 tests. Your local run (60 passed, 6 skipped) must be repeated after applying the patch; it has not been reproduced here.
- B0 and the pinned Toolkit were not modified. No existing repository file was edited.

## Fixture outcomes (15 synthetic fixtures, authored fresh)
13 produce the intended category. Two further fixtures are deliberately documented limitations (their recorded expectation is the lexical outcome, not the intended category): `SYN-L01` (a human-acceptable paraphrase is **not** supported — false-rejection risk) and `SYN-L02` (contradiction with no negation cue is labelled `INSUFFICIENT`, still withheld). The safety property — no unsupported-intent fixture is ever `SUPPORTED` — holds on all fixtures.

## What this does not show
- Not that B1 reduces false acceptance on the benchmark. B1 is `NOT_EVALUATED`.
- Not that `lexical-v1` is semantically adequate. It is crude by design; see design §8.
- Fixtures are small and written by the same author as the thresholds; they demonstrate behaviour, not accuracy.
- The staged case's `evidence_items` schema was not verifiable here (no payloads); a mapping to `{evidence_id, text}` is an integration item.

## Apply
Copy the new files into `C:\Urielle-AIMS-Audit-Reliability` (no overwrites), then run `python -m unittest discover -s tests -v` and compare with your prior 60-pass baseline. Commit separately.

```text
B1_ENGINEERING_TESTS=30_PASSED_IN_SANDBOX
B1_INTERVENTION=NOT_EVALUATED
MVP1_SCIENTIFIC_EVALUATION=NOT_COMPLETED
G4_ACTUAL_SCIENTIFIC_SCORING=NOT_AUTHORIZED
```
