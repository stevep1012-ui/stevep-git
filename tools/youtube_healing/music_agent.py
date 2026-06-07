from __future__ import annotations

import json
from pathlib import Path

from .models import LicenseEvidence, MusicSelection, MusicTrack
from .policy_guard import _has_allowed_music_source, _has_usable_license_terms


ALLOWED_MVP_SOURCES = {"YouTube Audio Library", "Musopen"}
DEFAULT_MUSIC_GAIN_DB = -18.0


def _normalize_mood(value: str) -> str:
    return value.strip().lower()


def _contains_placeholder_text(value: str) -> bool:
    normalized = value.strip().lower()
    return (
        "replace with" in normalized
        or "replace-with" in normalized
        or "record the exact" in normalized
    )


def load_music_catalog(path: Path) -> list[MusicTrack]:
    raw_tracks = json.loads(path.read_text(encoding="utf-8"))
    tracks: list[MusicTrack] = []
    for item in raw_tracks:
        evidence = LicenseEvidence(**item["evidence"])
        tracks.append(
            MusicTrack(
                track_id=item["track_id"],
                title=item["title"],
                artist=item["artist"],
                duration_seconds=int(item["duration_seconds"]),
                local_path=item["local_path"],
                mood_tags=list(item["mood_tags"]),
                has_vocals=bool(item["has_vocals"]),
                strong_beat=bool(item["strong_beat"]),
                evidence=evidence,
            )
        )
    return tracks


def is_track_allowed_for_mvp(track: MusicTrack) -> bool:
    return (
        track.evidence.source_name in ALLOWED_MVP_SOURCES
        and not track.has_vocals
        and not track.strong_beat
        and _has_allowed_music_source(
            track.evidence.source_name,
            track.evidence.source_url,
        )
        and _has_usable_license_terms(track.evidence.license_terms)
        and bool(track.evidence.access_date.strip())
        and not _contains_placeholder_text(track.title)
        and not _contains_placeholder_text(track.artist)
        and not _contains_placeholder_text(track.local_path)
    )


def select_music(
    tracks: list[MusicTrack], desired_moods: list[str]
) -> MusicSelection:
    normalized_desired_moods = {_normalize_mood(mood) for mood in desired_moods}
    allowed = [track for track in tracks if is_track_allowed_for_mvp(track)]
    ranked = sorted(
        allowed,
        key=lambda track: len(
            {_normalize_mood(mood) for mood in track.mood_tags}.intersection(
                normalized_desired_moods
            )
        ),
        reverse=True,
    )
    if not ranked:
        raise ValueError("No eligible YouTube Audio Library or Musopen music track found")
    selected = ranked[0]
    matched = sorted(
        {_normalize_mood(mood) for mood in selected.mood_tags}.intersection(
            normalized_desired_moods
        )
    )
    reason = (
        "Matched moods: " + ", ".join(matched)
        if matched
        else "Selected first eligible calm track"
    )
    return MusicSelection(
        track=selected,
        target_gain_db=DEFAULT_MUSIC_GAIN_DB,
        reason=reason,
    )
