import unittest

from tools.youtube_healing.models import (
    LicenseEvidence,
    MediaProfile,
    MusicSelection,
    MusicTrack,
    SourceAsset,
)
from tools.youtube_healing.metadata_agent import build_youtube_metadata
from tools.youtube_healing.policy_guard import evaluate_policy


def make_asset(**overrides):
    values = {
        "source_path": "/input/birds.mp4",
        "owned_by_user": True,
        "shooting_date": "2026-05-28",
        "general_location": "forest",
        "privacy_notes": "no people visible",
    }
    values.update(overrides)
    return SourceAsset(**values)


def make_profile(**overrides):
    values = {
        "source_path": "/input/birds.mp4",
        "duration_seconds": 37.1,
        "width": 1080,
        "height": 1920,
        "video_codec": "hevc",
        "audio_codec": "aac",
        "frame_rate": 29.97,
        "has_audio": True,
        "orientation": "vertical",
        "youtube_format": "shorts",
    }
    values.update(overrides)
    return MediaProfile(**values)


def make_selection(**evidence_overrides):
    evidence_values = {
        "source_name": "YouTube Audio Library",
        "source_url": "https://studio.youtube.com/channel/audio-library",
        "license_terms": "Use allowed in YouTube videos",
        "attribution_required": False,
        "access_date": "2026-05-28",
    }
    evidence_values.update(evidence_overrides)
    return MusicSelection(
        track=MusicTrack(
            track_id="yt-calm-001",
            title="Calm Forest Pad",
            artist="Example Artist",
            duration_seconds=120,
            local_path="/music/calm.mp3",
            mood_tags=["calm"],
            has_vocals=False,
            strong_beat=False,
            evidence=LicenseEvidence(**evidence_values),
        ),
        target_gain_db=-28.0,
        reason="Matched calm",
    )


class PolicyGuardTests(unittest.TestCase):
    def test_blocks_when_source_not_owned(self):
        asset = make_asset(owned_by_user=False)
        profile = make_profile()
        findings = evaluate_policy(asset, profile, music_selection=None)

        self.assertTrue(
            any(finding.code == "source_ownership_missing" for finding in findings)
        )
        self.assertTrue(any(finding.blocking for finding in findings))

    def test_allows_owned_source_with_youtube_audio_library_music(self):
        asset = make_asset()
        profile = make_profile()
        selection = make_selection()

        findings = evaluate_policy(asset, profile, selection)

        self.assertFalse(any(finding.blocking for finding in findings))

    def test_allows_musopen_public_domain_music(self):
        selection = make_selection(
            source_name="Musopen",
            source_url="https://musopen.org/music/5232-salut-damour-op-12/",
            license_terms="Public domain recording from Musopen for use, copying, performance, distribution, and commercial projects.",
            access_date="2026-05-29",
        )

        findings = evaluate_policy(make_asset(), make_profile(), selection)

        self.assertFalse(any(finding.blocking for finding in findings))

    def test_blocks_fake_musopen_music_url(self):
        selection = make_selection(
            source_name="Musopen",
            source_url="https://musopen.org/not-music/5232-salut-damour-op-12/",
            license_terms="Public domain recording from Musopen for use, copying, performance, distribution, and commercial projects.",
            access_date="2026-05-29",
        )

        findings = evaluate_policy(make_asset(), make_profile(), selection)

        self.assertTrue(
            any(finding.code == "music_license_evidence_incomplete" for finding in findings)
        )
        self.assertTrue(any(finding.blocking for finding in findings))

    def test_blocks_when_source_has_no_audio(self):
        findings = evaluate_policy(make_asset(), make_profile(has_audio=False), make_selection())

        self.assertTrue(any(finding.code == "source_audio_missing" for finding in findings))
        self.assertTrue(any(finding.blocking for finding in findings))

    def test_blocks_korean_privacy_term(self):
        findings = evaluate_policy(
            make_asset(privacy_notes="영상에 차량번호가 보임"),
            make_profile(),
            make_selection(),
        )

        self.assertTrue(any(finding.code == "privacy_review_required" for finding in findings))
        self.assertTrue(any(finding.blocking for finding in findings))

    def test_blocks_english_plural_people_visible(self):
        findings = evaluate_policy(
            make_asset(privacy_notes="people visible near the trail"),
            make_profile(),
            make_selection(),
        )

        self.assertTrue(any(finding.code == "privacy_review_required" for finding in findings))
        self.assertTrue(any(finding.blocking for finding in findings))

    def test_allows_clear_negative_privacy_notes(self):
        for privacy_notes in (
            "no face visible",
            "no license plate visible",
            "AI-generated content, no personal data",
        ):
            with self.subTest(privacy_notes=privacy_notes):
                findings = evaluate_policy(
                    make_asset(privacy_notes=privacy_notes),
                    make_profile(),
                    make_selection(),
                )

                self.assertFalse(
                    any(finding.code == "privacy_review_required" for finding in findings)
                )
                self.assertFalse(any(finding.blocking for finding in findings))

    def test_blocks_disallowed_music_source(self):
        findings = evaluate_policy(
            make_asset(),
            make_profile(),
            make_selection(source_name="Other Music Library"),
        )

        self.assertTrue(any(finding.code == "music_source_not_allowed" for finding in findings))
        self.assertTrue(any(finding.blocking for finding in findings))

    def test_blocks_placeholder_license_evidence(self):
        findings = evaluate_policy(
            make_asset(),
            make_profile(),
            make_selection(license_terms="No copyright music"),
        )

        self.assertTrue(
            any(finding.code == "music_license_evidence_incomplete" for finding in findings)
        )
        self.assertTrue(any(finding.blocking for finding in findings))

    def test_blocks_spoofed_youtube_audio_library_url(self):
        findings = evaluate_policy(
            make_asset(),
            make_profile(),
            make_selection(source_url="https://example.com/youtube-audio-library"),
        )

        self.assertTrue(
            any(finding.code == "music_license_evidence_incomplete" for finding in findings)
        )
        self.assertTrue(any(finding.blocking for finding in findings))

    def test_blocks_general_youtube_url(self):
        findings = evaluate_policy(
            make_asset(),
            make_profile(),
            make_selection(source_url="https://www.youtube.com/watch?v=abc123"),
        )

        self.assertTrue(
            any(finding.code == "music_license_evidence_incomplete" for finding in findings)
        )
        self.assertTrue(any(finding.blocking for finding in findings))

    def test_blocks_fake_audio_library_url_segments(self):
        for source_url in (
            "https://www.youtube.com/audiolibraryfake",
            "https://studio.youtube.com/channel/not-audio-library-fake",
        ):
            with self.subTest(source_url=source_url):
                findings = evaluate_policy(
                    make_asset(),
                    make_profile(),
                    make_selection(source_url=source_url),
                )

                self.assertTrue(
                    any(
                        finding.code == "music_license_evidence_incomplete"
                        for finding in findings
                    )
                )
                self.assertTrue(any(finding.blocking for finding in findings))

    def test_blocks_weak_license_term(self):
        for license_terms in ("free", "TBD"):
            with self.subTest(license_terms=license_terms):
                findings = evaluate_policy(
                    make_asset(),
                    make_profile(),
                    make_selection(license_terms=license_terms),
                )

                self.assertTrue(
                    any(
                        finding.code == "music_license_evidence_incomplete"
                        for finding in findings
                    )
                )
                self.assertTrue(any(finding.blocking for finding in findings))

    def test_blocks_additional_korean_privacy_terms(self):
        for privacy_notes in ("전화번호가 들림", "개인정보가 화면에 보임"):
            with self.subTest(privacy_notes=privacy_notes):
                findings = evaluate_policy(
                    make_asset(privacy_notes=privacy_notes),
                    make_profile(),
                    make_selection(),
                )

                self.assertTrue(
                    any(finding.code == "privacy_review_required" for finding in findings)
                )
                self.assertTrue(any(finding.blocking for finding in findings))

    def test_metadata_does_not_expose_full_source_path(self):
        asset = make_asset(source_path="/Users/example/private/birds.mp4")
        metadata = build_youtube_metadata(asset, make_profile(), make_selection())

        self.assertNotIn("/Users/example/private/birds.mp4", metadata)
        self.assertIn("birds.mp4", metadata)

    def test_metadata_does_not_expose_windows_source_path(self):
        asset = make_asset(source_path=r"C:\Users\example\private\birds.mp4")
        metadata = build_youtube_metadata(asset, make_profile(), make_selection())

        self.assertNotIn(r"C:\Users", metadata)
        self.assertIn("birds.mp4", metadata)


if __name__ == "__main__":
    unittest.main()
