"""Layout regressions for factory20 components (found on a 20-page audit run, 2026-11-10).

Each test renders one component to SVG/HTML and checks geometry directly, so it runs
without a browser: swimlane bars never hide each other, graph boxes never overlap,
zero bars draw nothing, timeline labels stay on the canvas, and the page-20 ledger
chart counts only ledger rows.
"""
from __future__ import annotations

import pathlib
import re
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1] / "audit-factory"
sys.path.insert(0, str(ROOT))

from factory20 import components as C  # noqa: E402
from factory20 import render  # noqa: E402


def ctx(actions=None, rows=None):
    audit = {"meta": {"subject": "Test Subject", "research_cutoff": "2026-11-12"},
             "actions": actions or [], "exams": {"brand_authority": {"rows": rows or []}}}
    return render.Ctx(audit, None, pathlib.Path("."))


def rects(svg: str, cls: str):
    out = []
    for m in re.finditer(r'<rect x="([-\d.]+)" y="([-\d.]+)" width="([-\d.]+)" height="([-\d.]+)"[^>]*class="([^"]*)"', svg):
        if cls in m.group(5).split():
            out.append(tuple(float(m.group(i)) for i in range(1, 5)))
    return out


def overlap(a, b, pad=0.0):
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    return ax < bx + bw - pad and bx < ax + aw - pad and ay < by + bh - pad and by < ay + ah - pad


class SwimlaneTests(unittest.TestCase):
    def test_every_bar_visible_when_a_lane_holds_many_actions(self):
        items = [{"id": f"A{i}", "lane": "Web", "start": 7, "end": 30, "executor": "AGENT_AFTER_APPROVAL"} for i in range(1, 6)]
        html = C.swimlane({"items": items}, ctx())
        bars = [r for r in rects(html, "bar") if r[3] == 12.0]  # action bars; legend swatches are 8px tall
        self.assertEqual(len(bars), 5)
        for i in range(len(bars)):
            for j in range(i + 1, len(bars)):
                self.assertFalse(overlap(bars[i], bars[j]), f"bars {i} and {j} overlap")
        for i in range(1, 6):
            self.assertIn(f">A{i}<", html)

    def test_executor_styles_and_legend(self):
        items = [{"id": "A1", "lane": "Owner", "start": 0, "end": 4, "executor": "HUMAN", "due": 0},
                 {"id": "A2", "lane": "Web", "start": 7, "end": 30, "executor": "AGENT_AFTER_APPROVAL"},
                 {"id": "A3", "lane": "Research", "start": 60, "end": 90, "executor": "AGENT"}]
        html = C.swimlane({"items": items}, ctx())
        self.assertIn("<path", html)               # dated person decision drawn as a diamond
        self.assertIn('class="bar ro"', html)      # read-only agent bar outlined
        self.assertIn("only a person can do it", html)
        self.assertIn("agent, read-only", html)

    def test_last_axis_label_is_end_anchored(self):
        html = C.swimlane({"items": [{"id": "A1", "lane": "Web", "start": 0, "end": 90}]}, ctx())
        self.assertRegex(html, r'text-anchor="end">Day 90<')


class GraphTests(unittest.TestCase):
    def test_no_node_boxes_overlap(self):
        nodes = [{"id": f"n{i}", "label": f"A fairly long node label {i}", "sub": "a sub-label that widens the box", "state": "OBSERVED"} for i in range(10)]
        edges = [{"from": "c", "to": f"n{i}", "type": "link", "label": "record"} for i in range(10)]
        html = C.graph({"nodes": nodes, "edges": edges, "center": {"id": "c", "label": "Center node"}, "span": 8, "height": 330}, ctx())
        boxes = [tuple(map(float, m.groups())) for m in re.finditer(r'<rect x="([-\d.]+)" y="([-\d.]+)" width="([-\d.]+)" height="([-\d.]+)" rx="5" class="node', html)]
        self.assertEqual(len(boxes), 11)
        for i in range(len(boxes)):
            for j in range(i + 1, len(boxes)):
                self.assertFalse(overlap(boxes[i], boxes[j], pad=1.0), f"node boxes {i} and {j} overlap")

    def test_legend_lists_only_drawn_styles_and_repeat_is_thick(self):
        html = C.graph({"nodes": [{"id": "a", "label": "Partner"}, {"id": "b", "label": "Host"}],
                        "edges": [{"from": "c", "to": "a", "type": "repeat"}, {"from": "c", "to": "b", "type": "interview"}],
                        "center": {"id": "c", "label": "Subject"}}, ctx())
        self.assertIn("stroke-width:2.8", html)
        self.assertIn("repeated work tie", html)
        self.assertIn("interview", html)
        self.assertNotIn("co-presence", html)


class SmallComponentTests(unittest.TestCase):
    def test_zero_bar_draws_no_rect(self):
        html = C.bars({"items": [{"label": "his sites", "value": 0, "display": "0"}, {"label": "others", "value": 28}]}, ctx())
        self.assertEqual(len(rects(html, "bar")), 1)
        pair = C._micro({"type": "pair", "a": {"label": "x", "value": 28}, "b": {"label": "y", "value": 0}}, ctx())
        self.assertIn("width:0.0%", pair)

    def test_unmeasured_bar_uses_display_text(self):
        html = C.bars({"items": [{"label": "AI engines", "value": None, "display": "UNTESTED"}]}, ctx())
        self.assertIn("UNTESTED", html)

    def test_doors_warn_state_has_no_strike_class(self):
        html = C._micro({"type": "doors", "items": [{"label": "role to confirm", "ok": "warn"}, {"label": "current", "ok": True}]}, ctx())
        self.assertIn('class="door warn"', html)
        self.assertIn('class="door ok"', html)

    def test_timeline_labels_stay_on_canvas(self):
        ev = [{"date": "inOrbit (undated)", "label": "a long first label that would clip at the left edge"},
              {"date": "Feb 2027", "label": "a long last label that would clip at the right edge"}]
        html = C.timeline({"events": ev, "span": 12}, ctx())
        self.assertIn('text-anchor="start"', html)
        self.assertIn('text-anchor="end"', html)

    def test_heatmap_short_label_and_provisional_mark(self):
        rows = [{"n": 2, "name": "Media relationships and offline authority", "label": "Media and offline authority", "score": 7},
                {"n": 5, "name": "Monetizable positioning", "score": 5, "provisional": True}]
        html = C.heatmap({"rows": rows, "auto": False}, ctx(rows=rows))
        self.assertIn("2. Media and offline authority", html)
        self.assertIn(">5*<", html)


class ReceiptTests(unittest.TestCase):
    def test_ledger_chart_counts_only_ledger_rows(self):
        from factory20.ledger import Ledger
        led = Ledger.load(ROOT / "fixtures" / "demo" / "ledger.json")
        blocks = render._receipt_blocks({"meta": {}, "pages": []}, led)
        chart = blocks[0]
        labels = [i["label"] for i in chart["items"]]
        self.assertFalse(any("namesake" in l or "conflict" in l or "unknown" in l for l in labels))
        self.assertIn("not counted", chart.get("caption", ""))

    def test_crosswalk_shows_partners_not_internal_name(self):
        blocks = render._receipt_blocks({"meta": {}, "pages": []}, None)
        xw = [b for b in blocks if b.get("title", "").startswith("Coverage crosswalk")][0]
        self.assertNotIn("lighthouse", [r[1] for r in xw["rows"]])
        self.assertIn("partners", [r[1] for r in xw["rows"]])


class LauncherTests(unittest.TestCase):
    def test_candidates_honour_env_override(self):
        import os
        import tempfile
        with tempfile.NamedTemporaryFile() as f:
            old = os.environ.get("FACTORY20_CHROMIUM")
            os.environ["FACTORY20_CHROMIUM"] = f.name
            try:
                self.assertEqual(render.chromium_candidates()[0], f.name)
            finally:
                if old is None:
                    os.environ.pop("FACTORY20_CHROMIUM")
                else:
                    os.environ["FACTORY20_CHROMIUM"] = old


if __name__ == "__main__":
    unittest.main()
