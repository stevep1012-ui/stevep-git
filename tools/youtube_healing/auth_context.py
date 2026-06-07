from __future__ import annotations

from urllib.parse import parse_qs

from .tenant_store import sanitize_user_id


class AuthError(ValueError):
    pass


def _header_value(headers, name: str) -> str:
    if hasattr(headers, "get"):
        return str(headers.get(name, "")).strip()
    return ""


def _normalize_authenticated_value(value: str) -> str:
    clean = value.strip()
    if ":" in clean:
        clean = clean.rsplit(":", 1)[-1]
    return sanitize_user_id(clean)


def resolve_user_id(
    query: str,
    headers,
    public_cloud: bool,
    auth_user_header: str,
) -> str:
    if public_cloud:
        authenticated_value = _header_value(headers, auth_user_header)
        if not authenticated_value:
            raise AuthError(f"Missing authenticated user header: {auth_user_header}")
        return _normalize_authenticated_value(authenticated_value)

    query_user_id = parse_qs(query).get("user_id", ["guest"])[0]
    return sanitize_user_id(query_user_id)
