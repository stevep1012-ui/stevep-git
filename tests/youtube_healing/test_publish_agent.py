import json
import tempfile
import unittest
from pathlib import Path

from tools.youtube_healing.publish_agent import (
    assert_music_volume_approved,
    build_instagram_container_payload,
    build_publish_plan,
    build_youtube_upload_body,
    check_youtube_oauth_inputs,
    load_publish_plan,
    upload_instagram_from_plan,
    write_publish_plan,
)


class PublishAgentTests(unittest.TestCase):
    def test_build_publish_plan_defaults_youtube_to_unlisted(self):
        with tempfile.TemporaryDirectory() as tmp:
            package_dir = Path(tmp)
            video = package_dir / "final_video.mp4"
            metadata = package_dir / "youtube_metadata.md"
            video.write_bytes(b"video")
            metadata.write_text(
                "# Title\nOld title\n\n# Description\nQuiet forest.\n\n# Hashtags\n#Birdsong #Shorts\n",
                encoding="utf-8",
            )

            plan = build_publish_plan(package_dir, title="아침 숲속 새소리")

            self.assertEqual(plan["title"], "아침 숲속 새소리")
            self.assertEqual(plan["video_path"], str(video))
            self.assertEqual(plan["youtube"]["privacy_status"], "unlisted")
            self.assertEqual(plan["youtube"]["status"], "ready")
            self.assertIn("Quiet forest.", plan["description"])
            self.assertIn("#Birdsong #Shorts", plan["description"])

    def test_build_publish_plan_blocks_missing_title(self):
        with tempfile.TemporaryDirectory() as tmp:
            package_dir = Path(tmp)
            (package_dir / "final_video.mp4").write_bytes(b"video")
            (package_dir / "youtube_metadata.md").write_text("# Description\nx\n", encoding="utf-8")

            with self.assertRaises(ValueError):
                build_publish_plan(package_dir, title="   ")

    def test_instagram_requires_hosted_video_url(self):
        with tempfile.TemporaryDirectory() as tmp:
            package_dir = Path(tmp)
            (package_dir / "final_video.mp4").write_bytes(b"video")
            (package_dir / "youtube_metadata.md").write_text("# Description\nx\n", encoding="utf-8")

            plan = build_publish_plan(package_dir, title="Birds")

            self.assertEqual(plan["instagram"]["status"], "waiting_for_public_video_url")
            self.assertIn("INSTAGRAM_VIDEO_URL", plan["instagram"]["required_env"])

    def test_write_publish_plan_writes_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            package_dir = Path(tmp)
            (package_dir / "final_video.mp4").write_bytes(b"video")
            (package_dir / "youtube_metadata.md").write_text("# Description\nx\n", encoding="utf-8")
            plan = build_publish_plan(package_dir, title="Birds")

            path = write_publish_plan(package_dir, plan)

            self.assertEqual(path, package_dir / "publish_plan.json")
            saved = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(saved["youtube"]["privacy_status"], "unlisted")

    def test_build_youtube_upload_body_uses_title_and_unlisted_status(self):
        plan = {
            "title": "아침 숲속 새소리",
            "description": "Quiet forest.",
            "youtube": {"privacy_status": "unlisted"},
        }

        body = build_youtube_upload_body(plan)

        self.assertEqual(body["snippet"]["title"], "아침 숲속 새소리")
        self.assertEqual(body["snippet"]["description"], "Quiet forest.")
        self.assertEqual(body["status"]["privacyStatus"], "unlisted")
        self.assertFalse(body["status"]["selfDeclaredMadeForKids"])

    def test_build_instagram_container_payload_requires_public_video_url(self):
        plan = {
            "title": "Birds",
            "description": "Quiet forest.",
            "instagram": {"video_url": "https://example.com/final_video.mp4"},
        }

        payload = build_instagram_container_payload(plan)

        self.assertEqual(payload["media_type"], "REELS")
        self.assertEqual(payload["video_url"], "https://example.com/final_video.mp4")
        self.assertIn("Birds", payload["caption"])

    def test_load_publish_plan_reads_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "publish_plan.json"
            path.write_text(json.dumps({"title": "Birds"}), encoding="utf-8")

            self.assertEqual(load_publish_plan(path)["title"], "Birds")

    def test_assert_music_volume_approved_blocks_upload_without_user_approval(self):
        with tempfile.TemporaryDirectory() as tmp:
            package_dir = Path(tmp)
            plan_path = package_dir / "publish_plan.json"
            plan_path.write_text(json.dumps({"package_dir": str(package_dir), "title": "Birds"}), encoding="utf-8")

            with self.assertRaises(PermissionError):
                assert_music_volume_approved(plan_path)

    def test_assert_music_volume_approved_allows_upload_after_user_approval(self):
        with tempfile.TemporaryDirectory() as tmp:
            package_dir = Path(tmp)
            plan_path = package_dir / "publish_plan.json"
            plan_path.write_text(json.dumps({"package_dir": str(package_dir), "title": "Birds"}), encoding="utf-8")
            (package_dir / "music_volume_approval.json").write_text(
                json.dumps({"approved": True, "music_gain_db": -30}),
                encoding="utf-8",
            )

            self.assertEqual(assert_music_volume_approved(plan_path)["music_gain_db"], -30)

    def test_upload_instagram_from_plan_creates_polls_and_publishes_reel(self):
        with tempfile.TemporaryDirectory() as tmp:
            plan_path = Path(tmp) / "publish_plan.json"
            plan_path.write_text(
                json.dumps(
                    {
                        "package_dir": tmp,
                        "title": "Birds",
                        "description": "Quiet forest.",
                        "instagram": {"video_url": "https://example.com/final_video.mp4"},
                    }
                ),
                encoding="utf-8",
            )
            (Path(tmp) / "music_volume_approval.json").write_text(
                json.dumps({"approved": True, "music_gain_db": -30}),
                encoding="utf-8",
            )
            post_calls = []
            get_calls = []

            def fake_post(url, payload):
                post_calls.append((url, payload))
                if url.endswith("/media"):
                    return {"id": "container123"}
                return {"id": "media456", "permalink": "https://instagram.com/reel/media456"}

            def fake_get(url):
                get_calls.append(url)
                return {"status_code": "FINISHED"}

            report = upload_instagram_from_plan(
                plan_path,
                access_token="token",
                instagram_user_id="ig-user",
                http_post=fake_post,
                http_get=fake_get,
                sleep=lambda _seconds: None,
            )

            self.assertEqual(report["instagram_container_id"], "container123")
            self.assertEqual(report["instagram_media_id"], "media456")
            self.assertEqual(post_calls[0][1]["media_type"], "REELS")
            self.assertEqual(post_calls[1][1]["creation_id"], "container123")
            self.assertIn("fields=status_code", get_calls[0])

    def test_upload_instagram_from_plan_requires_credentials(self):
        with tempfile.TemporaryDirectory() as tmp:
            plan_path = Path(tmp) / "publish_plan.json"
            plan_path.write_text(
                json.dumps({"title": "Birds", "instagram": {"video_url": "https://example.com/video.mp4"}}),
                encoding="utf-8",
            )

            with self.assertRaises(ValueError):
                upload_instagram_from_plan(plan_path, access_token="", instagram_user_id="ig-user")

    def test_check_youtube_oauth_inputs_requires_client_secret(self):
        with tempfile.TemporaryDirectory() as tmp:
            token = Path(tmp) / "youtube_token.json"

            with self.assertRaises(FileNotFoundError):
                check_youtube_oauth_inputs(Path(tmp) / "missing.json", token)

    def test_check_youtube_oauth_inputs_creates_token_parent(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            secret = root / "client_secret.json"
            token = root / "auth" / "youtube_token.json"
            secret.write_text("{}", encoding="utf-8")

            check_youtube_oauth_inputs(secret, token)

            self.assertTrue(token.parent.exists())


if __name__ == "__main__":
    unittest.main()
