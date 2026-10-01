#!/usr/bin/env python3
"""Render a Content Factory X-ray SVG/HTML from one snapshot file.

    python3 skills/content-factory/scripts/render_xray.py \\
        skills/content-factory/examples/xray-business.example.json \\
        --out /tmp/xray-business [--png]

Example snapshots must stay labeled EXAMPLE DATA. Observed snapshots must not
invent numbers. This script colors what the file already claims; it does not
infer effectiveness from raw values.

Exit codes: 0 rendered, 2 the snapshot failed validation, 1 the PNG step
failed after the SVG/HTML were written.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from png_shot import PngError, write_png  # noqa: E402

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
ARTICLE_KINDS = {"definitive", "meta"}
# Seats from standards/pick-the-cheapest-capable-fleet-lane.md in its cost
# order. cursor, claude-fleet and other are all that rule's "any other seat".
LANES = (
    "qwen",
    "muse",
    "astra",
    "kimi-codex",
    "grok-desk",
    "cursor",
    "claude-fleet",
    "other",
)
LANE_LABEL = {
    "qwen": "Local Qwen",
    "muse": "Muse on Spark",
    "astra": "Astra (experimental)",
    "kimi-codex": "Kimi/Codex cron",
    "grok-desk": "Grok desk",
    "cursor": "Cursor cloud",
    "claude-fleet": "Claude Fleet",
    "other": "Other seat",
}
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

WIDTH = 1480
MARGIN = 24
SANS = "ui-sans-serif, sans-serif"
SERIF = "Georgia, serif"


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


def _non_empty(value: object, where: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise XrayError(f"{where} must be a non-empty string")
    return value


def _kebab(value: object, where: str) -> str:
    if not isinstance(value, str) or not KEBAB.match(value):
        raise XrayError(f"{where} must be kebab-case")
    return value


def _one_of(value: object, allowed, where: str) -> str:
    if value not in allowed:
        raise XrayError(f"{where} must be one of {sorted(allowed)}, got {value!r}")
    return value  # type: ignore[return-value]


def validate(data: dict) -> dict:
    if _req(data, "schema_version") != "1.0":
        raise XrayError("schema_version must be '1.0'")
    _one_of(_req(data, "kind"), KINDS, "kind")
    _kebab(_req(data, "id"), "id")
    for key in (
        "title",
        "subject",
        "period",
        "generated_at",
        "data_class",
        "owner_function",
        "approval_gate",
    ):
        _non_empty(_req(data, key), key)
    _one_of(data["data_class"], {"example", "observed"}, "data_class")
    if data["data_class"] == "example":
        disclaimer = data.get("disclaimer") or ""
        if "EXAMPLE DATA" not in disclaimer:
            raise XrayError("example snapshots need a disclaimer containing 'EXAMPLE DATA'")
        if "example.invalid" not in json.dumps(data) and "EXAMPLE" not in data["period"]:
            raise XrayError("example snapshots must say EXAMPLE in period or use example.invalid URLs")
    hub = data.get("canonical_hub")
    if hub is not None and not isinstance(hub, str):
        raise XrayError("canonical_hub must be a URL string or null")
    stages = _req(data, "stages")
    if not isinstance(stages, list) or len(stages) != 6 or not all(isinstance(s, dict) for s in stages):
        raise XrayError("stages must be a list of the six locked stations")
    got = [(s.get("id"), s.get("label")) for s in stages]
    if got != LOCKED_STAGES:
        raise XrayError(f"stages must be {LOCKED_STAGES} in order, got {got}")
    for stage in stages:
        _validate_stage(stage, data["data_class"])
    loop = _req(data, "loop")
    if not isinstance(loop, dict):
        raise XrayError("loop must be an object")
    for key in ("metrics_summary", "analysis", "action", "feeds_produce"):
        _non_empty(loop.get(key), f"loop.{key}")
    _validate_articles(data.get("articles"), "snapshot")
    return data


def _validate_stage(stage: dict, data_class: str) -> None:
    where = f"stage {stage.get('id')}"
    for key in ("status", "effectiveness", "owner", "lane", "handoff_in", "handoff_out"):
        _non_empty(stage.get(key), f"{where}.{key}")
    _one_of(stage["status"], STATUSES, f"{where}.status")
    _one_of(stage["effectiveness"], EFFECTS, f"{where}.effectiveness")
    _one_of(stage["lane"], LANES, f"{where}.lane")
    metrics = stage.get("metrics")
    if metrics is None:
        metrics = []
    if not isinstance(metrics, list):
        raise XrayError(f"{where}.metrics must be a list")
    for metric in metrics:
        _validate_metric(metric, data_class, stage["id"])
    subs = stage.get("subcomponents")
    if subs is None:
        subs = []
    if not isinstance(subs, list):
        raise XrayError(f"{where}.subcomponents must be a list")
    for sub in subs:
        if not isinstance(sub, dict):
            raise XrayError(f"{where} subcomponents must be objects")
        sub_where = f"{where} subcomponent {sub.get('id')!r}"
        _kebab(sub.get("id"), f"{sub_where}.id")
        _non_empty(sub.get("label"), f"{sub_where}.label")
        _one_of(sub.get("status"), STATUSES, f"{sub_where}.status")
        tasks = sub.get("tasks")
        if tasks is None:
            tasks = []
        if not isinstance(tasks, list):
            raise XrayError(f"{sub_where}.tasks must be a list")
        for task in tasks:
            if not isinstance(task, dict):
                raise XrayError(f"{sub_where} tasks must be objects")
            task_where = f"{sub_where} task {task.get('id')!r}"
            _kebab(task.get("id"), f"{task_where}.id")
            _non_empty(task.get("label"), f"{task_where}.label")
            _one_of(task.get("status"), STATUSES, f"{task_where}.status")
            _non_empty(
                task.get("owner"),
                f"{task_where}.owner (name the accountable desk or seat from the fleet map)",
            )
            if task.get("lane") is not None:
                _one_of(task["lane"], LANES, f"{task_where}.lane")
            skill = task.get("skill")
            if skill is not None and not isinstance(skill, str):
                raise XrayError(f"{task_where}.skill must be a string or null")
            _validate_articles(task.get("articles"), task_where)


def _validate_articles(articles: object, where: str) -> None:
    if articles is None:
        return
    if not isinstance(articles, list):
        raise XrayError(f"{where}.articles must be a list")
    for index, article in enumerate(articles):
        here = f"{where}.articles[{index}]"
        if not isinstance(article, dict):
            raise XrayError(f"{here} must be an object")
        _one_of(article.get("kind"), ARTICLE_KINDS, f"{here}.kind")
        _non_empty(article.get("title"), f"{here}.title")
        _one_of(article.get("status"), STATUSES, f"{here}.status")
        url = article.get("url")
        if url is not None and not isinstance(url, str):
            raise XrayError(f"{here}.url must be a string or null")
        if article["kind"] == "meta":
            _non_empty(
                article.get("execution_id"),
                f"{here}.execution_id (a meta article records one execution)",
            )


def _validate_metric(metric: object, data_class: str, stage_id: str) -> None:
    if not isinstance(metric, dict) or not metric.get("name"):
        raise XrayError(f"metric on {stage_id} needs a name")
    name = metric["name"]
    value = metric.get("value")
    if isinstance(value, bool) or not (value is None or isinstance(value, (int, float))):
        raise XrayError(f"metric {name!r} on {stage_id}: value must be a number or null")
    if data_class == "example" and metric.get("example") is not True:
        raise XrayError(f"example metric {name!r} on {stage_id} must set example=true")
    if data_class == "observed" and metric.get("example") is True:
        raise XrayError(f"observed metric {name!r} on {stage_id} cannot be example=true")
    effect = metric.get("effectiveness")
    if effect is not None:
        _one_of(effect, EFFECTS, f"metric {name!r} on {stage_id} effectiveness")


def _esc(text: object) -> str:
    return html.escape(str(text), quote=True)


def _max_chars(width_px: int, font_px: int) -> int:
    # Sans-serif glyphs at these sizes average a little under 0.6em; using
    # 0.6em keeps every line inside its box so the PNG never clips.
    return max(8, int(width_px / (font_px * 0.6)))


def _wrap(text: str, width_px: int, font_px: int, max_lines: int | None = None) -> list[str]:
    """Greedy word wrap on a conservative average glyph width.

    When max_lines is set, the last kept line ends with an ellipsis instead of
    overflowing.
    """
    max_chars = _max_chars(width_px, font_px)
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
    lines = lines or [""]
    if max_lines is not None and len(lines) > max_lines:
        kept = lines[:max_lines]
        kept[-1] = kept[-1][: max(0, max_chars - 2)].rstrip() + " …"
        return kept
    return lines


def _fmt_value(metric: dict) -> str:
    value = metric.get("value")
    if value is None:
        return "—"
    if isinstance(value, float) and not value.is_integer():
        number = f"{abs(value):,.2f}"
    else:
        number = f"{abs(int(value)):,}"
    sign = "-" if value < 0 else ""
    if metric.get("unit") == "usd":
        return f"{sign}${number}"
    return f"{sign}{number}"


def _text(x: int, y: int, body: str, *, size: int, fill: str, font: str = SANS, anchor: str | None = None, weight: str | None = None) -> str:
    extra = f' text-anchor="{anchor}"' if anchor else ""
    extra += f' font-weight="{weight}"' if weight else ""
    return (
        f'<text x="{x}" y="{y}" fill="{fill}" font-family="{font}" font-size="{size}"{extra}>'
        f"{_esc(body)}</text>"
    )


def _legend(x: int, y: int) -> tuple[str, int]:
    items = [
        (STATUS_FILL["done"], "Done"),
        (STATUS_FILL["in_progress"], "In progress"),
        (STATUS_FILL["missing"], "Missing"),
        (EFFECT_FILL["working"], "Working"),
        (EFFECT_FILL["watch"], "Watch"),
        (EFFECT_FILL["weak"], "Weak"),
        (EFFECT_FILL["unknown"], "Unknown"),
    ]
    parts = []
    cursor = x
    for fill, label in items:
        parts.append(
            f'<rect x="{cursor}" y="{y}" width="118" height="22" rx="11" fill="{fill}"/>'
            + _text(cursor + 59, y + 16, label, size=12, fill="#FFF7ED", anchor="middle")
        )
        cursor += 126
    caption = (
        "First three pills = station status. Next four = effectiveness of results, also the "
        "station's left bar and each metric chip. * on a metric = example number, not a measurement. "
        "Owner = accountable desk; seat = the lane doing the work (pick-the-cheapest-capable-fleet-lane)."
    )
    caption_lines = _wrap(caption, WIDTH - 2 * (x), 12)
    caption_svg = "".join(
        _text(x, y + 42 + i * 16, line, size=12, fill="#475569") for i, line in enumerate(caption_lines)
    )
    return "".join(parts) + caption_svg, y + 42 + 16 * (len(caption_lines) - 1)


def _stage_block(stage: dict, x: int, y: int, w: int) -> tuple[str, int]:
    effect = EFFECT_FILL[stage["effectiveness"]]
    status = STATUS_FILL[stage["status"]]
    inner_w = w - 36
    tasks = []
    for sub in stage.get("subcomponents") or []:
        for task in sub.get("tasks") or []:
            tasks.append(f"{sub['label']}: {task['label']} ({task['status'].replace('_', ' ')})")
    task_text = " · ".join(tasks[:4]) or "No tasks listed"
    task_lines = _wrap(task_text, inner_w, 12, max_lines=4)
    if len(tasks) > 4:
        # The marker must survive truncation; trim the last line to make room.
        suffix = f" · +{len(tasks) - 4} more"
        room = _max_chars(inner_w, 12) - len(suffix)
        last = task_lines[-1]
        if len(last) > room:
            last = last[: max(0, room - 2)].rstrip() + " …"
        task_lines[-1] = last + suffix

    metrics = stage.get("metrics") or []
    metric_bits = []
    mx = x + 430
    for metric in metrics[:5]:
        fill = EFFECT_FILL.get(metric.get("effectiveness") or "unknown", EFFECT_FILL["unknown"])
        label = f"{metric['name']} {_fmt_value(metric)}"
        if metric.get("example"):
            label += " *"
        metric_bits.append(
            f'<rect x="{mx}" y="{y + 18}" width="172" height="36" rx="8" fill="{fill}"/>'
            + _text(mx + 86, y + 41, label, size=12, fill="#FFF7ED", anchor="middle")
        )
        mx += 182
    if len(metrics) > 5:
        metric_bits.append(_text(mx, y + 41, f"+{len(metrics) - 5} more", size=12, fill="#64748B"))
    if not metric_bits:
        metric_bits.append(_text(x + 430, y + 42, "No MAA numbers connected", size=12, fill="#64748B"))

    owner_line = f"Owner: {stage['owner']} · Seat: {LANE_LABEL[stage['lane']]}"
    handoff = f"in: {stage['handoff_in']}  →  out: {stage['handoff_out']}"
    handoff_lines = _wrap(handoff, inner_w, 11, max_lines=2)

    task_y = y + 110
    task_svg = "".join(
        _text(x + 18, task_y + i * 16, line, size=12, fill="#1E293B") for i, line in enumerate(task_lines)
    )
    handoff_y = task_y + 16 * (len(task_lines) - 1) + 24
    handoff_svg = "".join(
        _text(x + 18, handoff_y + i * 15, line, size=11, fill="#64748B") for i, line in enumerate(handoff_lines)
    )
    bottom = handoff_y + 15 * (len(handoff_lines) - 1) + 14
    h = max(160, bottom - y)
    block = f"""
    <rect x="{x}" y="{y}" width="{w}" height="{h}" rx="14" fill="#FFFFFF" stroke="#D6D3C9"/>
    <rect x="{x}" y="{y}" width="10" height="{h}" rx="4" fill="{effect}"/>
    {_text(x + 28, y + 32, stage['label'], size=20, fill="#0F172A", font=SERIF)}
    <rect x="{x + 28}" y="{y + 44}" width="86" height="22" rx="11" fill="{status}"/>
    {_text(x + 71, y + 60, stage['status'].replace('_', ' '), size=11, fill="#FFF7ED", anchor="middle")}
    <rect x="{x + 122}" y="{y + 44}" width="96" height="22" rx="11" fill="{effect}"/>
    {_text(x + 170, y + 60, stage['effectiveness'], size=11, fill="#FFF7ED", anchor="middle")}
    {_text(x + 28, y + 88, owner_line, size=12, fill="#334155")}
    {''.join(metric_bits)}
    {task_svg}
    {handoff_svg}
    """
    return block, h


def _loop_block(loop: dict, x: int, y: int, w: int) -> tuple[str, int]:
    inner_w = w - 48
    rows = [
        (loop["metrics_summary"], "#E2E8F0", ""),
        (loop["analysis"], "#CBD5E1", "Analysis: "),
        (loop["action"], "#F8FAFC", "Action: "),
        (loop["feeds_produce"], "#F5A623", "Next Produce: "),
    ]
    parts = [_text(x + 24, y + 28, "MAA loop — Action feeds Produce", size=16, fill="#F5A623", font=SERIF)]
    cursor = y + 54
    for body, fill, prefix in rows:
        lines = _wrap(prefix + body, inner_w, 13)
        for line in lines:
            parts.append(_text(x + 24, cursor, line, size=13, fill=fill))
            cursor += 18
        cursor += 6
    h = cursor - y + 6
    return (
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="14" fill="#0F172A"/>' + "".join(parts),
        h,
    )


def render_svg(data: dict) -> tuple[str, int]:
    example = data["data_class"] == "example"
    y0 = 48 if example else 16
    banner = (
        f'<rect x="0" y="0" width="{WIDTH}" height="36" fill="#9F1239"/>'
        + _text(WIDTH // 2, 24, data["disclaimer"], size=15, fill="#FFF7ED", font=SERIF, anchor="middle", weight="700")
        if example
        else ""
    )
    meta = (
        f"kind={data['kind']} · owner function={data['owner_function']} · "
        f"approval={data['approval_gate']} · generated {data['generated_at']}"
    )
    legend_svg, legend_bottom = _legend(40, y0 + 104)

    y = legend_bottom + 28
    stage_svgs = []
    for stage in data["stages"]:
        block, h = _stage_block(stage, MARGIN, y, WIDTH - 2 * MARGIN)
        stage_svgs.append(block)
        y += h + 12
    loop_svg, loop_h = _loop_block(data["loop"], MARGIN, y + 4, WIDTH - 2 * MARGIN)
    y += 4 + loop_h + 22
    footer = _text(
        MARGIN,
        y,
        f"Generated by render_xray.py from {data['id']}.json · schema {data['schema_version']} · "
        "seats follow standards/pick-the-cheapest-capable-fleet-lane.md · nothing public or paid ships without Dennis",
        size=11,
        fill="#64748B",
    )
    height = y + 20
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{height}"
      viewBox="0 0 {WIDTH} {height}" role="img"
      aria-label="{_esc(data['title'])}">
  <rect width="{WIDTH}" height="{height}" fill="#F4F1EA"/>
  {banner}
  {_text(40, y0 + 36, data['title'], size=28, fill="#0F172A", font=SERIF)}
  {_text(40, y0 + 64, f"{data['subject']} · {data['period']}", size=15, fill="#334155")}
  {_text(40, y0 + 88, meta, size=13, fill="#475569")}
  {legend_svg}
  {''.join(stage_svgs)}
  {loop_svg}
  {footer}
</svg>
"""
    return svg, height


def render_html(data: dict, svg: str) -> str:
    notice = (
        "<p class='banner'>EXAMPLE DATA — illustration only. Do not treat these numbers as real. "
        "A * on a metric chip marks an example number.</p>"
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
    .wrap {{ max-width: {WIDTH}px; margin: 0 auto; padding: 24px; }}
    h1 {{ font-size: 28px; margin: 0 0 8px; }}
    .sub {{ font-family: ui-sans-serif, sans-serif; color: #D6D3C9; }}
    .banner {{ background: #9F1239; color: #FFF7ED; padding: 10px 14px; border-radius: 8px;
              font-family: ui-sans-serif, sans-serif; }}
    .svg {{ background: #F4F1EA; border-radius: 16px; overflow: hidden; margin-top: 16px; }}
    .svg svg {{ display: block; width: 100%; height: auto; }}
    footer {{ font-family: ui-sans-serif, sans-serif; font-size: 12px; color: #A8A29E; margin-top: 16px; }}
  </style>
</head>
<body>
  <div class="wrap">
    {notice}
    <h1>{_esc(data['title'])}</h1>
    <p class="sub">{_esc(data['subject'])}</p>
    <div class="svg">{svg}</div>
    <footer>Generated from the Content Factory X-ray schema. Approval gate: {_esc(data['approval_gate'])}.
      Nothing public or paid ships without Dennis.</footer>
  </div>
</body>
</html>
"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("snapshot", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--png", action="store_true", help="also capture a PNG with headless Chrome")
    args = parser.parse_args()
    try:
        data = validate(load_snapshot(args.snapshot))
    except (OSError, json.JSONDecodeError, XrayError) as exc:
        print(f"xray: {exc}", file=sys.stderr)
        return 2
    args.out.mkdir(parents=True, exist_ok=True)
    svg, height = render_svg(data)
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
            write_png(bare, png_path, WIDTH, height)
        except PngError as exc:
            print(f"xray png failed: {exc}", file=sys.stderr)
            return 1
        finally:
            if bare.exists():
                bare.unlink()
        print(png_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
