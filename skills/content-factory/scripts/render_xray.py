#!/usr/bin/env python3
"""Render a Content Factory X-ray SVG/HTML from one snapshot file.

    python3 skills/content-factory/scripts/render_xray.py \\
        skills/content-factory/examples/xray-business.example.json \\
        --out /tmp/xray-business [--png]

Example snapshots must stay labeled EXAMPLE DATA. Observed snapshots must not
invent numbers. This script colors what the file already claims; it does not
infer effectiveness from raw values.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
LOCKED_STAGES = [
    ("plumbing", "Plumbing"),
    ("produce", "Produce"),
    ("process", "Process"),
    ("post", "Post"),
    ("promote", "Promote"),
    ("perform", "Perform / MAA"),
]
KINDS = {"business", "project", "content"}
STATUSES = {"done", "in_progress", "missing"}
EFFECTS = {"working", "watch", "weak", "unknown", "missing"}
LANES = {"qwen", "muse", "astra", "kimi-codex", "grok-desk", "cursor", "claude-fleet"}
KEBAB = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")

STATUS_FILL = {
    "done": "#0F766E",
    "in_progress": "#C47B17",
    "missing": "#94A3B8",
}
EFFECT_FILL = {
    "working": "#157A4B",
    "watch": "#C47B17",
    "weak": "#B42318",
    "unknown": "#64748B",
    "missing": "#94A3B8",
}
LANE_LABEL = {
    "qwen": "Local Qwen",
    "muse": "Muse on Spark",
    "astra": "Astra (experimental)",
    "kimi-codex": "Kimi/Codex",
    "grok-desk": "Grok desk",
    "cursor": "Cursor cloud",
    "claude-fleet": "Claude Fleet",
}


class XrayError(ValueError):
    pass


def load_snapshot(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() in {".yaml", ".yml"}:
        try:
            import yaml  # type: ignore
        except ImportError as exc:
            raise XrayError("PyYAML is not installed; save the snapshot as JSON") from exc
        data = yaml.safe_load(text)
    else:
        data = json.loads(text)
    if not isinstance(data, dict):
        raise XrayError("snapshot must be a JSON/YAML object")
    return data


def _req(data: dict, key: str) -> object:
    if key not in data:
        raise XrayError(f"missing required field {key!r}")
    return data[key]


def validate(data: dict) -> dict:
    if _req(data, "schema_version") != "1.0":
        raise XrayError("schema_version must be '1.0'")
    kind = _req(data, "kind")
    if kind not in KINDS:
        raise XrayError(f"kind must be one of {sorted(KINDS)}")
    ident = _req(data, "id")
    if not isinstance(ident, str) or not KEBAB.match(ident):
        raise XrayError("id must be kebab-case")
    for key in (
        "title",
        "subject",
        "period",
        "generated_at",
        "data_class",
        "owner_function",
        "approval_gate",
    ):
        if not isinstance(_req(data, key), str) or not data[key].strip():
            raise XrayError(f"{key} must be a non-empty string")
    if data["data_class"] not in {"example", "observed"}:
        raise XrayError("data_class must be example or observed")
    if data["data_class"] == "example":
        disclaimer = data.get("disclaimer") or ""
        if "EXAMPLE DATA" not in disclaimer:
            raise XrayError("example snapshots need a disclaimer containing 'EXAMPLE DATA'")
        if "example.invalid" not in json.dumps(data) and "EXAMPLE" not in data["period"]:
            raise XrayError("example snapshots must say EXAMPLE in period or use example.invalid URLs")
    stages = _req(data, "stages")
    if not isinstance(stages, list) or len(stages) != 6:
        raise XrayError("stages must be a list of the six locked stations")
    got = [(s.get("id"), s.get("label")) for s in stages if isinstance(s, dict)]
    if got != LOCKED_STAGES:
        raise XrayError(f"stages must be {LOCKED_STAGES} in order, got {got}")
    for stage in stages:
        _validate_stage(stage, data["data_class"])
    loop = _req(data, "loop")
    if not isinstance(loop, dict):
        raise XrayError("loop must be an object")
    for key in ("metrics_summary", "analysis", "action", "feeds_produce"):
        if not isinstance(loop.get(key), str) or not loop[key].strip():
            raise XrayError(f"loop.{key} must be a non-empty string")
    return data


def _validate_stage(stage: dict, data_class: str) -> None:
    for key in ("status", "effectiveness", "owner", "lane", "handoff_in", "handoff_out"):
        if not isinstance(stage.get(key), str) or not stage[key].strip():
            raise XrayError(f"stage {stage.get('id')} missing {key}")
    if stage["status"] not in STATUSES:
        raise XrayError(f"bad status on {stage['id']}")
    if stage["effectiveness"] not in EFFECTS:
        raise XrayError(f"bad effectiveness on {stage['id']}")
    if stage["lane"] not in LANES:
        raise XrayError(f"unknown lane {stage['lane']!r} on {stage['id']}")
    for metric in stage.get("metrics") or []:
        _validate_metric(metric, data_class, stage["id"])
    for sub in stage.get("subcomponents") or []:
        if sub.get("status") not in STATUSES:
            raise XrayError(f"bad subcomponent status on {stage['id']}")
        for task in sub.get("tasks") or []:
            if task.get("status") not in STATUSES:
                raise XrayError(f"bad task status on {stage['id']}")
            if task.get("lane") and task["lane"] not in LANES:
                raise XrayError(f"unknown task lane {task.get('lane')!r}")


def _validate_metric(metric: dict, data_class: str, stage_id: str) -> None:
    if not isinstance(metric, dict) or not metric.get("name"):
        raise XrayError(f"metric on {stage_id} needs a name")
    if data_class == "example" and metric.get("example") is not True:
        raise XrayError(f"example metric {metric['name']!r} on {stage_id} must set example=true")
    if data_class == "observed" and metric.get("example") is True:
        raise XrayError(f"observed metric {metric['name']!r} on {stage_id} cannot be example=true")
    effect = metric.get("effectiveness")
    if effect and effect not in EFFECTS:
        raise XrayError(f"bad metric effectiveness on {stage_id}")


def _esc(text: object) -> str:
    return html.escape(str(text), quote=True)


def _wrap(text: str, width: int) -> list[str]:
    words = str(text).split()
    lines: list[str] = []
    current = ""
    for word in words:
        trial = f"{current} {word}".strip()
        if len(trial) > width and current:
            lines.append(current)
            current = word
        else:
            current = trial
    if current:
        lines.append(current)
    return lines or [""]


def render_svg(data: dict) -> str:
    width = 1480
    header_h = 196
    stage_h = 188
    loop_h = 168
    height = header_h + 6 * stage_h + loop_h + 36
    example = data["data_class"] == "example"
    banner = (
        '<rect x="0" y="0" width="1480" height="36" fill="#9F1239"/>'
        '<text x="740" y="24" text-anchor="middle" fill="#FFF7ED" '
        'font-family="Georgia, serif" font-size="15" font-weight="700">'
        f"{_esc(data['disclaimer'])}</text>"
        if example
        else ""
    )
    y0 = 48 if example else 16
    stages_svg = []
    y = y0 + 140
    for index, stage in enumerate(data["stages"]):
        stages_svg.append(_stage_block(stage, 24, y + index * stage_h, width - 48, stage_h - 16))
    loop = data["loop"]
    loop_y = y0 + 140 + 6 * stage_h
    loop_svg = f"""
    <rect x="24" y="{loop_y}" width="{width - 48}" height="{loop_h - 16}" rx="14" fill="#0F172A"/>
    <text x="48" y="{loop_y + 28}" fill="#F5A623" font-family="Georgia, serif" font-size="16">
      MAA loop — Action feeds Produce</text>
    <text x="48" y="{loop_y + 54}" fill="#E2E8F0" font-family="ui-sans-serif, sans-serif" font-size="13">
      {_esc(loop['metrics_summary'])}</text>
    <text x="48" y="{loop_y + 78}" fill="#CBD5E1" font-family="ui-sans-serif, sans-serif" font-size="13">
      Analysis: {_esc(loop['analysis'])}</text>
    <text x="48" y="{loop_y + 102}" fill="#F8FAFC" font-family="ui-sans-serif, sans-serif" font-size="13">
      Action: {_esc(loop['action'])}</text>
    <text x="48" y="{loop_y + 126}" fill="#F5A623" font-family="ui-sans-serif, sans-serif" font-size="13">
      Next Produce: {_esc(loop['feeds_produce'])}</text>
    """
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}"
      viewBox="0 0 {width} {height}" role="img"
      aria-label="{_esc(data['title'])}">
  <rect width="{width}" height="{height}" fill="#F4F1EA"/>
  {banner}
  <text x="40" y="{y0 + 36}" font-family="Georgia, serif" font-size="28" fill="#0F172A">
    {_esc(data['title'])}</text>
  <text x="40" y="{y0 + 64}" font-family="ui-sans-serif, sans-serif" font-size="15" fill="#334155">
    {_esc(data['subject'])} · {_esc(data['period'])}</text>
  <text x="40" y="{y0 + 88}" font-family="ui-sans-serif, sans-serif" font-size="13" fill="#475569">
    kind={_esc(data['kind'])} · owner function={_esc(data['owner_function'])}
    · approval={_esc(data['approval_gate'])} · generated { _esc(data['generated_at']) }</text>
  <g font-family="ui-sans-serif, sans-serif" font-size="12">
    {_legend_pills(40, y0 + 104)}
  </g>
  {''.join(stages_svg)}
  {loop_svg}
</svg>
"""


def _legend_pills(x: int, y: int) -> str:
    items = [
        ("done", STATUS_FILL["done"], "Done"),
        ("in_progress", STATUS_FILL["in_progress"], "In progress"),
        ("missing", STATUS_FILL["missing"], "Missing"),
        ("working", EFFECT_FILL["working"], "Working"),
        ("watch", EFFECT_FILL["watch"], "Watch"),
        ("weak", EFFECT_FILL["weak"], "Weak"),
    ]
    parts = []
    cursor = x
    for _key, fill, label in items:
        parts.append(
            f'<rect x="{cursor}" y="{y}" width="118" height="22" rx="11" fill="{fill}"/>'
            f'<text x="{cursor + 59}" y="{y + 16}" text-anchor="middle" fill="#FFF7ED">{label}</text>'
        )
        cursor += 126
    return "".join(parts)


def _stage_block(stage: dict, x: int, y: int, w: int, h: int) -> str:
    effect = EFFECT_FILL[stage["effectiveness"]]
    status = STATUS_FILL[stage["status"]]
    tasks = []
    for sub in stage.get("subcomponents") or []:
        for task in sub.get("tasks") or []:
            tasks.append(f"{sub['label']}: {task['label']} ({task['status'].replace('_', ' ')})")
    task_text = " · ".join(tasks[:3]) or "No tasks listed"
    metrics = stage.get("metrics") or []
    metric_bits = []
    mx = x + 430
    for metric in metrics[:4]:
        fill = EFFECT_FILL.get(metric.get("effectiveness") or "unknown", EFFECT_FILL["unknown"])
        value = metric["value"]
        shown = "—" if value is None else value
        label = f"{metric['name']} {shown}"
        if metric.get("example"):
            label += " *"
        metric_bits.append(
            f'<rect x="{mx}" y="{y + 18}" width="150" height="36" rx="8" fill="{fill}"/>'
            f'<text x="{mx + 75}" y="{y + 41}" text-anchor="middle" fill="#FFF7ED" '
            f'font-size="12" font-family="ui-sans-serif, sans-serif">{_esc(label)}</text>'
        )
        mx += 160
    if not metric_bits:
        metric_bits.append(
            f'<text x="{x + 430}" y="{y + 42}" fill="#64748B" font-size="12" '
            f'font-family="ui-sans-serif, sans-serif">No MAA numbers connected</text>'
        )
    lines = _wrap(task_text, 88)
    task_svg = "".join(
        f'<text x="{x + 18}" y="{y + 118 + i * 16}" fill="#1E293B" font-size="12" '
        f'font-family="ui-sans-serif, sans-serif">{_esc(line)}</text>'
        for i, line in enumerate(lines[:3])
    )
    return f"""
    <rect x="{x}" y="{y}" width="{w}" height="{h}" rx="14" fill="#FFFFFF" stroke="#D6D3C9"/>
    <rect x="{x}" y="{y}" width="10" height="{h}" rx="4" fill="{effect}"/>
    <text x="{x + 28}" y="{y + 32}" font-family="Georgia, serif" font-size="20" fill="#0F172A">
      {_esc(stage['label'])}</text>
    <rect x="{x + 28}" y="{y + 44}" width="86" height="22" rx="11" fill="{status}"/>
    <text x="{x + 71}" y="{y + 60}" text-anchor="middle" fill="#FFF7ED" font-size="11"
      font-family="ui-sans-serif, sans-serif">{_esc(stage['status'].replace('_', ' '))}</text>
    <rect x="{x + 122}" y="{y + 44}" width="96" height="22" rx="11" fill="{effect}"/>
    <text x="{x + 170}" y="{y + 60}" text-anchor="middle" fill="#FFF7ED" font-size="11"
      font-family="ui-sans-serif, sans-serif">{_esc(stage['effectiveness'])}</text>
    <text x="{x + 28}" y="{y + 88}" fill="#334155" font-size="12" font-family="ui-sans-serif, sans-serif">
      {_esc(stage['owner'])} · {_esc(LANE_LABEL[stage['lane']])}</text>
    {''.join(metric_bits)}
    {task_svg}
    <text x="{x + 18}" y="{y + h - 16}" fill="#64748B" font-size="11" font-family="ui-sans-serif, sans-serif">
      in: {_esc(stage['handoff_in'])}  →  out: {_esc(stage['handoff_out'])}</text>
    """


def render_html(data: dict, svg: str) -> str:
    notice = (
        "<p class='banner'>EXAMPLE DATA — illustration only. Do not treat these numbers as real.</p>"
        if data["data_class"] == "example"
        else ""
    )
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <title>{_esc(data['title'])}</title>
  <style>
    body {{ margin: 0; background: #1C1916; color: #F4F1EA; font-family: Georgia, serif; }}
    .wrap {{ max-width: 1480px; margin: 0 auto; padding: 24px; }}
    h1 {{ font-size: 28px; margin: 0 0 8px; }}
    .sub {{ font-family: ui-sans-serif, sans-serif; color: #D6D3C9; }}
    .banner {{ background: #9F1239; color: #FFF7ED; padding: 10px 14px; border-radius: 8px;
              font-family: ui-sans-serif, sans-serif; }}
    .svg {{ background: #F4F1EA; border-radius: 16px; overflow: hidden; margin-top: 16px; }}
    footer {{ font-family: ui-sans-serif, sans-serif; font-size: 12px; color: #A8A29E; margin-top: 16px; }}
  </style>
</head>
<body>
  <div class="wrap">
    {notice}
    <h1>{_esc(data['title'])}</h1>
    <p class="sub">{_esc(data['subject'])}</p>
    <div class="svg">{svg}</div>
    <footer>Generated from the Content Factory X-ray schema. Approval gate: Dennis for anything public or paid.</footer>
  </div>
</body>
</html>
"""


def write_png(html_path: Path, png_path: Path) -> None:
    chrome = shutil.which("google-chrome") or shutil.which("google-chrome-stable")
    if not chrome:
        raise XrayError("no Chromium on PATH; skip --png or install google-chrome")
    subprocess.run(
        [
            chrome,
            "--headless=new",
            "--disable-gpu",
            "--no-sandbox",
            "--hide-scrollbars",
            "--window-size=1480,1600",
            f"--screenshot={png_path}",
            html_path.resolve().as_uri(),
        ],
        check=True,
        capture_output=True,
        text=True,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("snapshot", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--png", action="store_true")
    args = parser.parse_args()
    try:
        data = validate(load_snapshot(args.snapshot))
    except (OSError, json.JSONDecodeError, XrayError) as exc:
        print(f"xray: {exc}", file=sys.stderr)
        return 2
    args.out.mkdir(parents=True, exist_ok=True)
    svg = render_svg(data)
    ident = data["id"]
    svg_path = args.out / f"{ident}.svg"
    html_path = args.out / f"{ident}.html"
    json_path = args.out / f"{ident}.json"
    svg_path.write_text(svg, encoding="utf-8")
    html_path.write_text(render_html(data, svg), encoding="utf-8")
    json_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print(svg_path)
    print(html_path)
    if args.png:
        png_path = args.out / f"{ident}.png"
        bare = args.out / f"{ident}.png.html"
        bare.write_text(
            f'<!DOCTYPE html><html><body style="margin:0;background:#F4F1EA">{svg}</body></html>',
            encoding="utf-8",
        )
        try:
            write_png(bare, png_path)
        except (XrayError, subprocess.CalledProcessError) as exc:
            print(f"xray png skipped: {exc}", file=sys.stderr)
            return 0
        finally:
            if bare.exists():
                bare.unlink()
        print(png_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
