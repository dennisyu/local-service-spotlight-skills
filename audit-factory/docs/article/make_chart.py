"""Draw the cost chart in the article package from the kit's own numbers.

    python audit-factory/docs/article/make_chart.py

Writes two shapes of the same chart: img/cost-per-audit.png (wide, for desktop) and
img/cost-per-audit-phone.png (tall, with bigger type, for screens under 600px; the article
picks it with <picture>). The all-Claude reference and the two estimates come from
factory20.cost, the same functions `python -m factory20 cost` prints, so the chart cannot
drift from the cost model. The blind test's $2.45 is the one measured session cost the cost
model does not hold; it is copied from the blind-test table in docs/CALIBRATION.md.
"""
from __future__ import annotations

import pathlib
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

# Inter where it is installed, DejaVu Sans (bundled with matplotlib) everywhere else.
plt.rcParams["font.family"] = ["Inter", "DejaVu Sans"]

HERE = pathlib.Path(__file__).resolve().parent
KIT = HERE.parent.parent
sys.path.insert(0, str(KIT))
from factory20 import cost as K  # noqa: E402

BLIND_TEST_USD = 2.45        # docs/CALIBRATION.md, "Blind tests": Sonnet 5.5 + kit, clean run
SURFACE, BAR, INK, MUTED, FAINT, GRID = "#fcfcfb", "#2a78d6", "#111111", "#5b5b5b", "#7a7a7a", "#e6e6e6"
TITLE = "Model fees for one 20-page audit, in US dollars"
SOURCES = "Sources: audit-factory/docs/CALIBRATION.md and config/routing.json in the public kit, Nov 4, 2026."


def numbers() -> list[dict]:
    cfg = K.load_routing()
    ref = K.reference_cost(cfg)["audit_usd"]
    std = K.measured_range("standard", cfg)["typical"]["total_usd"]
    lean = K.measured_range("openrouter-lean", cfg)["typical"]["total_usd"]
    return [
        {"label": "All-Claude audit, Oct 23: research,\nwriting and 7 review rounds (measured)", "usd": ref, "measured": True},
        {"label": "Sonnet + the kit, writing from Claude's\nresearch, no review (measured, Nov 4)", "usd": BLIND_TEST_USD, "measured": True},
        {"label": "Standard tier via the API, writing from\nresearch + 1 Opus review (estimate)", "usd": std, "measured": False},
        {"label": "One OpenRouter key, lean tier, writing\nfrom research + 1 Opus review (estimate)", "usd": lean, "measured": False},
    ]


def money(v: float) -> str:
    return f"${v:,.0f}" if v >= 100 else f"${v:,.2f}"


def _value(r: dict) -> str:
    return money(r["usd"]) if r["measured"] else f"{money(r['usd'])}  estimate"


def _frame(ax, top: int, step: int, size: float) -> None:
    ax.set_xlim(0, top)
    ticks = list(range(0, 301, step))
    ax.set_xticks(ticks)
    ax.set_xticklabels([f"${x}" for x in ticks], fontsize=size, color=FAINT)
    ax.tick_params(axis="both", length=0, pad=6)
    ax.grid(axis="x", color=GRID, linewidth=1, zorder=0)
    for side in ("top", "right", "bottom", "left"):
        ax.spines[side].set_visible(False)


def draw_wide(rows: list[dict], out: pathlib.Path) -> None:
    fig = plt.figure(figsize=(8.8, 4.6), dpi=200, facecolor=SURFACE)
    ax = fig.add_axes([0.40, 0.20, 0.555, 0.56], facecolor=SURFACE)
    ys = list(range(len(rows)))[::-1]                 # first row on top
    ax.barh(ys, [r["usd"] for r in rows], height=0.55, color=BAR, zorder=3)
    for y, r in zip(ys, rows):
        ax.text(r["usd"] + 300 * 0.012, y, _value(r), va="center", ha="left", fontsize=12.5,
                fontweight="bold", color=INK, zorder=4)
    ax.set_yticks(ys)
    ax.set_yticklabels([r["label"] for r in rows], fontsize=10.5, color=INK)
    _frame(ax, 300, 50, 10)
    fig.text(0.015, 0.955, TITLE, fontsize=16.5, fontweight="bold", color=INK, va="top")
    fig.text(0.015, 0.885,
             "Measured = token counts at list price. Estimate = counted from a real audit's prompt and reply sizes,\n"
             "thinking included; the first live bill replaces it. The bottom three start from research already done.",
             fontsize=10.5, color=MUTED, va="top", linespacing=1.45)
    fig.text(0.015, 0.098,
             "Research for a new subject adds data fees (about $0.50) and the research model's tokens. "
             "OpenRouter also charges a fee when you buy credits.\n" + SOURCES,
             fontsize=8.6, color=FAINT, va="top", linespacing=1.5)
    fig.savefig(out, dpi=200, facecolor=SURFACE)
    plt.close(fig)


def draw_phone(rows: list[dict], out: pathlib.Path) -> None:
    fig = plt.figure(figsize=(4.5, 6.4), dpi=200, facecolor=SURFACE)
    ax = fig.add_axes([0.045, 0.165, 0.91, 0.545], facecolor=SURFACE)
    ys = list(range(len(rows)))[::-1]
    ax.barh(ys, [r["usd"] for r in rows], height=0.28, color=BAR, zorder=3)
    for y, r in zip(ys, rows):
        ax.text(0, y + 0.19, r["label"], va="bottom", ha="left", fontsize=10, color=INK,
                linespacing=1.3, zorder=4)
        ax.text(r["usd"] + 340 * 0.015, y, _value(r), va="center", ha="left", fontsize=12,
                fontweight="bold", color=INK, zorder=4)
    ax.set_ylim(-0.42, len(rows) - 0.25)
    ax.set_yticks([])
    _frame(ax, 340, 100, 9.5)
    fig.text(0.045, 0.975, "Model fees for one 20-page\naudit, in US dollars", fontsize=15, fontweight="bold",
             color=INK, va="top", linespacing=1.2)
    fig.text(0.045, 0.868,
             "Measured = token counts at list price.\n"
             "Estimate = a real audit's prompt and reply\n"
             "sizes, thinking included, until the first live\n"
             "bill. The bottom three start from finished research.",
             fontsize=9.5, color=MUTED, va="top", linespacing=1.4)
    fig.text(0.045, 0.105,
             "Research for a new subject adds data fees (about $0.50)\n"
             "and the research model's tokens. Sources: CALIBRATION.md\n"
             "and routing.json in the public kit, Nov 4, 2026.",
             fontsize=8, color=FAINT, va="top", linespacing=1.4)
    fig.savefig(out, dpi=200, facecolor=SURFACE)
    plt.close(fig)


def draw(folder: pathlib.Path) -> list[dict]:
    rows = numbers()
    folder.mkdir(parents=True, exist_ok=True)
    draw_wide(rows, folder / "cost-per-audit.png")
    draw_phone(rows, folder / "cost-per-audit-phone.png")
    return rows


if __name__ == "__main__":
    img = HERE / "img"
    for r in draw(img):
        print(f"{money(r['usd']):>8}  {'measured' if r['measured'] else 'estimate'}  {r['label'].replace(chr(10), ' ')}")
    print(f"wrote {img / 'cost-per-audit.png'} and {img / 'cost-per-audit-phone.png'}")
