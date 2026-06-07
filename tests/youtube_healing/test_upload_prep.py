import tempfile
import unittest
from pathlib import Path

from tools.youtube_healing.models import PolicyFinding
from tools.youtube_healing.upload_prep import (
    safe_slug,
    write_approval_checklist,
    write_metadata_file,
)


class UploadPrepTests(unittest.TestCase):
    def test_safe_slug_handles_common_inputs(self):
        self.assertEqual(safe_slug("Morning Bird Song"), "morning-bird-song")
        self.assertEqual(safe_slug("Morning---Bird!!!Song"), "morning-bird-song")
        self.assertEqual(safe_slug("  forest___rain  "), "forest___rain")
        self.assertEqual(safe_slug(""), "youtube-healing-video")

    def test_safe_slug_preserves_korean_text(self):
        self.assertEqual(safe_slug("숲속 새소리.mp4"), "숲속-새소리-mp4")

    def test_write_metadata_file_writes_markdown_content(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "package" / "metadata.md"
            metadata_text = "# Title\n숲속 새소리 힐링 Shorts\n\n# Description\nCalm birdsong.\n"

            write_metadata_file(output, metadata_text)

            self.assertEqual(output.read_text(encoding="utf-8"), metadata_text)

    def test_write_approval_checklist_marks_blocking_finding(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "approval.md"
            finding = PolicyFinding(
                code="music_license_missing",
                severity="blocker",
                message="No music selection and license evidence are attached.",
                blocking=True,
            )

            write_approval_checklist(output, [finding])

            checklist = output.read_text(encoding="utf-8")
            self.assertIn("- [ ] Watch final video", checklist)
            self.assertIn("- [ ] Confirm bird sound is primary", checklist)
            self.assertIn("- [ ] Confirm music license evidence", checklist)
            self.assertIn(
                "- [ ] Confirm no private person/license plate/sensitive location",
                checklist,
            )
            self.assertIn(
                "- [ ] Confirm no medical/guaranteed wellness claims",
                checklist,
            )
            self.assertIn("## Policy Findings", checklist)
            self.assertIn(
                "- [ ] Resolve blocker: music_license_missing - No music selection and license evidence are attached.",
                checklist,
            )

    def test_write_approval_checklist_marks_non_blocking_finding_as_info(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "approval.md"
            finding = PolicyFinding(
                code="ready_for_review",
                severity="info",
                message="No blocking policy issues found.",
                blocking=False,
            )

            write_approval_checklist(output, [finding])

            checklist = output.read_text(encoding="utf-8")
            self.assertIn("- Info: ready_for_review - No blocking policy issues found.", checklist)
            self.assertNotIn("- [x]", checklist)

    def test_write_approval_checklist_supports_generated_video_audio_check(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "approval.md"

            write_approval_checklist(
                output,
                [],
                audio_check="Confirm generated visuals and background music are appropriate",
            )

            checklist = output.read_text(encoding="utf-8")
            self.assertIn(
                "- [ ] Confirm generated visuals and background music are appropriate",
                checklist,
            )
            self.assertNotIn("Confirm bird sound is primary", checklist)


if __name__ == "__main__":
    unittest.main()
