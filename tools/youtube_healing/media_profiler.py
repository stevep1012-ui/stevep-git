from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from tools.youtube_healing.models import MediaProfile
from tools.youtube_healing.media_tools import media_tool_env

_profile_cache: dict[str, MediaProfile] = {}


def parse_frame_rate(value: str | None) -> float:
    if not value:
        return 0.0

    if "/" not in value:
        try:
            return float(value)
        except ValueError:
            return 0.0

    numerator_text, denominator_text = value.split("/", 1)
    try:
        numerator = float(numerator_text)
        denominator = float(denominator_text)
    except ValueError:
        return 0.0

    if denominator == 0:
        return 0.0
    return numerator / denominator


def classify_orientation(width: int, height: int) -> str:
    if height > width:
        return "vertical"
    if width > height:
        return "horizontal"
    return "square"


def classify_youtube_format(orientation: str, duration_seconds: float) -> str:
    if orientation == "vertical" and duration_seconds <= 60:
        return "shorts"
    return "standard"


def parse_ffprobe_json(payload: dict[str, Any], source_path: str | Path) -> MediaProfile:
    streams = payload.get("streams", [])
    video_stream = _first_stream(streams, "video")
    audio_stream = _first_stream(streams, "audio")

    if not video_stream:
        raise ValueError(f"No video stream found in ffprobe output for {source_path}")

    width = _parse_positive_int(video_stream.get("width"), "width", source_path)
    height = _parse_positive_int(video_stream.get("height"), "height", source_path)
    duration_seconds = _parse_duration(payload)
    orientation = classify_orientation(width, height)

    return MediaProfile(
        source_path=str(source_path),
        duration_seconds=duration_seconds,
        width=width,
        height=height,
        video_codec=str(video_stream.get("codec_name", "")),
        audio_codec=str(audio_stream.get("codec_name", "")) if audio_stream else "",
        frame_rate=parse_frame_rate(video_stream.get("avg_frame_rate")),
        has_audio=bool(audio_stream),
        orientation=orientation,
        youtube_format=classify_youtube_format(orientation, duration_seconds),
    )


def profile_media(source_path: str | Path) -> MediaProfile:
    path_obj = Path(source_path)
    cache_key = str(path_obj.resolve())

    if cache_key in _profile_cache:
        return _profile_cache[cache_key]

    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-print_format",
            "json",
            "-show_format",
            "-show_streams",
            str(path_obj),
        ],
        capture_output=True,
        check=True,
        env=media_tool_env(),
        text=True,
    )
    profile = parse_ffprobe_json(json.loads(result.stdout), source_path)
    _profile_cache[cache_key] = profile
    return profile


def clear_profile_cache() -> None:
    global _profile_cache
    _profile_cache.clear()


def _first_stream(streams: list[dict[str, Any]], codec_type: str) -> dict[str, Any]:
    for stream in streams:
        if stream.get("codec_type") == codec_type:
            return stream
    return {}


def _parse_duration(payload: dict[str, Any]) -> float:
    try:
        return float(payload.get("format", {}).get("duration", 0))
    except (TypeError, ValueError):
        return 0.0


def _parse_positive_int(value: Any, field_name: str, source_path: str | Path) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        raise ValueError(f"Invalid video {field_name} in ffprobe output for {source_path}") from None

    if parsed <= 0:
        raise ValueError(f"Invalid video {field_name} in ffprobe output for {source_path}")
    return parsed
