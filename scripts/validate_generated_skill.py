#!/usr/bin/env python3
"""Validate generated Skill structure, privacy, runtime assets, and placeholders."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from schema_utils import ValidationIssue, issues_payload, load_json
from stable_ids import content_hash
from validate_mentor_package import validate_mentor


REQUIRED = [
    "SKILL.md",
    "agents/openai.yaml",
    "lineage_manifest.json",
    "references/course_package.json",
    "scripts/search_course_notes.py",
    "scripts/fetch_course_evidence.py",
]
MENTOR_REQUIRED = [
    "mentor_manifest.json",
    "references/teacher_model.json",
    "references/capability_graph.json",
    "references/practice_bank.json",
    "references/assessment_bank.json",
    "references/mentor_package.json",
    "references/mentor_protocol.md",
    "references/graduation_policy.json",
    "references/schemas/apprenticeship_state.schema.json",
    "references/schemas/practice_episode.schema.json",
    "references/schemas/mastery_state.schema.json",
    "references/schemas/personal_skill_candidate.schema.json",
    "scripts/initialize_apprenticeship.py",
    "scripts/record_practice_episode.py",
    "scripts/rebuild_mastery_state.py",
    "scripts/select_next_practice.py",
    "scripts/schedule_retrieval.py",
    "scripts/validate_learner_state.py",
    "scripts/build_personal_skill_candidate.py",
]
PLACEHOLDERS = [re.compile(pattern, re.I) for pattern in [r"\bTODO\b", r"add .+ here", r"implement here", r"rest of code", r"similar to above"]]


def validate_skill(skill_dir: Path) -> dict:
    issues: list[ValidationIssue] = []
    manifest = load_json(skill_dir / "lineage_manifest.json") if (skill_dir / "lineage_manifest.json").exists() else {}
    required = REQUIRED + (MENTOR_REQUIRED if "mentor" in manifest.get("roles", []) else [])
    for relative in required:
        path = skill_dir / relative
        if not path.exists():
            issues.append(ValidationIssue(relative, "required generated Skill artifact is missing"))
        elif path.is_file() and path.stat().st_size == 0:
            issues.append(ValidationIssue(relative, "artifact is empty"))
    skill_md = skill_dir / "SKILL.md"
    if skill_md.exists():
        text = skill_md.read_text(encoding="utf-8", errors="ignore")
        lines = text.splitlines()
        if len(lines) > 500:
            issues.append(ValidationIssue("SKILL.md", f"SKILL.md has {len(lines)} lines; maximum is 500"))
        frontmatter = text.split("---", 2)[1] if text.startswith("---") and text.count("---") >= 2 else ""
        keys = [line.split(":", 1)[0].strip() for line in frontmatter.splitlines() if ":" in line]
        if set(keys) != {"name", "description"}:
            issues.append(ValidationIssue("SKILL.md", f"frontmatter must contain only name and description; got {keys}"))
    for path in skill_dir.rglob("*"):
        if not path.is_file() or any(part in {"transcripts", "analysis", "documents", "keyframes_model_selected"} for part in path.parts):
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if any(pattern.search(text) for pattern in PLACEHOLDERS):
            issues.append(ValidationIssue(str(path.relative_to(skill_dir)), "placeholder pattern found"))
    private_names = {
        "learner_progress.json",
        "apprenticeship_state.json",
        "mastery_state.json",
        "practice_episodes.jsonl",
        "review_queue.json",
        "error_library.json",
        "artifact_index.json",
        "graduation_record.json",
    }
    private_dirs = {"personal_skill_candidates", "apprenticeships", "learner-state", "learner_state"}
    for path in skill_dir.rglob("*"):
        if path.name in private_names or any(part in private_dirs for part in path.relative_to(skill_dir).parts):
            issues.append(ValidationIssue(str(path.relative_to(skill_dir)), "private learner state must remain external"))
    raw_dirs = {"transcripts", "analysis", "documents", "text_sources", "keyframe_selection", "keyframes_model_selected", "source_courses"}
    if manifest.get("source_artifacts_included") is not True:
        for dirname in sorted(raw_dirs):
            if (skill_dir / "references" / dirname).exists():
                issues.append(ValidationIssue(f"references/{dirname}", "raw source artifacts require explicit opt-in"))
    if (skill_dir / "keyframe_candidates").exists() or (skill_dir / "references" / "keyframe_candidates").exists():
        issues.append(ValidationIssue("references/keyframe_candidates", "raw keyframe candidate cache must not be packaged"))
    mentor_path = skill_dir / "references" / "mentor_package.json"
    if mentor_path.exists():
        mentor_result = validate_mentor(mentor_path)
        issues.extend(ValidationIssue(f"mentor:{item['path']}", item["message"], item["severity"]) for item in mentor_result["issues"])
    manifest_path = skill_dir / "lineage_manifest.json"
    if manifest_path.exists():
        if manifest.get("generated_by", {}).get("id") != "lineage-skill":
            issues.append(ValidationIssue("lineage_manifest.json", "generated_by.id must be lineage-skill"))
        for filename, expected_hash in manifest.get("package_hashes", {}).items():
            artifact = skill_dir / "references" / filename
            if not artifact.exists():
                issues.append(ValidationIssue(f"lineage_manifest.json.package_hashes.{filename}", "hashed artifact is missing"))
                continue
            actual_hash = content_hash(load_json(artifact))
            if actual_hash != expected_hash:
                issues.append(ValidationIssue(f"lineage_manifest.json.package_hashes.{filename}", "package hash does not match packaged artifact"))
    if mentor_path.exists():
        mentor = load_json(mentor_path)
        for filename, expected_hash in mentor.get("manifest", {}).get("package_hashes", {}).items():
            artifact = skill_dir / "references" / filename
            if not artifact.exists():
                issues.append(ValidationIssue(f"mentor_package.json.package_hashes.{filename}", "hashed artifact is missing"))
                continue
            actual_hash = content_hash(load_json(artifact))
            if actual_hash != expected_hash:
                issues.append(ValidationIssue(f"mentor_package.json.package_hashes.{filename}", "package hash does not match packaged artifact"))
    result = issues_payload(issues)
    result.update({"skill_dir": str(skill_dir), "required_artifact_count": len(required)})
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate a generated Lineage Skill.")
    parser.add_argument("--skill-dir", required=True)
    args = parser.parse_args()
    result = validate_skill(Path(args.skill_dir).expanduser().resolve())
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if not result["valid"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
