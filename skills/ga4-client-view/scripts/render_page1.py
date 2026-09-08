# -*- coding: utf-8 -*-
"""Render the GA4 client-view page-1 one-pager from a derived page1-spec JSON.

Usage:
    python3 render_page1.py <page1-spec.json> <out.html>

Every value comes from the JSON (which is DERIVED from the source MAA by the skill,
never invented). This script does presentation only: it draws the two standard
charts as inline SVG (dataviz rules), applies the stoplight colour system, and
lays out the Local Service Spotlight executive one-pager. Render to PDF with render_pdf.py.

See references/page1-schema.md for the JSON contract.
"""
import html, json, sys, base64, mimetypes, os

def esc(s): return html.escape(str(s))

# ---------------------------------------------------------------- palette / css
CSS = """
:root{
  --ink:#0f172a; --ink2:#334155; --muted:#64748b; --faint:#94a3b8;
  --line:#e6ebf2; --panel:#f7f9fc; --panel2:#eef3f9;
  --brand:#0e7490; --brand-d:#0b5563; --brand-soft:#d6ecf1;
  --good:#15803d; --good-soft:#dcfce7; --warn:#b45309; --warn-soft:#fdf0d5;
  --bad:#be123c; --bad-soft:#fde7ec;
}
*{box-sizing:border-box;-webkit-print-color-adjust:exact;print-color-adjust:exact;}
html,body{margin:0;padding:0;}
body{font-family:"Helvetica Neue",Helvetica,Arial,sans-serif;color:var(--ink);font-size:10.2px;line-height:1.45;}
.page{width:7.5in;margin:0 auto;padding:0;}
@page{size:Letter;margin:0.42in 0.5in;}
.sheet{page-break-after:always;}
.sheet:last-child{page-break-after:auto;}
.eyebrow{font-size:8.2px;letter-spacing:.16em;text-transform:uppercase;color:var(--brand);font-weight:700;}
h1.client{font-size:24px;line-height:1.05;margin:3px 0 4px;font-weight:800;letter-spacing:-.01em;}
.subline{color:var(--muted);font-size:9.4px;font-weight:600;}
.topbar{height:5px;border-radius:3px;background:linear-gradient(90deg,var(--brand),#22a3b8 60%,#5ac2cf);margin-bottom:12px;}
.hdr{display:flex;justify-content:space-between;align-items:flex-start;gap:16px;}
.brandrow{display:flex;gap:11px;align-items:flex-start;}
.logo{flex:0 0 auto;height:38px;width:auto;max-width:150px;object-fit:contain;margin-top:2px;}
.hdr-right{display:flex;flex-direction:column;gap:7px;align-items:flex-end;}
.periodpill{white-space:nowrap;text-align:right;font-size:8.6px;color:var(--muted);font-weight:600;
  border:1px solid var(--line);border-radius:8px;padding:7px 10px;background:var(--panel);}
.periodpill b{color:var(--ink);font-size:9.2px;display:block;}
.prepared{display:flex;gap:7px;align-items:center;}
.prepared img{width:26px;height:26px;border-radius:50%;object-fit:cover;border:1px solid var(--line);}
.prepared .pl{font-size:7.6px;color:var(--muted);font-weight:600;line-height:1.25;text-align:right;}
.prepared .pl b{color:var(--ink);font-size:8.4px;display:block;}
.pulse{margin:11px 0 12px;padding:11px 13px;border:1px solid var(--line);border-left:3px solid var(--brand);
  border-radius:9px;background:var(--panel);font-size:10.6px;line-height:1.5;color:var(--ink2);}
.pulse b{color:var(--ink);}
.tiles{display:grid;grid-template-columns:repeat(4,1fr);gap:9px;margin-bottom:13px;}
.tile{border:1px solid var(--line);border-radius:10px;padding:9px 11px;background:#fff;}
.tile .lab{font-size:8px;letter-spacing:.06em;text-transform:uppercase;color:var(--muted);font-weight:700;}
.tile .val{font-size:22px;font-weight:800;letter-spacing:-.02em;margin-top:2px;line-height:1;}
.tile .sub{font-size:8.4px;color:var(--faint);margin-top:3px;font-weight:600;}
.delta{display:inline-block;font-size:8.6px;font-weight:800;padding:1px 6px;border-radius:20px;margin-top:5px;}
.d-up{color:var(--good);background:var(--good-soft);}
.d-dn{color:var(--bad);background:var(--bad-soft);}
.d-fl{color:var(--muted);background:var(--panel2);}
.d-wn{color:var(--warn);background:var(--warn-soft);}
.grid2{display:grid;grid-template-columns:1.15fr 1fr;gap:14px;margin-bottom:12px;}
.card{border:1px solid var(--line);border-radius:10px;padding:11px 12px 9px;background:#fff;}
.card h3{margin:0 0 8px;font-size:9px;letter-spacing:.06em;text-transform:uppercase;color:var(--ink2);font-weight:800;}
.card .cap{font-size:8.2px;color:var(--faint);margin-top:6px;font-weight:600;}
.svgwrap{width:100%;}
.svgwrap svg{display:block;width:100%;height:auto;overflow:visible;}
text{font-family:"Helvetica Neue",Helvetica,Arial,sans-serif;}
.flags{display:flex;flex-direction:column;gap:7px;}
.flag{display:flex;gap:8px;align-items:flex-start;font-size:9.6px;line-height:1.42;color:var(--ink2);}
.flag .dot{flex:0 0 auto;width:15px;height:15px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:9px;margin-top:1px;}
.dot.g{background:var(--good-soft);} .dot.w{background:var(--warn-soft);} .dot.b{background:var(--bad-soft);}
.flag b{color:var(--ink);}
.todo{margin-top:12px;border:1px solid var(--line);border-radius:10px;overflow:hidden;}
.todo .th{background:var(--brand);color:#fff;font-size:8.6px;letter-spacing:.1em;text-transform:uppercase;font-weight:800;padding:7px 12px;}
.todo ul{list-style:none;margin:0;padding:2px 0;}
.todo li{display:flex;gap:9px;padding:8px 12px;border-top:1px solid var(--line);font-size:9.8px;line-height:1.42;color:var(--ink2);}
.todo li:first-child{border-top:none;}
.todo .box{flex:0 0 auto;width:13px;height:13px;border:1.5px solid var(--brand);border-radius:3px;margin-top:1px;}
.todo .start{font-weight:800;color:#fff;background:var(--brand);border-radius:4px;padding:0 6px;font-size:7.6px;letter-spacing:.08em;align-self:flex-start;margin-top:1px;}
.todo li.us .box{background:var(--brand-soft);border-color:var(--brand);}
.todo .ustag{font-size:7.4px;font-weight:800;color:var(--brand);letter-spacing:.06em;}
.todo .who{font-size:7.4px;font-weight:800;color:var(--muted);letter-spacing:.04em;}
.foot{display:flex;justify-content:space-between;align-items:center;gap:12px;margin-top:12px;
  padding-top:8px;border-top:1px solid var(--line);font-size:8px;color:var(--faint);font-weight:600;}
.foot a{color:var(--muted);text-decoration:none;}
.callout{margin-bottom:12px;border:1px solid #f3d9c4;background:#fff8f0;border-radius:10px;padding:10px 13px;}
.callout .k{font-size:8.4px;letter-spacing:.08em;text-transform:uppercase;color:var(--warn);font-weight:800;}
.callout p{margin:4px 0 0;font-size:9.8px;line-height:1.5;color:var(--ink2);}
.callout b{color:var(--ink);}
.outcome{display:flex;align-items:center;gap:9px;margin:0 0 12px;padding:8px 12px;border:1px solid var(--line);
  border-left:3px solid var(--good);background:var(--good-soft);border-radius:9px;}
.outcome .ol{letter-spacing:.06em;text-transform:uppercase;color:var(--ink2);font-weight:800;font-size:8.4px;}
.outcome .ov{font-size:16px;font-weight:800;color:var(--ink);letter-spacing:-.01em;}
.outcome .osub{color:var(--muted);font-weight:600;font-size:8.6px;}
.clienttag{font-size:7.4px;font-weight:800;color:var(--muted);letter-spacing:.04em;}
.callout.bad{border-color:#f3c4c4;background:#fef2f4;}
.callout.bad .k{color:var(--bad);}
"""

# ---------------------------------------------------------------- helpers
def data_uri(path):
    """Inline an image file as a data: URI so the HTML/PDF is self-contained.
    Accepts either a filesystem path or an already-formed data: URI."""
    if not path:
        return None
    if isinstance(path, str) and path.startswith("data:"):
        return path
    if not os.path.exists(path):
        return None
    mime = mimetypes.guess_type(path)[0] or "image/png"
    with open(path, "rb") as f:
        b = base64.b64encode(f.read()).decode("ascii")
    return f"data:{mime};base64,{b}"

def line_area(values, w=430, h=150, hi_idx=None, lo_idx=None,
              first_lab="13 wks ago", last_lab="last wk", last_color="var(--brand-d)"):
    padL, padR, padT, padB = 8, 30, 16, 20
    iw, ih = w - padL - padR, h - padT - padB
    vmax = max(values) or 1; vmin = 0
    n = len(values)
    def X(i): return padL + iw * (i/(n-1))
    def Y(v): return padT + ih * (1 - (v - vmin)/(vmax - vmin))
    pts = [(X(i), Y(v)) for i, v in enumerate(values)]
    line = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    area = f"M{pts[0][0]:.1f},{padT+ih:.1f} L" + " L".join(f"{x:.1f},{y:.1f}" for x,y in pts) + f" L{pts[-1][0]:.1f},{padT+ih:.1f} Z"
    base = padT + ih
    grid = ""
    for gy in [vmax, vmax/2]:
        y = Y(gy)
        grid += f'<line x1="{padL}" y1="{y:.1f}" x2="{padL+iw}" y2="{y:.1f}" stroke="#eef2f7" stroke-width="1"/>'
        grid += f'<text x="{padL+iw+4}" y="{y+3:.1f}" font-size="7.5" fill="#b3bdcb">{int(round(gy))}</text>'
    dots = ""
    for i,(x,y) in enumerate(pts):
        r = 2.2; sw=1.4
        if i==hi_idx or i==lo_idx or i==n-1: r=3.1; sw=1.6
        dots += f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="#fff" stroke="var(--brand)" stroke-width="{sw}"/>'
    labs = ""
    if hi_idx is not None:
        x,y = pts[hi_idx]; labs += f'<text x="{x:.1f}" y="{y-6:.1f}" font-size="8" font-weight="800" fill="var(--brand-d)" text-anchor="middle">{values[hi_idx]}</text>'
    lx,ly = pts[-1]
    labs += f'<text x="{lx-3:.1f}" y="{ly-6:.1f}" font-size="8" font-weight="800" fill="{last_color}" text-anchor="end">{values[-1]}</text>'
    xlabs = (f'<text x="{padL}" y="{h-5}" font-size="7.5" fill="#9aa6b4">{esc(first_lab)}</text>'
             f'<text x="{padL+iw}" y="{h-5}" font-size="7.5" fill="#9aa6b4" text-anchor="end">{esc(last_lab)}</text>')
    return f'''<div class="svgwrap"><svg viewBox="0 0 {w} {h}" role="img">
<defs><linearGradient id="ga" x1="0" x2="0" y1="0" y2="1">
<stop offset="0" stop-color="var(--brand)" stop-opacity="0.20"/>
<stop offset="1" stop-color="var(--brand)" stop-opacity="0.02"/></linearGradient></defs>
{grid}<path d="{area}" fill="url(#ga)"/>
<polyline points="{line}" fill="none" stroke="var(--brand)" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"/>
<line x1="{padL}" y1="{base:.1f}" x2="{padL+iw}" y2="{base:.1f}" stroke="#dbe2ec" stroke-width="1"/>
{dots}{labs}{xlabs}</svg></div>'''

def hbars(rows, w=430, rowh=25, maxval=None, unit="", labW=112, barTrack=150):
    padL, padT = 2, 4
    maxval = maxval or max((r[1] for r in rows), default=1) or 1
    h = padT + rowh*len(rows) + 4
    out = [f'<div class="svgwrap"><svg viewBox="0 0 {w} {h}" role="img">']
    for i,row in enumerate(rows):
        lab, val = row[0], row[1]
        right = row[2] if len(row) > 2 else ""
        y = padT + i*rowh; cy = y + rowh/2
        bw = max(2.0, barTrack * (val/maxval)); frac = val/maxval
        op = 0.45 + 0.55*frac
        out.append(f'<text x="{padL}" y="{cy+3:.1f}" font-size="8.6" fill="var(--ink2)" font-weight="600">{esc(lab)}</text>')
        out.append(f'<rect x="{labW}" y="{cy-6.5:.1f}" width="{barTrack}" height="13" rx="3" fill="#f1f5f9"/>')
        out.append(f'<rect x="{labW}" y="{cy-6.5:.1f}" width="{bw:.1f}" height="13" rx="3" fill="var(--brand)" fill-opacity="{op:.2f}"/>')
        out.append(f'<text x="{labW+bw+5:.1f}" y="{cy+3:.1f}" font-size="8.6" font-weight="800" fill="var(--ink)">{esc(val)}{unit}</text>')
        if right:
            out.append(f'<text x="{w-1}" y="{cy+3:.1f}" font-size="8" fill="var(--muted)" text-anchor="end" font-weight="700">{esc(right)}</text>')
    out.append('</svg></div>')
    return "".join(out)

# stoplight maps
PILL = {"good":"d-up","bad":"d-dn","watch":"d-wn","flat":"d-fl"}
FLAG = {"good":"g","watch":"w","bad":"b"}
FLAG_ICON = {"g":"✓","w":"!","b":"↓"}

def tile(p):
    d = f'<div class="delta {PILL.get(p.get("state","flat"),"d-fl")}">{esc(p["delta"])}</div>' if p.get("delta") else ""
    return (f'<div class="tile"><div class="lab">{esc(p["lab"])}</div>'
            f'<div class="val">{esc(p["val"])}</div>{d}<div class="sub">{esc(p.get("sub",""))}</div></div>')

def flag(f):
    kind = FLAG.get(f.get("state","watch"),"w")
    return f'<div class="flag"><span class="dot {kind}">{FLAG_ICON[kind]}</span><span>{f["text"]}</span></div>'

def chart_html(c):
    if c["type"] == "trend":
        last_color = "var(--bad)" if c.get("last_state") == "bad" else "var(--brand-d)"
        svg = line_area(c["values"], hi_idx=c.get("hi_idx"), lo_idx=c.get("lo_idx"),
                        first_lab=c.get("first_lab","13 wks ago"), last_lab=c.get("last_lab","last wk"),
                        last_color=last_color)
    else:  # bars
        svg = hbars([tuple(r) for r in c["rows"]], maxval=c.get("maxval"),
                    labW=c.get("labW",112), barTrack=c.get("barTrack",130))
    return (c["title"], svg, c.get("caption",""))

def header(d):
    logo = data_uri(d.get("logo"))
    logo_html = f'<img class="logo" src="{logo}" alt="">' if logo else ""
    prep = d.get("prepared_by") or {}
    prep_html = ""
    if prep.get("name"):
        photo = data_uri(prep.get("photo"))
        img = f'<img src="{photo}" alt="">' if photo else ""
        prep_html = (f'<div class="prepared">{img}<div class="pl">Prepared by'
                     f'<b>{esc(prep["name"])}</b>{esc(prep.get("role",""))}</div></div>')
    return (f'<div class="hdr"><div class="brandrow">{logo_html}<div>'
            f'<div class="eyebrow">{esc(d["eyebrow"])}</div>'
            f'<h1 class="client">{esc(d["client"])}</h1>'
            f'<div class="subline">{esc(d.get("subline",""))}</div></div></div>'
            f'<div class="hdr-right">{prep_html}'
            f'<div class="periodpill">Reporting period<b>{esc(d["period"])}</b>{esc(d.get("period2",""))}</div>'
            f'</div></div>')

def todo_html(items):
    out = []
    for it in items:
        role = it.get("role","client")
        if role == "start":
            out.append(f'<li><span class="start">Start&nbsp;here</span><span>{it["text"]}</span></li>')
        elif role == "us":
            out.append(f'<li class="us"><span class="box"></span><span>{it["text"]} <span class="ustag">✓ we\'re on this</span></span></li>')
        else:
            who = f' <span class="clienttag">→ {esc(it["owner"])}</span>' if it.get("owner") else ""
            out.append(f'<li><span class="box"></span><span>{it["text"]}{who}</span></li>')
    return "".join(out)

def citations_foot(d):
    cit = d.get("citations") or {}
    left_bits = []
    if cit.get("project_url"): left_bits.append(f'<a href="{esc(cit["project_url"])}">Project</a>')
    if cit.get("ga4_url"): left_bits.append(f'<a href="{esc(cit["ga4_url"])}">GA4 data</a>')
    prep = (d.get("prepared_by") or {}).get("name")
    if prep: left_bits.append(f'Prepared by {esc(prep)}')
    left = " · ".join(left_bits) if left_bits else esc(d.get("foot_l",""))
    right = esc(cit.get("date") or d.get("foot_r",""))
    return f'<div class="foot"><span>{left}</span><span>{right}</span></div>'

def page(d):
    tiles = "".join(tile(p) for p in d["pills"])
    flags = "".join(flag(f) for f in d["flags"])
    callout = ""
    if d.get("callout"):
        ccls = "callout bad" if d["callout"].get("state") == "bad" else "callout"
        callout = f'<div class="{ccls}"><div class="k">{esc(d["callout"]["k"])}</div><p>{d["callout"]["body"]}</p></div>'
    outcome = ""
    if d.get("outcome"):
        o = d["outcome"]
        od = f'<span class="delta {PILL.get(o.get("state","good"),"d-up")}">{esc(o["delta"])}</span>' if o.get("delta") else ""
        osub = f'<span class="osub">{esc(o.get("sub",""))}</span>' if o.get("sub") else ""
        outcome = (f'<div class="outcome"><span class="ol">{esc(o["label"])}</span>'
                   f'<span class="ov">{esc(o["value"])}</span>{od}{osub}</div>')
    lc = chart_html(d["left_chart"]); rc = chart_html(d["right_chart"])
    return f'''<div class="page sheet">
<div class="topbar"></div>
{header(d)}
<div class="pulse">{d["pulse"]}</div>
{outcome}
<div class="tiles">{tiles}</div>
{callout}
<div class="grid2">
  <div class="card"><h3>{esc(lc[0])}</h3>{lc[1]}<div class="cap">{esc(lc[2])}</div></div>
  <div class="card"><h3>{esc(rc[0])}</h3>{rc[1]}<div class="cap">{esc(rc[2])}</div></div>
</div>
<div class="grid2" style="grid-template-columns:1fr 1fr;">
  <div class="card"><h3>What stands out</h3><div class="flags">{flags}</div></div>
  <div><div class="todo"><div class="th">What to do next</div><ul>{todo_html(d["todo"])}</ul></div></div>
</div>
{citations_foot(d)}
</div>'''

def full_html(spec):
    pages = spec if isinstance(spec, list) else [spec]
    body = "\n".join(page(p) for p in pages)
    return f"<!doctype html><html><head><meta charset='utf-8'><style>{CSS}</style></head><body>{body}</body></html>"

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("usage: python3 render_page1.py <page1-spec.json> <out.html>"); sys.exit(1)
    with open(sys.argv[1]) as f:
        spec = json.load(f)
    with open(sys.argv[2], "w") as f:
        f.write(full_html(spec))
    print("wrote", sys.argv[2])
