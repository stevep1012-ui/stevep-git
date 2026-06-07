from __future__ import annotations

import argparse
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

YOUTUBE_UPLOAD_SCOPE = "https://www.googleapis.com/auth/youtube.upload"
INSTAGRAM_GRAPH_API_VERSION = os.environ.get("INSTAGRAM_GRAPH_API_VERSION", "v25.0")


def _section(markdown: str, heading: str) -> str:
    marker = f"# {heading}"
    if marker not in markdown:
        return ""
    after = markdown.split(marker, 1)[1]
    next_heading = after.find("\n# ")
    if next_heading >= 0:
        after = after[:next_heading]
    return after.strip()


def _description_from_metadata(metadata_path: Path) -> str:
    markdown = metadata_path.read_text(encoding="utf-8")
    parts = [
        _section(markdown, "Description"),
        _section(markdown, "Hashtags"),
        _section(markdown, "Music Attribution"),
    ]
    return "\n\n".join(part for part in parts if part)


def build_publish_plan(
    package_dir: Path,
    title: str,
    privacy_status: str = "unlisted",
) -> dict:
    clean_title = title.strip()
    if not clean_title:
        raise ValueError("Title is required before publishing.")
    if privacy_status not in {"private", "unlisted", "public"}:
        raise ValueError("privacy_status must be private, unlisted, or public.")

    package_dir = package_dir.expanduser()
    if not package_dir.is_absolute():
        package_dir = package_dir.resolve()
    video_path = package_dir / "final_video.mp4"
    metadata_path = package_dir / "youtube_metadata.md"
    if not video_path.exists():
        raise FileNotFoundError(f"Missing final video: {video_path}")
    if not metadata_path.exists():
        raise FileNotFoundError(f"Missing YouTube metadata: {metadata_path}")

    instagram_video_url = os.environ.get("INSTAGRAM_VIDEO_URL", "").strip()
    instagram_token = os.environ.get("INSTAGRAM_ACCESS_TOKEN", "").strip()
    instagram_user_id = os.environ.get("INSTAGRAM_USER_ID", "").strip()
    instagram_ready = bool(instagram_video_url and instagram_token and instagram_user_id)

    return {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "package_dir": str(package_dir),
        "video_path": str(video_path),
        "title": clean_title,
        "description": _description_from_metadata(metadata_path),
        "youtube": {
            "status": "ready",
            "privacy_status": privacy_status,
            "required_env": ["YOUTUBE_CLIENT_SECRET_FILE", "YOUTUBE_TOKEN_FILE"],
        },
        "instagram": {
            "status": "ready" if instagram_ready else "waiting_for_public_video_url",
            "media_type": "REELS",
            "video_url": instagram_video_url,
            "required_env": ["INSTAGRAM_ACCESS_TOKEN", "INSTAGRAM_USER_ID", "INSTAGRAM_VIDEO_URL"],
        },
    }


def build_youtube_upload_body(plan: dict) -> dict:
    return {
        "snippet": {
            "title": plan["title"],
            "description": plan.get("description", ""),
            "categoryId": "22",
        },
        "status": {
            "privacyStatus": plan["youtube"]["privacy_status"],
            "selfDeclaredMadeForKids": False,
        },
    }


def build_instagram_container_payload(plan: dict) -> dict:
    video_url = plan.get("instagram", {}).get("video_url", "").strip() or os.environ.get("INSTAGRAM_VIDEO_URL", "").strip()
    if not video_url:
        raise ValueError("INSTAGRAM_VIDEO_URL is required for Instagram Reels publishing.")
    caption = f"{plan['title']}\n\n{plan.get('description', '')}".strip()
    return {
        "media_type": "REELS",
        "video_url": video_url,
        "caption": caption,
    }


def write_publish_plan(package_dir: Path, plan: dict) -> Path:
    path = package_dir / "publish_plan.json"
    path.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def load_publish_plan(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def assert_music_volume_approved(plan_path: Path) -> dict:
    plan = load_publish_plan(plan_path)
    package_dir = Path(plan.get("package_dir") or plan_path.parent).expanduser()
    approval_path = package_dir / "music_volume_approval.json"
    if not approval_path.exists():
        raise PermissionError("Background music volume must be previewed and approved before posting.")
    approval = json.loads(approval_path.read_text(encoding="utf-8"))
    if not approval.get("approved"):
        raise PermissionError("Background music volume approval is not complete.")
    return approval


def _instagram_url(path: str, graph_version: str = INSTAGRAM_GRAPH_API_VERSION) -> str:
    return f"https://graph.facebook.com/{graph_version}/{path.lstrip('/')}"


def _post_form(url: str, payload: dict) -> dict:
    data = urlencode(payload).encode("utf-8")
    request = Request(url, data=data, method="POST")
    request.add_header("Content-Type", "application/x-www-form-urlencoded")
    with urlopen(request, timeout=120) as response:
        return json.loads(response.read().decode("utf-8"))


def _get_json(url: str) -> dict:
    with urlopen(url, timeout=120) as response:
        return json.loads(response.read().decode("utf-8"))


def upload_instagram_from_plan(
    plan_path: Path,
    access_token: str | None = None,
    instagram_user_id: str | None = None,
    token_data: dict | None = None,
    graph_version: str | None = None,
    max_attempts: int = 20,
    poll_seconds: int = 5,
    http_post=_post_form,
    http_get=_get_json,
    sleep=time.sleep,
) -> dict:
    token_source = token_data or {}
    token = (access_token or token_source.get("access_token", "") or os.environ.get("INSTAGRAM_ACCESS_TOKEN", "")).strip()
    user_id = (
        instagram_user_id
        or token_source.get("instagram_user_id", "")
        or os.environ.get("INSTAGRAM_USER_ID", "")
    ).strip()
    version = (graph_version or os.environ.get("INSTAGRAM_GRAPH_API_VERSION", INSTAGRAM_GRAPH_API_VERSION)).strip()
    if not token:
        raise ValueError("INSTAGRAM_ACCESS_TOKEN is required for Instagram publishing.")
    if not user_id:
        raise ValueError("INSTAGRAM_USER_ID is required for Instagram publishing.")

    assert_music_volume_approved(plan_path)
    plan = load_publish_plan(plan_path)
    container_payload = build_instagram_container_payload(plan)
    container_payload["access_token"] = token
    container_response = http_post(_instagram_url(f"{user_id}/media", version), container_payload)
    container_id = container_response.get("id")
    if not container_id:
        raise RuntimeError(f"Instagram container creation failed: {container_response}")

    status_response = {}
    for attempt in range(max_attempts):
        query = urlencode({"fields": "status_code", "access_token": token})
        status_response = http_get(f"{_instagram_url(container_id, version)}?{query}")
        status = status_response.get("status_code")
        if status == "FINISHED":
            break
        if status == "ERROR":
            raise RuntimeError(f"Instagram container processing failed: {status_response}")
        if attempt < max_attempts - 1:
            sleep(poll_seconds)
    else:
        raise TimeoutError(f"Instagram container was not ready: {status_response}")

    publish_payload = {"creation_id": container_id, "access_token": token}
    publish_response = http_post(_instagram_url(f"{user_id}/media_publish", version), publish_payload)
    return {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "instagram_container_id": container_id,
        "instagram_media_id": publish_response.get("id"),
        "permalink": publish_response.get("permalink", ""),
        "container_response": container_response,
        "container_status": status_response,
        "publish_response": publish_response,
        "media_type": "REELS",
    }


def check_youtube_oauth_inputs(client_secret_file: Path, token_file: Path) -> None:
    client_secret_file = client_secret_file.expanduser()
    token_file = token_file.expanduser()
    if not client_secret_file.exists():
        raise FileNotFoundError(f"Missing YouTube OAuth client secret file: {client_secret_file}")
    token_file.parent.mkdir(parents=True, exist_ok=True)


def authorize_youtube(client_secret_file: Path, token_file: Path):
    check_youtube_oauth_inputs(client_secret_file, token_file)
    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
    except ImportError as exc:
        raise RuntimeError(
            "Missing Google OAuth dependency. Install google-auth-oauthlib first."
        ) from exc

    flow = InstalledAppFlow.from_client_secrets_file(
        str(client_secret_file),
        scopes=[YOUTUBE_UPLOAD_SCOPE],
    )
    credentials = flow.run_local_server(port=0)
    token_file.write_text(credentials.to_json(), encoding="utf-8")
    return credentials


def upload_youtube_from_plan(plan_path: Path, client_secret_file: Path, token_file: Path) -> dict:
    check_youtube_oauth_inputs(client_secret_file, token_file)
    try:
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload
    except ImportError as exc:
        raise RuntimeError(
            "Missing Google API dependency. Install google-api-python-client and google-auth-oauthlib first."
        ) from exc

    assert_music_volume_approved(plan_path)
    plan = load_publish_plan(plan_path)
    credentials = Credentials.from_authorized_user_file(str(token_file), scopes=[YOUTUBE_UPLOAD_SCOPE])
    youtube = build("youtube", "v3", credentials=credentials)
    media = MediaFileUpload(plan["video_path"], chunksize=-1, resumable=True, mimetype="video/mp4")
    request = youtube.videos().insert(
        part="snippet,status",
        body=build_youtube_upload_body(plan),
        media_body=media,
    )
    response = request.execute()
    return {
        "youtube_video_id": response.get("id"),
        "youtube_response": response,
        "privacy_status_requested": plan["youtube"]["privacy_status"],
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Prepare or publish an upload-ready video package.")
    parser.add_argument("--package-dir", help="Output package folder containing final_video.mp4")
    parser.add_argument("--title", help="Posting title. If omitted, prompt before creating the plan.")
    parser.add_argument(
        "--privacy-status",
        default="unlisted",
        choices=["private", "unlisted", "public"],
        help="YouTube privacy status. Default: unlisted",
    )
    parser.add_argument("--authorize-youtube", action="store_true", help="Create or refresh YouTube OAuth token.")
    parser.add_argument("--upload-youtube", action="store_true", help="Upload the package to YouTube.")
    parser.add_argument("--upload-instagram", action="store_true", help="Upload the package to Instagram Reels.")
    parser.add_argument("--client-secret-file", help="Google OAuth client secret JSON file.")
    parser.add_argument("--token-file", help="YouTube OAuth token JSON output file.")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    client_secret = Path(args.client_secret_file).expanduser() if args.client_secret_file else None
    token_file = Path(args.token_file).expanduser() if args.token_file else None
    if args.authorize_youtube and not args.package_dir and not args.upload_youtube:
        if not client_secret or not token_file:
            raise SystemExit("--client-secret-file and --token-file are required for --authorize-youtube")
        authorize_youtube(client_secret, token_file)
        print(f"YouTube token written: {token_file}")
        return
    if not args.package_dir:
        raise SystemExit("--package-dir is required unless only --authorize-youtube is used")

    title = args.title or input("YouTube 제목을 입력하세요: ")
    package_dir = Path(args.package_dir).expanduser()
    if not package_dir.is_absolute():
        package_dir = package_dir.resolve()
    plan = build_publish_plan(package_dir, title=title, privacy_status=args.privacy_status)
    path = write_publish_plan(package_dir, plan)
    print(f"Publish plan written: {path}")
    print(f"YouTube privacy: {plan['youtube']['privacy_status']}")
    print(f"Instagram status: {plan['instagram']['status']}")

    if args.authorize_youtube:
        if not client_secret or not token_file:
            raise SystemExit("--client-secret-file and --token-file are required for --authorize-youtube")
        authorize_youtube(client_secret, token_file)
        print(f"YouTube token written: {token_file}")
    if args.upload_youtube:
        if not client_secret or not token_file:
            raise SystemExit("--client-secret-file and --token-file are required for --upload-youtube")
        report = upload_youtube_from_plan(path, client_secret, token_file)
        report_path = package_dir / "youtube_upload_report.json"
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"YouTube upload report written: {report_path}")
    if args.upload_instagram:
        report = upload_instagram_from_plan(path)
        report_path = package_dir / "instagram_upload_report.json"
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"Instagram upload report written: {report_path}")


if __name__ == "__main__":
    main()
