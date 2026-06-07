from __future__ import annotations

import json
import os
import secrets
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen


GRAPH_VERSION = os.environ.get("INSTAGRAM_GRAPH_API_VERSION", "v25.0")
DEFAULT_SCOPES = [
    "instagram_basic",
    "instagram_content_publish",
    "pages_show_list",
    "pages_read_engagement",
]


def instagram_token_path(config_root: Path) -> Path:
    return config_root / "instagram_token.json"


def instagram_state_path(config_root: Path) -> Path:
    return config_root / "instagram_oauth_state.json"


def _graph_url(path: str, graph_version: str = GRAPH_VERSION) -> str:
    return f"https://graph.facebook.com/{graph_version}/{path.lstrip('/')}"


def _get_json(url: str) -> dict:
    with urlopen(url, timeout=120) as response:
        return json.loads(response.read().decode("utf-8"))


def build_instagram_login_url(
    config_root: Path,
    user_id: str,
    app_id: str,
    redirect_uri: str,
    nonce: str | None = None,
    scopes: list[str] | None = None,
    graph_version: str = GRAPH_VERSION,
) -> tuple[str, str]:
    clean_nonce = nonce or secrets.token_urlsafe(18)
    state = f"{user_id}.{clean_nonce}"
    config_root.mkdir(parents=True, exist_ok=True)
    instagram_state_path(config_root).write_text(
        json.dumps({"state": state, "created_at": datetime.now(timezone.utc).isoformat()}, indent=2) + "\n",
        encoding="utf-8",
    )
    query = urlencode(
        {
            "client_id": app_id,
            "redirect_uri": redirect_uri,
            "state": state,
            "scope": ",".join(scopes or DEFAULT_SCOPES),
            "response_type": "code",
        }
    )
    return f"https://www.facebook.com/{graph_version}/dialog/oauth?{query}", state


def validate_instagram_state(config_root: Path, state: str) -> None:
    saved = json.loads(instagram_state_path(config_root).read_text(encoding="utf-8"))
    if saved.get("state") != state:
        raise ValueError("Invalid Instagram OAuth state.")


def save_instagram_token(config_root: Path, token: dict) -> Path:
    config_root.mkdir(parents=True, exist_ok=True)
    clean = {
        "access_token": token["access_token"],
        "instagram_user_id": token["instagram_user_id"],
        "instagram_username": token.get("instagram_username", ""),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    path = instagram_token_path(config_root)
    path.write_text(json.dumps(clean, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def load_instagram_token(config_root: Path) -> dict:
    return json.loads(instagram_token_path(config_root).read_text(encoding="utf-8"))


def instagram_token_status(config_root: Path) -> dict:
    path = instagram_token_path(config_root)
    if not path.exists():
        return {"connected": False, "instagram_user_id": "", "instagram_username": ""}
    token = load_instagram_token(config_root)
    return {
        "connected": True,
        "instagram_user_id": token.get("instagram_user_id", ""),
        "instagram_username": token.get("instagram_username", ""),
        "created_at": token.get("created_at", ""),
    }


def _select_instagram_account(accounts_response: dict) -> dict:
    for page in accounts_response.get("data", []):
        account = page.get("instagram_business_account") or {}
        if account.get("id"):
            return account
    raise ValueError("No Instagram Business/Creator account found for this login.")


def exchange_code_for_instagram_token(
    config_root: Path,
    code: str,
    app_id: str,
    app_secret: str,
    redirect_uri: str,
    graph_version: str = GRAPH_VERSION,
    http_get=_get_json,
) -> dict:
    token_query = urlencode(
        {
            "client_id": app_id,
            "redirect_uri": redirect_uri,
            "client_secret": app_secret,
            "code": code,
        }
    )
    token = http_get(f"{_graph_url('oauth/access_token', graph_version)}?{token_query}")
    access_token = token.get("access_token", "")
    if not access_token:
        raise RuntimeError(f"Instagram OAuth token exchange failed: {token}")
    accounts_query = urlencode(
        {
            "fields": "instagram_business_account{id,username}",
            "access_token": access_token,
        }
    )
    account = _select_instagram_account(http_get(f"{_graph_url('me/accounts', graph_version)}?{accounts_query}"))
    saved = {
        "access_token": access_token,
        "instagram_user_id": account["id"],
        "instagram_username": account.get("username", ""),
    }
    save_instagram_token(config_root, saved)
    return saved
