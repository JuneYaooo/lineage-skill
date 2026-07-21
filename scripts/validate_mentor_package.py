#!/usr/bin/env python3
"""Validate MentorPackage and its referenced teacher/runtime assets."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from schema_utils import ValidationIssue, duplicate_ids, find_prerequisite_cycles, issues_payload, load_json, validate_schema


ROOT = Path(__file__).resolve().parents[1]


def mentor_path(value: str | Path) -> Path:
    path = Path(value).expanduser().resolve()
    if path.is_dir():
        path = path / "mentor_package.json"
    return path


def validate_mentor(path: Path) -> dict:
    mentor = load_json(path)
    base = path.parent
    schema = load_json(ROOT / "references" / "schemas" / "mentor_package.schema.json")
    issues = validate_schema(mentor, schema)
    references = [
        "capability_graph_ref",
        "teacher_model_ref",
        "practice_bank_ref",
        "assessment_bank_ref",
        "mentor_protocol_ref",
        "graduation_policy_ref",
    ]
    for field in references:
        target = base / str(mentor.get(field) or "")
        if not target.exists():
            issues.append(ValidationIssue(f"$.{field}", f"referenced artifact does not exist: {target}"))
    if (base / mentor.get("capability_graph_ref", "capability_graph.json")).exists():
        graph = load_json(base / mentor.get("capability_graph_ref", "capability_graph.json"))
        issues.extend(duplicate_ids(graph.get("nodes", []), "$.capability_graph.nodes"))
        for cycle in find_prerequisite_cycles(graph.get("nodes", [])):
            issues.append(ValidationIssue("$.capability_graph.nodes", f"prerequisite cycle: {' -> '.join(cycle)}"))
    mode = mentor.get("manifest", {}).get("apprenticeship_mode")
    readiness = mentor.get("quality", {}).get("mentor_readiness")
    if mode == "full" and readiness != "ready":
        issues.append(ValidationIssue("$.manifest.apprenticeship_mode", "full mode requires mentor_readiness=ready"))
    result = issues_payload(issues)
    result.update({"artifact": str(path), "apprenticeship_mode": mode, "mentor_readiness": readiness})
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate MentorPackage 1.0.")
    parser.add_argument("--fixture")
    parser.add_argument("--package")
    args = parser.parse_args()
    target = args.package or args.fixture
    if not target:
        raise SystemExit("provide --package or --fixture")
    result = validate_mentor(mentor_path(target))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if not result["valid"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
