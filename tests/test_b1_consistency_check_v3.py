"""Engineering tests for MVP2 B1. Synthetic fixtures only; no benchmark case, no
reference label, no B0 toolkit execution, no scoring. Passing these tests is
engineering verification, not scientific evidence."""
import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import b1_consistency_check_v3 as b1
import paired_input_gate

FIXTURES = json.loads((ROOT / "tests" / "fixtures" / "b1_synthetic_fixtures_v3.json").read_text("utf-8"))["fixtures"]


def make_case(**over):
    base = {"case_id": "SYN-T01", "organization": "Zephyr Freight Ltd",
            "claim_text": "The AIMS scope includes the route-optimisation model deployed in the Rotterdam hub.",
            "evidence_items": [{"evidence_id": "EV-T1",
                                "text": "The AIMS scope includes the route-optimisation model deployed in the Rotterdam hub."}],
            "cited_evidence_ids": ["EV-T1"]}
    base.update(over)
    return base


def b0(cid="SYN-T01", disposition="ACCEPT", failure=None):
    return {"case_id": cid, "operational_disposition": disposition, "technical_failure": failure}


class FixtureOutcomes(unittest.TestCase):
    def test_each_fixture_matches_its_engineering_expectation(self):
        for fx in FIXTURES:
            with self.subTest(fx["fixture_id"]):
                result = b1.check_claim_evidence(fx["case"])
                self.assertEqual(result["status"], "OK")
                self.assertEqual(result["outcome"], fx["engineering_expectation"])

    def test_safety_property_nothing_unsupported_is_ever_supported(self):
        """Core B1 safety claim on the fixtures: only a SUPPORTED-intent, non-limitation
        fixture may come back SUPPORTED. Failures of this test are blocking."""
        for fx in FIXTURES:
            if fx["intent"] == "SUPPORTED" and not fx["known_limitation"]:
                continue
            with self.subTest(fx["fixture_id"]):
                self.assertNotEqual(b1.check_claim_evidence(fx["case"])["outcome"], "SUPPORTED")

    def test_known_limitations_are_documented_not_hidden(self):
        limited = [f for f in FIXTURES if f["known_limitation"]]
        self.assertGreaterEqual(len(limited), 2)
        l01 = next(f for f in limited if f["fixture_id"] == "SYN-L01")
        # a human-acceptable paraphrase is NOT supported by the lexical judge: false-rejection risk
        self.assertEqual(l01["intent"], "SUPPORTED")
        self.assertNotEqual(b1.check_claim_evidence(l01["case"])["outcome"], "SUPPORTED")

    def test_deterministic(self):
        for fx in FIXTURES:
            self.assertEqual(b1.check_claim_evidence(fx["case"]), b1.check_claim_evidence(fx["case"]))


class InputHandling(unittest.TestCase):
    def failure_code(self, case):
        r = b1.check_claim_evidence(case)
        self.assertEqual(r["status"], "TECHNICAL_FAILURE")
        self.assertIsNone(r["outcome"])
        return r["failure_code"]

    def test_malformed_inputs_fail_safely_without_raising(self):
        bad = [None, "x", [], {}, make_case(claim_text=""), make_case(claim_text=7),
               make_case(case_id=""), make_case(evidence_items="x"), make_case(cited_evidence_ids="EV-T1"),
               make_case(evidence_items=[{"evidence_id": "bad id!", "text": "t"}]),
               make_case(evidence_items=[{"evidence_id": "EV-T1"}]),
               make_case(evidence_items=["EV-T1"]), make_case(cited_evidence_ids=[5]),
               make_case(cited_evidence_ids=["bad id!"])]
        for case in bad:
            with self.subTest(repr(case)[:60]):
                self.assertEqual(self.failure_code(case), "INPUT_MALFORMED")

    def test_missing_evidence(self):
        r = b1.check_claim_evidence(make_case(evidence_items=[], cited_evidence_ids=[]))
        self.assertEqual((r["outcome"], r["reason_codes"]), ("INSUFFICIENT", ["NO_CITED_EVIDENCE"]))

    def test_unresolved_only_id_is_insufficient(self):
        r = b1.check_claim_evidence(make_case(cited_evidence_ids=["EV-NOPE"]))
        self.assertEqual((r["outcome"], r["reason_codes"]), ("INSUFFICIENT", ["NO_RESOLVABLE_EVIDENCE"]))
        self.assertEqual(r["unresolved_evidence_ids"], ["EV-NOPE"])

    def test_unresolved_id_blocks_automatic_support(self):
        r = b1.check_claim_evidence(make_case(cited_evidence_ids=["EV-T1", "EV-NOPE"]))
        self.assertEqual(r["outcome"], "AMBIGUOUS")
        self.assertIn("UNRESOLVED_CITED_ID", r["reason_codes"])

    def test_duplicate_cited_id_is_deduped_and_flagged(self):
        r = b1.check_claim_evidence(make_case(cited_evidence_ids=["EV-T1", "EV-T1"]))
        self.assertEqual(r["outcome"], "SUPPORTED")
        self.assertEqual(r["cited_evidence_ids"], ["EV-T1"])
        self.assertIn("DUPLICATE_CITED_ID_DEDUPED", r["input_flags"])

    def test_duplicate_identical_evidence_item_deduped(self):
        item = {"evidence_id": "EV-T1", "text": make_case()["evidence_items"][0]["text"]}
        r = b1.check_claim_evidence(make_case(evidence_items=[item, dict(item)]))
        self.assertEqual(r["outcome"], "SUPPORTED")
        self.assertIn("DUPLICATE_EVIDENCE_ITEM_DEDUPED", r["input_flags"])

    def test_duplicate_evidence_id_with_different_text_is_a_failure(self):
        items = [{"evidence_id": "EV-T1", "text": "a"}, {"evidence_id": "EV-T1", "text": "b"}]
        self.assertEqual(self.failure_code(make_case(evidence_items=items)), "DUPLICATE_EVIDENCE_ID_CONFLICT")

    def test_reference_label_fields_are_rejected_anywhere(self):
        for key in ("reference_label", "expected_label", "adjudication"):
            with self.subTest(key):
                self.assertEqual(self.failure_code(make_case(**{key: "SUPPORTED"})), "RESTRICTED_FIELD_PRESENT")
        nested = make_case()
        nested["evidence_items"][0]["meta"] = {"Reference_Label": "NEGATIVE"}
        self.assertEqual(self.failure_code(nested), "RESTRICTED_FIELD_PRESENT")

    def test_input_is_never_mutated(self):
        for fx in FIXTURES:
            original = copy.deepcopy(fx["case"])
            b1.check_claim_evidence(fx["case"])
            self.assertEqual(fx["case"], original)

    def test_record_traces_claim_and_evidence_identity(self):
        r = b1.check_claim_evidence(make_case())
        self.assertEqual(r["resolved_evidence_ids"], ["EV-T1"])
        self.assertEqual(len(r["claim_sha256"]), 64)
        self.assertEqual(set(r["evidence_sha256"]), {"EV-T1"})
        self.assertTrue(r["matches"] and r["matches"][0]["evidence_id"] == "EV-T1")


class JudgeSafety(unittest.TestCase):
    def test_judge_exception_becomes_typed_failure(self):
        class Boom:
            judge_id = "boom"
            def judge(self, *a, **k):
                raise RuntimeError("secret detail must not leak")
        r = b1.check_claim_evidence(make_case(), judge=Boom())
        self.assertEqual((r["status"], r["failure_code"]), ("TECHNICAL_FAILURE", "UNEXPECTED_ERROR"))
        self.assertNotIn("secret", json.dumps(r))

    def test_invalid_judge_output_is_failure(self):
        for out in ({"outcome": "MAYBE"}, {}, None, "SUPPORTED"):
            class Bad:
                judge_id = "bad"
                def judge(self, *a, _o=out, **k):
                    return _o
            with self.subTest(repr(out)):
                r = b1.check_claim_evidence(make_case(), judge=Bad())
                self.assertEqual(r["failure_code"], "JUDGE_OUTPUT_INVALID")

    def test_pluggable_judge_identity_is_recorded_and_unresolved_still_blocks(self):
        class Yes:
            judge_id = "always-supported-test-double"
            def judge(self, *a, **k):
                return {"outcome": "SUPPORTED", "reason_codes": ["TEST_DOUBLE"], "matches": []}
        r = b1.check_claim_evidence(make_case(cited_evidence_ids=["EV-T1", "EV-NOPE"]), judge=Yes())
        self.assertEqual(r["judge_id"], "always-supported-test-double")
        self.assertEqual(r["outcome"], "AMBIGUOUS")

    def test_policy_hash_changes_with_any_threshold(self):
        base = b1.B1Policy()
        self.assertEqual(base.sha256(), b1.B1Policy().sha256())
        self.assertNotEqual(base.sha256(), b1.B1Policy(support_coverage_min=0.9).sha256())
        r = b1.check_claim_evidence(make_case(), policy=b1.B1Policy(support_coverage_min=0.9))
        self.assertEqual(r["policy_sha256"], b1.B1Policy(support_coverage_min=0.9).sha256())


class WrapperPolicy(unittest.TestCase):
    def test_b0_withhold_is_never_upgraded(self):
        for fx in FIXTURES:
            with self.subTest(fx["fixture_id"]):
                res = b1.apply_b1(b0(fx["case"]["case_id"], "WITHHOLD"), fx["case"])
                self.assertEqual(res["final_disposition"], "WITHHOLD")
                self.assertFalse(res["release_positive_report_entry"])

    def test_b0_accept_released_only_when_supported(self):
        for fx in FIXTURES:
            with self.subTest(fx["fixture_id"]):
                res = b1.apply_b1(b0(fx["case"]["case_id"], "ACCEPT"), fx["case"])
                supported = fx["engineering_expectation"] == "SUPPORTED"
                self.assertEqual(res["final_disposition"], "ACCEPT" if supported else "WITHHOLD")
                self.assertEqual(res["release_positive_report_entry"], supported)

    def test_reason_and_human_review_mapping(self):
        by = {fx["fixture_id"]: b1.apply_b1(b0(fx["case"]["case_id"]), fx["case"]) for fx in FIXTURES}
        self.assertEqual(by["SYN-C01"]["final_reason"], "B1_DOWNGRADE_CONTRADICTED")
        self.assertEqual(by["SYN-R01"]["final_reason"], "B1_DOWNGRADE_IRRELEVANT")
        self.assertEqual(by["SYN-I01"]["final_reason"], "B1_DOWNGRADE_INSUFFICIENT")
        self.assertTrue(by["SYN-A01"]["human_review_required"])
        self.assertEqual(by["SYN-A01"]["final_disposition"], "WITHHOLD")
        self.assertFalse(by["SYN-S01"]["human_review_required"])

    def test_b0_technical_failure_passes_through_without_disposition(self):
        res = b1.apply_b1(b0(disposition=None, failure="NATIVE_ERROR"), make_case())
        self.assertIsNone(res["final_disposition"])
        self.assertFalse(res["b1_applied"])
        self.assertFalse(res["release_positive_report_entry"])

    def test_b0_accept_with_b1_failure_has_no_disposition_and_blocks_entry(self):
        res = b1.apply_b1(b0(), make_case(claim_text=""))
        self.assertIsNone(res["final_disposition"])
        self.assertEqual(res["final_reason"], "B1_TECHNICAL_FAILURE_ENTRY_BLOCKED")
        self.assertFalse(res["release_positive_report_entry"])

    def test_case_id_mismatch_between_b0_and_b1_input_blocks_entry(self):
        res = b1.apply_b1(b0("SYN-OTHER"), make_case())
        self.assertFalse(res["release_positive_report_entry"])
        self.assertIsNone(res["final_disposition"])

    def test_b0_record_not_mutated(self):
        record = b0()
        before = copy.deepcopy(record)
        b1.apply_b1(record, make_case())
        self.assertEqual(record, before)


class PairedTable(unittest.TestCase):
    def ledgers(self):
        cases = [fx["case"] for fx in FIXTURES]
        ledger = [b0(c["case_id"], "ACCEPT") for c in cases]
        return ledger, [b1.apply_b1(row, c) for row, c in zip(ledger, cases)]

    def test_rows_are_label_free_and_complete(self):
        ledger, results = self.ledgers()
        rows = b1.paired_difference_rows(ledger, results)
        self.assertEqual(len(rows), len(FIXTURES))
        for row in rows:
            self.assertFalse({"reference", "label", "expected"} & {k.split("_")[0] for k in row})
        changes = {r["change"] for r in rows}
        self.assertEqual(changes, {"UNCHANGED", "DOWNGRADED"})

    def test_mismatched_or_duplicate_ids_rejected(self):
        ledger, results = self.ledgers()
        with self.assertRaises(ValueError):
            b1.paired_difference_rows(ledger[:-1], results)
        with self.assertRaises(ValueError):
            b1.paired_difference_rows(ledger + [ledger[0]], results)

    def test_upgrade_is_detected_as_invariant_violation(self):
        ledger = [b0("SYN-T01", "WITHHOLD")]
        forged = [{"case_id": "SYN-T01", "final_disposition": "ACCEPT", "final_reason": "forged",
                   "b1_check": {"outcome": "SUPPORTED"}, "human_review_required": False}]
        with self.assertRaises(ValueError):
            b1.paired_difference_rows(ledger, forged)

    def test_existing_paired_input_gate_accepts_equal_inputs_and_rejects_drift(self):
        case = make_case()
        rec = lambda arm: {"case_id": case["case_id"], "condition_id": "R2", "canonical_case_payload": case,
                           "reviewer_condition_input": {"response": "x"},
                           "implementation_differences": [arm]}
        result = paired_input_gate.compare([rec("B0")], [rec("B1_claim_evidence_check")])
        self.assertEqual(result["status"], "PASS")
        drifted = rec("B1")
        drifted["canonical_case_payload"] = make_case(claim_text="Something else entirely.")
        with self.assertRaises(paired_input_gate.PairingError):
            paired_input_gate.compare([rec("B0")], [drifted])


class Isolation(unittest.TestCase):
    def test_module_does_not_import_b0_or_scoring_or_touch_files(self):
        source = (ROOT / "src" / "b1_consistency_check_v3.py").read_text("utf-8")
        for forbidden in ("g4_offline_scorer", "mvp1r_metrics", "baseline_adapter", "import os",
                          "open(", "subprocess", "pathlib", "requests", "urllib"):
            self.assertNotIn(forbidden, source, forbidden)


if __name__ == "__main__":
    unittest.main()
