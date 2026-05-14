"""HTTP client for the UnraidClaw REST API."""

import json
import os
import ssl
import urllib.request
import urllib.error
from pathlib import Path
from typing import Any
from . import __version__


def _load_dotenv() -> None:
    """Load .env file from project root into os.environ.
    
    Reads the file at <project-root>/.env if it exists.
    Does NOT override already-set environment variables,
    so exports and CLI flags always take precedence.
    """
    env_file = Path(__file__).resolve().parent.parent / ".env"
    if not env_file.is_file():
        return

    with open(env_file) as f:
        for line in f:
            line = line.strip()
            # Skip blank lines and comments
            if not line or line.startswith("#"):
                continue
            # Parse KEY=VALUE (allow = in value)
            if "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip()

            # Remove optional surrounding quotes
            if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
                value = value[1:-1]

            if key and key not in os.environ:
                os.environ[key] = value


class UnraidAPIError(Exception):
    def __init__(self, message: str, status_code: int = 0, error_code: str = ""):
        self.status_code = status_code
        self.error_code = error_code
        super().__init__(message)


def _get_config():
    server_url = os.environ.get("UNRAIDCLAW_URL", "").rstrip("/")
    api_key = os.environ.get("UNRAIDCLAW_KEY", "")
    tls_skip = os.environ.get("UNRAIDCLAW_TLS_SKIP", "").lower() in ("1", "true", "yes")

    if not server_url:
        raise UnraidAPIError(
            "UNRAIDCLAW_URL not set. Export it or pass --url.\n"
            "Example: export UNRAIDCLAW_URL=https://your-unraid:9876",
            error_code="CONFIG_ERROR",
        )
    if not api_key:
        raise UnraidAPIError(
            "UNRAIDCLAW_KEY not set. Export it or pass --key.\n"
            "Example: export UNRAIDCLAW_KEY=your-api-key",
            error_code="CONFIG_ERROR",
        )
    return server_url, api_key, tls_skip


def _request(method: str, path: str, body: Any = None) -> Any:
    """Make an API request. Returns the 'data' field on success."""
    server_url, api_key, tls_skip = _get_config()
    url = f"{server_url}{path}"

    payload = json.dumps(body).encode() if body is not None else None
    headers = {"x-api-key": api_key, "User-Agent": f"unraidclaw/{__version__}"}
    if payload:
        headers["Content-Type"] = "application/json"

    req = urllib.request.Request(url, data=payload, headers=headers, method=method)

    ctx = None
    if tls_skip and url.startswith("https"):
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

    try:
        with urllib.request.urlopen(req, context=ctx, timeout=30) as resp:
            body_dict = json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        try:
            body_dict = json.loads(e.read().decode())
        except Exception:
            raise UnraidAPIError(
                f"HTTP {e.code}: {e.reason}", status_code=e.code, error_code="HTTP_ERROR"
            ) from e
    except urllib.error.URLError as e:
        raise UnraidAPIError(
            f"Connection failed: {e.reason}", error_code="CONNECTION_ERROR"
        ) from e

    if not body_dict.get("ok"):
        err = body_dict.get("error", {})
        if isinstance(err, str):
            raise UnraidAPIError(err, error_code="UNKNOWN")
        raise UnraidAPIError(
            err.get("message", "Unknown error"),
            error_code=err.get("code", "UNKNOWN"),
        )
    return body_dict["data"]


def get(path: str, query: dict[str, str] | None = None) -> Any:
    if query:
        from urllib.parse import urlencode
        path = f"{path}?{urlencode(query)}"
    return _request("GET", path)


def post(path: str, body: Any = None) -> Any:
    return _request("POST", path, body)


def patch(path: str, body: Any = None) -> Any:
    return _request("PATCH", path, body)


def delete(path: str) -> Any:
    return _request("DELETE", path)
