import json
import tempfile
import unittest
from pathlib import Path

from tools.youtube_healing.music_agent import load_music_catalog, select_music


class MusicAgentTests(unittest.TestCase):
    def test_selects_safe_youtube_audio_library_track(self):
        with tempfile.TemporaryDirectory() as tmp:
            catalog_path = Path(tmp) / "music_catalog.json"
            catalog_path.write_text(
                json.dumps(
                    [
                        {
                            "track_id": "unsafe-vocal",
                            "title": "Loud Vocal Track",
                            "artist": "Example",
                            "duration_seconds": 90,
                            "local_path": "/music/loud.mp3",
                            "mood_tags": ["calm"],
                            "has_vocals": True,
                            "strong_beat": False,
                            "evidence": {
                                "source_name": "YouTube Audio Library",
                                "source_url": "https://studio.youtube.com/channel/audio-library",
                                "license_terms": "Use allowed in YouTube videos",
                                "attribution_required": False,
                                "access_date": "2026-05-28",
                            },
                        },
                        {
                            "track_id": "yt-calm-001",
                            "title": "Calm Forest Pad",
                            "artist": "Example Artist",
                            "duration_seconds": 120,
                            "local_path": "/music/calm.mp3",
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
                        },
                    ]
                ),
                encoding="utf-8",
            )

            tracks = load_music_catalog(catalog_path)
            selection = select_music(tracks, desired_moods=["forest", "calm"])

            self.assertEqual(selection.track.track_id, "yt-calm-001")
            self.assertEqual(selection.target_gain_db, -18.0)
            self.assertIn("forest", selection.reason)

    def test_rejects_non_youtube_source_for_mvp(self):
        with tempfile.TemporaryDirectory() as tmp:
            catalog_path = Path(tmp) / "music_catalog.json"
            catalog_path.write_text(
                json.dumps(
                    [
                        {
                            "track_id": "random-free",
                            "title": "Free Music Claim",
                            "artist": "Unknown",
                            "duration_seconds": 120,
                            "local_path": "/music/free.mp3",
                            "mood_tags": ["calm"],
                            "has_vocals": False,
                            "strong_beat": False,
                            "evidence": {
                                "source_name": "Random YouTube Channel",
                                "source_url": "https://youtube.com/example",
                                "license_terms": "No copyright music",
                                "attribution_required": False,
                                "access_date": "2026-05-28",
                            },
                        }
                    ]
                ),
                encoding="utf-8",
            )

            tracks = load_music_catalog(catalog_path)

            with self.assertRaises(ValueError):
                select_music(tracks, desired_moods=["calm"])

    def test_rejects_placeholder_catalog_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            catalog_path = Path(tmp) / "music_catalog.json"
            catalog_path.write_text(
                json.dumps(
                    [
                        {
                            "track_id": "placeholder",
                            "title": "Replace With Actual YouTube Audio Library Track",
                            "artist": "Replace With Actual Artist",
                            "duration_seconds": 120,
                            "local_path": "assets/music/replace-with-downloaded-track.mp3",
                            "mood_tags": ["calm"],
                            "has_vocals": False,
                            "strong_beat": False,
                            "evidence": {
                                "source_name": "YouTube Audio Library",
                                "source_url": "https://studio.youtube.com/channel/audio-library",
                                "license_terms": "Record the exact license terms shown in YouTube Studio for this track.",
                                "attribution_required": False,
                                "access_date": "2026-05-28",
                            },
                        }
                    ]
                ),
                encoding="utf-8",
            )

            tracks = load_music_catalog(catalog_path)

            with self.assertRaises(ValueError):
                select_music(tracks, desired_moods=["calm"])

    def test_rejects_placeholder_artist(self):
        with tempfile.TemporaryDirectory() as tmp:
            catalog_path = Path(tmp) / "music_catalog.json"
            catalog_path.write_text(
                json.dumps(
                    [
                        {
                            "track_id": "placeholder-artist",
                            "title": "Calm Forest Pad",
                            "artist": "Replace With Actual Artist",
                            "duration_seconds": 120,
                            "local_path": "/music/calm-forest-pad.mp3",
                            "mood_tags": ["calm"],
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

            tracks = load_music_catalog(catalog_path)

            with self.assertRaises(ValueError):
                select_music(tracks, desired_moods=["calm"])

    def test_normalizes_mood_tags_for_matching(self):
        with tempfile.TemporaryDirectory() as tmp:
            catalog_path = Path(tmp) / "music_catalog.json"
            catalog_path.write_text(
                json.dumps(
                    [
                        {
                            "track_id": "yt-neutral-001",
                            "title": "Neutral Pad",
                            "artist": "Example Artist",
                            "duration_seconds": 120,
                            "local_path": "/music/neutral.mp3",
                            "mood_tags": ["sleep"],
                            "has_vocals": False,
                            "strong_beat": False,
                            "evidence": {
                                "source_name": "YouTube Audio Library",
                                "source_url": "https://studio.youtube.com/channel/audio-library",
                                "license_terms": "Use allowed in YouTube videos",
                                "attribution_required": False,
                                "access_date": "2026-05-28",
                            },
                        },
                        {
                            "track_id": "yt-calm-001",
                            "title": "Calm Forest Pad",
                            "artist": "Example Artist",
                            "duration_seconds": 120,
                            "local_path": "/music/calm.mp3",
                            "mood_tags": [" Calm ", "Ambient"],
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

            tracks = load_music_catalog(catalog_path)
            selection = select_music(tracks, desired_moods=["calm"])

            self.assertEqual(selection.track.track_id, "yt-calm-001")
            self.assertIn("calm", selection.reason)

    def test_skips_invalid_higher_mood_match_for_policy_compatible_track(self):
        with tempfile.TemporaryDirectory() as tmp:
            catalog_path = Path(tmp) / "music_catalog.json"
            catalog_path.write_text(
                json.dumps(
                    [
                        {
                            "track_id": "invalid-url",
                            "title": "Perfect Forest Match",
                            "artist": "Example Artist",
                            "duration_seconds": 120,
                            "local_path": "/music/perfect.mp3",
                            "mood_tags": ["calm", "ambient", "forest"],
                            "has_vocals": False,
                            "strong_beat": False,
                            "evidence": {
                                "source_name": "YouTube Audio Library",
                                "source_url": "https://www.youtube.com/watch?v=abc123",
                                "license_terms": "Use allowed in YouTube videos",
                                "attribution_required": False,
                                "access_date": "2026-05-28",
                            },
                        },
                        {
                            "track_id": "valid-audio-library",
                            "title": "Lower Mood Match",
                            "artist": "Example Artist",
                            "duration_seconds": 120,
                            "local_path": "/music/lower.mp3",
                            "mood_tags": ["calm"],
                            "has_vocals": False,
                            "strong_beat": False,
                            "evidence": {
                                "source_name": "YouTube Audio Library",
                                "source_url": "https://studio.youtube.com/channel/audio-library",
                                "license_terms": "Use allowed in YouTube videos",
                                "attribution_required": False,
                                "access_date": "2026-05-28",
                            },
                        },
                    ]
                ),
                encoding="utf-8",
            )

            tracks = load_music_catalog(catalog_path)
            selection = select_music(tracks, desired_moods=["calm", "ambient", "forest"])

            self.assertEqual(selection.track.track_id, "valid-audio-library")

    def test_selects_musopen_public_domain_track(self):
        with tempfile.TemporaryDirectory() as tmp:
            catalog_path = Path(tmp) / "music_catalog.json"
            catalog_path.write_text(
                json.dumps(
                    [
                        {
                            "track_id": "musopen-salut-damour",
                            "title": "Elgar - Salut d'Amour",
                            "artist": "Felipe Sarro",
                            "duration_seconds": 210,
                            "local_path": "/music/salut-damour.mp3",
                            "mood_tags": ["calm", "classical", "piano"],
                            "has_vocals": False,
                            "strong_beat": False,
                            "evidence": {
                                "source_name": "Musopen",
                                "source_url": "https://musopen.org/music/5232-salut-damour-op-12/",
                                "license_terms": "Public domain recording from Musopen for use, copying, performance, distribution, and commercial projects.",
                                "attribution_required": False,
                                "access_date": "2026-05-29",
                            },
                        }
                    ]
                ),
                encoding="utf-8",
            )

            tracks = load_music_catalog(catalog_path)
            selection = select_music(tracks, desired_moods=["calm", "piano"])

            self.assertEqual(selection.track.track_id, "musopen-salut-damour")
            self.assertEqual(selection.track.evidence.source_name, "Musopen")


if __name__ == "__main__":
    unittest.main()
