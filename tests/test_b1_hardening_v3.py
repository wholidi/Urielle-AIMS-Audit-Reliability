"""Tests for b1 v0.2 hardening: synthetic adversarial cases authored independently of the
fixtures/benchmark. Engineering only; reads no labels."""
import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import b1_consistency_check_v3 as b

CASES = {
 "omission_verb": ("The AIMS scope covers the customer-facing chatbot.",
   "The AIMS scope covers the internal staff chatbot. Customer-facing chatbots are omitted from the scope."),
 "version_digit": ("The scope covers the Phoenix-1 credit scoring engine used for retail loan approvals across lending channels.",
   "The scope covers the Phoenix-2 credit scoring engine used for retail loan approvals across lending channels."),
 "number_word": ("The scope covers two regional data centres supporting the customer analytics platform.",
   "The scope covers three regional data centres supporting the customer analytics platform."),
 "partial_conjunct": ("The scope covers the chatbot, the voice assistant, the recommender and the fraud model.",
   "The scope covers the chatbot, the voice assistant and the recommender."),
 "role_swap": ("The regulator audits the supplier.", "The supplier audits the regulator."),
 "future_tense": ("The chatbot is in scope.", "The chatbot will be brought into scope in 2028 after the pilot."),
 "non_ascii_name": ("The scope covers the Łódź plant.", "The scope covers the Łomża plant."),
 "lacks": ("The system has a documented incident response procedure.",
   "The system lacks a documented incident response procedure."),
 "hedge": ("The scope includes the recommender engine.",
   "The scope may include the recommender engine if the steering board approves it."),
 "pilot_qualifier": ("The scope covers the fraud detection model in production at all branches.",
   "The scope covers the fraud detection model. It runs in a pilot at one branch only."),
 "anchor_other_sentence": ("The scope covers the Atlas pricing model for corporate customers.",
   "Atlas is a retired project. The scope covers the pricing model for corporate customers."),
}
def case(c, e): return {"case_id": "X", "claim_text": c, "evidence_items": [{"evidence_id": "E1", "text": e}], "cited_evidence_ids": ["E1"]}
B0 = {"case_id": "X", "operational_disposition": "ACCEPT", "technical_failure": None}

class Adversarial(unittest.TestCase):
    def test_never_supported(self):
        for name, (c, e) in CASES.items():
            with self.subTest(name):
                self.assertNotEqual(b.check_claim_evidence(case(c, e))["outcome"], "SUPPORTED")
                self.assertFalse(b.apply_b1(B0, case(c, e))["release_positive_report_entry"])

class Hardening(unittest.TestCase):
    def test_restricted_key_variants(self):
        for k in ("expectedLabel", "expected-label", " expected_label", "Ground_Truth", "reviewer1_calibration_id"):
            with self.subTest(k):
                r = b.check_claim_evidence({**case("a b c", "a b c"), "meta": [{k: 1}]})
                self.assertEqual(r["failure_code"], "RESTRICTED_FIELD_PRESENT")
    def test_apply_b1_never_raises(self):
        ok = case("a b c", "a b c")
        for b0 in (None, 5, {"case_id": "X", "operational_disposition": ["ACCEPT"], "technical_failure": None}, {}):
            with self.subTest(str(b0)):
                r = b.apply_b1(b0, ok)
                self.assertFalse(r["release_positive_report_entry"]); self.assertIsNone(r["final_disposition"])
    def test_straightforward_support_still_supported(self):
        r = b.check_claim_evidence(case("The scope covers the chatbot operated in Singapore.",
                                        "The scope covers the chatbot operated in Singapore."))
        self.assertEqual(r["outcome"], "SUPPORTED")
if __name__ == "__main__": unittest.main()


class PolicyHashCoversCues(unittest.TestCase):
    def test_every_cue_list_changes_the_policy_hash(self):
        import dataclasses
        base = b.B1Policy()
        for field in ("negation_cues", "negation_phrases", "hedge_cues", "number_words"):
            with self.subTest(field):
                changed = dataclasses.replace(base, **{field: getattr(base, field) + ("zzzcue",)})
                self.assertNotEqual(base.sha256(), changed.sha256())
    def test_policy_cues_drive_behaviour(self):
        import dataclasses
        c = case("The scope includes the recommender engine.", "The scope may include the recommender engine.")
        self.assertNotEqual(b.check_claim_evidence(c)["outcome"], "SUPPORTED")
        relaxed = dataclasses.replace(b.B1Policy(), hedge_cues=())
        self.assertEqual(b.check_claim_evidence(c, policy=relaxed)["outcome"], "SUPPORTED")
    def test_default_policy_hash_is_stable(self):
        self.assertEqual(b.B1Policy().sha256(), b.B1Policy().sha256())
