import unittest

from tools.youtube_healing.media_profiler import (
    classify_orientation,
    classify_youtube_format,
    parse_ffprobe_json,
    parse_frame_rate,
)


class MediaProfilerTests(unittest.TestCase):
    def test_parse_frame_rate_returns_float_for_fraction(self):
        self.assertAlmostEqual(
            parse_frame_rate("50040000/1671571"),
            29.93591058949934,
            places=6,
        )

    def test_parse_frame_rate_returns_zero_for_invalid_values(self):
        self.assertEqual(parse_frame_rate("0/0"), 0.0)
        self.assertEqual(parse_frame_rate("not-a-rate"), 0.0)
        self.assertEqual(parse_frame_rate(None), 0.0)

    def test_classify_orientation(self):
        self.assertEqual(classify_orientation(1080, 1920), "vertical")
        self.assertEqual(classify_orientation(1920, 1080), "horizontal")
        self.assertEqual(classify_orientation(1080, 1080), "square")

    def test_classify_youtube_format(self):
        self.assertEqual(classify_youtube_format("vertical", 37.150114), "shorts")
        self.assertEqual(classify_youtube_format("vertical", 61.0), "standard")
        self.assertEqual(classify_youtube_format("horizontal", 37.150114), "standard")

    def test_parse_ffprobe_json_returns_media_profile_for_seed_payload(self):
        payload = {
            "streams": [
                {
                    "codec_type": "video",
                    "codec_name": "hevc",
                    "width": 1080,
                    "height": 1920,
                    "avg_frame_rate": "50040000/1671571",
                },
                {
                    "codec_type": "audio",
                    "codec_name": "aac",
                },
            ],
            "format": {
                "duration": "37.150114",
            },
        }

        profile = parse_ffprobe_json(payload, "/videos/birds.mp4")

        self.assertEqual(profile.source_path, "/videos/birds.mp4")
        self.assertEqual(profile.duration_seconds, 37.150114)
        self.assertEqual(profile.width, 1080)
        self.assertEqual(profile.height, 1920)
        self.assertEqual(profile.video_codec, "hevc")
        self.assertEqual(profile.audio_codec, "aac")
        self.assertAlmostEqual(profile.frame_rate, 29.93591058949934, places=6)
        self.assertTrue(profile.has_audio)
        self.assertEqual(profile.orientation, "vertical")
        self.assertEqual(profile.youtube_format, "shorts")

    def test_parse_ffprobe_json_raises_for_audio_only_payload(self):
        payload = {
            "streams": [
                {
                    "codec_type": "audio",
                    "codec_name": "aac",
                },
            ],
            "format": {
                "duration": "37.150114",
            },
        }

        with self.assertRaisesRegex(ValueError, "No video stream"):
            parse_ffprobe_json(payload, "/videos/audio-only.m4a")


if __name__ == "__main__":
    unittest.main()
