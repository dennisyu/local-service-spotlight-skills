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
import re

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


def check_pages(obj, ledger, first: int = 3, last: int = 19):
    pages = obj.get("pages", [])
    probs = []
    ns = sorted(p.get("n") for p in pages)
    if ns != list(range(first, last + 1)):
        probs.append(f"return pages {first}-{last} exactly; got {ns}")
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
    head = [f"# BRIEF\n{json.dumps(brief, ensure_ascii=False, indent=1)}",
            f"# EVIDENCE LEDGER (pack)\n{ledger.pack(include_notes=stage in ('identity', 'score', 'synthesis'))}"]
    decided = [f"# {name.upper()} (already decided — stay consistent)\n{(run / f'{name}.json').read_text()}"
               for name in ("identity", "score", "synthesis", "pages", "actions")
               if (run / f"{name}.json").exists() and name != stage]
    tail = (["# EXTRA\n" + json.dumps(extra, ensure_ascii=False, indent=1)] if extra else [])
    tail.append("Answer with JSON only, in the output shape your card defines.")
    # Stable prefix first (brief + ledger, then the stage files already decided), the part
    # that changes from call to call last, so repeated calls can reuse a cached prefix.
    return router.CACHE_MARK.join(["\n\n".join(head)] + (["\n\n".join(decided)] if decided else []) + ["\n\n".join(tail)])


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


def check_review(obj, ledger):
    probs = []
    if obj.get("verdict") not in ("READY", "READY_WITH_FIXES", "NOT_READY"):
        probs.append("verdict must be READY, READY_WITH_FIXES or NOT_READY")
    for f in obj.get("findings", []):
        if f.get("severity") not in ("S0", "S1", "S2", "S3"):
            probs.append(f"finding {f.get('id')}: severity must be S0, S1, S2 or S3")
    if obj.get("verdict") == "READY" and _serious(obj):
        probs.append("READY needs zero S0/S1 findings")
    return probs


def check_fix(obj, ledger):
    """A fix returns only the pages it changed, each a full page object for pages 3-19."""
    pages = obj.get("pages", [])
    if not pages:
        return ["return the pages you changed under 'pages' (at least one)"]
    bad = [p.get("n") for p in pages if p.get("n") not in range(3, 20)]
    probs = [f"fix may only return pages 3-19; got {bad}"] if bad else []
    probs += [f"unknown evidence id {x}" for x in _ids_missing(pages, ledger)][:15]
    return probs


CHECKS = {"identity": check_identity, "score": check_score, "synthesis": check_synthesis,
          "pages": check_pages, "actions": check_actions}
MAX_FIX_ROUNDS = 3
FRONT_GATES = {"G20", "G21", "G22", "G24"}
# Not the writer's to fix: the preparer's photo comes from the brief and assets (G81), and a
# private field inside a screenshot needs the image cropped or redacted, which no drafting
# model can do (G75). A G75 FAIL holds the audit until the runner fixes the image file.
NOT_THE_WRITERS = {"G81", "G75"}
# Pages 3-19 come back in four calls, not one. A real audit's pages run about 19,000 output
# tokens (measured on the Nov 4 clean blind run), more than one reply may carry; four
# batches share the same cached prefix, so the split costs little and nothing is cut off.
PAGE_BATCHES = [(3, 6), (7, 10), (11, 14), (15, 19)]


def run_pages(run_dir: pathlib.Path, ledger: Ledger, tier: str, cfg: dict, fake=None,
              confidential: bool = False, max_usd: float | None = None) -> dict:
    """Write pages 3-19 batch by batch; each batch sees the layouts already chosen."""
    done: list[dict] = []
    for first, last in PAGE_BATCHES:
        layout = [{"n": p.get("n"), "type": p.get("type"), "blocks": [b.get("type") for b in p.get("blocks", [])]}
                  for p in done]
        res = router.run_stage("pages", prompt("pages", run_dir, ledger, extra={
            "task": f"Write pages {first}-{last} only, as {{\"pages\": [...]}}. The other pages are written in "
                    "separate calls; keep the page plan's order and vary layouts against pages_so_far.",
            "pages_so_far": layout}), tier, run_dir,
            check=lambda o, a=first, b=last: check_pages(o, ledger, a, b), cfg=cfg, fake=fake,
            confidential=confidential, max_usd=max_usd, write=False)
        if not res["ok"]:
            return {"ok": False, "batch": f"{first}-{last}"}
        done += sorted(res["obj"].get("pages", []), key=lambda p: p.get("n"))
    (run_dir / "pages.json").write_text(json.dumps({"pages": done}, indent=1, ensure_ascii=False))
    return {"ok": True}


def _serious(review: dict | None) -> list[dict]:
    return [f for f in (review or {}).get("findings", []) if f.get("severity") in ("S0", "S1")]


def fix_list(gate_rep: dict, render_rep: dict | None = None, review: dict | None = None) -> list[dict]:
    """Every open item, in the words a drafting model can act on."""
    items = [{"from": "gate", "id": c["id"], "status": c["status"], "msg": c["msg"]}
             for c in gate_rep.get("checks", []) if c["status"] != "PASS" and c["id"] not in NOT_THE_WRITERS]
    if render_rep:
        items += [{"from": "render", "id": c["id"], "status": c["status"], "msg": c["msg"]}
                  for c in render_rep.get("gates", {}).get("checks", [])
                  if c["status"] != "PASS" and not c["msg"].startswith("QR not checked")]
    if review:
        items += [{"from": "review", "id": f.get("id"), "status": "FAIL" if f.get("severity") in ("S0", "S1") else "WARN",
                   "page": f.get("page"), "msg": f"{f.get('problem', '')} Fix: {f.get('fix', '')}"}
                  for f in review.get("findings", []) if f.get("severity") in ("S0", "S1", "S2")]
    return items


def _front(item: dict) -> bool:
    if item.get("id") in FRONT_GATES or item.get("page") in (1, 2):
        return True
    return bool(re.search(r"\bpages? \[?([12])\b|\bpage 2\b|\bp[12]:", item.get("msg") or ""))


def _apply_fixes(run_dir: pathlib.Path, ledger: Ledger, tier: str, cfg: dict, fake, items: list[dict],
                 review: dict | None = None, confidential: bool = False, max_usd: float | None = None) -> bool:
    """One fix round: the synthesis model revises pages 1-2, the fix model patches pages 3-19,
    and reviewer score adjustments go back into score.json (code re-checks them). A fix round
    obeys the same confidential guard and spending cap as the first draft."""
    ok = True
    front = [i for i in items if _front(i)]
    rest = [i for i in items if not _front(i)]
    if front:
        res = router.run_stage("synthesis", prompt("synthesis", run_dir, ledger, extra={
            "task": "Revise synthesis.json so every item in fix_list is cleared; keep what already works.",
            "fix_list": front, "current_synthesis": json.loads((run_dir / "synthesis.json").read_text())}),
            tier, run_dir, check=lambda o: check_synthesis(o, ledger), cfg=cfg, fake=fake,
            confidential=confidential, max_usd=max_usd)
        ok &= res["ok"]
    if rest:
        res = router.run_stage("fix", prompt("fix", run_dir, ledger, extra={
            "task": "Clear every item in fix_list. Return ONLY the pages you changed, each as a full page "
                    "object (pages 3-19), under 'pages'. Never shrink type: cut words or move a block.",
            "fix_list": rest}), tier, run_dir, check=lambda o: check_fix(o, ledger), cfg=cfg, fake=fake,
            confidential=confidential, max_usd=max_usd)
        if res["ok"]:
            cur = json.loads((run_dir / "pages.json").read_text())
            by_n = {p.get("n"): p for p in cur.get("pages", [])}
            by_n.update({p.get("n"): p for p in res["obj"].get("pages", [])})
            cur["pages"] = [by_n[n] for n in sorted(by_n)]
            (run_dir / "pages.json").write_text(json.dumps(cur, indent=1, ensure_ascii=False))
        ok &= res["ok"]
    if review and review.get("score_adjustments"):
        sc = json.loads((run_dir / "score.json").read_text())
        ba = sc.get("brand_authority", sc)
        for adj in review["score_adjustments"]:
            for row in ba.get("rows", []):
                if row.get("n") == adj.get("row") and adj.get("to") is not None:
                    row["score"] = adj["to"]
                    row["why"] = f"{row.get('why', '')} (review: {adj.get('why', '')})".strip()
        (run_dir / "score.json").write_text(json.dumps(sc, indent=1, ensure_ascii=False))
    return ok


def review_prompt(run_dir: pathlib.Path, ledger: Ledger, gate_rep: dict, render_rep: dict | None) -> str:
    """Fresh context: the reviewer sees the exact final files, never the drafting history."""
    brief = json.loads((run_dir / "brief.json").read_text())
    brief.pop("do_not_print", None)
    head = [f"# BRIEF\n{json.dumps(brief, ensure_ascii=False, indent=1)}",
            f"# EVIDENCE LEDGER (pack)\n{ledger.pack(include_notes=True)}"]
    final = [f"# FINAL audit.json\n{(run_dir / 'audit.json').read_text()}",
             f"# gate.json\n{json.dumps(gate_rep, indent=1)}"]
    if render_rep:
        final.append(f"# render report\n{json.dumps({k: v for k, v in render_rep.items() if k != 'html'}, indent=1)}")
    return router.CACHE_MARK.join(["\n\n".join(head), "\n\n".join(final),
                                   "Answer with JSON only, in the output shape your card defines."])


def _check_all(run_dir: pathlib.Path, ledger: Ledger, tier: str, render_pdf: bool):
    audit = assemble(run_dir)
    full = render.expand(audit, ledger)
    brief = json.loads((run_dir / "brief.json").read_text())
    rep = gates.gate_audit(full, ledger, tier if tier in gates.TIERS else "standard",
                           do_not_print=brief.get("do_not_print", []),
                           allowed_phones=brief.get("allowed_phones", []), asset_base=run_dir).summary()
    (run_dir / "gate.json").write_text(json.dumps(rep, indent=1))
    rr = None
    if render_pdf:
        rr = render.render(run_dir / "audit.json", run_dir / "ledger.json", run_dir / "audit.pdf")
        rr["gates"] = gates.gate_render(rr, audit["meta"].get("install_url", render.INSTALL_URL)).summary()
        (run_dir / "audit.pdf.render.json").write_text(json.dumps(rr, indent=1))
    return audit, rep, rr


def run(run_dir: str | pathlib.Path, tier: str = "standard", fake=None, render_pdf: bool = True,
        review: bool = True, max_usd: float | None = None) -> dict:
    """Stages 30-70 (reusing any stage file already present), then: assemble -> gates -> render ->
    up to three fix rounds -> one fresh-context review -> fix and re-review if it found S0/S1.

    max_usd caps what the run may spend (default: the tier's max_usd). Reaching it, or a
    provider refusing the key or the credits, ends the run as HOLD with the reason, never
    as a half-finished audit that looks done."""
    run_dir = pathlib.Path(run_dir)
    cfg = K.load_routing()
    if tier not in cfg["tiers"]:
        raise ValueError(f"unknown tier {tier!r}; choose one of {sorted(cfg['tiers'])}")
    if max_usd is None:
        max_usd = cfg["tiers"][tier].get("max_usd")
    out = {"tier": tier, "stages": {}, "max_usd": max_usd}
    if cfg["tiers"][tier].get("experimental"):
        out["warning"] = "experimental tier: its quality is not measured yet; review every page before it is shared"
    try:
        return _run(run_dir, tier, cfg, fake, render_pdf, review, max_usd, out)
    except (router.BudgetExceeded, router.ProviderError) as e:
        out["verdict"] = "HOLD"
        out["hold_reason"] = str(e)
        out["usd"] = router.spent(run_dir)
        return out


def _run(run_dir: pathlib.Path, tier: str, cfg: dict, fake, render_pdf: bool, review: bool,
         max_usd: float | None, out: dict) -> dict:
    ledger = Ledger.load(run_dir / "ledger.json")
    brief = json.loads((run_dir / "brief.json").read_text())
    confidential = bool(brief.get("do_not_print"))
    for st in ("identity", "score", "synthesis", "pages", "actions"):
        if (run_dir / f"{st}.json").exists():
            out["stages"][st] = "reused"
            continue
        if st == "pages":
            res = run_pages(run_dir, ledger, tier, cfg, fake, confidential, max_usd)
        else:
            res = router.run_stage(st, prompt(st, run_dir, ledger), tier, run_dir,
                                   check=lambda o, s=st: CHECKS[s](o, ledger), cfg=cfg, fake=fake,
                                   confidential=confidential, max_usd=max_usd)
        out["stages"][st] = "ok" if res["ok"] else "FAILED"
        if not res["ok"]:
            out["verdict"] = f"HOLD at {st}" + (f" (pages {res['batch']})" if res.get("batch") else "")
            out["usd"] = router.spent(run_dir)
            return out
    audit, rep, rr = _check_all(run_dir, ledger, tier, render_pdf)
    rounds = 0
    while fix_list(rep, rr) and rounds < MAX_FIX_ROUNDS:
        rounds += 1
        if not _apply_fixes(run_dir, ledger, tier, cfg, fake, fix_list(rep, rr),
                            confidential=confidential, max_usd=max_usd):
            break
        audit, rep, rr = _check_all(run_dir, ledger, tier, render_pdf)
    out["fix_rounds"] = rounds
    out["gate"] = rep["verdict"]
    if rr:
        out["render"] = rr["gates"]["verdict"]
    gates_ok = rep["verdict"] != "HOLD" and (rr is None or rr["gates"]["verdict"] != "HOLD")
    rv = None
    if review and gates_ok:
        passes = cfg["tiers"].get(tier, {}).get("review_passes", 1)
        for p in range(1, passes + 1):
            res = router.run_stage("review", review_prompt(run_dir, ledger, rep, rr), tier, run_dir,
                                   check=lambda o: check_review(o, ledger), cfg=cfg, fake=fake,
                                   confidential=confidential, max_usd=max_usd)
            if not res["ok"]:
                out["verdict"] = "HOLD at review"
                out["usd"] = router.spent(run_dir)
                return out
            rv = res["obj"]
            out["review_passes"] = p
            if not _serious(rv) or p == passes:
                break
            _apply_fixes(run_dir, ledger, tier, cfg, fake, fix_list(rep, rr, rv), review=rv,
                         confidential=confidential, max_usd=max_usd)
            audit, rep, rr = _check_all(run_dir, ledger, tier, render_pdf)
            gates_ok = rep["verdict"] != "HOLD" and (rr is None or rr["gates"]["verdict"] != "HOLD")
        out["review"] = rv.get("verdict") if rv else None
        out["gate"] = rep["verdict"]
    log = json.loads((run_dir / "run.json").read_text()) if (run_dir / "run.json").exists() else {"attempts": []}
    out["usd"] = round(sum(a.get("usd", 0) for a in log["attempts"]), 4)
    if not gates_ok:
        out["verdict"] = "HOLD"
        # name what holds it, so a hold no writer can clear (a private field in a screenshot,
        # the preparer's photo) is visible without opening gate.json
        out["holding_gates"] = sorted({c["id"] for c in rep["checks"] if c["status"] == "FAIL"}
                                      | {c["id"] for c in ((rr or {}).get("gates") or {}).get("checks", [])
                                         if c["status"] == "FAIL"})
    elif not review:
        out["verdict"] = "REVIEW_READY"
    else:
        out["verdict"] = "READY" if rv and not _serious(rv) else "HOLD"
    return out
