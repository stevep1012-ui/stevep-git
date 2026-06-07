import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.youtube_healing.moneyprinter_turbo import (
    build_turbo_run_command,
    build_turbo_server_command,
    create_turbo_video_task,
    default_turbo_output_dir,
    default_turbo_root,
    ensure_turbo_api_server,
    import_turbo_video,
    list_turbo_videos,
    moneyprinter_engine_status,
    moneyprinter_status,
    run_moneyprinter_engine,
    wait_for_turbo_task,
)


class MoneyPrinterTurboTests(unittest.TestCase):
    def test_moneyprinter_status_reports_missing_output_dir(self):
        status = moneyprinter_status(output_dir=Path("/missing/moneyprinter/output"))

        self.assertFalse(status["configured"])
        self.assertEqual(status["videos"], [])

    def test_default_turbo_root_points_to_external_project_folder(self):
        with patch.dict(os.environ, {}, clear=True):
            root = default_turbo_root(Path("/project"))

        self.assertEqual(root, Path("/project/external/MoneyPrinterTurbo"))

    def test_default_turbo_output_dir_points_to_task_outputs(self):
        with patch.dict(os.environ, {}, clear=True):
            output_dir = default_turbo_output_dir(Path("/project"))

        self.assertEqual(output_dir, Path("/project/external/MoneyPrinterTurbo/storage/tasks"))

    def test_moneyprinter_engine_status_reports_command_and_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "MoneyPrinterTurbo"
            output_dir = root / "storage" / "videos"
            root.mkdir()

            status = moneyprinter_engine_status(
                root=root,
                output_dir=output_dir,
                command_template="python main.py --topic {topic}",
            )

            self.assertTrue(status["installed"])
            self.assertTrue(status["command_configured"])
            self.assertEqual(status["root"], str(root))
            self.assertEqual(status["output_dir"], str(output_dir))

    def test_build_turbo_run_command_formats_topic_without_shell(self):
        command = build_turbo_run_command("python main.py --topic {topic}", "forest birds")

        self.assertEqual(command, ["python", "main.py", "--topic", "forest", "birds"])

    def test_build_turbo_server_command_uses_project_venv_and_removes_topic_argument(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            venv_python = root / ".venv" / "bin" / "python"
            venv_python.parent.mkdir(parents=True)
            venv_python.write_bytes(b"")

            command = build_turbo_server_command(
                root=root,
                command_template="python main.py --topic {topic}",
                topic="forest birds",
            )

        self.assertEqual(command, [str(venv_python), "main.py"])

    def test_run_moneyprinter_engine_creates_output_dir_and_invokes_runner(self):
        calls = []

        def fake_runner(command, **kwargs):
            calls.append({"command": command, "kwargs": kwargs})

            class Result:
                returncode = 0
                stdout = "ok"
                stderr = ""

            return Result()

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "MoneyPrinterTurbo"
            output_dir = root / "storage" / "videos"
            root.mkdir()

            report = run_moneyprinter_engine(
                root=root,
                output_dir=output_dir,
                topic="forest birds",
                command_template="python main.py --topic {topic}",
                runner=fake_runner,
            )

            self.assertTrue(output_dir.exists())
            self.assertEqual(calls[0]["command"], ["python", "main.py", "--topic", "forest", "birds"])
            self.assertEqual(calls[0]["kwargs"]["cwd"], root)
            self.assertEqual(calls[0]["kwargs"]["env"]["MONEYPRINTER_TURBO_OUTPUT_DIR"], str(output_dir))
            self.assertEqual(calls[0]["kwargs"]["env"]["MONEYPRINTER_TURBO_TOPIC"], "forest birds")
            self.assertEqual(report["status"], "completed")

    def test_run_moneyprinter_engine_requires_command_template(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "MoneyPrinterTurbo"
            root.mkdir()

            with self.assertRaises(ValueError):
                run_moneyprinter_engine(
                    root=root,
                    output_dir=root / "storage" / "videos",
                    topic="forest birds",
                    command_template="",
                )

    def test_ensure_turbo_api_server_allows_slow_startup(self):
        checks = {"count": 0}

        def fake_running(api_url):
            checks["count"] += 1
            return checks["count"] >= 51

        with (
            patch(
                "tools.youtube_healing.moneyprinter_turbo.turbo_api_running",
                side_effect=fake_running,
            ),
            patch("tools.youtube_healing.moneyprinter_turbo.time.sleep"),
        ):
            started = ensure_turbo_api_server(
                root=Path("/turbo"),
                command=["python", "main.py"],
                api_url="http://127.0.0.1:8080",
                popen=lambda *args, **kwargs: None,
            )

        self.assertTrue(started)

    def test_wait_for_turbo_task_returns_completed_task(self):
        responses = iter(
            [
                {"status": 200, "data": {"state": 4, "progress": 50}},
                {
                    "status": 200,
                    "data": {
                        "state": 1,
                        "progress": 100,
                        "videos": ["/tasks/task-1/final-1.mp4"],
                    },
                },
            ]
        )
        sleeps = []

        class Response:
            status = 200

            def __init__(self, payload):
                self.payload = payload

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, traceback):
                return False

            def read(self):
                return json.dumps(self.payload).encode("utf-8")

        def fake_urlopen(request, timeout):
            return Response(next(responses))

        task = wait_for_turbo_task(
            api_url="http://127.0.0.1:8080",
            task_id="task-1",
            max_attempts=2,
            poll_seconds=0.1,
            urlopen=fake_urlopen,
            sleep=sleeps.append,
        )

        self.assertEqual(task["state"], 1)
        self.assertEqual(task["videos"], ["/tasks/task-1/final-1.mp4"])
        self.assertEqual(sleeps, [0.1])

    def test_create_turbo_video_task_avoids_llm_and_voice_api_dependencies(self):
        captured = {}

        class Response:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, traceback):
                return False

            def read(self):
                return json.dumps(
                    {"status": 200, "data": {"task_id": "task-1"}}
                ).encode("utf-8")

        def fake_urlopen(request, timeout):
            captured["url"] = request.full_url
            captured["payload"] = json.loads(request.data.decode("utf-8"))
            return Response()

        create_turbo_video_task(
            api_url="http://127.0.0.1:8080",
            topic="숲속 새소리",
            urlopen=fake_urlopen,
        )

        self.assertTrue(captured["payload"]["video_script"])
        self.assertTrue(captured["payload"]["video_terms"])
        self.assertEqual(captured["payload"]["voice_name"], "no-voice")
        self.assertEqual(
            captured["url"],
            "http://127.0.0.1:8080/api/v1/videos",
        )

    def test_list_turbo_videos_finds_supported_outputs_newest_first(self):
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            older = output_dir / "older.mp4"
            newer = output_dir / "newer.mov"
            ignored = output_dir / "notes.txt"
            older.write_bytes(b"old")
            newer.write_bytes(b"new")
            ignored.write_text("ignore", encoding="utf-8")

            videos = list_turbo_videos(output_dir)

            self.assertEqual([item["name"] for item in videos], ["newer.mov", "older.mp4"])
            self.assertEqual(videos[0]["size_bytes"], 3)

    def test_list_turbo_videos_finds_nested_task_outputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            task_dir = output_dir / "task-1"
            task_dir.mkdir()
            (task_dir / "final-1.mp4").write_bytes(b"video")

            videos = list_turbo_videos(output_dir)

            self.assertEqual(videos[0]["name"], "task-1/final-1.mp4")

    def test_import_turbo_video_copies_output_into_local_video_inputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output_dir = root / "turbo"
            input_root = root / "inputs"
            output_dir.mkdir()
            (output_dir / "turbo result.mp4").write_bytes(b"video")

            asset = import_turbo_video(output_dir, input_root, "turbo result.mp4")

            self.assertEqual(asset["kind"], "video")
            self.assertEqual(asset["name"], "turbo-result.mp4")
            self.assertEqual((input_root / "videos" / "turbo-result.mp4").read_bytes(), b"video")

    def test_import_turbo_video_rejects_path_traversal(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output_dir = root / "turbo"
            output_dir.mkdir()

            with self.assertRaises(ValueError):
                import_turbo_video(output_dir, root / "inputs", "../secret.mp4")

    def test_import_turbo_video_accepts_nested_task_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output_dir = root / "turbo"
            task_dir = output_dir / "task-1"
            input_root = root / "inputs"
            task_dir.mkdir(parents=True)
            (task_dir / "final-1.mp4").write_bytes(b"video")

            asset = import_turbo_video(output_dir, input_root, "task-1/final-1.mp4")

            self.assertEqual(asset["name"], "final-1.mp4")
            self.assertEqual((input_root / "videos" / "final-1.mp4").read_bytes(), b"video")


if __name__ == "__main__":
    unittest.main()
