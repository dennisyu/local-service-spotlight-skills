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
    if stage in ("synthesis", "pages", "fix"):
        # The cards ask for "real captured image only", but until Nov 10 no writer was told which
        # files exist, so all four pilot rebuilds put an invented screenshot on the cover.
        head.append("# ASSETS (the only image files there are: a photo or screenshot block may use one of "
                    "these and nothing else; with none listed, use another visual)\n"
                    + json.dumps(render.assets_available(run, brief), ensure_ascii=False))
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


def check_fix(obj, ledger, must: frozenset | set = frozenset()):
    """A fix returns only the pages it changed, each a full page object for pages 3-19. An empty
    list is an answer when nothing on pages 3-19 can clear the list (a ledger-level warning such
    as G12). Rejecting it, as the kit did until Nov 10, bought a retry and then a bigger model to
    say the same thing, or pushed the writer to swap in citations that do not support the claim.
    `must` holds the pages 3-19 that a FAIL in the list names: then an empty list is no answer,
    and the writer hears so and tries again inside the stage instead of spending a whole round."""
    if not isinstance(obj.get("pages"), list):
        return ["return the pages you changed under 'pages' (an empty list if no page can clear it)"]
    pages = obj["pages"]
    bad = [p.get("n") for p in pages if p.get("n") not in range(3, 20)]
    probs = [f"fix may only return pages 3-19; got {bad}"] if bad else []
    if not pages and must:
        probs.append(f"the fix list holds a FAIL on page {', '.join(map(str, sorted(must)))}: return "
                     "each such page changed so the FAIL clears")
    probs += [f"unknown evidence id {x}" for x in _ids_missing(pages, ledger)][:15]
    return probs


CHECKS = {"identity": check_identity, "score": check_score, "synthesis": check_synthesis,
          "pages": check_pages, "actions": check_actions}
MAX_FIX_ROUNDS = 3
FRONT_GATES = {"G20", "G21", "G22", "G24"}
# Gates on the action register. Until Nov 10 no fix path could revise the register, so an item
# from these gates, or a privacy hit inside an action, stayed open through every fix round.
ACTION_GATES = {"G60", "G61", "G62", "G63", "G64", "G65"}
# Failures no fix-loop writer can clear (structure, identity and score stages, page count): a
# bigger model on pages or the register would only pay for the same answer.
NO_WRITER = {"G01", "G02", "G05", "G50", "G51", "G52", "G53", "G54", "R01"}
NOT_THE_WRITERS = {"G81"}   # the preparer's photo comes from the brief and assets, not from a model
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
                   "page": f.get("page"), "where": f.get("where"), "msg": f"{f.get('problem', '')} Fix: {f.get('fix', '')}"}
                  for f in review.get("findings", []) if f.get("severity") in ("S0", "S1", "S2")]
    return items


PAGE_LIST = re.compile(r"\bpages? \[?((?:\d{1,2}(?:\s*(?:,|and|&|-|–|to)\s*)?)+)\]?", re.I)


def _page_numbers(text: str, where: bool = False) -> set[int]:
    """Page numbers a text names: "page 7", "Pages [2, 7]", "pages 5-8", "pages 1, 2 and 18", "p7:".
    A review finding's where field also says "p16 headline" and "cover headline"."""
    found: set[int] = set()
    for grp in PAGE_LIST.findall(text):
        for a, b in re.findall(r"(\d{1,2})(?:\s*(?:-|–|to)\s*(\d{1,2}))?", grp):
            found |= set(range(int(a), int(b) + 1)) if b and int(a) <= int(b) else {int(a)}
    found |= {int(n) for n in re.findall(r"\bp(\d{1,2}):", text)}
    if where:
        found |= {int(n) for n in re.findall(r"\bp\.?\s?(\d{1,2})\b", text, re.I)}
        if re.search(r"\bcover\b", text, re.I):
            found.add(1)
    return {n for n in found if 1 <= n <= 20}


def _pages_named(item: dict) -> set[int]:
    """Every page number an open item names: its page field, the pages its message names, and the
    pages a review finding's where field lists. Until Nov 12 the where field was read only for the
    register, so "p5 'What moves the number'; p10 Trust row; p18 Days 1-7" reached none of them."""
    found = _page_numbers(item.get("msg") or "") | _page_numbers(str(item.get("where") or ""), where=True)
    if isinstance(item.get("page"), int):
        found.add(item["page"])
    return {n for n in found if 1 <= n <= 20}


def _front(item: dict) -> bool:
    """Pages 1-2 belong to the synthesis model."""
    if "route" in item:
        return item["route"]["front"]
    return item.get("id") in FRONT_GATES or bool(_pages_named(item) & {1, 2})


def _acts(item: dict) -> bool:
    """The action register belongs to the actions model: every action-gate item, any gate item the
    gates locate in the register ("action register A8"), and a review finding whose `where` names
    the register or an action id, or that _located finds in the register. A review's other free
    text is not read: "register the domain" is a page finding."""
    if "route" in item:
        return item["route"]["acts"]
    if item.get("from") == "review":
        return bool(re.search(r"\bregister\b|\bactions?\b|\bA\d{1,3}\b", str(item.get("where") or ""), re.I))
    if item.get("id") in ACTION_GATES:
        return True
    return bool(re.search(r"action register", str(item.get("msg") or ""), re.I))


def _score(item: dict) -> bool:
    """An exam row's reason belongs to the score model: it lives in score.json, and the page only
    draws the row's name, score and evidence ids. Until Nov 12 nothing could revise a reason, so a
    review finding against one went to the page writer, which printed a note about its own page."""
    if "route" in item:
        return item["route"]["score"]
    return item.get("from") == "review" and bool(
        re.search(r"\b(exam|heatmap|score)\b", str(item.get("where") or ""), re.I))


def _back(item: dict) -> bool:
    """Pages 3-19 belong to the fix model, including an item that also names a front page.
    An item that names no page and lives only in the register or an exam row is not sent here:
    the fix model returns pages and cannot clear it. Nor is one that names only page 20: code
    builds that page whole, so no writer can change it, and a rung-up round on it would pay for
    nothing."""
    if "route" in item:
        return item["route"]["back"]
    named = _pages_named(item)
    if any(3 <= n <= 19 for n in named):
        return True
    if named and named <= {20}:
        return False
    return not _front(item) and not _acts(item) and not _score(item)


# A review finding quotes the words it faults. Quotes are read from its problem, never from its fix
# (the fix quotes the new wording), and an apostrophe inside a word ("the owner's") is not a quote mark.
QUOTE_RE = re.compile(r"(?<![\w'’])['‘]([^'‘’\n]{12,}?)['’](?!\w)|[\"“]([^\"“”\n]{12,}?)[\"”]")
# "Four pages say ...", "everywhere": the finding covers pages it does not number.
SPANS_PAGES = re.compile(r"\b(?:two|three|four|five|six|seven|eight|nine|ten|several|many|all|every|each|\d+)\s+"
                         r"(?:other\s+)?pages\b|\beverywhere\b|\bevery page\b|\bacross (?:the )?pages\b", re.I)


def _norm(s: str) -> str:
    s = s.replace("**", "").translate(str.maketrans({"’": "'", "‘": "'", "“": '"', "”": '"', " ": " "}))
    return re.sub(r"\s+", " ", s).strip().lower()


def _strings(o) -> list[str]:
    if isinstance(o, str):
        return [o]
    if isinstance(o, dict):
        return [s for v in o.values() for s in _strings(v)]
    if isinstance(o, list):
        return [s for v in o for s in _strings(v)]
    return []


def _quoted(item: dict) -> list[str]:
    """The words a review finding quotes from the audit, normalized, each at least three words and
    12 characters; a quote cut with an ellipsis counts as its pieces."""
    problem = (item.get("msg") or "").split(" Fix: ", 1)[0]
    out: list[str] = []
    for m in QUOTE_RE.finditer(problem):
        for frag in re.split(r"\.\.\.|…", m.group(1) or m.group(2)):
            frag = _norm(frag).strip(" .,;:")
            if len(frag) >= 12 and len(frag.split()) >= 3 and frag not in out:
                out.append(frag)
    return out


def _texts(run_dir: pathlib.Path) -> list[tuple[str, object, str]]:
    """Every text a fix-loop writer owns, normalized: ("page", n) for pages 1-19, ("action", id)
    for the register, ("row", n) for each Brand Authority row's reason."""
    def load(name: str) -> dict:
        p = run_dir / f"{name}.json"
        return json.loads(p.read_text()) if p.exists() else {}
    out = [("page", p["n"], _norm(" ".join(_strings(p))))
           for src in (load("synthesis"), load("pages")) for p in src.get("pages", []) if isinstance(p.get("n"), int)]
    out += [("action", a["id"], _norm(" ".join(_strings(a)))) for a in load("actions").get("actions", []) if a.get("id")]
    sc = load("score")
    out += [("row", r.get("n"), _norm(str(r.get("why") or ""))) for r in sc.get("brand_authority", sc).get("rows", [])]
    return out


def _pages_phrase(ns: list[int]) -> str:
    return f"page {ns[0]}" if len(ns) == 1 else f"pages [{', '.join(map(str, ns))}]"


def _located(item: dict, run_dir: pathlib.Path) -> dict:
    """Send a review finding to every writer that owns the words it faults. The reviewer files a
    finding under one page; on Nov 12 (person standard, 229cfc9) that sent "Row 4 says 'two
    relationships independently corroborated'" to the page writer, though the words were a row's
    reason in score.json, and "Four pages say we ask each client to 'repeat their words' as a
    review" to the cover's writer alone. Each quote is looked up where it now stands
    (pages 1-19, the register, the exam rows' reasons), and the pages and actions its where field
    and text name count too; words like "four pages" add the page writer. A short quote that
    stands in more than three places is a term the audit uses throughout (his name, a title), not
    the words at fault: on the same run such terms sent three findings to every writer. Words a
    row's reason shares with a page are the page's, unless the finding names that row. When every
    quote stands only off the pages (a row's reason, the register) and nothing names a page, the
    page field no longer sends the finding to the page writer. The writers are told where."""
    if item.get("from") != "review":
        return item
    msg = item.get("msg") or ""
    where_txt = str(item.get("where") or "")
    problem = msg.split(" Fix: ", 1)[0]
    texts = _texts(run_dir)
    named_rows = {int(n) for grp in re.findall(r"\brows? ((?:\d{1,2}(?:\s*(?:,|and|&)\s*)?)+)", f"{problem} {where_txt}", re.I)
                  for n in re.findall(r"\d+", grp)}
    pages: set[int] = set()
    acts: set[str] = set()
    rows: set[int] = set()
    missed = False
    for q in _quoted(item):
        hits = [(kind, key) for kind, key, text in texts if q in text]
        if len(q.split()) < 6 and len(hits) > 3:
            continue
        missed |= not hits
        on_a_page = any(kind == "page" for kind, _ in hits)
        for kind, key in hits:
            if kind == "row" and on_a_page and key not in named_rows:
                continue
            {"page": pages, "action": acts, "row": rows}[kind].add(key)
    named = _pages_named({"msg": msg, "where": where_txt})          # not the page field
    off_page = bool(acts or rows) and not pages and not missed and not named
    acts |= {key for kind, key, _ in texts if kind == "action"
             and re.search(rf"(?<![\w-]){re.escape(str(key))}(?![\w-])", f"{msg} {where_txt}")}
    spans = bool(SPANS_PAGES.search(msg))
    if not (pages or acts or rows or spans):
        return item          # nothing found: the page field, the pages named and where route it
    on = pages | named
    if isinstance(item.get("page"), int) and not off_page:
        on.add(item["page"])
    route = {"front": bool(on & {1, 2}) or item.get("id") in FRONT_GATES,
             "back": spans or any(3 <= n <= 19 for n in on),
             "acts": bool(acts) or _acts(item), "score": bool(rows) or _score(item)}
    where = [f"on {_pages_phrase(sorted(n for n in pages if n <= 2))}"] if pages & {1, 2} else []
    if any(3 <= n <= 19 for n in pages):
        where.append(f"on {_pages_phrase(sorted(n for n in pages if 3 <= n <= 19))}")
    if acts:
        where.append("in " + ", ".join(sorted(acts, key=lambda a: (len(a), a))))
    if rows:
        where.append(f"in the reason of exam row{'s' if len(rows) > 1 else ''} {', '.join(map(str, sorted(rows)))}"
                     " (the score file; the page draws no reasons)")
    note = (f" [Where it stands: {'; '.join(where)}.]" if where else "") + \
           (" [It spans pages it does not number: fix every page 3-19 that carries it.]" if spans else "")
    return {**item, "msg": msg + note, "route": route}


def _ids_unknown_in(text: str, ledger: Ledger) -> list[str]:
    """Ids written into prose that look like this ledger's ids but are not in it."""
    families = {r["id"].rsplit("-", 1)[0] for r in ledger.rows if "-" in str(r.get("id"))}
    return sorted({t for t in re.findall(r"\b[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)+\b", text)
                   if t.rsplit("-", 1)[0] in families and not ledger.has(t)})


def check_score_revision(obj, current, ledger) -> list[str]:
    """A review round may rewrite a Brand Authority row's reason and evidence, never its score: a
    score changes only through the reviewer's score_adjustments, which code applies. Problems the
    current file already has are not the reviser's."""
    before = set(check_score(current, ledger))
    probs = [p for p in check_score(obj, ledger) if p not in before]
    old = {r.get("n"): r for r in current.get("brand_authority", current).get("rows", [])}
    for r in obj.get("brand_authority", obj).get("rows", []):
        was = old.get(r.get("n"))
        if was is None:
            probs.append(f"row {r.get('n')}: there is no such row")
            continue
        if r.get("score") != was.get("score"):
            probs.append(f"row {r.get('n')}: keep the score {was.get('score')}; a score changes only through the "
                         "reviewer's score_adjustments")
        if not str(r.get("why") or "").strip():
            probs.append(f"row {r.get('n')}: the reason is empty")
        probs += [f"row {r.get('n')}: unknown evidence id {x} in the reason" for x in _ids_unknown_in(str(r.get("why") or ""), ledger)]
    return probs


def _kept_action_ids(obj: dict, current: dict) -> list[str]:
    """A revised register keeps every action id it had. Pages print ids in fields and as plain
    table text (an "Action" column), and the to-dos follow the ids, so an id is a stable key."""
    have = {a.get("id") for a in obj.get("actions", [])}
    return [f"keep action {i}: every id stays, because pages and to-dos already print it"
            for i in sorted({a.get("id") for a in current.get("actions", [])} - have)]


def _apply_fixes(run_dir: pathlib.Path, ledger: Ledger, tier: str, cfg: dict, fake, items: list[dict],
                 review: dict | None = None, confidential: bool = False, max_usd: float | None = None,
                 up_writers: frozenset = frozenset()) -> bool:
    """One fix round, upstream first, so each writer sees the stage files already decided: the
    reviewer's score adjustments go into score.json (code applies them), the score model revises
    the exam rows' reasons, the fix model patches pages 3-19, the synthesis model revises pages 1-2
    with those pages in view, and the actions model revises the action register. Each review
    finding goes to the writers that own the words it quotes (_located). A fix round obeys the same
    confidential guard and spending cap as the first draft. up_writers names the writers
    ("synthesis", "fix", "actions") that run one rung up the ladder this round (the loop asks for
    that for one round, once, after a round that left a FAIL those writers own)."""
    ok = True
    if review and review.get("score_adjustments"):
        # Before any writer: until Nov 12 these landed after the pages were revised, so a page
        # writer described a row's old score in the same round that changed it.
        sc = json.loads((run_dir / "score.json").read_text())
        ba = sc.get("brand_authority", sc)
        for adj in review["score_adjustments"]:
            for row in ba.get("rows", []):
                if row.get("n") == adj.get("row") and adj.get("to") is not None:
                    row["score"] = adj["to"]
                    row["why"] = f"{row.get('why', '')} (review: {adj.get('why', '')})".strip()
        (run_dir / "score.json").write_text(json.dumps(sc, indent=1, ensure_ascii=False))
    items = [_located(i, run_dir) for i in items]
    rows = [i for i in items if _score(i)]
    front = [i for i in items if _front(i)]
    rest = [i for i in items if _back(i)]
    acts = [i for i in items if _acts(i)]
    def up(st: str) -> str | None:
        return router.next_rung(cfg, cfg["tiers"][tier]["models"][st], tier) if st in up_writers else None
    if rows:
        current = json.loads((run_dir / "score.json").read_text())
        res = router.run_stage("score", prompt("score", run_dir, ledger, extra={
            "task": "Revise the reason ('why') of each Brand Authority row that fix_list faults, so every item "
                    "clears. Return the whole score file in your card's output shape. Keep every score: a score "
                    "changes only through the reviewer's score_adjustments, which code applies.",
            "fix_list": rows, "current_score": current}), tier, run_dir,
            check=lambda o: check_score_revision(o, current, ledger), cfg=cfg, fake=fake,
            confidential=confidential, max_usd=max_usd, write=False)
        if res["ok"]:
            new = {r.get("n"): r for r in res["obj"].get("brand_authority", res["obj"]).get("rows", [])}
            for r in current.get("brand_authority", current).get("rows", []):
                if r.get("n") in new:
                    r["why"] = new[r["n"]].get("why", r.get("why"))
                    r["evidence"] = new[r["n"]].get("evidence", r.get("evidence"))
            (run_dir / "score.json").write_text(json.dumps(current, indent=1, ensure_ascii=False))
        ok &= res["ok"]
    # Pages 3-19 first, pages 1-2 after: the front pages summarize the rest, and every writer sees
    # the stage files already decided. With the summary first, a person replay's cover kept a
    # $21 ad test that the same round's page fix changed to $14 on page 11 (Nov 10).
    if rest:
        must = frozenset(n for i in rest if i["status"] == "FAIL" for n in _pages_named(i) if 3 <= n <= 19)
        res = router.run_stage("fix", prompt("fix", run_dir, ledger, extra={
            "task": "Clear every item in fix_list. Return ONLY the pages you changed, each as a full page "
                    "object (pages 3-19), under 'pages'. Never shrink type: cut words or move a block. "
                    "Blocks the renderer draws itself (the exam heatmap and scorebar, the plan swimlane, "
                    "the agents QR) are not in your page objects and cannot be changed: make room in your own. "
                    "The heatmap draws each row's name, score and evidence ids, not its reason; the score "
                    "writer revises reasons. Write only what a reader needs: never write a note about how "
                    "the page was made or what another file still says.",
            "fix_list": rest}), tier, run_dir, check=lambda o: check_fix(o, ledger, must), cfg=cfg, fake=fake,
            confidential=confidential, max_usd=max_usd, model=up("fix"))
        if res["ok"]:
            cur = json.loads((run_dir / "pages.json").read_text())
            by_n = {p.get("n"): p for p in cur.get("pages", [])}
            by_n.update({p.get("n"): p for p in res["obj"].get("pages", [])})
            cur["pages"] = [by_n[n] for n in sorted(by_n)]
            (run_dir / "pages.json").write_text(json.dumps(cur, indent=1, ensure_ascii=False))
        ok &= res["ok"]
    if front:
        res = router.run_stage("synthesis", prompt("synthesis", run_dir, ledger, extra={
            "task": "Revise synthesis.json so every item in fix_list is cleared; keep what already works.",
            "fix_list": front, "current_synthesis": json.loads((run_dir / "synthesis.json").read_text())}),
            tier, run_dir, check=lambda o: check_synthesis(o, ledger), cfg=cfg, fake=fake,
            confidential=confidential, max_usd=max_usd, model=up("synthesis"))
        ok &= res["ok"]
    if acts:
        current = json.loads((run_dir / "actions.json").read_text())
        res = router.run_stage("actions", prompt("actions", run_dir, ledger, extra={
            "task": "Revise the action register so every item in fix_list is cleared. Return the whole "
                    "register under 'actions'; keep every action id and everything that already works.",
            "fix_list": acts, "current_actions": current}),
            tier, run_dir, check=lambda o: check_actions(o, ledger) + _kept_action_ids(o, current), cfg=cfg,
            fake=fake, confidential=confidential, max_usd=max_usd, model=up("actions"))
        ok &= res["ok"]
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
                           allowed_phones=brief.get("allowed_phones", [])).summary()
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
    odd = M.off_shape(r["id"] for r in ledger.rows)
    if odd:   # G05 would hold the finished audit; say it before a single model call is paid for
        out["verdict"] = "HOLD at ledger"
        out["hold_reason"] = (f"ledger ids {odd[:10]} lack the id shape (V-E012, E-001) that a table cell "
                              "cites by; rename them in the ledger and run again")
        out["usd"] = router.spent(run_dir)
        return out
    if not M.iso_day(ledger.capture_date):   # the bundle would refuse the finished run; say it now
        out["verdict"] = "HOLD at ledger"
        out["hold_reason"] = (f"ledger capture_date is {ledger.capture_date!r}, not one date (YYYY-MM-DD). "
                              "The house-gate bundle dates every ledger row by it and refuses any other "
                              "shape, so the finished audit could not be graded. Put the research cutoff "
                              "date there; times of later re-checks go in sources.jsonl")
        out["usd"] = router.spent(run_dir)
        return out
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
    loop = {"rounds": 0, "last": None, "escalated": False}

    def gate_rounds(audit, rep, rr):
        """Fix rounds on the gate and render lists, MAX_FIX_ROUNDS in the whole run."""
        while loop["rounds"] < MAX_FIX_ROUNDS:
            items = fix_list(rep, rr)
            open_now = sorted((i["from"], str(i["id"]), i["status"]) for i in items)
            last = loop["last"]
            if not items:
                break
            if last is not None and all(i["status"] == "WARN" for i in items) and set(open_now) <= set(last):
                break   # only warnings the last round already had: no round on them alone
            up_writers: frozenset = frozenset()
            if open_now == last:
                # The last round cleared nothing. A warning alone is not worth more rounds (it often
                # sits in the ledger, beyond any writer), so stop. A FAIL holds the audit: until Nov 10
                # the loop stopped here too, leaving it on HOLD with rounds unspent when only the cheap
                # model had tried. Now, once per run, a FAIL a writer owns gets one round with that
                # writer one rung up the ladder; the round after goes back to the tier's models.
                owners = {w for i in items if i["status"] == "FAIL" and i["id"] not in NO_WRITER
                          for w, owns in (("synthesis", _front), ("fix", _back), ("actions", _acts)) if owns(i)}
                ups = {w: router.next_rung(cfg, cfg["tiers"][tier]["models"][w], tier) for w in owners}
                if loop["escalated"] or not any(ups.values()):
                    break
                loop["escalated"] = True
                up_writers = frozenset(w for w, m in ups.items() if m)
                out["fix_escalated_to"] = ups.get("fix") or next(m for m in ups.values() if m)
                out["fix_escalated"] = {w: m for w, m in ups.items() if m}
            loop["last"] = open_now
            loop["rounds"] += 1
            if not _apply_fixes(run_dir, ledger, tier, cfg, fake, items,
                                confidential=confidential, max_usd=max_usd, up_writers=up_writers):
                break
            audit, rep, rr = _check_all(run_dir, ledger, tier, render_pdf)
        return audit, rep, rr

    def holds(rep, rr) -> bool:
        return rep["verdict"] == "HOLD" or (rr is not None and rr["gates"]["verdict"] == "HOLD")

    audit, rep, rr = gate_rounds(audit, rep, rr)
    gates_ok = not holds(rep, rr)
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
            # A review fix can break a hard gate: in the Nov 10 replays a page fix ran page 19
            # 40px over, and the next review was paid for on a draft that could only end HOLD.
            # Such a draft gets the gate rounds the run has left first; if it still holds, no
            # review can change the verdict, so none is paid for.
            if holds(rep, rr):
                audit, rep, rr = gate_rounds(audit, rep, rr)
            gates_ok = not holds(rep, rr)
            if not gates_ok:
                break
        out["review"] = rv.get("verdict") if rv else None
    out["fix_rounds"] = loop["rounds"]
    out["gate"] = rep["verdict"]          # the final files' verdicts, not the ones before the review
    if rr:
        out["render"] = rr["gates"]["verdict"]
    log = json.loads((run_dir / "run.json").read_text()) if (run_dir / "run.json").exists() else {"attempts": []}
    out["usd"] = round(sum(a.get("usd", 0) for a in log["attempts"]), 4)
    if not gates_ok:
        out["verdict"] = "HOLD"
    elif not review:
        out["verdict"] = "REVIEW_READY"
    else:
        out["verdict"] = "READY" if rv and not _serious(rv) else "HOLD"
    return out
