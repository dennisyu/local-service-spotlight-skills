#!/usr/bin/env python3
"""
render_charts.py - chart generator for the Google Ads Client View render stage

Deterministic chart generator for the weekly client report. Reads a per-client
trend CSV and emits two PNGs:
  {slug}_chart_leads_{date}.png
  {slug}_chart_cost-per-lead_{date}.png

This step does NO analysis. It only plots numbers that already exist in the
archived MAAs. Keeping it as pure code (not LLM) removes model variance from the
charts entirely.

Trend CSV contract (header row required), one row per week, oldest -> newest:
    week,leads,cpl_week,cpl_30d
    3/20,3,179.50,186.91
    4/10,5,163.92,
    ...
- week     : short label shown on the x-axis (e.g. "6/12")
- leads    : integer lead/conversion count for that week (primary campaign or
             account total, be consistent with the MAA)
- cpl_week : that week's cost per lead (blank if no conversions)
- cpl_30d  : the 30-day rolling cost per lead reported that week (blank if not
             reported; the line simply skips blanks)

Usage:
    python3 render_charts.py --data trend.csv --outdir ./out \
        --client "Summit Dumpster Rental" --date 2026-06-12 --target 80
"""
import argparse, csv, os, re

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

GREEN_HI, GREEN_MID, GREEN_LO = "#1f7a4d", "#3a9b6e", "#9ec9b4"
RED, BLUE, AMBER = "#c0392b", "#2c6fb3", "#c98a00"


def slugify(name):
    return re.sub(r"[^A-Za-z0-9]+", "", name)


def read_trend(path):
    weeks, leads, cplw, cpl30 = [], [], [], {}
    with open(path, newline="") as f:
        for i, row in enumerate(csv.DictReader(f)):
            weeks.append(row["week"].strip())
            leads.append(int(float(row["leads"])) if row.get("leads", "").strip() else 0)
            cw = row.get("cpl_week", "").strip()
            cplw.append(float(cw) if cw else None)
            c30 = row.get("cpl_30d", "").strip()
            if c30:
                cpl30[i] = float(c30)
    return weeks, leads, cplw, cpl30


def style():
    plt.rcParams.update({
        "font.family": "DejaVu Sans", "font.size": 12,
        "axes.edgecolor": "#cccccc", "axes.linewidth": 0.8, "figure.dpi": 160,
    })


def bar_color(v, mx):
    if v >= 0.85 * mx:
        return GREEN_HI
    if v >= 0.5 * mx:
        return GREEN_MID
    return GREEN_LO


def chart_leads(weeks, leads, outpath):
    style()
    fig, ax = plt.subplots(figsize=(6.4, 3.5))
    mx = max(leads) if leads else 1
    top = mx * 1.15 or 1
    for i, v in enumerate(leads):
        ax.bar(i, v, color=bar_color(v, mx), width=0.62, zorder=3)
        ax.text(i, v + top * 0.02, str(v), ha="center", va="bottom",
                fontsize=11, fontweight="bold", color="#2a2a2a")
    ax.set_xticks(range(len(weeks)))
    ax.set_xticklabels(weeks, fontsize=9, color="#666")
    ax.set_ylim(0, top)
    ax.tick_params(axis="y", labelcolor="#999", labelsize=9)
    ax.grid(axis="y", color="#eeeeee", zorder=0)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.set_title("Leads per week", fontsize=13, fontweight="bold",
                 color="#1d1d1f", loc="left", pad=10)
    fig.tight_layout()
    fig.savefig(outpath, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def chart_cpl(weeks, cplw, cpl30, target, outpath):
    style()
    fig, ax = plt.subplots(figsize=(6.4, 3.5))
    vals = [v for v in cplw if v is not None] + list(cpl30.values()) + [target]
    top = max(vals) * 1.12 if vals else 100
    if target:
        ax.axhline(target, color=AMBER, ls="--", lw=1.6, zorder=2)
        ax.text(0, target + top * 0.012, f"${int(target)} target",
                color=AMBER, fontsize=9.5, fontweight="bold", va="bottom")
    if cpl30:
        xs = sorted(cpl30)
        ax.plot(xs, [cpl30[i] for i in xs], color=BLUE, lw=2.4, ls=(0, (2, 2)),
                marker="o", ms=4, zorder=3, label="30-day average")
    xw = [i for i, v in enumerate(cplw) if v is not None]
    yw = [cplw[i] for i in xw]
    ax.plot(xw, yw, color=RED, lw=2.6, marker="o", ms=4.5, zorder=4,
            label="This week's cost")
    # endpoint labels
    if yw:
        li = xw[-1]
        ax.text(li, cplw[li] - top * 0.055, f"${int(round(cplw[li]))}",
                color=RED, fontsize=11, fontweight="bold", ha="center")
    if cpl30:
        l30 = sorted(cpl30)[-1]
        ax.text(l30, cpl30[l30] + top * 0.025, f"${int(round(cpl30[l30]))}",
                color=BLUE, fontsize=11, fontweight="bold", ha="center")
    ax.set_xticks(range(len(weeks)))
    ax.set_xticklabels(weeks, fontsize=9, color="#666")
    ax.set_ylim(0, top)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"${int(v)}"))
    ax.tick_params(axis="y", labelcolor="#999", labelsize=9)
    ax.grid(axis="y", color="#eeeeee", zorder=0)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.set_title("Cost per lead", fontsize=13, fontweight="bold",
                 color="#1d1d1f", loc="left", pad=10)
    ax.legend(loc="upper right", fontsize=9, frameon=False)
    fig.tight_layout()
    fig.savefig(outpath, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--data", required=True, help="trend CSV path")
    p.add_argument("--outdir", required=True)
    p.add_argument("--client", required=True)
    p.add_argument("--date", required=True, help="report date YYYY-MM-DD")
    p.add_argument("--target", type=float, default=0, help="target CPA for guide line")
    a = p.parse_args()

    weeks, leads, cplw, cpl30 = read_trend(a.data)
    os.makedirs(a.outdir, exist_ok=True)
    slug = slugify(a.client)
    leads_png = os.path.join(a.outdir, f"{slug}_chart_leads_{a.date}.png")
    cpl_png = os.path.join(a.outdir, f"{slug}_chart_cost-per-lead_{a.date}.png")
    chart_leads(weeks, leads, leads_png)
    chart_cpl(weeks, cplw, cpl30, a.target, cpl_png)
    print(leads_png)
    print(cpl_png)


if __name__ == "__main__":
    main()
