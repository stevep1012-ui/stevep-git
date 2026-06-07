from __future__ import annotations

import os
import re
import shlex
import subprocess
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib import error, request


SUPPORTED_TURBO_VIDEO_EXTENSIONS = {".mp4", ".mov", ".m4v"}


def default_turbo_root(project_root: Path) -> Path:
    env_dir = os.environ.get("MONEYPRINTER_TURBO_DIR", "").strip()
    if env_dir:
        return Path(env_dir).expanduser()
    return project_root / "external" / "MoneyPrinterTurbo"


def default_turbo_output_dir(project_root: Path) -> Path:
    env_dir = os.environ.get("MONEYPRINTER_TURBO_OUTPUT_DIR", "").strip()
    if env_dir:
        return Path(env_dir).expanduser()
    return default_turbo_root(project_root) / "storage" / "tasks"


def default_turbo_command_template() -> str:
    return os.environ.get("MONEYPRINTER_TURBO_COMMAND", "").strip()


def default_turbo_api_url() -> str:
    return os.environ.get("MONEYPRINTER_TURBO_API_URL", "http://127.0.0.1:8080").strip().rstrip("/")


def moneyprinter_engine_status(root: Path, output_dir: Path, command_template: str, api_url: str | None = None) -> dict:
    resolved_api_url = (api_url or default_turbo_api_url()).rstrip("/")
    return {
        "installed": root.exists() and root.is_dir(),
        "command_configured": bool(command_template.strip()),
        "api_url": resolved_api_url,
        "api_running": turbo_api_running(resolved_api_url),
        "root": str(root),
        "output_dir": str(output_dir),
        "command_template": command_template,
    }


def build_turbo_run_command(command_template: str, topic: str) -> list[str]:
    template = command_template.strip()
    if not template:
        raise ValueError("MONEYPRINTER_TURBO_COMMAND is required.")
    return shlex.split(template.format(topic=topic))


def build_turbo_server_command(
    root: Path,
    command_template: str,
    topic: str,
) -> list[str]:
    if not command_template.strip():
        raise ValueError("MONEYPRINTER_TURBO_COMMAND is required.")
    template_parts = shlex.split(command_template.strip())
    command = []
    index = 0
    while index < len(template_parts):
        if (
            template_parts[index] == "--topic"
            and index + 1 < len(template_parts)
            and template_parts[index + 1] == "{topic}"
        ):
            index += 2
            continue
        command.append(template_parts[index].format(topic=topic))
        index += 1

    venv_python = root / ".venv" / "bin" / "python"
    if command and command[0] in {"python", "python3"} and venv_python.is_file():
        command[0] = str(venv_python)
    return command


def run_moneyprinter_engine(
    root: Path,
    output_dir: Path,
    topic: str,
    command_template: str,
    runner=subprocess.run,
) -> dict:
    if not root.exists() or not root.is_dir():
        raise FileNotFoundError(f"MoneyPrinterTurbo directory not found: {root}")
    clean_topic = topic.strip()
    if not clean_topic:
        raise ValueError("Turbo topic is required.")
    output_dir.mkdir(parents=True, exist_ok=True)
    started_at = datetime.now(timezone.utc).isoformat()
    if runner is subprocess.run:
        api_url = default_turbo_api_url()
        command = build_turbo_server_command(root, command_template, clean_topic)
        server_started = ensure_turbo_api_server(root=root, command=command, api_url=api_url)
        task = create_turbo_video_task(api_url=api_url, topic=clean_topic)
        completed_task = wait_for_turbo_task(
            api_url=api_url,
            task_id=task.get("task_id", ""),
        )
        return {
            "status": "completed",
            "started_at": started_at,
            "finished_at": datetime.now(timezone.utc).isoformat(),
            "root": str(root),
            "output_dir": str(output_dir),
            "topic": clean_topic,
            "command": command,
            "api_url": api_url,
            "api_server_started": server_started,
            "task_id": task.get("task_id", ""),
            "task": completed_task,
            "videos": list_turbo_videos(output_dir),
        }
    command = build_turbo_run_command(command_template, clean_topic)
    env = os.environ.copy()
    env["MONEYPRINTER_TURBO_OUTPUT_DIR"] = str(output_dir)
    env["MONEYPRINTER_TURBO_TOPIC"] = clean_topic
    result = runner(
        command,
        cwd=root,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    status = "completed" if result.returncode == 0 else "failed"
    return {
        "status": status,
        "started_at": started_at,
        "finished_at": datetime.now(timezone.utc).isoformat(),
        "root": str(root),
        "output_dir": str(output_dir),
        "topic": clean_topic,
        "command": command,
        "returncode": result.returncode,
        "stdout": result.stdout[-4000:] if result.stdout else "",
        "stderr": result.stderr[-4000:] if result.stderr else "",
        "videos": list_turbo_videos(output_dir),
    }


def turbo_api_running(api_url: str, urlopen=request.urlopen) -> bool:
    try:
        with urlopen(f"{api_url.rstrip('/')}/docs", timeout=2) as response:
            return 200 <= response.status < 500
    except (OSError, error.URLError):
        return False


def ensure_turbo_api_server(root: Path, command: list[str], api_url: str, popen=subprocess.Popen) -> bool:
    if turbo_api_running(api_url):
        return False
    env = os.environ.copy()
    popen(command, cwd=root, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(120):
        if turbo_api_running(api_url):
            return True
        time.sleep(0.5)
    raise RuntimeError(f"MoneyPrinterTurbo API did not start: {api_url}")


def create_turbo_video_task(api_url: str, topic: str, urlopen=request.urlopen) -> dict:
    payload = {
        "video_subject": topic,
        "video_script": (
            f"{topic}. 자연의 조용한 풍경과 편안한 분위기를 천천히 감상하는 영상입니다."
        ),
        "video_terms": [
            "forest birds",
            "peaceful forest",
            "birds in nature",
            "sunlight forest",
            "nature ambience",
        ],
        "video_aspect": "9:16",
        "video_count": 1,
        "video_clip_duration": 5,
        "video_source": "pexels",
        "voice_name": "no-voice",
        "subtitle_enabled": False,
        "bgm_type": "random",
    }
    data = json.dumps(payload).encode("utf-8")
    req = request.Request(
        f"{api_url.rstrip('/')}/api/v1/videos",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(req, timeout=10) as response:
        body = json.loads(response.read().decode("utf-8"))
    if body.get("status") != 200:
        raise RuntimeError(body.get("message") or "MoneyPrinterTurbo task creation failed.")
    return body.get("data") or {}


def wait_for_turbo_task(
    api_url: str,
    task_id: str,
    max_attempts: int = 360,
    poll_seconds: float = 5,
    urlopen=request.urlopen,
    sleep=time.sleep,
) -> dict:
    if not task_id:
        raise RuntimeError("MoneyPrinterTurbo task ID is missing.")

    task = {}
    for attempt in range(max_attempts):
        with urlopen(
            f"{api_url.rstrip('/')}/api/v1/tasks/{task_id}",
            timeout=10,
        ) as response:
            body = json.loads(response.read().decode("utf-8"))
        if body.get("status") != 200:
            raise RuntimeError(body.get("message") or "MoneyPrinterTurbo task query failed.")

        task = body.get("data") or {}
        state = task.get("state")
        if state == 1:
            return task
        if state == -1:
            raise RuntimeError(f"MoneyPrinterTurbo task failed: {task_id}")
        if attempt < max_attempts - 1:
            sleep(poll_seconds)

    raise TimeoutError(f"MoneyPrinterTurbo task did not finish: {task_id}")


def list_turbo_videos(output_dir: Path) -> list[dict]:
    if not output_dir.exists() or not output_dir.is_dir():
        return []
    files = [
        path
        for path in output_dir.rglob("*")
        if path.is_file() and path.suffix.lower() in SUPPORTED_TURBO_VIDEO_EXTENSIONS
    ]
    return [
        {"name": path.relative_to(output_dir).as_posix(), "path": str(path), "size_bytes": path.stat().st_size}
        for path in sorted(files, key=lambda item: item.stat().st_mtime, reverse=True)
    ]


def moneyprinter_status(output_dir: Path) -> dict:
    videos = list_turbo_videos(output_dir)
    return {
        "configured": output_dir.exists() and output_dir.is_dir(),
        "output_dir": str(output_dir),
        "videos": videos,
    }


def import_turbo_video(output_dir: Path, input_root: Path, video_name: str) -> dict:
    relative_name = video_name.replace("\\", "/").strip()
    relative_path = Path(relative_name)
    if (
        not relative_name
        or relative_path.is_absolute()
        or any(part in {"", ".", ".."} for part in relative_path.parts)
    ):
        raise ValueError("Invalid MoneyPrinterTurbo video name")
    source = output_dir / relative_path
    if not source.exists() or not source.is_file():
        raise FileNotFoundError(f"MoneyPrinterTurbo video not found: {relative_name}")
    if source.suffix.lower() not in SUPPORTED_TURBO_VIDEO_EXTENSIONS:
        raise ValueError("Unsupported MoneyPrinterTurbo video extension")
    target_dir = input_root / "videos"
    target_dir.mkdir(parents=True, exist_ok=True)
    target_name = _sanitize_filename(source.name)
    target = _unique_file_path(target_dir, target_name)
    target.write_bytes(source.read_bytes())
    return {"kind": "video", "name": target.name, "path": str(target), "size_bytes": target.stat().st_size}


def _sanitize_filename(filename: str) -> str:
    raw_name = filename.replace("\\", "/").split("/")[-1]
    stem = Path(raw_name).stem
    suffix = Path(raw_name).suffix.lower()
    safe_stem = re.sub(r"[^A-Za-z0-9가-힣._-]+", "-", stem).strip("-._")
    return f"{safe_stem or 'turbo-video'}{suffix}"


def _unique_file_path(directory: Path, filename: str) -> Path:
    path = directory / filename
    if not path.exists():
        return path
    stem = path.stem
    suffix = path.suffix
    index = 2
    while True:
        candidate = directory / f"{stem}-{index}{suffix}"
        if not candidate.exists():
            return candidate
        index += 1
