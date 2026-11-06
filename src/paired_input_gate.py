#!/usr/bin/env python3
"""Fail-closed equality gate for paired baseline/intervention input records."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


REQUIRED = {"case_id", "condition_id", "canonical_case_payload", "reviewer_condition_input"}
ALLOWED = REQUIRED | {"implementation_differences"}


class PairingError(ValueError):
    pass


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def sha(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def load_records(path: Path) -> list[dict[str, Any]]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, list):
        raise PairingError(f"{path} must contain a JSON array")
    result = []
    keys: set[tuple[str, str]] = set()
    for index, record in enumerate(value):
        if not isinstance(record, dict) or not REQUIRED <= set(record) or not set(record) <= ALLOWED:
            raise PairingError(f"record {index} in {path} has invalid fields")
        case_id, condition_id = record["case_id"], record["condition_id"]
        if not isinstance(case_id, str) or not case_id or not isinstance(condition_id, str) or not condition_id:
            raise PairingError(f"record {index} in {path} has invalid pair identifiers")
        key = (case_id, condition_id)
        if key in keys:
            raise PairingError(f"duplicate pair key in {path}: {key}")
        keys.add(key)
        result.append(record)
    return result


def compare(baseline: list[dict[str, Any]], intervention: list[dict[str, Any]]) -> dict[str, Any]:
    left = {(r["case_id"], r["condition_id"]): r for r in baseline}
    right = {(r["case_id"], r["condition_id"]): r for r in intervention}
    if set(left) != set(right):
        missing_left = sorted(set(right) - set(left))
        missing_right = sorted(set(left) - set(right))
        raise PairingError(f"pair key sets differ; missing_baseline={missing_left}, missing_intervention={missing_right}")
    rows = []
    for key in sorted(left):
        lrecord, rrecord = left[key], right[key]
        lp = sha(lrecord["canonical_case_payload"])
        rp = sha(rrecord["canonical_case_payload"])
        lr = sha(lrecord["reviewer_condition_input"])
        rr = sha(rrecord["reviewer_condition_input"])
        if lp != rp or lr != rr:
            raise PairingError(
                f"input mismatch for case_id={key[0]} condition_id={key[1]}: "
                f"payload {lp}/{rp}, reviewer {lr}/{rr}"
            )
        rows.append({
            "case_id": key[0], "condition_id": key[1],
            "canonical_payload_sha256": lp, "reviewer_input_sha256": lr,
            "baseline_implementation_differences": lrecord.get("implementation_differences", []),
            "intervention_implementation_differences": rrecord.get("implementation_differences", []),
        })
    return {"status": "PASS", "pair_count": len(rows), "pairs": rows}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--intervention", type=Path, required=True)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    try:
        result = compare(load_records(args.baseline), load_records(args.intervention))
    except (OSError, UnicodeError, json.JSONDecodeError, PairingError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"PASS: {result['pair_count']} paired inputs are byte-identical after canonical normalization")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
