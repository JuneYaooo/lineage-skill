#!/usr/bin/env python3
"""Small dependency-free schema and referential-integrity helpers."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


@dataclass(frozen=True)
class ValidationIssue:
    path: str
    message: str
    severity: str = "error"

    def as_dict(self) -> dict[str, str]:
        return {"path": self.path, "message": self.message, "severity": self.severity}


JSON_TYPES: dict[str, type | tuple[type, ...]] = {
    "object": dict,
    "array": list,
    "string": str,
    "number": (int, float),
    "integer": int,
    "boolean": bool,
    "null": type(None),
}


def load_json(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path: str | Path, payload: Any) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def validate_schema(instance: Any, schema: dict[str, Any], path: str = "$") -> list[ValidationIssue]:
    """Validate the JSON-Schema subset used by bundled Lineage contracts."""
    issues: list[ValidationIssue] = []
    expected = schema.get("type")
    if isinstance(expected, list):
        accepted = tuple(JSON_TYPES[item] for item in expected if item in JSON_TYPES)
    else:
        accepted = JSON_TYPES.get(expected) if expected else None
    numeric_expected = expected in {"integer", "number"} if isinstance(expected, str) else any(item in {"integer", "number"} for item in expected or [])
    if accepted and (isinstance(instance, bool) and numeric_expected or not isinstance(instance, accepted)):
        return [ValidationIssue(path, f"expected {expected}, got {type(instance).__name__}")]

    if "const" in schema and instance != schema["const"]:
        issues.append(ValidationIssue(path, f"expected constant {schema['const']!r}"))
    if "enum" in schema and instance not in schema["enum"]:
        issues.append(ValidationIssue(path, f"value {instance!r} is not in enum"))
    if isinstance(instance, str):
        if len(instance) < schema.get("minLength", 0):
            issues.append(ValidationIssue(path, "string is shorter than minLength"))
    if isinstance(instance, list):
        if len(instance) < schema.get("minItems", 0):
            issues.append(ValidationIssue(path, "array is shorter than minItems"))
        item_schema = schema.get("items")
        if isinstance(item_schema, dict):
            for index, value in enumerate(instance):
                issues.extend(validate_schema(value, item_schema, f"{path}[{index}]"))
    if isinstance(instance, dict):
        for key in schema.get("required", []):
            if key not in instance:
                issues.append(ValidationIssue(path, f"missing required property: {key}"))
        properties = schema.get("properties", {})
        for key, value in instance.items():
            if key in properties:
                issues.extend(validate_schema(value, properties[key], f"{path}.{key}"))
    return issues


def validate_file(instance_path: str | Path, schema_path: str | Path) -> list[ValidationIssue]:
    return validate_schema(load_json(instance_path), load_json(schema_path))


def duplicate_ids(objects: Iterable[Any], path: str = "$") -> list[ValidationIssue]:
    seen: dict[str, str] = {}
    issues: list[ValidationIssue] = []
    for index, item in enumerate(objects):
        if not isinstance(item, dict) or not item.get("id"):
            continue
        item_id = str(item["id"])
        current = f"{path}[{index}].id"
        if item_id in seen:
            issues.append(ValidationIssue(current, f"duplicate id {item_id}; first seen at {seen[item_id]}"))
        else:
            seen[item_id] = current
    return issues


def collect_ids(payload: dict[str, Any], fields: Iterable[str]) -> set[str]:
    ids: set[str] = set()
    for field in fields:
        for item in payload.get(field, []) if isinstance(payload.get(field), list) else []:
            if isinstance(item, dict) and item.get("id"):
                ids.add(str(item["id"]))
    return ids


def dangling_references(
    objects: Iterable[Any],
    *,
    reference_fields: Iterable[str],
    valid_ids: set[str],
    path: str = "$",
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    for index, item in enumerate(objects):
        if not isinstance(item, dict):
            continue
        for field in reference_fields:
            value = item.get(field)
            refs = value if isinstance(value, list) else [value] if value else []
            for ref in refs:
                if isinstance(ref, str) and ref not in valid_ids:
                    issues.append(ValidationIssue(f"{path}[{index}].{field}", f"dangling reference: {ref}"))
    return issues


def find_prerequisite_cycles(nodes: list[dict[str, Any]]) -> list[list[str]]:
    graph = {str(node.get("id")): [str(item) for item in node.get("prerequisites", [])] for node in nodes if node.get("id")}
    visiting: set[str] = set()
    visited: set[str] = set()
    cycles: list[list[str]] = []

    def visit(node_id: str, trail: list[str]) -> None:
        if node_id in visiting:
            start = trail.index(node_id) if node_id in trail else 0
            cycle = trail[start:] + [node_id]
            if cycle not in cycles:
                cycles.append(cycle)
            return
        if node_id in visited:
            return
        visiting.add(node_id)
        for parent in graph.get(node_id, []):
            if parent in graph:
                visit(parent, trail + [node_id])
        visiting.remove(node_id)
        visited.add(node_id)

    for node_id in graph:
        visit(node_id, [])
    return cycles


def issues_payload(issues: list[ValidationIssue]) -> dict[str, Any]:
    return {
        "valid": not any(issue.severity == "error" for issue in issues),
        "error_count": sum(issue.severity == "error" for issue in issues),
        "warning_count": sum(issue.severity == "warning" for issue in issues),
        "issues": [issue.as_dict() for issue in issues],
    }
