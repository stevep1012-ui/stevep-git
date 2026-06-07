from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import date, datetime, timezone
from email.parser import BytesParser
from email.policy import default
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

# Initialize Sentry for error tracking (optional)
try:
    import sentry_sdk
    if sentry_dsn := os.getenv("SENTRY_DSN"):
        sentry_sdk.init(
            dsn=sentry_dsn,
            environment=os.getenv("SENTRY_ENVIRONMENT", "production"),
            traces_sample_rate=float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.1")),
            attach_stacktrace=True,
        )
except ImportError:
    sentry_sdk = None  # Sentry is optional

from .auth_context import AuthError, resolve_user_id
from .cloud_config import CloudConfigError, load_cloud_config
from .instagram_auth import (
    build_instagram_login_url,
    exchange_code_for_instagram_token,
    instagram_token_status,
    load_instagram_token,
    validate_instagram_state,
)
from .moneyprinter_turbo import (
    default_turbo_command_template,
    default_turbo_output_dir,
    default_turbo_root,
    import_turbo_video,
    moneyprinter_engine_status,
    moneyprinter_status,
    run_moneyprinter_engine,
)
from .editor import render_image_video, render_sequence_video, render_video
from .media_profiler import profile_media
from .metadata_agent import build_youtube_metadata
from .models import (
    LicenseEvidence,
    MediaProfile,
    MusicSelection,
    MusicTrack,
    SourceAsset,
    to_jsonable,
    write_json,
)
from .publish_agent import upload_instagram_from_plan
from .subtitle_agent import render_subtitled_video
from .tenant_store import build_user_paths
from .upload_prep import safe_slug, write_approval_checklist, write_metadata_file


PROJECT_ROOT = Path(__file__).resolve().parents[2]
WEB_ROOT = PROJECT_ROOT / "web"
INPUT_ROOT = PROJECT_ROOT / "inputs"
CONFIG_ROOT = PROJECT_ROOT / "config" / "youtube_healing"
MULTI_USER_ROOT = PROJECT_ROOT / "data" / "users"
ALLOWED_EXTENSIONS = {
    "video": {".mp4", ".mov", ".m4v"},
    "music": {".mp3", ".wav", ".m4a"},
    "image": {".jpg", ".jpeg", ".png"},
}

# Security validation helpers
def validate_package_name(name: str) -> None:
    """Prevent path traversal attacks in package names."""
    if not isinstance(name, str) or not name.strip():
        raise ValueError("Package name must be non-empty string")
    if "/" in name or "\\" in name or name in {".", ".."}:
        raise ValueError("Invalid package name: contains path separators or reserved names")
    if len(name) > 255:
        raise ValueError("Package name too long (max 255 chars)")


def validate_query_string(value: str, max_length: int = 256) -> str:
    """Validate and sanitize query string parameters."""
    if not isinstance(value, str):
        raise TypeError("Query parameter must be string")
    if len(value) > max_length:
        raise ValueError(f"Query parameter too long (max {max_length} chars)")
    return value.strip()


def validate_json_string(data: str, max_size: int = 1024 * 1024) -> dict:
    """Safely parse JSON with size validation."""
    if not isinstance(data, str):
        raise TypeError("JSON must be string")
    if len(data) > max_size:
        raise ValueError(f"JSON payload too large (max {max_size} bytes)")
    try:
        return json.loads(data)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON: {str(e)[:100]}")


def _read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _metadata_title(path: Path) -> str:
    if not path.exists():
        return ""
    lines = path.read_text(encoding="utf-8").splitlines()
    for index, line in enumerate(lines):
        if line.strip() == "# Title" and index + 1 < len(lines):
            return lines[index + 1].strip()
    return ""


def _music_selection_from_dict(data: dict) -> MusicSelection:
    track = data["track"]
    evidence = track["evidence"]
    return MusicSelection(
        track=MusicTrack(
            track_id=track["track_id"],
            title=track["title"],
            artist=track["artist"],
            duration_seconds=track["duration_seconds"],
            local_path=track["local_path"],
            mood_tags=track.get("mood_tags", []),
            has_vocals=track["has_vocals"],
            strong_beat=track["strong_beat"],
            evidence=LicenseEvidence(
                source_name=evidence["source_name"],
                source_url=evidence["source_url"],
                license_terms=evidence["license_terms"],
                attribution_required=evidence["attribution_required"],
                access_date=evidence["access_date"],
            ),
        ),
        target_gain_db=data["target_gain_db"],
        reason=data.get("reason", ""),
    )


def build_package_summary(package_dir: Path) -> dict:
    publish_plan = _read_json(package_dir / "publish_plan.json")
    upload_report = _read_json(package_dir / "youtube_upload_report.json")
    instagram_report = _read_json(package_dir / "instagram_upload_report.json")
    volume_approval = _read_json(package_dir / "music_volume_approval.json")
    video_id = upload_report.get("youtube_video_id", "")
    instagram_media_id = instagram_report.get("instagram_media_id", "")
    instagram_url = instagram_report.get("permalink", "")
    final_video_ready = (package_dir / "final_video.mp4").exists() and (package_dir / "edit_report.json").exists()
    return {
        "name": package_dir.name,
        "path": str(package_dir),
        "title": publish_plan.get("title", "") or _metadata_title(
            package_dir / "youtube_metadata.md"
        ),
        "privacy_status": publish_plan.get("youtube", {}).get("privacy_status", ""),
        "youtube_video_id": video_id,
        "youtube_url": f"https://youtu.be/{video_id}" if video_id else "",
        "instagram_media_id": instagram_media_id,
        "instagram_url": instagram_url,
        "music_volume_approved": bool(volume_approval.get("approved")),
        "music_gain_db": volume_approval.get("music_gain_db", ""),
        "has_final_video": final_video_ready,
        "has_subtitled_video": (package_dir / "subtitled_video.mp4").exists(),
        "has_thumbnail": (package_dir / "thumbnail.jpg").exists(),
        "instagram_status": "uploaded" if instagram_media_id else publish_plan.get("instagram", {}).get("status", ""),
    }


def list_package_summaries(output_root: Path) -> list[dict]:
    if not output_root.exists():
        return []
    packages = [path for path in output_root.iterdir() if path.is_dir()]
    return [build_package_summary(path) for path in sorted(packages, key=lambda item: item.name, reverse=True)]


def resolve_request_roots(
    query: str,
    shared_input_root: Path,
    shared_output_root: Path,
    shared_config_root: Path,
    multi_user_root: Path | None,
    headers=None,
    public_cloud: bool = False,
    auth_user_header: str = "X-Authenticated-User",
) -> dict:
    if not multi_user_root:
        return {
            "user_id": "",
            "input_root": shared_input_root,
            "output_root": shared_output_root,
            "config_root": shared_config_root,
        }
    user_id = resolve_user_id(
        query=query,
        headers=headers or {},
        public_cloud=public_cloud,
        auth_user_header=auth_user_header,
    )
    paths = build_user_paths(multi_user_root, user_id)
    return {
        "user_id": paths.user_id,
        "input_root": paths.input_root,
        "output_root": paths.output_root,
        "config_root": paths.config_root,
    }


def build_package_path(output_root: Path, package_name: str) -> Path:
    if "/" in package_name or "\\" in package_name or package_name in {"", ".", ".."}:
        raise ValueError("Invalid package name")
    path = output_root / package_name
    if not path.exists() or not path.is_dir():
        raise FileNotFoundError(f"Package not found: {package_name}")
    return path


def sanitize_upload_filename(filename: str) -> str:
    raw_name = filename.replace("\\", "/").split("/")[-1]
    stem = Path(raw_name).stem
    suffix = Path(raw_name).suffix.lower()
    safe_stem = re.sub(r"[^A-Za-z0-9가-힣._-]+", "-", stem).strip("-._")
    return f"{safe_stem or 'uploaded'}{suffix}"


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


def save_imported_asset(input_root: Path, kind: str, filename: str, data: bytes) -> dict:
    if kind not in ALLOWED_EXTENSIONS:
        raise ValueError("kind must be video, image, or music")
    safe_name = sanitize_upload_filename(filename)
    suffix = Path(safe_name).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS[kind]:
        raise ValueError(f"Unsupported {kind} file extension: {suffix}")
    directory = input_root / {"video": "videos", "image": "images", "music": "music"}[kind]
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / safe_name
    if path.exists():
        return {
            "kind": kind,
            "name": path.name,
            "path": str(path),
            "size_bytes": path.stat().st_size,
            "already_exists": True,
        }
    path.write_bytes(data)
    return {"kind": kind, "name": path.name, "path": str(path), "size_bytes": path.stat().st_size}


def list_imported_assets(input_root: Path, kind: str) -> list[dict]:
    if kind not in ALLOWED_EXTENSIONS:
        raise ValueError("kind must be video, image, or music")
    directory = input_root / {"video": "videos", "image": "images", "music": "music"}[kind]
    if not directory.exists():
        return []
    files = [path for path in directory.iterdir() if path.is_file() and path.suffix.lower() in ALLOWED_EXTENSIONS[kind]]
    return [
        {"kind": kind, "name": path.name, "path": str(path), "size_bytes": path.stat().st_size}
        for path in sorted(files, key=lambda item: item.name.lower())
    ]


def delete_imported_asset(input_root: Path, kind: str, name: str) -> None:
    _asset_path(input_root, kind, name).unlink()


def clear_imported_assets(input_root: Path) -> dict:
    removed = {"video": 0, "image": 0, "music": 0}
    for kind in removed:
        directory = input_root / {"video": "videos", "image": "images", "music": "music"}[kind]
        if not directory.exists():
            continue
        for path in directory.iterdir():
            if path.is_file() and path.suffix.lower() in ALLOWED_EXTENSIONS[kind]:
                path.unlink()
                removed[kind] += 1
    return removed


def _asset_path(input_root: Path, kind: str, name: str) -> Path:
    safe_name = sanitize_upload_filename(name)
    path = input_root / {"video": "videos", "image": "images", "music": "music"}[kind] / safe_name
    if not path.exists():
        raise FileNotFoundError(f"Imported {kind} not found: {safe_name}")
    return path


def _user_music_selection(music_path: Path) -> MusicSelection:
    return MusicSelection(
        track=MusicTrack(
            track_id=safe_slug(music_path.stem),
            title=music_path.stem,
            artist="User provided",
            duration_seconds=0,
            local_path=str(music_path),
            mood_tags=["calm", "ambient"],
            has_vocals=False,
            strong_beat=False,
            evidence=LicenseEvidence(
                source_name="User provided",
                source_url="local import",
                license_terms="User must confirm license before posting.",
                attribution_required=False,
                access_date=str(date.today()),
            ),
        ),
        target_gain_db=-18.0,
        reason="Selected by user in dashboard.",
    )


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


def create_work_package(
    input_root: Path,
    output_root: Path,
    media_kind: str,
    media_name: str,
    music_name: str,
    title: str,
    duration_seconds: float | None = None,
    media_items: list[dict] | None = None,
    music_items: list[str] | None = None,
    profile_func=profile_media,
    render_func=render_video,
    render_sequence_func=render_sequence_video,
) -> Path:
    normalized_media_items = media_items or [{"kind": media_kind, "name": media_name}]
    normalized_music_items = music_items or [music_name]
    if not normalized_media_items:
        raise ValueError("media_items is required.")
    if not normalized_music_items:
        raise ValueError("music_items is required.")
    for item in normalized_media_items:
        if item.get("kind") not in {"video", "image"}:
            raise ValueError("media item kind must be video or image")

    media_paths = [
        {
            "kind": item["kind"],
            "name": sanitize_upload_filename(item["name"]),
            "path": _asset_path(input_root, item["kind"], item["name"]),
        }
        for item in normalized_media_items
    ]
    music_paths = [_asset_path(input_root, "music", name) for name in normalized_music_items]
    first_media = media_paths[0]
    media_kind = first_media["kind"]
    media_name = first_media["name"]
    media_path = first_media["path"]
    clean_title = title.strip() or "힐링되는 새소리"
    output_dir = _unique_output_dir(output_root, f"{date.today().isoformat()}-{safe_slug(Path(media_name).stem)}")
    output_dir.mkdir(parents=True, exist_ok=True)

    asset = SourceAsset(
        source_path=str(media_path),
        owned_by_user=True,
        shooting_date=str(date.today()),
        general_location="user import",
        privacy_notes="pending user review",
    )
    requested_duration = float(duration_seconds or 0)
    if requested_duration <= 0:
        requested_duration = 30.0 if media_kind == "image" else 0.0
    if media_kind == "video":
        base_profile = profile_func(media_path)
        profile = MediaProfile(
            source_path=base_profile.source_path,
            duration_seconds=requested_duration or base_profile.duration_seconds,
            width=base_profile.width,
            height=base_profile.height,
            video_codec=base_profile.video_codec,
            audio_codec=base_profile.audio_codec,
            frame_rate=base_profile.frame_rate,
            has_audio=base_profile.has_audio,
            orientation=base_profile.orientation,
            youtube_format=base_profile.youtube_format,
        )
    else:
        profile = MediaProfile(
            source_path=str(media_path),
            duration_seconds=requested_duration,
            width=1080,
            height=1920,
            video_codec="image",
            audio_codec="none",
            frame_rate=30,
            has_audio=False,
            orientation="vertical",
            youtube_format="shorts",
        )
    music_selections = [_user_music_selection(path) for path in music_paths]
    selection = music_selections[0]
    final_video = output_dir / "final_video.mp4"
    thumbnail = output_dir / "thumbnail.jpg"
    if len(media_paths) > 1 or len(music_selections) > 1:
        report = render_sequence_func(
            media_items=[{"kind": item["kind"], "name": item["name"], "path": item["path"]} for item in media_paths],
            music_selections=music_selections,
            output_video=final_video,
            thumbnail_path=thumbnail,
            duration_seconds=profile.duration_seconds,
        )
    elif media_kind == "image" and render_func is render_video:
        report = render_image_video(
            source_image=media_path,
            music_selection=selection,
            output_video=final_video,
            thumbnail_path=thumbnail,
            duration_seconds=profile.duration_seconds,
        )
    else:
        report = render_func(
            source_video=media_path,
            music_selection=selection,
            output_video=final_video,
            thumbnail_path=thumbnail,
            duration_seconds=profile.duration_seconds,
        )
    write_json(
        output_dir / "edit_sequence.json",
        {
            "media_items": [
                {"kind": item["kind"], "name": item["name"], "path": str(item["path"])}
                for item in media_paths
            ],
            "music_items": [path.name for path in music_paths],
            "music_paths": [str(path) for path in music_paths],
            "duration_seconds": profile.duration_seconds,
        },
    )
    write_json(output_dir / "asset_manifest.json", asset)
    write_json(output_dir / "media_profile.json", profile)
    write_json(output_dir / "music_selection.json", selection)
    write_json(output_dir / "license_log.json", selection.track.evidence)
    write_json(output_dir / "edit_report.json", report)
    write_metadata_file(
        output_dir / "youtube_metadata.md",
        build_youtube_metadata(asset=asset, profile=profile, music_selection=selection, bilingual=False),
    )
    write_approval_checklist(output_dir / "approval_checklist.md", [])
    write_json(
        output_dir / "publish_plan.json",
        {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "package_dir": str(output_dir),
            "video_path": str(final_video),
            "title": clean_title,
            "description": "",
            "youtube": {"status": "draft", "privacy_status": "unlisted"},
            "instagram": {"status": "waiting_for_public_video_url", "media_type": "REELS", "video_url": ""},
        },
    )
    return output_dir


def parse_multipart_upload_file(content_type: str, body: bytes) -> tuple[str, bytes]:
    message = BytesParser(policy=default).parsebytes(
        f"Content-Type: {content_type}\r\nMIME-Version: 1.0\r\n\r\n".encode("utf-8") + body
    )
    if not message.is_multipart():
        raise ValueError("Expected multipart form upload")
    for part in message.iter_parts():
        if part.get_param("name", header="content-disposition") == "file":
            filename = part.get_filename()
            if not filename:
                break
            return filename, part.get_payload(decode=True) or b""
    raise ValueError("Missing upload file")


class DashboardHandler(SimpleHTTPRequestHandler):
    output_root = PROJECT_ROOT / "outputs" / "youtube-healing"
    input_root = INPUT_ROOT
    config_root = CONFIG_ROOT
    multi_user_root = None
    public_cloud = False
    auth_user_header = "X-Authenticated-User"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEB_ROOT), **kwargs)

    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def _send_error_json(self, code: int, message: str, details: str = "") -> None:
        response = {
            "error": message,
            "code": code,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        if details:
            response["details"] = details
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(json.dumps(response).encode("utf-8"))

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path
        try:
            roots = self._request_roots(parsed.query)
        except AuthError as exc:
            self.send_error(401, str(exc))
            return
        if path == "/api/health":
            self._send_json({"status": "ok", "multi_user": bool(self.multi_user_root)})
            return
        if path == "/api/packages":
            self._send_json({"user_id": roots["user_id"], "packages": list_package_summaries(roots["output_root"])})
            return
        if path == "/api/assets":
            self._send_json(
                {
                    "user_id": roots["user_id"],
                    "videos": list_imported_assets(roots["input_root"], "video"),
                    "images": list_imported_assets(roots["input_root"], "image"),
                    "music": list_imported_assets(roots["input_root"], "music"),
                }
            )
            return
        if path == "/api/turbo/status":
            self._send_json(moneyprinter_status(default_turbo_output_dir(PROJECT_ROOT)))
            return
        if path == "/api/turbo/engine-status":
            self._send_json(
                moneyprinter_engine_status(
                    root=default_turbo_root(PROJECT_ROOT),
                    output_dir=default_turbo_output_dir(PROJECT_ROOT),
                    command_template=default_turbo_command_template(),
                )
            )
            return
        if path == "/api/instagram/status":
            self._send_json(instagram_token_status(roots["config_root"]))
            return
        if path == "/api/instagram/auth-url":
            self._handle_instagram_auth_url(roots)
            return
        if path == "/api/instagram/callback":
            self._handle_instagram_callback(parsed.query)
            return
        if path == "/api/package-file":
            self._handle_package_file(parsed.query, roots["output_root"])
            return
        if path == "/":
            self.path = "/index.html"
        super().do_GET()

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path
        try:
            roots = self._request_roots(parsed.query)
        except AuthError as exc:
            self.send_error(401, str(exc))
            return
        if path == "/api/import/video":
            self._handle_import("video", roots["input_root"])
            return
        if path == "/api/import/image":
            self._handle_import("image", roots["input_root"])
            return
        if path == "/api/import/music":
            self._handle_import("music", roots["input_root"])
            return
        if path == "/api/assets/delete":
            self._handle_asset_delete(roots["input_root"])
            return
        if path == "/api/assets/clear":
            self._handle_assets_clear(roots["input_root"])
            return
        if path == "/api/packages/create":
            self._handle_package_create(roots["input_root"], roots["output_root"])
            return
        if path == "/api/turbo/import":
            self._handle_turbo_import(roots["input_root"])
            return
        if path == "/api/turbo/run":
            self._handle_turbo_run()
            return
        if path == "/api/subtitles/render":
            self._handle_subtitle_render(roots["output_root"])
            return
        if path == "/api/instagram/upload":
            self._handle_instagram_upload(roots)
            return
        if path == "/api/music-volume/preview":
            self._handle_music_volume_preview(roots["output_root"])
            return
        if path == "/api/music-volume/approve":
            self._handle_music_volume_approve(roots["output_root"])
            return
        self.send_error(404)

    def _request_roots(self, query: str) -> dict:
        return resolve_request_roots(
            query=query,
            shared_input_root=self.input_root,
            shared_output_root=self.output_root,
            shared_config_root=self.config_root,
            multi_user_root=self.multi_user_root,
            headers=self.headers,
            public_cloud=self.public_cloud,
            auth_user_header=self.auth_user_header,
        )

    def _instagram_oauth_env(self) -> tuple[str, str, str]:
        app_id = os.environ.get("INSTAGRAM_APP_ID", "").strip()
        app_secret = os.environ.get("INSTAGRAM_APP_SECRET", "").strip()
        redirect_uri = os.environ.get("INSTAGRAM_REDIRECT_URI", "").strip()
        if not redirect_uri:
            host = self.headers.get("Host", "127.0.0.1:8787")
            redirect_uri = f"http://{host}/api/instagram/callback"
        if not app_id:
            raise ValueError("INSTAGRAM_APP_ID is required.")
        return app_id, app_secret, redirect_uri

    def _handle_instagram_auth_url(self, roots: dict) -> None:
        try:
            app_id, _app_secret, redirect_uri = self._instagram_oauth_env()
            url, state = build_instagram_login_url(
                config_root=roots["config_root"],
                user_id=roots["user_id"] or "local",
                app_id=app_id,
                redirect_uri=redirect_uri,
            )
        except ValueError as exc:
            self.send_error(400, str(exc))
            return
        self._send_json({"auth_url": url, "state": state, "redirect_uri": redirect_uri})

    def _roots_from_instagram_state(self, state: str) -> dict:
        user_id = state.split(".", 1)[0]
        if self.multi_user_root:
            paths = build_user_paths(self.multi_user_root, user_id)
            return {
                "user_id": paths.user_id,
                "input_root": paths.input_root,
                "output_root": paths.output_root,
                "config_root": paths.config_root,
            }
        return {"user_id": "", "input_root": self.input_root, "output_root": self.output_root, "config_root": self.config_root}

    def _handle_instagram_callback(self, query: str) -> None:
        from urllib.parse import parse_qs

        params = parse_qs(query)
        code = params.get("code", [""])[0]
        state = params.get("state", [""])[0]
        if not code or not state:
            self.send_error(400, "Missing Instagram OAuth code or state.")
            return
        try:
            roots = self._roots_from_instagram_state(state)
            validate_instagram_state(roots["config_root"], state)
            app_id, app_secret, redirect_uri = self._instagram_oauth_env()
            if not app_secret:
                raise ValueError("INSTAGRAM_APP_SECRET is required for callback.")
            token = exchange_code_for_instagram_token(
                config_root=roots["config_root"],
                code=code,
                app_id=app_id,
                app_secret=app_secret,
                redirect_uri=redirect_uri,
            )
        except (ValueError, RuntimeError, FileNotFoundError) as exc:
            self.send_error(400, str(exc))
            return
        body = (
            "<!doctype html><html><body>"
            "<h1>Instagram 연결 완료</h1>"
            f"<p>계정: {token.get('instagram_username') or token.get('instagram_user_id')}</p>"
            "<p>이 창을 닫고 YouTube Bird Studio로 돌아가세요.</p>"
            "</body></html>"
        ).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _handle_import(self, kind: str, input_root: Path) -> None:
        try:
            length = int(self.headers.get("Content-Length", "0"))
            filename, data = parse_multipart_upload_file(
                self.headers.get("Content-Type", ""),
                self.rfile.read(length),
            )
            asset = save_imported_asset(input_root, kind, filename, data)
        except ValueError as exc:
            self.send_error(400, str(exc))
            return
        self._send_json({"asset": asset})

    def _handle_asset_delete(self, input_root: Path) -> None:
        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            delete_imported_asset(input_root, payload.get("kind", ""), payload.get("name", ""))
        except (ValueError, FileNotFoundError, KeyError, json.JSONDecodeError) as exc:
            self.send_error(400, str(exc))
            return
        self._send_json({"status": "deleted"})

    def _handle_assets_clear(self, input_root: Path) -> None:
        self._send_json({"removed": clear_imported_assets(input_root)})

    def _handle_package_create(self, input_root: Path, output_root: Path) -> None:
        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            package_dir = create_work_package(
                input_root=input_root,
                output_root=output_root,
                media_kind=payload.get("media_kind", ""),
                media_name=payload.get("media_name", ""),
                music_name=payload.get("music_name", ""),
                title=payload.get("title", "힐링되는 새소리"),
                duration_seconds=payload.get("duration_seconds"),
                media_items=payload.get("media_items"),
                music_items=payload.get("music_items"),
            )
        except (ValueError, FileNotFoundError, json.JSONDecodeError, KeyError) as exc:
            self.send_error(400, str(exc))
            return
        self._send_json({"package": build_package_summary(package_dir)})

    def _handle_turbo_import(self, input_root: Path) -> None:
        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            asset = import_turbo_video(
                output_dir=default_turbo_output_dir(PROJECT_ROOT),
                input_root=input_root,
                video_name=payload.get("video_name", ""),
            )
        except (ValueError, FileNotFoundError, json.JSONDecodeError) as exc:
            self.send_error(400, str(exc))
            return
        self._send_json({"asset": asset})

    def _handle_turbo_run(self) -> None:
        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            report = run_moneyprinter_engine(
                root=default_turbo_root(PROJECT_ROOT),
                output_dir=default_turbo_output_dir(PROJECT_ROOT),
                topic=payload.get("topic", ""),
                command_template=default_turbo_command_template(),
            )
        except (ValueError, RuntimeError, FileNotFoundError, json.JSONDecodeError) as exc:
            self.send_error(400, str(exc))
            return
        self._send_json({"report": report})

    def _package_render_inputs(self, output_root: Path, package_name: str) -> tuple[Path, Path, MusicSelection, float]:
        package_dir = build_package_path(output_root, package_name)
        asset = _read_json(package_dir / "asset_manifest.json")
        profile = _read_json(package_dir / "media_profile.json")
        selection = _read_json(package_dir / "music_selection.json")
        if not asset or not profile or not selection:
            raise FileNotFoundError("Package render metadata is missing.")
        return (
            package_dir,
            Path(asset["source_path"]).expanduser(),
            _music_selection_from_dict(selection),
            float(profile["duration_seconds"]),
        )

    def _render_package_video(
        self,
        package_dir: Path,
        source_video: Path,
        selection: MusicSelection,
        output_video: Path,
        thumbnail_path: Path,
        duration_seconds: float,
        music_gain_db: float,
    ):
        sequence = _read_json(package_dir / "edit_sequence.json")
        media_items = sequence.get("media_items", [])
        music_paths = sequence.get("music_paths", [])
        if len(media_items) > 1 or len(music_paths) > 1:
            return render_sequence_video(
                media_items=[
                    {"kind": item["kind"], "path": Path(item["path"]).expanduser()}
                    for item in media_items
                ],
                music_selections=[_user_music_selection(Path(path).expanduser()) for path in music_paths],
                output_video=output_video,
                thumbnail_path=thumbnail_path,
                duration_seconds=duration_seconds,
                music_gain_db=music_gain_db,
            )
        if media_items and media_items[0].get("kind") == "image":
            return render_image_video(
                source_image=Path(media_items[0]["path"]).expanduser(),
                music_selection=selection,
                output_video=output_video,
                thumbnail_path=thumbnail_path,
                duration_seconds=duration_seconds,
                music_gain_db=music_gain_db,
            )
        return render_video(
            source_video=source_video,
            music_selection=selection,
            output_video=output_video,
            thumbnail_path=thumbnail_path,
            duration_seconds=duration_seconds,
            music_gain_db=music_gain_db,
        )

    def _handle_music_volume_preview(self, output_root: Path) -> None:
        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            gain_db = float(payload.get("music_gain_db"))
            package_dir, source_video, selection, duration_seconds = self._package_render_inputs(
                output_root,
                payload.get("package_name", ""),
            )
            preview_duration = min(duration_seconds, 20.0)
            preview_path = package_dir / "volume_preview.mp4"
            thumbnail_path = package_dir / "volume_preview.jpg"
            report = self._render_package_video(
                package_dir=package_dir,
                source_video=source_video,
                output_video=preview_path,
                thumbnail_path=thumbnail_path,
                duration_seconds=preview_duration,
                music_gain_db=gain_db,
                selection=selection,
            )
            report_payload = {
                "music_gain_db": gain_db,
                "preview_video": str(preview_path),
                "preview_url": f"/api/package-file?package_name={package_dir.name}&file=volume_preview.mp4",
                "render_report": to_jsonable(report),
            }
            write_json(package_dir / "music_volume_preview.json", report_payload)
        except (ValueError, FileNotFoundError, json.JSONDecodeError, KeyError) as exc:
            self.send_error(400, str(exc))
            return
        self._send_json(report_payload)

    def _handle_music_volume_approve(self, output_root: Path) -> None:
        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            gain_db = float(payload.get("music_gain_db"))
            package_dir, source_video, selection, duration_seconds = self._package_render_inputs(
                output_root,
                payload.get("package_name", ""),
            )
            report = self._render_package_video(
                package_dir=package_dir,
                source_video=source_video,
                output_video=package_dir / "final_video.mp4",
                thumbnail_path=package_dir / "thumbnail.jpg",
                duration_seconds=duration_seconds,
                music_gain_db=gain_db,
                selection=selection,
            )
            approval = {
                "approved": True,
                "music_gain_db": gain_db,
                "final_video": str(package_dir / "final_video.mp4"),
                "render_report": to_jsonable(report),
            }
            write_json(package_dir / "music_volume_approval.json", approval)
            write_json(package_dir / "edit_report.json", report)
        except (ValueError, FileNotFoundError, json.JSONDecodeError, KeyError) as exc:
            self.send_error(400, str(exc))
            return
        self._send_json({"approval": approval})

    def _handle_subtitle_render(self, output_root: Path) -> None:
        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            package_dir = build_package_path(output_root, payload.get("package_name", ""))
            input_video = package_dir / "final_video.mp4"
            if not input_video.exists() or not (package_dir / "edit_report.json").exists():
                raise FileNotFoundError("final_video.mp4 is not ready yet")
            output_video = package_dir / "subtitled_video.mp4"
            report = render_subtitled_video(
                input_video=input_video,
                output_video=output_video,
                settings=payload.get("settings", {}),
            )
        except (ValueError, FileNotFoundError, json.JSONDecodeError, subprocess.CalledProcessError) as exc:
            self.send_error(400, str(exc))
            return
        self._send_json({"report": report})

    def _handle_package_file(self, query: str, output_root: Path) -> None:
        from urllib.parse import parse_qs

        params = parse_qs(query)
        package_name = params.get("package_name", [""])[0]
        filename = params.get("file", [""])[0]
        if filename not in {"volume_preview.mp4", "final_video.mp4", "subtitled_video.mp4"}:
            self.send_error(400, "Unsupported package file.")
            return
        try:
            package_dir = build_package_path(output_root, package_name)
        except (ValueError, FileNotFoundError) as exc:
            self.send_error(400, str(exc))
            return
        file_path = package_dir / filename
        if not file_path.exists():
            self.send_error(404, "Package file not found.")
            return
        self.send_response(200)
        self.send_header("Content-Type", "video/mp4")
        self.send_header("Content-Length", str(file_path.stat().st_size))
        self.end_headers()
        with file_path.open("rb") as handle:
            self.wfile.write(handle.read())

    def _handle_instagram_upload(self, roots: dict) -> None:
        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            package_dir = build_package_path(roots["output_root"], payload.get("package_name", ""))
            plan_path = package_dir / "publish_plan.json"
            if not plan_path.exists():
                raise FileNotFoundError("publish_plan.json not found")
            token_data = load_instagram_token(roots["config_root"])
            report = upload_instagram_from_plan(plan_path, token_data=token_data)
            report_path = package_dir / "instagram_upload_report.json"
            report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        except (ValueError, FileNotFoundError, json.JSONDecodeError, RuntimeError, TimeoutError) as exc:
            self.send_error(400, str(exc))
            return
        self._send_json({"report": report})

    def _send_json(self, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the local cross-platform YouTube healing dashboard.")
    parser.add_argument("--host", default="127.0.0.1", help="Bind host. Use 0.0.0.0 for phone access on LAN.")
    parser.add_argument("--port", type=int, default=8787, help="Dashboard port.")
    parser.add_argument("--output-root", default=str(PROJECT_ROOT / "outputs" / "youtube-healing"))
    parser.add_argument("--input-root", default=str(INPUT_ROOT))
    parser.add_argument(
        "--multi-user-root",
        help="Enable user_id-scoped mobile workspaces under this root. Example: data/users",
    )
    parser.add_argument(
        "--public-cloud",
        action="store_true",
        help="Require HTTPS base URL, real auth mode, and session secret before starting.",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    try:
        cloud_config = load_cloud_config(public_cloud=args.public_cloud)
    except CloudConfigError as exc:
        raise SystemExit(f"Cloud configuration error: {exc}") from exc
    DashboardHandler.output_root = Path(args.output_root).expanduser()
    DashboardHandler.input_root = Path(args.input_root).expanduser()
    DashboardHandler.config_root = CONFIG_ROOT
    DashboardHandler.multi_user_root = Path(args.multi_user_root).expanduser() if args.multi_user_root else None
    DashboardHandler.public_cloud = cloud_config.public_cloud
    DashboardHandler.auth_user_header = cloud_config.auth_user_header
    server = ThreadingHTTPServer((args.host, args.port), DashboardHandler)
    print(f"Dashboard: http://{args.host}:{args.port}/")
    print("Press Ctrl+C to stop.")
    server.serve_forever()


if __name__ == "__main__":
    main()
