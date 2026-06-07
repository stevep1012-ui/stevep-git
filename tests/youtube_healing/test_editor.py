import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.youtube_healing.editor import (
    build_ffmpeg_command,
    build_sequence_ffmpeg_command,
    build_thumbnail_command,
    render_video,
)
from tools.youtube_healing.models import (
    LicenseEvidence,
    MusicSelection,
    MusicTrack,
)


def _music_selection() -> MusicSelection:
    track = MusicTrack(
        track_id="yt-calm-001",
        title="Calm Forest Pad",
        artist="Example Artist",
        duration_seconds=120,
        local_path="/music/calm.mp3",
        mood_tags=["calm"],
        has_vocals=False,
        strong_beat=False,
        evidence=LicenseEvidence(
            source_name="YouTube Audio Library",
            source_url="https://studio.youtube.com/channel/audio-library",
            license_terms="Use allowed in YouTube videos",
            attribution_required=False,
            access_date="2026-05-28",
        ),
    )
    return MusicSelection(track=track, target_gain_db=-28.0, reason="Matched calm")


class EditorTests(unittest.TestCase):
    def test_build_ffmpeg_command_preserves_vertical_video_and_mixes_audio(self):
        command = build_ffmpeg_command(
            source_video=Path("/input/birds.mp4"),
            music_selection=_music_selection(),
            output_video=Path("/output/final_video.mp4"),
            duration_seconds=37.1,
        )

        self.assertEqual(command[0], "ffmpeg")
        self.assertIn("/input/birds.mp4", command)
        self.assertIn("/music/calm.mp3", command)
        self.assertIn("/output/final_video.mp4", command)
        self.assertIn("-filter_complex", command)
        self.assertIn("0:v:0", command)
        self.assertIn("-c:v", command)
        self.assertIn("libx264", command)
        self.assertIn("-stream_loop", command)
        self.assertIn("-t", command)
        self.assertIn("37.1", command)
        self.assertTrue(any("amix=inputs=2" in part for part in command))

    def test_build_ffmpeg_command_can_override_music_volume_for_preview(self):
        command = build_ffmpeg_command(
            source_video=Path("/input/birds.mp4"),
            music_selection=_music_selection(),
            output_video=Path("/output/volume_preview.mp4"),
            duration_seconds=12,
            music_gain_db=-34,
        )

        filter_complex = command[command.index("-filter_complex") + 1]
        self.assertIn("volume=-34dB", filter_complex)
        self.assertIn("atrim=0:12", filter_complex)

    def test_build_ffmpeg_command_loops_video_and_music_for_long_duration(self):
        command = build_ffmpeg_command(
            source_video=Path("/input/birds.mp4"),
            music_selection=_music_selection(),
            output_video=Path("/output/long.mp4"),
            duration_seconds=1800,
        )

        self.assertEqual(command.count("-stream_loop"), 2)
        self.assertIn("1800", command)
        filter_complex = command[command.index("-filter_complex") + 1]
        self.assertIn("atrim=0:1800", filter_complex)

    def test_build_sequence_ffmpeg_command_stitches_media_and_music_items(self):
        command = build_sequence_ffmpeg_command(
            media_items=[
                {"kind": "video", "path": Path("/input/forest-a.mp4")},
                {"kind": "image", "path": Path("/input/forest-still.jpg")},
                {"kind": "video", "path": Path("/input/forest-b.mp4")},
            ],
            music_selections=[_music_selection(), _music_selection()],
            output_video=Path("/output/stitched.mp4"),
            duration_seconds=1800,
        )

        self.assertEqual(command[0], "ffmpeg")
        self.assertIn("/input/forest-a.mp4", command)
        self.assertIn("/input/forest-still.jpg", command)
        self.assertIn("/input/forest-b.mp4", command)
        self.assertIn("/output/stitched.mp4", command)
        self.assertGreaterEqual(command.count("-stream_loop"), 4)
        self.assertIn("-filter_complex", command)
        filter_complex = command[command.index("-filter_complex") + 1]
        self.assertIn("concat=n=3:v=1:a=1[basev][bird]", filter_complex)
        self.assertIn("concat=n=2:v=0:a=1[musiccat]", filter_complex)
        self.assertIn("amix=inputs=2", filter_complex)
        self.assertIn("-t", command)
        self.assertIn("1800", command)

    def test_build_thumbnail_command(self):
        command = build_thumbnail_command(
            source_video=Path("/output/final_video.mp4"),
            thumbnail_path=Path("/output/thumbnail.jpg"),
            timestamp_seconds=5,
        )

        self.assertEqual(command[0], "ffmpeg")
        self.assertIn("-ss", command)
        self.assertIn("5", command)
        self.assertIn("/output/thumbnail.jpg", command)

    @patch("tools.youtube_healing.editor.subprocess.run")
    def test_render_video_creates_output_dirs_and_uses_safe_short_thumbnail_timestamp(
        self, run
    ):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output_video = root / "video" / "final_video.mp4"
            thumbnail_path = root / "thumbs" / "thumbnail.jpg"

            report = render_video(
                source_video=Path("/input/birds.mp4"),
                music_selection=_music_selection(),
                output_video=output_video,
                thumbnail_path=thumbnail_path,
                duration_seconds=3,
            )

            self.assertTrue(output_video.parent.exists())
            self.assertTrue(thumbnail_path.parent.exists())
            self.assertEqual(run.call_count, 2)
            ffmpeg_call = run.call_args_list[0]
            thumbnail_call = run.call_args_list[1]
            self.assertEqual(ffmpeg_call.args[0], report.ffmpeg_command)
            self.assertTrue(ffmpeg_call.kwargs["check"])
            self.assertTrue(thumbnail_call.kwargs["check"])
            self.assertIn(str(output_video), thumbnail_call.args[0])
            self.assertIn(str(thumbnail_path), thumbnail_call.args[0])
            ss_index = thumbnail_call.args[0].index("-ss")
            self.assertEqual(thumbnail_call.args[0][ss_index + 1], "1")


if __name__ == "__main__":
    unittest.main()
