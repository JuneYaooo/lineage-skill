#!/usr/bin/env python3
"""Build a catalog for multiple distilled course workspaces."""

from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BASE_DIR = ROOT / ".lineage" / "courses"
DEFAULT_OUTPUT_DIR = ROOT / "dist"


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def latest(patterns: list[str], root: Path) -> str:
    matches = []
    for pattern in patterns:
        matches.extend(root.glob(pattern))
    matches = sorted((path for path in matches if path.is_file()), key=lambda path: path.stat().st_mtime, reverse=True)
    return str(matches[0].relative_to(root)) if matches else ""


def artifact_counts(course_dir: Path) -> dict[str, int]:
    return {
        "transcripts": len(list(course_dir.glob("transcripts/*_transcript.json"))),
        "visual_analyses": len(list(course_dir.glob("analysis/*_analysis.md"))),
        "screenshots": len([path for path in course_dir.glob("analysis/screenshots/**/*") if path.is_file()]),
        "documents": len([path for path in course_dir.glob("documents/**/*") if path.is_file()]),
        "distillations": len(list(course_dir.glob("course_distillation_*.*"))),
    }


def generated_skills_for_course(output_dir: Path, course_name: str, course_dir: Path) -> list[dict[str, Any]]:
    rows = []
    if not output_dir.exists():
        return rows
    for skill_dir in sorted(path for path in output_dir.iterdir() if path.is_dir()):
        manifest = load_json(skill_dir / "lineage_manifest.json")
        source_dir = manifest.get("source", {}).get("source_dir") or manifest.get("source_dir")
        manifest_course = manifest.get("course", {}).get("name") or manifest.get("course_name")
        if manifest_course != course_name and source_dir != str(course_dir):
            continue
        roles = manifest.get("roles") or manifest.get("course", {}).get("roles") or manifest.get("modes") or manifest.get("course", {}).get("modes") or []
        rows.append(
            {
                "skill_name": skill_dir.name,
                "path": str(skill_dir),
                "roles": roles,
                "modes": roles,
                "scope": manifest.get("scope", ""),
                "evidence_strategy": manifest.get("evidence_strategy", ""),
                "progress_strategy": manifest.get("progress_strategy", ""),
                "generated_at": manifest.get("generated_at", ""),
            }
        )
    return rows


def build_course_row(course_dir: Path, output_dir: Path) -> dict[str, Any]:
    progress = load_json(course_dir / "lineage_progress.json")
    package = load_json(course_dir / "course_package.json")
    manifest = package.get("manifest") if isinstance(package.get("manifest"), dict) else {}
    course_name = progress.get("course_name") or manifest.get("course_name") or course_dir.name
    quality = package.get("quality") if isinstance(package.get("quality"), dict) else {}
    return {
        "course_name": course_name,
        "course_dir": str(course_dir),
        "status": {
            "next_stage": progress.get("next_stage"),
            "artifacts": progress.get("artifacts") or artifact_counts(course_dir),
            "quality": quality,
        },
        "latest": {
            "distillation": latest(["course_distillation_*.md"], course_dir),
            "course_package": "course_package.json" if (course_dir / "course_package.json").exists() else "",
            "progress": "lineage_progress.json" if (course_dir / "lineage_progress.json").exists() else "",
        },
        "generated_skills": generated_skills_for_course(output_dir, course_name, course_dir),
    }


def build_catalog(base_dir: Path, output_dir: Path) -> dict[str, Any]:
    course_dirs = sorted(path for path in base_dir.iterdir() if path.is_dir()) if base_dir.exists() else []
    rows = [build_course_row(course_dir, output_dir) for course_dir in course_dirs]
    return {
        "schema_version": "0.1",
        "generated_at": dt.datetime.now().isoformat(timespec="seconds"),
        "base_dir": str(base_dir),
        "output_dir": str(output_dir),
        "course_count": len(rows),
        "courses": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a catalog for multiple distilled course workspaces.")
    parser.add_argument("--base-dir", default=str(DEFAULT_BASE_DIR), help="Course workspace root. Defaults to ./.lineage/courses.")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="Generated skill output directory. Defaults to ./dist.")
    parser.add_argument("--catalog", help="Output catalog path. Defaults to <base-dir>/course_catalog.json.")
    args = parser.parse_args()

    base_dir = Path(args.base_dir).expanduser().resolve()
    output_dir = Path(args.output_dir).expanduser().resolve()
    catalog_path = Path(args.catalog).expanduser().resolve() if args.catalog else base_dir / "course_catalog.json"
    catalog_path.parent.mkdir(parents=True, exist_ok=True)
    catalog = build_catalog(base_dir, output_dir)
    catalog_path.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {catalog_path}")
    print(f"courses: {catalog['course_count']}")


if __name__ == "__main__":
    main()
