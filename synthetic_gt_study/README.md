# When AI Auditors Get It Wrong

**OdySEA AI Safety Capstone — Research Study**

**Scope:** ISO/IEC 42001 Clause 4.3 — AI Management System Scope  
**Audit question:** C4-Q03  
**Status:** Study complete (synthetic data). Inputs, runs and analysis were sealed on 18 November 2026, before this README was finalised. The written report is in preparation (freeze 27 November 2026).

## 1. What this study asks

When an AI audit toolkit accepts a claim supported by weak, contradictory, or irrelevant evidence, can a simple post-processing consistency check reduce incorrect acceptance?

What does that intervention cost in terms of incorrectly downgrading claims supported by adequate evidence?

The study compares:

- **B0:** An existing AI audit toolkit, run unmodified at a pinned commit.
- **B1:** A frozen, downgrade-only lexical consistency check (v0.3, `lexical-v3`, without an organisation key).

The objective is to measure error propagation and the trade-off between rejecting unsupported claims and preserving supported ones.

## 2. Study design

This is a synthetic ground-truth evaluation of **200 cases**, produced by two generators (100 cases each). Each generator contributes 25 cases in each of four ground-truth categories: `SUPPORTED`, `INSUFFICIENT`, `CONTRADICTED`, and `IRRELEVANT`. Each case is submitted to B0 using a fixed response template. B0 runs unmodified at a pinned commit, and its output is evaluated both directly and after applying B1. B1 can downgrade a decision but cannot upgrade it. The study compares paired outcomes against the constructed labels.

### Evaluation flow

```text
Two synthetic generators
          |
          v
200 labelled cases
(50 per ground-truth category)
          |
          v
Fixed response template
          |
          v
B0: Pinned audit toolkit
          |
          +--------------------+
          |                    |
          v                    v
    B0 decision         B1 lexical-v3
                              |
                              v
                       Adjusted decision
          |                    |
          +--------------------+
                   |
                   v
          Paired evaluation
                   |
                   v
       Metrics and uncertainty
```

### Pre-declared analysis

- Incorrect-accept rate
- Propagation
- False-downgrade rate
- Coverage
- Wilson 95% confidence intervals
- Exact paired sign test
- Generator and label strata
- Sensitivity analyses with declared exclusions

Metric definitions, denominators, and exclusion rules: defined in the pre-declared protocol amendment and the study decision record (see *Hashes and provenance*). In short: the incorrect-accept rate uses a fixed denominator (all 150 unsupported cases); false-downgrade rate = supported cases that B0 accepted and B1 did not accept, over supported cases that B0 accepted (45/50 here); Wilson 95% intervals throughout; exact two-sided paired sign test; technical failures reported separately and never silently dropped.

## 3. Headline result

**The pre-declared success rule was not met** (`B1_REDUCTION_SUPPORTED = NO`).

| Measure | B0 (toolkit alone) | B0 + B1 |
|---|---|---|
| Incorrect-accept rate (unsupported cases accepted) | 150/150 = 1.000 (Wilson 0.975–1.000) | 0/150 = 0.000 (Wilson 0.000–0.025) |
| Propagation | 150/150 | n/a (0/0) |
| Coverage (cases with a disposition) | 200/200 | 200/200 |
| Technical failures | 0 | 0 |

| Cost of B1 | Result |
|---|---|
| False-downgrade rate (supported claims accepted by B0 but not by B1) | **45/50 = 0.900** (Wilson 0.786–0.957) |
| Pre-declared tolerance (point estimate) | 0.20 |
| Exact paired sign test | b = 150, c = 0, p ≈ 1.4e-45 |

B1 removed every incorrect acceptance, but it did so by withholding 195 of 200 cases, including 45 of the 50 supported ones. The false-downgrade rate is far above the 0.20 tolerance fixed before any run, so the rule (sign-test p < 0.05 **and** false-downgrade point estimate ≤ 0.20) fails on its second condition.

Reading notes:

- **B0 accepts all 200 cases by construction.** The fixed response template never compares claim to evidence, so the B0 result is a property of the template, not a finding about the toolkit's judgement. What the study measures is what B1 changes.
- **The sign test is uninformative here.** B1 can only downgrade, so c = 0 is guaranteed whenever B0 accepts everything; the very small p-value reflects the design, not evidence of a favourable trade-off.
- **Generators differ.** False-downgrade rate was 25/25 = 1.000 for `AUTH_TEMPLATE` and 20/25 = 0.800 for `CHATGPT` (the five accepted supported cases were in families S1, 4 of 8, and S5, 1 of 8). Trap cases: 17/17 = 1.000; non-trap: 28/33 = 0.848.
- **Sensitivity exclusions do not change the picture.** Excluding the 4 cases flagged for second-reading disagreement, the 3 flagged for label ambiguity, or both (196, 197 and 193 cases) leaves the false-downgrade rate at 45/50 = 0.900 and B1 incorrect-accept at 0.
- **Exploratory only (not pre-declared):** B1 kept 5 of 50 supported cases versus 0 of 150 unsupported cases (Fisher exact p ≈ 0.0008). This shows B1's rule has some discrimination; it does not change the pre-declared outcome.
- **Dominant B1 reason code** was `MISSING_ANCHOR_TERM` (118 of 200 cases), consistent with a strict lexical rule applied to constructed evidence.

Detailed results: per-stratum tables (`overall`, `by_generator`, `by_family`, `by_trap`, `by_label`, `sensitivity`) and `metrics.json` / `summary.md` in the analysis output folder; the written report once frozen.

The results above separate error reduction from false downgrades, exclusions, uncertainty and technical failures. Nothing here should be read as evidence about real audits.

## 4. Limitations

This is a controlled synthetic study, not an evaluation of real-world audit performance.

- **Synthetic cases:** The evidence and claims are constructed rather than collected from operational audits.
- **Constructed labels:** Ground truth reflects the study's predefined labelling rules, not independently established organisational facts.
- **Fixed response template:** B0 accepts essentially every case by construction under this template. The experiment primarily tests whether B1 can correct these propagated acceptances, not B0's natural acceptance behaviour.
- **Single run and seed:** The design does not measure variability across repeated runs or random seeds.
- **One audit question:** All cases concern ISO/IEC 42001 Clause 4.3, C4-Q03. Generalisation to other clauses or audit tasks is unknown.
- **ChatGPT generator style uniformity:** Similarities in generated language may make lexical patterns easier to detect than in independently authored or real-world evidence.
- **Sign test:** because B1 is downgrade-only and B0 accepts every case, the paired sign test cannot be unfavourable to B1 and carries no information about the trade-off. The false-downgrade rate is the deciding measure.
- **Partial second reading:** the independent second reading of labels covered only the ChatGPT half; the template half relies on the generator's own construction rules plus a 20-case spot-check.
- **Lexical intervention:** B1 tests a frozen rule-based consistency check, not general semantic understanding or independent evidence verification.

The findings cannot establish effectiveness across organisations, audit contexts, document styles, or independently collected evidence.

## 5. Repository layout

```text
<repo-or-study-root>/
  scripts/     split_cases.py, validate_cases.py, seal_manifest.py,
               merge_halves.py, run_b0_b1.py, analyse.py
  inputs/      cases.jsonl (label-free), flags file, decision record, seal_gate2/
  runs/        real_b0/ (ledger, run manifest), real_b1/ (ledger, paired rows,
               run manifest), seal_gate3/
  analysis/    analysis_real/ (metrics.json, summary.md, CSV tables), seal_analysis/
  docs/        protocol amendment, case-family specification, report
```

> TODO (author to confirm before publishing): final folder names, and which of these folders are published. `labels.jsonl` and the flags file are not part of this public layout until a publication decision is made; without them, steps 5 onward cannot be re-run by a third party, but the sealed hashes below still let a reader check any copy they are later given.

The repository should distinguish frozen inputs, source code, execution outputs, analysis outputs, and provenance records.

## 6. How to reproduce

Prerequisites: Python 3 (standard library only for the study scripts, run with `python -I`); Git; a local checkout of the B0 toolkit at the pinned commit below; the study inputs and their seal manifests.

Run the following stages in order, using the frozen study inputs and specified software versions.

### Step 1 — Seal study inputs

```bash
python -I scripts/seal_manifest.py seal --files <input files> --out-dir <seal folder> --label "<gate label>"
```

### Step 2 — Verify input integrity

```bash
python -I scripts/seal_manifest.py verify --manifest <seal folder>/manifest.json
```

### Step 3 — Run B0 without modification

```bash
python -I scripts/run_b0_b1.py b0 --cases <cases.jsonl> --out-dir <real_b0> --src <scripts folder> --toolkit <toolkit checkout at pinned commit>
```

### Step 4 — Apply frozen B1

```bash
python -I scripts/run_b0_b1.py b1 --cases <cases.jsonl> --b0-ledger <real_b0>/b0_ledger.jsonl --out-dir <real_b1> --src <scripts folder>
```

### Step 5 — Analyse paired outcomes

```bash
python -I scripts/analyse.py --labels <labels.jsonl> --b0-ledger <real_b0>/b0_ledger.jsonl --b1-ledger <real_b1>/b1_ledger.jsonl --paired-rows <real_b1>/paired_rows.jsonl --out-dir <analysis_real> --false-downgrade-tolerance 0.20 --flags-file <flags.json>
```

Complete reproduction instructions: see `--help` on each script for the full option list. Seal the outputs of each gate (Gate 3 after B0/B1, then the analysis) with the same `seal` command, and verify before and after each stage.

Reproduction requires matching the pinned B0 revision, frozen B1 version, input manifest, execution configuration, and declared analysis protocol.

## 7. Hashes and provenance

SHA-256 values, recorded at sealing on 18 November 2026.

| Item | SHA-256 |
|---|---|
| `cases.jsonl` (200 cases, label-free) | `5a555ba99b1ec2ffcc8f7ed0eb7d7ebedeab26f7fb6dc4db5c087fed9f4ddf44` |
| `labels.jsonl` | `2cde02302f6b8bad229550a2caac61f9f631dcc62bdb2c7027e59989b463df81` |
| flags file | `2edd64adecb6b43d01ef1b9a1791e9795d4be760ded7cd67bd9c3566a3246e75` |
| decision record | `d260843ef4d87a584687ad5043471b48609d1cb5df4aefb9989b785226365b9b` |
| `b0_ledger.jsonl` | `e6e9e890411e82bebbc5f32020522681f6e8467e577cd9c61749d404e5931b42` |
| `b0_run_manifest.json` | `ece252edd95ae47bb18b824ba9d5d908a6d24e5e6c6825ae436e8be09e27e4c5` |
| `b1_ledger.jsonl` | `4b0596ec027b1e814d18ae6540117bfb08b6a14b186c504a0b0e3b231a8fb845` |
| `paired_rows.jsonl` | `0b290e8a075c7ca5b499c4cc31b3601609c4710ed918d49be205e986e82cdf59` |
| `b1_run_manifest.json` | `f9f39c88f8a1b26caebecd935593da2f35815dd771e4717dc0370249a1008858` |
| `metrics.json` | `7be31eda19d3c60cd3df4df1229714b6a6808b3c0091208f7e59e82c4e666b31` |
| `summary.md` | `a3116aeb1583ef34c8705f243d0a1872214354b903957585ee6b4701f5efb3bc` |
| B1 policy (`b1-0.3.0`) | `ee8b5195ea5b6f6d9671a202b07f7165dc6d2f1b2fe61a167ddf99d4d5f8ccf5` |
| `run_b0_b1.py` v2 (raw file hash) | `7BB6D5E050FABCE4BA989BB68DBBF45DE8D50E533853FD17F2CCDD385FB9B5CB` |
| `analyse.py` v2 (raw file hash) | `09CCB7CC74EFF0DD6DC43DDFB18DAB8CBC523570351728AE192F7741C0FA3406` |

Seal manifests (`manifest_body_sha256`):

| Seal | Covers | manifest_body_sha256 |
|---|---|---|
| Gate 2 | cases, labels, flags, decision record | `d7d3f1cbdc055dbb818ea082655cac68274efa6304912f3bbd8c3b2cd2b70045` |
| Gate 3 | B0/B1 ledgers, run manifests, paired rows | `ff6d17a54ffb484d51947d902585545de766a4e178352fd68f37f062c25e2fce` |
| Analysis | all analysis output files | `26816a8905120c4b923d23b6a308874db8888b93cb7fe9390a4f136d8073e829` |

**B0 commit:** `a561e7d9f73cecb0ccd7d0823dfc481bc5a7ea37` (toolkit checkout clean before and after the run)  
**B1 version:** `v0.3 lexical-v3` (no organisation key)  
**Input manifest:** Gate 2 seal (above)  
**Output manifest:** Gate 3 seal and analysis seal (above)  
**Execution record:** `b0_run_manifest.json` and `b1_run_manifest.json`: 200 valid B0 runs, 0 technical failures; B1 ACCEPT = 5, WITHHOLD = 195, 0 technical failures  
**Generator provenance:** 100 cases from a template-based generator (`AUTH_TEMPLATE`) and 100 from a ChatGPT-assisted generator (`CHATGPT`), 25 per label each. Case IDs are `SG-` plus 8 hex characters. One ID collision between the two halves was found before any run and fixed by re-splitting the ChatGPT half with a new seed; the superseded split is kept as a record. A 20-case spot-check of label fit passed 20/20; a second reading covered the ChatGPT half only.

Hashes establish file integrity relative to recorded manifests; they do not independently establish label correctness or scientific validity.

## 8. Licence and contact

**Licence:** TODO (author to confirm: licence for code and for data)

**Contact:** TODO (author to confirm)

**Research affiliation:** OdySEA AI Safety Capstone

**Last updated:** 19 November 2026