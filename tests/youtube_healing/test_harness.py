import argparse
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.youtube_healing.harness import run
from tools.youtube_healing.models import EditReport, MediaProfile


def make_profile(source_path: str) -> MediaProfile:
    return MediaProfile(
        source_path=source_path,
        duration_seconds=37.1,
        width=1080,
        height=1920,
        video_codec="h264",
        audio_codec="aac",
        frame_rate=29.97,
        has_audio=True,
        orientation="vertical",
        youtube_format="shorts",
    )


class HarnessTests(unittest.TestCase):
    def test_music_selection_failure_writes_review_package_without_rendering(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "owned-birds.mp4"
            catalog = root / "music_catalog.json"
            output_root = root / "outputs"
            source.write_bytes(b"not a real video")
            catalog.write_text("[]\n", encoding="utf-8")
            args = argparse.Namespace(
                source=str(source),
                music_catalog=str(catalog),
                output_root=str(output_root),
                shooting_date="2026-05-29",
                general_location="forest",
                privacy_notes="no people visible",
                not_owned=False,
                bilingual=False,
            )

            with patch("tools.youtube_healing.harness.profile_media", return_value=make_profile(str(source))):
                output_dir = run(args)

            self.assertTrue((output_dir / "asset_manifest.json").exists())
            self.assertTrue((output_dir / "media_profile.json").exists())
            self.assertTrue((output_dir / "policy_report.json").exists())
            self.assertTrue((output_dir / "approval_checklist.md").exists())
            self.assertFalse((output_dir / "final_video.mp4").exists())
            self.assertFalse((output_dir / "thumbnail.jpg").exists())
            self.assertFalse((output_dir / "edit_report.json").exists())

            findings = json.loads((output_dir / "policy_report.json").read_text(encoding="utf-8"))
            self.assertTrue(any(finding["code"] == "music_selection_failed" for finding in findings))
            self.assertTrue(any(finding["blocking"] for finding in findings))
            checklist = (output_dir / "approval_checklist.md").read_text(encoding="utf-8")
            self.assertIn("Resolve blocker: music_selection_failed", checklist)

    def test_missing_music_file_writes_blocker_without_rendering(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "owned-birds.mp4"
            catalog = root / "music_catalog.json"
            output_root = root / "outputs"
            source.write_bytes(b"not a real video")
            catalog.write_text(
                json.dumps(
                    [
                        {
                            "track_id": "missing-file",
                            "title": "Calm Forest Pad",
                            "artist": "Example Artist",
                            "duration_seconds": 120,
                            "local_path": str(root / "missing.mp3"),
                            "mood_tags": ["calm", "ambient", "forest"],
                            "has_vocals": False,
                            "strong_beat": False,
                            "evidence": {
                                "source_name": "YouTube Audio Library",
                                "source_url": "https://studio.youtube.com/channel/audio-library",
                                "license_terms": "Use allowed in YouTube videos",
                                "attribution_required": False,
                                "access_date": "2026-05-28",
                            },
                        }
                    ]
                ),
                encoding="utf-8",
            )
            args = argparse.Namespace(
                source=str(source),
                music_catalog=str(catalog),
                output_root=str(output_root),
                shooting_date="2026-05-29",
                general_location="forest",
                privacy_notes="no people visible",
                not_owned=False,
                bilingual=False,
            )

            with (
                patch("tools.youtube_healing.harness.profile_media", return_value=make_profile(str(source))),
                patch("tools.youtube_healing.harness.render_video") as render_video,
            ):
                output_dir = run(args)

            render_video.assert_not_called()
            self.assertFalse((output_dir / "final_video.mp4").exists())
            findings = json.loads((output_dir / "policy_report.json").read_text(encoding="utf-8"))
            self.assertTrue(any(finding["code"] == "music_file_missing" for finding in findings))
            self.assertTrue(any(finding["blocking"] for finding in findings))
            checklist = (output_dir / "approval_checklist.md").read_text(encoding="utf-8")
            self.assertIn("Resolve blocker: music_file_missing", checklist)

    def test_repeated_source_same_day_uses_unique_output_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "owned-birds.mp4"
            catalog = root / "music_catalog.json"
            output_root = root / "outputs"
            music = root / "calm.mp3"
            source.write_bytes(b"not a real video")
            music.write_bytes(b"not real music")
            catalog.write_text(
                json.dumps(
                    [
                        {
                            "track_id": "valid-track",
                            "title": "Calm Forest Pad",
                            "artist": "Example Artist",
                            "duration_seconds": 120,
                            "local_path": str(music),
                            "mood_tags": ["calm", "ambient", "forest"],
                            "has_vocals": False,
                            "strong_beat": False,
                            "evidence": {
                                "source_name": "YouTube Audio Library",
                                "source_url": "https://studio.youtube.com/channel/audio-library",
                                "license_terms": "Use allowed in YouTube videos",
                                "attribution_required": False,
                                "access_date": "2026-05-28",
                            },
                        }
                    ]
                ),
                encoding="utf-8",
            )
            args = argparse.Namespace(
                source=str(source),
                music_catalog=str(catalog),
                output_root=str(output_root),
                shooting_date="2026-05-29",
                general_location="forest",
                privacy_notes="no people visible",
                not_owned=False,
                bilingual=False,
            )

            with (
                patch("tools.youtube_healing.harness.profile_media", return_value=make_profile(str(source))),
                patch(
                    "tools.youtube_healing.harness.render_video",
                    return_value=EditReport(
                        output_path=str(output_root / "final_video.mp4"),
                        thumbnail_path=str(output_root / "thumbnail.jpg"),
                        ffmpeg_command=["ffmpeg"],
                    ),
                ),
            ):
                first_output_dir = run(args)
                second_output_dir = run(args)

            self.assertNotEqual(first_output_dir, second_output_dir)
            self.assertEqual(second_output_dir.name, f"{first_output_dir.name}-2")


if __name__ == "__main__":
    unittest.main()
