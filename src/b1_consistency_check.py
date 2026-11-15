"""MVP2 B1: one claim-evidence consistency check, wrapped around unchanged B0 output.

Scope: ISO/IEC 42001 Clause 4.3, C4-Q03 only. Engineering prototype.

What this module is
-------------------
* A SEPARATE layer. It never imports, patches or re-implements the pinned B0
  toolkit. It consumes B0's already-captured operational disposition.
* DOWNGRADE-ONLY. B1 can turn a B0 ACCEPT into WITHHOLD. It can never turn a
  B0 WITHHOLD (or a technical failure) into ACCEPT. Any change in false
  acceptance / false rejection is therefore attributable to the single check.
* FAIL-SAFE. A positive report entry is released only when B0 said ACCEPT and
  the check returned SUPPORTED with no technical failure. Every other path
  withholds the entry; errors are returned as typed values, never raised.
* LABEL-BLIND. Inputs containing reference-label fields are rejected.
* NOT SCIENTIFIC EVIDENCE. Passing tests here is engineering verification. This
  module reads no reference labels, runs no benchmark case and scores nothing.

The default judge is a deterministic lexical/polarity heuristic ("lexical-v1").
It is intentionally crude and is documented as such in the design specification.
A different judge (for example an LLM) may be plugged in through the
``ConsistencyJudge`` protocol; its identity is recorded and its output is
validated, but none is provided or enabled here.
"""
from __future__ import annotations

import copy
import hashlib
import json
import re
from dataclasses import asdict, dataclass, field
from typing import Any, Mapping, Protocol, Sequence

try:  # reuse the repository's existing restricted-field guard when available
    from condition_materializer import RESTRICTED_KEYS
except ImportError:  # pragma: no cover - standalone fallback
    RESTRICTED_KEYS = frozenset({
        "expected_label", "reference_label", "reference_labels", "class_assignment",
        "case_category", "category_mapping", "expected_outcome", "correct_disposition",
        "adjudication", "grading_key", "scoring_key",
    })

B1_VERSION = "b1-0.1.0"
OUTCOMES = ("SUPPORTED", "INSUFFICIENT", "CONTRADICTED", "IRRELEVANT", "AMBIGUOUS")
FAILURE_CODES = (
    "INPUT_MALFORMED", "RESTRICTED_FIELD_PRESENT", "DUPLICATE_EVIDENCE_ID_CONFLICT",
    "JUDGE_OUTPUT_INVALID", "UNEXPECTED_ERROR",
)
_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,99}$")
_TOKEN = re.compile(r"[a-z0-9][a-z0-9'/-]*")
_SENTENCE_SPLIT = re.compile(r"(?<=[.!?;])\s+|\n+")
_STOP = frozenset((
    "a an the and or of to in on for with by from at as is are was were be been being this that "
    "these those it its into over under than then there their they them we our us you your has "
    "have had having will shall may might can could should would also any all each every both "
    "such which who whom whose what when where while within across per via not no nor but if "
    "other others more most less least only own same so too very just out within"
).split())
_NEGATION_CUES = ("not", "no", "never", "without", "except", "exclude", "excluded", "excludes",
                  "excluding", "exclusion", "outside", "n't", "neither")
_NEGATION_PHRASES = ("out of scope", "out-of-scope", "does not", "do not", "is not", "are not")


class ConsistencyJudge(Protocol):
    judge_id: str

    def judge(self, claim_text: str, evidence: Sequence[Mapping[str, str]],
              policy: "B1Policy", skip_terms: frozenset[str] = frozenset()) -> Mapping[str, Any]:
        """Return {"outcome": one of OUTCOMES, "reason_codes": [...], "matches": [...]}."""


@dataclass(frozen=True)
class B1Policy:
    """Explicit, hashable decision policy. Change a threshold => new policy hash."""
    policy_id: str = "b1-lexical-v1"
    support_coverage_min: float = 0.85       # share of claim terms found in resolvable evidence
    support_sentence_min: float = 0.60       # best single-sentence share of claim terms
    irrelevant_coverage_max: float = 0.25    # below this the evidence does not address the claim
    partial_coverage_min: float = 0.50       # between this and support_* => INSUFFICIENT
    contradiction_sentence_min: float = 0.50  # sentence overlap needed to count a polarity conflict
    boilerplate_terms: tuple[str, ...] = (
        "aims", "scope", "scoped", "organization", "organisation", "management", "iso", "iec",
        "42001", "clause", "document", "documented", "statement", "claim",
    )

    def sha256(self) -> str:
        return _sha(asdict(self))


def _sha(value: Any) -> str:
    data = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
                      allow_nan=False).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def _norm(token: str) -> str:
    """Light, deterministic stemming applied identically to claim and evidence."""
    t = token.strip("'-/")
    if t.endswith("'s"):
        t = t[:-2]
    for suffix in ("ing", "ed", "es", "s"):
        if t.endswith(suffix) and len(t) - len(suffix) >= 3 and not (suffix == "s" and t.endswith("ss")):
            t = t[: -len(suffix)]
            break
    if t.endswith("e") and len(t) > 3:
        t = t[:-1]
    return t


def _pieces(raw: str) -> list[str]:
    """Split hyphen/slash compounds so 'shipment-delay' matches 'shipment delay'."""
    return [p for p in re.split(r"[-/]", raw.strip("'-/")) if p]


def _skip_set(policy: B1Policy, skip_extra: frozenset[str]) -> set[str]:
    return {_norm(t) for t in policy.boilerplate_terms} | set(skip_extra)


def _terms(text: str, policy: B1Policy, skip_extra: frozenset[str] = frozenset()) -> set[str]:
    skip = _skip_set(policy, skip_extra)
    out = set()
    for raw in _TOKEN.findall(text.lower()):
        if raw.strip("'-/") in _NEGATION_CUES:
            continue
        for piece in _pieces(raw):
            tok = _norm(piece)
            if piece in _STOP or tok in _STOP or tok in skip or piece in _NEGATION_CUES:
                continue
            if len(tok) >= 3 or tok.isdigit():
                out.add(tok)
    return out


def _anchors(claim: str, policy: B1Policy, skip_extra: frozenset[str]) -> set[str]:
    """Specific terms a supporting passage must contain: numbers and names that are
    capitalised mid-sentence in the claim (e.g. a site, system or product name)."""
    out = set()
    skip = _skip_set(policy, skip_extra)
    for sentence in _sentences(claim):
        words = re.findall(r"[A-Za-z0-9][A-Za-z0-9'/-]*", sentence)
        for pos, word in enumerate(words):
            marked = any(c.isdigit() for c in word) or (pos > 0 and word[0].isupper() and not word.isupper())
            if not marked:
                continue
            for piece in _pieces(word.lower()):
                tok = _norm(piece)
                if tok in skip or tok in _STOP or piece in _STOP or len(tok) < 2:
                    continue
                out.add(tok)
    return out


def _org_terms(case: Mapping[str, Any], policy: B1Policy) -> frozenset[str]:
    org = case.get("organization")
    if not isinstance(org, str):
        return frozenset()
    return frozenset(_norm(p) for t in _TOKEN.findall(org.lower()) for p in _pieces(t))


def _negative(text: str) -> bool:
    low = text.lower()
    if any(p in low for p in _NEGATION_PHRASES):
        return True
    return any(tok.strip("'-/") in _NEGATION_CUES or tok.endswith("n't")
               for tok in _TOKEN.findall(low))


def _sentences(text: str) -> list[str]:
    return [s.strip() for s in _SENTENCE_SPLIT.split(text) if s and s.strip()]


class DeterministicLexicalJudge:
    """Term-coverage plus polarity heuristic. Reproducible; semantically shallow."""
    judge_id = "lexical-v1"

    def judge(self, claim_text: str, evidence: Sequence[Mapping[str, str]],
              policy: B1Policy, skip_terms: frozenset[str] = frozenset()) -> Mapping[str, Any]:
        claim_terms = _terms(claim_text, policy, skip_terms)
        anchors = _anchors(claim_text, policy, skip_terms)
        claim_neg = _negative(claim_text)
        if not claim_terms:
            return {"outcome": "AMBIGUOUS", "reason_codes": ["NO_MATERIAL_CLAIM_TERMS"], "matches": []}
        covered: set[str] = set()
        best = 0.0
        supporting = conflicting = False
        matches = []
        for item in evidence:
            for idx, sentence in enumerate(_sentences(item["text"])):
                s_terms = _terms(sentence, policy, skip_terms)
                overlap = len(claim_terms & s_terms) / len(claim_terms)
                covered |= claim_terms & s_terms
                if overlap == 0:
                    continue
                s_neg = _negative(sentence)
                same = s_neg == claim_neg
                matches.append({"evidence_id": item["evidence_id"], "sentence_index": idx,
                                "overlap": round(overlap, 4), "polarity_matches_claim": same})
                if overlap >= policy.contradiction_sentence_min and not same:
                    conflicting = True
                if overlap >= policy.support_sentence_min and same:
                    supporting = True
                if same:
                    best = max(best, overlap)
        coverage = len(covered) / len(claim_terms)
        missing_anchor = anchors - covered
        base = {"coverage": round(coverage, 4), "best_same_polarity_sentence": round(best, 4),
                "matches": matches}
        if conflicting and supporting:
            return {**base, "outcome": "AMBIGUOUS", "reason_codes": ["CONFLICTING_PASSAGES"]}
        if conflicting:
            return {**base, "outcome": "CONTRADICTED", "reason_codes": ["POLARITY_CONFLICT"]}
        if coverage < policy.irrelevant_coverage_max:
            return {**base, "outcome": "IRRELEVANT", "reason_codes": ["LOW_TERM_OVERLAP"]}
        if missing_anchor:
            return {**base, "outcome": "INSUFFICIENT",
                    "reason_codes": ["MISSING_ANCHOR_TERM"]}
        if coverage >= policy.support_coverage_min:
            if best >= policy.support_sentence_min:
                return {**base, "outcome": "SUPPORTED", "reason_codes": ["COVERAGE_AND_POLARITY_OK"]}
            return {**base, "outcome": "AMBIGUOUS", "reason_codes": ["SCATTERED_SUPPORT"]}
        if coverage >= policy.partial_coverage_min:
            return {**base, "outcome": "INSUFFICIENT", "reason_codes": ["PARTIAL_COVERAGE"]}
        return {**base, "outcome": "INSUFFICIENT", "reason_codes": ["WEAK_OVERLAP"]}


# --------------------------------------------------------------------------- input handling

def _find_restricted(value: Any) -> str | None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if isinstance(key, str) and key.casefold() in RESTRICTED_KEYS:
                return key
            hit = _find_restricted(child)
            if hit:
                return hit
    elif isinstance(value, (list, tuple)):
        for child in value:
            hit = _find_restricted(child)
            if hit:
                return hit
    return None


def _failure(case_id: Any, code: str, detail: str, policy: B1Policy, judge_id: str) -> dict[str, Any]:
    assert code in FAILURE_CODES
    return {"case_id": case_id if isinstance(case_id, str) else None, "status": "TECHNICAL_FAILURE",
            "failure_code": code, "failure_detail": detail, "outcome": None, "reason_codes": [],
            "b1_version": B1_VERSION, "policy_id": policy.policy_id,
            "policy_sha256": policy.sha256(), "judge_id": judge_id}


def check_claim_evidence(case: Mapping[str, Any], *, policy: B1Policy | None = None,
                         judge: ConsistencyJudge | None = None) -> dict[str, Any]:
    """Run the single consistency check. Never raises; never mutates ``case``.

    ``case`` keys: case_id, claim_text, evidence_items=[{evidence_id, text}],
    cited_evidence_ids=[...]. Returns a traceable result record.
    """
    policy = policy or B1Policy()
    judge = judge or DeterministicLexicalJudge()
    judge_id = getattr(judge, "judge_id", "unknown")
    case_id = case.get("case_id") if isinstance(case, Mapping) else None
    try:
        if not isinstance(case, Mapping):
            return _failure(None, "INPUT_MALFORMED", "case is not a mapping", policy, judge_id)
        snapshot = copy.deepcopy(dict(case))
        hit = _find_restricted(snapshot)
        if hit:
            return _failure(case_id, "RESTRICTED_FIELD_PRESENT", f"restricted field '{hit}'",
                            policy, judge_id)
        claim = snapshot.get("claim_text")
        items = snapshot.get("evidence_items")
        cited = snapshot.get("cited_evidence_ids")
        if (not isinstance(case_id, str) or not case_id.strip() or not isinstance(claim, str)
                or not claim.strip() or not isinstance(items, list)
                or not isinstance(cited, list)):
            return _failure(case_id, "INPUT_MALFORMED",
                            "case_id/claim_text/evidence_items/cited_evidence_ids invalid",
                            policy, judge_id)
        by_id: dict[str, str] = {}
        flags: list[str] = []
        for item in items:
            if (not isinstance(item, Mapping) or not isinstance(item.get("evidence_id"), str)
                    or not _ID.match(item["evidence_id"]) or not isinstance(item.get("text"), str)):
                return _failure(case_id, "INPUT_MALFORMED", "malformed evidence item",
                                policy, judge_id)
            eid, text = item["evidence_id"], item["text"]
            if eid in by_id:
                if by_id[eid] != text:
                    return _failure(case_id, "DUPLICATE_EVIDENCE_ID_CONFLICT",
                                    f"evidence_id '{eid}' repeated with different text",
                                    policy, judge_id)
                flags.append("DUPLICATE_EVIDENCE_ITEM_DEDUPED")
            else:
                by_id[eid] = text
        cited_unique: list[str] = []
        for eid in cited:
            if not isinstance(eid, str) or not _ID.match(eid):
                return _failure(case_id, "INPUT_MALFORMED", "malformed cited evidence id",
                                policy, judge_id)
            if eid in cited_unique:
                flags.append("DUPLICATE_CITED_ID_DEDUPED")
            else:
                cited_unique.append(eid)
        resolved = [e for e in cited_unique if e in by_id]
        unresolved = [e for e in cited_unique if e not in by_id]
        evidence = [{"evidence_id": e, "text": by_id[e]} for e in resolved]
        record: dict[str, Any] = {
            "case_id": case_id, "status": "OK", "b1_version": B1_VERSION,
            "policy_id": policy.policy_id, "policy_sha256": policy.sha256(), "judge_id": judge_id,
            "claim_sha256": hashlib.sha256(claim.encode("utf-8")).hexdigest(),
            "cited_evidence_ids": cited_unique, "resolved_evidence_ids": resolved,
            "unresolved_evidence_ids": unresolved,
            "evidence_sha256": {e["evidence_id"]: hashlib.sha256(e["text"].encode("utf-8")).hexdigest()
                                for e in evidence},
            "input_flags": sorted(set(flags)),
        }
        if not evidence:
            reason = "NO_CITED_EVIDENCE" if not cited_unique else "NO_RESOLVABLE_EVIDENCE"
            return {**record, "outcome": "INSUFFICIENT", "reason_codes": [reason], "matches": []}
        verdict = judge.judge(claim, evidence, policy, _org_terms(snapshot, policy))
        outcome = verdict.get("outcome") if isinstance(verdict, Mapping) else None
        if outcome not in OUTCOMES:
            return _failure(case_id, "JUDGE_OUTPUT_INVALID", f"judge returned {outcome!r}",
                            policy, judge_id)
        reasons = list(verdict.get("reason_codes", []))
        if unresolved:
            reasons.append("UNRESOLVED_CITED_ID")
            if outcome == "SUPPORTED":  # a citation that does not resolve blocks automatic support
                outcome = "AMBIGUOUS"
        return {**record, "outcome": outcome, "reason_codes": reasons,
                "matches": list(verdict.get("matches", [])),
                "coverage": verdict.get("coverage"),
                "best_same_polarity_sentence": verdict.get("best_same_polarity_sentence")}
    except Exception as exc:  # noqa: BLE001 - fail safe: typed value, never an exception
        return _failure(case_id, "UNEXPECTED_ERROR", f"{type(exc).__name__}", policy, judge_id)


# --------------------------------------------------------------------------- B0 wrapper

def apply_b1(b0_outcome: Mapping[str, Any], case: Mapping[str, Any], *,
             policy: B1Policy | None = None, judge: ConsistencyJudge | None = None) -> dict[str, Any]:
    """Combine a captured B0 operational outcome with the consistency check.

    ``b0_outcome`` needs ``case_id``, ``operational_disposition`` (ACCEPT/WITHHOLD/None)
    and ``technical_failure`` (None or text). The B0 record is copied, never edited.
    Downgrade-only: final ACCEPT requires B0 ACCEPT *and* check SUPPORTED.
    """
    b0 = copy.deepcopy(dict(b0_outcome))
    check = check_claim_evidence(case, policy=policy, judge=judge)
    b0_disp = b0.get("operational_disposition")
    b0_fail = b0.get("technical_failure")
    if b0.get("case_id") != check.get("case_id") and check["status"] == "OK":
        check = _failure(b0.get("case_id"), "INPUT_MALFORMED",
                         "B0 and B1 case_id differ", policy or B1Policy(), check["judge_id"])
    result = {"case_id": b0.get("case_id"), "b0_operational_disposition": b0_disp,
              "b0_technical_failure": b0_fail, "b1_check": check,
              "human_review_required": False, "release_positive_report_entry": False}
    if b0_fail is not None or b0_disp not in {"ACCEPT", "WITHHOLD"}:
        return {**result, "b1_applied": False, "final_disposition": None,
                "final_reason": "B0_NO_VALID_DISPOSITION"}
    if b0_disp == "WITHHOLD":  # downgrade-only: never upgrade; check kept for information
        return {**result, "b1_applied": True, "final_disposition": "WITHHOLD",
                "final_reason": "B0_WITHHOLD_UNCHANGED"}
    if check["status"] != "OK":  # B0 ACCEPT but check failed: no disposition, entry blocked
        return {**result, "b1_applied": True, "final_disposition": None,
                "final_reason": "B1_TECHNICAL_FAILURE_ENTRY_BLOCKED"}
    if check["outcome"] == "SUPPORTED":
        return {**result, "b1_applied": True, "final_disposition": "ACCEPT",
                "final_reason": "B0_ACCEPT_CONFIRMED_BY_CHECK", "release_positive_report_entry": True}
    if check["outcome"] == "AMBIGUOUS":
        return {**result, "b1_applied": True, "final_disposition": "WITHHOLD",
                "final_reason": "B1_AMBIGUOUS_HUMAN_REVIEW", "human_review_required": True}
    return {**result, "b1_applied": True, "final_disposition": "WITHHOLD",
            "final_reason": f"B1_DOWNGRADE_{check['outcome']}"}


def paired_difference_rows(b0_ledger: Sequence[Mapping[str, Any]],
                           b1_results: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Label-free per-case B0 -> B1 change table. The reference join happens later,
    only inside a separately authorized, controlled scoring step."""
    b0 = {r["case_id"]: r for r in b0_ledger}
    b1 = {r["case_id"]: r for r in b1_results}
    if len(b0) != len(b0_ledger) or len(b1) != len(b1_results) or set(b0) != set(b1):
        raise ValueError("B0 and B1 ledgers must contain the same unique case ids")
    rows = []
    for cid in sorted(b0):
        before, after = b0[cid].get("operational_disposition"), b1[cid]["final_disposition"]
        if before == "WITHHOLD" and after == "ACCEPT":
            raise ValueError(f"downgrade-only invariant violated for {cid}")
        rows.append({"case_id": cid, "b0_disposition": before, "b1_disposition": after,
                     "change": ("DOWNGRADED" if before == "ACCEPT" and after == "WITHHOLD"
                                else "NO_DISPOSITION" if after is None or before is None
                                else "UNCHANGED"),
                     "b1_reason": b1[cid]["final_reason"],
                     "check_outcome": b1[cid]["b1_check"].get("outcome"),
                     "human_review_required": b1[cid]["human_review_required"]})
    return rows
