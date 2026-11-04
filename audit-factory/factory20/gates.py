"""Deterministic quality gates for audit.json and its rendered PDF.

Every gate returns PASS / WARN / FAIL with a message written for the agent that must fix
it ("what is wrong, where, what to do"). FAIL on a HARD gate is HOLD: the audit does not
ship. WARN is a fix-before-send note. No model is involved; the gates cost nothing and
run on every draft, so the expensive review pass only ever sees work that already clears
the mechanical bar.

Thresholds are calibrated on finished audits (see docs/CALIBRATION.md): Claude's
October audits clear every density/evidence gate; the thin cheap-lane drafts fail them.
"""
from __future__ import annotations

import datetime as _dt
import re
from collections import Counter

from . import model as M
from . import score as S
from .ledger import Ledger

TIERS = {
    #               min unique refs  refs/page  words/page  numbers/page  visual types
    # words_page counts reader text in audit.json; the rendered PDF adds ~20% (headers,
    # footers, evidence ids, chart labels). 260 JSON words ~= 330 PDF words at house type.
    "lean":       {"refs_total": 30, "refs_page": 2, "words_page": 200, "numbers_page": 6, "visual_types": 6},
    "standard":   {"refs_total": 50, "refs_page": 3, "words_page": 260, "numbers_page": 10, "visual_types": 8},
    "enterprise": {"refs_total": 80, "refs_page": 4, "words_page": 320, "numbers_page": 14, "visual_types": 10},
}

GENERIC_TITLES = re.compile(
    r"^(executive summary|summary|overview|introduction|appendix|the verdict|verdict|next steps|"
    r"recommendations|conclusion|findings|analysis|methodology|about|background)$", re.I)
BANNED = [
    "build awareness", "post more", "improve seo", "increase engagement", "boost engagement",
    "leverage", "synergy", "holistic", "robust", "cutting-edge", "cutting edge", "game-changer",
    "game changer", "unlock", "elevate", "seamless", "empower", "in today's", "digital landscape",
    "next level", "world-class", "best-in-class", "passionate about", "thought leader",
    "lorem ipsum", "placeholder", "tbd", "todo", "insert ", "[name]", "xx%",
]
GENERIC_ACCEPTANCE = re.compile(r"^(done|complete|completed|improved|better|launched|live|finished)\.?$", re.I)
EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE = re.compile(r"(?<!\d)(?:\+?1[\s.-]?)?\(?\d{3}\)?[\s.-]\d{3}[\s.-]\d{4}(?!\d)")
SECRETS = re.compile(r"(api[_-]?key|password|passwd|secret[_-]?key|bearer\s+[a-z0-9]|sk-[a-z0-9]{8,}|agent receipt:)", re.I)
BOLD_CLAIM = re.compile(r"(\$\s?\d[\d,.]*\s?(?:m|mm|million|b|billion)\b|#\s?1\b|\bnumber one\b|\blargest\b|\bleading\b|\bbest\b)", re.I)
ALLOWED_EMAILS = {"operations@localservicespotlight.com"}

# Page 2 is one printed page. Measured 2026-11-04 on four page-2 renders: eight cards fit at
# about 600 words (title + body + "So:") counting each micro-chart as 20 words; 635 overflowed.
P2_BUDGET, P2_VIZ_WORDS, P2_BODY_MAX = 600, 20, 52


class Report:
    def __init__(self):
        self.checks: list[dict] = []

    def add(self, gid: str, name: str, level: str, ok: bool, msg: str = "", where: str = "", hard: bool = True):
        status = "PASS" if ok else ("FAIL" if hard else "WARN")
        self.checks.append({"id": gid, "name": name, "status": status, "hard": hard,
                            "level": level, "where": where, "msg": "" if ok else msg})

    @property
    def verdict(self) -> str:
        if any(c["status"] == "FAIL" for c in self.checks):
            return "HOLD"
        if any(c["status"] == "WARN" for c in self.checks):
            return "FIX"
        return "PASS"

    def summary(self) -> dict:
        c = Counter(ch["status"] for ch in self.checks)
        return {"verdict": self.verdict, "pass": c.get("PASS", 0), "warn": c.get("WARN", 0),
                "fail": c.get("FAIL", 0), "checks": self.checks}

    def failures(self) -> list[dict]:
        return [c for c in self.checks if c["status"] != "PASS"]


def _is_date(s: str) -> bool:
    try:
        _dt.date.fromisoformat(str(s)[:10])
        return True
    except ValueError:
        return False


INTERNAL_DEST = re.compile(r"basecamp|action register|agent audit library|\bdrive\b|internal|\breport\b|team thread", re.I)


def _digits(s: str) -> str:
    return re.sub(r"\D", "", s)[-10:]


def gate_audit(audit: dict, ledger: Ledger | None = None, tier: str = "standard",
               do_not_print: list[str] | None = None, allowed_phones: list[str] | None = None) -> Report:
    T = TIERS[tier]
    R = Report()
    pages = audit.get("pages", [])
    meta = audit.get("meta", {})
    actions = audit.get("actions", [])
    action_ids = {a.get("id") for a in actions}

    # ---------- G01 structure ----------
    ns = [p.get("n") for p in pages]
    R.add("G01", "Exactly 20 pages numbered 1-20", "structure", sorted(ns) == list(range(1, 21)),
          f"pages are {ns}; the product is exactly 20 pages, numbered 1-20")
    for n, t in M.FIXED.items():
        p = next((p for p in pages if p.get("n") == n), None)
        R.add("G02", f"Page {n} is the {t} page", "structure", bool(p) and p.get("type") == t,
              f"page {n} must have type '{t}'", where=f"p{n}")
    covered = set()
    for p in pages:
        covered.add(p.get("type"))
        covered.update(p.get("covers") or [])
    missing = [t for t in M.PAGE_TYPES if t not in covered]
    R.add("G03", "Every blueprint requirement is covered", "structure", not missing,
          f"no page covers: {', '.join(missing)} — give a page that type or list it in 'covers'")
    unknown_blocks = [(p.get("n"), b.get("type")) for p in pages for b in p.get("blocks", [])
                      if b.get("type") not in M.ALL_BLOCKS]
    R.add("G04", "Only known block types", "structure", not unknown_blocks,
          f"unknown block types {unknown_blocks}; use one of {sorted(M.ALL_BLOCKS)}")

    # ---------- G10 evidence linkage ----------
    all_refs = M.refs_in(pages) + M.refs_in(actions) + M.refs_in(audit.get("exams", {}))
    uniq = set(all_refs)
    if ledger is not None:
        dangling = sorted(r for r in uniq if not ledger.has(r))
        R.add("G10", "Every evidence ref exists in the ledger", "evidence", not dangling,
              f"{len(dangling)} refs not in ledger: {dangling[:12]} — cite real ledger ids only")
        cited = [ledger.get(r) for r in uniq if ledger.get(r)]
        wrong_person = [c["id"] for c in cited if c["kind"] == "ambiguous" or c["match"] in ("AMBIGUOUS", "NAMESAKE", "REJECTED")]
        # ambiguous rows may be cited only on the identity page
        id_page = M.page_by_type(audit, "identity") or {}
        allowed = set(M.refs_in(id_page)) | set(M.refs_in(M.page_by_type(audit, "risks") or {}))
        leak = sorted(set(wrong_person) - allowed)
        R.add("G11", "Namesake/ambiguous rows cited only on identity or risks pages", "evidence", not leak,
              f"ambiguous/namesake evidence used as proof: {leak[:10]}")
        with_url = sum(1 for c in cited if c["kind"] == "evidence" and c["url"].startswith("http"))
        ev_cited = sum(1 for c in cited if c["kind"] == "evidence")
        share = with_url / ev_cited if ev_cited else 0
        R.add("G12", "Most cited evidence has a public link", "evidence", share >= 0.6,
              f"only {share:.0%} of cited evidence rows carry a URL; readers need clickable sources", hard=False)
    R.add("G13", f"At least {T['refs_total']} distinct evidence refs", "evidence", len(uniq) >= T["refs_total"],
          f"{len(uniq)} distinct refs; a {tier} audit weaves >= {T['refs_total']} — use more of the ledger")
    thin = [p.get("n") for p in pages if len(M.refs_in(p)) < T["refs_page"]]
    R.add("G14", f"Every page cites >= {T['refs_page']} evidence rows", "evidence", not thin,
          f"pages {thin} cite fewer than {T['refs_page']} rows; put the proof on the page where the claim lives")

    # ---------- G20 page 2 insight cards ----------
    p2 = next((p for p in pages if p.get("n") == 2), {})
    cards = [i for b in p2.get("blocks", []) if b.get("type") == "cards" for i in b.get("items", [])]
    R.add("G20", "Page 2 has 5-8 insight cards", "insight", 5 <= len(cards) <= 8,
          f"page 2 has {len(cards)} cards; write 5-8 non-obvious findings")
    bad = []
    for i, c in enumerate(cards, 1):
        probs = []
        if c.get("badge") not in M.BADGES:
            probs.append("badge")
        if M.words(c.get("title", "")) < 4:
            probs.append("title<4 words")
        if M.words(c.get("body", "")) < 25:
            probs.append("body<25 words")
        if M.words(c.get("so", "")) < 6:
            probs.append("'so' implication missing/short")
        if not M.refs_in(c):
            probs.append("no evidence")
        if not M.action_refs_in(c):
            probs.append("no action id")
        if M.numbers(c.get("title", "") + " " + c.get("body", "")) < 1:
            probs.append("no number")
        if probs:
            bad.append(f"card {i}: {', '.join(probs)}")
    R.add("G21", "Each insight card: badge, claim title, proof, 'So:', evidence, action, a number", "insight",
          not bad, "; ".join(bad[:8]))
    unk = sum(1 for c in cards if c.get("badge") == "UNKNOWN")
    R.add("G22", "Summary is findings, not open questions (<= 2 UNKNOWN cards)", "insight", unk <= 2,
          f"{unk} of {len(cards)} summary cards are UNKNOWN — that is a research gap; go get the evidence")
    dangling_a = sorted(set(M.action_refs_in(pages)) - action_ids)
    R.add("G23", "Every action id on a page exists in the register", "insight", not dangling_a,
          f"pages reference actions not in the register: {dangling_a[:10]}")
    card_words = [M.words(" ".join(str(c.get(k, "")) for k in ("title", "body", "so"))) for c in cards]
    load = sum(card_words) + P2_VIZ_WORDS * sum(1 for c in cards if c.get("viz"))
    budget = P2_BUDGET if len(cards) >= 7 else P2_BUDGET + 80
    long_bodies = [(M.words(c.get("body", "")), i) for i, c in enumerate(cards, 1)
                   if M.words(c.get("body", "")) > P2_BODY_MAX]
    p2_msg = (f"page 2 carries about {load} words (counting {P2_VIZ_WORDS} per micro-chart); about {budget} fit on "
              f"one page, so cut at least {max(0, load - budget)} words before rendering")
    if long_bodies:
        p2_msg += "; longest bodies: " + ", ".join(f"card {i} ({w} words, keep each ≤ {P2_BODY_MAX})"
                                                     for w, i in sorted(long_bodies, reverse=True)[:3])
    R.add("G24", "Page 2 fits on one page (card word budget)", "insight", load <= budget and not long_bodies,
          p2_msg, hard=False)

    # ---------- G30 headlines and writing ----------
    weak_heads = []
    for p in pages:
        h = (p.get("headline") or "").strip()
        if M.words(h) < 5 or GENERIC_TITLES.match(h.rstrip(".")):
            weak_heads.append(p.get("n"))
    R.add("G30", "Every headline states a claim (>= 5 words, not a label)", "writing", not weak_heads,
          f"pages {weak_heads}: headline is a label; write the takeaway as a sentence")
    text = M.text_of(pages)
    low = text.lower()
    hits = sorted({b for b in BANNED if b in low})
    R.add("G31", "No filler, buzzwords or placeholders", "writing", not hits,
          f"remove: {hits}")
    per_page_words = {p.get("n"): M.words(M.text_of(p)) for p in pages}
    mean_words = sum(per_page_words.values()) / max(len(pages), 1)
    R.add("G32", f"Density >= {T['words_page']} words/page on average", "density", mean_words >= T["words_page"],
          f"{mean_words:.0f} words/page; add proof, captions and implications (not padding); a frontier page carries ~330-470 rendered words",
          hard=False)
    airy = [n for n, w in per_page_words.items() if w < 120 and n not in (17,)]
    R.add("G33", "No airy page (< 120 words)", "density", not airy,
          f"pages {airy} are nearly empty; merge, add evidence visuals, or cut", hard=False)
    nums = M.numbers(text) / max(len(pages), 1)
    R.add("G34", f"Specificity >= {T['numbers_page']} numbers/page", "density", nums >= T["numbers_page"],
          f"{nums:.1f} numbers/page; replace adjectives with counts, dates, ranks and amounts", hard=False)

    # ---------- G40 visuals ----------
    def _has_visual(p):
        for b in p.get("blocks", []):
            if b.get("type") in M.VISUAL_BLOCKS:
                return True
            # insight cards carrying micro-charts count as the page visual (page 2 pattern)
            if b.get("type") == "cards" and sum(1 for i in b.get("items", []) if i.get("viz")) >= 2:
                return True
        return False

    no_visual = [p.get("n") for p in pages if not _has_visual(p)]
    R.add("G40", "Every page has a meaningful visual (tables/prose do not count)", "visual", not no_visual,
          f"pages {no_visual} have no visual block; add a graph, chart, timeline, photo or diagram")
    vtypes = {b.get("type") for p in pages for b in p.get("blocks", []) if b.get("type") in M.VISUAL_BLOCKS}
    R.add("G41", f">= {T['visual_types']} distinct visual types", "visual", len(vtypes) >= T["visual_types"],
          f"only {len(vtypes)} visual types {sorted(vtypes)}; repeating one diagram on every page reads as a template",
          hard=False)
    sigs = [tuple(b.get("type") for b in p.get("blocks", [])) for p in sorted(pages, key=lambda x: x.get("n", 0))]
    runs = max((sum(1 for _ in g) for _, g in __import__("itertools").groupby(sigs)), default=0)
    R.add("G42", "No 3+ consecutive pages with the same layout", "visual", runs < 3,
          "three or more pages in a row use identical block layouts; vary the argument visual", hard=False)

    # ---------- G50 exams ----------
    ident = (meta.get("identity") or {})
    istatus = ident.get("status", "UNKNOWN")
    attrs = [a for a in ident.get("attributes", []) if M.refs_in(a)]
    R.add("G50", "Identity: CONFIRMED with >= 2 evidenced attributes, or HOLD", "identity",
          (istatus == "CONFIRMED" and len(attrs) >= 2) or istatus == "HOLD",
          f"identity is {istatus} with {len(attrs)} evidenced attributes; confirm two independent attributes or HOLD")
    ba = (audit.get("exams") or {}).get("brand_authority")
    if ba:
        res = S.compute(ba, istatus)
        R.add("G51", "Brand Authority has ten rows", "exam", len(ba.get("rows", [])) == 10,
              f"{len(ba.get('rows', []))} rows; the exam is exactly ten rows")
        flags = S.calibration_flags(ba, ledger)
        hard_flags = [f for f in flags if f["level"] == "FAIL"]
        R.add("G52", "Scores match evidence strength (calibration)", "exam", not hard_flags,
              "; ".join(f"row {f['row']}: {f['msg']}" for f in hard_flags[:6]))
        soft = [f for f in flags if f["level"] == "WARN"]
        R.add("G53", "Each row records its anchor reason", "exam", not soft,
              "; ".join(f"row {f['row']}: {f['msg']}" for f in soft[:6]), hard=False)
        typed = set(int(x) for x in re.findall(r"\b(\d{1,3})\s*/\s*100\b", text))
        sep = {int(re.sub(r"\D", "", str(x.get("value", "")) or "-1") or -1)
               for x in (audit.get("exams") or {}).get("separate", []) if re.search(r"\d", str(x.get("value", "")))}
        stray = typed - {res["total"], res["known_subtotal"]} - sep
        R.add("G54", "No hand-typed score that disagrees with the arithmetic", "exam", not stray,
              f"text shows {sorted(stray)}/100 but the rows sum to {res['known_subtotal']}; let the renderer print scores")
    else:
        R.add("G51", "Brand Authority exam present", "exam", False,
              "no exams.brand_authority; score the ten rows or set every row UNKNOWN", hard=False)

    # ---------- G60 actions ----------
    R.add("G60", "Action register has 12-40 actions", "actions", 12 <= len(actions) <= 40,
          f"{len(actions)} actions; a 20-page audit ships a dated register of 12-40")
    probs = []
    for a in actions:
        aid = a.get("id", "?")
        miss = [f for f in M.ACTION_FIELDS if not a.get(f)]
        if miss:
            probs.append(f"{aid}: missing {miss}")
        if a.get("due") and not _is_date(a["due"]):
            probs.append(f"{aid}: due '{a['due']}' is not a date")
        if a.get("state") and a["state"] not in M.ACTION_STATES:
            probs.append(f"{aid}: state '{a['state']}'")
        if GENERIC_ACCEPTANCE.match((a.get("acceptance_test") or "").strip()) or M.words(a.get("acceptance_test", "")) < 4:
            probs.append(f"{aid}: acceptance test is not observable")
        al = (a.get("action") or "").lower()
        if any(b in al for b in BANNED[:5]):
            probs.append(f"{aid}: generic action")
        if ledger is not None:
            bad_ev = [e for e in (a.get("evidence") or []) if not ledger.has(e)]
            if bad_ev:
                probs.append(f"{aid}: evidence {bad_ev} not in ledger")
    R.add("G61", "Every action meets the contract", "actions", not probs, "; ".join(probs[:10]))
    dup = [k for k, v in Counter(a.get("id") for a in actions).items() if v > 1]
    R.add("G62", "Action ids are unique", "actions", not dup, f"duplicate ids {dup}")
    ex = [a.get("id") for a in actions if a.get("executor") and a["executor"] not in M.EXECUTORS]
    unset = [a.get("id") for a in actions if not a.get("executor")]
    R.add("G63", "Each action says who executes (AGENT / AGENT_AFTER_APPROVAL / HUMAN)", "actions",
          not ex and not unset, f"executor missing on {unset[:10]} or invalid on {ex[:10]}", hard=False)
    windows = {str(a.get("window")) for a in actions}
    R.add("G64", "Plan covers 7, 30, 60 and 90 days", "actions", {"7", "30", "60", "90"} <= windows,
          f"windows present {sorted(windows)}; include first-seven-day moves and 30/60/90", hard=False)
    # Changing anything the client owns or anything public about them needs the client's yes
    # on record. Only internal work (reports, the register, our own threads) runs with no gate.
    ungated = [a.get("id") for a in actions if a.get("executor") == "AGENT" and not a.get("pre_approved")
               and a.get("destination") and not INTERNAL_DEST.search(str(a.get("destination")))]
    R.add("G65", "Client-facing changes wait for the client's approval", "actions", not ungated,
          f"{ungated[:10]} change a client-facing property with no approval gate; make each AGENT_AFTER_APPROVAL "
          "and name who approves in human_gate, or set pre_approved to the recorded approval")

    # ---------- G70 privacy and claims ----------
    emails = sorted({e for e in EMAIL.findall(text) if e.lower() not in ALLOWED_EMAILS})
    R.add("G70", "No personal email addresses in the client edition", "privacy", not emails,
          f"remove {emails}")
    # A local business's own listed numbers are fair game (name-address-phone checks need them);
    # list them in brief.allowed_phones. Any other number is a private one.
    ok_phones = {_digits(p) for p in (allowed_phones or [])}
    phones = [p for p in PHONE.findall(text) if _digits(p) not in ok_phones]
    R.add("G71", "No phone numbers except the business's own listed numbers", "privacy", not phones,
          f"remove {phones[:5]}, or add the business's own listed numbers to brief.allowed_phones")
    sec = sorted(set(m.lower() for m in SECRETS.findall(text)))
    R.add("G72", "No credentials or internal agent receipts", "privacy", not sec, f"remove {sec}")
    # The brief's do-not-print list: confidential numbers, embargoed titles, private names.
    # Cheap models leaked exactly these in the Oct 25 bake-off. The message never repeats
    # the strings, because gate.json travels further than the brief.
    dnp = [s.strip().lower() for s in (do_not_print or []) if isinstance(s, str) and len(s.strip()) >= 3]
    hits_dnp = []
    for p in pages:
        pt = M.text_of(p).lower()
        hits_dnp += [(p.get("n"), j) for j, s in enumerate(dnp, 1) if s in pt]
    act_text = M.text_of(actions).lower()
    hits_dnp += [("actions", j) for j, s in enumerate(dnp, 1) if s in act_text]
    R.add("G74", "Nothing on the brief's do-not-print list appears", "privacy", not hits_dnp,
          "brief.do_not_print items found — " + ", ".join(f"item {j} on page {n}" for n, j in hits_dnp[:8])
          + "; remove them and do not paraphrase them")
    if ledger is not None:
        risky = []
        for p in (pg for pg in pages if pg.get("n") in (1, 2)):
            for blk in M.walk(p):
                t = " ".join(str(blk.get(k, "")) for k in ("title", "headline", "body", "text", "dek"))
                if BOLD_CLAIM.search(t):
                    ids = M.refs_in(blk) or M.refs_in(p)
                    strong = [i for i in ids if (ledger.get(i) or {}).get("cls") in S.INDEPENDENT]
                    if not strong:
                        risky.append(f"p{p.get('n')}: '{BOLD_CLAIM.search(t).group(0)}'")
        R.add("G73", "Bold claims on pages 1-2 rest on independent evidence", "claims", not risky,
              f"self-claimed money/rank language on the front: {sorted(set(risky))[:6]} — attribute it or cite an independent source",
              hard=False)

    # ---------- G80 agents page ----------
    install = meta.get("install_url", "https://localservicespotlight.com/install/")
    qrs = [b for p in pages for b in p.get("blocks", []) if b.get("type") == "qr"]
    R.add("G80", "Agents page QR points to the install URL", "delivery", any(b.get("url") == install for b in qrs),
          f"add a qr block with url {install} on the agents page")
    return R


def gate_render(render_report: dict, expected_qr: str | None = None) -> Report:
    """Gates on the rendered PDF, using the facts the renderer measured."""
    R = Report()
    R.add("R01", "Rendered PDF has exactly 20 pages", "render", render_report.get("pdf_pages") == 20,
          f"PDF has {render_report.get('pdf_pages')} pages")
    over = render_report.get("overflow_pages", [])
    detail = render_report.get("overflow_detail", {})
    parts = []
    for n in over:
        d = detail.get(str(n)) or {}
        if d:
            parts.append(f"page {n} runs {round(100 * d.get('over_pct', 0))}% past the page — cut about "
                         f"{d.get('cut_words', '?')} words or shrink a visual; tallest: {', '.join(d.get('tallest', []))}")
        else:
            parts.append(f"page {n} overflows")
    R.add("R02", "No page overflows (text cut off)", "render", not over,
          "; ".join(parts) + ". Never shrink type to fit: cut words, or move a block to a later page")
    fills = render_report.get("fill", {})
    airy = sorted((int(k), v) for k, v in fills.items() if v < 0.55)
    R.add("R03", "Pages are at least 55% full", "render", len(airy) <= 1,
          "pages " + ", ".join(f"{n} ({round(100 * v)}% full)" for n, v in airy)
          + " look empty at thumbnail size; add an evidence table, a stat strip or a taller visual (never filler)",
          hard=False)
    R.add("R04", "PDF carries clickable source links", "render", render_report.get("links", 0) >= 30,
          f"only {render_report.get('links', 0)} link annotations", hard=False)
    if expected_qr:
        R.add("R05", "QR decodes to the install URL", "render", render_report.get("qr_decoded") == expected_qr,
              f"QR decoded to {render_report.get('qr_decoded')!r}")
    return R
