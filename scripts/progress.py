#!/usr/bin/env python3
"""Progress records for Lineage course pipeline runs."""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
from typing import Any


STAGE_ORDER = [
    "transcribe",
    "analyze",
    "keyframes",
    "documents",
    "text_distill",
    "distill",
    "audit",
    "package",
    "teacher_model",
    "capability_graph",
    "practice_bank",
    "assessment_bank",
    "mentor_package",
    "mentor_audit",
    "build_skill",
    "validate_skill",
    "catalog",
]


def now() -> str:
    return dt.datetime.now().isoformat(timespec="seconds")


def progress_path(course_dir: Path) -> Path:
    return course_dir / "lineage_progress.json"


def load_progress(course_dir: Path) -> dict[str, Any]:
    path = progress_path(course_dir)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def summarize_artifacts(course_dir: Path, skill_dir: Path | None = None) -> dict[str, Any]:
    transcripts = sorted(course_dir.glob("transcripts/*_transcript.json"))
    analyses = sorted(course_dir.glob("analysis/*_analysis.md"))
    screenshots = sorted(path for path in course_dir.glob("analysis/screenshots/**/*") if path.is_file())
    keyframe_candidates = sorted(path for path in course_dir.glob("keyframe_candidates/**/*.jpg") if path.is_file())
    model_keyframes = sorted(path for path in course_dir.glob("keyframes_model_selected/**/*.jpg") if path.is_file())
    keyframe_manifests = sorted(course_dir.glob("keyframe_selection/*_model_keyframes_manifest.json"))
    keyframe_summaries = sorted(course_dir.glob("keyframe_selection/model_keyframe_summary.md"))
    document_files = sorted(path for path in course_dir.glob("documents/**/*") if path.is_file())
    text_source_chunks = sorted(course_dir.glob("text_sources/chunks.jsonl"))
    text_cards = sorted(course_dir.glob("text_distillation/evidence_cards.jsonl"))
    text_synthesis = course_dir / "text_distillation" / "text_course_synthesis.md"
    text_quality = course_dir / "text_distillation" / "text_distillation_quality.json"
    distillations = sorted(course_dir.glob("course_distillation_*.*"))
    summary_path = course_dir / "lesson_summaries.json"
    package_path = course_dir / "course_package.json"
    audit_json = course_dir / "distillation_audit.json"
    audit_markdown = course_dir / "distillation_audit.md"
    teacher_model = course_dir / "teacher_model.json"
    capability_graph = course_dir / "capability_graph.json"
    practice_bank = course_dir / "practice_bank.json"
    assessment_bank = course_dir / "assessment_bank.json"
    mentor_package = course_dir / "mentor_package.json"
    mentor_audit_json = course_dir / "mentor_readiness_audit.json"
    mentor_audit_markdown = course_dir / "mentor_readiness_audit.md"
    mineru_manifest = course_dir / "documents" / "mineru_manifest.json"
    mineru_supplement = course_dir / "documents" / "mineru_supplement.md"
    return {
        "transcripts": len(transcripts),
        "visual_analyses": len(analyses),
        "screenshots": len(screenshots),
        "keyframe_candidates": len(keyframe_candidates),
        "model_selected_keyframes": len(model_keyframes),
        "keyframe_manifests": len(keyframe_manifests),
        "keyframe_summaries": len(keyframe_summaries),
        "document_files": len(document_files),
        "text_source_chunks": len(text_source_chunks),
        "text_evidence_cards": len(text_cards),
        "text_synthesis": text_synthesis.exists(),
        "text_distillation_quality": text_quality.exists(),
        "mineru_manifest": mineru_manifest.exists(),
        "mineru_supplement": mineru_supplement.exists(),
        "lesson_summaries": summary_path.exists(),
        "course_distillations": len(distillations),
        "course_package": package_path.exists(),
        "distillation_audit_json": audit_json.exists(),
        "distillation_audit_markdown": audit_markdown.exists(),
        "teacher_model": teacher_model.exists(),
        "capability_graph": capability_graph.exists(),
        "practice_bank": practice_bank.exists(),
        "assessment_bank": assessment_bank.exists(),
        "mentor_package": mentor_package.exists(),
        "mentor_readiness_audit_json": mentor_audit_json.exists(),
        "mentor_readiness_audit_markdown": mentor_audit_markdown.exists(),
        "generated_skill": bool(skill_dir and skill_dir.exists()),
    }


def next_stage(stages: dict[str, Any]) -> str | None:
    for stage in STAGE_ORDER:
        item = stages.get(stage) or {}
        if item.get("status") not in {"completed", "skipped"}:
            return stage
    return None


def write_progress(
    course_dir: Path,
    *,
    course_name: str,
    skill_name: str,
    base_dir: Path,
    output_dir: Path,
    mode: str,
    scope: str | None = None,
    evidence: str | None = None,
    progress_strategy: str | None = None,
    input_dir: str | None = None,
    documents_input: list[str] | None = None,
    stage: str | None = None,
    status: str | None = None,
    command: list[str] | None = None,
    error: str | None = None,
) -> dict[str, Any]:
    course_dir.mkdir(parents=True, exist_ok=True)
    skill_dir = output_dir / skill_name
    data = load_progress(course_dir)
    if not data:
        data = {
            "schema_version": "1.0",
            "created_at": now(),
            "stages": {},
        }
    data.update(
        {
            "updated_at": now(),
            "course_name": course_name,
            "skill_name": skill_name,
            "mode": mode,
            "base_dir": str(base_dir),
            "course_dir": str(course_dir),
            "output_dir": str(output_dir),
            "skill_dir": str(skill_dir),
        }
    )
    if scope is not None:
        data["scope"] = scope
    if evidence is not None:
        data["evidence_strategy"] = evidence
    if progress_strategy is not None:
        data["progress_strategy"] = progress_strategy
        data["pipeline_progress_strategy"] = progress_strategy
        data.setdefault("deprecations", {})["progress_strategy"] = "Use pipeline_progress_strategy for compiler state; learner mastery is external."
    if input_dir is not None:
        data["input_dir"] = input_dir
    if documents_input is not None:
        data["documents_input"] = documents_input
    stages = data.setdefault("stages", {})
    if stage and status:
        item = stages.setdefault(stage, {})
        item["status"] = status
        item["updated_at"] = now()
        if status == "running":
            item.setdefault("started_at", now())
        if status in {"completed", "failed", "skipped"}:
            item["finished_at"] = now()
        if command is not None:
            item["command"] = command
        if error:
            item["error"] = error
        elif "error" in item and status in {"running", "completed", "skipped"}:
            item.pop("error", None)
    data["artifacts"] = summarize_artifacts(course_dir, skill_dir)
    data["next_stage"] = next_stage(stages)
    progress_path(course_dir).write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return data
