from __future__ import annotations

import os
from dataclasses import dataclass


class CloudConfigError(ValueError):
    pass


@dataclass(frozen=True)
class CloudConfig:
    public_cloud: bool
    app_base_url: str
    auth_mode: str
    session_secret: str
    auth_user_header: str


def load_cloud_config(public_cloud: bool) -> CloudConfig:
    app_base_url = os.environ.get("APP_BASE_URL", "").strip()
    auth_mode = os.environ.get("AUTH_MODE", "local").strip().lower()
    session_secret = os.environ.get("SESSION_SECRET", "").strip()
    auth_user_header = os.environ.get("AUTH_USER_HEADER", "X-Authenticated-User").strip()

    if public_cloud:
        if not app_base_url.startswith("https://"):
            raise CloudConfigError("APP_BASE_URL must be https:// for public cloud mode.")
        if auth_mode == "local":
            raise CloudConfigError("AUTH_MODE must not be local in public cloud mode.")
        if len(session_secret) < 32:
            raise CloudConfigError("SESSION_SECRET must be at least 32 characters in public cloud mode.")

    return CloudConfig(
        public_cloud=public_cloud,
        app_base_url=app_base_url,
        auth_mode=auth_mode,
        session_secret=session_secret,
        auth_user_header=auth_user_header,
    )
