#!/usr/bin/env python3
"""Build and verify a fail-closed evaluator-only benchmark staging tree."""

from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import os
import re
import shutil
import stat
import sys
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any


FIXED_TIMESTAMP = "2000-01-01T00:00:00Z"
FIXED_EPOCH = 946684800
ALLOWED_MANIFEST_KEYS = {
    "dataset_id", "schema_version", "case_count", "case_order",
    "evaluator_root", "case_file", "reference_material_included", "status",
}
ALLOWED_CASE_KEYS = {
    "case_id", "question_id", "requirement_ref", "organization", "system",
    "claim_text", "response_text", "evidence_items", "fixed_timestamp",
}
ALLOWED_EVIDENCE_KEYS = {"evidence_id", "locator", "media_type", "sha256"}
FORBIDDEN_STRUCTURED_KEYS = {
    "expected_label", "reference_label", "reference_labels", "class_assignment",
    "case_category", "category_mapping", "expected_outcome", "correct_disposition",
    "adjudication", "grading_key", "scoring_key", "reviewer_id",
    "reviewer1_calibration_id", "reviewer2_practice_id",
}
FORBIDDEN_PATH_PARTS = {
    "reference_labels_restricted", "restricted", "calibration", "adjudication",
    "scoring", "grading", "protocol", "admin", "reviewer",
}
PRECISE_LEAK_PATTERNS = (
    re.compile(r"\bR[12]-[0-9A-F]{8}\b"),
    re.compile(r"(?i)[\"']?(?:expected_label|reference_label|class_assignment|case_category|expected_outcome|correct_disposition)[\"']?\s*[:=]"),
)


class StageError(RuntimeError):
    pass


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _is_link_or_reparse(path: Path) -> bool:
    info = path.lstat()
    attrs = getattr(info, "st_file_attributes", 0)
    reparse = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    return path.is_symlink() or bool(attrs & reparse)


def safe_child(root: Path, relative: str) -> Path:
    if Path(relative).is_absolute() or re.match(r"^[A-Za-z]:[/\\]", relative):
        raise StageError(f"unsafe absolute path: {relative!r}")
    candidate_rel = PurePosixPath(relative.replace("\\", "/"))
    if candidate_rel.is_absolute() or ".." in candidate_rel.parts or not candidate_rel.parts:
        raise StageError(f"unsafe relative path: {relative!r}")
    if any(part in {"", "."} for part in candidate_rel.parts):
        raise StageError(f"non-canonical relative path: {relative!r}")
    candidate = root.joinpath(*candidate_rel.parts)
    resolved_root = root.resolve(strict=True)
    resolved = candidate.resolve(strict=True)
    if not _is_relative_to(resolved, resolved_root):
        raise StageError(f"path escapes source root: {relative!r}")
    current = resolved_root
    for part in candidate_rel.parts:
        current = current / part
        if _is_link_or_reparse(current):
            raise StageError(f"link/reparse point rejected: {relative!r}")
    if not resolved.is_file():
        raise StageError(f"not a regular file: {relative!r}")
    return resolved


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise StageError(f"invalid JSON {path}: {exc}") from exc


def _reject_forbidden_keys(value: Any, where: str = "$") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if key.casefold() in FORBIDDEN_STRUCTURED_KEYS:
                raise StageError(f"forbidden structured field {key!r} at {where}")
            _reject_forbidden_keys(child, f"{where}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _reject_forbidden_keys(child, f"{where}[{index}]")


def validate_manifest(manifest: Any) -> list[str]:
    if not isinstance(manifest, dict) or set(manifest) != ALLOWED_MANIFEST_KEYS:
        raise StageError("evaluator_manifest.json has unexpected structure")
    if manifest.get("case_count") != 20 or manifest.get("evaluator_root") != "evaluator_inputs":
        raise StageError("manifest does not declare the canonical 20-case evaluator root")
    if manifest.get("case_file") != "case.json" or manifest.get("reference_material_included") is not False:
        raise StageError("manifest safety declarations are invalid")
    if manifest.get("status") != "RESEARCH_REVISION_NOT_FROZEN":
        raise StageError("unexpected benchmark status")
    case_order = manifest.get("case_order")
    if not isinstance(case_order, list) or len(case_order) != 20:
        raise StageError("case_order must contain exactly 20 cases")
    if len(set(case_order)) != len(case_order):
        raise StageError("duplicate case paths/IDs in manifest")
    for case_id in case_order:
        if not isinstance(case_id, str) or not case_id.isalnum() or case_id.upper() != case_id:
            raise StageError(f"unsafe case ID: {case_id!r}")
    _reject_forbidden_keys(manifest)
    return case_order


def validate_case(case: Any, expected_id: str) -> list[dict[str, str]]:
    if not isinstance(case, dict) or set(case) != ALLOWED_CASE_KEYS:
        raise StageError(f"case {expected_id} has unexpected fields")
    if case.get("case_id") != expected_id or case.get("question_id") != "C4-Q03" or case.get("requirement_ref") != "4.3":
        raise StageError(f"case identity mismatch for {expected_id}")
    _reject_forbidden_keys(case)
    items = case.get("evidence_items")
    if not isinstance(items, list) or not items:
        raise StageError(f"case {expected_id} has no evidence items")
    locators: set[str] = set()
    evidence_ids: set[str] = set()
    result: list[dict[str, str]] = []
    for item in items:
        if not isinstance(item, dict) or set(item) != ALLOWED_EVIDENCE_KEYS:
            raise StageError(f"case {expected_id} evidence item has unexpected fields")
        locator = item.get("locator")
        evidence_id = item.get("evidence_id")
        digest = item.get("sha256")
        if not all(isinstance(v, str) and v for v in (locator, evidence_id, digest)):
            raise StageError(f"case {expected_id} contains an incomplete evidence declaration")
        if locator in locators or evidence_id in evidence_ids:
            raise StageError(f"case {expected_id} contains duplicate evidence declarations")
        if len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
            raise StageError(f"case {expected_id} contains an invalid SHA-256")
        locators.add(locator)
        evidence_ids.add(evidence_id)
        result.append(item)
    return result


def _set_windows_times(path: Path, epoch: int) -> None:
    # Set creation, access and modification times, including directories.
    kernel32 = ctypes.windll.kernel32
    kernel32.CreateFileW.argtypes = [
        ctypes.c_wchar_p, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_void_p,
        ctypes.c_uint32, ctypes.c_uint32, ctypes.c_void_p,
    ]
    kernel32.CreateFileW.restype = ctypes.c_void_p
    kernel32.SetFileTime.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p]
    kernel32.SetFileTime.restype = ctypes.c_int
    kernel32.CloseHandle.argtypes = [ctypes.c_void_p]
    kernel32.CloseHandle.restype = ctypes.c_int
    handle = kernel32.CreateFileW(
        str(path), 0x0100, 0x7, None, 3,
        0x02000000 if path.is_dir() else 0x00000080, None,
    )
    if handle == ctypes.c_void_p(-1).value:
        raise StageError(f"cannot open for timestamp normalization: {path}")
    ticks = int((epoch + 11644473600) * 10_000_000)
    ft = ctypes.c_ulonglong(ticks)
    try:
        if not kernel32.SetFileTime(handle, ctypes.byref(ft), ctypes.byref(ft), ctypes.byref(ft)):
            raise StageError(f"cannot normalize timestamps: {path}")
    finally:
        kernel32.CloseHandle(handle)


def set_uniform_times(root: Path) -> None:
    paths = sorted(root.rglob("*"), key=lambda p: len(p.parts), reverse=True)
    for path in paths + [root]:
        if os.name == "nt":
            _set_windows_times(path, FIXED_EPOCH)
        else:
            os.utime(path, (FIXED_EPOCH, FIXED_EPOCH), follow_symlinks=False)


def verify_uniform_times(root: Path) -> None:
    for path in [root, *root.rglob("*")]:
        info = path.stat()
        if int(info.st_mtime) != FIXED_EPOCH:
            raise StageError(f"non-uniform modification time: {path} ({info.st_mtime} != {FIXED_EPOCH})")
        if os.name == "nt" and int(info.st_ctime) != FIXED_EPOCH:
            raise StageError(f"non-uniform creation time: {path}")


def normalize_and_verify_times(root: Path, attempts: int = 5) -> None:
    last_error: StageError | None = None
    for _ in range(attempts):
        set_uniform_times(root)
        try:
            verify_uniform_times(root)
            return
        except StageError as exc:
            last_error = exc
    raise last_error or StageError("timestamp normalization failed")


def make_files_readonly(root: Path) -> None:
    for path in (p for p in root.rglob("*") if p.is_file()):
        path.chmod(stat.S_IREAD)


def inventory(root: Path) -> list[dict[str, Any]]:
    records = []
    for path in sorted((p for p in root.rglob("*") if p.is_file()), key=lambda p: p.relative_to(root).as_posix()):
        records.append({
            "path": path.relative_to(root).as_posix(),
            "size": path.stat().st_size,
            "sha256": sha256_file(path),
        })
    return records


def verify_no_precise_leakage(root: Path) -> None:
    """Detect precise administrative markers, not ordinary semantic English."""
    manifest = load_json(root / "evaluator_manifest.json")
    case_ids = validate_manifest(manifest)
    for case_id in case_ids:
        case_path = root / "evaluator_inputs" / case_id / "case.json"
        validate_case(load_json(case_path), case_id)
    for path in (p for p in root.rglob("*") if p.is_file()):
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeError as exc:
            raise StageError(f"non-UTF-8 evaluator content: {path}") from exc
        for pattern in PRECISE_LEAK_PATTERNS:
            if pattern.search(text):
                raise StageError(f"precise restricted marker found in evaluator content: {path}")


def verify_staged(stage: Path, expected: list[dict[str, Any]], *, check_times: bool = True) -> None:
    # Verify metadata before opening file contents; Windows filesystem filters can
    # react to first reads of newly created files.
    if check_times:
        verify_uniform_times(stage)
    actual = inventory(stage)
    if actual != expected:
        raise StageError("staged inventory differs from the explicit allowlist")
    case_files = [x for x in actual if x["path"].endswith("/case.json")]
    evidence_files = [x for x in actual if x["path"] != "evaluator_manifest.json" and not x["path"].endswith("/case.json")]
    if len(case_files) != 20 or len(evidence_files) != 23 or len(actual) != 44:
        raise StageError("staged view must contain 20 cases, 23 evidence files, and one manifest")
    for record in actual:
        parts = {part.casefold() for part in PurePosixPath(record["path"]).parts}
        if parts & FORBIDDEN_PATH_PARTS:
            raise StageError(f"restricted path staged: {record['path']}")
    verify_no_precise_leakage(stage)


def build_stage(source: Path, destination: Path, inventory_path: Path) -> dict[str, Any]:
    source = source.resolve(strict=True)
    destination = destination.resolve(strict=False)
    inventory_path = inventory_path.resolve(strict=False)
    if _is_relative_to(destination, source) or destination == source:
        raise StageError("destination must not be inside the protected benchmark")
    if destination.exists():
        raise StageError("destination must be fresh and must not already exist")
    if _is_relative_to(inventory_path, destination):
        raise StageError("inventory must be outside the evaluator bundle")

    manifest_path = safe_child(source, "evaluator_manifest.json")
    manifest = load_json(manifest_path)
    case_ids = validate_manifest(manifest)
    source_case_root = source / "evaluator_inputs"
    actual_case_dirs = sorted(p.name for p in source_case_root.iterdir() if p.is_dir())
    if actual_case_dirs != sorted(case_ids) or any(not p.is_dir() for p in source_case_root.iterdir()):
        raise StageError("undeclared or missing entries exist under evaluator_inputs")

    copy_plan: list[tuple[Path, str, str]] = [
        (manifest_path, "evaluator_manifest.json", sha256_file(manifest_path))
    ]
    total_evidence = 0
    seen_relative: set[str] = {"evaluator_manifest.json"}
    for case_id in case_ids:
        case_dir = source_case_root / case_id
        case_path = safe_child(case_dir, "case.json")
        case = load_json(case_path)
        items = validate_case(case, case_id)
        declared_names = {"case.json", *(str(item["locator"]) for item in items)}
        actual_names = {p.name for p in case_dir.iterdir()}
        if actual_names != declared_names or any(not p.is_file() for p in case_dir.iterdir()):
            raise StageError(f"case {case_id} has undeclared, missing, or non-file entries")
        case_rel = f"evaluator_inputs/{case_id}/case.json"
        if case_rel in seen_relative:
            raise StageError(f"duplicate case path: {case_rel}")
        seen_relative.add(case_rel)
        copy_plan.append((case_path, case_rel, sha256_file(case_path)))
        for item in items:
            evidence = safe_child(case_dir, item["locator"])
            observed = sha256_file(evidence)
            if observed != item["sha256"]:
                raise StageError(f"declared evidence hash mismatch: {case_id}/{item['locator']}")
            relative = f"evaluator_inputs/{case_id}/{item['locator']}"
            if relative in seen_relative:
                raise StageError(f"duplicate evidence path: {relative}")
            seen_relative.add(relative)
            copy_plan.append((evidence, relative, observed))
            total_evidence += 1
    if total_evidence != 23:
        raise StageError(f"expected 23 evidence files, found {total_evidence}")

    destination.mkdir(parents=True, exist_ok=False)
    try:
        for source_file, relative, _ in copy_plan:
            target = destination.joinpath(*PurePosixPath(relative).parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source_file, target, follow_symlinks=False)
        expected = [
            {"path": relative, "size": source_file.stat().st_size, "sha256": digest}
            for source_file, relative, digest in sorted(copy_plan, key=lambda x: x[1])
        ]
        # Perform all content reads before the final metadata operation. Some Windows
        # filesystem filters update metadata while scanning newly read files.
        verify_staged(destination, expected, check_times=False)
        make_files_readonly(destination)
        normalize_and_verify_times(destination)
        report = {
            "schema_version": "1.0.0",
            "status": "PASS",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "stage_root": str(destination),
            "fixed_timestamp": FIXED_TIMESTAMP,
            "case_count": 20,
            "evidence_file_count": 23,
            "file_count": len(expected),
            "files": expected,
        }
        inventory_path.parent.mkdir(parents=True, exist_ok=True)
        inventory_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="\n")
        return report
    except Exception:
        # A failed partial bundle is unsafe. Remove only the exact new destination.
        if destination.exists():
            shutil.rmtree(destination)
        raise


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--destination", type=Path, required=True)
    parser.add_argument("--inventory", type=Path, required=True)
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()
    try:
        if args.verify_only:
            report = load_json(args.inventory.resolve(strict=True))
            verify_staged(args.destination.resolve(strict=True), report["files"])
        else:
            build_stage(args.source, args.destination, args.inventory)
    except (StageError, OSError, KeyError, TypeError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    print("PASS: evaluator staging controls verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
