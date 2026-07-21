#!/usr/bin/env python3
"""Validate CoursePackage 1.0 schema, stable IDs, and evidence references."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from schema_utils import ValidationIssue, collect_ids, duplicate_ids, issues_payload, load_json, validate_schema


ROOT = Path(__file__).resolve().parents[1]
OBJECT_FIELDS = ["sources", "lessons", "claims", "concepts", "topics", "cases", "methods", "diagnostics", "workflows", "rubrics", "templates", "transfer_rules", "failure_modes", "boundaries", "quotes", "learning_checks", "study_paths", "evidence"]


def package_path(value: str | Path) -> Path:
    path = Path(value).expanduser().resolve()
    if path.is_dir():
        path = path / "course_package.json"
    return path


def validate_package(path: Path) -> dict:
    package = load_json(path)
    schema = load_json(ROOT / "references" / "schemas" / "course_package.schema.json")
    issues = validate_schema(package, schema)
    for field in OBJECT_FIELDS:
        issues.extend(duplicate_ids(package.get(field, []), f"$.{field}"))
    evidence_ids = collect_ids(package, ["evidence"])
    source_ids = collect_ids(package, ["sources"])
    for index, pointer in enumerate(package.get("evidence", [])):
        if pointer.get("source_id") not in source_ids:
            issues.append(ValidationIssue(f"$.evidence[{index}].source_id", f"dangling source: {pointer.get('source_id')}"))
    for field in ["claims", "concepts", "topics", "cases", "methods", "diagnostics", "workflows", "rubrics", "templates", "transfer_rules", "failure_modes", "boundaries", "quotes", "study_paths"]:
        for index, item in enumerate(package.get(field, [])):
            for evidence_id in item.get("evidence", []):
                if evidence_id not in evidence_ids:
                    issues.append(ValidationIssue(f"$.{field}[{index}].evidence", f"dangling evidence: {evidence_id}"))
            if item.get("provenance") == "unsupported" and item.get("confidence") == "high":
                issues.append(ValidationIssue(f"$.{field}[{index}].confidence", "unsupported content cannot have high confidence"))
    payload = issues_payload(issues)
    payload.update({"artifact": str(path), "schema_version": package.get("schema_version")})
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate CoursePackage 1.0.")
    parser.add_argument("--fixture", help="Course workspace or course_package.json")
    parser.add_argument("--package", help="CoursePackage path")
    args = parser.parse_args()
    target = args.package or args.fixture
    if not target:
        raise SystemExit("provide --package or --fixture")
    result = validate_package(package_path(target))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if not result["valid"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
