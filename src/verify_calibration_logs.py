#!/usr/bin/env python3
"""Read-only integrity and completeness verifier for recovered calibration logs."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


EXPECTED_FILES = (
    "OdySEA_PIC04_Reviewer1_Calibration_log(1).csv",
    "OdySEA_P1C04_Reviewer2_Practice_Calibration_Log_Regenerated(1).csv",
)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalized(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", name.strip().casefold()).strip("_")


def select_column(headers: list[str], concepts: tuple[str, ...], label: str) -> str:
    indexed = {normalized(h): h for h in headers}
    for concept in concepts:
        if concept in indexed:
            return indexed[concept]
    for key, original in indexed.items():
        if any(concept in key for concept in concepts):
            return original
    raise ValueError(f"cannot identify {label} column from {headers}")


def parse_checksums(path: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        match = re.match(r"^([0-9a-fA-F]{64})\s+\*?(.+?)\s*$", line)
        if not match:
            raise ValueError(f"unrecognized checksum line: {line!r}")
        filename = Path(match.group(2)).name
        if filename in result:
            raise ValueError(f"duplicate checksum declaration: {filename}")
        result[filename] = match.group(1).lower()
    return result


def audit_csv(path: Path) -> dict[str, object]:
    raw = path.read_bytes()
    if b"\x00" in raw:
        raise ValueError("CSV contains NUL bytes")
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        headers = reader.fieldnames or []
        rows = list(reader)
    if len(rows) != 20:
        raise ValueError(f"expected exactly 20 raw judgments, found {len(rows)}")
    id_col = select_column(headers, (
        "reviewer_id", "review_id", "calibration_id", "judgment_id", "judgement_id", "case_id",
    ), "reviewer/judgment ID")
    initial_col = select_column(headers, (
        "initial_judgment", "initial_judgement", "initial_label", "initial_decision", "initial",
    ), "initial judgment")
    final_col = select_column(headers, (
        "final_judgment", "final_judgement", "final_label", "final_decision", "final",
    ), "final judgment")
    ids = [row.get(id_col, "").strip() for row in rows]
    initials = [row.get(initial_col, "").strip() for row in rows]
    finals = [row.get(final_col, "").strip() for row in rows]
    if any(not value for value in ids) or len(set(ids)) != 20:
        raise ValueError("reviewer/judgment IDs must be 20 populated unique values")
    if any(not value for value in initials) or any(not value for value in finals):
        raise ValueError("all 20 initial and final judgments must be populated")
    return {
        "filename": path.name,
        "sha256": hashlib.sha256(raw).hexdigest(),
        "byte_size": len(raw),
        "raw_row_count": len(rows),
        "header_count": len(headers),
        "identified_columns": {"id": id_col, "initial": initial_col, "final": final_col},
        "unique_id_count": len(set(ids)),
        "populated_initial_count": sum(bool(x) for x in initials),
        "populated_final_count": sum(bool(x) for x in finals),
        "raw_bytes_preserved": True,
    }


def verify(log_dir: Path, checksum_file: Path) -> dict[str, object]:
    report: dict[str, object] = {
        "schema_version": "1.0.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "classification": "research-lead calibration; not independently blinded human ground truth",
        "source_directory": str(log_dir),
        "checksum_file": str(checksum_file),
        "reviewer2_provenance_limitation": (
            "Reviewer 2 is a regenerated export. A byte match authenticates the recovered export against "
            "the recovery-package checksum, but does not establish equivalence to an earlier native export "
            "or independent/blinded authorship."
        ),
        "files": [],
    }
    failures: list[str] = []
    if not log_dir.is_dir():
        failures.append(f"missing specified original-log directory: {log_dir}")
    if not checksum_file.is_file():
        failures.append(f"missing recovery checksum file: {checksum_file}")
    checksums: dict[str, str] = {}
    if not failures:
        try:
            checksums = parse_checksums(checksum_file)
        except Exception as exc:
            failures.append(f"checksum file invalid: {exc}")
    for filename in EXPECTED_FILES:
        path = log_dir / filename
        if not path.is_file():
            failures.append(f"missing exact completed file: {filename}")
            continue
        if filename not in checksums:
            failures.append(f"no recovery checksum for: {filename}")
            continue
        actual = digest(path)
        if actual != checksums[filename]:
            failures.append(f"SHA-256 mismatch for {filename}: {actual} != {checksums[filename]}")
            continue
        try:
            entry = audit_csv(path)
            entry["expected_sha256"] = checksums[filename]
            entry["checksum_match"] = True
            report["files"].append(entry)
        except Exception as exc:
            failures.append(f"raw-row audit failed for {filename}: {exc}")
    report["failures"] = failures
    report["status"] = "PASS" if not failures and len(report["files"]) == 2 else "BLOCKED"
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--log-dir", type=Path, required=True)
    parser.add_argument("--checksums", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    result = verify(args.log_dir.resolve(strict=False), args.checksums.resolve(strict=False))
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"{result['status']}: calibration log integrity verification")
    for failure in result["failures"]:
        print(f"- {failure}", file=sys.stderr)
    return 0 if result["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
