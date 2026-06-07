from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

from .editor import render_video
from .media_profiler import profile_media
from .metadata_agent import build_youtube_metadata
from .models import PolicyFinding, SourceAsset, write_json
from .music_agent import load_music_catalog, select_music
from .policy_guard import evaluate_policy
from .upload_prep import safe_slug, write_approval_checklist, write_metadata_file


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Prepare upload-ready YouTube healing video packages from owned bird-sound videos."
    )
    parser.add_argument("--source", required=True, help="Path to owned source video")
    parser.add_argument("--music-catalog", required=True, help="Path to local music catalog JSON")
    parser.add_argument(
        "--output-root",
        default="outputs/youtube-healing",
        help="Output root folder",
    )
    parser.add_argument(
        "--shooting-date",
        default=str(date.today()),
        help="Shooting date in YYYY-MM-DD",
    )
    parser.add_argument(
        "--general-location",
        default="forest",
        help="General non-sensitive location label",
    )
    parser.add_argument(
        "--privacy-notes",
        default="no people visible",
        help="Privacy notes for policy review",
    )
    parser.add_argument("--not-owned", action="store_true", help="Mark source ownership as unconfirmed")
    parser.add_argument("--bilingual", action="store_true", help="Generate Korean and English metadata")
    return parser


def _unique_output_dir(output_root: Path, folder_name: str) -> Path:
    output_dir = output_root / folder_name
    if not output_dir.exists():
        return output_dir
    suffix = 2
    while True:
        candidate = output_root / f"{folder_name}-{suffix}"
        if not candidate.exists():
            return candidate
        suffix += 1


def run(args: argparse.Namespace) -> Path:
    source_path = Path(args.source).expanduser().resolve()
    catalog_path = Path(args.music_catalog).expanduser().resolve()
    output_root = Path(args.output_root).expanduser().resolve()

    asset = SourceAsset(
        source_path=str(source_path),
        owned_by_user=not args.not_owned,
        shooting_date=args.shooting_date,
        general_location=args.general_location,
        privacy_notes=args.privacy_notes,
    )
    profile = profile_media(source_path)

    folder_name = f"{date.today().isoformat()}-{safe_slug(source_path.stem)}"
    output_dir = _unique_output_dir(output_root, folder_name)
    output_dir.mkdir(parents=True, exist_ok=True)

    write_json(output_dir / "asset_manifest.json", asset)
    write_json(output_dir / "media_profile.json", profile)

    tracks = load_music_catalog(catalog_path)
    try:
        selection = select_music(tracks, desired_moods=["calm", "ambient", "forest"])
    except ValueError as exc:
        findings = [
            PolicyFinding(
                code="music_selection_failed",
                severity="blocker",
                message=str(exc),
                blocking=True,
            )
        ]
        write_json(output_dir / "policy_report.json", findings)
        write_approval_checklist(output_dir / "approval_checklist.md", findings)
        return output_dir

    findings = evaluate_policy(asset, profile, selection)

    write_json(output_dir / "music_selection.json", selection)
    write_json(output_dir / "license_log.json", selection.track.evidence)

    music_path = Path(selection.track.local_path).expanduser()
    if not music_path.exists():
        findings.append(
            PolicyFinding(
                code="music_file_missing",
                severity="blocker",
                message="Selected music file is missing. Check music catalog local_path.",
                blocking=True,
            )
        )

    write_json(output_dir / "policy_report.json", findings)

    if any(finding.blocking for finding in findings):
        write_approval_checklist(output_dir / "approval_checklist.md", findings)
        return output_dir

    final_video = output_dir / "final_video.mp4"
    thumbnail = output_dir / "thumbnail.jpg"
    edit_report = render_video(
        source_video=source_path,
        music_selection=selection,
        output_video=final_video,
        thumbnail_path=thumbnail,
        duration_seconds=profile.duration_seconds,
    )
    write_json(output_dir / "edit_report.json", edit_report)

    metadata_text = build_youtube_metadata(
        asset=asset,
        profile=profile,
        music_selection=selection,
        bilingual=args.bilingual,
    )
    write_metadata_file(output_dir / "youtube_metadata.md", metadata_text)
    write_approval_checklist(output_dir / "approval_checklist.md", findings)
    return output_dir


def main() -> None:
    parser = build_parser()
    output_dir = run(parser.parse_args())
    print(f"Upload-ready review folder: {output_dir}")


if __name__ == "__main__":
    main()
