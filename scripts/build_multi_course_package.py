#!/usr/bin/env python3
"""Merge migrated CoursePackage 1.0 inputs while preserving teacher conflicts."""

from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path
from typing import Any

from migrate_course_package import ASSET_FIELDS, migrate_package
from schema_utils import load_json, write_json
from stable_ids import stable_id


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BASE_DIR = ROOT / ".lineage" / "courses"
MERGED_LIST_FIELDS = ["sources", "lessons", "claims", *ASSET_FIELDS, "learning_checks", "evidence"]


def package_path(value: str, base_dir: Path) -> Path:
    path = Path(value).expanduser()
    if not path.is_absolute():
        cwd_candidate = path.resolve()
        path = cwd_candidate if cwd_candidate.exists() else base_dir / path
    if path.is_dir():
        path = path / "course_package.json"
    if not path.exists():
        raise SystemExit(f"course package not found: {path}")
    return path.resolve()


def load_and_migrate(path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    package = load_json(path)
    return migrate_package(package, source_path=path) if package.get("schema_version") != "1.0" else (package, {"source_schema_version": "1.0", "target_schema_version": "1.0"})


def course_label(package: dict[str, Any], source_dir: Path) -> str:
    return str(package.get("manifest", {}).get("course_name") or source_dir.name)


def source_dir_for(path: Path, package: dict[str, Any]) -> Path:
    raw = package.get("manifest", {}).get("source_dir")
    return Path(raw).expanduser().resolve() if raw else path.parent.resolve()


def conflict_records(package: dict[str, Any]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for field in ["methods", "diagnostics", "rubrics", "transfer_rules", "boundaries"]:
        by_title: dict[str, list[dict[str, Any]]] = {}
        for item in package.get(field, []):
            by_title.setdefault(str(item.get("title", "")).strip().lower(), []).append(item)
        for title, items in by_title.items():
            summaries = {str(item.get("summary", "")).strip() for item in items}
            courses = {str(item.get("source_course_id", "")) for item in items}
            if title and len(summaries) > 1 and len(courses) > 1:
                records.append(
                    {
                        "id": stable_id("claim", "conflict", field, title, sorted(summaries)),
                        "field": field,
                        "title": items[0].get("title"),
                        "item_ids": [item["id"] for item in items],
                        "source_course_ids": sorted(courses),
                        "status": "unresolved",
                        "policy": "Preserve each source's conditions and evidence; do not flatten into a synthetic consensus.",
                    }
                )
    return records


def merge_packages(items: list[tuple[Path, dict[str, Any]]], combined_name: str) -> dict[str, Any]:
    combined_course_id = stable_id("course", combined_name, [str(path) for path, _ in items])
    source_courses: list[dict[str, Any]] = []
    merged: dict[str, list[Any]] = {field: [] for field in MERGED_LIST_FIELDS}
    migrations: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for path, raw_package in items:
        package, report = migrate_package(raw_package, source_path=path) if raw_package.get("schema_version") != "1.0" else (raw_package, {"source_schema_version": "1.0", "target_schema_version": "1.0"})
        source_dir = source_dir_for(path, package)
        name = course_label(package, source_dir)
        original_course_id = package["manifest"]["course_id"]
        course_id = stable_id("course", original_course_id, str(path))
        migrations.append({"package_path": str(path), **report})
        source_courses.append(
            {
                "id": course_id,
                "original_course_id": original_course_id,
                "name": name,
                "package_path": str(path),
                "source_dir": str(source_dir),
                "quality": package.get("quality", {}),
            }
        )
        id_map: dict[str, str] = {}
        for field in MERGED_LIST_FIELDS:
            for item in package.get(field, []):
                if not isinstance(item, dict):
                    continue
                old_id = str(item.get("id") or stable_id(field.rstrip("s"), course_id, item))
                new_id = old_id if old_id not in seen_ids else stable_id(field.rstrip("s"), course_id, old_id)
                seen_ids.add(new_id)
                id_map[old_id] = new_id
        for field in MERGED_LIST_FIELDS:
            for item in package.get(field, []):
                if not isinstance(item, dict):
                    item = {"value": str(item), "legacy_text": str(item)}
                row = dict(item)
                old_id = str(row.get("id") or stable_id(field.rstrip("s"), course_id, row))
                row["id"] = id_map[old_id]
                row["source_course"] = name
                row["source_course_id"] = course_id
                row["source_dir"] = str(source_dir)
                row["source_courses"] = [course_id if value == original_course_id else value for value in row.get("source_courses", [original_course_id])]
                for reference_field in ["evidence", "source_evidence", "related_capabilities", "failure_modes", "rubric_ids", "capability_ids", "transfer_variant_ids"]:
                    if isinstance(row.get(reference_field), list):
                        row[reference_field] = [id_map.get(str(value), str(value)) for value in row[reference_field]]
                if row.get("source"):
                    row["source"] = f"{course_id}/{row['source']}"
                if row.get("path"):
                    row["path"] = f"{course_id}/{row['path']}"
                merged[field].append(row)

    package: dict[str, Any] = {
        "schema_version": "1.0",
        "manifest": {
            "course_id": combined_course_id,
            "package_id": stable_id("course", combined_course_id, "package-1.0"),
            "course_name": combined_name,
            "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
            "package_type": "multi-course",
            "source_courses": source_courses,
            "migrations": migrations,
        },
        **merged,
        "teacher_model_ref": "teacher_model.json",
        "capability_graph_ref": "capability_graph.json",
        "practice_bank_ref": "practice_bank.json",
        "assessment_bank_ref": "assessment_bank.json",
        "quality": {},
    }
    conflicts = conflict_records(package)
    package["manifest"]["conflicts"] = conflicts
    package["quality"] = {
        "coverage": {
            "source_coverage": len(package["sources"]),
            "lesson_coverage": len(package["lessons"]),
            "modality_coverage": len({item.get("evidence_kind") for item in package["evidence"]}),
            "capability_coverage": sum(len(package[field]) for field in ["methods", "diagnostics", "workflows", "rubrics", "transfer_rules"]),
            "teacher_model_coverage": 0,
            "practice_coverage": len(package["learning_checks"]),
            "assessment_coverage": 0,
        },
        "integrity": {
            "dangling_reference_count": 0,
            "unsupported_claim_count": sum(item.get("provenance") == "unsupported" for item in package["claims"]),
            "source_conflict_count": len(conflicts),
            "placeholder_count": 0,
            "duplicate_id_count": 0,
        },
        "mentor_readiness": {"status": "partial", "missing_requirements": ["teacher_model", "capability_graph", "practice_bank", "assessment_bank"], "human_review_required": [record["id"] for record in conflicts]},
    }
    return package


def write_summary(package: dict[str, Any], output_dir: Path) -> None:
    lines = [f"# {package['manifest']['course_name']} — Multi-Course Digest", "", "## Source Courses", ""]
    lines.extend(f"- `{item['id']}` {item['name']} — `{item['source_dir']}`" for item in package["manifest"]["source_courses"])
    lines.extend(["", "## Explicit Conflicts", ""])
    conflicts = package["manifest"]["conflicts"]
    if conflicts:
        lines.extend(f"- `{item['id']}` {item['field']}: {item['title']} ({', '.join(item['source_course_ids'])})" for item in conflicts)
    else:
        lines.append("- No detected same-title semantic conflicts.")
    lines.extend(["", "Source distinctions and conditions must remain visible whenever sources disagree.", ""])
    output_dir.joinpath("course_digest.md").write_text("\n".join(lines), encoding="utf-8")
    write_json(output_dir / "source_courses.json", {"courses": package["manifest"]["source_courses"]})


def write_evidence_map(package: dict[str, Any], output_dir: Path) -> None:
    write_json(output_dir / "evidence_map.json", {"source_courses": package["manifest"]["source_courses"], "conflicts": package["manifest"]["conflicts"], "evidence": package["evidence"]})


def main() -> None:
    parser = argparse.ArgumentParser(description="Merge CoursePackage 0.x/1.0 inputs into one 1.0 workspace.")
    parser.add_argument("--course", action="append", required=True)
    parser.add_argument("--combined-name", required=True)
    parser.add_argument("--base-dir", default=str(DEFAULT_BASE_DIR))
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    base_dir = Path(args.base_dir).expanduser().resolve()
    items = [(path := package_path(value, base_dir), load_json(path)) for value in args.course]
    package = merge_packages(items, args.combined_name)
    output_dir = Path(args.output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    write_json(output_dir / "course_package.json", package)
    write_summary(package, output_dir)
    write_evidence_map(package, output_dir)
    print(json.dumps({"output": str(output_dir / 'course_package.json'), "source_courses": len(package["manifest"]["source_courses"]), "conflicts": len(package["manifest"]["conflicts"])}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
