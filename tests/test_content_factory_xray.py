import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RENDER = ROOT / "skills" / "content-factory" / "scripts" / "render_xray.py"
VISUALS = ROOT / "skills" / "content-factory" / "scripts" / "render_factory_visuals.py"
FLEET_MAP = ROOT / "skills" / "content-factory" / "references" / "fleet-orchestration.md"
EXAMPLES = sorted(
    (ROOT / "skills" / "content-factory" / "examples").glob("xray-*.example.json")
)

# Desks and seats named in references/fleet-orchestration.md. An X-ray owner
# outside this set is an invented agent.
NAMED_SEATS = {
    "Austin",
    "Trenton",
    "Tanner",
    "Q",
    "Alex",
    "Sam",
    "Mario",
    "Meter Maid",
    "Data",
    "Muse / Happy",
    "Kimi/Codex crons",
    "Claude Fleet",
    "Cursor cloud",
    "Dennis",
}


def _render(snapshot: dict, temp: str) -> subprocess.CompletedProcess:
    path = Path(temp) / "snapshot.json"
    path.write_text(json.dumps(snapshot), encoding="utf-8")
    return subprocess.run(
        [sys.executable, str(RENDER), str(path), "--out", temp],
        capture_output=True,
        text=True,
    )


class ContentFactoryXrayTests(unittest.TestCase):
    def test_example_owners_are_named_seats_from_the_fleet_map(self):
        map_text = FLEET_MAP.read_text(encoding="utf-8")
        for path in EXAMPLES:
            data = json.loads(path.read_text(encoding="utf-8"))
            for stage in data["stages"]:
                self.assertIn(stage["owner"], NAMED_SEATS, f"{path.name}:{stage['id']}")
                self.assertNotIn(stage["owner"], {"Astra", "Dot"}, "Dot is never an owner")
                for sub in stage.get("subcomponents") or []:
                    for task in sub.get("tasks") or []:
                        self.assertIn(task["owner"], NAMED_SEATS, f"{path.name}:{task['id']}")
                        self.assertNotIn(task["owner"], {"Astra", "Dot"}, "Dot is never an owner")
        for name in NAMED_SEATS - {"Cursor cloud", "Kimi/Codex crons", "Muse / Happy"}:
            self.assertIn(name, map_text, f"{name} is not on the fleet map")

    def test_accepts_other_lane_and_shows_seat_label(self):
        data = json.loads(EXAMPLES[0].read_text(encoding="utf-8"))
        data["stages"][2]["lane"] = "other"
        with tempfile.TemporaryDirectory() as temp:
            proc = _render(data, temp)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            svg = (Path(temp) / f"{data['id']}.svg").read_text(encoding="utf-8")
            self.assertIn("Seat: Other seat", svg)
            self.assertIn("* on a metric = example number", svg)
            self.assertIn("pick-the-cheapest-capable-fleet-lane", svg)

    def test_rejects_unknown_lane_and_missing_task_fields(self):
        base = json.loads(EXAMPLES[0].read_text(encoding="utf-8"))
        cases = []
        bad = json.loads(json.dumps(base))
        bad["stages"][1]["lane"] = "gemini"
        cases.append((bad, "lane must be one of"))
        bad = json.loads(json.dumps(base))
        del bad["stages"][1]["subcomponents"][0]["tasks"][0]["label"]
        cases.append((bad, "label must be a non-empty string"))
        bad = json.loads(json.dumps(base))
        del bad["stages"][1]["subcomponents"][0]["tasks"][0]["owner"]
        cases.append((bad, "owner (name the accountable desk"))
        bad = json.loads(json.dumps(base))
        bad["stages"][5]["metrics"][2]["value"] = "1240"
        cases.append((bad, "value must be a number or null"))
        bad = json.loads(json.dumps(base))
        for task in bad["stages"][2]["subcomponents"][1]["tasks"]:
            for article in task["articles"]:
                article.pop("execution_id", None)
        cases.append((bad, "execution_id"))
        for snapshot, needle in cases:
            with tempfile.TemporaryDirectory() as temp:
                proc = _render(snapshot, temp)
                self.assertEqual(proc.returncode, 2, needle)
                self.assertIn(needle, proc.stderr)

    def test_long_text_grows_the_canvas_instead_of_overlapping(self):
        data = json.loads(EXAMPLES[0].read_text(encoding="utf-8"))
        stage = data["stages"][2]
        stage["handoff_in"] = "A very long handoff that names the artifact and the place it lives " * 3
        stage["subcomponents"] = [
            {
                "id": "transcribe-mine",
                "label": "Transcribe & mine",
                "status": "in_progress",
                "tasks": [
                    {
                        "id": f"task-{i}",
                        "label": "A long task label that forces the wrap logic to use several lines " * 4,
                        "status": "in_progress",
                        "owner": "Trenton",
                        "lane": "qwen",
                        "articles": [],
                    }
                    for i in range(6)
                ],
            }
        ]
        data["loop"]["analysis"] = "EXAMPLE DATA — " + "a long analysis sentence " * 20
        with tempfile.TemporaryDirectory() as temp:
            short = _render(json.loads(EXAMPLES[0].read_text(encoding="utf-8")), temp)
            short_svg = (Path(temp) / f"{data['id']}.svg").read_text(encoding="utf-8")
            long = _render(data, temp)
            long_svg = (Path(temp) / f"{data['id']}.svg").read_text(encoding="utf-8")
        self.assertEqual(short.returncode, 0, short.stderr)
        self.assertEqual(long.returncode, 0, long.stderr)
        height = lambda svg: int(svg.split('height="', 1)[1].split('"', 1)[0])  # noqa: E731
        self.assertGreater(height(long_svg), height(short_svg))
        self.assertIn("+2 more", long_svg)
        self.assertIn(" …", long_svg)
    def test_three_example_kinds_exist(self):
        kinds = set()
        for path in EXAMPLES:
            data = json.loads(path.read_text(encoding="utf-8"))
            kinds.add(data["kind"])
            self.assertEqual(data["data_class"], "example")
            self.assertIn("EXAMPLE DATA", data["disclaimer"])
            self.assertTrue(
                all(m.get("example") is True for s in data["stages"] for m in s.get("metrics") or []),
                path,
            )
        self.assertEqual(kinds, {"business", "project", "content"})

    def test_examples_render_svg_with_banner_and_locked_stages(self):
        self.assertGreaterEqual(len(EXAMPLES), 3)
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp)
            for path in EXAMPLES:
                proc = subprocess.run(
                    [sys.executable, str(RENDER), str(path), "--out", str(out)],
                    check=True,
                    capture_output=True,
                    text=True,
                )
                data = json.loads(path.read_text(encoding="utf-8"))
                svg = (out / f"{data['id']}.svg").read_text(encoding="utf-8")
                self.assertIn("EXAMPLE DATA", svg)
                for label in (
                    "Plumbing",
                    "Produce",
                    "Process",
                    "Post",
                    "Promote",
                    "Perform / MAA",
                ):
                    self.assertIn(label, svg)
                self.assertIn("Action feeds Produce", svg)
                self.assertTrue((out / f"{data['id']}.html").is_file())
                self.assertIn(str(out / f"{data['id']}.svg"), proc.stdout)

    def test_rejects_renamed_stage(self):
        data = json.loads(EXAMPLES[0].read_text(encoding="utf-8"))
        data["stages"][1]["label"] = "Publish"
        with tempfile.TemporaryDirectory() as temp:
            bad = Path(temp) / "bad.json"
            bad.write_text(json.dumps(data), encoding="utf-8")
            proc = subprocess.run(
                [sys.executable, str(RENDER), str(bad), "--out", temp],
                capture_output=True,
                text=True,
            )
            self.assertEqual(proc.returncode, 2)
            self.assertIn("stages must be", proc.stderr)

    def test_rejects_example_metric_without_flag(self):
        data = json.loads(EXAMPLES[0].read_text(encoding="utf-8"))
        data["stages"][5]["metrics"][0]["example"] = False
        with tempfile.TemporaryDirectory() as temp:
            bad = Path(temp) / "bad.json"
            bad.write_text(json.dumps(data), encoding="utf-8")
            proc = subprocess.run(
                [sys.executable, str(RENDER), str(bad), "--out", temp],
                capture_output=True,
                text=True,
            )
            self.assertEqual(proc.returncode, 2)
            self.assertIn("example=true", proc.stderr)

    def test_agency_visual_names_muse_maximum_and_future_state(self):
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp)
            subprocess.run(
                [sys.executable, str(VISUALS), "--out", str(out)],
                check=True,
                capture_output=True,
                text=True,
            )
            flow = (out / "agency-flow.svg").read_text(encoding="utf-8")
            hierarchy = (out / "hierarchy.svg").read_text(encoding="utf-8")
            self.assertIn("3B Muse tokens per week", flow)
            self.assertIn("Future state", flow)
            self.assertIn("Muse on Spark", flow)
            self.assertIn("Astra", flow)
            self.assertIn("experimental", flow.lower())
            self.assertIn("Claude Fleet", flow)
            self.assertIn("Produce", flow)
            self.assertIn("Post", flow)
            self.assertIn("Promote", flow)
            # Cost order from standards/pick-the-cheapest-capable-fleet-lane.md
            self.assertIn("local Qwen → Muse → everything else", flow)
            self.assertLess(flow.index("1 · Free — Local Qwen"), flow.index("2 · Muse — the volume lane"))
            self.assertLess(flow.index("2 · Muse — the volume lane"), flow.index("3 · Everything else"))
            self.assertIn("fresh ChatGPT task checks critical work", flow)
            # Dollar figures the merged rule does not support must stay out
            for unsupported in ("$1K", "$80", "$200", "buggy"):
                self.assertNotIn(unsupported, flow)
                self.assertNotIn(unsupported, hierarchy)
            self.assertIn("pick-the-cheapest-capable-fleet-lane", hierarchy)
            self.assertIn("Stage → subcomponent → task", hierarchy)
            self.assertIn("META ARTICLE", hierarchy)
            self.assertIn("EXAMPLE DATA", hierarchy)
            self.assertTrue((out / "agency-flow.html").is_file())
            self.assertTrue((out / "hierarchy.html").is_file())


if __name__ == "__main__":
    unittest.main()
