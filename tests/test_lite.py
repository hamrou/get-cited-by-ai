import importlib.util
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("build_lite", ROOT / "tools" / "build_lite.py")
build = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build)

ALLOWED = {".md", ".txt", ".json", ".yaml", ".yml", ".png", ""}


class LitePluginTests(unittest.TestCase):
    def test_only_directory_safe_files(self):
        files = [p for p in (ROOT / "plugin-lite").rglob("*") if p.is_file()]
        self.assertTrue(files)
        for p in files:
            self.assertIn(p.suffix.lower(), ALLOWED, p)
            self.assertFalse(p.read_bytes().startswith(b"#!"), p)

    def test_lite_is_in_sync_with_the_full_skill(self):
        built = build.lite_skill()
        on_disk = (ROOT / "plugin-lite" / "skills" / "get-cited-by-ai" / "SKILL.md").read_text(encoding="utf-8")
        self.assertEqual(built, on_disk, "run: python tools/build_lite.py")

    def test_icon_is_square_png_in_range(self):
        import struct
        d = (ROOT / "plugin-lite" / ".claude-plugin" / "icon.png").read_bytes()
        w, h = struct.unpack(">II", d[16:24])
        self.assertEqual(w, h)
        self.assertTrue(512 <= w <= 2048)
        self.assertLess(len(d), 2_000_000)


if __name__ == "__main__":
    unittest.main()
