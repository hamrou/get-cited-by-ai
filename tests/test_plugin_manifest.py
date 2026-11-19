import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class KimiPluginManifestTests(unittest.TestCase):
    def setUp(self):
        self.manifest = json.loads((ROOT / "kimi.plugin.json").read_text(encoding="utf-8"))

    def test_manifest_points_to_the_existing_skill(self):
        skills_root = ROOT / self.manifest["skills"]
        skill = skills_root / "get-cited-by-ai" / "SKILL.md"
        self.assertTrue(skill.is_file())
        content = skill.read_text(encoding="utf-8")
        self.assertIn("name: get-cited-by-ai", content)
        self.assertIn("description:", content)
        self.assertEqual(self.manifest["name"], "get-cited-by-ai")

    def test_kimi_and_claude_versions_stay_aligned(self):
        claude = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
        self.assertEqual(self.manifest["version"], claude["version"])

    def test_installation_does_not_autostart_or_register_execution_hooks(self):
        self.assertNotIn("sessionStart", self.manifest)
        self.assertNotIn("hooks", self.manifest)
        self.assertNotIn("mcpServers", self.manifest)


if __name__ == "__main__":
    unittest.main()
