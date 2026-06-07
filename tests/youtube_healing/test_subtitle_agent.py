import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.youtube_healing.subtitle_agent import (
    build_subtitle_filter,
    build_subtitle_ffmpeg_command,
    find_subtitle_ffmpeg,
    render_subtitled_video,
)


class SubtitleAgentTests(unittest.TestCase):
    def test_build_subtitle_filter_supports_intro_outro_method(self):
        subtitle_filter = build_subtitle_filter(
            {
                "method": "intro_outro",
                "text": "숲속 새소리",
                "intro_seconds": 3,
                "outro_seconds": 2,
                "duration_seconds": 30,
                "position": "bottom",
                "font_size": 48,
                "box": True,
            }
        )

        self.assertIn("drawtext", subtitle_filter)
        self.assertIn("숲속 새소리", subtitle_filter)
        self.assertIn("between(t,0.0,3.0)", subtitle_filter)
        self.assertIn("between(t,28.0,30.0)", subtitle_filter)

    def test_build_subtitle_filter_supports_lower_third_method(self):
        subtitle_filter = build_subtitle_filter(
            {
                "method": "lower_third",
                "text": "잠시 쉬어가세요",
                "start_seconds": 4,
                "end_seconds": 10,
                "position": "bottom",
                "font_size": 42,
                "box": True,
            }
        )

        self.assertIn("잠시 쉬어가세요", subtitle_filter)
        self.assertIn("between(t,4.0,10.0)", subtitle_filter)

    def test_build_subtitle_filter_supports_timed_captions_method(self):
        subtitle_filter = build_subtitle_filter(
            {
                "method": "timed_captions",
                "captions": [
                    {"text": "아침 숲", "start_seconds": 0, "end_seconds": 3},
                    {"text": "새소리", "start_seconds": 3, "end_seconds": 6},
                ],
                "position": "top",
                "font_size": 36,
                "box": False,
            }
        )

        self.assertIn("아침 숲", subtitle_filter)
        self.assertIn("새소리", subtitle_filter)
        self.assertIn("between(t,3.0,6.0)", subtitle_filter)

    def test_build_subtitle_ffmpeg_command_reencodes_video_after_music_mix(self):
        command = build_subtitle_ffmpeg_command(
            input_video=Path("/output/final_video.mp4"),
            output_video=Path("/output/subtitled_video.mp4"),
            settings={"method": "lower_third", "text": "Birdsong", "start_seconds": 0, "end_seconds": 4},
        )

        self.assertIn("/output/final_video.mp4", command)
        self.assertIn("/output/subtitled_video.mp4", command)
        self.assertIn("-vf", command)
        self.assertIn("libx264", command)
        self.assertIn("copy", command)

    @patch("tools.youtube_healing.subtitle_agent._supports_drawtext")
    def test_find_subtitle_ffmpeg_skips_binary_without_drawtext(self, supports_drawtext):
        supports_drawtext.side_effect = lambda path: path.name == "ffmpeg-with-drawtext"

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            unsupported = root / "ffmpeg"
            supported = root / "ffmpeg-with-drawtext"
            unsupported.touch()
            supported.touch()

            result = find_subtitle_ffmpeg([unsupported, supported])

            self.assertEqual(result, supported)

    @patch("tools.youtube_healing.subtitle_agent.subprocess.run")
    @patch("tools.youtube_healing.subtitle_agent.find_subtitle_ffmpeg")
    def test_render_subtitled_video_creates_output_dir_and_runs_ffmpeg(self, find_ffmpeg, run):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_video = root / "final_video.mp4"
            output_video = root / "captioned" / "subtitled_video.mp4"
            input_video.write_bytes(b"video")
            find_ffmpeg.return_value = Path("/tools/ffmpeg")

            report = render_subtitled_video(
                input_video=input_video,
                output_video=output_video,
                settings={"method": "lower_third", "text": "Birdsong", "start_seconds": 0, "end_seconds": 4},
            )

            self.assertTrue(output_video.parent.exists())
            run.assert_called_once()
            self.assertEqual(run.call_args.args[0][0], "/tools/ffmpeg")
            self.assertEqual(report["output_path"], str(output_video))


if __name__ == "__main__":
    unittest.main()
