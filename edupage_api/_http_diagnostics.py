"""HTTP shape diagnostics: never expose URLs, cookies, identities or payloads."""

from collections.abc import Mapping
from urllib.parse import urlsplit


def context(client):
    result = {}
    for key in ("entry_id", "student_id"):
        value = getattr(client, "_diagnostic_" + key, None)
        result[key] = value if isinstance(value, (str, int)) else None
    return result


def response_shape(response, subdomain):
    try:
        return _response_shape(response, subdomain)
    except Exception as exc:
        # Diagnostics must not mask or alter the operation being diagnosed.
        return {"diagnostic_error": type(exc).__name__}


def _response_shape(response, subdomain):
    url = getattr(response, "url", "")
    parts = urlsplit(url if isinstance(url, str) else "")
    path = parts.path.rstrip("/")
    if path == "/user":
        endpoint = "user"
    elif path == "/login/edupageChange":
        endpoint = "parent_switch"
    elif path == "/login" or path.startswith("/login/"):
        endpoint = "login"
    else:
        endpoint = "other"
    text = getattr(response, "text", "")
    text = text if isinstance(text, str) else ""
    content = getattr(response, "content", None)
    size = len(content) if isinstance(content, (bytes, bytearray)) else len(text.encode())
    headers = getattr(response, "headers", {})
    headers = headers if isinstance(headers, Mapping) else {}
    mime = headers.get("Content-Type", "").split(";", 1)[0].lower()
    mime = mime if mime in ("text/html", "application/json", "text/plain") else "other"
    history = getattr(response, "history", [])
    history = history if isinstance(history, (list, tuple)) else []
    statuses = [getattr(item, "status_code", None) for item in history[:8]]
    statuses = [status for status in statuses if isinstance(status, int)]
    status = getattr(response, "status_code", None)
    return {
        "status": status if isinstance(status, int) else None,
        "endpoint": endpoint,
        "same_school_host": parts.hostname == f"{subdomain}.edupage.org",
        "redirect_count": len(history), "redirect_statuses": statuses,
        "content_type": mime, "body_bytes": size,
        "has_userhome": "userhome(" in text,
        "has_gsec_hash": "ASC.gsechash=" in text,
        "login_failed_marker": "EdupageLoginFailed" in (url if isinstance(url, str) else ""),
    }
