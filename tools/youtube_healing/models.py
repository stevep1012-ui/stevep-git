from __future__ import annotations

import json
from dataclasses import asdict, dataclass, is_dataclass
from enum import Enum
from pathlib import Path
from typing import Any


class VideoPackageStatus(Enum):
    DRAFT = "draft"
    READY_FOR_REVIEW = "ready_for_review"
    APPROVED = "approved"
    UPLOADED = "uploaded"
    REJECTED = "rejected"


@dataclass(frozen=True)
class SourceAsset:
    source_path: str
    owned_by_user: bool
    shooting_date: str
    general_location: str
    privacy_notes: str


@dataclass(frozen=True)
class MediaProfile:
    source_path: str
    duration_seconds: float
    width: int
    height: int
    video_codec: str
    audio_codec: str
    frame_rate: float
    has_audio: bool
    orientation: str
    youtube_format: str


@dataclass(frozen=True)
class LicenseEvidence:
    source_name: str
    source_url: str
    license_terms: str
    attribution_required: bool
    access_date: str


@dataclass(frozen=True)
class MusicTrack:
    track_id: str
    title: str
    artist: str
    duration_seconds: int
    local_path: str
    mood_tags: list[str]
    has_vocals: bool
    strong_beat: bool
    evidence: LicenseEvidence


@dataclass(frozen=True)
class MusicSelection:
    track: MusicTrack
    target_gain_db: float
    reason: str


@dataclass(frozen=True)
class PolicyFinding:
    code: str
    severity: str
    message: str
    blocking: bool


@dataclass(frozen=True)
class EditReport:
    output_path: str
    thumbnail_path: str
    ffmpeg_command: list[str]


def to_jsonable(value: Any) -> Any:
    if is_dataclass(value):
        return {key: to_jsonable(item) for key, item in asdict(value).items()}
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, list):
        return [to_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {key: to_jsonable(item) for key, item in value.items()}
    return value


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(to_jsonable(value), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


# Validation helpers
def validate_duration(duration_seconds: float) -> float:
    if not isinstance(duration_seconds, (int, float)):
        raise TypeError(f"Duration must be number, got {type(duration_seconds)}")
    if duration_seconds <= 0:
        raise ValueError(f"Duration must be positive, got {duration_seconds}")
    if duration_seconds > 3600:
        raise ValueError(f"Duration too long (max 1 hour), got {duration_seconds}s")
    return float(duration_seconds)


def validate_file_path(path_str: str, kind: str = "file") -> str:
    if not isinstance(path_str, str):
        raise TypeError(f"Path must be string, got {type(path_str)}")
    if not path_str.strip():
        raise ValueError("Path cannot be empty")
    if len(path_str) > 4096:
        raise ValueError(f"Path too long (max 4096 chars)")
    if ".." in path_str or path_str.startswith("/"):
        raise ValueError(f"Invalid path: contains .. or absolute path")
    return path_str.strip()


def validate_resolution(width: int, height: int) -> tuple[int, int]:
    if not isinstance(width, int) or not isinstance(height, int):
        raise TypeError("Width and height must be integers")
    if width < 100 or height < 100:
        raise ValueError(f"Resolution too small: {width}x{height} (min 100x100)")
    if width > 7680 or height > 4320:
        raise ValueError(f"Resolution too large: {width}x{height} (max 7680x4320)")
    return width, height


def validate_url(url: str) -> str:
    if not isinstance(url, str):
        raise TypeError(f"URL must be string, got {type(url)}")
    if not url.startswith(("http://", "https://")):
        raise ValueError(f"URL must start with http:// or https://")
    if len(url) > 2048:
        raise ValueError(f"URL too long (max 2048 chars)")
    return url
