#!/usr/bin/env python3
"""Draw the Content Factory agency-flow and hierarchy visuals.

    python3 skills/content-factory/scripts/render_factory_visuals.py \\
        --out skills/content-factory/references/visuals [--png]
"""

from __future__ import annotations

import argparse
import html
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from png_shot import PngError, write_png  # noqa: E402

AGENTS = [
    ("MU", "Muse / Happy", "#1D4E89", "Muse Maximum · 3B tokens/week", "muse"),
    ("QW", "Local Qwen", "#1B7A4E", "Free · Macs", "qwen"),
    ("AS", "Astra / Dot", "#BE185D", "Experimental thinking", "astra"),
    ("KI", "Kimi cron", "#6B21A8", "Cheap scheduled", "cheap"),
    ("CX", "Codex / Pollen", "#C2410C", "Cheap scheduled", "cheap"),
    ("CU", "Cursor cloud", "#334155", "Repo + site builds", "premium"),
    ("CF", "Claude Fleet", "#9F1239", "Basecamp poster only", "premium"),
    ("TR", "Trenton", "#0E7490", "Head of content", "grok"),
    ("TN", "Tanner", "#7C3AED", "EA / calendar", "grok"),
    ("Q", "Q", "#0369A1", "OS / routing", "grok"),
    ("AX", "Alex · docs", "#0F766E", "SOPs / skills", "grok"),
    ("9T", "Alex · 9T", "#A16207", "Nine Triangles", "grok"),
    ("SM", "Sam", "#BE185D", "Personal-brand sites", "grok"),
    ("MR", "Mario", "#4338CA", "Site work", "grok"),
    ("AU", "Austin", "#B45309", "IT / Plumbing", "grok"),
    ("MM", "Meter Maid", "#047857", "Seat usage", "grok"),
    ("DA", "Data", "#1E3A8A", "Registry / uptime", "grok"),
    ("DY", "Dennis", "#9F1239", "Public + paid gate", "gate"),
]

STAGES = [
    {
        "id": "plumbing",
        "label": "Plumbing",
        "tag": "BEFORE",
        "color": "#334155",
        "owner": "Austin",
        "lane": "Muse for Google logins",
        "agents": ["AU", "MU", "CU"],
        "work": [
            "GSC / CMS / GA4 / GTM",
            "YouTube + social + ads",
            "Record access once",
        ],
        "handoff_in": "Kickoff list",
        "handoff_out": "Green register → Drive",
        "gate": "Human adds users",
    },
    {
        "id": "produce",
        "label": "Produce",
        "tag": "FACTORY",
        "color": "#0F766E",
        "owner": "Trenton",
        "lane": "Muse watch + bookings",
        "agents": ["TR", "TN", "MU"],
        "work": [
            "Book + record Zoom",
            "Watch stranded YouTube",
            "Confirm accepted GCT",
        ],
        "handoff_in": "MAA Action / calendar",
        "handoff_out": "Recording → Drive",
        "gate": None,
    },
    {
        "id": "process",
        "label": "Process",
        "tag": "FACTORY",
        "color": "#1D4ED8",
        "owner": "Trenton",
        "lane": "Qwen bulk · Astra think",
        "agents": ["QW", "AS", "TR"],
        "work": [
            "Transcript + mine",
            "Definitive reasoning",
            "Descript atomize + A-",
        ],
        "handoff_in": "Drive recording",
        "handoff_out": "Hub + clips → Drive",
        "gate": "Fresh check on Dot's reasoning",
    },
    {
        "id": "post",
        "label": "Post",
        "tag": "FACTORY",
        "color": "#6B21A8",
        "owner": "Trenton · Sam/Mario (web)",
        "lane": "Muse drafts · CF Basecamp",
        "agents": ["MU", "CF", "SM", "MR", "CU"],
        "work": [
            "Stage hub on site",
            "FB/IG/email packs",
            "GitHub issue → Basecamp",
        ],
        "handoff_in": "Staged pack + issue",
        "handoff_out": "Draft URL / BC comment",
        "gate": "Dennis publishes",
    },
    {
        "id": "promote",
        "label": "Promote",
        "tag": "FACTORY",
        "color": "#C2410C",
        "owner": "Alex · 9T",
        "lane": "Muse Meta chores",
        "agents": ["MU", "9T", "DY"],
        "work": [
            "Rank proven organic",
            "Stage $1/day × 7",
            "Day-7 kill / scale rec",
        ],
        "handoff_in": "Engaged posts",
        "handoff_out": "Staged calendar",
        "gate": "Dennis spends",
    },
    {
        "id": "perform",
        "label": "Perform / MAA",
        "tag": "AFTER",
        "color": "#9F1239",
        "owner": "Kimi/Codex crons (Friday MAA)",
        "lane": "Crons · Qwen tables · Astra analysis",
        "agents": ["KI", "CX", "AS", "QW", "MM", "DA"],
        "work": [
            "Metrics: $ / profit / clicks",
            "Analysis that must be right",
            "Action → next Produce",
        ],
        "handoff_in": "Connectors + Buzz",
        "handoff_out": "Action packet → Produce",
        "gate": "Dennis if public/paid · Dot checked",
    },
]


def _esc(text: object) -> str:
    return html.escape(str(text), quote=True)


def _wrap(text: str, width_px: int, font_px: int) -> list[str]:
    """Greedy word wrap using a conservative average glyph width.

    Sans-serif glyphs at these sizes average a little under 0.6em; using 0.6em
    keeps every line inside its box so nothing is clipped in the PNG.
    """
    max_chars = max(8, int(width_px / (font_px * 0.6)))
    lines: list[str] = []
    current = ""
    for word in str(text).split():
        trial = f"{current} {word}".strip()
        if len(trial) > max_chars and current:
            lines.append(current)
            current = word
        else:
            current = trial
    if current:
        lines.append(current)
    return lines or [""]


def _badge(cx: int, cy: int, monogram: str, fill: str, label: str | None = None, experimental: bool = False) -> str:
    ring = "#F5A623" if experimental else "#F8FAFC"
    title = f"<title>{_esc(label or monogram)}</title>"
    dash = 'stroke-dasharray="3 3"' if experimental else ""
    text = (
        f'<text x="{cx}" y="{cy + 5}" text-anchor="middle" fill="#FFF7ED" '
        f'font-family="ui-sans-serif, sans-serif" font-size="11" font-weight="700">{monogram}</text>'
    )
    return (
        f'<g>{title}<circle cx="{cx}" cy="{cy}" r="16" fill="{fill}" stroke="{ring}" '
        f'stroke-width="2" {dash}/>{text}</g>'
    )


def agency_svg() -> tuple[str, int, int]:
    width = 2480
    agent_index = {row[0]: row for row in AGENTS}
    cols = []
    col_w = 380
    gap = 20
    x0 = 40
    y0 = 430
    for i, stage in enumerate(STAGES):
        x = x0 + i * (col_w + gap)
        badges = []
        for j, key in enumerate(stage["agents"]):
            agent = agent_index[key]
            bx = x + 36 + (j % 5) * 68
            by = y0 + 168 + (j // 5) * 44
            badges.append(_badge(bx, by, agent[0], agent[2], agent[1], experimental=key == "AS"))
        work = "".join(
            f'<text x="{x + 24}" y="{y0 + 268 + n * 22}" fill="#E2E8F0" font-size="14" '
            f'font-family="ui-sans-serif, sans-serif">• {_esc(line)}</text>'
            for n, line in enumerate(stage["work"])
        )
        gate = (
            f'<rect x="{x + 20}" y="{y0 + 348}" width="{col_w - 40}" height="36" rx="8" fill="#9F1239"/>'
            f'<text x="{x + col_w / 2}" y="{y0 + 371}" text-anchor="middle" fill="#FFF7ED" '
            f'font-size="13" font-family="ui-sans-serif, sans-serif">GATE · {_esc(stage["gate"])}</text>'
            if stage["gate"]
            else f'<text x="{x + col_w / 2}" y="{y0 + 371}" text-anchor="middle" fill="#94A3B8" '
            f'font-size="13" font-family="ui-sans-serif, sans-serif">No public/paid gate in this station</text>'
        )
        arrow = ""
        if i < 5:
            ax = x + col_w + 2
            arrow = (
                f'<path d="M{ax} {y0 + 90} h{gap - 8}" stroke="#F5A623" stroke-width="3" fill="none"/>'
                f'<polygon points="{ax + gap - 8},{y0 + 84} {ax + gap},{y0 + 90} {ax + gap - 8},{y0 + 96}" fill="#F5A623"/>'
            )
        cols.append(
            f"""
            <rect x="{x}" y="{y0}" width="{col_w}" height="400" rx="18" fill="#0F172A"/>
            <rect x="{x}" y="{y0}" width="{col_w}" height="54" rx="18" fill="{stage['color']}"/>
            <rect x="{x}" y="{y0 + 30}" width="{col_w}" height="24" fill="{stage['color']}"/>
            <text x="{x + 20}" y="{y0 + 34}" fill="#FFF7ED" font-family="Georgia, serif" font-size="22">
              {_esc(stage['label'])}</text>
            <text x="{x + col_w - 20}" y="{y0 + 32}" text-anchor="end" fill="#FEF3C7" font-size="11"
              font-family="ui-sans-serif, sans-serif">{stage['tag']}</text>
            <text x="{x + 20}" y="{y0 + 82}" fill="#F8FAFC" font-size="14" font-family="ui-sans-serif, sans-serif">
              Owner: {_esc(stage['owner'])}</text>
            <text x="{x + 20}" y="{y0 + 104}" fill="#F5A623" font-size="13" font-family="ui-sans-serif, sans-serif">
              Cheapest capable: {_esc(stage['lane'])}</text>
            <text x="{x + 20}" y="{y0 + 132}" fill="#94A3B8" font-size="12" font-family="ui-sans-serif, sans-serif">
              in: {_esc(stage['handoff_in'])}</text>
            <text x="{x + 20}" y="{y0 + 150}" fill="#94A3B8" font-size="12" font-family="ui-sans-serif, sans-serif">
              out: {_esc(stage['handoff_out'])}</text>
            {''.join(badges)}
            {work}
            {gate}
            {arrow}
            """
        )

    # Feedback arrow from Perform back under the row into Produce
    feedback = f"""
      <path d="M {x0 + 5 * (col_w + gap) + col_w / 2} {y0 + 412}
               v 70 H {x0 + col_w + col_w / 2} v -70"
            fill="none" stroke="#F5A623" stroke-width="4"
            marker-end="url(#arrowhead)"/>
      <text x="{x0 + 3 * (col_w + gap)}" y="{y0 + 468}" text-anchor="middle"
            fill="#92400E" font-family="Georgia, serif" font-size="16">
        MAA Action feeds Produce — revenue, profit, clicks decide the next recording
      </text>
    """

    band_specs = [
        (40, 1200, "#1D4E89", "#DBEAFE", "Muse on Spark — volume lane (cost order 2)",
         "Inbox, calendar, bookings, Google Photos/Docs/Gmail, Meta (FB/IG/WA/Threads), "
         "watch-and-ping, volume monitoring. Not frontier reasoning. Local Qwen (free) comes "
         "first for offline bulk text that can wait for a Mac."),
        (1260, 1180, "#BE185D", "#FCE7F3", "Astra — thinking lane (experimental, cost order 3)",
         "Hard research, strategy/judgment drafts, definitive-article reasoning, MAA analysis "
         "that must be right, code/docs that matter. Spot-check Dot; on critical work a human "
         "or a fresh ChatGPT task checks it before anyone acts."),
    ]
    bands = ""
    for bx, bw, fill, text_fill, title, blurb in band_specs:
        lines = _wrap(blurb, bw - 48, 13)
        band_h = 40 + 19 * len(lines)
        bands += (
            f'<rect x="{bx}" y="274" width="{bw}" height="{band_h}" rx="14" fill="{fill}"/>'
            f'<text x="{bx + 24}" y="300" fill="#FFF7ED" font-family="Georgia, serif" font-size="18">{_esc(title)}</text>'
            + "".join(
                f'<text x="{bx + 24}" y="{322 + n * 19}" fill="{text_fill}" font-family="ui-sans-serif, sans-serif" '
                f'font-size="13">{_esc(line)}</text>'
                for n, line in enumerate(lines)
            )
        )

    # Cost order from standards/pick-the-cheapest-capable-fleet-lane.md:
    # local Qwen (free) -> Muse -> everything else. Three boxes, wrapped text,
    # box height follows the longest blurb so nothing is clipped.
    cost_y = y0 + 548
    cost = [
        (40, 560, "#1B7A4E", "1 · Free — Local Qwen",
         "Offline bulk text only: transcript triage, first drafts, MAA/GCT first passes. "
         "Trenton's seat on the Macs. No browser, no logins, no publishing."),
        (620, 760, "#1D4E89", "2 · Muse — the volume lane",
         "Muse Maximum is about 3B Muse tokens per week. Non-frontier volume: inbox, calendar, "
         "bookings, Google/Meta chores, watch-and-ping, volume monitoring. Do not buy more Muse."),
        (1400, 1040, "#475569", "3 · Everything else",
         "Astra / Dot (experimental; a human or a fresh ChatGPT task checks critical work) · "
         "Kimi and Codex crons already live · Grok desks for judgment, publishing calls, routing "
         "(short turns) · any other seat — Cursor cloud, Claude Fleet, the rest — keeps the work "
         "already assigned to it."),
    ]
    wrapped = [(x, w, fill, title, _wrap(blurb, w - 36, 12)) for x, w, fill, title, blurb in cost]
    cost_h = 44 + 18 * max(len(lines) for *_rest, lines in wrapped)
    cost_svg = []
    for x, w, fill, title, lines in wrapped:
        body = "".join(
            f'<text x="{x + 18}" y="{cost_y + 52 + n * 18}" fill="#FEF3C7" font-size="12" '
            f'font-family="ui-sans-serif, sans-serif">{_esc(line)}</text>'
            for n, line in enumerate(lines)
        )
        cost_svg.append(
            f'<rect x="{x}" y="{cost_y}" width="{w}" height="{cost_h}" rx="12" fill="{fill}"/>'
            f'<text x="{x + 18}" y="{cost_y + 28}" fill="#FFF7ED" font-size="16" font-family="Georgia, serif">{_esc(title)}</text>'
            f"{body}"
        )
    cost_label_y = cost_y - 14

    legend_title_y = cost_y + cost_h + 54
    legend_agents = []
    for i, agent in enumerate(AGENTS):
        lx = 48 + (i % 9) * 268
        ly = legend_title_y + 20 + (i // 9) * 54
        legend_agents.append(
            _badge(lx + 18, ly + 16, agent[0], agent[2], agent[1], experimental=agent[0] == "AS")
            + f'<text x="{lx + 44}" y="{ly + 12}" font-size="13" font-family="ui-sans-serif, sans-serif" fill="#0F172A">{_esc(agent[1])}</text>'
            + f'<text x="{lx + 44}" y="{ly + 30}" font-size="11" font-family="ui-sans-serif, sans-serif" fill="#475569">{_esc(agent[3])}</text>'
        )
    legend_rows = (len(AGENTS) + 8) // 9
    notes_y = legend_title_y + 20 + legend_rows * 54 + 20
    height = notes_y + 118

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}"
      viewBox="0 0 {width} {height}" role="img"
      aria-label="Content Factory agency swimlanes from Plumbing through Perform MAA">
  <defs>
    <marker id="arrowhead" markerWidth="12" markerHeight="10" refX="10" refY="5" orient="auto">
      <polygon points="0 0, 12 5, 0 10" fill="#F5A623"/>
    </marker>
  </defs>
  <rect width="{width}" height="{height}" fill="#F4F1EA"/>
  <rect x="0" y="0" width="{width}" height="118" fill="#22698A"/>
  <text x="48" y="48" fill="#FFF7ED" font-family="Georgia, serif" font-size="34">
    Content Factory as a digital marketing agency</text>
  <text x="48" y="84" fill="#DBEAFE" font-family="ui-sans-serif, sans-serif" font-size="18">
    Plumbing → Produce → Process → Post → Promote → Perform / MAA · Local Service Spotlight</text>
  <rect x="40" y="136" width="1195" height="120" rx="16" fill="#0F172A"/>
  <text x="64" y="172" fill="#F5A623" font-family="Georgia, serif" font-size="20">Current state (2026-10-01)</text>
  <text x="64" y="200" fill="#E2E8F0" font-family="ui-sans-serif, sans-serif" font-size="14">
    Work is still divided across the named desks. Muse on Spark does high-volume non-frontier work:</text>
  <text x="64" y="222" fill="#E2E8F0" font-family="ui-sans-serif, sans-serif" font-size="14">
    Google/Meta errands, inbox, calendar, bookings, watch-and-ping, volume monitoring.</text>
  <text x="64" y="244" fill="#E2E8F0" font-family="ui-sans-serif, sans-serif" font-size="14">
    Astra (Dot + specific ChatGPT tasks) does the thinking — and Dot is experimental.</text>
  <rect x="1255" y="136" width="1185" height="120" rx="16" fill="#3B0764"/>
  <text x="1279" y="172" fill="#F5A623" font-family="Georgia, serif" font-size="20">Future state</text>
  <text x="1279" y="200" fill="#E2E8F0" font-family="ui-sans-serif, sans-serif" font-size="14">
    As there are many Dots, the models absorb the harness.</text>
  <text x="1279" y="222" fill="#E2E8F0" font-family="ui-sans-serif, sans-serif" font-size="14">
    Fewer humans need to divide the work and project-manage the handoffs.</text>
  <text x="1279" y="244" fill="#E2E8F0" font-family="ui-sans-serif, sans-serif" font-size="14">
    The locked line does not change. Do not retire a desk because this note exists.</text>
  {bands}
  <text x="48" y="{y0 - 44}" fill="#0F172A" font-family="Georgia, serif" font-size="20">
    Swimlanes — each badge is a named seat. Gold arrows are handoffs. Nothing public or paid without Dennis.</text>
  {''.join(cols)}
  {feedback}
  <text x="48" y="{cost_label_y}" font-family="Georgia, serif" font-size="18" fill="#0F172A">
    Cost order (pick-the-cheapest-capable-fleet-lane): local Qwen → Muse → everything else. Lanes are seats, not desk names.</text>
  {''.join(cost_svg)}
  <text x="48" y="{legend_title_y}" font-family="Georgia, serif" font-size="20" fill="#0F172A">Named seats — do not invent agents</text>
  {''.join(legend_agents)}
  <text x="48" y="{notes_y}" font-family="ui-sans-serif, sans-serif" font-size="13" fill="#475569">
    Tools on the line, not seats: Zoom recordings · Descript · jennifer A- grader · $1/day boosting.
    Handoff places: Drive · GitHub issue · Basecamp (Claude Fleet only) · Buzz (Monday MAA catch-up).</text>
  <text x="48" y="{notes_y + 26}" font-family="ui-sans-serif, sans-serif" font-size="12" fill="#64748B">
    Badges are monograms, not official marks. If a later revision adds a vendor mark, use a permissive
    source such as Simple Icons (CC0) and note the license here. Dashed gold ring = experimental seat.</text>
  <text x="48" y="{notes_y + 48}" font-family="ui-sans-serif, sans-serif" font-size="12" fill="#64748B">
    Seat picker: standards/pick-the-cheapest-capable-fleet-lane.md (merged 2026-10-01). Factory split per station:
    skills/content-factory/references/fleet-orchestration.md. Sam, Data and the Buzz handoff are from the 2026-10-01 brief only.</text>
  <text x="48" y="{notes_y + 84}" font-family="ui-sans-serif, sans-serif" font-size="12" fill="#64748B">
    Locked names: Plumbing (before) · Produce · Process · Post · Promote · Perform/MAA (after). Do not rename.</text>
</svg>
"""
    return svg, width, height


def hierarchy_svg() -> tuple[str, int, int]:
    width, height = 2480, 1330
    columns = [
        (
            "Plumbing",
            "#334155",
            [
                ("Access", "Austin · Muse", "GSC, CMS, YouTube, ads"),
                ("Tracking", "Austin · Cursor", "GA4 / GTM live tag"),
                ("Credentials", "Austin", "Record; do not re-ask"),
            ],
            "No article yet — the register is the artifact",
        ),
        (
            "Produce",
            "#0F766E",
            [
                ("Capture", "Tanner · Muse", "Office Hours / podcast Zoom"),
                ("Source inventory", "Muse watch · Trenton", "Stranded YouTube triage"),
                ("Aim", "Alex 9T · Astra draft", "Accepted GCT"),
            ],
            "Recording + inventory.json",
        ),
        (
            "Process",
            "#1D4ED8",
            [
                ("Transcribe & mine", "Local Qwen", "transcript.md"),
                ("Definitive article", "Qwen draft · Astra + second check", "Hub recipe"),
                ("Atomize + grade", "Trenton · jennifer A-", "Clips + A-"),
            ],
            "Definitive hub  →  meta run record",
        ),
        (
            "Post",
            "#6B21A8",
            [
                ("Hub page", "Sam / Mario / Cursor", "CMS draft"),
                ("Channel packages", "Muse · Grok desk", "FB/IG/email pack"),
                ("Client update", "Claude Fleet", "Basecamp via GitHub issue"),
            ],
            "Dennis publish click",
        ),
        (
            "Promote",
            "#C2410C",
            [
                ("Rank organic", "Muse volume", "Last 60–90 days"),
                ("$1/day test", "Muse · Dennis", "Staged calendar"),
                ("Kill / scale rec", "Astra if it must be right", "Day-7 MAA"),
            ],
            "Spend receipt · not a second factory",
        ),
        (
            "Perform / MAA",
            "#9F1239",
            [
                ("Metrics", "Kimi/Codex · Qwen", "Revenue, profit, clicks"),
                ("Analysis", "Astra + fresh second check", "Why it moved"),
                ("Action", "Stage-owner desk · Dennis if public/paid", "Feeds Produce"),
            ],
            "Monday: Codex/Pollen from Buzz",
        ),
    ]
    cards = []
    for i, (title, color, rows, foot) in enumerate(columns):
        x = 40 + i * 405
        y = 220
        items = []
        for n, (sub, owner, task) in enumerate(rows):
            iy = y + 80 + n * 150
            items.append(
                f"""
                <rect x="{x + 18}" y="{iy}" width="360" height="136" rx="12" fill="#0F172A"/>
                <text x="{x + 36}" y="{iy + 28}" fill="#F5A623" font-size="13" font-family="ui-sans-serif, sans-serif">SUBCOMPONENT</text>
                <text x="{x + 36}" y="{iy + 54}" fill="#F8FAFC" font-size="18" font-family="Georgia, serif">{_esc(sub)}</text>
                <text x="{x + 36}" y="{iy + 80}" fill="#93C5FD" font-size="13" font-family="ui-sans-serif, sans-serif">TASK · {_esc(task)}</text>
                <text x="{x + 36}" y="{iy + 104}" fill="#CBD5E1" font-size="13" font-family="ui-sans-serif, sans-serif">AGENT · {_esc(owner)}</text>
                """
            )
            if n < 2:
                items.append(
                    f'<path d="M{x + 198} {iy + 136} v14" stroke="#F5A623" stroke-width="2"/>'
                )
        cards.append(
            f"""
            <rect x="{x}" y="{y}" width="396" height="620" rx="18" fill="#FFFFFF" stroke="#D6D3C9"/>
            <rect x="{x}" y="{y}" width="396" height="58" rx="18" fill="{color}"/>
            <rect x="{x}" y="{y + 36}" width="396" height="22" fill="{color}"/>
            <text x="{x + 20}" y="{y + 38}" fill="#FFF7ED" font-size="22" font-family="Georgia, serif">{_esc(title)}</text>
            {''.join(items)}
            <text x="{x + 20}" y="{y + 600}" fill="#334155" font-size="13" font-family="ui-sans-serif, sans-serif">{_esc(foot)}</text>
            """
        )

    example = """
      <rect x="40" y="880" width="2400" height="280" rx="18" fill="#0F172A"/>
      <text x="64" y="920" fill="#F5A623" font-family="Georgia, serif" font-size="22">
        Worked leaf — Thursday Office Hours (EXAMPLE DATA, not a real run)</text>
      <text x="64" y="956" fill="#E2E8F0" font-family="ui-sans-serif, sans-serif" font-size="16">
        STAGE Produce → SUBCOMPONENT Capture → TASK Thursday Office Hours Zoom (Tanner books, Muse sends calendar)</text>
      <text x="64" y="988" fill="#E2E8F0" font-family="ui-sans-serif, sans-serif" font-size="16">
        STAGE Process → SUBCOMPONENT Definitive article → TASK Office Hours hub (Qwen draft, Astra reasoning, Trenton voice, jennifer A-)</text>
      <text x="64" y="1020" fill="#F8FAFC" font-family="ui-sans-serif, sans-serif" font-size="16">
        DEFINITIVE ARTICLE — How we run Thursday Office Hours (example hub at example.invalid)</text>
      <text x="64" y="1052" fill="#F8FAFC" font-family="ui-sans-serif, sans-serif" font-size="16">
        META ARTICLE — Office Hours run EXAMPLE-2026-09-25 (one execution; not a second recipe)</text>
      <text x="64" y="1088" fill="#F5A623" font-family="ui-sans-serif, sans-serif" font-size="16">
        STAGE Perform / MAA → Action: record the Q&amp;A the comments asked for → back to Produce</text>
      <text x="64" y="1124" fill="#94A3B8" font-family="ui-sans-serif, sans-serif" font-size="14">
        Same pattern on every leaf: a named seat sits on a task, the task hangs off a subcomponent,
        the subcomponent hangs off a locked stage, and only then do articles appear.</text>
    """
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}"
      viewBox="0 0 {width} {height}" role="img"
      aria-label="Content Factory hierarchy from stage to subcomponent to task to articles">
  <rect width="{width}" height="{height}" fill="#F4F1EA"/>
  <rect x="0" y="0" width="{width}" height="118" fill="#22698A"/>
  <text x="48" y="48" fill="#FFF7ED" font-family="Georgia, serif" font-size="34">
    Content Factory hierarchy</text>
  <text x="48" y="84" fill="#DBEAFE" font-family="ui-sans-serif, sans-serif" font-size="18">
    Stage → subcomponent → task → definitive article → meta article · agents sit on tasks, not on invented boxes</text>
  <text x="48" y="168" fill="#0F172A" font-family="Georgia, serif" font-size="20">
    Six stations, left to right. Gold connectors are depth inside a stage, not a second factory line.</text>
  <text x="48" y="196" fill="#475569" font-family="ui-sans-serif, sans-serif" font-size="14">
    Cost order: local Qwen (free) → Muse (volume) → everything else. Astra / Dot = thinking on the task, experimental,
    with a fresh second check on critical work. Current state still divides these tasks across the named desks.</text>
  {''.join(cards)}
  {example}
  <text x="48" y="1208" fill="#0F172A" font-family="Georgia, serif" font-size="20">How to read an X-ray</text>
  <text x="48" y="1240" fill="#334155" font-family="ui-sans-serif, sans-serif" font-size="15">
    The X-ray is this same tree with status (done / in progress / missing) and effectiveness
    (working / watch / weak / unknown) plus MAA numbers. Generate it from JSON — do not draw it by hand.</text>
  <text x="48" y="1272" fill="#334155" font-family="ui-sans-serif, sans-serif" font-size="15">
    python3 skills/content-factory/scripts/render_xray.py skills/content-factory/examples/xray-business.example.json --out /tmp/xray</text>
  <text x="48" y="1304" fill="#64748B" font-family="ui-sans-serif, sans-serif" font-size="12">
    Monogram badges; no official vendor marks in this file. Simple Icons (CC0) may be added later with the license noted.
    Do not invent seats. Do not rename Produce → Process → Post → Promote. Seat picker: standards/pick-the-cheapest-capable-fleet-lane.md.</text>
</svg>
"""
    return svg, width, height


def wrap_html(title: str, svg: str, note: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <title>{html.escape(title)}</title>
  <style>
    body {{ margin: 0; background: #1C1916; color: #F4F1EA; font-family: Georgia, serif; }}
    header {{ padding: 28px 40px 8px; }}
    h1 {{ margin: 0 0 8px; font-size: 30px; }}
    p {{ font-family: ui-sans-serif, sans-serif; color: #D6D3C9; max-width: 980px; }}
    .stage {{ background: #F4F1EA; }}
    footer {{ padding: 16px 40px 40px; font-family: ui-sans-serif, sans-serif; font-size: 12px; color: #A8A29E; }}
  </style>
</head>
<body>
  <header>
    <h1>{html.escape(title)}</h1>
    <p>{html.escape(note)}</p>
  </header>
  <div class="stage">{svg}</div>
  <footer>Locked line: Plumbing → Produce → Process → Post → Promote → Perform/MAA.
  Muse Maximum = 3B Muse tokens per week. Astra/Dot is experimental. Nothing public or paid without Dennis.</footer>
</body>
</html>
"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--png", action="store_true")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    visuals = {
        "agency-flow": (
            *agency_svg(),
            "Content Factory agency flow",
            "Swimlanes for the locked line. Muse on Spark is volume. Astra is thinking and experimental. Current desks still divide the work.",
        ),
        "hierarchy": (
            *hierarchy_svg(),
            "Content Factory hierarchy",
            "Stage → subcomponent → task → definitive article → meta article, with the named seat on each task.",
        ),
    }
    for name, (svg, width, height, title, note) in visuals.items():
        svg_path = args.out / f"{name}.svg"
        html_path = args.out / f"{name}.html"
        svg_path.write_text(svg, encoding="utf-8")
        html_path.write_text(wrap_html(title, svg, note), encoding="utf-8")
        print(svg_path)
        print(html_path)
        if args.png:
            bare = args.out / f"{name}.png.html"
            bare.write_text(
                f'<!DOCTYPE html><html><body style="margin:0;background:#F4F1EA">{svg}</body></html>',
                encoding="utf-8",
            )
            png_path = args.out / f"{name}.png"
            try:
                write_png(bare, png_path, width, height)
            except PngError as exc:
                print(f"visuals png failed: {exc}", file=sys.stderr)
                return 1
            finally:
                if bare.exists():
                    bare.unlink()
            print(png_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
