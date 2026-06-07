from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class UserPaths:
    user_id: str
    user_root: Path
    input_root: Path
    output_root: Path
    config_root: Path


def sanitize_user_id(user_id: str) -> str:
    if "/" in user_id or "\\" in user_id:
        raise ValueError("Invalid user_id")
    safe = re.sub(r"[^A-Za-z0-9._-]+", "-", user_id.strip()).strip("-._")
    if not safe or safe in {".", ".."}:
        raise ValueError("Invalid user_id")
    return safe


def build_user_paths(multi_user_root: Path, user_id: str) -> UserPaths:
    safe_user_id = sanitize_user_id(user_id)
    user_root = multi_user_root / safe_user_id
    return UserPaths(
        user_id=safe_user_id,
        user_root=user_root,
        input_root=user_root / "inputs",
        output_root=user_root / "outputs" / "youtube-healing",
        config_root=user_root / "config",
    )
