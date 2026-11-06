# Benchmark publication status

The Week 1 benchmark contains 20 synthetic `C4-Q03` cases and 23 evidence
files. Structural validation found all 20 cases and all 23 evidence files, and
every declared evidence SHA-256 matched the corresponding file.

The benchmark is **not formally frozen** and its case files, evidence files,
reference labels, category mappings, calibration records, adjudication records,
and rationales are intentionally not included in this repository. Release
requires separate research-lead approval and a leakage/privacy review.

The reference judgments are research-lead calibration, not independent blinded
ground truth. The public count and integrity facts do not disclose which label
belongs to any case.

The staging utility in `src/stage_evaluator.py` can build a strict evaluator-only
view from an authorized local benchmark. It does not download or reconstruct
the benchmark, and running it is not part of this publication task.
