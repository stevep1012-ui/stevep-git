from __future__ import annotations

import re
from pathlib import Path

from .models import PolicyFinding


def safe_slug(value: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"Slug input must be string, got {type(value)}")
    if len(value) > 256:
        raise ValueError(f"Slug too long (max 256 chars)")
    normalized = value.strip().lower()
    slug = re.sub(r"[^\w]+", "-", normalized, flags=re.UNICODE)
    slug = slug.strip("-_")
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug or "youtube-healing-video"


def validate_filename(filename: str, max_length: int = 255) -> str:
    if not isinstance(filename, str):
        raise TypeError(f"Filename must be string, got {type(filename)}")
    if not filename.strip():
        raise ValueError("Filename cannot be empty")
    if len(filename) > max_length:
        raise ValueError(f"Filename too long (max {max_length} chars)")
    if "/" in filename or "\\" in filename:
        raise ValueError("Filename cannot contain path separators")
    if filename.startswith("."):
        raise ValueError("Filename cannot start with dot (hidden file)")
    if filename in {".", "..", "CON", "PRN", "AUX", "NUL", "COM1", "LPT1"}:
        raise ValueError(f"Filename '{filename}' is reserved")
    return filename


def write_metadata_file(path: Path, metadata_text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(metadata_text, encoding="utf-8")


def write_approval_checklist(
    path: Path,
    findings: list[PolicyFinding],
    audio_check: str = "Confirm bird sound is primary",
) -> None:
    lines = [
        "# Upload Approval Checklist",
        "",
        "- [ ] Watch final video",
        f"- [ ] {audio_check}",
        "- [ ] Confirm music license evidence",
        "- [ ] Confirm no private person/license plate/sensitive location",
        "- [ ] Confirm no medical/guaranteed wellness claims",
        "",
        "## Policy Findings",
    ]

    if findings:
        for finding in findings:
            if finding.blocking:
                lines.append(f"- [ ] Resolve blocker: {finding.code} - {finding.message}")
            else:
                lines.append(f"- Info: {finding.code} - {finding.message}")
    else:
        lines.append("- Info: No policy findings recorded.")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
