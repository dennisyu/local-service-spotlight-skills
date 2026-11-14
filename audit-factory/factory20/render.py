"""audit.json + ledger -> 20-page HTML -> PDF, with the measurements the gates need.

Design system: Inter / Inter Display, one accent colour, three evidence states that read
without colour (labelled badges, hatching for UNKNOWN), an evidence footer on every page
whose ids are clickable links to the ledger source. Pages are fixed-size boxes; the
renderer measures overflow and fill so a cheap model gets told exactly which page to fix.

Code-owned content (never typed by a model): the Brand Authority total and heatmap, the
separate-exam strip, the 30/60/90 swimlane built from the action register, the agents QR,
and the page-20 working receipt (evidence by class, checks, coverage crosswalk, companions).
"""
from __future__ import annotations

import copy
import datetime as _dt
import html
import json
import pathlib
import re
import subprocess
import tempfile

from . import components as C
from . import model as M
from . import score as S
from .ledger import Ledger

E = html.escape
DEFAULT_PALETTE = {"ink": "#111318", "paper": "#ffffff", "accent": "#E8B10A", "dark": "#0d0f14",
                   "muted": "#5b616e", "rule": "#e3e5ea"}
INSTALL_URL = "https://localservicespotlight.com/install/"


class Ctx:
    def __init__(self, audit: dict, ledger: Ledger | None, base: pathlib.Path):
        self.audit, self.ledger, self.base = audit, ledger, base
        self.meta = audit.get("meta", {})
        self.subject = self.meta.get("subject", "")
        self.missing_assets: list[str] = []
        self.gate_summary: dict | None = None

    def asset_path(self, src: str) -> pathlib.Path | None:
        if not src or src.startswith(("http://", "https://", "data:")):
            return None
        p = (self.base / src).resolve()
        return p if p.exists() else None

    def asset_ok(self, src: str) -> bool:
        return bool(src) and (src.startswith("data:") or self.asset_path(src) is not None)

    def asset_url(self, src: str) -> str:
        if src.startswith("data:"):
            return src
        p = self.asset_path(src)
        return p.as_uri() if p else src

    def exam(self) -> dict | None:
        return (self.audit.get("exams") or {}).get("brand_authority")

    def exam_rows(self) -> list[dict]:
        ex = self.exam() or {}
        rows = ex.get("rows", [])
        for k, r in enumerate(rows):
            r.setdefault("name", S.ROWS[k] if k < len(S.ROWS) else f"Row {k + 1}")
        return rows

    def exam_result(self) -> dict | None:
        ex = self.exam()
        if not ex:
            return None
        return S.compute(ex, (self.meta.get("identity") or {}).get("status", "UNKNOWN"))

    def separate_exams(self) -> list[dict]:
        return (self.audit.get("exams") or {}).get("separate", [])

    def plan_items(self) -> list[dict]:
        start = self.meta.get("plan_start") or self.meta.get("date") or str(_dt.date.today())
        try:
            d0 = _dt.date.fromisoformat(start[:10])
        except ValueError:
            d0 = _dt.date.today()
        out = []
        for a in self.audit.get("actions", []):
            try:
                due = (_dt.date.fromisoformat(str(a.get("due"))[:10]) - d0).days
            except ValueError:
                due = int(a.get("window") or 30)
            win = int(a.get("window") or (7 if due <= 7 else 30 if due <= 30 else 60 if due <= 60 else 90))
            startd = {7: 0, 30: 7, 60: 30, 90: 60}.get(win, 0)
            lane = (a.get("function") or "Owner").split("(")[0].strip()[:22]
            out.append({"id": a.get("id"), "lane": lane, "start": startd, "end": max(due, startd + 4),
                        "executor": a.get("executor", ""), "due": max(due, 0)})
        return out


# ------------------------------------------------------------------ expansion
def expand(audit: dict, ledger: Ledger | None) -> dict:
    """Inject code-owned blocks so gates and renderer see the same final pages."""
    a = copy.deepcopy(audit)
    meta = a.setdefault("meta", {})
    install = meta.setdefault("install_url", INSTALL_URL)
    for p in a.get("pages", []):
        t = p.get("type")
        types = {b.get("type") for b in p.get("blocks", [])}
        if t == "exams" and a.get("exams", {}).get("brand_authority"):
            if "heatmap" not in types:
                p.setdefault("blocks", []).insert(0, {"type": "heatmap", "auto": True, "span": 12,
                                                      "title": "Brand Authority — ten rows, each scored only after it was checked"})
            if "scorebar" not in types and a.get("exams", {}).get("separate"):
                p["blocks"].insert(1, {"type": "scorebar", "span": 12})
            ex = a["exams"]["brand_authority"]
            p.setdefault("evidence", [])
            for r in ex.get("rows", []):
                for e in r.get("evidence") or []:
                    if e not in p["evidence"]:
                        p["evidence"].append(e)
        if t == "plan" and "swimlane" not in types and a.get("actions"):
            p.setdefault("blocks", []).insert(0, {"type": "swimlane", "auto": True, "span": 12,
                                                  "title": "Who does what, when — every bar is an action in the register"})
        if t == "agents" and "qr" not in types:
            p.setdefault("blocks", []).append({"type": "qr", "url": install, "span": 3,
                                               "caption": "Scan to install the agents this plan routes work to."})
        if t == "receipt":
            p.setdefault("blocks", []).extend(_receipt_blocks(a, ledger))
    return a


def chromium_candidates() -> list[str]:
    """Chromium binaries to try when Playwright's bundled build is missing.

    Order: $FACTORY20_CHROMIUM, then any pre-installed Playwright Chromium under
    $PLAYWRIGHT_BROWSERS_PATH or /opt/pw-browsers (cloud sessions ship one whose
    revision can differ from the installed Python package).
    """
    import glob
    import os
    out = []
    env = os.environ.get("FACTORY20_CHROMIUM")
    if env:
        out.append(env)
    roots = [os.environ.get("PLAYWRIGHT_BROWSERS_PATH") or "", "/opt/pw-browsers"]
    for root in roots:
        if root:
            out += sorted(glob.glob(os.path.join(root, "chromium-*", "chrome-linux*", "chrome")), reverse=True)
    return [p for p in dict.fromkeys(out) if os.path.exists(p)]


def launch_chromium(pw):
    """Launch Playwright's Chromium; fall back to a known binary when the bundled one is absent."""
    try:
        return pw.chromium.launch()
    except Exception as first:  # noqa: BLE001 - Playwright raises a generic Error for a missing browser
        for path in chromium_candidates():
            try:
                return pw.chromium.launch(executable_path=path)
            except Exception:  # noqa: BLE001
                continue
        raise first


def _receipt_blocks(a: dict, ledger: Ledger | None) -> list[dict]:
    blocks = []
    if ledger:
        st = ledger.stats()
        short = {"INDEPENDENTLY-CORROBORATED": "independent", "FIRM-UNATTRIBUTED": "firm, unattributed"}
        items = [{"label": short.get(k, k.replace("-", " ").lower()), "value": v} for k, v in
                 sorted(st["by_class"].items(), key=lambda x: -x[1])]
        blocks.append({"type": "bars", "span": 6, "title": f"Evidence ledger — {st['evidence']} rows by class",
                       "items": items,
                       "caption": f"Kept beside the ledger, not counted in the {st['evidence']}: {st['ambiguous']} namesake rows, "
                                  f"{st['conflicts']} conflict groups, {st['unknowns']} named unknowns."})
        # five most-cited facts: what a stranger should check first
        counts: dict[str, int] = {}
        for p in a.get("pages", []):
            for r in M.refs_in(p):
                counts[r] = counts.get(r, 0) + 1
        top = [r for r, _ in sorted(counts.items(), key=lambda x: -x[1]) if ledger.get(r)
               and ledger.get(r)["kind"] == "evidence"][:5]
        rows = [[r, ledger.get(r)["claim"][:70], ledger.get(r)["source"][:40], ledger.get(r)["state"]] for r in top]
        blocks.append({"type": "table", "span": 6, "title": "The five facts this audit leans on most — check these first",
                       "columns": ["Evidence", "Claim", "Source", "State"], "rows": rows, "evidence": top})
    cover = {t: [] for t in M.PAGE_TYPES}
    for p in a.get("pages", []):
        for t in [p.get("type")] + list(p.get("covers") or []):
            if t in cover:
                cover[t].append(str(p.get("n")))
    shown = {"lighthouse": "partners"}
    xw = [[str(i + 1), shown.get(t, t.replace("_", " ")), ", ".join(cover[t]) or "MISSING"] for i, t in enumerate(M.PAGE_TYPES)]
    blocks.append({"type": "table", "span": 6, "title": "Coverage crosswalk — default blueprint page → this PDF",
                   "columns": ["Default", "Requirement", "This PDF"], "rows": xw, "compact": True})
    files = a.get("meta", {}).get("companions") or ["evidence ledger (JSON/CSV)", "action register (CSV + Basecamp to-dos)",
                                                     "gate report (JSON)", "render report (JSON)", "run record (stages, models, cost)"]
    blocks.append({"type": "checklist", "span": 6, "title": "Companion files", "items": [{"label": f, "state": "PASS"} for f in files]})
    nd = a.get("meta", {}).get("next_decision")
    if nd:
        blocks.append({"type": "callout", "tone": "decision", "span": 12, "title": "Next decision", "body": nd})
    return blocks


# ------------------------------------------------------------------ html
CSS = r"""
@page { size: 8.5in 11in; margin: 0 }
* { box-sizing: border-box }
html, body { margin: 0; padding: 0; background: #888 }
body { font-family: Inter, "Helvetica Neue", Arial, sans-serif; color: var(--ink); -webkit-print-color-adjust: exact; print-color-adjust: exact }
.page { width: 8.5in; height: 11in; background: var(--paper); padding: 0.38in 0.44in 0.30in; display: flex; flex-direction: column;
  overflow: hidden; position: relative; page-break-after: always; break-after: page }
.top { display: flex; justify-content: space-between; align-items: baseline; border-bottom: 2px solid var(--ink); padding-bottom: 4px; margin-bottom: 8px }
.kick { font: 800 9.2px/1 Inter; letter-spacing: .16em; text-transform: uppercase; color: var(--ink) }
.kick b { background: var(--accent); color: #111; padding: 2px 5px; margin-right: 6px; letter-spacing: .04em }
.tmeta { font: 600 8px/1 Inter; letter-spacing: .12em; text-transform: uppercase; color: var(--muted) }
h1.hl { font: 800 26.5px/1.08 "Inter Display", Inter, sans-serif; letter-spacing: -.012em; margin: 2px 0 5px }
.acc { color: var(--accent-ink) }
.dek { font: 400 11.6px/1.42 Inter; color: #2c313a; margin: 0 0 10px; max-width: 97% }
.body { flex: 1; display: grid; grid-template-columns: repeat(12, 1fr); gap: 11px 14px; align-content: start; overflow: hidden; min-height: 0 }
.foot { border-top: 1px solid var(--rule); padding-top: 4px; margin-top: 6px; display: grid; grid-template-columns: auto 1fr auto; gap: 10px; align-items: start;
  font: 500 6.9px/1.35 Inter; color: var(--muted) }
.foot .evf .ev { font-size: 6.4px; padding: 0 2px; margin: 0 1px 1px 0 }
.pn { font-weight: 800; color: var(--ink) }
.blk { min-width: 0; font-size: 10.3px; line-height: 1.42 }
.btitle { font: 800 8.6px/1.25 Inter; letter-spacing: .1em; text-transform: uppercase; color: var(--muted); margin: 0 0 4px }
.prose p { margin: 0 0 6px; font-size: 10.6px; line-height: 1.5 }
.mut { color: var(--muted) }
.chips { display: inline }
.ev, .act { display: inline-block; font: 600 7.5px/1.35 "DejaVu Sans Mono", monospace; padding: 0 3px; margin: 1px 2px 0 0; border: 1px solid #c9ccd3; border-radius: 3px; color: #343a46; text-decoration: none; background: #fafafa }
a.ev { color: #1d4ed8; border-color: #b8c6ef; background: #f3f6fe }
.act { background: var(--accent); border-color: var(--accent); color: #111 }
.badge { display: inline-block; font: 800 6.8px/1 Inter; letter-spacing: .08em; padding: 3px 5px; border-radius: 3px }
.b-obs { background: var(--obs); color: #fff } .b-inf { background: #fff; color: var(--inf); border: 1.2px solid var(--inf) }
.b-unk { color: #374151; background: repeating-linear-gradient(45deg,#e5e7eb 0 3px,#f9fafb 3px 6px); border: 1px solid #9ca3af }
.cgrid { display: grid; gap: 9px }
.card { border: 1px solid var(--rule); border-top: 3px solid var(--ink); padding: 8px 10px 8px; background: #fff; display: flex; flex-direction: column; gap: 3px }
.chead { display: flex; justify-content: space-between; align-items: center }
.cnum { font: 800 15px/1 "Inter Display"; color: #d1d5db }
.ctitle { font: 800 12.4px/1.22 "Inter Display", Inter; letter-spacing: -.005em }
.cbody { font-size: 9.9px; line-height: 1.45; color: #222 }
.so { font-size: 9.9px; line-height: 1.42; border-left: 3px solid var(--accent); padding-left: 5px; background: #fffbea }
.cfoot { margin-top: auto }
.pair { margin: 2px 0 } .pr { display: grid; grid-template-columns: 34% 1fr auto; gap: 5px; align-items: center; font-size: 8.6px }
.pb { height: 9px; background: var(--ink); display: block; border-radius: 1px } .pb.alt { background: var(--accent) } .pv { font-weight: 800; font-size: 8px }
.doors { display: flex; gap: 4px; flex-wrap: wrap } .door { font: 700 8.2px Inter; padding: 3px 6px; border-radius: 3px; border: 1px solid }
.door.ok { color: var(--obs); border-color: var(--obs) } .door.no { color: #b91c1c; border-color: #b91c1c } .door.warn { color: #92400e; border-color: #d97706; background: #fffbeb }
.sgrid { display: grid; gap: 6px }
.stat { border: 1px solid var(--rule); padding: 6px 8px; border-left: 4px solid var(--accent) }
.sv { font: 800 25px/1 "Inter Display"; letter-spacing: -.02em } .sl { font: 700 9.4px/1.28 Inter; margin-top: 4px } .ss { font-size: 8.4px; color: var(--muted); margin-top: 2px }
.fmap ol { list-style: none; margin: 0; padding: 0; display: grid; gap: 5px }
.fmap li { display: grid; grid-template-columns: 18px 1fr; gap: 6px }
.fn { font: 800 12px/1 "Inter Display"; color: #111; background: var(--accent); text-align: center; border-radius: 2px; height: 16px; padding-top: 2px }
.ft { font: 800 10.6px/1.28 Inter } .fp { font-size: 9.2px; line-height: 1.35; color: #3b4150 }
table { width: 100%; border-collapse: collapse; font-size: 9.1px; line-height: 1.36 }
th { text-align: left; background: var(--ink); color: #fff; font: 700 8.2px/1.25 Inter; letter-spacing: .04em; padding: 4px 5px }
td { border-bottom: 1px solid var(--rule); padding: 4px 6px; vertical-align: top }
.cap { font-size: 8.4px; color: var(--muted); margin-top: 3px; line-height: 1.35 }
.callout { border-left: 4px solid var(--ink); background: #f5f6f8; padding: 6px 9px; align-self: start }
.callout.t-decision { border-color: var(--accent); background: #111318; color: #fff } .callout.t-decision .ctl { color: var(--accent) }
.callout.t-warn { border-color: #b91c1c; background: #fef2f2 } .callout.t-info { border-color: #1d4ed8; background: #f3f6fe }
.ctl { font: 800 10.6px/1.28 Inter; margin-bottom: 3px } .cbd { font-size: 10px; line-height: 1.45 }
.quote .q { font: 600 14px/1.38 "Inter Display"; } .quote .qa { font-size: 8px; color: var(--muted); margin-top: 3px }
.checklist .ck { display: grid; grid-template-columns: 58px 1fr; gap: 7px; font-size: 9.2px; padding: 2px 0; border-bottom: 1px solid var(--rule) }
.cks { font: 800 6.8px/1.6 Inter; text-align: center; border-radius: 3px; color: #fff; background: #6b7280; align-self: start; margin-top: 1px }
.cks.s-pass { background: var(--obs) } .cks.s-fail { background: #b91c1c } .cks.s-warn, .cks.s-partial { background: var(--inf) }
.conflicts .cf { border: 1px solid var(--rule); padding: 5px 7px; margin-bottom: 5px } .cm { font: 800 9px Inter } .cv { font-size: 8.2px } .cr { font-size: 8.2px; margin-top: 2px }
figure.photo { margin: 0 } .frame { width: 100%; overflow: hidden; border-radius: 3px; background: #eef0f3 }
.frame img { width: 100%; height: 100%; object-fit: cover; display: block }
.noimg { height: 100%; display: flex; flex-direction: column; align-items: center; justify-content: center; font: 800 9px Inter; color: #b91c1c; border: 2px dashed #b91c1c; text-align: center }
.noimg span { font-weight: 500; font-size: 7.5px; color: #555 }
svg.viz { display: block; width: 100%; height: auto }
svg .tl { font: 600 9.6px Inter; fill: #2b303a } svg .tl2 { font: 500 9px Inter; fill: #2b303a } svg .tl2b { font: 600 9.4px Inter; fill: #1f232b } svg .tv { font: 800 10px Inter; fill: #111 } svg .tvb { font: 800 11px Inter; fill: #111 }
svg .tu { font: 700 8.6px Inter; fill: #374151 } svg .tid { font: 600 7.6px "DejaVu Sans Mono"; fill: #6b7280 } svg .td { font: 800 8.4px Inter; fill: #5b616e }
svg .bar { fill: var(--ink) } svg .bar.alt { fill: var(--accent) } svg .bar.ro { fill: #fff; stroke: var(--ink); stroke-width: 1.2 } svg .hatch { fill: url(#hatch); stroke: #9ca3af; stroke-width: .6 }
svg .hc { fill: #eceef2 } svg .hc.on { fill: var(--accent) }
svg .axis { stroke: var(--ink); stroke-width: 1.6 } svg .grid { stroke: #d7dae0; stroke-width: 1; stroke-dasharray: 2 3 }
svg .dot.n-obs { fill: var(--obs) } svg .dot.n-inf { fill: var(--inf) } svg .dot.n-unk { fill: #9ca3af } svg .ring { fill: #fff; stroke: var(--accent); stroke-width: 2.4 }
svg .gap { stroke: var(--accent); stroke-width: 3; stroke-dasharray: 3 2 }
svg .edge { stroke: #6b7280; stroke-width: 1.2 } svg .edge.conflict { stroke: #b91c1c } svg .edge.proposed { stroke: var(--accent); stroke-width: 1.6 }
svg .el { font: 700 7.6px Inter; fill: #4b5260 } svg .elbg { fill: #fff; opacity: .9 } svg .laneband { fill: #f6f7f9 }
svg .node { stroke-width: 1.2 } svg .node.n-obs { fill: #fff; stroke: var(--obs) } svg .node.n-inf { fill: #fffaf0; stroke: var(--inf); stroke-dasharray: 3 2 }
svg .node.n-unk { fill: #f3f4f6; stroke: #9ca3af; stroke-dasharray: 2 2 } svg .node.center { fill: var(--ink); stroke: var(--ink) }
svg .nl { font: 700 9px Inter; fill: #111 } svg .nl.cl { fill: #fff; font-size: 10.6px } svg .ns { font: 500 7.6px Inter; fill: #5b616e }
svg .mx { fill: #fafafa; stroke: #d7dae0 } svg .ql { font: 800 8.6px Inter; fill: #9ca3af; letter-spacing: .06em }
svg .sl2 { font: 800 7.6px "DejaVu Sans Mono"; fill: #fff } svg .sl2.dk { fill: #111 } svg .seg { stroke: #fff; stroke-width: 1.5 }
svg .s0 { fill: var(--ink) } svg .s1 { fill: var(--accent) } svg .s2 { fill: #0f6b5c } svg .s3 { fill: #b45309 } svg .s4 { fill: #1d4ed8 } svg .s5 { fill: #9ca3af }
.legend { display: flex; gap: 10px; flex-wrap: wrap; font: 600 7.8px Inter; color: #5b616e; margin-top: 2px }
.lg::before { content: ""; display: inline-block; width: 8px; height: 8px; margin-right: 3px; vertical-align: -1px; border-radius: 2px; background: #ccc }
.lg.obs::before { background: var(--obs) } .lg.inf::before { background: var(--inf) } .lg.unk::before { background: #9ca3af } .lg.ring::before { background: #fff; border: 2px solid var(--accent); border-radius: 50% } .lg.ln::before { display: none }
.hmwrap { display: grid; grid-template-columns: 1fr 140px; gap: 10px; align-items: center }
.examtot { border: 2px solid var(--ink); padding: 10px; text-align: center } .et-v { font: 800 38px/1 "Inter Display" } .et-v span { font-size: 12px; color: var(--muted) }
.et-s { font: 800 8.6px/1.3 Inter; margin-top: 4px; text-transform: uppercase; letter-spacing: .06em } .et-p { font-size: 7.8px; color: var(--muted); margin-top: 3px }
.sxg { display: grid; grid-template-columns: repeat(4, 1fr); gap: 6px } .sx { border: 1px solid var(--rule); padding: 5px 7px }
.sxn { font: 800 8.4px Inter; text-transform: uppercase; letter-spacing: .06em; color: var(--muted) } .sxv { font: 800 17px/1.1 "Inter Display"; margin: 3px 0 } .sxd { font-size: 8.6px }
.frow { display: flex; align-items: stretch; gap: 4px } .fstep { flex: 1; border: 1px solid var(--rule); border-top: 3px solid var(--ink); padding: 7px 9px; background: #fff }
.fstep.s-unk { border-top-color: #9ca3af } .fstep.s-inf { border-top-color: var(--inf) } .fstep.s-obs { border-top-color: var(--obs) }
.fl { font: 800 10.4px/1.25 Inter } .fd { font-size: 9.2px; line-height: 1.4; margin-top: 2px; color: #333 } .fs { margin-top: 3px } .farrow { align-self: center; font: 800 14px Inter; color: var(--accent) }
.qr { text-align: center } .qrimg svg { width: 132px; height: 132px } .qrurl { font: 700 8.4px "DejaVu Sans Mono"; margin-top: 2px; word-break: break-all } .qrurl a { color: #111 }
/* cover */
.page.cover { background: var(--dark); color: #fff }
.page.cover .top { border-bottom-color: var(--accent) } .page.cover .kick { color: #fff } .page.cover .tmeta { color: #aab0bd }
.page.cover h1.hl { font-size: 37px; line-height: 1.03; color: #fff } .page.cover .acc { color: var(--accent) }
.page.cover .dek { color: #d6d9e0; font-size: 12.4px }
.page.cover .stat { background: #151922; border-color: #2a303c; border-left-color: var(--accent) } .page.cover .sl { color: #fff } .page.cover .ss { color: #aab0bd }
.page.cover .card, .page.cover .fstep, .page.cover .sx { background: #151922; border-color: #2a303c; color: #e5e7eb } .page.cover .cbody, .page.cover .fd { color: #d1d5db }
.page.cover .fmap .ft { color: #fff } .page.cover .fmap .fp { color: #b8bec9 } .page.cover .btitle { color: var(--accent) }
.page.cover .callout { background: #151922; color: #e5e7eb; border-color: var(--accent) } .page.cover .cap { color: #9aa1ad }
.page.cover .ev { background: #1f2430; border-color: #353c4a; color: #c7ccd6 } .page.cover a.ev { color: #9db7ff; border-color: #3a4a78 }
.page.cover .foot { border-top-color: #2a303c; color: #8f96a3 } .page.cover .pn { color: #fff }
.prep { display: flex; gap: 8px; align-items: center; border: 1px solid #2a303c; padding: 6px 8px; border-radius: 4px }
.prep img, .prep .ini { width: 40px; height: 40px; border-radius: 50%; object-fit: cover; flex: none }
.prep .ini { background: var(--accent); color: #111; font: 800 14px/40px Inter; text-align: center }
.prep .pt { font: 800 8px Inter; letter-spacing: .1em; text-transform: uppercase; color: var(--accent) } .prep .pnm { font: 800 10.5px Inter } .prep .prl { font-size: 8px; color: #b8bec9 }
.fit1 .blk { font-size: 9.6px } .fit1 .cbody, .fit1 .so { font-size: 9.2px } .fit1 .prose p { font-size: 9.9px } .fit1 table { font-size: 8.5px }
.compact td { padding: 2px 5px; font-size: 8.2px }
"""


def _hatch_defs() -> str:
    return ('<svg width="0" height="0" style="position:absolute"><defs><pattern id="hatch" width="6" height="6" '
            'patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><rect width="6" height="6" fill="#f9fafb"/>'
            '<line x1="0" y1="0" x2="0" y2="6" stroke="#cbd0d8" stroke-width="3"/></pattern></defs></svg>')


def _prepared_by(ctx: Ctx) -> str:
    pb = ctx.meta.get("prepared_by") or {}
    name = pb.get("name", "Dennis Yu")
    photo = pb.get("photo", "")
    face = (f'<img src="{E(ctx.asset_url(photo))}" alt="{E(name)}">' if ctx.asset_ok(photo)
            else f'<div class="ini">{E("".join(w[0] for w in name.split()[:2]))}</div>')
    if photo and not ctx.asset_ok(photo):
        ctx.missing_assets.append(photo)
    return (f'<div class="blk prep" style="grid-column: span {int(pb.get("span", 4))}">{face}<div><div class="pt">Prepared by</div>'
            f'<div class="pnm">{E(name)}</div><div class="prl">{E(pb.get("role", "Local Service Spotlight"))}</div></div></div>')


def page_html(p: dict, ctx: Ctx, total: int) -> str:
    n = p.get("n")
    kicker = p.get("kicker") or p.get("type", "").replace("_", " ")
    subj = ctx.meta.get("subject", "")
    date = ctx.meta.get("date", "")
    blocks = "".join(C.render_block(b, ctx) for b in p.get("blocks", []))
    if p.get("type") == "cover":
        blocks += _prepared_by(ctx)
    refs = M.refs_in(p)
    evf = C.chips(refs, ctx) if refs else '<span class="mut">none</span>'
    conf = ctx.meta.get("confidentiality", f"Confidential — prepared for {subj}")
    headline = p.get("headline", "")
    return (f'<section class="page {E(p.get("type", ""))}" data-n="{n}">'
            f'<header class="top"><span class="kick"><b>{int(n):02d}</b>{E(kicker)}</span>'
            f'<span class="tmeta">{E(subj)} · {E(date)}</span></header>'
            f'<h1 class="hl">{C.md(headline)}</h1>'
            + (f'<p class="dek">{C.md(p.get("dek", ""))}</p>' if p.get("dek") else "")
            + f'<div class="body">{blocks}</div>'
            f'<footer class="foot"><span class="conf">{E(conf)}</span>'
            f'<span class="evf">Evidence on this page ({len(refs)}): {evf}</span>'
            f'<span class="pn">{int(n)} / {total}</span></footer></section>')


def build_html(audit: dict, ledger: Ledger | None, base: pathlib.Path) -> tuple[str, Ctx]:
    full = expand(audit, ledger)
    ctx = Ctx(full, ledger, base)
    pal = {**DEFAULT_PALETTE, **(ctx.meta.get("palette") or {})}
    accent_ink = pal.get("accent_ink") or _readable_accent(pal["accent"])
    root = (f":root {{ --ink:{pal['ink']}; --paper:{pal['paper']}; --accent:{pal['accent']}; --accent-ink:{accent_ink};"
            f" --dark:{pal['dark']}; --muted:{pal['muted']}; --rule:{pal['rule']}; --obs:#0f6b5c; --inf:#b45309 }}")
    pages = sorted(full.get("pages", []), key=lambda x: x.get("n", 0))
    body = "".join(page_html(p, ctx, len(pages)) for p in pages)
    title = E(ctx.meta.get("title") or f"{ctx.subject} audit")
    doc = (f'<!doctype html><html lang="en"><head><meta charset="utf-8"><title>{title}</title>'
           f'<style>{root}{CSS}</style></head><body>{_hatch_defs()}{body}</body></html>')
    return doc, ctx


def _readable_accent(hexcolor: str) -> str:
    """Accent used as text on white must stay readable; darken light accents."""
    h = hexcolor.lstrip("#")
    if len(h) != 6:
        return "#8a6400"
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    lum = (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255
    if lum < 0.55:
        return hexcolor
    f = 0.55 / lum
    return "#%02x%02x%02x" % (int(r * f), int(g * f), int(b * f))


MEASURE_JS = """
() => [...document.querySelectorAll('section.page')].map(p => {
  const body = p.querySelector('.body');
  const br = body.getBoundingClientRect();
  let maxB = br.top;
  for (const c of body.children) { const r = c.getBoundingClientRect(); if (r.bottom > maxB) maxB = r.bottom; }
  const kids = [...body.children].map(c => Math.round(c.getBoundingClientRect().height));
  // a card's own content height (grid rows stretch both cards of a row to the taller one)
  const cards = [...body.querySelectorAll('.card')].map(c =>
    Math.round([...c.children].reduce((s, k) => s + k.getBoundingClientRect().height, 0)));
  return { n: +p.dataset.n, overflow: body.scrollHeight > body.clientHeight + 2,
           over: Math.max(0, body.scrollHeight - body.clientHeight), h: body.clientHeight, kids, cards,
           fill: Math.min(1, (maxB - br.top) / Math.max(1, br.height)) };
})
"""


def _overflow_detail(page: dict, meas: dict) -> dict:
    """How far a page runs over and what to cut, in words a drafting model can act on."""
    pct = meas.get("over", 0) / max(meas.get("h", 1), 1)
    words = M.words(M.text_of(page))
    blocks = page.get("blocks", [])
    tallest = []
    if meas.get("cards") and any(b.get("type") == "cards" for b in blocks):
        items = [i for b in blocks if b.get("type") == "cards" for i in b.get("items", [])]
        sized = sorted(zip(meas["cards"], range(1, len(items) + 1), items), key=lambda x: -x[0])
        tallest = [f"card {j} ({M.words(' '.join(str(it.get(k, '')) for k in ('title', 'body', 'so')))} words)"
                   for _, j, it in sized[:3]]
    else:
        sized = sorted(zip(meas.get("kids", []), range(1, len(blocks) + 1), blocks), key=lambda x: -x[0])
        tallest = [f"block {j} {b.get('type')} ({h}px, {M.words(M.text_of(b))} words)" for h, j, b in sized[:2]]
    return {"over_pct": round(pct, 3), "cut_words": int(words * pct * 1.15) + 10, "tallest": tallest}


def render(audit_path: str | pathlib.Path, ledger_path: str | pathlib.Path | None, out_pdf: str | pathlib.Path,
           html_out: str | pathlib.Path | None = None) -> dict:
    """Render to PDF and return the render report the R-gates read."""
    audit_path = pathlib.Path(audit_path)
    audit = M.load(audit_path)
    ledger = Ledger.load(ledger_path) if ledger_path else None
    doc, ctx = build_html(audit, ledger, audit_path.parent)
    html_file = pathlib.Path(html_out) if html_out else pathlib.Path(tempfile.mkdtemp()) / "audit.html"
    html_file.write_text(doc, encoding="utf-8")
    from playwright.sync_api import sync_playwright

    with sync_playwright() as pw:
        b = launch_chromium(pw)
        pg = b.new_page(viewport={"width": 816, "height": 1056})
        pg.goto(html_file.resolve().as_uri(), wait_until="load")
        pg.evaluate("document.fonts.ready")
        m = pg.evaluate(MEASURE_JS)
        fitted = [x["n"] for x in m if x["overflow"]]
        if fitted:  # one gentle fit step, never more (shrinking a wall of text is a failure)
            pg.evaluate("ns => ns.forEach(n => document.querySelector(`section.page[data-n='${n}']`).classList.add('fit1'))", fitted)
            m = pg.evaluate(MEASURE_JS)
        pg.pdf(path=str(out_pdf), width="8.5in", height="11in", print_background=True,
               margin={"top": "0", "right": "0", "bottom": "0", "left": "0"})
        b.close()
    from pypdf import PdfReader

    r = PdfReader(str(out_pdf))
    links = sum(1 for pgx in r.pages for a in (pgx.get("/Annots") or [])
                if a.get_object().get("/Subtype") == "/Link")
    by_n = {p.get("n"): p for p in expand(audit, ledger).get("pages", [])}
    report = {
        "pdf": str(out_pdf), "html": str(html_file), "pdf_pages": len(r.pages),
        "overflow_pages": [x["n"] for x in m if x["overflow"]], "fit_applied": fitted,
        "overflow_detail": {str(x["n"]): _overflow_detail(by_n.get(x["n"], {}), x) for x in m if x["overflow"]},
        "fill": {str(x["n"]): round(x["fill"], 3) for x in m}, "links": links,
        "missing_assets": sorted(set(ctx.missing_assets)),
        "qr_decoded": _decode_qr(out_pdf, audit),
    }
    return report


QR_UNCHECKED = "UNCHECKED"


def _decode_qr(pdf: str | pathlib.Path, audit: dict) -> str | None:
    """The URL the agents-page QR decodes to, None if it decodes to nothing, or a value starting
    with QR_UNCHECKED when a tool the check needs is not installed (not the writer's fault)."""
    pages = [p.get("n") for p in audit.get("pages", []) if p.get("type") == "agents"]
    if not pages:
        return None
    try:
        import cv2
    except ImportError:
        return f"{QR_UNCHECKED}: opencv-python-headless is not installed"
    tmp = pathlib.Path(tempfile.mkdtemp())
    try:
        subprocess.run(["pdftoppm", "-r", "200", "-f", str(pages[0]), "-l", str(pages[0]), "-png", str(pdf), str(tmp / "q")],
                       check=False, capture_output=True)
    except FileNotFoundError:
        return f"{QR_UNCHECKED}: pdftoppm (poppler-utils) is not installed"
    for png in tmp.glob("q*.png"):
        img = cv2.imread(str(png))
        if img is None:
            continue
        val, _, _ = cv2.QRCodeDetector().detectAndDecode(img)
        if val:
            return val
    return None
