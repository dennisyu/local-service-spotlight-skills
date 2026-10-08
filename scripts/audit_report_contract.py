#!/usr/bin/env python3
"""Deterministic audit QA. No network, model requests or invented scoring weights.

Use an approved rubric JSON plus report JSON; --batch checks final text artifacts
against shared-fact revisions. This does not verify source truth or rendered layout.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path


class AuditContractError(ValueError):
    pass


def canonical_hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                     ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def number(value, label):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise AuditContractError(f"{label}: expected finite number")
    return Decimal(str(value))


def validate_report(rubric, report):
    if rubric.get("approved") is not True:
        raise AuditContractError("rubric is not approved; do not substitute weights")
    for field in ("exam_family", "rubric_id", "rubric_version"):
        if not rubric.get(field) or report.get(field) != rubric[field]:
            raise AuditContractError(f"{field}: missing or mismatched rubric")
    if report.get("rubric_sha256") != canonical_hash(rubric):
        raise AuditContractError("rubric_sha256: exact manifest mismatch")
    definitions = rubric.get("rows", [])
    rows = report.get("rows", [])
    ids = [r.get("id") for r in definitions]
    if not ids or len(set(ids)) != len(ids) or None in ids:
        raise AuditContractError("rubric rows: missing or duplicate IDs")
    row_ids = [r.get("id") for r in rows]
    if len(set(row_ids)) != len(row_ids) or set(row_ids) != set(ids):
        raise AuditContractError("report rows: must match every rubric row exactly once")
    mode = rubric.get("calculation")
    if mode not in ("sum", "weighted_mean"):
        raise AuditContractError("unsupported calculation; no implicit denominator policy")
    by_id = {r["id"]: r for r in rows}
    unknown, total = [], Decimal(0)
    for spec in definitions:
        maximum = number(spec.get("max"), "row maximum")
        if maximum <= 0:
            raise AuditContractError("row maximum must be positive")
        if mode == "weighted_mean" and number(spec.get("weight"), "weight") < 0:
            raise AuditContractError("negative weight")
        row = by_id[spec["id"]]
        state = row.get("state")
        if state == "UNKNOWN":
            if row.get("score") is not None or not row.get("reason"):
                raise AuditContractError(f"{row['id']}: UNKNOWN requires null and reason")
            unknown.append(row["id"])
            continue
        if state == "N/A":
            raise AuditContractError("N/A denominator rule unsupported; hold for explicit policy")
        if state != "CHECKED" or not row.get("evidence_ids"):
            raise AuditContractError(f"{row['id']}: numeric score requires checked evidence")
        value = number(row.get("score"), row["id"])
        if maximum <= 0 or value < 0 or value > maximum:
            raise AuditContractError(f"{row['id']}: score outside approved range")
        if mode == "sum":
            total += value
        else:
            weight = number(spec.get("weight"), "weight")
            if weight < 0:
                raise AuditContractError("negative weight")
            total += value / maximum * weight
    # Full declared weight total, not only researched rows. Missing rows never get renormalized.
    if mode == "weighted_mean":
        declared = sum((number(s.get("weight"), "weight") for s in definitions), Decimal(0))
        if declared != number(rubric.get("scale_max"), "scale_max"):
            raise AuditContractError("weights do not sum to declared scale")
    elif sum((number(s.get("max"), "maximum") for s in definitions), Decimal(0)) != number(rubric.get("scale_max"), "scale_max"):
        raise AuditContractError("row maxima do not sum to declared scale")
    # Verdict uses the raw calculation. Display precision is an explicit rubric rule.
    precision = rubric.get("display_decimals", 2)
    if isinstance(precision, bool) or not isinstance(precision, int) or not 0 <= precision <= 6:
        raise AuditContractError("invalid display precision")
    displayed = total.quantize(Decimal(1).scaleb(-precision), rounding=ROUND_HALF_UP)
    if unknown:
        if report.get("total") is not None or report.get("verdict") != "INCOMPLETE":
            raise AuditContractError("UNKNOWN required rows: no total/pass/fail verdict")
        if number(report.get("known_subtotal"), "known_subtotal") != displayed:
            raise AuditContractError("incorrect known subtotal")
    else:
        if number(report.get("total"), "headline total") != displayed:
            raise AuditContractError("headline does not equal calculated rows")
        expected = "PASS" if total >= number(rubric.get("pass_line"), "pass_line") else "FAIL"
        if report.get("verdict") != expected:
            raise AuditContractError("verdict does not match pinned pass line")
    entity = report.get("entity")
    if entity is not None:
        if not report.get("subject_id"):
            raise AuditContractError("entity receipts require stable report subject_id")
        graph = entity.get("graph_object_status")
        if graph not in ("RESOLVED", "AMBIGUOUS", "NO_SAFE_OBJECT_RETURNED", "UNKNOWN"):
            raise AuditContractError("invalid graph-object state")
        if graph == "RESOLVED" and (not entity.get("kgmid") or len(set(entity.get("identity_evidence_ids", []))) < 2):
            raise AuditContractError("resolved graph object requires ID and two identity receipts")
        panel = entity.get("normal_google_panel_status")
        if panel not in ("VISIBLE", "NOT_VISIBLE_IN_THIS_CHECK", "UNKNOWN"):
            raise AuditContractError("invalid ordinary-panel state")
        if panel != "UNKNOWN":
            receipt = entity.get("normal_query_receipt", {})
            for key in ("query", "captured_at", "locale", "location", "device", "personalization", "locator"):
                if not receipt.get(key):
                    raise AuditContractError(f"panel observation requires separate {key} receipt")
            if receipt.get("forced_kgmid") is not False:
                raise AuditContractError("forced KGMID is not an ordinary panel observation")
        claim = entity.get("owner_claim_status")
        if claim not in ("CLAIMED", "NOT_CLAIMED", "UNKNOWN"):
            raise AuditContractError("invalid owner-claim state")
        if claim != "UNKNOWN":
            receipt = entity.get("owner_claim_receipt", {})
            if (not isinstance(receipt, dict) or receipt.get("evidence_class") != "OWNER_SIDE" or
                    receipt.get("authorized_owner_access") is not True or
                    receipt.get("subject_id") != report["subject_id"] or
                    receipt.get("status") != claim or not receipt.get("captured_at") or not receipt.get("locator")):
                raise AuditContractError("claim status requires subject-matched authorized owner-side receipt")
    return {"state": "INCOMPLETE" if unknown else "CHECKED", "calculated_subtotal": float(total),
            "displayed_subtotal": float(displayed),
            "unknown_rows": unknown, "verification_scope": "structure/arithmetic only"}


def comparable(before, after):
    return all(before.get(k) == after.get(k) and before.get(k) is not None for k in
               ("exam_family", "rubric_id", "rubric_version", "rubric_sha256", "coverage_id"))


def extract_pdf(data_path):
    """Extract the current binary, never trust text supplied by a worker alone."""
    try:
        from pypdf import PdfReader
        reader = PdfReader(str(data_path), strict=True)
        if reader.is_encrypted:
            raise AuditContractError("encrypted final PDF; extraction HOLD")
        return "\n\f\n".join(page.extract_text() or "" for page in reader.pages).encode("utf-8")
    except Exception as exc:
        raise AuditContractError("final PDF extraction unavailable/failed; batch HOLD") from exc


def validate_batch(manifest, root):
    root = Path(root).resolve()
    expected = manifest.get("expected_artifacts", [])
    artifacts = manifest.get("artifacts", [])
    paths = [a.get("path") for a in artifacts]
    if not expected or len(set(expected)) != len(expected) or len(set(paths)) != len(paths) or set(paths) != set(expected):
        raise AuditContractError("batch must contain every expected final artifact exactly once")
    facts = manifest.get("shared_facts", {})
    if not facts:
        raise AuditContractError("batch requires authoritative shared-fact ledger")
    for artifact in artifacts:
        path = (root / artifact["path"]).resolve()
        if not path.is_relative_to(root):
            raise AuditContractError("artifact outside allowed root")
        data = path.read_bytes()
        if hashlib.sha256(data).hexdigest() != artifact.get("sha256"):
            raise AuditContractError(f"{artifact['path']}: final hash mismatch")
        kind = artifact.get("kind", "text")
        if path.suffix.lower() == ".pdf" and kind != "pdf":
            raise AuditContractError("final PDF requires binary/extraction binding")
        if kind == "pdf":
            text_path = (root / artifact.get("text_path", "")).resolve()
            if not text_path.is_relative_to(root) or not text_path.is_file():
                raise AuditContractError("missing final PDF text companion")
            extracted = extract_pdf(path)
            if (extracted != text_path.read_bytes() or
                    hashlib.sha256(extracted).hexdigest() != artifact.get("text_sha256")):
                raise AuditContractError(f"{artifact['path']}: stale PDF extraction")
            text = extracted.decode("utf-8")
        elif kind == "text":
            text = data.decode("utf-8")
        else:
            raise AuditContractError("unsupported final artifact kind")
        for fact_id, fact in facts.items():
            if any(old.casefold() in text.casefold() for old in fact.get("retired_text", [])):
                raise AuditContractError(f"{artifact['path']}: retired claim {fact_id} survived")
            if artifact["path"] in fact.get("dependents", []):
                if artifact.get("shared_fact_revisions", {}).get(fact_id) != fact.get("revision"):
                    raise AuditContractError(f"{artifact['path']}: stale shared fact {fact_id}")
                if fact.get("required_text") and fact["required_text"] not in text:
                    raise AuditContractError(f"{artifact['path']}: corrected fact {fact_id} missing")
    for fact_id, fact in facts.items():
        if not fact.get("revision") or not set(fact.get("dependents", [])).issubset(set(expected)):
            raise AuditContractError(f"{fact_id}: missing revision/dependent artifact")
    return {"state": "CHECKED", "artifact_count": len(artifacts),
            "verification_scope": "exact hashes/shared-fact propagation; visual review separate"}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--rubric", type=Path)
    p.add_argument("--report", type=Path)
    p.add_argument("--batch", type=Path)
    args = p.parse_args()
    try:
        if args.batch and not (args.rubric or args.report):
            receipt = validate_batch(json.loads(args.batch.read_text()), args.batch.parent)
        elif args.rubric and args.report and not args.batch:
            receipt = validate_report(json.loads(args.rubric.read_text()), json.loads(args.report.read_text()))
        else:
            p.error("use --rubric and --report, or --batch")
    except (AuditContractError, OSError, ValueError) as exc:
        print(json.dumps({"state": "HOLD", "reason": str(exc)}))
        return 1
    print(json.dumps(receipt))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
