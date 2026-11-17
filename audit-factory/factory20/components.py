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
        wa = 0 if av == 0 else max(2, 100 * av / mx)
        wc = 0 if cv == 0 else max(2, 100 * cv / mx)
        return (f'<div class="pair"><div class="pr"><span class="pl">{md(a.get("label", ""))}</span>'
                f'<span class="pb" style="width:{wa:.1f}%"></span><span class="pv">{E(str(a.get("display", a.get("value", ""))))}</span></div>'
                f'<div class="pr"><span class="pl">{md(c.get("label", ""))}</span>'
                f'<span class="pb alt" style="width:{wc:.1f}%"></span><span class="pv">{E(str(c.get("display", c.get("value", ""))))}</span></div></div>')
    if v.get("type") == "doors":
        return '<div class="doors">' + "".join(
            f'<span class="door {"ok" if d.get("ok") is True else ("warn" if d.get("ok") == "warn" else "no")}">{md(d.get("label", ""))}</span>'
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
            w = 0.0 if float(v) == 0 else max(2.0, (Wd - lab - 74) * float(v) / mx)
            cls = "bar alt" if i.get("highlight") else "bar"
            if w > 0:
                g.append(f'<rect x="{lab}" y="{y + 3}" width="{w:.1f}" height="{rowh - 8}" class="{cls}" rx="2"/>')
            g.append(f'<text x="{lab + w + 6}" y="{y + 16}" class="tv">{E(str(i.get("display", v)))}</text>')
        else:
            g.append(f'<rect x="{lab}" y="{y + 3}" width="{Wd - lab - 74}" height="{rowh - 8}" class="hatch" rx="2"/>')
            g.append(f'<text x="{lab + 8}" y="{y + 16}" class="tu">{E(str(i.get("display") or "UNKNOWN — not measured"))}</text>')
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
        g.append(f'<text x="{lab - 8}" y="{y + 17}" class="tl" text-anchor="end">{r.get("n", k + 1)}. {E(str(r.get("label") or r.get("name", ""))[:38])}</text>')
        s_ = r.get("score")
        for c in range(10):
            x = lab + c * (cell + 3)
            if isinstance(s_, (int, float)):
                g.append(f'<rect x="{x}" y="{y + 4}" width="{cell}" height="{rowh - 9}" class="hc{" on" if c < s_ else ""}" rx="2"/>')
            else:
                g.append(f'<rect x="{x}" y="{y + 4}" width="{cell}" height="{rowh - 9}" class="hatch" rx="2"/>')
        xs = lab + 10 * (cell + 3) + 8
        sv = (f"{s_}*" if r.get("provisional") else str(s_)) if isinstance(s_, (int, float)) else "UNKNOWN"
        g.append(f'<text x="{xs}" y="{y + 18}" class="tvb">{E(sv)}</text>')
        ev = r.get("evidence") or []
        g.append(f'<text x="{xs + 30}" y="{y + 17}" class="tid">{E(" ".join(ev[:3]))}</text>')
    H = 10 + len(rows) * rowh
    res = ctx.exam_result()
    tot = (f'<div class="examtot"><div class="et-v">{E(str(res["total"] if res["total"] is not None else res["known_subtotal"]))}'
           f'<span>/100</span></div><div class="et-s">{E(res["verdict"])}</div>'
           f'<div class="et-p">Pass line {res["pass_line"]} · ten equal rows · never averaged with other exams</div></div>') if res else ""
    return f'<div class="blk heatmap" {_span(b)}>{_title(b)}<div class="hmwrap">{_svg(Wd, H, "".join(g))}{tot}</div>{_caption(b, ctx)}</div>'


def scorebar(b, ctx):
    items = b.get("items") or ctx.separate_exams()
    tiles = "".join(
        f'<div class="sx"><div class="sxn">{md(i.get("name", ""))}</div><div class="sxv">{E(str(i.get("value", "UNKNOWN")))}</div>'
        f'<div class="sxd">{md(i.get("note", ""))} {chips(i.get("evidence"), ctx)}</div></div>' for i in items)
    return f'<div class="blk scorebar" {_span(b)}>{_title(b) or "<div class=btitle>Separate exams — never averaged</div>"}<div class="sxg">{tiles}</div></div>'


EDGE_STYLE = {"repeat": "", "collab": "", "interview": "6 3", "testimonial": "0.1 6", "employment": "",
              "co-presence": "1 4", "proposed": "8 5", "conflict": "3 3", "link": ""}


def graph(b, ctx):
    """Radial graph. Boxes are pushed apart until none overlap (fix 2026-11-10), edge labels sit on the
    part of the edge outside both boxes, 'repeat' edges draw thick, and the legend lists only what is drawn."""
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
        rx, ry = (Wd * 0.36, H * 0.39) if ring == 0 else (Wd * 0.46, H * 0.46)
        for k, nd in enumerate(rset):
            a = -math.pi / 2 + 2 * math.pi * k / max(len(rset), 1) + (0.3 if ring else 0)
            pos[nd.get("id")] = (cx + rx * math.cos(a), cy + ry * math.sin(a))
    box = {}
    for nd in [center] + nodes:
        is_c = nd is center
        lines = _wrap(str(nd.get("label", "")), 18 if not is_c else 16)[:3]
        sub = str(nd.get("sub") or "")[:34]
        bw = max(max(len(L) for L in lines) * (6.2 if not is_c else 7.4), len(sub) * 4.3) + 18
        bh = 12 + 12.5 * len(lines) + (11 if sub else 0)
        x, y = pos.get(nd.get("id"), (cx, cy))
        box[nd.get("id")] = [x, y, bw, bh, lines, sub, is_c, nd]
    def clamp(bx):
        bx[0] = min(max(bx[0], bx[2] / 2 + 2), Wd - bx[2] / 2 - 2)
        bx[1] = min(max(bx[1], bx[3] / 2 + 2), H - bx[3] / 2 - 2)
    for bx in box.values():
        clamp(bx)
    ids = list(box)
    for _ in range(200):
        moved = False
        for i in range(len(ids)):
            for j in range(i + 1, len(ids)):
                A_, B_ = box[ids[i]], box[ids[j]]
                ox = (A_[2] + B_[2]) / 2 + 6 - abs(A_[0] - B_[0])
                oy = (A_[3] + B_[3]) / 2 + 5 - abs(A_[1] - B_[1])
                if ox <= 0 or oy <= 0:
                    continue
                moved = True
                wa, wb = (0.0, 1.0) if A_[6] else ((1.0, 0.0) if B_[6] else (0.5, 0.5))
                first_x = ox / max(A_[2] + B_[2], 1) < oy / max(A_[3] + B_[3], 1)
                for axis in ((0, 1) if first_x else (1, 0)):
                    ox = (A_[2] + B_[2]) / 2 + 6 - abs(A_[0] - B_[0])
                    oy = (A_[3] + B_[3]) / 2 + 5 - abs(A_[1] - B_[1])
                    if ox <= 0 or oy <= 0:
                        break
                    if axis == 0:
                        d = ox if A_[0] >= B_[0] else -ox
                        A_[0] += d * wa; B_[0] -= d * wb
                    else:
                        d = oy if A_[1] >= B_[1] else -oy
                        A_[1] += d * wa; B_[1] -= d * wb
                    clamp(A_); clamp(B_)
        if not moved:
            break
    def inside(px, py, bx, pad=3):
        return abs(px - bx[0]) <= bx[2] / 2 + pad and abs(py - bx[1]) <= bx[3] / 2 + pad
    g, used = [], set()
    for e in b.get("edges", []):
        fb, tb = box.get(e.get("from")), box.get(e.get("to"))
        if not fb or not tb:
            continue
        et = e.get("type", "link")
        used.add(et)
        dash = EDGE_STYLE.get(et, "")
        cls = "edge conflict" if et == "conflict" else ("edge proposed" if et == "proposed" else "edge")
        sw = (' style="stroke-width:2.8"' if et == "repeat" else (' style="stroke:#a3a9b5"' if et == "link" else
              (' style="stroke-width:2.4;stroke-linecap:round"' if et == "testimonial" else "")))
        g.append(f'<line x1="{fb[0]:.1f}" y1="{fb[1]:.1f}" x2="{tb[0]:.1f}" y2="{tb[1]:.1f}" class="{cls}" stroke-dasharray="{dash}"{sw}/>')
        if e.get("label"):
            lab_ = str(e["label"])[:24]
            ts = [k / 40 for k in range(41)]
            free = [t for t in ts if not inside(fb[0] + (tb[0] - fb[0]) * t, fb[1] + (tb[1] - fb[1]) * t, fb)
                    and not inside(fb[0] + (tb[0] - fb[0]) * t, fb[1] + (tb[1] - fb[1]) * t, tb)]
            t = (free[0] + free[-1]) / 2 if free else 0.55
            mx, my = fb[0] + (tb[0] - fb[0]) * t, fb[1] + (tb[1] - fb[1]) * t + 3
            g.append(f'<rect x="{mx - 3.2 * len(lab_) - 3:.1f}" y="{my - 8:.1f}" width="{6.4 * len(lab_) + 6:.1f}" height="11" rx="2" class="elbg"/>')
            g.append(f'<text x="{mx:.1f}" y="{my:.1f}" class="el" text-anchor="middle">{E(lab_)}</text>')
    states = set()
    for x, y, bw, bh, lines, sub, is_c, nd in box.values():
        st = STATE_CLASS.get(str(nd.get("state", "OBSERVED")).upper(), "obs")
        if not is_c:
            states.add(st)
        g.append(f'<rect x="{x - bw / 2:.1f}" y="{y - bh / 2:.1f}" width="{bw:.1f}" height="{bh:.1f}" rx="5" class="node n-{st}{" center" if is_c else ""}"/>')
        for k, L in enumerate(lines):
            g.append(f'<text x="{x:.1f}" y="{y - bh / 2 + 16 + 12.5 * k:.1f}" class="nl{" cl" if is_c else ""}" text-anchor="middle">{E(L)}</text>')
        if sub:
            g.append(f'<text x="{x:.1f}" y="{y + bh / 2 - 6:.1f}" class="ns" text-anchor="middle">{E(sub)}</text>')
    if b.get("legend"):
        items = "".join(f'<span class="lg ln">{md(t)}</span>' for t in b["legend"])
    else:
        items = "".join(f'<span class="lg {c}">{t}</span>' for c, t in (("obs", "observed"), ("inf", "inferred"), ("unk", "unknown / namesake")) if c in states)
        names = {"repeat": "━ repeated work tie", "collab": "— work tie", "employment": "— company record", "link": "grey — record or listing",
                 "interview": "‒ ‒ interview", "testimonial": "· · quote", "co-presence": "··· co-presence, not a relationship",
                 "proposed": "gold ‒ ‒ proposed", "conflict": "red ‒ ‒ broken or wrong"}
        seen = []
        for et in ("repeat", "collab", "employment", "link", "interview", "testimonial", "co-presence", "proposed", "conflict"):
            if et in used and names[et] not in seen:
                seen.append(names[et])
        items += "".join(f'<span class="lg ln">{t}</span>' for t in seen)
    legend = f'<div class="legend">{items}</div>'
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
    states = set()
    for k, e in enumerate(ev):
        x = 44 + (Wd - 88) * (k / (n - 1) if n > 1 else 0.5)
        up = k % 2 == 0
        st = STATE_CLASS.get(str(e.get("state", "OBSERVED")).upper(), "obs")
        states.add(st)
        g.append(f'<line x1="{x:.1f}" y1="{H / 2}" x2="{x:.1f}" y2="{H / 2 + (-18 if up else 18)}" class="grid"/>')
        g.append(f'<circle cx="{x:.1f}" cy="{H / 2}" r="6" class="dot n-{st}"/>')
        y0 = H / 2 - 64 if up else H / 2 + 32
        lines = [str(e.get("date", ""))] + _wrap(str(e.get("label", "")), 22)[:3]
        half = max(len(L) for L in lines) * 2.6 + 4
        if x - half < 2:
            tx, anc = 2, "start"
        elif x + half > Wd - 2:
            tx, anc = Wd - 2, "end"
        else:
            tx, anc = x, "middle"
        g.append(f'<text x="{tx:.1f}" y="{y0:.1f}" class="td" text-anchor="{anc}">{E(lines[0])}</text>')
        for j, L in enumerate(lines[1:]):
            g.append(f'<text x="{tx:.1f}" y="{y0 + 13 + 11.5 * j:.1f}" class="tl2" text-anchor="{anc}">{E(L)}</text>')
    leg = ""
    if len(states) > 1 and not b.get("no_legend"):
        leg = '<div class="legend"><span class="lg obs">on record</span><span class="lg inf">planned or proposed</span></div>'
    return f'<div class="blk timeline" {_span(b)}>{_title(b)}{_svg(Wd, H, "".join(g))}{leg}{_caption(b, ctx)}</div>'


def swimlane(b, ctx):
    # Interval-packed lanes: every action gets its own visible bar (fix 2026-11-10: the old
    # two-sub-row stacking drew the third bar in a row on top of the first). Colour = executor.
    items = b.get("items") or ctx.plan_items()
    lanes = []
    for it in items:
        if it["lane"] not in lanes:
            lanes.append(it["lane"])
    horizon = int(b.get("horizon_days", 90))
    Wd, lab = W(b), 132
    x = lambda d: lab + (Wd - lab - 12) * min(d, horizon) / horizon
    packed = {}
    for ln in lanes:
        rows_end = []
        place = []
        for it in sorted([i for i in items if i["lane"] == ln], key=lambda i: (i.get("start", 0), i.get("end", 7))):
            s0, e0 = it.get("start", 0), max(it.get("end", 7), it.get("start", 0) + 4)
            px0, px1 = x(s0), x(s0) + max(x(e0) - x(s0), 30)
            if str(it.get("executor", "")).upper() == "HUMAN" and it.get("due") is not None and it["due"] - s0 <= 4:
                it = dict(it, diamond=True)
                px0 = x(it["due"]) - 5
                px1 = px0 + 12 + 6 * len(str(it.get("id", "")))
            for r, end in enumerate(rows_end):
                if px0 >= end + 3:
                    rows_end[r] = px1; place.append((it, r, px0, px1)); break
            else:
                rows_end.append(px1); place.append((it, len(rows_end) - 1, px0, px1))
        packed[ln] = (place, max(len(rows_end), 1))
    ys, y = {}, 22
    for ln in lanes:
        ys[ln] = y; y += 8 + 13 * packed[ln][1]
    H = y + 22
    g = []
    for li, ln in enumerate(lanes):
        if li % 2 == 0:
            g.append(f'<rect x="0" y="{ys[ln]}" width="{Wd}" height="{8 + 13 * packed[ln][1]}" class="laneband"/>')
    for d, name in ((0, b.get("today_label", "Today")), (7, "Day 7"), (30, "Day 30"), (60, "Day 60"), (90, "Day 90")):
        g.append(f'<line x1="{x(d):.1f}" y1="16" x2="{x(d):.1f}" y2="{H - 22}" class="grid"/>')
        g.append(f'<text x="{x(d):.1f}" y="12" class="td" text-anchor="{"end" if d >= horizon else "middle"}">{name}</text>')
    for ln in lanes:
        yb = ys[ln]
        g.append(f'<text x="{lab - 8}" y="{yb + 4 + 6.5 * packed[ln][1] + 4}" class="tl" text-anchor="end">{E(ln[:22])}</text>')
        for it, r, px0, px1 in packed[ln][0]:
            yy = yb + 4 + 13 * r
            ex_ = str(it.get("executor", "")).upper()
            human = ex_ == "HUMAN"
            cls = "bar alt" if human else ("bar ro" if ex_ == "AGENT" else "bar")
            human = human or ex_ == "AGENT"
            if it.get("diamond"):
                cxd, cyd = px0 + 5, yy + 6
                g.append(f'<path d="M{cxd - 6:.1f} {cyd} L{cxd:.1f} {cyd - 6} L{cxd + 6:.1f} {cyd} L{cxd:.1f} {cyd + 6} Z" class="bar alt"/>')
                g.append(f'<text x="{cxd + 9:.1f}" y="{yy + 9}" class="sl2 dk">{E(str(it.get("id", "")))}</text>')
                continue
            g.append(f'<rect x="{px0:.1f}" y="{yy}" width="{px1 - px0:.1f}" height="12" rx="2" class="{cls}"/>')
            g.append(f'<text x="{px0 + 4:.1f}" y="{yy + 9}" class="sl2{" dk" if human else ""}">{E(str(it.get("id", "")))}</text>')
    ly = H - 8
    g.append(f'<rect x="{lab}" y="{ly - 8}" width="10" height="8" class="bar"/><text x="{lab + 14}" y="{ly}" class="tl">agent, after approval</text>')
    g.append(f'<rect x="{lab + 140}" y="{ly - 8}" width="10" height="8" class="bar ro"/><text x="{lab + 154}" y="{ly}" class="tl">agent, read-only</text>')
    g.append(f'<rect x="{lab + 262}" y="{ly - 8}" width="10" height="8" class="bar alt"/><text x="{lab + 276}" y="{ly}" class="tl">only a person can do it (◆ = a dated decision)</text>')
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
