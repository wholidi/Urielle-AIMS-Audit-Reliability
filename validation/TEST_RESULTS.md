# Test results

## Recorded internal Week 1 run

The original operational-control suite ran on 6 November 2026 against the
authorized local benchmark:

```text
Ran 13 tests in 3.891s

OK
```

Machine-readable source evidence recorded `tests_run: 13`, `failures: 0`,
`errors: 0`, and `skipped: 0`. This is a historical validation result, not a
fresh public benchmark run.

## Public repository rerun

Run from the repository root with:

```powershell
python -m unittest discover -s tests -v
```

The public rerun result is recorded after publication preparation below. Tests
that require the unreleased benchmark are expected to skip unless an authorized
local path is supplied in `URIELLE_BENCHMARK_DIR`. The remaining tests use only
temporary synthetic fixtures and standard-library dependencies.

Executed on 6 November 2026 with Python 3.12.0:

```text
Ran 13 tests in 0.186s

OK (skipped=6)
```

Seven tests passed and six benchmark-dependent staging tests were skipped. No
test failed or errored. The import check for all three public modules also
passed. No benchmark case and no baseline experiment was executed.

## Test-harness provenance

The three files in `src/` are byte-for-byte copies of the internally tested
control scripts. `tests/test_operational_controls.py` is not byte-identical to
the internal test file: its import path and benchmark discovery were made
portable, and benchmark-dependent methods are explicitly skipped when the
unreleased data are absent. No tested control assertion was weakened or
reclassified as a pass. Opaque internal fixture identifiers were also replaced
with runtime discovery or content-neutral synthetic identifiers to avoid
publishing benchmark metadata.
