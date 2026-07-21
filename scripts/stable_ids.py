#!/usr/bin/env python3
"""Deterministic identifiers and content hashes for Lineage packages."""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from typing import Any


ID_PREFIXES = {
    "source": "src",
    "lesson": "lesson",
    "chunk": "chunk",
    "card": "card",
    "claim": "claim",
    "capability": "cap",
    "edge": "edge",
    "rule": "rule",
    "rubric": "rubric",
    "task": "task",
    "assessment": "assess",
    "demonstration": "demo",
    "episode": "episode",
    "error": "error",
    "candidate": "candidate",
    "teacher": "teacher",
    "course": "course",
    "mentor_package": "mentor",
}


def normalize_part(value: Any) -> str:
    """Normalize an ID input without discarding non-Latin source text."""
    if value is None:
        return ""
    if isinstance(value, (dict, list, tuple, set)):
        value = canonical_json(value)
    text = unicodedata.normalize("NFKC", str(value)).strip().lower()
    return re.sub(r"\s+", " ", text)


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)


def content_hash(value: Any, length: int = 64) -> str:
    raw = value if isinstance(value, bytes) else canonical_json(value).encode("utf-8")
    digest = hashlib.sha256(raw).hexdigest()
    return digest[:length]


def stable_id(kind: str, *parts: Any, namespace: str | None = None, length: int = 16) -> str:
    """Return a readable prefix plus a stable SHA-256 fragment."""
    prefix = ID_PREFIXES.get(kind, kind).strip("_")
    payload = [normalize_part(namespace)] if namespace else []
    payload.extend(normalize_part(part) for part in parts)
    digest = hashlib.sha256("\x1f".join(payload).encode("utf-8")).hexdigest()[:length]
    return f"{prefix}_{digest}"


def ensure_stable_id(value: str | None, kind: str, *parts: Any, namespace: str | None = None) -> str:
    """Keep an existing stable ID, otherwise derive one from content."""
    if value and re.match(r"^[a-z][a-z0-9-]*_[a-f0-9]{8,64}$", value):
        return value
    return stable_id(kind, *(parts or (value or kind,)), namespace=namespace)
