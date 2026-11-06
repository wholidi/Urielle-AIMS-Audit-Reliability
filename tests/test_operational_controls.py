from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parents[1]
SOURCE_ROOT = HERE / "src"
sys.path.insert(0, str(SOURCE_ROOT))

import paired_input_gate  # noqa: E402
import stage_evaluator  # noqa: E402
import verify_calibration_logs  # noqa: E402


DEFAULT_BENCHMARK = HERE.parent / "OdySEA_P1C_Benchmark_v0_2"
BENCHMARK = Path(os.environ.get("URIELLE_BENCHMARK_DIR", DEFAULT_BENCHMARK))
BENCHMARK_AVAILABLE = (BENCHMARK / "evaluator_manifest.json").is_file()
requires_benchmark = unittest.skipUnless(
    BENCHMARK_AVAILABLE,
    "unreleased benchmark unavailable; set URIELLE_BENCHMARK_DIR to an authorized local copy",
)


class StagingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(dir=HERE)
        self.root = Path(self.temp.name)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def build(self, name: str = "stage"):
        return stage_evaluator.build_stage(BENCHMARK, self.root / name, self.root / f"{name}-inventory.json")

    def sample_case_id(self) -> str:
        manifest = json.loads((BENCHMARK / "evaluator_manifest.json").read_text(encoding="utf-8"))
        return manifest["case_order"][0]

    @requires_benchmark
    def test_real_source_has_exact_counts_hashes_and_uniform_times(self):
        report = self.build()
        self.assertEqual(report["case_count"], 20)
        self.assertEqual(report["evidence_file_count"], 23)
        self.assertEqual(report["file_count"], 44)
        stage_evaluator.verify_staged(self.root / "stage", report["files"])

    @requires_benchmark
    def test_staging_is_deterministic_across_different_destinations(self):
        one = self.build("one")
        two = self.build("two")
        self.assertEqual(one["files"], two["files"])

    @requires_benchmark
    def test_path_traversal_and_absolute_paths_are_rejected(self):
        case_root = BENCHMARK / "evaluator_inputs" / self.sample_case_id()
        with self.assertRaises(stage_evaluator.StageError):
            stage_evaluator.safe_child(case_root, "../case.json")
        with self.assertRaises(stage_evaluator.StageError):
            stage_evaluator.safe_child(case_root, str((case_root / "case.json").resolve()))

    def test_symlink_attack_is_rejected(self):
        target = self.root / "target.txt"
        target.write_text("x", encoding="utf-8")
        link = self.root / "link.txt"
        try:
            os.symlink(target, link)
        except OSError:
            # Exercise the link/reparse rejection decision even on hosts that deny link creation.
            from unittest.mock import patch
            with patch.object(Path, "is_symlink", return_value=True):
                self.assertTrue(stage_evaluator._is_link_or_reparse(target))
        else:
            with self.assertRaises(stage_evaluator.StageError):
                stage_evaluator.safe_child(self.root, "link.txt")

    @requires_benchmark
    def test_deliberately_inserted_forbidden_file_fails_closed(self):
        report = self.build()
        forbidden = self.root / "stage" / "reference_labels_restricted.json"
        forbidden.write_text('{"expected_label":"X"}', encoding="utf-8")
        stage_evaluator.normalize_and_verify_times(self.root / "stage")
        with self.assertRaises(stage_evaluator.StageError):
            stage_evaluator.verify_staged(self.root / "stage", report["files"])

    @requires_benchmark
    def test_structured_label_field_is_rejected_without_banning_ordinary_words(self):
        sample_id = self.sample_case_id()
        sample = json.loads((BENCHMARK / "evaluator_inputs" / sample_id / "case.json").read_text(encoding="utf-8"))
        sample["claim_text"] += " The process may be supported by records."
        stage_evaluator.validate_case(sample, sample_id)
        sample["expected_label"] = "hidden"
        with self.assertRaises(stage_evaluator.StageError):
            stage_evaluator.validate_case(sample, sample_id)

    @requires_benchmark
    def test_duplicate_case_paths_are_rejected(self):
        manifest = json.loads((BENCHMARK / "evaluator_manifest.json").read_text(encoding="utf-8"))
        manifest["case_order"][1] = manifest["case_order"][0]
        with self.assertRaises(stage_evaluator.StageError):
            stage_evaluator.validate_manifest(manifest)


class PairedInputTests(unittest.TestCase):
    def record(self):
        return {
            "case_id": "SYNTHETIC_CASE", "condition_id": "CONDITION_A",
            "canonical_case_payload": {"b": 2, "a": [1, "x"]},
            "reviewer_condition_input": {"disposition": "ACCEPTED", "time": "2000-01-01T00:00:00Z"},
            "implementation_differences": ["adapter name"],
        }

    def test_equal_normalized_inputs_pass_despite_key_order(self):
        left = self.record()
        right = self.record()
        right["canonical_case_payload"] = {"a": [1, "x"], "b": 2}
        right["implementation_differences"] = ["different model implementation"]
        report = paired_input_gate.compare([left], [right])
        self.assertEqual(report["pair_count"], 1)

    def test_payload_difference_fails_closed(self):
        left = self.record()
        right = self.record()
        right["canonical_case_payload"] = {"a": [1, "changed"], "b": 2}
        with self.assertRaises(paired_input_gate.PairingError):
            paired_input_gate.compare([left], [right])

    def test_reviewer_difference_fails_closed(self):
        left = self.record()
        right = self.record()
        right["reviewer_condition_input"]["disposition"] = "REJECTED"
        with self.assertRaises(paired_input_gate.PairingError):
            paired_input_gate.compare([left], [right])

    def test_missing_pair_and_duplicate_pair_fail_closed(self):
        record = self.record()
        with self.assertRaises(paired_input_gate.PairingError):
            paired_input_gate.compare([record], [])
        with tempfile.TemporaryDirectory(dir=HERE) as folder:
            path = Path(folder) / "duplicates.json"
            path.write_text(json.dumps([record, record]), encoding="utf-8")
            with self.assertRaises(paired_input_gate.PairingError):
                paired_input_gate.load_records(path)


class CalibrationLogVerifierTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=HERE)
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def make_files(self):
        rows = ["reviewer_id,initial_judgment,final_judgment,raw_rationale"]
        rows.extend(f"J-{i:02d},INITIAL_{i},FINAL_{i},unaltered raw record {i}" for i in range(20))
        content = ("\n".join(rows) + "\n").encode()
        checksums = []
        for filename in verify_calibration_logs.EXPECTED_FILES:
            path = self.root / filename
            path.write_bytes(content)
            checksums.append(f"{verify_calibration_logs.digest(path)}  {filename}")
        checksum = self.root / "CALIBRATION_LOG_SHA256SUMS.txt"
        checksum.write_text("\n".join(checksums) + "\n", encoding="utf-8")
        return checksum

    def test_exact_hash_and_twenty_raw_rows_pass(self):
        checksum = self.make_files()
        report = verify_calibration_logs.verify(self.root, checksum)
        self.assertEqual(report["status"], "PASS")
        self.assertEqual([item["raw_row_count"] for item in report["files"]], [20, 20])

    def test_byte_change_is_blocked(self):
        checksum = self.make_files()
        path = self.root / verify_calibration_logs.EXPECTED_FILES[1]
        path.write_bytes(path.read_bytes() + b"changed")
        report = verify_calibration_logs.verify(self.root, checksum)
        self.assertEqual(report["status"], "BLOCKED")


if __name__ == "__main__":
    unittest.main()
