import argparse
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.youtube_healing.models import EditReport, MediaProfile
from tools.youtube_healing.turbo_harness import run


def make_profile(source_path: str) -> MediaProfile:
    return MediaProfile(
        source_path=source_path,
        duration_seconds=30.0,
        width=1080,
        height=1920,
        video_codec="h264",
        audio_codec="aac",
        frame_rate=30.0,
        has_audio=True,
        orientation="vertical",
        youtube_format="shorts",
    )


def write_catalog(path: Path, music_path: Path) -> None:
    path.write_text(
        json.dumps(
            [
                {
                    "track_id": "musopen-calm",
                    "title": "Calm Piano",
                    "artist": "Example Artist",
                    "duration_seconds": 120,
                    "local_path": str(music_path),
                    "mood_tags": ["calm", "ambient"],
                    "has_vocals": False,
                    "strong_beat": False,
                    "evidence": {
                        "source_name": "Musopen",
                        "source_url": "https://musopen.org/music/1234-calm-piano/",
                        "license_terms": "Public domain recording for commercial and personal projects.",
                        "attribution_required": False,
                        "access_date": "2026-06-05",
                    },
                }
            ]
        ),
        encoding="utf-8",
    )


class TurboHarnessTests(unittest.TestCase):
    def make_args(self, root: Path, confirm_source_rights: bool) -> argparse.Namespace:
        return argparse.Namespace(
            topic="forest birds",
            use_existing_video="task-1/final-1.mp4",
            music_catalog=str(root / "music_catalog.json"),
            output_root=str(root / "outputs"),
            shooting_date="2026-06-05",
            general_location="generated",
            privacy_notes="no people visible",
            bilingual=False,
            turbo_root=str(root / "MoneyPrinterTurbo"),
            turbo_output=str(root / "MoneyPrinterTurbo" / "storage" / "tasks"),
            turbo_command="python main.py",
            confirm_source_rights=confirm_source_rights,
        )

    def test_run_renders_package_when_source_rights_are_confirmed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            turbo_root = root / "MoneyPrinterTurbo"
            turbo_output = turbo_root / "storage" / "tasks"
            source = turbo_output / "task-1" / "final-1.mp4"
            music = root / "calm.mp3"
            catalog = root / "music_catalog.json"
            source.parent.mkdir(parents=True)
            source.write_bytes(b"video")
            music.write_bytes(b"music")
            write_catalog(catalog, music)

            def fake_import(output_dir, input_root, video_name):
                return {"name": source.name, "path": str(source)}

            def fake_render(**kwargs):
                kwargs["output_video"].write_bytes(b"rendered")
                kwargs["thumbnail_path"].write_bytes(b"thumbnail")
                return EditReport(
                    output_path=str(kwargs["output_video"]),
                    thumbnail_path=str(kwargs["thumbnail_path"]),
                    ffmpeg_command=["ffmpeg"],
                )

            with (
                patch(
                    "tools.youtube_healing.turbo_harness.moneyprinter_engine_status",
                    return_value={"installed": True},
                ),
                patch(
                    "tools.youtube_healing.turbo_harness.list_turbo_videos",
                    return_value=[{"name": "task-1/final-1.mp4", "path": str(source)}],
                ),
                patch(
                    "tools.youtube_healing.turbo_harness.import_turbo_video",
                    side_effect=fake_import,
                ),
                patch(
                    "tools.youtube_healing.turbo_harness.profile_media",
                    return_value=make_profile(str(source)),
                ),
                patch(
                    "tools.youtube_healing.turbo_harness.render_video",
                    side_effect=fake_render,
                ),
            ):
                output_dir = run(self.make_args(root, confirm_source_rights=True))

            self.assertTrue((output_dir / "final_video.mp4").exists())
            self.assertTrue((output_dir / "thumbnail.jpg").exists())
            self.assertTrue((output_dir / "youtube_metadata.md").exists())
            self.assertTrue((output_dir / "edit_report.json").exists())
            self.assertTrue((output_dir / "publish_plan.json").exists())
            publish_plan = json.loads(
                (output_dir / "publish_plan.json").read_text(encoding="utf-8")
            )
            self.assertEqual(publish_plan["youtube"]["privacy_status"], "unlisted")
            metadata = (output_dir / "youtube_metadata.md").read_text(encoding="utf-8")
            self.assertIn("forest birds", metadata)
            self.assertIn("생성형 도구", metadata)
            self.assertNotIn("직접 촬영한", metadata)
            checklist = (output_dir / "approval_checklist.md").read_text(encoding="utf-8")
            self.assertIn("generated visuals and background music", checklist)
            self.assertNotIn("bird sound is primary", checklist)

    def test_run_blocks_rendering_when_source_rights_are_unconfirmed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            turbo_root = root / "MoneyPrinterTurbo"
            turbo_output = turbo_root / "storage" / "tasks"
            source = turbo_output / "task-1" / "final-1.mp4"
            music = root / "calm.mp3"
            catalog = root / "music_catalog.json"
            source.parent.mkdir(parents=True)
            source.write_bytes(b"video")
            music.write_bytes(b"music")
            write_catalog(catalog, music)

            with (
                patch(
                    "tools.youtube_healing.turbo_harness.moneyprinter_engine_status",
                    return_value={"installed": True},
                ),
                patch(
                    "tools.youtube_healing.turbo_harness.list_turbo_videos",
                    return_value=[{"name": "task-1/final-1.mp4", "path": str(source)}],
                ),
                patch(
                    "tools.youtube_healing.turbo_harness.import_turbo_video",
                    return_value={"name": source.name, "path": str(source)},
                ),
                patch(
                    "tools.youtube_healing.turbo_harness.profile_media",
                    return_value=make_profile(str(source)),
                ),
                patch("tools.youtube_healing.turbo_harness.render_video") as render_video,
            ):
                output_dir = run(self.make_args(root, confirm_source_rights=False))

            render_video.assert_not_called()
            self.assertFalse((output_dir / "final_video.mp4").exists())
            checklist = (output_dir / "approval_checklist.md").read_text(encoding="utf-8")
            self.assertIn("source_ownership_missing", checklist)


if __name__ == "__main__":
    unittest.main()
