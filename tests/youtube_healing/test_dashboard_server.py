import json
import tempfile
import unittest
from io import BytesIO
from pathlib import Path

from tools.youtube_healing.dashboard_server import (
    DashboardHandler,
    build_package_path,
    build_package_summary,
    clear_imported_assets,
    create_work_package,
    delete_imported_asset,
    list_imported_assets,
    list_package_summaries,
    parse_multipart_upload_file,
    resolve_request_roots,
    sanitize_upload_filename,
    save_imported_asset,
)


class DashboardServerTests(unittest.TestCase):
    def test_dashboard_disables_browser_cache(self):
        handler = DashboardHandler.__new__(DashboardHandler)
        handler._headers_buffer = []
        handler.request_version = "HTTP/1.1"
        handler.wfile = BytesIO()

        handler.end_headers()

        self.assertIn(b"Cache-Control: no-store", handler.wfile.getvalue())

    def test_build_package_summary_reads_upload_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            package_dir = Path(tmp) / "pkg"
            package_dir.mkdir()
            (package_dir / "final_video.mp4").write_bytes(b"video")
            (package_dir / "edit_report.json").write_text(
                json.dumps({"output_path": str(package_dir / "final_video.mp4")}),
                encoding="utf-8",
            )
            (package_dir / "subtitled_video.mp4").write_bytes(b"captioned")
            (package_dir / "music_volume_approval.json").write_text(
                json.dumps({"approved": True, "music_gain_db": -32}),
                encoding="utf-8",
            )
            (package_dir / "publish_plan.json").write_text(
                json.dumps({"title": "힐링되는 새소리", "youtube": {"privacy_status": "unlisted"}}),
                encoding="utf-8",
            )
            (package_dir / "youtube_upload_report.json").write_text(
                json.dumps({"youtube_video_id": "abc123"}),
                encoding="utf-8",
            )
            (package_dir / "instagram_upload_report.json").write_text(
                json.dumps({"instagram_media_id": "ig123", "permalink": "https://instagram.com/reel/ig123"}),
                encoding="utf-8",
            )

            summary = build_package_summary(package_dir)

            self.assertEqual(summary["name"], "pkg")
            self.assertEqual(summary["title"], "힐링되는 새소리")
            self.assertEqual(summary["youtube_video_id"], "abc123")
            self.assertEqual(summary["youtube_url"], "https://youtu.be/abc123")
            self.assertEqual(summary["privacy_status"], "unlisted")
            self.assertEqual(summary["instagram_media_id"], "ig123")
            self.assertEqual(summary["instagram_url"], "https://instagram.com/reel/ig123")
            self.assertEqual(summary["instagram_status"], "uploaded")
            self.assertTrue(summary["music_volume_approved"])
            self.assertEqual(summary["music_gain_db"], -32)
            self.assertTrue(summary["has_final_video"])
            self.assertTrue(summary["has_subtitled_video"])

    def test_build_package_summary_waits_for_edit_report_before_final_video_ready(self):
        with tempfile.TemporaryDirectory() as tmp:
            package_dir = Path(tmp) / "pkg"
            package_dir.mkdir()
            (package_dir / "final_video.mp4").write_bytes(b"still-writing")

            summary = build_package_summary(package_dir)

            self.assertFalse(summary["has_final_video"])

    def test_build_package_summary_uses_metadata_title_before_publish_plan_exists(self):
        with tempfile.TemporaryDirectory() as tmp:
            package_dir = Path(tmp) / "pkg"
            package_dir.mkdir()
            (package_dir / "youtube_metadata.md").write_text(
                "# Title\n숲속 새소리 힐링 | 생성형 힐링 영상\n\n# Description\n설명\n",
                encoding="utf-8",
            )

            summary = build_package_summary(package_dir)

            self.assertEqual(summary["title"], "숲속 새소리 힐링 | 생성형 힐링 영상")

    def test_delete_and_clear_imported_assets(self):
        with tempfile.TemporaryDirectory() as tmp:
            input_root = Path(tmp)
            video = save_imported_asset(input_root, "video", "forest.mp4", b"video")
            save_imported_asset(input_root, "image", "cover.jpg", b"image")
            save_imported_asset(input_root, "music", "piano.mp3", b"music")

            delete_imported_asset(input_root, "video", video["name"])
            removed = clear_imported_assets(input_root)

            self.assertEqual(list_imported_assets(input_root, "video"), [])
            self.assertEqual(list_imported_assets(input_root, "image"), [])
            self.assertEqual(list_imported_assets(input_root, "music"), [])
            self.assertEqual(removed, {"video": 0, "image": 1, "music": 1})

    def test_list_package_summaries_orders_newest_first(self):
        with tempfile.TemporaryDirectory() as tmp:
            output_root = Path(tmp)
            older = output_root / "2026-05-28-old"
            newer = output_root / "2026-05-29-new"
            older.mkdir()
            newer.mkdir()
            (older / "final_video.mp4").write_bytes(b"old")
            (newer / "final_video.mp4").write_bytes(b"new")

            summaries = list_package_summaries(output_root)

            self.assertEqual([item["name"] for item in summaries], ["2026-05-29-new", "2026-05-28-old"])

    def test_sanitize_upload_filename_removes_paths_and_unsafe_chars(self):
        self.assertEqual(sanitize_upload_filename(r"C:\Users\me\bird song!.mp4"), "bird-song.mp4")
        self.assertEqual(sanitize_upload_filename("../../music file.mp3"), "music-file.mp3")

    def test_save_imported_asset_writes_video_under_inputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            input_root = Path(tmp)

            asset = save_imported_asset(
                input_root=input_root,
                kind="video",
                filename="forest birds.mp4",
                data=b"video",
            )

            saved_path = Path(asset["path"])
            self.assertEqual(saved_path.parent, input_root / "videos")
            self.assertEqual(saved_path.name, "forest-birds.mp4")
            self.assertEqual(saved_path.read_bytes(), b"video")

    def test_save_imported_asset_accepts_images(self):
        with tempfile.TemporaryDirectory() as tmp:
            asset = save_imported_asset(Path(tmp), "image", "forest photo.jpg", b"image")

            saved_path = Path(asset["path"])
            self.assertEqual(saved_path.parent, Path(tmp) / "images")
            self.assertEqual(saved_path.name, "forest-photo.jpg")

    def test_save_imported_asset_reports_existing_file_without_copy(self):
        with tempfile.TemporaryDirectory() as tmp:
            input_root = Path(tmp)
            first = save_imported_asset(input_root, "video", "forest.mp4", b"first")
            duplicate = save_imported_asset(input_root, "video", "forest.mp4", b"second")

            self.assertTrue(duplicate["already_exists"])
            self.assertEqual(Path(first["path"]).read_bytes(), b"first")
            self.assertEqual(len(list_imported_assets(input_root, "video")), 1)

    def test_list_imported_assets_returns_music_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            input_root = Path(tmp)
            music_dir = input_root / "music"
            music_dir.mkdir(parents=True)
            (music_dir / "calm.mp3").write_bytes(b"music")

            assets = list_imported_assets(input_root, "music")

            self.assertEqual(assets[0]["name"], "calm.mp3")
            self.assertEqual(assets[0]["kind"], "music")

    def test_create_work_package_uses_imported_video_and_music(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_root = root / "inputs"
            output_root = root / "outputs"
            video = save_imported_asset(input_root, "video", "forest.mp4", b"video")
            music = save_imported_asset(input_root, "music", "calm.mp3", b"music")

            def fake_profile(path):
                from tools.youtube_healing.models import MediaProfile

                return MediaProfile(
                    source_path=str(path),
                    duration_seconds=15,
                    width=1080,
                    height=1920,
                    video_codec="h264",
                    audio_codec="aac",
                    frame_rate=30,
                    has_audio=True,
                    orientation="vertical",
                    youtube_format="shorts",
                )

            def fake_render(**kwargs):
                from tools.youtube_healing.models import EditReport

                kwargs["output_video"].write_bytes(b"final")
                kwargs["thumbnail_path"].write_bytes(b"thumb")
                return EditReport(
                    output_path=str(kwargs["output_video"]),
                    thumbnail_path=str(kwargs["thumbnail_path"]),
                    ffmpeg_command=["ffmpeg"],
                )

            package = create_work_package(
                input_root=input_root,
                output_root=output_root,
                media_kind="video",
                media_name=video["name"],
                music_name=music["name"],
                title="힐링되는 새소리",
                duration_seconds=1800,
                profile_func=fake_profile,
                render_func=fake_render,
            )

            self.assertTrue((package / "final_video.mp4").exists())
            self.assertTrue((package / "music_selection.json").exists())
            self.assertTrue((package / "youtube_metadata.md").exists())
            profile = json.loads((package / "media_profile.json").read_text(encoding="utf-8"))
            self.assertEqual(profile["duration_seconds"], 1800)

    def test_create_work_package_records_media_and_music_sequences(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_root = root / "inputs"
            output_root = root / "outputs"
            first_video = save_imported_asset(input_root, "video", "forest-a.mp4", b"video")
            second_video = save_imported_asset(input_root, "video", "forest-b.mp4", b"video")
            first_music = save_imported_asset(input_root, "music", "calm-a.mp3", b"music")
            second_music = save_imported_asset(input_root, "music", "calm-b.mp3", b"music")

            def fake_profile(path):
                from tools.youtube_healing.models import MediaProfile

                return MediaProfile(
                    source_path=str(path),
                    duration_seconds=15,
                    width=1080,
                    height=1920,
                    video_codec="h264",
                    audio_codec="aac",
                    frame_rate=30,
                    has_audio=True,
                    orientation="vertical",
                    youtube_format="shorts",
                )

            def fake_render_sequence(**kwargs):
                from tools.youtube_healing.models import EditReport

                kwargs["output_video"].write_bytes(b"final")
                kwargs["thumbnail_path"].write_bytes(b"thumb")
                self.assertEqual(len(kwargs["media_items"]), 2)
                self.assertEqual(len(kwargs["music_selections"]), 2)
                return EditReport(
                    output_path=str(kwargs["output_video"]),
                    thumbnail_path=str(kwargs["thumbnail_path"]),
                    ffmpeg_command=["ffmpeg", "sequence"],
                )

            package = create_work_package(
                input_root=input_root,
                output_root=output_root,
                media_kind="",
                media_name="",
                music_name="",
                title="힐링되는 새소리",
                duration_seconds=1800,
                media_items=[
                    {"kind": "video", "name": first_video["name"]},
                    {"kind": "video", "name": second_video["name"]},
                ],
                music_items=[first_music["name"], second_music["name"]],
                profile_func=fake_profile,
                render_sequence_func=fake_render_sequence,
            )

            sequence = json.loads((package / "edit_sequence.json").read_text(encoding="utf-8"))
            self.assertEqual([item["name"] for item in sequence["media_items"]], ["forest-a.mp4", "forest-b.mp4"])
            self.assertEqual(sequence["music_items"], ["calm-a.mp3", "calm-b.mp3"])
            self.assertTrue((package / "final_video.mp4").exists())

    def test_parse_multipart_upload_file_reads_file_part(self):
        boundary = "----bird-boundary"
        body = (
            f"--{boundary}\r\n"
            'Content-Disposition: form-data; name="file"; filename="forest birds.mp4"\r\n'
            "Content-Type: video/mp4\r\n\r\n"
        ).encode("utf-8") + b"video-bytes" + f"\r\n--{boundary}--\r\n".encode("utf-8")

        filename, data = parse_multipart_upload_file(f"multipart/form-data; boundary={boundary}", body)

        self.assertEqual(filename, "forest birds.mp4")
        self.assertEqual(data, b"video-bytes")

    def test_build_package_path_rejects_traversal(self):
        with tempfile.TemporaryDirectory() as tmp:
            output_root = Path(tmp)
            (output_root / "safe").mkdir()

            self.assertEqual(build_package_path(output_root, "safe"), output_root / "safe")
            with self.assertRaises(ValueError):
                build_package_path(output_root, "../outside")

    def test_resolve_request_roots_uses_shared_roots_without_multi_user_mode(self):
        roots = resolve_request_roots(
            query="user_id=mobile",
            shared_input_root=Path("/shared/inputs"),
            shared_output_root=Path("/shared/outputs"),
            shared_config_root=Path("/shared/config"),
            multi_user_root=None,
        )

        self.assertEqual(roots["user_id"], "")
        self.assertEqual(roots["input_root"], Path("/shared/inputs"))
        self.assertEqual(roots["output_root"], Path("/shared/outputs"))
        self.assertEqual(roots["config_root"], Path("/shared/config"))

    def test_resolve_request_roots_uses_user_roots_in_multi_user_mode(self):
        roots = resolve_request_roots(
            query="user_id=mobile",
            headers={},
            shared_input_root=Path("/shared/inputs"),
            shared_output_root=Path("/shared/outputs"),
            shared_config_root=Path("/shared/config"),
            multi_user_root=Path("/users"),
            public_cloud=False,
            auth_user_header="X-Authenticated-User",
        )

        self.assertEqual(roots["user_id"], "mobile")
        self.assertEqual(roots["input_root"], Path("/users/mobile/inputs"))
        self.assertEqual(roots["output_root"], Path("/users/mobile/outputs/youtube-healing"))
        self.assertEqual(roots["config_root"], Path("/users/mobile/config"))

    def test_resolve_request_roots_uses_auth_header_in_public_cloud_mode(self):
        roots = resolve_request_roots(
            query="user_id=spoofed",
            headers={"X-Authenticated-User": "person@example.com"},
            shared_input_root=Path("/shared/inputs"),
            shared_output_root=Path("/shared/outputs"),
            shared_config_root=Path("/shared/config"),
            multi_user_root=Path("/users"),
            public_cloud=True,
            auth_user_header="X-Authenticated-User",
        )

        self.assertEqual(roots["user_id"], "person-example.com")
        self.assertEqual(roots["input_root"], Path("/users/person-example.com/inputs"))
        self.assertEqual(roots["config_root"], Path("/users/person-example.com/config"))


if __name__ == "__main__":
    unittest.main()
