"""Output formatting: plain, JSON, and simple table."""

import json
import sys
from typing import Any


def format_output(data: Any, fmt: str = "json") -> str:
    if fmt == "json":
        return json.dumps(data, indent=2, default=str)
    return _table(data)


def _table(data: Any) -> str:
    """Render a list of dicts as a simple aligned table."""
    if isinstance(data, dict):
        # Try to pull a list field out
        for k, v in data.items():
            if isinstance(v, list) and v and isinstance(v[0], dict):
                return _render_rows(v)
        # Single dict: key: value
        return "\n".join(f"{k}: {v}" for k, v in data.items())
    if isinstance(data, list):
        if not data:
            return "(empty)"
        if all(isinstance(row, dict) for row in data):
            return _render_rows(data)
        return "\n".join(str(item) for item in data)
    return str(data)


def _render_rows(rows: list[dict]) -> str:
    keys = list(rows[0].keys())
    widths = {k: len(k) for k in keys}
    for row in rows:
        for k in keys:
            widths[k] = max(widths[k], len(str(row.get(k, ""))))
    header = "  ".join(k.ljust(widths[k]) for k in keys)
    sep = "  ".join("-" * widths[k] for k in keys)
    lines = [header, sep]
    for row in rows:
        lines.append("  ".join(str(row.get(k, "")).ljust(widths[k]) for k in keys))
    return "\n".join(lines)


def die(message: str, code: int = 1):
    print(f"Error: {message}", file=sys.stderr)
    sys.exit(code)
