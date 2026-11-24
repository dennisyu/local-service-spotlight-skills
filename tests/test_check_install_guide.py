import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from check_install_guide import compare, manifest_facts, page_text  # noqa: E402


class InstallGuideTest(unittest.TestCase):
    facts = {"version": "1.11.0", "skill_count": 51}

    def test_matching_guide_passes(self):
        text = page_text("<p>Install <b>lss-everything</b> v1.11.0 (51 skills) from "
                         "github.com/dennisyu/local-service-spotlight-skills</p>")
        self.assertEqual([], compare(text, self.facts))

    def test_stale_version_and_count_fail(self):
        text = page_text("<p>lss-everything 1.10.0, 50 skills, github.com/dennisyu/local-service-spotlight-skills</p>")
        problems = compare(text, self.facts)
        self.assertTrue(any("1.11.0" in p for p in problems))
        self.assertTrue(any("51" in p for p in problems))

    def test_missing_repo_and_bundle_fail(self):
        problems = compare(page_text("<p>Version 1.11.0, 51 skills</p>"), self.facts)
        self.assertEqual(2, len(problems))

    def test_script_text_is_ignored(self):
        text = page_text("<script>var v='1.11.0 51 skills lss-everything github.com/dennisyu/local-service-spotlight-skills'</script>")
        self.assertEqual(4, len(compare(text, self.facts)))

    def test_repository_manifest_is_readable(self):
        facts = manifest_facts()
        self.assertRegex(facts["version"] or "", r"^\d+\.\d+\.\d+$")
        self.assertIsInstance(facts["skill_count"], int)


if __name__ == "__main__":
    unittest.main()
