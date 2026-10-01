import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RENDER = ROOT / "skills" / "content-factory" / "scripts" / "render_xray.py"
VISUALS = ROOT / "skills" / "content-factory" / "scripts" / "render_factory_visuals.py"
EXAMPLES = sorted(
    (ROOT / "skills" / "content-factory" / "examples").glob("xray-*.example.json")
)


class ContentFactoryXrayTests(unittest.TestCase):
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
            self.assertIn("Stage → subcomponent → task", hierarchy)
            self.assertIn("META ARTICLE", hierarchy)
            self.assertIn("EXAMPLE DATA", hierarchy)
            self.assertTrue((out / "agency-flow.html").is_file())
            self.assertTrue((out / "hierarchy.html").is_file())


if __name__ == "__main__":
    unittest.main()
