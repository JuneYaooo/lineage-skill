#!/usr/bin/env python3
"""Merge multiple CoursePackage files into one combined course workspace."""

from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BASE_DIR = ROOT / ".lineage" / "courses"

MERGED_LIST_FIELDS = [
    "lessons",
    "concepts",
    "topics",
    "cases",
    "methods",
    "diagnostics",
    "workflows",
    "rubrics",
    "templates",
    "transfer_rules",
    "failure_modes",
    "learning_checks",
    "quotes",
    "evidence",
    "study_paths",
    "boundaries",
]


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"not a JSON object: {path}")
    return data


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


def course_label(package: dict[str, Any], source_dir: Path) -> str:
    manifest = package.get("manifest") if isinstance(package.get("manifest"), dict) else {}
    return manifest.get("course_name") or source_dir.name


def source_dir_for(package_path: Path, package: dict[str, Any]) -> Path:
    manifest = package.get("manifest") if isinstance(package.get("manifest"), dict) else {}
    raw = manifest.get("source_dir")
    if raw:
        return Path(raw).expanduser().resolve()
    return package_path.parent.resolve()


def with_course_prefix(item: Any, course_name: str, course_id: str, source_dir: Path) -> Any:
    if isinstance(item, dict):
        row = dict(item)
        row.setdefault("source_course", course_name)
        row.setdefault("source_course_id", course_id)
        if "id" in row:
            row["id"] = f"{course_id}:{row['id']}"
        if "source" in row and row["source"]:
            row["source"] = f"{course_id}/{row['source']}"
        if "path" in row and row["path"]:
            row["path"] = f"{course_id}/{row['path']}"
        row.setdefault("source_dir", str(source_dir))
        return row
    return {
        "value": item,
        "source_course": course_name,
        "source_course_id": course_id,
        "source_dir": str(source_dir),
    }


def merge_packages(items: list[tuple[Path, dict[str, Any]]], combined_name: str) -> dict[str, Any]:
    source_courses = []
    merged: dict[str, Any] = {field: [] for field in MERGED_LIST_FIELDS}
    for idx, (pkg_path, package) in enumerate(items, start=1):
        source_dir = source_dir_for(pkg_path, package)
        name = course_label(package, source_dir)
        course_id = f"course-{idx:03d}"
        source_courses.append(
            {
                "id": course_id,
                "name": name,
                "package_path": str(pkg_path),
                "source_dir": str(source_dir),
                "quality": package.get("quality", {}),
            }
        )
        for field in MERGED_LIST_FIELDS:
            values = package.get(field) or []
            if not isinstance(values, list):
                values = [values]
            merged[field].extend(with_course_prefix(value, name, course_id, source_dir) for value in values)

    counts = {field: len(merged[field]) for field in MERGED_LIST_FIELDS}
    return {
        "schema_version": "0.1",
        "manifest": {
            "course_name": combined_name,
            "generated_at": dt.datetime.now().isoformat(timespec="seconds"),
            "package_type": "multi-course",
            "source_courses": source_courses,
        },
        **merged,
        "quality": {
            "counts": counts,
            "source_course_count": len(source_courses),
            "status": "usable" if source_courses else "thin",
        },
    }


def write_summary(package: dict[str, Any], output_dir: Path) -> None:
    manifest = package["manifest"]
    lines = [
        f"# {manifest['course_name']} — Multi-Course Digest",
        "",
        f"Generated at: {manifest['generated_at']}",
        "",
        "## Source Courses",
        "",
    ]
    for course in manifest["source_courses"]:
        lines.append(f"- `{course['id']}` {course['name']} — `{course['source_dir']}`")
    lines.extend(
        [
            "",
            "## Package Counts",
            "",
        ]
    )
    for key, value in sorted(package["quality"]["counts"].items()):
        lines.append(f"- {key}: {value}")
    lines.extend(
        [
            "",
            "## Notes",
            "",
            "This is a combined CoursePackage. Use `source_course` and `source_course_id` fields to distinguish where each lesson, concept, method, quote, or evidence item came from.",
            "If source courses disagree, preserve the source-course distinction instead of flattening them into one claim.",
            "",
        ]
    )
    output_dir.joinpath("course_digest.md").write_text("\n".join(lines), encoding="utf-8")
    output_dir.joinpath("source_courses.json").write_text(
        json.dumps({"courses": manifest["source_courses"]}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def write_evidence_map(package: dict[str, Any], output_dir: Path) -> None:
    evidence = package.get("evidence") if isinstance(package.get("evidence"), list) else []
    by_course: dict[str, int] = {}
    by_type: dict[str, int] = {}
    for row in evidence:
        if not isinstance(row, dict):
            continue
        by_course[row.get("source_course_id", "unknown")] = by_course.get(row.get("source_course_id", "unknown"), 0) + 1
        by_type[row.get("type", "unknown")] = by_type.get(row.get("type", "unknown"), 0) + 1
    payload = {
        "generated_at": package["manifest"]["generated_at"],
        "source_dir": str(output_dir),
        "source_courses": package["manifest"]["source_courses"],
        "counts": {
            "total": len(evidence),
            "by_course": dict(sorted(by_course.items())),
            "by_type": dict(sorted(by_type.items())),
        },
        "evidence": evidence,
        "notes": [
            "Paths with course-001/course-002 prefixes refer to merged CoursePackage paths.",
            "Packaged Skill references also copy each source workspace under references/source_courses/<source-dir-name>/.",
        ],
    }
    output_dir.joinpath("evidence_map.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Merge multiple CoursePackage files into one combined workspace.")
    parser.add_argument("--course", action="append", required=True, help="Course workspace or course_package.json path. Repeatable.")
    parser.add_argument("--combined-name", required=True, help="Human-readable combined package name.")
    parser.add_argument("--output-dir", required=True, help="Combined workspace output directory.")
    parser.add_argument("--base-dir", default=str(DEFAULT_BASE_DIR), help="Base dir for relative course workspace names.")
    args = parser.parse_args()

    base_dir = Path(args.base_dir).expanduser().resolve()
    output_dir = Path(args.output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    items = [(path, load_json(path)) for path in (package_path(value, base_dir) for value in args.course)]
    package = merge_packages(items, args.combined_name)
    output_dir.joinpath("course_package.json").write_text(json.dumps(package, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_summary(package, output_dir)
    write_evidence_map(package, output_dir)
    print(f"wrote {output_dir / 'course_package.json'}")
    print(f"source courses: {len(items)}")


if __name__ == "__main__":
    main()
