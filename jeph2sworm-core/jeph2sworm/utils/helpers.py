"""Helpers - Utility functions used across the swarm."""

from __future__ import annotations

import hashlib
import json
import os
import re
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional


def generate_id(prefix: str = "") -> str:
    """Generate a short unique ID with optional prefix."""
    uid = uuid.uuid4().hex[:12]
    return f"{prefix}_{uid}" if prefix else uid


def timestamp_ms() -> int:
    """Current timestamp in milliseconds."""
    return int(time.time() * 1000)


def timestamp_iso() -> str:
    """Current timestamp in ISO format."""
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()


def safe_json_dumps(obj: Any, indent: int = 2) -> str:
    """JSON serialize with fallback for non-serializable objects."""
    def default_handler(o):
        if hasattr(o, "model_dump"):
            return o.model_dump()
        if hasattr(o, "__dict__"):
            return o.__dict__
        return str(o)

    return json.dumps(obj, indent=indent, default=default_handler)


def safe_json_loads(text: str) -> Any:
    """Parse JSON, returning None on failure."""
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return None


def extract_json_from_text(text: str) -> Optional[dict]:
    """
    Extract a JSON object from a text string that may contain
    markdown code blocks or other surrounding text.
    """
    # Try direct parse first
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        pass

    # Try extracting from code blocks
    patterns = [
        r"```json\s*\n(.*?)\n```",
        r"```\s*\n(.*?)\n```",
        r"\{[\s\S]*\}",
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.DOTALL)
        if match:
            try:
                candidate = match.group(1) if match.lastindex else match.group(0)
                return json.loads(candidate)
            except (json.JSONDecodeError, TypeError, IndexError):
                continue

    return None


def file_extension(filepath: str) -> str:
    """Get file extension without the dot."""
    return Path(filepath).suffix.lstrip(".")


def detect_language(filepath: str) -> str:
    """Detect programming language from file extension."""
    ext_map = {
        "py": "python",
        "js": "javascript",
        "ts": "typescript",
        "tsx": "typescript",
        "jsx": "javascript",
        "html": "html",
        "css": "css",
        "scss": "scss",
        "json": "json",
        "yaml": "yaml",
        "yml": "yaml",
        "md": "markdown",
        "sql": "sql",
        "sh": "bash",
        "bash": "bash",
        "dockerfile": "dockerfile",
        "toml": "toml",
        "rs": "rust",
        "go": "go",
        "java": "java",
        "rb": "ruby",
        "php": "php",
        "swift": "swift",
        "kt": "kotlin",
        "dart": "dart",
    }
    ext = file_extension(filepath).lower()
    return ext_map.get(ext, "unknown")


def truncate(text: str, max_length: int = 500, suffix: str = "...") -> str:
    """Truncate text to max_length, adding suffix if truncated."""
    if len(text) <= max_length:
        return text
    return text[: max_length - len(suffix)] + suffix


def file_hash(filepath: str) -> str:
    """Calculate SHA-256 hash of a file."""
    sha = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha.update(chunk)
    return sha.hexdigest()


def ensure_dir(path: str) -> str:
    """Ensure a directory exists, creating it if necessary."""
    os.makedirs(path, exist_ok=True)
    return path


def flatten_dict(d: Dict[str, Any], parent_key: str = "", sep: str = ".") -> Dict[str, Any]:
    """Flatten a nested dict into a single-level dict with dot-separated keys."""
    items: List = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def chunk_list(lst: list, chunk_size: int) -> List[list]:
    """Split a list into chunks of chunk_size."""
    return [lst[i : i + chunk_size] for i in range(0, len(lst), chunk_size)]


def sanitize_filename(name: str) -> str:
    """Sanitize a string for use as a filename.

    Removes or replaces characters that are unsafe in file names.
    """
    import re

    # Replace path separators and other dangerous chars
    sanitized = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name)
    # Collapse multiple underscores / spaces
    sanitized = re.sub(r"_{2,}", "_", sanitized)
    sanitized = sanitized.strip(" ._")
    # Fallback for empty result
    return sanitized or "unnamed"
