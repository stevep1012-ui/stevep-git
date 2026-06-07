from __future__ import annotations

from pathlib import Path, PureWindowsPath

from .models import MediaProfile, MusicSelection, SourceAsset


def _source_file_label(source_path: str) -> str:
    windows_name = PureWindowsPath(source_path).name
    return Path(windows_name).name or "owned source video"


def build_youtube_metadata(
    asset: SourceAsset,
    profile: MediaProfile,
    music_selection: MusicSelection,
    bilingual: bool = False,
    title: str | None = None,
    description: str | None = None,
) -> str:
    title_ko = title or "숲속 새소리 힐링 Shorts | 자연의 아침 소리"
    title_en = "Calm Forest Birdsong Shorts | Peaceful Nature Ambience"
    title_block = f"# Title\n{title_ko}\n"
    if bilingual:
        title_block += f"\n# English Title\n{title_en}\n"
    description_text = description or (
        "직접 촬영한 숲속 영상과 새소리에 조용한 배경음악을 낮게 더한 짧은 영상입니다.\n"
        "새소리와 자연의 분위기를 편안하게 감상해 주세요."
    )

    attribution = ""
    if music_selection.track.evidence.attribution_required:
        attribution = (
            "\n\n# Music Attribution\n"
            f"{music_selection.track.title} by {music_selection.track.artist}\n"
            f"Source: {music_selection.track.evidence.source_name}\n"
            f"{music_selection.track.evidence.source_url}\n"
        )
    source_label = _source_file_label(asset.source_path)

    return (
        f"{title_block}\n"
        "# Description\n"
        f"{description_text}\n\n"
        "# Hashtags\n"
        "#새소리 #숲소리 #힐링영상 #자연소리 #Birdsong #NatureSounds #Shorts\n\n"
        "# Source Notes\n"
        f"- Source video: {source_label}\n"
        f"- Format: {profile.width}x{profile.height}, {profile.duration_seconds:.1f}s\n"
        f"- Music: {music_selection.track.title} / {music_selection.track.artist}\n"
        f"{attribution}\n"
    )
