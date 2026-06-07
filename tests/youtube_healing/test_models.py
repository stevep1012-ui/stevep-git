import json
import tempfile
import unittest
from pathlib import Path

from tools.youtube_healing.models import (
    LicenseEvidence,
    MusicTrack,
    SourceAsset,
    VideoPackageStatus,
    write_json,
)


class ModelTests(unittest.TestCase):
    def test_write_json_serializes_dataclass(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "asset.json"
            asset = SourceAsset(
                source_path="/videos/birds.mp4",
                owned_by_user=True,
                shooting_date="2026-05-28",
                general_location="forest",
                privacy_notes="no people visible",
            )

            write_json(output, asset)

            data = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(data["source_path"], "/videos/birds.mp4")
            self.assertTrue(data["owned_by_user"])
            self.assertEqual(data["privacy_notes"], "no people visible")

    def test_music_track_requires_license_evidence_shape(self):
        evidence = LicenseEvidence(
            source_name="YouTube Audio Library",
            source_url="https://studio.youtube.com/channel/audio-library",
            license_terms="YouTube Audio Library track for use in YouTube videos",
            attribution_required=False,
            access_date="2026-05-28",
        )
        track = MusicTrack(
            track_id="yt-calm-001",
            title="Calm Forest Pad",
            artist="Example Artist",
            duration_seconds=120,
            local_path="/music/calm.mp3",
            mood_tags=["calm", "ambient"],
            has_vocals=False,
            strong_beat=False,
            evidence=evidence,
        )

        self.assertEqual(track.evidence.source_name, "YouTube Audio Library")
        self.assertFalse(track.has_vocals)
        self.assertEqual(track.mood_tags, ["calm", "ambient"])

    def test_status_values_are_stable(self):
        self.assertEqual(VideoPackageStatus.DRAFT.value, "draft")
        self.assertEqual(VideoPackageStatus.READY_FOR_REVIEW.value, "ready_for_review")
        self.assertEqual(VideoPackageStatus.APPROVED.value, "approved")
        self.assertEqual(VideoPackageStatus.UPLOADED.value, "uploaded")
        self.assertEqual(VideoPackageStatus.REJECTED.value, "rejected")


if __name__ == "__main__":
    unittest.main()
