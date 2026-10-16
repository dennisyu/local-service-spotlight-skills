import tempfile
import unittest
import zipfile
from pathlib import Path

from scripts.pack2plugin import build_plugin, kebab_name


class PackToPluginTests(unittest.TestCase):
    def test_stable_name_strips_release_suffix(self):
        self.assertEqual(kebab_name("DealCon-Skills-v3-11"), "dealcon-skills")

    def test_builds_plugin_and_repairs_skill_name(self):
        with tempfile.TemporaryDirectory() as temp_name:
            root = Path(temp_name)
            pack = root / "SOMBA-Skills-v2"
            skill = pack / "nested" / "Content Helper"
            skill.mkdir(parents=True)
            (skill / "SKILL.md").write_text(
                '---\nname: "wrong-name"\ndescription: "Test helper."\n---\n\n# Test\n',
                encoding="utf-8",
            )
            (pack / "commands").mkdir()
            (pack / "commands" / "cook.md").write_text("Cook.\n", encoding="utf-8")

            result = build_plugin(pack, root / "dist")

            self.assertEqual(result.name, "somba-skills.plugin")
            with zipfile.ZipFile(result) as archive:
                names = set(archive.namelist())
                self.assertIn(".claude-plugin/plugin.json", names)
                self.assertIn("skills/content-helper/SKILL.md", names)
                self.assertIn("commands/cook.md", names)
                skill_text = archive.read("skills/content-helper/SKILL.md").decode()
                self.assertIn('name: "content-helper"', skill_text)

    def test_rejects_zip_path_traversal(self):
        with tempfile.TemporaryDirectory() as temp_name:
            root = Path(temp_name)
            archive_path = root / "unsafe.zip"
            with zipfile.ZipFile(archive_path, "w") as archive:
                archive.writestr("../SKILL.md", "bad")
            with self.assertRaisesRegex(ValueError, "unsafe path"):
                build_plugin(archive_path, root / "dist")


if __name__ == "__main__":
    unittest.main()
