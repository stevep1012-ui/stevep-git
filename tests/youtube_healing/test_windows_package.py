import tempfile
import unittest
from pathlib import Path

from tools.youtube_healing.windows_package import build_windows_package_plan, write_windows_package


class WindowsPackageTests(unittest.TestCase):
    def test_build_windows_package_plan_includes_required_files(self):
        plan = build_windows_package_plan()

        self.assertIn("tools", plan["copy_dirs"])
        self.assertIn("web", plan["copy_dirs"])
        self.assertIn("Start-Windows.bat", plan["generated_files"])
        self.assertIn("Authorize-YouTube.bat", plan["generated_files"])
        self.assertIn("YouTube-OAuth-Setup-KO.txt", plan["generated_files"])
        self.assertIn("README-FIRST-KO.txt", plan["generated_files"])

    def test_write_windows_package_creates_launcher_and_readme(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "tools" / "youtube_healing").mkdir(parents=True)
            (root / "tools" / "youtube_healing" / "__init__.py").write_text("", encoding="utf-8")
            (root / "web").mkdir()
            (root / "web" / "index.html").write_text("<html></html>", encoding="utf-8")
            (root / "config" / "youtube_healing").mkdir(parents=True)
            (root / "config" / "youtube_healing" / "music_catalog.example.json").write_text("[]", encoding="utf-8")

            package_dir = write_windows_package(root, root / "dist" / "YoutubeBirdStudio-Windows")

            self.assertTrue((package_dir / "Start-Windows.bat").exists())
            self.assertTrue((package_dir / "Authorize-YouTube.bat").exists())
            self.assertTrue((package_dir / "Build-Exe-Windows.bat").exists())
            self.assertTrue((package_dir / "README-FIRST-KO.txt").exists())
            self.assertTrue((package_dir / "YouTube-OAuth-Setup-KO.txt").exists())
            self.assertTrue((package_dir / "secrets").exists())
            self.assertFalse((package_dir / "config" / "youtube_healing" / "youtube_token.json").exists())
            self.assertTrue((package_dir / "tools" / "youtube_healing" / "__init__.py").exists())
            self.assertTrue((package_dir / "web" / "index.html").exists())
            self.assertIn("Instagram", (package_dir / "README-FIRST-KO.txt").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
