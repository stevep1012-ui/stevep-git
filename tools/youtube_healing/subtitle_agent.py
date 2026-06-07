from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

from .media_tools import media_tool_env


VALID_METHODS = {"intro_outro", "lower_third", "timed_captions"}
DEFAULT_KOREAN_FONT = Path("/System/Library/Fonts/AppleSDGothicNeo.ttc")


def _float_setting(settings: dict, key: str, default: float) -> float:
    try:
        return float(settings.get(key, default))
    except (TypeError, ValueError):
        return default


def _int_setting(settings: dict, key: str, default: int) -> int:
    try:
        return int(settings.get(key, default))
    except (TypeError, ValueError):
        return default


def _escape_drawtext_text(text: str) -> str:
    return (
        str(text)
        .replace("\\", "\\\\")
        .replace(":", "\\:")
        .replace("'", "\\'")
        .replace("%", "\\%")
        .replace("\n", " ")
    )


def _y_expression(position: str) -> str:
    if position == "top":
        return "h*0.12"
    if position == "center":
        return "(h-text_h)/2"
    return "h-text_h-h*0.12"


def _drawtext(text: str, start: float, end: float, settings: dict) -> str:
    font_size = _int_setting(settings, "font_size", 44)
    position = settings.get("position", "bottom")
    font_color = settings.get("font_color", "white")
    box_enabled = bool(settings.get("box", True))
    box = ":box=1:boxcolor=black@0.38:boxborderw=18" if box_enabled else ""
    font_file = Path(settings.get("font_file", DEFAULT_KOREAN_FONT))
    font = f":fontfile='{font_file}'" if font_file.is_file() else ""
    return (
        "drawtext="
        f"text='{_escape_drawtext_text(text)}'"
        f":x=(w-text_w)/2:y={_y_expression(position)}"
        f":fontsize={font_size}:fontcolor={font_color}"
        f"{font}"
        f"{box}:shadowcolor=black@0.55:shadowx=2:shadowy=2"
        f":enable='between(t,{start:.1f},{end:.1f})'"
    )


def build_subtitle_filter(settings: dict) -> str:
    method = settings.get("method", "lower_third")
    if method not in VALID_METHODS:
        raise ValueError("Subtitle method must be intro_outro, lower_third, or timed_captions.")

    if method == "intro_outro":
        text = settings.get("text", "").strip()
        if not text:
            raise ValueError("Subtitle text is required.")
        duration = _float_setting(settings, "duration_seconds", 30)
        intro = _float_setting(settings, "intro_seconds", 3)
        outro = _float_setting(settings, "outro_seconds", 3)
        first = _drawtext(text, 0, min(intro, duration), settings)
        second = _drawtext(text, max(duration - outro, 0), duration, settings)
        return ",".join([first, second])

    if method == "lower_third":
        text = settings.get("text", "").strip()
        if not text:
            raise ValueError("Subtitle text is required.")
        start = _float_setting(settings, "start_seconds", 0)
        end = _float_setting(settings, "end_seconds", 5)
        return _drawtext(text, start, end, settings)

    captions = settings.get("captions", [])
    if not captions:
        raise ValueError("At least one timed caption is required.")
    filters = []
    for caption in captions:
        text = str(caption.get("text", "")).strip()
        if not text:
            continue
        start = _float_setting(caption, "start_seconds", 0)
        end = _float_setting(caption, "end_seconds", start + 3)
        filters.append(_drawtext(text, start, end, settings))
    if not filters:
        raise ValueError("At least one timed caption with text is required.")
    return ",".join(filters)


def _supports_drawtext(ffmpeg_path: Path) -> bool:
    result = subprocess.run(
        [str(ffmpeg_path), "-hide_banner", "-h", "filter=drawtext"],
        env=media_tool_env(),
        capture_output=True,
        text=True,
        check=False,
    )
    return "Filter drawtext" in f"{result.stdout}\n{result.stderr}"


def _subtitle_ffmpeg_candidates() -> list[Path]:
    candidates = []
    configured = os.environ.get("YOUTUBE_HEALING_FFMPEG", "").strip()
    if configured:
        candidates.append(Path(configured).expanduser())
    installed = shutil.which("ffmpeg")
    if installed:
        candidates.append(Path(installed))
    candidates.extend(
        [
            Path("/opt/homebrew/bin/ffmpeg"),
            Path("/usr/local/bin/ffmpeg"),
        ]
    )
    for turbo_root in (
        Path(os.environ.get("MONEYPRINTER_TURBO_DIR", "")).expanduser(),
        Path.home() / "MoneyPrinterTurbo",
        Path.home() / "Applications" / "MoneyPrinterTurbo",
    ):
        if str(turbo_root) in {"", "."}:
            continue
        candidates.extend(
            turbo_root.glob(".venv/lib/python*/site-packages/imageio_ffmpeg/binaries/ffmpeg-*")
        )
    return candidates


def find_subtitle_ffmpeg(candidates: list[Path] | None = None) -> Path:
    for candidate in candidates or _subtitle_ffmpeg_candidates():
        if candidate.is_file() and _supports_drawtext(candidate):
            return candidate
    raise FileNotFoundError(
        "FFmpeg with drawtext support is required for subtitles. "
        "Set YOUTUBE_HEALING_FFMPEG to a compatible FFmpeg binary."
    )


def build_subtitle_ffmpeg_command(
    input_video: Path,
    output_video: Path,
    settings: dict,
    ffmpeg_executable: str = "ffmpeg",
) -> list[str]:
    return [
        ffmpeg_executable,
        "-y",
        "-i",
        str(input_video),
        "-vf",
        build_subtitle_filter(settings),
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-crf",
        "20",
        "-c:a",
        "copy",
        str(output_video),
    ]


def render_subtitled_video(input_video: Path, output_video: Path, settings: dict) -> dict:
    output_video.parent.mkdir(parents=True, exist_ok=True)
    ffmpeg_path = find_subtitle_ffmpeg()
    command = build_subtitle_ffmpeg_command(
        input_video,
        output_video,
        settings,
        ffmpeg_executable=str(ffmpeg_path),
    )
    subprocess.run(command, env=media_tool_env(), check=True)
    report = {
        "input_path": str(input_video),
        "output_path": str(output_video),
        "settings": settings,
        "ffmpeg_command": command,
    }
    (output_video.parent / "subtitle_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return report
