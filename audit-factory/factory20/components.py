"""Typed blocks -> HTML/SVG. Deterministic: same audit.json, same pixels.

Each function takes the block dict and a context (ledger lookups, palette, actions) and
returns an HTML string. Models never write markup; they choose blocks and fill fields.
"""
from __future__ import annotations

import html
import math
import re

E = html.escape
STATE_CLASS = {"OBSERVED": "obs", "INFERRED": "inf", "UNKNOWN": "unk", "PROPOSED": "inf", "REPORTED": "inf"}


# ---------------------------------------------------------------- inline helpers
def md(s: str) -> str:
    """Escape, then **accent** and _muted_ spans. Nothing else is interpreted."""
    s = E(s or "")
    s = re.sub(r"\*\*(.+?)\*\*", r'<b class="acc">\1</b>', s)
    s = re.sub(r"(?<![A-Za-z0-9])_(.+?)_(?![A-Za-z0-9])", r'<span class="mut">\1</span>', s)
    return s


def chips(ids, ctx, cls="ev") -> str:
    if not ids:
        return ""
    if isinstance(ids, str):
        ids = [ids]
    out = []
    for i in ids:
        row = ctx.ledger.get(i) if ctx.ledger else None
        url = (row or {}).get("url", "")
        if url.startswith("http"):
            out.append(f'<a class="{cls}" href="{E(url)}">{E(i)}</a>')
        else:
            out.append(f'<span class="{cls}">{E(i)}</span>')
    return '<span class="chips">' + "".join(out) + "</span>"


def act_chips(ids) -> str:
    if not ids:
        return ""
    if isinstance(ids, str):
        ids = [ids]
    return '<span class="chips">' + "".join(f'<span class="act">{E(i)}</span>' for i in ids) + "</span>"


def badge(state: str) -> str:
    s = (state or "UNKNOWN").upper()
    return f'<span class="badge b-{STATE_CLASS.get(s, "unk")}">{E(s)}</span>'


def _span(b, default=12) -> str:
    return f'style="grid-column: span {int(b.get("span", default))}"'


def _title(b) -> str:
    t = b.get("title")
    return f'<div class="btitle">{md(t)}</div>' if t else ""


def _caption(b, ctx) -> str:
    c = b.get("caption")
    ev = chips(b.get("evidence"), ctx)
    if not c and not ev:
        return ""
    return f'<div class="cap">{md(c or "")} {ev}</div>'


# ---------------------------------------------------------------- text blocks
def prose(b, ctx):
    paras = b.get("text", "")
    paras = paras if isinstance(paras, list) else [paras]
    body = "".join(f"<p>{md(p)}</p>" for p in paras)
    return f'<div class="blk prose" {_span(b)}>{_title(b)}{body}{chips(b.get("evidence"), ctx)}</div>'


def _micro(v, ctx):
    """Micro visual inside an insight card: pair of numbers drawn to scale, or a strip."""
    if not v:
        return ""
    if v.get("type") == "pair":
        a, c = v.get("a", {}), v.get("b", {})
        av, cv = float(a.get("value") or 0), float(c.get("value") or 0)
        mx = max(av, cv, 1e-9)
        wa, wc = max(2, 100 * av / mx), max(2, 100 * cv / mx)
        return (f'<div class="pair"><div class="pr"><span class="pl">{md(a.get("label", ""))}</span>'
                f'<span class="pb" style="width:{wa:.1f}%"></span><span class="pv">{E(str(a.get("display", a.get("value", ""))))}</span></div>'
                f'<div class="pr"><span class="pl">{md(c.get("label", ""))}</span>'
                f'<span class="pb alt" style="width:{wc:.1f}%"></span><span class="pv">{E(str(c.get("display", c.get("value", ""))))}</span></div></div>')
    if v.get("type") == "doors":
        return '<div class="doors">' + "".join(
            f'<span class="door {"ok" if d.get("ok") else "no"}">{md(d.get("label", ""))}</span>'
            for d in v.get("items", [])) + "</div>"
    return ""


def cards(b, ctx):
    items = b.get("items", [])
    cols = int(b.get("cols", 2))
    out = []
    for k, c in enumerate(items, 1):
        so = f'<div class="so"><b>So:</b> {md(c.get("so", ""))}</div>' if c.get("so") else ""
        num = c.get("n", k) if b.get("numbered", True) else ""
        out.append(
            f'<div class="card">'
            f'<div class="chead">{badge(c.get("badge", "UNKNOWN"))}'
            f'<span class="cnum">{E(str(num))}</span></div>'
            f'<div class="ctitle">{md(c.get("title", ""))}</div>'
            f'<div class="cbody">{md(c.get("body", ""))}</div>'
            f'{_micro(c.get("viz"), ctx)}{so}'
            f'<div class="cfoot">{chips(c.get("evidence"), ctx)}{act_chips(c.get("actions"))}</div></div>')
    return (f'<div class="blk cards" {_span(b)}>{_title(b)}'
            f'<div class="cgrid" style="grid-template-columns: repeat({cols}, 1fr)">{"".join(out)}</div></div>')


def stat_strip(b, ctx):
    items = b.get("items", [])
    tiles = "".join(
        f'<div class="stat"><div class="sv">{E(str(i.get("value", "")))}</div>'
        f'<div class="sl">{md(i.get("label", ""))}</div>'
        f'<div class="ss">{md(i.get("sub", ""))} {chips(i.get("evidence"), ctx)}</div></div>' for i in items)
    return (f'<div class="blk stats" {_span(b)}>{_title(b)}'
            f'<div class="sgrid" style="grid-template-columns: repeat({max(len(items), 1)}, 1fr)">{tiles}</div></div>')


def finding_map(b, ctx):
    rows = "".join(
        f'<li><span class="fn">{k}</span><div><div class="ft">{md(i.get("title", ""))}</div>'
        f'<div class="fp">{md(i.get("proof", ""))} {chips(i.get("evidence"), ctx)}</div></div></li>'
        for k, i in enumerate(b.get("items", []), 1))
    return f'<div class="blk fmap" {_span(b)}>{_title(b) or "<div class=btitle>Finding map — what a buyer’s diligence finds first</div>"}<ol>{rows}</ol></div>'


def table(b, ctx):
    cols = b.get("columns", [])
    ev_col = {i for i, c in enumerate(cols) if str(c).lower() in ("evidence", "refs", "source ids", "evidence ids")}
    st_col = {i for i, c in enumerate(cols) if str(c).lower() in ("state", "status")}
    head = "".join(f"<th>{md(str(c))}</th>" for c in cols)
    body = []
    for r in b.get("rows", []):
        cells = []
        for i, v in enumerate(r):
            if i in ev_col:
                ids = v if isinstance(v, list) else re.split(r"[,\s]+", str(v).strip())
                cells.append(f"<td>{chips([x for x in ids if x], ctx)}</td>")
            elif i in st_col and str(v).upper() in STATE_CLASS:
                cells.append(f"<td>{badge(str(v))}</td>")
            else:
                cells.append(f"<td>{md(str(v))}</td>")
        body.append("<tr>" + "".join(cells) + "</tr>")
    return (f'<div class="blk tbl{" compact" if b.get("compact") else ""}" {_span(b)}>{_title(b)}<table><thead><tr>{head}</tr></thead>'
            f'<tbody>{"".join(body)}</tbody></table>{_caption(b, ctx)}</div>')


def callout(b, ctx):
    tone = b.get("tone", "info")
    return (f'<div class="blk callout t-{E(tone)}" {_span(b)}><div class="ctl">{md(b.get("title", ""))}</div>'
            f'<div class="cbd">{md(b.get("body", ""))}</div>{chips(b.get("evidence"), ctx)}{act_chips(b.get("actions"))}</div>')


def quote(b, ctx):
    return (f'<div class="blk quote" {_span(b)}><div class="q">“{md(b.get("text", ""))}”</div>'
            f'<div class="qa">— {md(b.get("who", ""))} {chips(b.get("evidence"), ctx)}</div></div>')


def checklist(b, ctx):
    rows = "".join(
        f'<div class="ck"><span class="cks s-{E(str(i.get("state", "UNKNOWN")).lower())}">{E(str(i.get("state", "UNKNOWN")))}</span>'
        f'<span>{md(i.get("label", ""))}</span></div>' for i in b.get("items", []))
    return f'<div class="blk checklist" {_span(b)}>{_title(b)}{rows}</div>'


def conflicts(b, ctx):
    rows = []
    for i in b.get("items", []):
        vals = "".join(f'<div class="cv">{md(v.get("value", ""))} <span class="mut">({md(v.get("source", ""))})</span></div>'
                       for v in i.get("values", []))
        rows.append(f'<div class="cf"><div class="cm">{md(i.get("metric", ""))} {chips(i.get("evidence"), ctx)}</div>'
                    f'{vals}<div class="cr"><b>Present as:</b> {md(i.get("resolution", ""))}</div></div>')
    return f'<div class="blk conflicts" {_span(b)}>{_title(b)}{"".join(rows)}</div>'


# ---------------------------------------------------------------- visual blocks
def photo(b, ctx):
    src = b.get("src", "")
    ok = ctx.asset_ok(src)
    if ok:
        img = f'<img src="{E(ctx.asset_url(src))}" alt="{E(b.get("alt", b.get("caption", "")))}">'
    else:
        ctx.missing_assets.append(src or "(no src)")
        img = f'<div class="noimg">IMAGE NEEDED<br><span>{E(src or b.get("caption", ""))}</span></div>'
    h = int(b.get("height", 150))
    return (f'<figure class="blk photo" {_span(b, 4)}><div class="frame" style="height:{h}px">{img}</div>'
            f'{_caption(b, ctx)}</figure>')


screenshot = photo


CONTENT_W, GAP = 732, 14


def W(b, default=12) -> int:
    """Pixel width of a block for its grid span, so SVG text renders at its true size."""
    sp = max(1, min(12, int(b.get("span", default))))
    col = (CONTENT_W - 11 * GAP) / 12
    return int(round(sp * col + (sp - 1) * GAP))


def _svg(w, h, inner, cls="viz"):
    return f'<svg class="{cls}" viewBox="0 0 {w} {h}" width="100%" preserveAspectRatio="xMidYMid meet">{inner}</svg>'


def bars(b, ctx):
    items = b.get("items", [])
    Wd = W(b); rowh = 27; lab = min(200, int(Wd * 0.38))
    nums = [float(i["value"]) for i in items if isinstance(i.get("value"), (int, float))]
    mx = float(b.get("max") or (max(nums) if nums else 1)) or 1
    g = []
    for k, i in enumerate(items):
        y = 6 + k * rowh
        g.append(f'<text x="{lab - 8}" y="{y + 16}" class="tl" text-anchor="end">{E(str(i.get("label", ""))[:int(lab / 5.6)])}</text>')
        v = i.get("value")
        if isinstance(v, (int, float)):
            w = max(2.0, (Wd - lab - 74) * float(v) / mx)
            cls = "bar alt" if i.get("highlight") else "bar"
            g.append(f'<rect x="{lab}" y="{y + 3}" width="{w:.1f}" height="{rowh - 8}" class="{cls}" rx="2"/>')
            g.append(f'<text x="{lab + w + 6}" y="{y + 16}" class="tv">{E(str(i.get("display", v)))}</text>')
        else:
            g.append(f'<rect x="{lab}" y="{y + 3}" width="{Wd - lab - 74}" height="{rowh - 8}" class="hatch" rx="2"/>')
            g.append(f'<text x="{lab + 8}" y="{y + 16}" class="tu">UNKNOWN — not measured</text>')
    H = 12 + len(items) * rowh
    return f'<div class="blk bars" {_span(b)}>{_title(b)}{_svg(Wd, H, "".join(g))}{_caption(b, ctx)}</div>'


def heatmap(b, ctx):
    rows = ctx.exam_rows() if b.get("auto", True) and not b.get("rows") else b.get("rows", [])
    Wd = W(b, 12) - 150
    rowh, lab = 27, 230
    cell = max(14, int((Wd - lab - 140) / 10) - 3)
    g = []
    for k, r in enumerate(rows):
        y = 4 + k * rowh
        g.append(f'<text x="{lab - 8}" y="{y + 17}" class="tl" text-anchor="end">{r.get("n", k + 1)}. {E(str(r.get("name", ""))[:38])}</text>')
        s_ = r.get("score")
        for c in range(10):
            x = lab + c * (cell + 3)
            if isinstance(s_, (int, float)):
                g.append(f'<rect x="{x}" y="{y + 4}" width="{cell}" height="{rowh - 9}" class="hc{" on" if c < s_ else ""}" rx="2"/>')
            else:
                g.append(f'<rect x="{x}" y="{y + 4}" width="{cell}" height="{rowh - 9}" class="hatch" rx="2"/>')
        xs = lab + 10 * (cell + 3) + 8
        g.append(f'<text x="{xs}" y="{y + 18}" class="tvb">{E(str(s_ if isinstance(s_, (int, float)) else "UNKNOWN"))}</text>')
        ev = r.get("evidence") or []
        g.append(f'<text x="{xs + 30}" y="{y + 17}" class="tid">{E(" ".join(ev[:3]))}</text>')
    H = 10 + len(rows) * rowh
    res = ctx.exam_result()
    tot = (f'<div class="examtot"><div class="et-v">{_exam_figure(res)}</div><div class="et-s">{E(res["verdict"])}</div>'
           f'<div class="et-p">Pass line {res["pass_line"]} · ten equal rows · never averaged with other exams</div></div>') if res else ""
    return f'<div class="blk heatmap" {_span(b)}>{_title(b)}<div class="hmwrap">{_svg(Wd, H, "".join(g))}{tot}</div>{_caption(b, ctx)}</div>'


def _exam_figure(res: dict) -> str:
    """The big number in the exam box. Only a complete exam prints a score out of 100: an
    incomplete one prints what it knows out of what it checked, and identity HOLD prints none."""
    if res["total"] is not None:
        return f'{E(str(res["total"]))}<span>/100</span>'
    if res["status"] == "INCOMPLETE":
        return f'{E(str(res["known_subtotal"]))}<span> of {10 * res["known_rows"]} checked</span>'
    return '\u2014<span> no score</span>'


def scorebar(b, ctx):
    items = b.get("items") or ctx.separate_exams()
    tiles = "".join(
        f'<div class="sx"><div class="sxn">{md(i.get("name", ""))}</div><div class="sxv">{E(str(i.get("value", "UNKNOWN")))}</div>'
        f'<div class="sxd">{md(i.get("note", ""))} {chips(i.get("evidence"), ctx)}</div></div>' for i in items)
    return f'<div class="blk scorebar" {_span(b)}>{_title(b) or "<div class=btitle>Separate exams — never averaged</div>"}<div class="sxg">{tiles}</div></div>'


EDGE_STYLE = {"repeat": "", "collab": "", "interview": "6 3", "testimonial": "2 3", "employment": "",
              "co-presence": "1 4", "proposed": "8 5", "conflict": "3 3", "link": ""}


def graph(b, ctx):
    nodes = b.get("nodes", [])
    center = b.get("center") or {"id": "center", "label": ctx.subject}
    Wd = W(b, 12)
    H = int(b.get("height", 330))
    cx, cy = Wd / 2, H / 2
    pos = {center.get("id", "center"): (cx, cy)}
    n = len(nodes)
    inner = nodes if n <= 10 else nodes[: (n + 1) // 2]
    outer = [] if n <= 10 else nodes[(n + 1) // 2:]
    for ring, rset in ((0, inner), (1, outer)):
        rx, ry = (Wd * 0.34, H * 0.37) if ring == 0 else (Wd * 0.46, H * 0.46)
        for k, nd in enumerate(rset):
            a = -math.pi / 2 + 2 * math.pi * k / max(len(rset), 1) + (0.3 if ring else 0)
            pos[nd.get("id")] = (cx + rx * math.cos(a), cy + ry * math.sin(a))
    g = []
    for e in b.get("edges", []):
        f, t = pos.get(e.get("from")), pos.get(e.get("to"))
        if not f or not t:
            continue
        dash = EDGE_STYLE.get(e.get("type", "link"), "")
        cls = "edge conflict" if e.get("type") == "conflict" else ("edge proposed" if e.get("type") == "proposed" else "edge")
        g.append(f'<line x1="{f[0]:.1f}" y1="{f[1]:.1f}" x2="{t[0]:.1f}" y2="{t[1]:.1f}" class="{cls}" stroke-dasharray="{dash}"/>')
        if e.get("label"):
            mx, my = (f[0] * 0.45 + t[0] * 0.55), (f[1] * 0.45 + t[1] * 0.55)
            g.append(f'<rect x="{mx - 3.2 * len(str(e["label"])[:22]) - 3:.1f}" y="{my - 8:.1f}" width="{6.4 * len(str(e["label"])[:22]) + 6:.1f}" height="11" rx="2" class="elbg"/>')
            g.append(f'<text x="{mx:.1f}" y="{my:.1f}" class="el" text-anchor="middle">{E(str(e["label"])[:22])}</text>')
    for nd in [center] + nodes:
        x, y = pos.get(nd.get("id"), (cx, cy))
        st = STATE_CLASS.get(str(nd.get("state", "OBSERVED")).upper(), "obs")
        is_c = nd is center
        lines = _wrap(str(nd.get("label", "")), 18 if not is_c else 16)[:3]
        bw = max(len(L) for L in lines) * (6.2 if not is_c else 7.4) + 18
        bh = 12 + 12.5 * len(lines) + (11 if nd.get("sub") else 0)
        x = min(max(x, bw / 2 + 2), Wd - bw / 2 - 2)
        y = min(max(y, bh / 2 + 2), H - bh / 2 - 2)
        g.append(f'<rect x="{x - bw / 2:.1f}" y="{y - bh / 2:.1f}" width="{bw:.1f}" height="{bh:.1f}" rx="5" class="node n-{st}{" center" if is_c else ""}"/>')
        for k, L in enumerate(lines):
            g.append(f'<text x="{x:.1f}" y="{y - bh / 2 + 16 + 12.5 * k:.1f}" class="nl{" cl" if is_c else ""}" text-anchor="middle">{E(L)}</text>')
        if nd.get("sub"):
            g.append(f'<text x="{x:.1f}" y="{y + bh / 2 - 6:.1f}" class="ns" text-anchor="middle">{E(str(nd["sub"])[:30])}</text>')
    legend = ('<div class="legend"><span class="lg obs">observed</span><span class="lg inf">inferred</span>'
              '<span class="lg unk">unknown / namesake</span><span class="lg ln">— repeat or work tie</span>'
              '<span class="lg ln">‒ ‒ interview</span><span class="lg ln">··· co-presence, not a relationship</span>'
              '<span class="lg ln">gold — proposed</span></div>')
    return f'<div class="blk graph" {_span(b)}>{_title(b)}{_svg(Wd, H, "".join(g))}{legend}{_caption(b, ctx)}</div>'


def _wrap(s, n):
    words, lines, cur = s.split(), [], ""
    for w_ in words:
        if len(cur) + len(w_) + 1 > n and cur:
            lines.append(cur)
            cur = w_
        else:
            cur = (cur + " " + w_).strip()
    if cur:
        lines.append(cur)
    return lines or [""]


def timeline(b, ctx):
    ev = b.get("events", [])
    Wd, H = W(b), int(b.get("height", 190))
    n = max(len(ev), 1)
    g = [f'<line x1="16" y1="{H / 2}" x2="{Wd - 16}" y2="{H / 2}" class="axis"/>']
    for k, e in enumerate(ev):
        x = 44 + (Wd - 88) * (k / (n - 1) if n > 1 else 0.5)
        up = k % 2 == 0
        st = STATE_CLASS.get(str(e.get("state", "OBSERVED")).upper(), "obs")
        g.append(f'<line x1="{x:.1f}" y1="{H / 2}" x2="{x:.1f}" y2="{H / 2 + (-18 if up else 18)}" class="grid"/>')
        g.append(f'<circle cx="{x:.1f}" cy="{H / 2}" r="6" class="dot n-{st}"/>')
        y0 = H / 2 - 64 if up else H / 2 + 32
        g.append(f'<text x="{x:.1f}" y="{y0:.1f}" class="td" text-anchor="middle">{E(str(e.get("date", "")))}</text>')
        for j, L in enumerate(_wrap(str(e.get("label", "")), 22)[:3]):
            g.append(f'<text x="{x:.1f}" y="{y0 + 13 + 11.5 * j:.1f}" class="tl2" text-anchor="middle">{E(L)}</text>')
    return f'<div class="blk timeline" {_span(b)}>{_title(b)}{_svg(Wd, H, "".join(g))}{_caption(b, ctx)}</div>'


def swimlane(b, ctx):
    items = b.get("items") or ctx.plan_items()
    lanes = []
    for it in items:
        if it["lane"] not in lanes:
            lanes.append(it["lane"])
    horizon = int(b.get("horizon_days", 90))
    Wd, lab, laneh = W(b), 132, 34
    H = 30 + laneh * max(len(lanes), 1)
    x = lambda d: lab + (Wd - lab - 12) * min(d, horizon) / horizon
    g = []
    for li in range(len(lanes)):
        if li % 2 == 0:
            g.append(f'<rect x="0" y="{22 + li * laneh}" width="{Wd}" height="{laneh}" class="laneband"/>')
    for d, name in ((0, "Today"), (7, "Day 7"), (30, "Day 30"), (60, "Day 60"), (90, "Day 90")):
        g.append(f'<line x1="{x(d):.1f}" y1="16" x2="{x(d):.1f}" y2="{H}" class="grid"/>')
        g.append(f'<text x="{x(d):.1f}" y="12" class="td" text-anchor="middle">{name}</text>')
    for li, ln in enumerate(lanes):
        y = 22 + li * laneh
        g.append(f'<text x="{lab - 8}" y="{y + 21}" class="tl" text-anchor="end">{E(ln[:22])}</text>')
        row = [i for i in items if i["lane"] == ln]
        for k, it in enumerate(row):
            s0, e0 = it.get("start", 0), max(it.get("end", 7), it.get("start", 0) + 4)
            yy = y + 4 + (k % 2) * 13
            g.append(f'<rect x="{x(s0):.1f}" y="{yy}" width="{max(x(e0) - x(s0), 30):.1f}" height="12" rx="2" class="bar{" alt" if k % 2 else ""}"/>')
            g.append(f'<text x="{x(s0) + 4:.1f}" y="{yy + 9}" class="sl2{" dk" if k % 2 else ""}">{E(str(it.get("id", "")))}</text>')
    return f'<div class="blk swim" {_span(b)}>{_title(b)}{_svg(Wd, H, "".join(g))}{_caption(b, ctx)}</div>'


def matrix(b, ctx):
    Wd, H, p = W(b), int(b.get("height", 300)), 36
    g = [f'<rect x="{p}" y="8" width="{Wd - p - 8}" height="{H - p - 8}" class="mx"/>',
         f'<line x1="{(p + Wd - 8) / 2}" y1="8" x2="{(p + Wd - 8) / 2}" y2="{H - p}" class="grid"/>',
         f'<line x1="{p}" y1="{(H - p + 8) / 2}" x2="{Wd - 8}" y2="{(H - p + 8) / 2}" class="grid"/>',
         f'<text x="{(p + Wd) / 2}" y="{H - 12}" class="tl" text-anchor="middle">{E(b.get("x_label", ""))} →</text>',
         f'<text x="13" y="{(H - p) / 2}" class="tl" transform="rotate(-90 13 {(H - p) / 2})" text-anchor="middle">{E(b.get("y_label", ""))} →</text>']
    for k, q in enumerate(b.get("quadrants", [])[:4]):
        qx = p + 10 if k in (0, 2) else (p + Wd) / 2 + 10
        qy = 26 if k in (0, 1) else (H - p) / 2 + 22
        g.append(f'<text x="{qx}" y="{qy}" class="ql">{E(q)}</text>')
    for pt in b.get("points", []):
        px = p + 8 + (Wd - p - 24) * float(pt.get("x", 0.5))
        py = 16 + (H - p - 28) * (1 - float(pt.get("y", 0.5)))
        st = STATE_CLASS.get(str(pt.get("state", "OBSERVED")).upper(), "obs")
        right = px < Wd * 0.62
        g.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="7" class="dot n-{st}"/>')
        g.append(f'<text x="{px + (11 if right else -11):.1f}" y="{py + 4:.1f}" class="tl2b" text-anchor="{"start" if right else "end"}">{E(str(pt.get("label", ""))[:30])}</text>')
    return f'<div class="blk matrix" {_span(b)}>{_title(b)}{_svg(Wd, H, "".join(g))}{_caption(b, ctx)}</div>'


def ladder(b, ctx):
    levels = b.get("levels") or ["0 none", "1 present", "2 visible", "3 credible", "4 preferred", "5 leading"]
    markers = b.get("markers", [])
    Wd, lab, rowh = W(b), 230, 32
    H = 30 + rowh * len(markers)
    step = (Wd - lab - 30) / (len(levels) - 1)
    g = []
    for i, L in enumerate(levels):
        xx = lab + i * step
        g.append(f'<line x1="{xx:.1f}" y1="18" x2="{xx:.1f}" y2="{H}" class="grid"/>')
        g.append(f'<text x="{xx:.1f}" y="12" class="td" text-anchor="middle">{E(L)}</text>')
    for k, m in enumerate(markers):
        y = 28 + k * rowh
        g.append(f'<text x="{lab - 10}" y="{y + 11}" class="tl" text-anchor="end">{E(str(m.get("label", ""))[:40])}</text>')
        a, t = float(m.get("level", 0)), float(m.get("target", m.get("level", 0)))
        g.append(f'<line x1="{lab + a * step:.1f}" y1="{y + 7}" x2="{lab + t * step:.1f}" y2="{y + 7}" class="gap"/>')
        g.append(f'<circle cx="{lab + a * step:.1f}" cy="{y + 7}" r="7" class="dot n-obs"/>')
        g.append(f'<circle cx="{lab + t * step:.1f}" cy="{y + 7}" r="7" class="ring"/>')
    return (f'<div class="blk ladder" {_span(b)}>{_title(b)}{_svg(Wd, H, "".join(g))}'
            f'<div class="legend"><span class="lg obs">today</span><span class="lg ring">90-day target</span></div>{_caption(b, ctx)}</div>')


def flow(b, ctx):
    steps = b.get("steps", [])
    cells = []
    for k, s_ in enumerate(steps):
        st = STATE_CLASS.get(str(s_.get("state", "")).upper(), "")
        cells.append(f'<div class="fstep {("s-" + st) if st else ""}"><div class="fl">{md(s_.get("label", ""))}</div>'
                     f'<div class="fd">{md(s_.get("detail", ""))}</div>'
                     f'<div class="fs">{badge(s_["state"]) if s_.get("state") else ""} {chips(s_.get("evidence"), ctx)}</div></div>')
        if k < len(steps) - 1:
            cells.append('<div class="farrow">→</div>')
    return f'<div class="blk flow" {_span(b)}>{_title(b)}<div class="frow">{"".join(cells)}</div>{_caption(b, ctx)}</div>'


def topic_wheel(b, ctx):
    topics = b.get("topics", [])
    tot = sum(float(t.get("weight", 1)) for t in topics) or 1
    Wd = W(b)
    r = min(108, Wd * 0.2)
    ri = r * 0.56
    cx, cy = r + 10, r + 10
    H = max(2 * r + 20, 30 + 26 * len(topics))
    a0, g = -math.pi / 2, []
    for k, t in enumerate(topics):
        frac = float(t.get("weight", 1)) / tot
        a1 = a0 + 2 * math.pi * frac
        large = 1 if frac > 0.5 else 0
        pts = [(cx + r * math.cos(a0), cy + r * math.sin(a0)), (cx + r * math.cos(a1), cy + r * math.sin(a1)),
               (cx + ri * math.cos(a1), cy + ri * math.sin(a1)), (cx + ri * math.cos(a0), cy + ri * math.sin(a0))]
        g.append(f'<path d="M{pts[0][0]:.1f},{pts[0][1]:.1f} A{r:.1f},{r:.1f} 0 {large} 1 {pts[1][0]:.1f},{pts[1][1]:.1f} '
                 f'L{pts[2][0]:.1f},{pts[2][1]:.1f} A{ri:.1f},{ri:.1f} 0 {large} 0 {pts[3][0]:.1f},{pts[3][1]:.1f} Z" class="seg s{k % 6}"/>')
        lx = 2 * r + 34
        g.append(f'<rect x="{lx}" y="{16 + k * 26}" width="13" height="13" class="seg s{k % 6}"/>')
        g.append(f'<text x="{lx + 19}" y="{27 + k * 26}" class="tl2b">{E(str(t.get("label", ""))[:44])}</text>')
        g.append(f'<text x="{Wd - 6}" y="{27 + k * 26}" class="tvb" text-anchor="end">{E(str(t.get("weight", "")))}</text>')
        a0 = a1
    g.append(f'<text x="{cx}" y="{cy + 4}" class="tvb" text-anchor="middle">{E(str(b.get("center_label", "topics")))}</text>')
    return f'<div class="blk wheel" {_span(b)}>{_title(b)}{_svg(Wd, H, "".join(g))}{_caption(b, ctx)}</div>'


donut = topic_wheel


def qr(b, ctx):
    url = b.get("url", "")
    try:
        import segno
        svg = segno.make(url, error="m").svg_inline(scale=4, border=3, dark="#111111", omitsize=True)
    except Exception:  # segno missing: the printed URL still works
        svg = '<div class="noimg">QR</div>'
    return (f'<div class="blk qr" {_span(b, 4)}><div class="qrimg">{svg}</div>'
            f'<div class="qrurl"><a href="{E(url)}">{E(url)}</a></div><div class="cap">{md(b.get("caption", "Scan to install the agents"))}</div></div>')


RENDERERS = {
    "prose": prose, "cards": cards, "stat_strip": stat_strip, "finding_map": finding_map, "table": table,
    "callout": callout, "quote": quote, "checklist": checklist, "conflicts": conflicts, "photo": photo,
    "screenshot": screenshot, "bars": bars, "heatmap": heatmap, "scorebar": scorebar, "graph": graph,
    "timeline": timeline, "swimlane": swimlane, "matrix": matrix, "ladder": ladder, "flow": flow,
    "topic_wheel": topic_wheel, "donut": donut, "qr": qr,
}


def render_block(b, ctx) -> str:
    fn = RENDERERS.get(b.get("type"))
    if not fn:
        return f'<div class="blk callout t-warn" style="grid-column: span 12">Unknown block type {E(str(b.get("type")))}</div>'
    return fn(b, ctx)
