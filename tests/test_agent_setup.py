"""Failure cases for portable setup source and handoff receipt gates."""

import json
import tempfile
import unittest
from pathlib import Path

from scripts.check_agent_setup import WORKSPACE_FILES, main, validate_receipt, validate_source, validate_workspace


def good_receipt():
    return {
        "schema_version": 1,
        "exercise": "practice",
        "task_id": "PRACTICE-001",
        "source_revision": "source-commit-abc",
        "scope": "Local synthetic exercise; no external action",
        "acceptance": "Receiver opens the same artifact; reviewer checks its two requested facts",
        "producer": {"agent": "Builder A", "runtime": "local session A"},
        "receiver": {"agent": "Receiver B", "runtime": "fresh local session B"},
        "artifact": {"ref": "agent-notes/practice.md", "revision": "sha256:artifact-abc"},
        "receiver_ack": {
            "artifact_ref": "agent-notes/practice.md",
            "artifact_revision": "sha256:artifact-abc",
            "evidence": "Local read transcript B, line 12",
            "observed_at": "2026-10-29T19:00:00-04:00",
        },
        "verification": {
            "reviewer": "Reviewer C",
            "result": "PASS",
            "evidence": "Local review C compares original task and artifact, lines 4-9",
            "observed_at": "2026-10-29T23:10:00Z",
        },
        "status": "VERIFIED",
    }


class ReceiptChecks(unittest.TestCase):
    def test_good_practice_packet(self):
        self.assertEqual(validate_receipt(good_receipt(), require_verified=True), [])

    def test_wrong_revision_fails(self):
        receipt = good_receipt()
        receipt["receiver_ack"]["artifact_revision"] = "old-revision"
        self.assertTrue(any("artifact_revision must match" in error for error in validate_receipt(receipt)))

    def test_missing_ack_cannot_be_delivered(self):
        for status in ("DELIVERED", "VERIFIED"):
            with self.subTest(status=status):
                receipt = good_receipt()
                receipt["status"] = status
                receipt["receiver_ack"] = None
                self.assertTrue(any("requires receiver_ack" in error for error in validate_receipt(receipt)))

    def test_self_review_cannot_be_verified(self):
        receipt = good_receipt()
        receipt["verification"]["reviewer"] = receipt["producer"]["agent"]
        self.assertTrue(any("reviewer different" in error for error in validate_receipt(receipt)))

    def test_naive_times_fail(self):
        for section in ("receiver_ack", "verification"):
            with self.subTest(section=section):
                receipt = good_receipt()
                receipt[section]["observed_at"] = "2026-10-29T23:00:00"
                self.assertTrue(any("timestamp with timezone" in error for error in validate_receipt(receipt)))

    def test_pass_without_evidence_fails(self):
        receipt = good_receipt()
        receipt["verification"]["evidence"] = " "
        self.assertTrue(any("PASS requires non-empty evidence" in error for error in validate_receipt(receipt)))

    def test_missing_required_field_fails(self):
        receipt = good_receipt()
        del receipt["acceptance"]
        self.assertIn("receipt is missing acceptance", validate_receipt(receipt))

    def test_false_verified_with_failed_review_fails(self):
        receipt = good_receipt()
        receipt["verification"]["result"] = "FAIL"
        self.assertIn("VERIFIED requires verification.result PASS", validate_receipt(receipt))

    def test_blocked_receipt_is_structurally_valid_but_fails_terminal_gate(self):
        receipt = good_receipt()
        receipt["receiver_ack"] = None
        receipt["verification"] = {"reviewer": "UNASSIGNED", "result": "NOT_CHECKED", "evidence": "", "observed_at": None}
        receipt["status"] = "BLOCKED"
        self.assertEqual(validate_receipt(receipt), [])
        self.assertTrue(any("terminal gate requires VERIFIED" in error for error in validate_receipt(receipt, require_verified=True)))

    def test_malformed_types_return_errors(self):
        receipt = good_receipt()
        receipt["producer"] = "builder"
        receipt["verification"] = None
        receipt["artifact"] = []
        self.assertGreaterEqual(len(validate_receipt(receipt)), 3)

    def test_non_scalar_enums_return_errors_instead_of_crashing(self):
        receipt = good_receipt()
        receipt["exercise"] = []
        receipt["status"] = {}
        receipt["verification"]["result"] = ["PASS"]
        self.assertGreaterEqual(len(validate_receipt(receipt)), 3)


class SourceChecks(unittest.TestCase):
    def make_source(self, root: Path):
        (root / "START-HERE.md").write_text("# Start\n\n[How](docs/how.md)\n", encoding="utf-8")
        (root / "docs").mkdir()
        (root / "docs/how.md").write_text("# How\n\n[Start](../START-HERE.md)\n", encoding="utf-8")
        templates = root / "templates/agent-workspace"
        templates.mkdir(parents=True)
        for name in WORKSPACE_FILES:
            path = templates / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("{}" if path.suffix == ".json" else "# Starter\n", encoding="utf-8")
        index = {"schema_version": 1, "entrypoint": "START-HERE.md", "docs": ["docs/how.md"], "templates_dir": "templates/agent-workspace"}
        (root / "agent-setup.json").write_text(json.dumps(index), encoding="utf-8")
        return index

    def test_good_source(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            self.make_source(root)
            self.assertEqual(validate_source(root), [])

    def test_null_index_fails(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            (root / "agent-setup.json").write_text("null", encoding="utf-8")
            self.assertIn("agent-setup.json must contain an object", validate_source(root))

    def test_index_path_escape_fails(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            index = self.make_source(root)
            index["docs"] = ["../outside.md"]
            (root / "agent-setup.json").write_text(json.dumps(index), encoding="utf-8")
            self.assertTrue(any("escapes the allowed root" in error for error in validate_source(root)))

    def test_malformed_index_paths_are_errors(self):
        for value in ("//[", "bad\x00path"):
            with self.subTest(value=value), tempfile.TemporaryDirectory() as name:
                root = Path(name)
                index = self.make_source(root)
                index["entrypoint"] = value
                (root / "agent-setup.json").write_text(json.dumps(index), encoding="utf-8")
                self.assertTrue(any("invalid local path" in error for error in validate_source(root)))

    def test_malformed_markdown_paths_are_errors(self):
        for value in ("//[", "bad\x00path"):
            with self.subTest(value=value), tempfile.TemporaryDirectory() as name:
                root = Path(name)
                self.make_source(root)
                (root / "docs/how.md").write_text(f"[Invalid]({value})", encoding="utf-8")
                self.assertTrue(any("invalid link path" in error for error in validate_source(root)))

    def test_markdown_path_escape_fails(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            self.make_source(root)
            (root / "docs/how.md").write_text("[Outside](../../outside.md)", encoding="utf-8")
            self.assertTrue(any("link escapes the allowed root" in error for error in validate_source(root)))

    def test_missing_markdown_target_fails(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            self.make_source(root)
            (root / "docs/how.md").write_text("[Missing](missing.md)", encoding="utf-8")
            self.assertTrue(any("missing local link target" in error for error in validate_source(root)))

    def test_symlink_escape_fails(self):
        with tempfile.TemporaryDirectory() as name, tempfile.TemporaryDirectory() as outside:
            root = Path(name)
            self.make_source(root)
            (root / "docs/escape.md").symlink_to(Path(outside) / "secret.md")
            (root / "docs/how.md").write_text("[Outside](escape.md)", encoding="utf-8")
            self.assertTrue(any("link escapes the allowed root" in error for error in validate_source(root)))

    def test_extra_template_markdown_symlink_cannot_be_read(self):
        with tempfile.TemporaryDirectory() as name, tempfile.TemporaryDirectory() as outside:
            root = Path(name)
            self.make_source(root)
            outside_file = Path(outside) / "outside.md"
            outside_file.write_bytes(b"\xff")
            (root / "templates/agent-workspace/outside.md").symlink_to(outside_file)
            # Invalid UTF-8 would crash if the outside file were read.
            self.assertTrue(any("escapes the allowed root" in error for error in validate_source(root)))

    def test_code_example_is_not_a_link(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            self.make_source(root)
            (root / "docs/how.md").write_text("```markdown\n[Example](not-a-real-target.md)\n```\n", encoding="utf-8")
            self.assertEqual(validate_source(root), [])

    def test_missing_workspace_file_fails(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            self.make_source(root)
            templates = root / "templates/agent-workspace"
            (templates / "status/NOW.md").unlink()
            self.assertIn("workspace is missing status/NOW.md", validate_workspace(templates))

    def test_receipt_cli_terminal_gate(self):
        with tempfile.TemporaryDirectory() as name:
            path = Path(name) / "receipt.json"
            path.write_text(json.dumps(good_receipt()), encoding="utf-8")
            self.assertEqual(main(["--receipt", str(path), "--require-verified"]), 0)


if __name__ == "__main__":
    unittest.main()
