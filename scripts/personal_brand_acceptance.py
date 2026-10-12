#!/usr/bin/env python3
"""Check a private audit acceptance manifest. Never certify source truth or A+.

Exit 0: declarations and local evidence agree, REVIEW_REQUIRED.
Exit 1: HOLD (failed/missing gate). Exit 2: malformed input or unavailable parser.
No network requests, delivery, installation or execution are performed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
import zipfile

INSTALL = "https://localservicespotlight.com/install/"
GUIDES = ("SKILL.md", "references/20-page-pdf-blueprint.md",
          "references/evidence-ledger.md", "references/intake-and-authority-boundary.md",
          "references/brand-authority-rubric.md", "references/acceptance-tests.md")
KIT_ROLES = {"start_here", "subject_facts", "source_map", "instructions",
             "first_task", "output_example", "permission_gates", "receipt_template"}
STATES = {"AVAILABLE", "INSTALLED", "ENABLED", "TESTED", "SCHEDULED", "OBSERVED"}


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def source_key(url: str) -> str:
    """Collapse fragments/tracking only; meaningful query parameters survive."""
    p = urlsplit(url)
    query = sorted((k, v) for k, v in parse_qsl(p.query, keep_blank_values=True)
                   if not k.lower().startswith("utm_") and k.lower() not in {"fbclid", "gclid"})
    return urlunsplit((p.scheme.lower(), p.netloc.lower(), p.path or "/", urlencode(query), ""))


def normalized(text: str) -> str:
    return " ".join(text.split())


def input_binding(manifest: dict) -> str:
    """Reviewer signs this projection; changing any input invalidates that review."""
    payload = {k: v for k, v in manifest.items() if k not in {"editorial_review", "_instructions"}}
    return digest(json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode())


def validate(manifest: dict, base: Path, repo: Path) -> dict:
    errors: list[str] = []

    def require(ok, code, message):
        if not ok:
            errors.append(f"{code}: {message}")

    def present(value):
        return isinstance(value, str) and value.strip() not in {"", "UNKNOWN", "UNTESTED"}

    def artifact(ref, label):
        require(isinstance(ref, dict), "ARTIFACT", label)
        if not isinstance(ref, dict):
            return b""
        try:
            # Local task-controlled files only. This checker never follows a remote URL.
            data = (base / ref["path"]).read_bytes()
            require(digest(data) == ref["sha256"], "HASH", label)
            return data
        except (OSError, KeyError, TypeError):
            require(False, "ARTIFACT", f"missing {label}")
            return b""

    def receipt(ref, label):
        try:
            data = json.loads(artifact(ref, label))
            if not isinstance(data, dict):
                raise ValueError("receipt must be object")
            return data
        except (ValueError, TypeError):
            require(False, "RECEIPT", label)
            return {}

    def unique_rows(rows, label):
        ids = [r["id"] for r in rows]
        require(len(set(ids)) == len(ids), "DUPLICATE_ID", label)
        return {r["id"]: r for r in rows}

    require(manifest["schema_version"] == 1, "SCHEMA", "expected version 1")
    require(present(manifest["subject_id"]), "SUBJECT", "resolved subject identifier")
    require(present(manifest["author_context"]), "FRESH_REVIEW", "record author context before comparing reviewer")
    require(bool(re.fullmatch(r"[0-9a-f]{40}", manifest["source_revision"])),
            "SOURCE_REVISION", "pin the source commit")
    guides = manifest["guide_hashes"]
    for name in GUIDES:
        data = (repo / "skills/personal-brand-audit" / name).read_bytes()
        require(guides.get(name) == digest(data), "GUIDE_DRIFT", name)
    for key in ("ledger", "action_register", "visual_brief"):
        artifact(manifest[key], key)
    brief = receipt(manifest["brief"], "engagement brief")
    require(brief.get("subject_id") == manifest["subject_id"], "BRIEF", "resolved subject")
    pdf_data = artifact(manifest["pdf"], "final PDF")
    pdf_hash = digest(pdf_data)
    from pypdf import PdfReader
    import io
    reader = PdfReader(io.BytesIO(pdf_data))
    require(len(reader.pages) == 20, "PAGE_COUNT", "exactly 20 physical pages")
    texts = [normalized(p.extract_text() or "") for p in reader.pages]
    links = {str(a.get_object().get("/A", {}).get("/URI", ""))
             for page in reader.pages for a in page.get("/Annots", [])}

    sources = unique_rows(manifest["sources"], "sources")
    captures = {}
    for sid, s in sources.items():
        captures[sid] = artifact(s["capture"], f"source {sid}").decode("utf-8")
        for key in ("url", "final_url", "title", "publisher", "source_class", "captured_at", "origin_id"):
            require(present(s.get(key)), "SOURCE", f"{sid}.{key}")
        require(urlsplit(s["final_url"]).scheme in {"http", "https"}
                or s.get("data_classification") == "PRIVATE-AUTHORIZED", "SOURCE", f"{sid} authorized locator")

    evidence = unique_rows(manifest["evidence"], "evidence")
    for eid, e in evidence.items():
        status = e["finding_type"]
        require(status in {"OBSERVED", "INFERRED", "UNKNOWN"}, "EVIDENCE_STATE", eid)
        require(e["evidence_state"] in {"UNKNOWN", "OBSERVED", "VERIFIED", "CONTRADICTED", "EXPIRED"},
                "EVIDENCE_STATE", eid)
        if status == "UNKNOWN":
            require(e.get("value") is None and present(e.get("owner")) and present(e.get("next_evidence")),
                    "UNKNOWN", f"{eid} null value, owner and next evidence")
        else:
            sid = e["source_id"]
            require(sid in sources, "TRACE", f"{eid} source")
            require(present(e.get("extract")) and normalized(e["extract"]) in normalized(captures.get(sid, "")),
                    "TRACE", f"{eid} exact captured extract")
            if status == "INFERRED":
                require(present(e.get("reasoning")), "INFERENCE", eid)

    def evidence_refs(ids, label):
        require(bool(ids) and all(i in evidence for i in ids), "TRACE", label)

    used_sources = set()
    claims = unique_rows(manifest["claims"], "claims")
    for cid, claim in claims.items():
        page = claim["page"]
        require(isinstance(page, int) and 1 <= page <= len(texts), "CLAIM_PAGE", cid)
        require(present(claim["text"]) and isinstance(page, int) and 1 <= page <= len(texts)
                and normalized(claim["text"]) in texts[page - 1], "PDF_CLAIM", cid)
        evidence_refs(claim["evidence_ids"], cid)
        used_sources.update(evidence[eid].get("source_id") for eid in claim["evidence_ids"] if eid in evidence)
    used_sources.discard(None)
    supporting = [sources[s] for s in used_sources if s in sources]
    canonical_sources = {}
    for sid in sources:
        trail = set()
        current = sid
        while sources.get(current, {}).get("duplicate_of"):
            row = sources[current]
            require(present(row.get("dedupe_basis")), "SOURCE_DEDUPE", f"{current} mirror/republication basis")
            trail.add(current)
            current = row["duplicate_of"]
            if current not in sources or current in trail:
                require(False, "SOURCE_DEDUPE", f"{sid} dangling or cyclic alias")
                current = sid
                break
        canonical_sources[sid] = sources[current]
    canonical_supporting = [canonical_sources[s] for s in used_sources if s in sources]
    url_count = len({source_key(s["final_url"]) for s in canonical_supporting
                     if urlsplit(s["final_url"]).scheme in {"http", "https"}})
    private_count = len({s["final_url"] for s in canonical_supporting
                         if urlsplit(s["final_url"]).scheme not in {"http", "https"}})
    origin_count = len({s["origin_id"] for s in supporting})
    counts = manifest["source_counts"]
    require(counts["unit"] == "distinct_supporting_urls", "SOURCE_UNIT", "URLs are not independent proofs")
    require(counts["reported"] == url_count, "SOURCE_COUNT", f"actual supporting URLs = {url_count}")
    require(counts["underlying_records"] == origin_count, "SOURCE_COUNT", "underlying records")
    require(counts.get("private_record_locators", 0) == private_count, "SOURCE_COUNT", "private supporting locators")
    require(counts["citation_occurrences"] == sum(len(c["evidence_ids"]) for c in claims.values()),
            "SOURCE_COUNT", "citation occurrences in the enumerated claim map")
    target = counts["engagement_target"]
    require(target is None or (type(target) is int and target >= 0), "SOURCE_TARGET", "null or declared target")
    require(present(counts["target_basis"]), "SOURCE_TARGET", "brief locator or no-quota explanation")
    require(brief.get("source_target") == target, "SOURCE_TARGET", "target must match pinned engagement brief")
    require(target is None or url_count >= target, "SOURCE_COVERAGE", "below declared brief target; PARTIAL")

    visuals = unique_rows(manifest["visuals"], "visuals")
    for vid, v in visuals.items():
        artifact(v["asset"], f"visual {vid}")
        evidence_refs(v["evidence_ids"], vid)
        require(v["kind"] in {"photo", "screenshot", "chart", "diagram"}, "MEANINGFUL_VISUAL", vid)
        require(present(v["caption"]) and present(v["purpose"]), "VISUAL_PURPOSE", vid)
        require(v["reuse_status"] == "APPROVED", "VISUAL_RIGHTS", vid)
        artifact(v["reuse_receipt"], f"visual permission {vid}")
        if v["kind"] == "photo":
            require(v["identity_status"] == "RESOLVED" and present(v["identity_basis"]), "PHOTO_IDENTITY", vid)
            require(v["photo_role"] in {"subject", "documentary_context"}, "PHOTO_ROLE", vid)
            require(v["original_source"] in sources, "PHOTO_PROVENANCE", f"{vid} original source capture")

    pages = manifest["pages"]
    require(sorted(p["page"] for p in pages) == list(range(1, 21)), "PAGE_REVIEWS", "review all 20 once")
    page_one = next((p for p in pages if p["page"] == 1), {})
    require(any(visuals.get(i, {}).get("kind") == "photo" for i in page_one.get("visual_ids", [])),
            "COVER_PHOTO", "page 1 needs approved real subject/context photo")
    review = receipt(manifest["editorial_review"], "fresh-context review")
    require(review.get("input_binding_sha256") == input_binding(manifest), "REVIEW_INPUT_DRIFT",
            "bind all inputs, permissions, source captures, visual brief, counts and applicability")
    require(review.get("pdf_sha256") == pdf_hash, "REVIEW_DRIFT", "review final PDF")
    require(present(review.get("reviewer_context")) and review.get("reviewer_context") != manifest["author_context"],
            "FRESH_REVIEW", "different context required")
    for gate in ("source_truth", "claim_inventory_complete", "visual_brief", "normal_size_readability",
                 "strategy", "privacy", "cover_identity_provenance"):
        item = review.get("gates", {}).get(gate, {})
        require(item.get("status") == "PASS" and present(item.get("basis")), "EDITORIAL_GATE", gate)
    for p in pages:
        require(present(p["takeaway"]) and present(p["layout_family"]), "PAGE_STORY", str(p["page"]))
        require(bool(p["visual_ids"]) and all(i in visuals for i in p["visual_ids"]), "PAGE_VISUAL", str(p["page"]))
        require(type(p["body_min_pt"]) in {int, float} and p["body_min_pt"] >= 11
                and type(p["label_min_pt"]) in {int, float} and p["label_min_pt"] >= 9,
                "READABILITY", str(p["page"]))
        artifact(p["render"], f"render page {p['page']}")
        verdict = review.get("pages", {}).get(str(p["page"]), {})
        require(verdict.get("render_sha256") == p["render"]["sha256"] and verdict.get("status") == "PASS"
                and present(verdict.get("basis")), "PAGE_REVIEW", str(p["page"]))
    crosswalk = manifest["coverage_crosswalk"]
    require(set(crosswalk) == {str(i) for i in range(1, 21)}, "CROSSWALK", "all default page requirements")
    require(all(isinstance(v, list) and v and all(type(n) is int and 1 <= n <= 20 for n in v)
                for v in crosswalk.values()), "CROSSWALK", "physical page locators")
    require(crosswalk.get("1") == [1] and crosswalk.get("2") == [2] and crosswalk.get("20") == [20],
            "INVARIANT_PAGES", "pages 1, 2 and 20 stay fixed")

    actions = unique_rows(manifest["actions"], "actions")
    require(bool(actions), "ACTIONS", "subject-specific actions required")
    for aid, a in actions.items():
        evidence_refs(a["evidence_ids"], aid)
        for key in ("observation", "consequence", "next_step", "function", "skill", "input",
                    "destination", "due", "human_gate", "acceptance_test", "state", "handoff"):
            require(present(a.get(key)), "ACTION", f"{aid}.{key}")
        require((repo / "skills" / a["skill"] / "SKILL.md").is_file(), "SKILL", aid)

    def qr_check(q, expected, label):
        crop = artifact(q["rendered_crop"], f"{label} QR crop")
        decoded = receipt(q["decode_receipt"], f"{label} decode")
        require(decoded.get("pdf_sha256") == pdf_hash and decoded.get("crop_sha256") == digest(crop),
                "QR_DRIFT", label)
        require(decoded.get("decoded_value") == expected and q["printed_url"] == expected
                and expected in links, "QR_DESTINATION", label)
        require(present(decoded.get("decoder")) and present(decoded.get("checked_at")), "QR_TEST", label)

    qr_check(manifest["install_qr"], INSTALL, "install")
    install = receipt(manifest["install_check"], "anonymous install/linked manifest check")
    require(install.get("guide_url") == INSTALL and install.get("status") == "PASS"
            and install.get("access") == "anonymous" and present(install.get("checked_at")), "INSTALL_ACCESS", "guide")
    require(install.get("repository") == "https://github.com/dennisyu/local-service-spotlight-skills"
            and install.get("bundle") == "lss-everything"
            and bool(re.fullmatch(r"[0-9a-f]{40}", install.get("manifest_commit", "")))
            and install.get("linked_manifest_verified") is True, "INSTALL_MANIFEST", "actual linked manifest/bundle")
    guide_capture = artifact(install.get("guide_capture"), "inspected install guide").decode("utf-8")
    marketplace = receipt(install.get("manifest_capture"), "inspected linked marketplace manifest")
    bundles = marketplace.get("plugins", [])
    master = next((b for b in bundles if b.get("name") == "lss-everything"), {})
    members = master.get("skills", [])
    require(bool(members) and len(set(members)) == len(members)
            and install.get("master_skill_count") == len(members)
            and install.get("manifest_version") == marketplace.get("metadata", {}).get("version"),
            "INSTALL_MANIFEST", "captured version and bundle membership/count")
    require(present(install.get("manifest_url")) and install["manifest_url"] in guide_capture
            and install.get("resolved_manifest_url") in {
                f"https://github.com/dennisyu/local-service-spotlight-skills/blob/{install.get('manifest_commit')}/.claude-plugin/marketplace.json",
                f"https://raw.githubusercontent.com/dennisyu/local-service-spotlight-skills/{install.get('manifest_commit')}/.claude-plugin/marketplace.json"},
            "INSTALL_MANIFEST", "follow guide link and retain resolved commit URL")

    kit = manifest["kit"]
    require(type(kit["required"]) is bool and present(kit["basis"]), "KIT_SCOPE", "brief promise or N/A basis")
    require(type(brief.get("kit_required")) is bool and kit["required"] == brief.get("kit_required"),
            "KIT_SCOPE", "cannot waive the pinned engagement promise")
    kit_hash = None
    if kit["required"]:
        require(present(kit["url"]) and kit["url"] != INSTALL, "BESPOKE_KIT", "separate subject kit URL")
        package = artifact(kit["package"], "personalized kit")
        kit_hash = digest(package)
        require(review.get("kit_sha256") == kit_hash, "REVIEW_DRIFT", "review final kit")
        with zipfile.ZipFile(io.BytesIO(package)) as archive:
            names = archive.namelist()
            require(len(set(names)) == len(names), "KIT_CONTENTS", "no duplicate archive paths")
            contents = receipt(kit["contents_manifest"], "kit contents QA projection")
            require(contents["subject_id"] == manifest["subject_id"] and present(contents["version"])
                    and contents["source_revision"] == manifest["source_revision"], "KIT_IDENTITY", "subject/version/source")
            delivered = contents["delivered_manifest"]
            delivered_data = archive.read(delivered["path"])
            require(digest(delivered_data) == delivered["sha256"], "KIT_MANIFEST", "actual delivered manifest hash")
            delivered_json = json.loads(delivered_data)
            delivered_version = delivered_json
            for key in delivered["version_path"]:
                delivered_version = delivered_version[key]
            require(bool(delivered["version_path"]) and delivered_version == contents["version"],
                    "KIT_MANIFEST", "actual delivered manifest version matches QA projection")
            files = contents["files"]
            require(KIT_ROLES <= {f["role"] for f in files}, "KIT_CONTENTS", "all promised starter roles")
            require(len({f["path"] for f in files}) == len(files), "KIT_CONTENTS", "distinct file mapping; no generic file repeated as every role")
            for f in files:
                data = archive.read(f["path"])
                require(bool(data.strip()) and digest(data) == f["sha256"], "KIT_CONTENTS", f["path"])
            worked_skills = unique_rows(contents["skills"], "kit skill mappings")
            require(set(brief.get("promised_skills", [])) == set(kit["promised_skills"])
                    and set(kit["promised_skills"]) <= set(worked_skills), "KIT_SKILL", "all promised skills explained")
            for skill, row in worked_skills.items():
                require((repo / "skills" / row["canonical_route"] / "SKILL.md").is_file(), "KIT_SKILL", skill)
                require(row["instruction_path"] in {f["path"] for f in files if f["role"] == "instructions"},
                        "KIT_SKILL", f"{skill} instruction file")
                require(row["output_example_path"] in {f["path"] for f in files if f["role"] == "output_example"},
                        "KIT_SKILL", f"{skill} worked output file")
                for field in ("input", "output", "cadence", "human_gate", "handoff", "receipt"):
                    require(present(row.get(field)), "KIT_SKILL", f"{skill}.{field}")
        qr_check(kit["qr"], kit["url"], "kit")
        access = receipt(kit["access_check"], "recipient kit/download check")
        require(access.get("status") == "PASS" and access.get("access") in {"anonymous", "authorized_recipient"}
                and access.get("subject_id") == manifest["subject_id"] and access.get("final_url") == kit["url"]
                and access.get("downloaded_sha256") == kit_hash and access.get("contents_opened") is True
                and present(access.get("checked_at")), "KIT_ACCESS", "recipient and actual downloaded contents")
        gate = review.get("gates", {}).get("bespoke_kit", {})
        require(gate.get("status") == "PASS" and present(gate.get("basis")), "EDITORIAL_GATE", "bespoke kit")

    for state in manifest["lifecycle_claims"]:
        require(state["state"] in STATES and present(state["runtime"]) and present(state["source_revision"]),
                "LIFECYCLE", "named state/account/revision")
        proof = receipt(state["receipt"], "lifecycle state")
        require(proof.get("state") == state["state"] and proof.get("runtime") == state["runtime"]
                and proof.get("source_revision") == state["source_revision"]
                and present(proof.get("event_id")) and present(proof.get("checked_at")), "LIFECYCLE", "state-specific event")
        require(proof.get("kind") == {"AVAILABLE": "merged_source", "INSTALLED": "account_inventory",
                "ENABLED": "account_setting", "TESTED": "fresh_task_output", "SCHEDULED": "scheduler_definition",
                "OBSERVED": "scheduler_firing"}.get(state["state"]), "LIFECYCLE", "package existence is not state proof")

    return {"mechanical_status": "HOLD" if errors else "PASS", "acceptance_status": "HOLD" if errors else "REVIEW_REQUIRED",
            "errors": errors, "pdf_sha256": pdf_hash, "kit_sha256": kit_hash,
            "input_binding_sha256": input_binding(manifest),
            "distinct_supporting_urls": url_count, "underlying_records": origin_count,
            "private_record_locators": private_count,
            "limitations": "Checks local files and declarations. Does not certify authenticity, rights, complete claim inventory, visual quality, strategy, live access or installation."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--binding-only", action="store_true", help="Print input SHA256 for a reviewer; performs no acceptance check")
    args = parser.parse_args()
    if args.binding_only:
        try:
            print(input_binding(json.loads(args.manifest.read_text())))
            return 0
        except (OSError, ValueError, AttributeError, TypeError) as exc:
            print(json.dumps({"acceptance_status": "HOLD", "error": f"Cannot bind input: {exc}"}))
            return 2
    try:
        from pypdf.errors import PyPdfError
    except ImportError:
        print(json.dumps({"acceptance_status": "HOLD", "error": "Install scripts/requirements-personal-brand-qa.txt"}))
        return 2
    try:
        report = validate(json.loads(args.manifest.read_text()), args.manifest.resolve().parent,
                          Path(__file__).resolve().parents[1])
    except (OSError, ValueError, KeyError, TypeError, AttributeError, ImportError, zipfile.BadZipFile, PyPdfError) as exc:
        print(json.dumps({"acceptance_status": "HOLD", "error": f"Invalid input or setup: {type(exc).__name__}: {exc}"}))
        return 2
    print(json.dumps(report, indent=2))
    return 1 if report["errors"] else 0


if __name__ == "__main__":
    sys.exit(main())
