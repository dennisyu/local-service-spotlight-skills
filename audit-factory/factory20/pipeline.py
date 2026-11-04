"""Drive one audit from ledger to reviewed PDF: identity -> score -> synthesis -> pages ->
actions -> assemble -> gates -> render -> review -> fix. One runner, files in one folder.

run folder layout
    brief.json      subject, goal, prepared_by, palette, date, plan_start (you write this)
    ledger.json     evidence ledger (stage 20 output, or an existing Claude ledger)
    identity.json score.json synthesis.json pages.json actions.json   (stage outputs)
    audit.json gate.json audit.pdf audit.pdf.render.json review.json run.json
"""
from __future__ import annotations

import json
import pathlib

from . import cost as K
from . import gates, model as M, render, router
from .ledger import Ledger


def _ids_missing(obj, ledger: Ledger) -> list[str]:
    return sorted({r for r in M.refs_in(obj) if not ledger.has(r)})


# ------------------------------------------------------------------ stage checks
def check_identity(obj, ledger):
    i = obj.get("identity", obj)
    probs = []
    if i.get("status") not in ("CONFIRMED", "HOLD"):
        probs.append("identity.status must be CONFIRMED or HOLD")
    if i.get("status") == "CONFIRMED" and len([a for a in i.get("attributes", []) if M.refs_in(a)]) < 2:
        probs.append("CONFIRMED needs two attributes, each with evidence ids")
    probs += [f"unknown evidence id {x}" for x in _ids_missing(i, ledger)]
    return probs


def check_score(obj, ledger):
    ba = obj.get("brand_authority", obj)
    probs = []
    if len(ba.get("rows", [])) != 10:
        probs.append(f"brand_authority needs exactly 10 rows, got {len(ba.get('rows', []))}")
    from . import score as S
    probs += [f"row {f['row']}: {f['msg']}" for f in S.calibration_flags(ba, ledger) if f["level"] == "FAIL"]
    probs += [f"unknown evidence id {x}" for x in _ids_missing(ba, ledger)]
    return probs


def check_synthesis(obj, ledger):
    probs = []
    pages = {p.get("n"): p for p in obj.get("pages", [])}
    if 1 not in pages or 2 not in pages:
        return ["synthesis must return pages 1 (cover) and 2 (summary)"]
    probe = {"pages": [pages[1], pages[2]], "meta": {}, "actions": []}
    rep = gates.gate_audit({**probe, "pages": [pages[1], pages[2]]}, ledger)
    keep = {"G20", "G21", "G22", "G30", "G31", "G10", "G11"}
    probs += [f"{c['id']} {c['name']}: {c['msg']}" for c in rep.failures() if c["id"] in keep]
    if not obj.get("next_decision"):
        probs.append("next_decision missing")
    return probs


def check_pages(obj, ledger):
    pages = obj.get("pages", [])
    probs = []
    ns = sorted(p.get("n") for p in pages)
    if ns != list(range(3, 20)):
        probs.append(f"return pages 3-19 exactly; got {ns}")
    for p in pages:
        n = p.get("n")
        if not any(b.get("type") in M.VISUAL_BLOCKS for b in p.get("blocks", [])) and p.get("type") not in ("exams", "agents", "plan"):
            probs.append(f"page {n}: add a visual block")
        if len(M.refs_in(p)) < 3 and p.get("type") != "exams":
            probs.append(f"page {n}: cite at least 3 evidence ids")
        if M.words(p.get("headline", "")) < 5:
            probs.append(f"page {n}: headline must be a sentence-length claim")
        bad = [b.get("type") for b in p.get("blocks", []) if b.get("type") not in M.ALL_BLOCKS]
        if bad:
            probs.append(f"page {n}: unknown block types {bad}")
    probs += [f"unknown evidence id {x}" for x in _ids_missing(pages, ledger)][:15]
    return probs


def check_actions(obj, ledger):
    acts = obj.get("actions", [])
    rep = gates.gate_audit({"pages": [], "meta": {}, "actions": acts}, ledger)
    return [f"{c['id']} {c['name']}: {c['msg']}" for c in rep.failures() if c["id"] in ("G60", "G61", "G62", "G63")]


# ------------------------------------------------------------------ prompts
def prompt(stage: str, run: pathlib.Path, ledger: Ledger, extra: dict | None = None) -> str:
    brief = json.loads((run / "brief.json").read_text()) if (run / "brief.json").exists() else {}
    parts = [f"# BRIEF\n{json.dumps(brief, ensure_ascii=False, indent=1)}",
             f"# EVIDENCE LEDGER (pack)\n{ledger.pack(include_notes=stage in ('identity', 'score', 'synthesis'))}"]
    for name in ("identity", "score", "synthesis", "pages", "actions"):
        f = run / f"{name}.json"
        if f.exists() and name != stage:
            parts.append(f"# {name.upper()} (already decided — stay consistent)\n{f.read_text()}")
    if extra:
        parts.append("# EXTRA\n" + json.dumps(extra, ensure_ascii=False, indent=1))
    parts.append("Answer with JSON only, in the output shape your card defines.")
    return "\n\n".join(parts)


CHECKS = {"identity": check_identity, "score": check_score, "synthesis": check_synthesis,
          "pages": check_pages, "actions": check_actions}


# ------------------------------------------------------------------ assembly
def assemble(run: pathlib.Path) -> dict:
    brief = json.loads((run / "brief.json").read_text())
    ident = json.loads((run / "identity.json").read_text())
    score = json.loads((run / "score.json").read_text())
    syn = json.loads((run / "synthesis.json").read_text())
    pages = json.loads((run / "pages.json").read_text())
    acts = json.loads((run / "actions.json").read_text())
    meta = {**{k: v for k, v in brief.items() if k not in ("goal", "do_not_print")},
            "identity": ident.get("identity", ident), "next_decision": syn.get("next_decision", "")}
    receipt = {"n": 20, "type": "receipt", "kicker": "Method, sources and acceptance receipt",
               "headline": brief.get("receipt_headline", "How this audit was built, what it can and cannot prove, and **the one decision** that moves it"),
               "dek": "Method: Local Service Spotlight 20-page audit; Brand Authority rubric 1.1; evidence ledger with OBSERVED / INFERRED / UNKNOWN states; scores are arithmetic from checked rows; gates run in code before review.",
               "blocks": []}
    all_pages = [p for p in syn["pages"] if p.get("n") in (1, 2)] + pages.get("pages", []) + [receipt]
    exams = {"brand_authority": score.get("brand_authority", score), "separate": score.get("separate", [])}
    audit = {"schema": "lss-audit/1.0", "meta": meta, "exams": exams, "pages": all_pages,
             "actions": acts.get("actions", [])}
    (run / "audit.json").write_text(json.dumps(audit, indent=1, ensure_ascii=False))
    return audit


def run(run_dir: str | pathlib.Path, tier: str = "standard", fake=None, render_pdf: bool = True) -> dict:
    run_dir = pathlib.Path(run_dir)
    cfg = K.load_routing()
    ledger = Ledger.load(run_dir / "ledger.json")
    out = {"tier": tier, "stages": {}}
    for st in ("identity", "score", "synthesis", "pages", "actions"):
        if (run_dir / f"{st}.json").exists():
            out["stages"][st] = "reused"
            continue
        res = router.run_stage(st, prompt(st, run_dir, ledger), tier, run_dir,
                               check=lambda o, s=st: CHECKS[s](o, ledger), cfg=cfg, fake=fake)
        out["stages"][st] = "ok" if res["ok"] else "FAILED"
        if not res["ok"]:
            out["verdict"] = f"HOLD at {st}"
            return out
    audit = assemble(run_dir)
    full = render.expand(audit, ledger)
    dnp = json.loads((run_dir / "brief.json").read_text()).get("do_not_print", [])
    rep = gates.gate_audit(full, ledger, tier if tier in gates.TIERS else "standard", do_not_print=dnp).summary()
    (run_dir / "gate.json").write_text(json.dumps(rep, indent=1))
    out["gate"] = rep["verdict"]
    if render_pdf:
        rr = render.render(run_dir / "audit.json", run_dir / "ledger.json", run_dir / "audit.pdf")
        rr["gates"] = gates.gate_render(rr, audit["meta"].get("install_url", render.INSTALL_URL)).summary()
        (run_dir / "audit.pdf.render.json").write_text(json.dumps(rr, indent=1))
        out["render"] = rr["gates"]["verdict"]
    log = json.loads((run_dir / "run.json").read_text()) if (run_dir / "run.json").exists() else {"attempts": []}
    out["usd"] = round(sum(a.get("usd", 0) for a in log["attempts"]), 4)
    out["verdict"] = "REVIEW_READY" if out["gate"] != "HOLD" and out.get("render", "PASS") != "HOLD" else "HOLD"
    return out
