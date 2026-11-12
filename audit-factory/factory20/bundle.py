"""Bundle a finished factory run for the house audit-quality gate (UAQG 1.1.0).

    python -m factory20 bundle <run-dir>

writes, inside the run folder and nowhere else:

    uaqg-receipt.json       the tier receipt (UAQG-TIER-RECEIPT-1.0.0); run.json stays the call log
    bundle-manifest.json    UAQG-BUNDLE-1.0.0: hashes of the receipt, the artifacts and every envelope
    uaqg/evidence/*.json    one capture envelope per evidence row (UAQG-EVIDENCE-SNAPSHOT-1.0.0)
    uaqg/captures/*.json    what an envelope captures when the run has no file of its own for it

Grade it with  python3 docs/audit-quality/verify_bundle.py --root <run-dir> [--mode exercise].

The bundle maps only what the run contains. A required check is PASS only where a factory gate
tests the same thing on the final content (today: identity, gates G50 and G11, re-run here);
every other check stays UNKNOWN beside a NOT_CHECKED record that says what is missing. Reviewer
calibration stays NOT_RUN and the six quality ratings stay null: the Brand Authority score rates
the business, not the audit. The factory's own review is recorded as what it is and the house
independent review stays open (REVIEW_LIMITS). A cost is MEASURED only when the provider
reported every charge. A synthetic run is labelled synthetic in every row, so the gate's
production mode refuses it. A consistent bundle proves which bytes were graded, never that the
audit is right.
"""
from __future__ import annotations

import datetime as _dt
import hashlib
import json
import pathlib
import re
import shutil
from collections import Counter

from . import cost as K
from . import gates, model as M, pipeline, render
from .ledger import Ledger

RECEIPT = "uaqg-receipt.json"
MANIFEST = "bundle-manifest.json"
FOLDER = "uaqg"
FINISHED = ("brief.json", "ledger.json", "audit.json", "gate.json", "audit.pdf", "audit.pdf.render.json", "run.json")
DEMO_LEDGER = pathlib.Path(__file__).resolve().parent.parent / "fixtures" / "demo" / "ledger.json"
SYNTHETIC_LOCATOR = "synthetic-fixture:"
PDF_ID, JSON_ID = "audit-pdf", "audit-json"

# The gate's required checks and the evidence kind each needs: docs/audit-quality/product-
# profiles.json 1.0.0. A test keeps this table equal to that file.
CHECK_KINDS = {
    "authority": "AUTHORITY", "privacy": "PRIVACY_REVIEW", "fidelity": "FIDELITY_CROSSWALK",
    "provenance": "SOURCE_LEDGER", "usability": "RENDER_REVIEW", "reproducibility": "INDEPENDENT_REVIEW",
    "identity": "IDENTITY_MAPPING", "gct": "GCT_CROSSWALK", "measurement": "METRIC_RECONCILIATION",
    "visual_function": "VISUAL_MANIFEST", "actions": "ACTION_REGISTER", "links_access": "LINK_RECEIPT",
    "unknowns": "SOURCE_LEDGER", "corrections": "CORRECTION_CROSSWALK", "budget": "BUDGET_RECORD",
}
# Every factory visual block, as one of the gate's visual kinds (a test keeps it complete).
VISUAL_KIND = {
    "photo": "PHOTO", "screenshot": "SCREENSHOT",
    "bars": "CHART", "heatmap": "CHART", "donut": "CHART", "scorebar": "CHART", "swimlane": "CHART",
    "graph": "DIAGRAM", "flow": "DIAGRAM", "matrix": "DIAGRAM", "ladder": "DIAGRAM",
    "topic_wheel": "DIAGRAM", "finding_map": "DIAGRAM", "timeline": "DIAGRAM",
    "qr": "DIAGRAM",   # the gate has no kind for a QR code; its caption says it is a link
}
CLAIM_OF_BADGE = {"OBSERVED": ("FACT", "OBSERVED"), "INFERRED": ("FACT", "INFERRED"),
                  "UNKNOWN": ("UNKNOWN", "UNKNOWN")}
API_PROVIDERS = {"anthropic", "openrouter", "openai", "gemini"}
LEDGER_SECTIONS = ("items", "ambiguous", "conflicts", "unknowns")   # Ledger.from_json reads them in this order
REVIEW_LIMITS = (
    "It does not count as the house independent review: it reads audit.json, the ledger pack and the "
    "gate and render reports, but pipeline.review_prompt sends no page images (the review card says "
    "so), so no reviewer saw the rendered PDF; review.json records no hash of what was reviewed; the "
    "brief's do-not-print list is withheld from it; and the second review on a different model that the "
    "kit asks of pilot and enterprise audits is not run by the code.")


class BundleError(Exception):
    """The run cannot be bundled honestly as it stands; the message says what to fix."""


# ------------------------------------------------------------------ small helpers
def sha256(path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).replace(microsecond=0).isoformat()


def _iso_date(value) -> str | None:
    return M.iso_day(value)        # one rule: the pipeline checks capture_date by it before any call


def _tz_aware(value) -> bool:
    try:
        return _dt.datetime.fromisoformat(str(value).replace("Z", "+00:00")).tzinfo is not None
    except ValueError:
        return False


def _file_date(path: pathlib.Path) -> str:
    return _dt.datetime.fromtimestamp(path.stat().st_mtime, _dt.timezone.utc).date().isoformat()


def _plain(text) -> str:
    return re.sub(r"\s+", " ", str(text or "").replace("**", "")).strip()


def _or(text, fallback: str) -> str:
    return _plain(text) or fallback


def _inside(run: pathlib.Path, rel) -> pathlib.Path | None:
    """A regular file inside the run folder with no symlink on the way, else None. The gate
    refuses symlinks and paths that leave the bundle, so the bundle never binds one."""
    if not isinstance(rel, str) or not rel.strip():
        return None
    parts = pathlib.Path(rel)
    if parts.is_absolute() or ".." in parts.parts:
        return None
    cur = run
    for part in parts.parts:
        cur = cur / part
        if cur.is_symlink():
            return None
    return cur if cur.is_file() and cur.resolve().is_relative_to(run.resolve()) else None


def _read(run: pathlib.Path, name: str):
    try:
        return json.loads((run / name).read_text(encoding="utf-8"))
    except ValueError as e:
        raise BundleError(f"{name} is not valid JSON: {e}") from None


# ------------------------------------------------------------------ load and cross-check the run
def load_run(run_dir) -> dict:
    """Read a finished run and prove its records describe the same final files."""
    run = pathlib.Path(run_dir).resolve()
    if not run.is_dir():
        raise BundleError(f"{run} is not a run folder")
    missing = [f for f in FINISHED if _inside(run, f) is None]
    if missing:
        hint = " (render it: run without --no-render)" if "audit.pdf" in missing else ""
        raise BundleError("not a finished run: missing or not a regular file: " + ", ".join(missing) + hint)
    ctx = {"run": run, "brief": _read(run, "brief.json"), "ledger_data": _read(run, "ledger.json"),
           "audit": _read(run, "audit.json"), "gate": _read(run, "gate.json"),
           "render": _read(run, "audit.pdf.render.json"), "log": _read(run, "run.json"),
           "review": _read(run, "review.json") if _inside(run, "review.json") else None}
    ctx["ledger"] = Ledger.from_json(ctx["ledger_data"])
    ctx["attempts"] = list(ctx["log"].get("attempts", []))
    ctx["tier"] = ctx["log"].get("tier") or "UNKNOWN"
    ctx["full"] = render.expand(ctx["audit"], ctx["ledger"])
    for name in ("audit.pdf", "audit.json", "ledger.json"):
        ctx[name] = sha256(run / name)
    ctx["demo_ledger"] = DEMO_LEDGER.is_file() and sha256(DEMO_LEDGER) == ctx["ledger.json"]
    _check_gates(ctx)
    _check_render(ctx)
    ctx["sources"] = _source_log(ctx)
    return ctx


def _check_gates(ctx: dict) -> None:
    """Re-run the free content gates on the final audit.json; gate.json must say the same."""
    brief = ctx["brief"]
    stored = [(c.get("id"), c.get("status")) for c in ctx["gate"].get("checks", [])]
    first = ctx["tier"] if ctx["tier"] in gates.TIERS else "standard"     # pipeline._check_all's choice
    for tier in [first] + [t for t in gates.TIERS if t != first]:
        rep = gates.gate_audit(ctx["full"], ctx["ledger"], tier, do_not_print=brief.get("do_not_print", []),
                               allowed_phones=brief.get("allowed_phones", [])).summary()
        if [(c["id"], c["status"]) for c in rep["checks"]] == stored:
            break
    else:
        raise BundleError("gate.json does not match the content gates re-run on the final audit.json; "
                          "re-run `factory20 run` so the gate report describes the final files")
    if rep["verdict"] == "HOLD":
        failing = sorted({c["id"] for c in rep["checks"] if c["status"] == "FAIL"})
        raise BundleError(f"the factory's own content gates hold this run ({', '.join(failing)}); "
                          "fix it and re-run before bundling")
    ctx["gate_tier"], ctx["gate_rerun"] = tier, rep


def _check_render(ctx: dict) -> None:
    """The render report must describe this audit.pdf, and its gates must not hold."""
    rr = ctx["render"]
    install = ctx["audit"].get("meta", {}).get("install_url", render.INSTALL_URL)
    rep = gates.gate_render(rr, install).summary()
    stored = [(c.get("id"), c.get("status")) for c in (rr.get("gates") or {}).get("checks", [])]
    if [(c["id"], c["status"]) for c in rep["checks"]] != stored:
        raise BundleError("audit.pdf.render.json's gates do not match a re-run of the render gates")
    if rep["verdict"] == "HOLD":
        failing = sorted({c["id"] for c in rep["checks"] if c["status"] == "FAIL"})
        raise BundleError(f"the factory's own render gates hold this run ({', '.join(failing)})")
    pdf = _pdf_facts(ctx["run"] / "audit.pdf")
    if (pdf["pages"], pdf["links"]) != (rr.get("pdf_pages"), rr.get("links")):
        raise BundleError(f"audit.pdf has {pdf['pages']} pages and {pdf['links']} link annotations but its render "
                          f"report says {rr.get('pdf_pages')} and {rr.get('links')}; re-render before bundling")
    if pdf["pages"] != len(ctx["full"].get("pages", [])):
        raise BundleError(f"audit.pdf has {pdf['pages']} pages but audit.json has {len(ctx['full'].get('pages', []))}")
    ctx["pdf"], ctx["render_rerun"] = pdf, rep


def _pdf_facts(path: pathlib.Path) -> dict:
    from pypdf import PdfReader

    try:
        reader = PdfReader(str(path))
        pages = len(reader.pages)
        links = sum(1 for pg in reader.pages for a in (pg.get("/Annots") or [])
                    if a.get_object().get("/Subtype") == "/Link")            # the count render.render records
        meta = reader.metadata or {}
    except Exception as e:                                                   # pypdf raises many types on a bad file
        raise BundleError(f"audit.pdf cannot be read: {e}") from None
    return {"pages": pages, "links": links, "creator": str(meta.get("/Creator") or "not recorded"),
            "producer": str(meta.get("/Producer") or "not recorded")}


def synthetic_reasons(ctx: dict) -> list[str]:
    """Why this run is synthetic (empty for a real run). Synthetic runs never reach production."""
    why = []
    if str(ctx["brief"].get("confidentiality", "")).upper().startswith("SYNTHETIC"):
        why.append("brief.json confidentiality starts with SYNTHETIC (the rule gate G81 uses)")
    if str(ctx["ledger_data"].get("method_note", "")).upper().startswith("SYNTHETIC"):
        why.append("ledger.json method_note says SYNTHETIC")
    if ctx["demo_ledger"]:
        why.append("ledger.json is the shipped demo fixture")
    fake = sum(1 for a in ctx["attempts"] if a.get("provider") == "fake")
    if fake:
        why.append(f"{fake} of {len(ctx['attempts'])} model answers were replayed by the stand-in (provider fake)")
    return why


# ------------------------------------------------------------------ evidence rows
def _row(eid, kind, purpose, locator, inspection, scope, source_date, when, artifact=None, reviewer=None) -> dict:
    return {"id": eid, "kind": kind, "purpose": purpose, "locator": locator, "observed_at": when,
            "inspection": inspection, "artifact_sha256": artifact, "reviewer_id": reviewer,
            "covered_pages": [], "scope": scope, "source_date": source_date, "retrieved_at": when}


def _source_log(ctx: dict) -> dict:
    """sources.jsonl (stage 10): url -> its capture, when exactly one unblocked line has that URL."""
    run = ctx["run"]
    path = _inside(run, "sources.jsonl")
    ctx["source_log"] = {"lines": 0, "unreadable": 0}
    if path is None:
        return {}
    by_url: dict[str, list] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        ctx["source_log"]["lines"] += 1
        try:
            rec = json.loads(line)
        except ValueError:
            ctx["source_log"]["unreadable"] += 1
            continue
        if isinstance(rec, dict) and rec.get("url") and str(rec.get("status", "")).lower() != "blocked":
            by_url.setdefault(rec["url"], []).append(rec)
    out = {}
    reserved = {"audit.pdf", "audit.json", RECEIPT, MANIFEST}
    for url, recs in by_url.items():
        if len(recs) != 1:
            continue                                 # the ledger row does not say which capture it came from
        rel = recs[0].get("path")
        rel = pathlib.Path(rel).as_posix() if isinstance(rel, str) and rel.strip() else None
        usable = rel and _inside(run, rel) and rel not in reserved and not rel.startswith(FOLDER + "/")
        out[url] = {"file": rel if usable else None, "captured_at": recs[0].get("captured_at")}
    return out


def _ledger_evidence(ctx: dict) -> list[dict]:
    """One SOURCE row per ledger row; its capture is the row as recorded, or its own source capture."""
    data, rows = ctx["ledger_data"], ctx["ledger"].rows
    captured = _iso_date(data.get("capture_date"))
    if not captured:
        raise BundleError(f"ledger.json capture_date is {data.get('capture_date')!r}, not one date "
                          "(YYYY-MM-DD); every source needs a date")
    raw = [(sec, r) for sec in LEDGER_SECTIONS for r in (data.get(sec) or [])]
    sources, out, seen = ctx["sources"], [], set()
    ctx["skipped_rows"] = 0
    for (sec, r), norm in zip(raw, rows):
        eid = norm["id"]
        if not eid:
            ctx["skipped_rows"] += 1                 # an id-less row cannot be cited by anything
            continue
        if eid in seen:
            raise BundleError(f"ledger.json uses id {eid} twice; a citation must point to one row")
        seen.add(eid)
        when, match = captured, sources.get(norm["url"]) if norm["url"] else None
        capture, data_obj = None, {"captured": "the ledger row as the harvest recorded it, not a snapshot of the "
                                               "original source", "ledger": "ledger.json",
                                   "ledger_sha256": ctx["ledger.json"], "section": sec, "row": r}
        how = "capture: the ledger row as recorded (the run folder has no capture of this source)"
        if match and match["file"]:
            capture, data_obj = match["file"], None
            how = f"capture: {match['file']}, the only sources.jsonl capture of this URL"
        if match and _tz_aware(match["captured_at"]):
            when = match["captured_at"]
        timing = "" if _tz_aware(when) else "; retrieved on the ledger's capture date, no time or timezone recorded"
        published = _iso_date(norm["published"])
        dated = ("" if published else
                 f"; published '{norm['published'] or 'not given'}', so the source date is the capture date")
        scope = (f"Ledger {sec} row: {norm['cls']}, state {norm['state']}"
                 + (f", subject match {norm['match']}" if norm["match"] else "") + f"; {how}{timing}{dated}. "
                 "Inspection is as the harvest recorded it; the bundle did not re-open the source.")
        row = _row(eid, "SOURCE", "claim", norm["url"] or f"ledger.json#{eid}",
                   "NOT_CHECKED" if norm["state"] == "UNKNOWN" else "CONTENT_INSPECTED",
                   scope, published or captured, when)
        out.append({"row": row, "capture": capture, "data": data_obj})
    return out


def _review_record(ctx: dict) -> dict | None:
    """What the factory review was, from review.json and run.json's review calls."""
    rv = ctx["review"]
    if rv is None:
        return None
    calls = [a for a in ctx["attempts"] if a.get("stage") == "review"]
    providers = {a.get("provider") for a in calls}
    findings = rv.get("findings") or []
    said = f"verdict {rv.get('verdict')}, {len(findings)} findings"
    if not calls:
        return {"reviewer": None, "fresh": False, "said": said,
                "what": "review.json is present but run.json logs no review call, so who wrote it is UNKNOWN."}
    if "fake" in providers:
        return {"reviewer": None, "fresh": False, "said": said,
                "what": "The review was replayed by the stand-in (provider fake): no review model ran."}
    last = ([a for a in calls if not a.get("problems")] or calls)[-1]      # the answer review.json holds
    if "manual" in providers:
        return {"reviewer": "factory20 review stage, answered through the manual provider by an app session "
                            "(model UNKNOWN)", "fresh": False, "said": said,
                "what": "An app session answered the review prompt file; its context and model are not recorded."}
    served = f", served by {last['served_by']}" if last.get("served_by") else ""
    writers = {a.get("model") for a in ctx["attempts"] if a.get("stage") == "synthesis"}
    same = " The same model wrote the findings (stage synthesis)." if last.get("model") in writers else ""
    return {"reviewer": f"factory20 review stage: {last.get('model')} via {last.get('provider')}{served}",
            "fresh": last.get("provider") in API_PROVIDERS, "said": said,
            "what": f"A fresh-context model review (stage 80, {len(calls)} call(s)).{same}"}


def _run_evidence(ctx: dict, when: str) -> list[dict]:
    """The run's own records, bound where they lie in the run folder (identity is an extract)."""
    run, out = ctx["run"], []

    def add(eid, rel, kind, purpose, scope, artifact=None, reviewer=None, inspection="CONTENT_INSPECTED",
            source_date=None, data=None):
        capture = None if data is not None else rel
        loc = rel if data is None else "audit.json#/meta/identity"
        date = source_date or _file_date(run / (rel if data is None else "audit.json"))
        out.append({"row": _row(eid, kind, purpose, loc, inspection, scope, date, when, artifact, reviewer),
                    "capture": capture, "data": data})

    st = ctx["ledger"].stats()
    add("RUN-ledger", "ledger.json", "SOURCE_LEDGER", "provenance",
        f"The run's evidence ledger: {st['evidence']} evidence rows, {st['ambiguous']} namesake rows, "
        f"{st['conflicts']} conflict groups, {st['unknowns']} named unknowns; each row is also its own evidence row.",
        source_date=_iso_date(ctx["ledger_data"].get("capture_date")))
    if _inside(run, "sources.jsonl"):
        add("RUN-source-log", "sources.jsonl", "SOURCE_LEDGER", "provenance",
            f"The stage-10 capture log: {ctx['source_log']['lines']} lines, {ctx['source_log']['unreadable']} unreadable.")
    g = ctx["gate_rerun"]
    add("RUN-gate-report", "gate.json", "MECHANICAL_VALIDATION", "provenance",
        f"The factory's content gates on audit.json: {g['pass']} PASS, {g['warn']} WARN, {g['fail']} FAIL. The bundle "
        f"re-ran them on the final audit.json (tier {ctx['gate_tier']}) and got the same statuses.",
        artifact=ctx["audit.json"])
    pdf, rr = ctx["pdf"], ctx["render_rerun"]
    add("RUN-render-report", "audit.pdf.render.json", "MECHANICAL_VALIDATION", "usability",
        f"Renderer measurements and render gates R01-R05 ({rr['verdict']}). The bundle re-ran the gates and read "
        f"audit.pdf itself: {pdf['pages']} pages and {pdf['links']} link annotations, as the report says.",
        artifact=ctx["audit.pdf"])
    providers = dict(Counter(a.get("provider", "unknown") for a in ctx["attempts"]))
    add("RUN-call-log", "run.json", "BUDGET_RECORD", "budget",
        f"The factory's call and cost log, unchanged: {len(ctx['attempts'])} calls by provider {providers}.")
    rv = _review_record(ctx)
    if rv:
        add("RUN-review", "review.json", "INDEPENDENT_REVIEW", "reproducibility",
            f"Factory review ({rv['said']}). {rv['what']} {REVIEW_LIMITS}", reviewer=rv["reviewer"],
            inspection="CONTENT_INSPECTED" if rv["reviewer"] else "NOT_CHECKED")
    ident = (ctx["audit"].get("meta") or {}).get("identity") or {}
    checks = {c["id"]: c for c in ctx["gate_rerun"]["checks"] if c["id"] in ("G50", "G11")}
    attrs = [a for a in ident.get("attributes", []) if M.refs_in(a)]
    extract = {"captured": "the identity mapping in the final audit.json, with the identity gates the bundle re-ran",
               "audit_json_sha256": ctx["audit.json"], "identity": ident,
               "identity_json_sha256": sha256(run / "identity.json") if _inside(run, "identity.json") else None,
               "gates_rerun": list(checks.values())}
    add("RUN-identity", None, "IDENTITY_MAPPING", "identity",
        f"Identity {ident.get('status', 'UNKNOWN')} with {len(attrs)} evidenced attributes and "
        f"{len(ident.get('namesakes') or [])} namesakes set aside; gate G50 "
        f"{checks.get('G50', {}).get('status', 'not run')}, G11 {checks.get('G11', {}).get('status', 'not run')} "
        "on the final audit.json.", artifact=ctx["audit.pdf"], data=extract)
    ctx["review_record"] = rv
    return out


def _gaps(ctx: dict) -> dict:
    """For each required check the factory does not perform: what exists, and the next step."""
    links, pages = ctx["pdf"]["links"], ctx["pdf"]["pages"]
    review = ["RUN-review"] if ctx["review"] is not None else []
    stated = [k for k in ("goal", "buyer") if _plain(ctx["brief"].get(k))]
    brief = f"brief.json states {' and '.join(stated) if stated else 'neither a goal nor a buyer'}"
    return {
        "authority": ("No authority, owner, publisher or hold record is in the run folder; brief.json names who the "
                      "audit is for and who prepared it, which is not authorization.",
                      "Record the current authority, outcome owner, publisher and holds, and where that record lives.", []),
        "privacy": ("Gates G70-G74 scanned audit.json text for personal emails, phone numbers, credentials and the "
                    "brief's do-not-print items. Nobody independent inspected the final PDF, its metadata, hidden "
                    "text or link targets.",
                    "An independent reviewer inspects the exact final PDF for privacy and records it against its SHA256.",
                    ["RUN-gate-report"]),
        "fidelity": ("No baseline-to-candidate crosswalk is recorded; the factory does not compare a run with an "
                     "earlier edition.",
                     "Name the baseline (an earlier audit of this subject, or none) and record the crosswalk.", []),
        "provenance": ("G10 found every cited id in the ledger and G14 counted ids per page; nothing checks that each "
                       "cited row supports the sentence citing it, or that conflicts are resolved or limited.",
                       "A reviewer traces every material claim to its cited rows and records the result.",
                       ["RUN-ledger", "RUN-gate-report"]),
        "usability": (f"Render gates R01-R05 measured {pages} pages, overflow, fill, {links} link annotations and the "
                      "QR code. Nobody independent looked at the rendered pages.",
                      f"An independent reviewer inspects all {pages} rendered pages and records a design result "
                      "against the PDF's SHA256.", ["RUN-render-report"]),
        "reproducibility": ("No independent exact-artifact review is recorded. The factory's own review, if any, is "
                            "RUN-review and does not meet this requirement.",
                            "A fresh-context independent reviewer reviews the exact final files, PDF included, and "
                            "records content/privacy and design results against their hashes.", review),
        "gct": (f"No goal, content and targeting crosswalk is recorded ({brief}; no agreement on either is recorded).",
                "Record the agreed goal and buyer, and map each finding and action to them.", []),
        "measurement": ("No check reconciles the audit's figures with their sources (units, windows, cohorts).",
                        "Reconcile every number on pages 1-2 and every exam row with the cited rows.", []),
        "visual_function": ("G40 found a visual block on every page and the receipt lists each page's visual; no "
                            "reviewer confirmed that each visual explains its page's finding, and no page has a "
                            "render review.",
                            "A reviewer checks the page-by-page visual manifest against the rendered pages.",
                            ["RUN-gate-report", "RUN-render-report"]),
        "actions": ("G60-G65 checked the action contract (owner function, dependency, approval gate, due date, "
                    "observable test, evidence). The factory's actions carry no business metric, and only actions "
                    "an insight card links to point back to a finding id.",
                    "Add a business metric (with source and baseline, or UNKNOWN) to each action and review the register.",
                    ["RUN-gate-report"]),
        "links_access": (f"The PDF carries {links} link annotations; none was opened, so reachability, expected "
                         "content, recipient access and media inspection are all unchecked.",
                         "Open every material link and record the four link states with evidence.",
                         ["RUN-render-report"]),
        "unknowns": ("The ledger names its unknown rows and the exam keeps UNKNOWN rows out of the total; nothing "
                     "checks that every UNKNOWN in the audit states its limitation and next verification.",
                     "A reviewer checks each UNKNOWN on the pages for a limitation and a next step.", ["RUN-ledger"]),
        "corrections": ("Fix rounds rebuild pages from the stage files and re-run every gate, but no correction "
                        "crosswalk is recorded.",
                        "Record each correction, its source and every output it reached.", ["RUN-call-log"]),
        "budget": ("run.json logs each call's charge, but the spending cap the run used is not recorded and no agreed "
                   "allowance is in the run folder.",
                   "Record the agreed time/cost allowance and the cap the run used.", ["RUN-call-log"]),
    }


def _gap_evidence(ctx: dict, open_checks: list[str], exam_scope: str | None, when: str) -> list[dict]:
    gaps, today, out = _gaps(ctx), when[:10], []

    def add(eid, kind, purpose, what, step, related):
        rel = f"{FOLDER}/captures/{eid}.json"
        data = {"gap": eid, "required_evidence_kind": kind, "inspection": "NOT_CHECKED", "what_exists": what,
                "next_step": step, "related_evidence": related}
        out.append({"row": _row(eid, kind, purpose, rel, "NOT_CHECKED", f"NOT CHECKED. {what} Next: {step}", today, when),
                    "capture": None, "data": data})

    for name in open_checks:
        what, step, related = gaps[name]
        add(f"GAP-{name}", CHECK_KINDS[name], name, what, step, related)
    add("GAP-routing", "CAPABILITY_TEST", "routing",
        "No stage has a recorded capability test on this task's evidence; a model name is not one.",
        "Record, per stage, the test that shows its executor handles this evidence and its negative cases.", [])
    if exam_scope:
        add("GAP-exam", "EXAM_VALIDATION", "specialist_exam",
            f"No independent validation of the {exam_scope} scoring is recorded, and the run does not record which "
            "rubric source revision factory20.score implements; gates G51-G54 check the arithmetic only.",
            "Pin the rubric source revision, then have an independent reviewer validate the exam rows for this artifact.",
            ["RUN-gate-report"])
    return out


# ------------------------------------------------------------------ claims, actions, pages
def _claims_and_actions(ctx: dict) -> tuple[list, list]:
    """Insight cards become claims; the action register becomes actions. An action no card links
    to points back to its own 'finding' label, kept as REPORTED by the register."""
    claims = []
    for p in sorted(ctx["audit"].get("pages", []), key=lambda x: x.get("n", 0)):
        items = [i for b in p.get("blocks", []) if b.get("type") == "cards" for i in b.get("items", [])]
        for k, item in enumerate(items, 1):
            ctype, state = CLAIM_OF_BADGE.get(item.get("badge"), ("FACT", "NOT_CHECKED"))
            unknown = ctype == "UNKNOWN"
            claims.append({
                "id": f"P{int(p.get('n', 0)):02d}-C{k}", "material": True, "type": ctype, "evidence_state": state,
                "statement": _or(item.get("title"), "The card has no title."),
                "evidence_ids": M.refs_in(item), "requires_content_inspection": not unknown,
                "limitation": _plain(item.get("body")) or None if unknown else None,
                "interpretation": _or(item.get("body"), "The card has no body."),
                "goal_consequence": _or(item.get("so"), "Not stated on the card."),
                "buyer_consequence": "Not stated separately on the card.",
                "action_ids": M.action_refs_in(item),
                "next_verification": _plain(item.get("so")) or None if unknown else None})
    linked: dict[str, list] = {}
    for c in claims:
        for aid in c["action_ids"]:
            linked.setdefault(aid, []).append(c["id"])
    actions = []
    for a in ctx["audit"].get("actions", []):
        aid = a.get("id")
        if not linked.get(aid):
            ev = M.refs_in({"evidence": a.get("evidence")})
            claims.append({
                "id": f"AF-{aid}", "material": True, "type": "FACT", "evidence_state": "REPORTED",
                "statement": _or(a.get("finding"), f"The register states no finding for {aid}."),
                "evidence_ids": ev, "requires_content_inspection": True,
                "limitation": f"Stated only as the action register's finding for {aid}; "
                              "no insight card states or badges it.",
                "interpretation": f"The register pairs this finding with {aid}: {_or(a.get('action'), 'not stated')}",
                "goal_consequence": "Not stated beyond the paired action.", "buyer_consequence": "Not stated.",
                "action_ids": [aid],
                "next_verification": f"Check it against its cited rows ({', '.join(ev) or 'none cited'}) "
                                     "before relying on it."})
            linked[aid] = [f"AF-{aid}"]
        actions.append(_action(a, linked[aid]))
    return claims, actions


def _action(a: dict, finding_ids: list) -> dict:
    window = f"; {a['window']}-day window" if a.get("window") else ""
    gate = _or(a.get("human_gate"), "No approval gate stated")
    return {"id": a.get("id"), "finding_ids": finding_ids, "evidence_ids": M.refs_in({"evidence": a.get("evidence")}),
            "owner_function": _or(a.get("function"), "Not stated"), "owner_state": "PROPOSED",
            "first_step": _or(a.get("action"), "Not stated"),
            "dependencies": [_plain(a["dependency"])] if _plain(a.get("dependency")) else [],
            "authority": f"{gate} (executor {a.get('executor') or 'not stated'}"
                         + (f"; pre-approved: {_plain(a['pre_approved'])}" if a.get("pre_approved") else "") + ")",
            "due_or_timeframe": f"{_or(a.get('due'), 'no date')} (proposed{window})", "date_state": "PROPOSED",
            "destination": _or(a.get("destination"), "Not stated"), "done_when": _or(a.get("acceptance_test"), "Not stated"),
            "business_metric": {"name": "Not stated in the factory's action register", "source": None, "baseline": None}}


def _visual_manifest(ctx: dict) -> list[dict]:
    """One entry per rendered page: the page's lead visual from render.expand (what the renderer drew)."""
    out = []
    for p in sorted(ctx["full"].get("pages", []), key=lambda x: x.get("n", 0)):
        blocks = p.get("blocks", [])
        vis = sorted((b for b in blocks if b.get("type") in VISUAL_KIND), key=lambda b: b.get("type") == "qr")
        micro = [i for b in blocks if b.get("type") == "cards" for i in b.get("items", []) if i.get("viz")]
        if vis:
            lead = vis[0]
            label = (lead.get("title") or lead.get("caption") or lead.get("center_label")
                     or " x ".join(filter(None, [lead.get("y_label"), lead.get("x_label")])) or "untitled in audit.json")
            caption = f"{lead['type']}: {_plain(label)}"
            if lead["type"] == "qr":
                caption += (f" ({lead.get('url', '')}); a QR code is a link, not an explanatory figure, so the "
                            "meaningful-visual review must judge this page")
            if vis[1:]:
                caption += f" (also: {', '.join(b['type'] for b in vis[1:])})"
            kind = VISUAL_KIND[lead["type"]]
        elif len(micro) >= 2:                          # gate G40 counts card micro-charts as the page visual
            kind, caption = "CHART", f"micro-charts on {len(micro)} insight cards"
        else:
            raise BundleError(f"page {p.get('n')} has no visual block; gate G40 should have held the run")
        out.append({"page": p.get("n"), "question": _or(p.get("kicker"), str(p.get("type", "page"))), "kind": kind,
                    "source_ids": M.refs_in(p), "caption": caption, "render_receipt_id": "GAP-usability"})
    return out


# ------------------------------------------------------------------ routing, timing, defects
def _calls_by(ctx: dict, stage: str) -> str | None:
    calls = [a for a in ctx["attempts"] if a.get("stage") == stage]
    if not calls:
        return None
    seen = []
    for a in calls:
        m, prov = a.get("model"), a.get("provider")
        who = (f"stand-in replay (provider fake) for {m}" if prov == "fake" else
               f"an app session via the manual provider (model UNKNOWN; configured {m})" if prov == "manual" else
               f"{m} via {prov}" + (f" ({a['served_by']})" if a.get("served_by") else ""))
        if who not in seen:
            seen.append(who)
    return "; ".join(seen)


def _stage_text(ctx: dict, stages: list[str], cfg: dict) -> tuple[str, str]:
    tier = cfg["tiers"].get(ctx["tier"], {}).get("models", {})
    plan = {s["id"]: s.get("effort", "none") for s in cfg["stages"]}
    who, effort = [], []
    for st in stages:
        calls = [a for a in ctx["attempts"] if a.get("stage") == st]
        why = " (stage file reused or supplied)" if st in pipeline.CHECKS else ""
        who.append(f"{st}: " + (_calls_by(ctx, st) or f"{tier.get(st, 'UNKNOWN')} per the tier; no call logged{why}"))
        efforts = sorted({str(a.get("effort") or "none") for a in calls})
        effort.append(f"{st}: " + ("/".join(efforts) if efforts else f"{plan.get(st, 'UNKNOWN')} (planned, no call logged)"))
    return "; ".join(who), "; ".join(effort)


def _routing(ctx: dict, synthetic: bool) -> list[dict]:
    cfg = K.load_routing()
    models = cfg["tiers"].get(ctx["tier"], {}).get("models", {})
    ladder = ("router.run_stage: retry once with the failure list, then one rung up the tier's ladder; a confidential "
              "brief skips flagged models; a call that could cross the spending cap is not made")
    code = "None: a failed hard gate holds the audit"
    captures = any(v["file"] for v in ctx["sources"].values())
    upstream = "NOT_REQUIRED" if synthetic else ("VERIFIED" if captures else "MISSING")
    if ctx["demo_ledger"]:
        collect = harvest = "none: ledger.json is the shipped synthetic fixture, copied by `factory20 init --from-demo`"
    else:
        collect = "outside factory20 (stages/10-collect.md; no collector code); the run folder does not record who collected"
        harvest = (f"outside factory20 (stages/20-harvest.md; no harvest code; the tier names "
                   f"{models.get('harvest', 'UNKNOWN')}); the run folder does not record who harvested")
    ident_who, ident_eff = _stage_text(ctx, ["identity"], cfg)
    syn_who, syn_eff = _stage_text(ctx, ["score", "synthesis", "pages", "actions", "fix"], cfg)
    rev_who, rev_eff = _stage_text(ctx, ["review"], cfg)
    pdf, missing = ctx["pdf"], ctx["render"].get("missing_assets") or []
    rows = [
        ("RETRIEVAL", collect, "UNKNOWN", upstream, "None recorded in the run folder"),
        ("PARSING", harvest, "UNKNOWN", upstream, "None recorded in the run folder"),
        ("ARITHMETIC", "factory20.score and factory20.gates (deterministic code; the bundle re-ran the gates)",
         "none: deterministic code", "VERIFIED", code),
        ("IDENTITY", ident_who, ident_eff, "VERIFIED", ladder),
        ("SYNTHESIS", syn_who, syn_eff, "VERIFIED", ladder),
        ("LAYOUT", f"factory20.render (HTML to PDF); the PDF names creator '{pdf['creator']}' and producer "
                   f"'{pdf['producer']}'", "none: deterministic code", "MISSING" if missing else "VERIFIED",
         "One fit step for an overflowing page, then render gates R01-R03 hold the audit"),
        ("FINAL_REVIEW", rev_who + "; the review prompt carries the ledger and audit.json, not the PDF pages",
         rev_eff, "MISSING", ladder),
    ]
    return [{"stage": s, "executor": who, "effort": eff, "capability_evidence_id": "GAP-routing",
             "source_access": acc, "fallback": fb} for s, who, eff, acc, fb in rows]


def _timing(ctx: dict) -> tuple[dict, float | None]:
    calls = ctx["attempts"]
    unknown = {"value": None, "unit": "UNKNOWN", "state": "UNKNOWN", "method": None, "evidence_id": None}
    t = {k: dict(unknown) for k in ("brief_demo", "draft", "qa", "human", "waits")}
    providers = Counter(a.get("provider", "unknown") for a in calls)
    stand_in = f" {providers['fake']} were stand-in replays (provider fake), not model time." if providers["fake"] else ""
    t["agent_runtime"] = {"value": round(sum(float(a.get("seconds") or 0) for a in calls), 1), "unit": "seconds",
                          "state": "MEASURED", "evidence_id": "RUN-call-log",
                          "method": f"Sum of the wall-clock seconds run.json logs for {len(calls)} model calls, made one "
                                    f"at a time; excludes local gate and render time.{stand_in}"}
    drafted, acted, retries, fixes, secs = False, False, 0, 0, 0.0
    for a in calls:
        st = a.get("stage")
        retry = (a.get("attempt") or 1) > 1
        # the findings or score writer after the pages exist, or the register writer after its
        # first draft, is revising: a fix-round call (the score revision dates from Nov 12)
        fix_round = st == "fix" or (st in ("synthesis", "score") and drafted) or (st == "actions" and acted and not retry)
        retries, fixes = retries + retry, fixes + fix_round
        secs += float(a.get("seconds") or 0) if (retry or fix_round) else 0.0
        drafted = drafted or st in ("pages", "actions", "review", "fix")
        acted = acted or st == "actions"
    t["retries_rework"] = {"value": round(secs, 1), "unit": "seconds", "state": "MEASURED", "evidence_id": "RUN-call-log",
                           "method": f"Seconds of the {retries} retry attempts and {fixes} fix-round calls in run.json "
                                     f"(attempt above 1, stage fix, a findings or score revision after pages were "
                                     f"drafted, or a register revision).{stand_in}"}
    replied = [a for a in calls if "cost_source" in a]
    measured = bool(replied) and all(a["cost_source"] == "reported" for a in replied) and set(providers) <= API_PROVIDERS
    estimate = round(sum(a.get("usd") or 0 for a in calls), 4)
    if measured:
        value = round(sum(a.get("usd") or 0 for a in replied), 6)
        t["actual_cost"] = {"value": value, "unit": "USD", "state": "MEASURED", "evidence_id": "RUN-call-log",
                            "method": f"Sum of the charges the provider reported for {len(replied)} calls (run.json "
                                      f"cost_source 'reported'); {len(calls) - len(replied)} failed calls "
                                      "reported no charge."}
        return t, value
    why = []
    if providers["fake"]:
        why.append(f"no model API was called for {providers['fake']} answers replayed by the stand-in; their usd values "
                   "are list-price arithmetic on character-count stand-in tokens, not charges")
    if providers["manual"]:
        why.append(f"{providers['manual']} answers came from an app session whose cost the log does not hold")
    if any(a.get("cost_source") == "list price" and a.get("provider") in API_PROVIDERS for a in calls):
        why.append("some calls carry only a list-price estimate from token counts, not a provider-reported charge")
    t["actual_cost"] = {"value": None, "unit": "UNKNOWN", "state": "UNKNOWN", "evidence_id": "RUN-call-log",
                        "method": f"Not measured: {'; '.join(why) or 'no call reported a charge'}. run.json sums to "
                                  f"${estimate} (an estimate, not a bill)."}
    return t, None


def _defects(ctx: dict) -> list[dict]:
    """Open items the run itself recorded: gate WARNs (the kit's fix-before-send notes, so S2)
    and every finding in review.json at the severity it was given (RUN-review says who gave it)."""
    out, seen = [], Counter()

    def add(base, severity):
        seen[base] += 1
        out.append({"id": base if seen[base] == 1 else f"{base}-{seen[base]}", "severity": severity, "closed": False,
                    "closure_review_receipt": None, "disposition": dict.fromkeys(
                        ("accepted_by", "risk_reason", "owner", "deadline", "completion_test"))})

    for prefix, rep in (("GATE", ctx["gate_rerun"]), ("RENDER", ctx["render_rerun"])):
        for c in rep["checks"]:
            if c["status"] != "PASS":
                add(f"{prefix}-{c['id']}", "S2" if c["status"] == "WARN" else "S1")
    for i, f in enumerate((ctx["review"] or {}).get("findings") or [], 1):
        if f.get("severity") in ("S0", "S1", "S2", "S3"):
            add(f"REVIEW-{_or(f.get('id'), str(i))}", f["severity"])
    return out


# ------------------------------------------------------------------ the receipt
def _exam(ctx: dict) -> dict | None:
    ba = (ctx["audit"].get("exams") or {}).get("brand_authority")
    if not ba:
        return None
    exam_id, _, version = str(ba.get("rubric") or "brand-authority").partition("@")
    # The run records no rubric source revision for factory20.score; GAP-exam says so.
    return {"id": exam_id, "version": version or "UNKNOWN", "source_revision": "UNKNOWN",
            "receipt_ref": "GAP-exam"}


def build_receipt(ctx: dict, synthetic: bool, when: str) -> tuple[dict, list]:
    meta, brief = ctx["audit"].get("meta") or {}, ctx["brief"]
    ident = meta.get("identity") or {}
    g = {c["id"]: c["status"] for c in ctx["gate_rerun"]["checks"] if c["id"] in ("G50", "G11")}
    identity_pass = ident.get("status") == "CONFIRMED" and g.get("G50") == "PASS" and g.get("G11") == "PASS"
    exam = _exam(ctx)
    exam_scope = f"{exam['id']}@{exam['version']}#{exam['source_revision']}" if exam else None
    evidence = _ledger_evidence(ctx) + _run_evidence(ctx, when)
    open_checks = [n for n in CHECK_KINDS if n != "identity"]
    evidence += _gap_evidence(ctx, open_checks, exam_scope, when)
    ids = {e["row"]["id"] for e in evidence}
    if len(ids) != len(evidence):
        raise BundleError("a ledger id collides with a bundle record id (RUN-*, GAP-*); rename the ledger row")
    gaps = _gaps(ctx)

    def check(name, status, evidence_ids):
        return {"name": name, "required": True, "status": status, "evidence_ids": evidence_ids,
                "artifact_sha256": ctx["audit.pdf"]}

    checks = []
    for n in CHECK_KINDS:
        if n == "identity":       # the one check a factory gate performs on the final content
            checks.append(check(n, "PASS", ["RUN-identity"]) if identity_pass
                          else check(n, "FAIL", ["RUN-identity", "RUN-gate-report"]))
        else:
            checks.append(check(n, "UNKNOWN", [f"GAP-{n}"] + [x for x in gaps[n][2] if x in ids]))
    claims, actions = _claims_and_actions(ctx)
    timing, measured_cost = _timing(ctx)
    rv = ctx["review_record"]
    review_id = "RUN-review" if rv else "GAP-reproducibility"
    pdf = ctx["pdf"]
    receipt = {
        "schema_version": "UAQG-TIER-RECEIPT-1.0.0", "standard": "UAQG-1.1.0", "synthetic": synthetic,
        "run_id": ("SYNTHETIC-" if synthetic else "") + f"factory20-{ctx['run'].name}-{ctx['audit.pdf'][:12]}",
        "author_id": f"factory20 pipeline (tier {ctx['tier']})", "audience": "PRIVATE",
        "source_revision": ("synthetic-" if synthetic else "") + f"ledger-sha256:{ctx['ledger.json']}",
        "goal": _or(brief.get("goal"), "UNKNOWN: brief.json records no goal; the audit states one on its goal page"),
        "buyer": _or(brief.get("buyer"), "UNKNOWN: brief.json records no buyer"),
        "offer": _or(brief.get("offer"), "UNKNOWN: brief.json records no offer"),
        "product_profile": {
            "id": "paid-full", "version": "1.0.0", "agreement": "PROPOSED",
            "contract_ref": "UNKNOWN: the run folder records no contract",
            "scope": [t.replace("_", " ") for t in M.PAGE_TYPES],
            "exclusions": ["Not recorded: the run folder holds no agreed exclusions; the ledger's unknown rows are its "
                           "coverage limits"],
            "source_window": f"ledger capture date {ctx['ledger_data'].get('capture_date')}; research cutoff "
                             f"{meta.get('research_cutoff') or 'not recorded'}",
            "required_outputs": [PDF_ID], "contracted_pages": len(M.PAGE_TYPES),
            "blueprint_ref": "audit-factory factory20.model.PAGE_TYPES: the factory's 20-page blueprint"},
        "specialist_exam": exam,
        "allowance": {"state": "UNKNOWN", "limit": None, "consumed": measured_cost, "unit": "USD",
                      "authority_ref": "UNKNOWN: no agreed allowance in the run folder, and the cap the run used is "
                                       "not recorded", "max_iterations": pipeline.MAX_FIX_ROUNDS, "rescope_ref": None},
        "routing": _routing(ctx, synthetic),
        "primary_artifact_id": PDF_ID, "candidate": {"sha256": ctx["audit.pdf"]},
        "artifacts": [
            {"id": PDF_ID, "path": "audit.pdf", "format": "PDF", "sha256": ctx["audit.pdf"], "required": True,
             "page_count": pdf["pages"], "visual_manifest": _visual_manifest(ctx)},
            {"id": JSON_ID, "path": "audit.json", "format": "JSON", "sha256": ctx["audit.json"], "required": False,
             "page_count": None, "visual_manifest": []}],
        "evidence": [e["row"] for e in evidence],
        "claim_scope": "FINDINGS", "no_findings_reason": None, "claims": claims, "actions": actions,
        "checks": checks, "links": [], "defects": _defects(ctx),
        "authority": {"verified": False, "current_holds": [],
                      "record": "UNKNOWN: the run folder holds no authority or hold record; holds were not checked",
                      "owner_function": "UNKNOWN: not recorded in the run folder",
                      "publisher": "UNKNOWN: not recorded in the run folder"},
        "quality": {"weights": [25, 25, 20, 15, 10, 5], "ratings": [None] * 6, "rationales_and_evidence": [None] * 6,
                    "calibration": {"status": "NOT_RUN", "receipt_id": None, "anchor_ids": []}, "total": None},
        "independent_review": {
            "reviewer_id": rv["reviewer"] if rv else None, "fresh_context": bool(rv and rv["fresh"]), "status": "UNKNOWN",
            "artifacts": [{"artifact_id": PDF_ID, "sha256": ctx["audit.pdf"], "coverage": "NONE",
                           "content_privacy": "UNKNOWN", "design": "UNKNOWN",
                           "privacy_receipt_id": "GAP-privacy", "render_receipt_id": "GAP-usability"}],
            "candidate_sha256": ctx["audit.pdf"], "receipt_id": review_id},
        "batch": None, "timing": timing,
        "release": {"attempted": False, "candidate_sha256": None, "observed_harm": False, "readback": []},
        "identity": {"status": {"CONFIRMED": "RESOLVED", "HOLD": "AMBIGUOUS"}.get(ident.get("status"), "UNKNOWN"),
                     "receipt_id": "RUN-identity"},
        "closure_receipts": [],
    }
    if synthetic:
        for row in receipt["evidence"]:
            row["locator"] = SYNTHETIC_LOCATOR + row["locator"]
    return receipt, evidence


# ------------------------------------------------------------------ writing the bundle
def _write_json(path: pathlib.Path, obj) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    return sha256(path)


def _file_name(eid: str, used: set) -> str:
    base = re.sub(r"[^A-Za-z0-9._-]", "_", eid) or "row"
    name, n = base, 1
    while name.lower() in used:
        n += 1
        name = f"{base}-{n}"
    used.add(name.lower())
    return name


def build(run_dir) -> dict:
    """Write the receipt, envelopes, captures and manifest; return a short summary."""
    ctx = load_run(run_dir)
    run = ctx["run"]
    why = synthetic_reasons(ctx)
    when = _now()
    receipt, evidence = build_receipt(ctx, bool(why), when)
    folder = run / FOLDER
    if folder.is_symlink() or (folder.exists() and not folder.is_dir()):
        raise BundleError(f"{folder} is not a plain folder; the bundle owns {FOLDER}/ and will not follow it")
    if folder.exists():
        shutil.rmtree(folder)                          # the bundle's own output, rebuilt from the run each time
    used, bound = set(), []
    for e, row in zip(evidence, receipt["evidence"]):
        name = _file_name(row["id"], used)
        capture = e["capture"]
        if e["data"] is not None:
            capture = f"{FOLDER}/captures/{name}.json"
            _write_json(run / capture, e["data"])
        envelope = {"schema_version": "UAQG-EVIDENCE-SNAPSHOT-1.0.0", "synthetic": receipt["synthetic"],
                    "evidence_id": row["id"], "original_locator": row["locator"],
                    "capture": {"path": capture, "sha256": sha256(run / capture)}}
        rel = f"{FOLDER}/evidence/{name}.json"
        bound.append({"id": row["id"], "path": rel, "sha256": _write_json(run / rel, envelope)})
    receipt["bundle_evidence"] = bound
    manifest = {"schema_version": "UAQG-BUNDLE-1.0.0",
                "receipt": {"path": RECEIPT, "sha256": _write_json(run / RECEIPT, receipt)},
                "artifacts": {a["id"]: {"path": a["path"], "sha256": a["sha256"]} for a in receipt["artifacts"]},
                "evidence": {b["id"]: {"path": b["path"], "sha256": b["sha256"]} for b in bound}}
    _write_json(run / MANIFEST, manifest)
    return _summary(ctx, receipt, why)


def _summary(ctx: dict, receipt: dict, why: list) -> dict:
    checks = {c["name"]: c["status"] for c in receipt["checks"]}
    claims = receipt["claims"]
    no_time = sum(1 for e in receipt["evidence"] if not _tz_aware(e["retrieved_at"]))
    rv = ctx["review_record"]
    review = ("no factory review ran" if rv is None else rv["what"][0].lower() + rv["what"][1:] if not rv["reviewer"]
              else "the factory review never saw the PDF pages and is not hash-bound")
    open_items = [
        "reviewer calibration: NOT_RUN (no calibration record exists)",
        f"independent review: open; {review}",
        "required checks not PASS: " + ", ".join(n for n, s in checks.items() if s != "PASS"),
        "authority, product agreement and allowance: not recorded in the run folder",
        "routing capability evidence and specialist-exam validation: not recorded",
        f"page render review: none recorded ({receipt['artifacts'][0]['page_count']} pages)",
    ]
    if no_time:
        open_items.append(f"evidence rows without a timezone-aware retrieval time: {no_time}")
    inferred = sum(1 for c in claims if c["evidence_state"] == "INFERRED" and not c["limitation"])
    if inferred:
        open_items.append(f"inferred findings that state no limitation or test: {inferred}")
    if receipt["defects"]:
        open_items.append("open defects: " + ", ".join(f"{d['id']} {d['severity']}" for d in receipt["defects"]))
    return {"run": str(ctx["run"]), "receipt": RECEIPT, "manifest": MANIFEST, "synthetic": receipt["synthetic"],
            "synthetic_reasons": why, "artifacts": len(receipt["artifacts"]), "evidence": len(receipt["evidence"]),
            "ledger_rows": sum(1 for e in receipt["evidence"] if e["kind"] == "SOURCE"),
            "skipped_rows": ctx.get("skipped_rows", 0), "claims": len(claims), "actions": len(receipt["actions"]),
            "checks": checks, "actual_cost": receipt["timing"]["actual_cost"]["state"], "open": open_items}
