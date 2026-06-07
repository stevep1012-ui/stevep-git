from __future__ import annotations

import os
import shutil
from pathlib import Path


COMMON_MEDIA_BIN_DIRS = (
    Path("/opt/homebrew/opt/ffmpeg/bin"),
    Path("/usr/local/opt/ffmpeg/bin"),
)


def media_tool_env() -> dict[str, str]:
    env = os.environ.copy()
    if shutil.which("ffmpeg") and shutil.which("ffprobe"):
        return env

    for directory in COMMON_MEDIA_BIN_DIRS:
        if (directory / "ffmpeg").is_file() and (directory / "ffprobe").is_file():
            current_path = env.get("PATH", "")
            env["PATH"] = os.pathsep.join(
                part for part in (str(directory), current_path) if part
            )
            return env
    return env
