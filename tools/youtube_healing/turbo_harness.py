#!/usr/bin/env python3
"""
MoneyPrinterTurbo + YouTube Bird Integrated Harness

Combines MoneyPrinterTurbo video generation with YouTube Bird's review-package pipeline.
Generates review-ready videos with music, metadata, and policy evidence.

Usage:
    python3 -m tools.youtube_healing.turbo_harness \\
      --topic "숲속 새소리" \\
      --confirm-source-rights \\
      --music-catalog config/youtube_healing/music_catalog.json \\
      --output-root outputs/youtube-healing

"""

from __future__ import annotations

import argparse
import logging
import sys
from datetime import date
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
    ]
)
logger = logging.getLogger(__name__)

from .moneyprinter_turbo import (
    default_turbo_root,
    default_turbo_output_dir,
    default_turbo_command_template,
    list_turbo_videos,
    run_moneyprinter_engine,
    import_turbo_video,
    moneyprinter_engine_status,
)
from .editor import render_video
from .media_profiler import profile_media
from .metadata_agent import build_youtube_metadata
from .models import PolicyFinding, SourceAsset, write_json
from .music_agent import load_music_catalog, select_music
from .policy_guard import evaluate_policy
from .publish_agent import build_publish_plan, write_publish_plan
from .upload_prep import safe_slug, write_approval_checklist, write_metadata_file


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate YouTube healing videos from MoneyPrinterTurbo content with automatic music mixing."
    )
    parser.add_argument(
        "--topic",
        required=True,
        help="MoneyPrinterTurbo topic (e.g., '숲속 새소리 힐링')",
    )
    parser.add_argument(
        "--use-existing-video",
        help="Use existing Turbo video instead of generating new one (filename in Turbo output)",
    )
    parser.add_argument(
        "--music-catalog",
        required=True,
        help="Path to local music catalog JSON",
    )
    parser.add_argument(
        "--output-root",
        default="outputs/youtube-healing",
        help="Output root folder for final packages",
    )
    parser.add_argument(
        "--shooting-date",
        default=str(date.today()),
        help="Creation date in YYYY-MM-DD",
    )
    parser.add_argument(
        "--general-location",
        default="generated",
        help="General location label",
    )
    parser.add_argument(
        "--privacy-notes",
        default="AI-generated content, no personal data",
        help="Privacy notes for policy review",
    )
    parser.add_argument(
        "--confirm-source-rights",
        action="store_true",
        help="Confirm rights to use the generated or imported source assets",
    )
    parser.add_argument(
        "--bilingual",
        action="store_true",
        help="Generate Korean and English metadata",
    )
    parser.add_argument(
        "--turbo-root",
        help="MoneyPrinterTurbo installation root (default: env or ./external/MoneyPrinterTurbo)",
    )
    parser.add_argument(
        "--turbo-output",
        help="MoneyPrinterTurbo output directory (default: $turbo-root/storage/tasks)",
    )
    parser.add_argument(
        "--turbo-command",
        help="MoneyPrinterTurbo server command template (default: MONEYPRINTER_TURBO_COMMAND)",
    )
    return parser


def _unique_output_dir(output_root: Path, folder_name: str) -> Path:
    output_dir = output_root / folder_name
    if not output_dir.exists():
        return output_dir
    index = 2
    while True:
        candidate = output_root / f"{folder_name}-{index}"
        if not candidate.exists():
            return candidate
        index += 1


def run(args: argparse.Namespace) -> Path:
    project_root = Path(__file__).resolve().parents[2]
    turbo_root = Path(args.turbo_root or default_turbo_root(project_root))
    turbo_output = Path(args.turbo_output or default_turbo_output_dir(project_root))
    turbo_command = args.turbo_command or default_turbo_command_template()

    # Check Turbo installation
    logger.info(f"MoneyPrinterTurbo Integration starting")
    logger.info(f"Root: {turbo_root}")
    logger.info(f"Output: {turbo_output}")

    turbo_status = moneyprinter_engine_status(turbo_root, turbo_output, turbo_command)
    if not turbo_status["installed"]:
        logger.error(f"MoneyPrinterTurbo not found at {turbo_root}")
        logger.error(f"Install from: https://github.com/harry0703/MoneyPrinterTurbo")
        raise RuntimeError(f"MoneyPrinterTurbo not found at {turbo_root}")

    logger.info(f"MoneyPrinterTurbo installed and ready")

    # Get or create Turbo video
    turbo_video_path = None
    if args.use_existing_video:
        logger.info(f"Loading existing Turbo video: {args.use_existing_video}")
        videos = list_turbo_videos(turbo_output)
        matching = [v for v in videos if v["name"] == args.use_existing_video]
        if not matching:
            logger.error(f"Turbo video not found: {args.use_existing_video}")
            logger.info(f"Available videos: {[v['name'] for v in videos[:10]]}")
            raise FileNotFoundError(f"Turbo video not found: {args.use_existing_video}")
        turbo_video_path = Path(matching[0]["path"])
        logger.info(f"Using existing Turbo video: {turbo_video_path.name}")
    else:
        logger.info(f"Generating new Turbo video for topic: '{args.topic}'")
        if not turbo_command.strip():
            logger.error("MONEYPRINTER_TURBO_COMMAND environment variable not set")
            raise RuntimeError("MONEYPRINTER_TURBO_COMMAND not set")

        try:
            result = run_moneyprinter_engine(
                root=turbo_root,
                output_dir=turbo_output,
                topic=args.topic,
                command_template=turbo_command,
            )
            if not result.get("videos"):
                logger.error("Turbo video generation failed or no videos produced")
                if result.get("stderr"):
                    logger.error(f"Engine error: {result['stderr'][:500]}")
                raise RuntimeError("Turbo video generation produced no videos")
            turbo_video_path = Path(result["videos"][0]["path"])
            logger.info(f"Turbo video generated successfully: {turbo_video_path.name}")
        except Exception as exc:
            logger.exception(f"Turbo execution failed: {exc}")
            raise

    if not turbo_video_path or not turbo_video_path.exists():
        logger.error(f"Turbo video file not found: {turbo_video_path}")
        raise FileNotFoundError(f"Turbo video not found: {turbo_video_path}")

    # Import Turbo video to YouTube Bird
    logger.info("Importing Turbo video to YouTube Bird")
    input_root = Path(args.output_root).parent / "inputs"
    input_root.mkdir(parents=True, exist_ok=True)

    try:
        imported = import_turbo_video(
            output_dir=turbo_output,
            input_root=input_root,
            video_name=turbo_video_path.relative_to(turbo_output).as_posix(),
        )
        source_path = Path(imported["path"])
        logger.info(f"Successfully imported: {imported['name']}")
    except Exception as exc:
        logger.exception(f"Video import failed: {exc}")
        raise

    # Load music catalog
    logger.info(f"Loading music catalog from {args.music_catalog}")
    try:
        tracks = load_music_catalog(Path(args.music_catalog))
        if not tracks:
            logger.error(f"No music tracks found in {args.music_catalog}")
            raise ValueError(f"No tracks found in {args.music_catalog}")
        logger.info(f"Loaded {len(tracks)} music track(s)")
    except Exception as exc:
        logger.exception(f"Music catalog load failed: {exc}")
        raise

    # Profile media
    logger.info(f"Analyzing Turbo video: {source_path}")
    try:
        media_profile = profile_media(source_path)
        logger.info(f"Video format: {media_profile.width}x{media_profile.height}, duration: {media_profile.duration_seconds}s, codec: {media_profile.video_codec}")
    except Exception as exc:
        logger.exception(f"Media profiling failed: {exc}")
        raise

    # Select music
    logger.info("Selecting background music (desired moods: calm, relaxing, ambient)")
    try:
        music_selection = select_music(
            tracks=tracks,
            desired_moods=["calm", "relaxing", "ambient"],
        )
        logger.info(f"Selected music: '{music_selection.track.title}' by {music_selection.track.artist} ({music_selection.reason})")
    except Exception as exc:
        logger.exception(f"Music selection failed: {exc}")
        raise

    # Create source asset model
    source_asset = SourceAsset(
        source_path=str(source_path),
        owned_by_user=args.confirm_source_rights,
        shooting_date=args.shooting_date,
        general_location=args.general_location,
        privacy_notes=args.privacy_notes,
    )

    # Evaluate policy
    logger.info("Evaluating policy for compliance and licensing")
    findings = evaluate_policy(
        asset=source_asset,
        profile=media_profile,
        music_selection=music_selection,
    )
    music_path = Path(music_selection.track.local_path).expanduser()
    if not music_path.exists():
        logger.warning(f"Music file not found at: {music_selection.track.local_path}")
        findings.append(
            PolicyFinding(
                code="music_file_missing",
                severity="blocker",
                message="Selected music file is missing. Check music catalog local_path.",
                blocking=True,
            )
        )
    blockers = [f for f in findings if f.blocking]
    if blockers:
        logger.warning(f"Policy blockers found: {len(blockers)}")
        for finding in blockers:
            logger.warning(f"  - {finding.code}: {finding.message}")
    else:
        logger.info(f"Policy evaluation passed ({len(findings)} info message(s))")

    # Create output directory
    logger.info(f"Creating output package directory")
    output_root = Path(args.output_root)
    output_root.mkdir(parents=True, exist_ok=True)
    folder_name = safe_slug(f"{date.today()}-{args.topic[:30]}")
    output_dir = _unique_output_dir(output_root, folder_name)
    output_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Output directory created: {output_dir}")

    # Write manifests
    asset_manifest = {
        "source": str(source_asset.source_path),
        "owned": source_asset.owned_by_user,
        "date": source_asset.shooting_date,
        "location": source_asset.general_location,
        "notes": source_asset.privacy_notes,
    }
    write_json(output_dir / "asset_manifest.json", asset_manifest)

    media_profile_data = {
        "width": media_profile.width,
        "height": media_profile.height,
        "duration_seconds": media_profile.duration_seconds,
        "format": media_profile.youtube_format,
        "codec_video": media_profile.video_codec,
        "codec_audio": media_profile.audio_codec,
    }
    write_json(output_dir / "media_profile.json", media_profile_data)

    music_data = {
        "track_id": music_selection.track.track_id,
        "title": music_selection.track.title,
        "artist": music_selection.track.artist,
        "source": music_selection.track.evidence.source_name,
        "source_url": music_selection.track.evidence.source_url,
        "license_terms": music_selection.track.evidence.license_terms,
        "attribution_required": music_selection.track.evidence.attribution_required,
        "access_date": music_selection.track.evidence.access_date,
    }
    write_json(output_dir / "music_selection.json", music_data)

    license_log = {
        "track_id": music_selection.track.track_id,
        "title": music_selection.track.title,
        "artist": music_selection.track.artist,
        "evidence": {
            "source_name": music_selection.track.evidence.source_name,
            "source_url": music_selection.track.evidence.source_url,
            "license_terms": music_selection.track.evidence.license_terms,
            "attribution_required": music_selection.track.evidence.attribution_required,
            "access_date": music_selection.track.evidence.access_date,
        },
    }
    write_json(output_dir / "license_log.json", license_log)

    policy_data = {
        "blockers": [
            {
                "code": f.code,
                "severity": f.severity,
                "message": f.message,
            }
            for f in blockers
        ],
        "info": [
            {
                "code": f.code,
                "message": f.message,
            }
            for f in findings if not f.blocking
        ],
    }
    write_json(output_dir / "policy_report.json", policy_data)

    # Write approval checklist
    write_approval_checklist(
        output_dir / "approval_checklist.md",
        findings,
        audio_check="Confirm generated visuals and background music are appropriate",
    )

    if blockers:
        print(f"\n⚠️  Review required: {len(blockers)} policy issue(s)")
        print(f"   Open: {output_dir / 'approval_checklist.md'}")
        return output_dir

    # Render video
    logger.info("Rendering final video with background music")
    try:
        edit_report = render_video(
            source_video=source_path,
            music_selection=music_selection,
            output_video=output_dir / "final_video.mp4",
            thumbnail_path=output_dir / "thumbnail.jpg",
            duration_seconds=media_profile.duration_seconds,
        )
        logger.info(f"Final video rendered: {edit_report.output_path}")
        logger.info(f"Thumbnail generated: {edit_report.thumbnail_path}")
        write_json(output_dir / "edit_report.json", edit_report)
    except Exception as exc:
        logger.exception(f"Video rendering failed: {exc}")
        raise

    # Generate metadata
    logger.info("Generating YouTube and Instagram metadata")
    try:
        metadata = build_youtube_metadata(
            asset=source_asset,
            profile=media_profile,
            music_selection=music_selection,
            bilingual=args.bilingual,
            title=f"{args.topic} | 생성형 힐링 영상",
            description=(
                "생성형 도구로 만든 영상에 라이선스를 확인한 배경음악을 더했습니다.\n"
                "사용된 영상·음원 자산의 권리와 공개 적합성을 업로드 전에 다시 확인해 주세요."
            ),
        )
        write_metadata_file(output_dir / "youtube_metadata.md", metadata)
        publish_plan = build_publish_plan(
            package_dir=output_dir,
            title=f"{args.topic} | 생성형 자연 영상",
            privacy_status="unlisted",
        )
        write_publish_plan(output_dir, publish_plan)
        logger.info(f"Metadata files written to {output_dir}")
    except Exception as exc:
        logger.warning(f"Metadata generation failed (non-critical): {exc}")

    logger.info("=" * 60)
    logger.info("YouTube Healing Video Package Ready")
    logger.info("=" * 60)
    logger.info(f"Output Directory: {output_dir}")
    logger.info(f"Final Video: {output_dir / 'final_video.mp4'}")
    logger.info(f"Thumbnail: {output_dir / 'thumbnail.jpg'}")
    logger.info(f"Metadata: {output_dir / 'youtube_metadata.md'}")
    logger.info(f"Next Steps: Review, approve music volume, add subtitles, publish")
    logger.info(f"Web Dashboard: http://127.0.0.1:8787/")

    return output_dir


def main() -> int:
    parser = build_parser()
    try:
        run(parser.parse_args())
    except Exception:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
