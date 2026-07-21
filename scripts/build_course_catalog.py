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
        "keyframe_candidates": len([path for path in course_dir.glob("keyframe_candidates/**/*.jpg") if path.is_file()]),
        "keyframe_manifests": len(list(course_dir.glob("keyframe_selection/*_model_keyframes_manifest.json"))),
        "keyframe_summaries": len(list(course_dir.glob("keyframe_selection/model_keyframe_summary.md"))),
        "model_selected_keyframes": len([path for path in course_dir.glob("keyframes_model_selected/**/*.jpg") if path.is_file()]),
        "documents": len([path for path in course_dir.glob("documents/**/*") if path.is_file()]),
        "text_source_chunks": len(list(course_dir.glob("text_sources/chunks.jsonl"))),
        "text_evidence_cards": len(list(course_dir.glob("text_distillation/evidence_cards.jsonl"))),
        "text_synthesis": int((course_dir / "text_distillation" / "text_course_synthesis.md").exists()),
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
    teacher = load_json(course_dir / "teacher_model.json")
    graph = load_json(course_dir / "capability_graph.json")
    practice = load_json(course_dir / "practice_bank.json")
    assessment = load_json(course_dir / "assessment_bank.json")
    mentor = load_json(course_dir / "mentor_package.json")
    readiness = load_json(course_dir / "mentor_readiness_audit.json")
    return {
        "course_name": course_name,
        "course_dir": str(course_dir),
        "status": {
            "next_stage": progress.get("next_stage"),
            "artifacts": progress.get("artifacts") or artifact_counts(course_dir),
            "quality": quality,
            "source_readiness": readiness.get("source_readiness", {}).get("status", "unknown"),
            "mentor_readiness": readiness.get("status", "missing"),
            "runtime_readiness": mentor.get("quality", {}).get("runtime_readiness", "missing"),
        },
        "schemas": {
            "course_package": package.get("schema_version"),
            "teacher_model": teacher.get("schema_version"),
            "capability_graph": graph.get("schema_version"),
            "practice_bank": practice.get("schema_version"),
            "assessment_bank": assessment.get("schema_version"),
            "mentor_package": mentor.get("schema_version"),
        },
        "apprenticeship_mode": mentor.get("manifest", {}).get("apprenticeship_mode", "none"),
        "capability_counts": {
            "capabilities": len(graph.get("nodes", [])),
            "tasks": len(practice.get("tasks", [])),
            "rubrics": len(practice.get("rubrics", [])),
            "assessments": len(assessment.get("items", [])),
        },
        "latest": {
            "distillation": latest(["course_distillation_*.md"], course_dir),
            "text_synthesis": latest(["text_distillation/text_course_synthesis.md"], course_dir),
            "course_package": "course_package.json" if (course_dir / "course_package.json").exists() else "",
            "progress": "lineage_progress.json" if (course_dir / "lineage_progress.json").exists() else "",
        },
        "generated_skills": generated_skills_for_course(output_dir, course_name, course_dir),
    }


def build_catalog(base_dir: Path, output_dir: Path) -> dict[str, Any]:
    course_dirs = sorted(path for path in base_dir.iterdir() if path.is_dir()) if base_dir.exists() else []
    rows = [build_course_row(course_dir, output_dir) for course_dir in course_dirs]
    return {
        "schema_version": "1.0",
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
