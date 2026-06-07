from __future__ import annotations

import re
from urllib.parse import urlparse

from .models import MediaProfile, MusicSelection, PolicyFinding, SourceAsset


PRIVACY_REVIEW_KEYWORDS = (
    "face",
    "person",
    "people",
    "license plate",
    "house number",
    "얼굴",
    "사람",
    "차량번호",
    "번호판",
    "집주소",
    "주소",
    "전화번호",
    "주민등록번호",
    "개인정보",
    "이름",
)
FORBIDDEN_LICENSE_TERMS = (
    "free",
    "unknown",
    "tbd",
    "no copyright music",
    "record the exact",
    "replace",
    "placeholder",
)
MIN_LICENSE_TERMS_LENGTH = 12
YOUTUBE_AUDIO_LIBRARY = "YouTube Audio Library"
MUSOPEN = "Musopen"
NEGATIVE_PRIVACY_PHRASES = {
    "face": ("no face visible", "face not visible"),
    "person": ("no person visible", "person not visible"),
    "people": ("no people visible", "people not visible"),
    "license plate": ("no license plate visible", "license plate not visible"),
}


def _has_allowed_youtube_url(source_url: str) -> bool:
    parsed = urlparse(source_url.strip())
    host = parsed.netloc.lower()
    path_segments = [segment.lower() for segment in parsed.path.split("/") if segment]
    if parsed.scheme not in {"http", "https"}:
        return False
    return (
        host == "studio.youtube.com"
        and "audio-library" in path_segments
    ) or (
        host in {"youtube.com", "www.youtube.com"}
        and "audiolibrary" in path_segments
    )


def _has_allowed_musopen_url(source_url: str) -> bool:
    parsed = urlparse(source_url.strip())
    host = parsed.netloc.lower()
    path_segments = [segment.lower() for segment in parsed.path.split("/") if segment]
    if parsed.scheme not in {"http", "https"}:
        return False
    return host in {"musopen.org", "www.musopen.org"} and "music" in path_segments


def _has_allowed_music_source(source_name: str, source_url: str) -> bool:
    if source_name == YOUTUBE_AUDIO_LIBRARY:
        return _has_allowed_youtube_url(source_url)
    if source_name == MUSOPEN:
        return _has_allowed_musopen_url(source_url)
    return False


def _has_usable_license_terms(license_terms: str) -> bool:
    normalized = license_terms.strip().lower()
    return len(normalized) >= MIN_LICENSE_TERMS_LENGTH and not any(
        forbidden in normalized for forbidden in FORBIDDEN_LICENSE_TERMS
    )


def _mentions_privacy_risk(privacy_text: str) -> bool:
    normalized = privacy_text.lower()
    for term in PRIVACY_REVIEW_KEYWORDS:
        if term.isascii():
            mentioned = bool(re.search(rf"\b{re.escape(term)}\b", normalized))
        else:
            mentioned = term in normalized
        if not mentioned:
            continue
        negative_phrases = NEGATIVE_PRIVACY_PHRASES.get(term, ())
        if not any(phrase in normalized for phrase in negative_phrases):
            return True
    return False


def evaluate_policy(
    asset: SourceAsset,
    profile: MediaProfile,
    music_selection: MusicSelection | None,
) -> list[PolicyFinding]:
    findings: list[PolicyFinding] = []

    if not asset.owned_by_user:
        findings.append(
            PolicyFinding(
                code="source_ownership_missing",
                severity="blocker",
                message="Source footage or original sound ownership is not confirmed.",
                blocking=True,
            )
        )

    if not profile.has_audio:
        findings.append(
            PolicyFinding(
                code="source_audio_missing",
                severity="blocker",
                message="Source video has no audio stream, so original bird sound is missing.",
                blocking=True,
            )
        )

    if _mentions_privacy_risk(asset.privacy_notes):
        findings.append(
            PolicyFinding(
                code="privacy_review_required",
                severity="warning",
                message="Privacy notes mention visible private information. Manual review is required.",
                blocking=True,
            )
        )

    if music_selection is None:
        findings.append(
            PolicyFinding(
                code="music_license_missing",
                severity="blocker",
                message="No music selection and license evidence are attached.",
                blocking=True,
            )
        )
    else:
        evidence = music_selection.track.evidence
        if evidence.source_name not in {YOUTUBE_AUDIO_LIBRARY, MUSOPEN}:
            findings.append(
                PolicyFinding(
                    code="music_source_not_allowed",
                    severity="blocker",
                    message="MVP allows only YouTube Audio Library or Musopen public domain music.",
                    blocking=True,
                )
            )
        if (
            not _has_allowed_music_source(evidence.source_name, evidence.source_url)
            or not _has_usable_license_terms(evidence.license_terms)
            or not evidence.access_date.strip()
        ):
            findings.append(
                PolicyFinding(
                    code="music_license_evidence_incomplete",
                    severity="blocker",
                    message="Music license evidence is incomplete.",
                    blocking=True,
                )
            )

    if not findings:
        findings.append(
            PolicyFinding(
                code="ready_for_review",
                severity="info",
                message="No blocking policy issues found. User review is still required before upload.",
                blocking=False,
            )
        )

    return findings
