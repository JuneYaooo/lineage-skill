#!/usr/bin/env python3
"""Build a course-backed Codex skill from prepared course notes.

This builder intentionally starts from already-prepared materials instead of
pretending to solve transcription, OCR, and visual analysis in one script.
It packages the course digest, lesson index, glossary, evidence map, and study
paths into a repeatable skill directory.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import shutil
from pathlib import Path

from build_assessment_bank import build_assessment_bank
from build_capability_graph import build_capability_graph
from build_course_package import build_package
from build_mentor_package import build_mentor_package
from build_practice_bank import build_practice_bank
from build_teacher_model import build_teacher_model, load_course_package
from build_okf_bundle import build_okf_bundle
from schema_utils import load_json as load_schema_json, write_json
from stable_ids import content_hash
from validate_generated_skill import validate_skill


REFERENCE_FILES = [
    "course_digest.md",
    "full_transcript.md",
    "lesson_index.json",
    "concept_glossary.md",
    "evidence_map.json",
    "quote_index.md",
    "study_paths.md",
]

BASE_REFERENCES = [
    "course_package.json",
    "course_digest.md",
    "full_transcript.md",
    "lesson_index.json",
    "concept_glossary.md",
    "evidence_map.json",
    "quote_index.md",
    "study_paths.md",
]

GENERATOR_ID = "lineage-skill"
GENERATOR_REPOSITORY = "https://github.com/JuneYaooo/lineage-skill"
GENERATOR_SCRIPT = "scripts/build_course_skill.py"
GENERATOR_SCHEMA_VERSION = "1.0"
PROVENANCE_WATERMARK = "lineage-skill:cognitive-apprenticeship-builder:v1.0"

MODE_SPECS = {
    "mentor": {
        "label": "Mentor",
        "description": "a source-grounded cognitive apprenticeship mentor for diagnosis, attempt-first practice, feedback, retrieval, transfer, and graduation",
        "focus": [
            "Act as a course-specific mentor grounded in the packaged course materials.",
            "Guide the learner from baseline diagnosis through modeling, coached practice, independent transfer, retention, and graduation.",
            "Ask clarifying or diagnostic questions when the user's goal, level, schedule, or application context is unclear.",
        ],
        "rules": [
            "Use course references first, and distinguish direct course content from mentor-style synthesis.",
            "Route explicit source lookup directly; use attempt-first for learning and training.",
            "Use the lowest effective hint, require revision, and record a PracticeEpisode after every training attempt.",
            "Treat learner state as external private data; never store real learner state in this Skill.",
            "If the course materials do not support a claim, say what is missing.",
        ],
        "extra_refs": {},
    },
    "expert": {
        "label": "Expert",
        "description": "course-grounded explanations, concept clarification, lesson lookup, and source-backed answers",
        "focus": [
            "Answer course questions using packaged references first.",
            "Explain concepts, lessons, themes, cases, quotes, and study paths.",
            "Distinguish course content from your own synthesis.",
        ],
        "rules": [
            "Cite the strongest available source path when answering factual course questions.",
            "For synthesis questions, explain which sources were combined.",
            "If references do not support an answer, say what is missing.",
        ],
        "extra_refs": {},
    },
    "consultant": {
        "label": "Consultant",
        "description": "course-grounded private consulting, scenario diagnosis, strategic analysis, and recommendations",
        "focus": [
            "Use course methods to analyze the user's concrete situation.",
            "Diagnose problems, name assumptions, compare options, and recommend next steps grounded in the course.",
            "Separate direct course guidance from adapted consulting judgment.",
        ],
        "rules": [
            "Ask for missing context before making high-impact recommendations.",
            "Label adaptations to the user's situation as inference.",
            "Do not present generic advice as if it came from the course.",
            "Respect professional boundaries in high-stakes domains.",
        ],
        "extra_refs": {
            "consulting_playbook.md": "Use CoursePackage diagnostics and decision rules to collect context, name assumptions, compare source-supported options, label adaptations as inference, and request evidence before high-impact recommendations.",
            "scenario_templates.md": "Structure each analysis as situation, observable evidence, constraints, source-grounded diagnosis, options, trade-offs, recommendation, uncertainty, and next verification action.",
        },
    },
    "practitioner": {
        "label": "Practitioner",
        "description": "course-grounded execution support, checklists, playbooks, templates, workflows, and practical outputs",
        "focus": [
            "Convert course methods into usable workflows, checklists, templates, and decision aids.",
            "Use course cases as application examples.",
            "Help users produce drafts, SOPs, briefs, plans, scripts, tables, or other work artifacts.",
        ],
        "rules": [
            "Prefer actionable steps backed by course references.",
            "When adapting a method to a new situation, label the adaptation as inference.",
            "Do not present generic advice as if it came from the course.",
        ],
        "extra_refs": {
            "playbooks.md": "Derive each operating procedure from CoursePackage workflows: trigger, inputs, ordered decisions/actions, output, evaluator, evidence, applicability conditions, and failure modes.",
            "checklists.md": "Build checklists only from packaged rubrics and workflows. Keep source evidence and mark every adapted item as inference.",
            "templates.md": "Use packaged templates when available. Otherwise derive the smallest structure needed for an observable output and label it as a course-grounded adaptation.",
            "case_index.json": {"cases": [], "notes": "Index examples, demos, stories, and practical applications."},
        },
    },
    "custom": {
        "label": "Custom",
        "description": "a user-defined course-backed Skill role based on the user's stated workflow",
        "focus": [
            "Follow the user's custom role and workflow while staying grounded in course materials.",
            "Translate the course package into the custom behavior, outputs, and boundaries requested by the user.",
            "Keep source-course distinctions when the package contains multiple courses.",
        ],
        "rules": [
            "Write the custom role, expected outputs, and boundaries into the generated Skill references.",
            "Distinguish direct course content, course-grounded synthesis, and custom adaptation.",
            "If the custom behavior needs information not present in the course package, say what is missing.",
        ],
        "extra_refs": {
            "custom_role.md": "Follow the user-defined role only within packaged evidence and explicit professional boundaries. Record its use cases, outputs, and limits in the current response when they are supplied.",
            "custom_workflows.md": "Compose custom workflows from packaged capabilities while keeping teacher rules, cross-source synthesis, and custom adaptation visibly separate.",
        },
    },
}

MODE_ALIASES = {
    "course-expert": "expert",
    "study-coach": "mentor",
    "citation-archive": "expert",
    "knowledge-base": "expert",
    "domain-expert": "expert",
}

ALIAS_OPTIONS = {
    "citation-archive": {"evidence": "strict"},
    "knowledge-base": {"scope": "multi-course"},
    "domain-expert": {"scope": "fused"},
    "study-coach": {"progress": "tracked"},
}

VALID_SCOPES = {"single-course", "multi-course", "fused", "auto"}
VALID_EVIDENCE = {"standard", "strict"}
VALID_PROGRESS = {"none", "tracked", "auto"}
VALID_APPRENTICESHIP = {"none", "guided", "full"}
RUNTIME_SCRIPTS = [
    "runtime_state.py",
    "initialize_apprenticeship.py",
    "record_practice_episode.py",
    "rebuild_mastery_state.py",
    "select_next_practice.py",
    "schedule_retrieval.py",
    "validate_learner_state.py",
    "build_personal_skill_candidate.py",
]
MENTOR_ARTIFACTS = [
    "teacher_model.json",
    "capability_graph.json",
    "practice_bank.json",
    "assessment_bank.json",
    "mentor_package.json",
    "mentor_protocol.md",
    "graduation_policy.json",
    "mentor_readiness_audit.json",
    "mentor_readiness_audit.md",
]


def newest_match(source_dir: Path, pattern: str) -> Path | None:
    matches = sorted(source_dir.glob(pattern), key=lambda path: path.stat().st_mtime, reverse=True)
    return matches[0] if matches else None


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9\u4e00-\u9fff_-]+", "-", value.strip()).strip("-")
    return slug.lower() or "course-skill"


def read_text_if_exists(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def load_json_if_exists(path: Path) -> object | None:
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def find_first_existing(source_dir: Path, names: list[str]) -> Path | None:
    for name in names:
        candidate = source_dir / name
        if candidate.exists():
            return candidate
    return None


def find_course_distillation_md(source_dir: Path) -> Path | None:
    return find_first_existing(source_dir, ["course_digest.md", "course_distillation.md"]) or newest_match(
        source_dir, "course_distillation_*.md"
    )


def find_course_distillation_json(source_dir: Path) -> Path | None:
    return find_first_existing(source_dir, ["course_distillation.json"]) or newest_match(source_dir, "course_distillation_*.json")


def copy_or_stub(source: Path | None, destination: Path, title: str, body: str) -> str:
    if source and source.exists():
        shutil.copy2(source, destination)
        return "copied"
    destination.write_text(f"# {title}\n\n{body}\n", encoding="utf-8")
    return "generated-fallback"


def normalize_lessons(data: object | None) -> list[dict[str, object]]:
    if data is None:
        return []
    if isinstance(data, list):
        lessons = data
    elif isinstance(data, dict):
        lessons = data.get("lessons") or data.get("lesson_summaries") or []
    else:
        lessons = []

    normalized = []
    for idx, item in enumerate(lessons, start=1):
        if isinstance(item, dict):
            title = item.get("title") or item.get("lesson_name") or item.get("name") or f"Lesson {idx}"
            normalized.append(
                {
                    "id": item.get("id") or f"lesson-{idx:03d}",
                    "title": title,
                    "summary": item.get("summary") or item.get("abstract") or "",
                    "topics": item.get("topics") or item.get("keywords") or [],
                    "source": item.get("source") or item.get("file") or "",
                }
            )
        else:
            normalized.append({"id": f"lesson-{idx:03d}", "title": str(item), "summary": "", "topics": [], "source": ""})
    return normalized


def extract_markdown_section(text: str, title_keyword: str) -> str:
    pattern = rf"(^##+\s*[^\n]*{re.escape(title_keyword)}[^\n]*\n)([\s\S]*?)(?=^##+\s+|\Z)"
    match = re.search(pattern, text, flags=re.M)
    if not match:
        return ""
    return match.group(0).strip() + "\n"


def write_derived_markdown(
    source_dir: Path,
    destination: Path,
    title: str,
    section_keywords: list[str],
    fallback: str,
) -> str:
    existing = find_first_existing(source_dir, [destination.name])
    if existing:
        shutil.copy2(existing, destination)
        return "copied"

    digest_path = find_course_distillation_md(source_dir)
    digest_text = read_text_if_exists(digest_path) if digest_path else ""
    sections = []
    for keyword in section_keywords:
        section = extract_markdown_section(digest_text, keyword)
        if section:
            sections.append(section)
    if sections:
        destination.write_text(f"# {title}\n\n" + "\n\n".join(sections).strip() + "\n", encoding="utf-8")
        return "derived"

    destination.write_text(f"# {title}\n\n{fallback}\n", encoding="utf-8")
    return "generated-fallback"


def build_lesson_index(source_dir: Path, destination: Path) -> str:
    existing = find_first_existing(source_dir, ["lesson_index.json"])
    if existing:
        shutil.copy2(existing, destination)
        return "copied"

    summary_path = find_first_existing(source_dir, ["lesson_summaries.json"]) or find_course_distillation_json(source_dir)
    lessons = normalize_lessons(load_json_if_exists(summary_path) if summary_path else None)
    payload = {
        "generated_at": dt.datetime.now().isoformat(timespec="seconds"),
        "lesson_count": len(lessons),
        "lessons": lessons,
    }
    destination.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return "generated" if lessons else "generated-empty-index"


def build_evidence_map(source_dir: Path, destination: Path, *, include_source_artifacts: bool = False) -> str:
    existing = find_first_existing(source_dir, ["evidence_map.json"])
    if existing and include_source_artifacts:
        shutil.copy2(existing, destination)
        return "copied"

    transcript_files = sorted(str(p.relative_to(source_dir)) for p in source_dir.glob("transcripts/**/*.json"))
    analysis_files = sorted(str(p.relative_to(source_dir)) for p in source_dir.glob("analysis/**/*_analysis.md"))
    screenshot_files = sorted(str(p.relative_to(source_dir)) for p in source_dir.glob("analysis/screenshots/**/*") if p.is_file())
    keyframe_manifests = sorted(str(p.relative_to(source_dir)) for p in source_dir.glob("keyframe_selection/*_model_keyframes_manifest.json"))
    keyframe_summaries = sorted(str(p.relative_to(source_dir)) for p in source_dir.glob("keyframe_selection/model_keyframe_summary.md"))
    selected_keyframes = sorted(str(p.relative_to(source_dir)) for p in source_dir.glob("keyframes_model_selected/**/*") if p.is_file())
    course_distillations = sorted(str(p.relative_to(source_dir)) for p in source_dir.glob("course_distillation_*.*"))
    document_files = sorted(str(p.relative_to(source_dir)) for p in source_dir.glob("documents/**/*") if p.is_file())
    text_source_files = sorted(str(p.relative_to(source_dir)) for p in source_dir.glob("text_sources/**/*") if p.is_file())
    text_distillation_files = sorted(str(p.relative_to(source_dir)) for p in source_dir.glob("text_distillation/**/*") if p.is_file())
    package = load_json_if_exists(source_dir / "course_package.json")
    packaged_evidence = []
    if isinstance(package, dict):
        for item in package.get("evidence", []):
            if not isinstance(item, dict):
                continue
            packaged_evidence.append(
                {
                    key: value
                    for key, value in item.items()
                    if key not in {"path", "source_dir", "local_path"}
                }
            )
    payload = {
        "generated_at": dt.datetime.now().isoformat(timespec="seconds"),
        "privacy_mode": "source-artifacts-included" if include_source_artifacts else "paths-withheld",
        "transcripts": transcript_files if include_source_artifacts else [],
        "analysis_files": analysis_files if include_source_artifacts else [],
        "screenshots": screenshot_files if include_source_artifacts else [],
        "model_keyframe_manifests": keyframe_manifests if include_source_artifacts else [],
        "model_keyframe_summaries": keyframe_summaries if include_source_artifacts else [],
        "model_selected_keyframes": selected_keyframes if include_source_artifacts else [],
        "course_distillations": course_distillations if include_source_artifacts else [],
        "documents": document_files if include_source_artifacts else [],
        "text_sources": text_source_files if include_source_artifacts else [],
        "text_distillation": text_distillation_files if include_source_artifacts else [],
        "packaged_evidence": packaged_evidence,
        "notes": [
            "Raw local paths and source bodies are withheld by default.",
            "Use stable evidence IDs for traceability; opt in to source artifacts only with authorization.",
        ],
    }
    destination.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return "generated"


def copy_optional_reference_dirs(source_dir: Path, references_dir: Path) -> dict[str, str]:
    statuses = {}
    for dirname in [
        "transcripts",
        "analysis",
        "documents",
        "text_sources",
        "text_distillation",
        "keyframe_selection",
        "keyframes_model_selected",
    ]:
        src = source_dir / dirname
        dst = references_dir / dirname
        if not src.exists():
            continue
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(
            src,
            dst,
            ignore=shutil.ignore_patterns(
                "__pycache__",
                "*.mp4",
                "*.m4s",
                "*.mp3",
                "*.wav",
                "*.mov",
                "*.mkv",
                "*.webm",
            ),
        )
        statuses[f"{dirname}/"] = "copied"
    return statuses


def copy_optional_reference_files(source_dir: Path, references_dir: Path) -> dict[str, str]:
    statuses = {}
    for filename in ["distillation_audit.json", "distillation_audit.md"]:
        src = source_dir / filename
        if not src.exists():
            continue
        destination = references_dir / filename
        if src.suffix == ".json":
            payload = load_schema_json(src)
            if isinstance(payload, dict):
                for key in ["source_dir", "course_dir", "base_dir", "output_dir"]:
                    if key in payload:
                        payload[key] = "<withheld-local-path>"
            write_json(destination, payload)
        else:
            text = src.read_text(encoding="utf-8", errors="ignore")
            text = text.replace(str(source_dir), "<withheld-local-path>")
            destination.write_text(text, encoding="utf-8")
        statuses[filename] = "copied"
    return statuses


def copy_source_courses_from_package(source_dir: Path, references_dir: Path) -> dict[str, str]:
    package = load_json_if_exists(source_dir / "course_package.json")
    manifest = package.get("manifest", {}) if isinstance(package, dict) and isinstance(package.get("manifest"), dict) else {}
    source_courses = manifest.get("source_courses") if isinstance(manifest.get("source_courses"), list) else []
    if not source_courses:
        return {}

    source_courses_dir = references_dir / "source_courses"
    if source_courses_dir.exists():
        shutil.rmtree(source_courses_dir)
    source_courses_dir.mkdir(parents=True, exist_ok=True)

    statuses = {}
    for course in source_courses:
        if not isinstance(course, dict) or not course.get("source_dir"):
            continue
        src = Path(str(course["source_dir"])).expanduser().resolve()
        if not src.exists() or not src.is_dir():
            statuses[f"source_courses/{src.name}/"] = "missing"
            continue
        dst = source_courses_dir / src.name
        shutil.copytree(
            src,
            dst,
            ignore=shutil.ignore_patterns(
                "__pycache__",
                "*.mp4",
                "*.m4s",
                "*.mp3",
                "*.wav",
                "*.mov",
                "*.mkv",
                "*.webm",
            ),
        )
        statuses[f"source_courses/{src.name}/"] = "copied"
    return statuses


def sanitize_course_package(package: dict[str, object]) -> dict[str, object]:
    """Remove host-local paths while preserving stable evidence identity."""
    payload = json.loads(json.dumps(package, ensure_ascii=False))
    manifest = payload.get("manifest", {}) if isinstance(payload.get("manifest"), dict) else {}
    for key in ["source_dir", "package_path", "source_path"]:
        manifest.pop(key, None)
    for course in manifest.get("source_courses", []) if isinstance(manifest.get("source_courses"), list) else []:
        if isinstance(course, dict):
            for key in ["source_dir", "package_path", "source_path"]:
                course.pop(key, None)
    for item in payload.get("sources", []) if isinstance(payload.get("sources"), list) else []:
        if isinstance(item, dict) and item.get("id"):
            item["path"] = f"withheld://source/{item['id']}"
    for item in payload.get("evidence", []) if isinstance(payload.get("evidence"), list) else []:
        if isinstance(item, dict) and item.get("id"):
            item["path"] = f"withheld://evidence/{item['id']}"
    for item in payload.get("lessons", []) if isinstance(payload.get("lessons"), list) else []:
        if isinstance(item, dict) and item.get("source"):
            item["source"] = f"withheld://lesson/{item.get('id', 'unknown')}"
    return payload


def copy_course_package(source_dir: Path, destination: Path, *, include_source_artifacts: bool = False) -> str:
    existing = find_first_existing(source_dir, ["course_package.json"])
    if existing:
        package = load_schema_json(existing)
        write_json(destination, package if include_source_artifacts else sanitize_course_package(package))
        return "copied" if include_source_artifacts else "copied-paths-withheld"
    payload = {
        "schema_version": "0.1",
        "manifest": {
            "source_dir": str(source_dir),
            "generated_at": dt.datetime.now().isoformat(timespec="seconds"),
            "note": "Run scripts/build_course_package.py to generate a normalized package.",
        },
        "lessons": [],
        "concepts": [],
        "topics": [],
        "cases": [],
        "methods": [],
        "diagnostics": [],
        "workflows": [],
        "rubrics": [],
        "templates": [],
        "transfer_rules": [],
        "failure_modes": [],
        "learning_checks": [],
        "quotes": [],
        "evidence": [],
        "study_paths": [],
        "boundaries": [],
    }
    destination.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return "generated-empty-package"


def parse_modes(raw_modes: str) -> list[str]:
    modes = []
    for raw in [mode.strip() for mode in raw_modes.split(",") if mode.strip()]:
        mode = MODE_ALIASES.get(raw, raw)
        if mode not in modes:
            modes.append(mode)
    if not modes:
        modes = ["mentor"]
    unknown = [mode for mode in modes if mode not in MODE_SPECS]
    if unknown:
        valid = ", ".join(sorted(MODE_SPECS))
        raise SystemExit(f"unknown role(s): {', '.join(unknown)}. valid roles: {valid}")
    return modes


def alias_options(raw_modes: str) -> dict[str, str]:
    options = {}
    for raw in [mode.strip() for mode in raw_modes.split(",") if mode.strip()]:
        options.update(ALIAS_OPTIONS.get(raw, {}))
    return options


def detect_scope(source_dir: Path) -> str:
    package = load_json_if_exists(source_dir / "course_package.json")
    manifest = package.get("manifest", {}) if isinstance(package, dict) and isinstance(package.get("manifest"), dict) else {}
    package_type = manifest.get("package_type")
    if package_type == "multi-course":
        return "multi-course"
    if manifest.get("source_courses"):
        return "multi-course"
    return "single-course"


def resolve_options(
    source_dir: Path,
    modes: list[str],
    raw_modes: str,
    scope: str,
    evidence: str,
    progress: str,
) -> dict[str, str]:
    if scope not in VALID_SCOPES:
        raise SystemExit(f"unknown scope: {scope}. valid scopes: {', '.join(sorted(VALID_SCOPES))}")
    if evidence not in VALID_EVIDENCE:
        raise SystemExit(f"unknown evidence strategy: {evidence}. valid evidence strategies: {', '.join(sorted(VALID_EVIDENCE))}")
    if progress not in VALID_PROGRESS:
        raise SystemExit(f"unknown progress strategy: {progress}. valid progress strategies: {', '.join(sorted(VALID_PROGRESS))}")

    options = alias_options(raw_modes)
    resolved_scope = options.get("scope", scope)
    if resolved_scope == "auto":
        resolved_scope = detect_scope(source_dir)

    resolved_progress = options.get("progress", progress)
    if resolved_progress == "auto":
        resolved_progress = "tracked" if "mentor" in modes else "none"

    return {
        "scope": resolved_scope,
        "evidence": options.get("evidence", evidence),
        "progress": resolved_progress,
    }


def default_skill_name(course_name: str, modes: list[str]) -> str:
    slug = slugify(course_name)
    if "custom" in modes:
        suffix = "custom"
    elif "consultant" in modes:
        suffix = "consultant"
    elif "mentor" in modes:
        suffix = "mentor"
    elif "practitioner" in modes:
        suffix = "practitioner"
    elif "expert" in modes:
        suffix = "expert"
    else:
        suffix = "mentor"
    lineage_suffix = f"{suffix}-lineage"
    if slug.endswith(f"-{lineage_suffix}"):
        return slug
    if slug.endswith(f"-{suffix}"):
        return f"{slug}-lineage"
    if slug.endswith("-lineage"):
        slug = slug[: -len("-lineage")]
    return f"{slug}-{lineage_suffix}"


def build_skill_md(
    course_name: str,
    skill_name: str,
    description: str,
    modes: list[str],
    destination: Path,
    *,
    apprenticeship_mode: str = "none",
) -> None:
    mode_specs = [MODE_SPECS[mode] for mode in modes]
    mode_labels = ", ".join(spec["label"] for spec in mode_specs)
    mode_descriptions = "; ".join(spec["description"] for spec in mode_specs)
    focus_lines = "\n".join(
        f"- **{spec['label']}**: " + " ".join(spec["focus"])
        for spec in mode_specs
    )
    rule_lines = []
    for spec in mode_specs:
        rule_lines.append(f"### {spec['label']}")
        rule_lines.extend(f"- {rule}" for rule in spec["rules"])
        rule_lines.append("")
    rules = "\n".join(rule_lines).rstrip()

    mentor_runtime = ""
    if "mentor" in modes:
        mentor_runtime = f"""
## Mentor Runtime

This package runs in `{apprenticeship_mode}` apprenticeship mode. Read `references/mentor_package.json`, `references/mentor_protocol.md`, `references/capability_graph.json`, `references/practice_bank.json`, `references/assessment_bank.json`, and `references/graduation_policy.json` before training.

Route each request as source lookup, direct explanation, diagnostic learning, guided practice, artifact feedback, real-world application, retrieval review, transfer test, or graduation test.

- Answer explicit source lookup directly and do not count it as mastery evidence.
- Honor an explicit direct-answer request, but say that it creates no mastery evidence.
- For learning, review, transfer, and graduation, collect a prediction or observable attempt before explanation.
- Evaluate the artifact against criterion-level rubrics; give the lowest effective H0-H4 hint and require a concrete revision.
- Advance a capability by at most one evidence state. Transfer requires H0 success in a changed context; retention requires delayed parallel-form retrieval.
- Fade templates, hints, and intervention timing one dimension at a time as independent success accumulates.
- Keep `[Teacher source]`, `[Source-grounded synthesis]`, `[Mentor inference]`, `[Learner hypothesis]`, and `[Learner real-world evidence]` distinct.

Learner state is external and private. Resolve the host-provided learner store as `{{learner_store_root}}/apprenticeships/{{mentor_package_id}}/`. Never write real learner data under `references/`. Initialize it with `scripts/initialize_apprenticeship.py`; append attempts with `scripts/record_practice_episode.py`; rebuild derived mastery with `scripts/rebuild_mastery_state.py`; schedule reviews and choose next practice with the provided runtime scripts. If the host cannot write state, return a complete JSON patch and state clearly that it was not persisted.

For high-risk medical, legal, financial, investment, or safety-sensitive materials, keep practice educational and source-bounded. Graduation shows competence with the packaged method, not professional licensure.
"""

    content = f"""---
name: {skill_name}
description: Use this skill when the user asks about {course_name} and needs packaged-course support for: {mode_descriptions}.
---

# {course_name}

You are a course-grounded skill for `{course_name}`.

Active role(s): {mode_labels}.

## Scope

- Answer questions using the files in `references/` first.
- Distinguish course content from your own inference.
- Prefer precise lesson, transcript, analysis, screenshot, or quote references when available.
- If the packaged materials do not support an answer, say what is missing instead of inventing details.
- For visual claims, prefer model-selected keyframes when available; cite the image path, approximate timestamp, and manifest path.

## Role Focus

{focus_lines}

## Reference Priority

1. `references/okf/index.md` for progressive reading, human-readable concept files, and cross-linked capability navigation.
2. `references/course_package.json` for normalized claims, capabilities, sources, and evidence pointers.
3. `references/teacher_model.json` for source-supported teacher cues, decisions, demonstrations, feedback, and boundaries.
4. `references/capability_graph.json`, `references/practice_bank.json`, and `references/assessment_bank.json` for observable training and assessment.
5. `references/course_digest.md`, `references/lesson_index.json`, `references/concept_glossary.md`, and `references/evidence_map.json` for human-readable navigation.
6. `references/distillation_audit.*` and `references/mentor_readiness_audit.*` for missing evidence, conflicts, and allowed apprenticeship mode.
7. `references/text_distillation/`, `references/text_sources/`, `references/transcripts/`, `references/analysis/`, `references/documents/`, and model-selected keyframes for exact evidence when present.

## Capability Reading Strategy

- For progressive reading, start with `references/okf/index.md`, open only the relevant OKF section index, then read individual concept files.
- For factual questions, start with `references/course_package.json`, then use `references/evidence_map.json` and `scripts/search_course_notes.py` to locate supporting lessons, cards, transcripts, documents, or chunks.
- Check `references/distillation_audit.md` or `references/distillation_audit.json` before treating a lesson as complete. Respect its `audit_mode` and per-lesson `cross_validation.policy`: cross-source validation is required only when comparable sources are available in auto mode, or when strict audit mode says it is required.
- For application, consulting, or output-producing requests, prioritize `methods`, `diagnostics`, `workflows`, `rubrics`, `templates`, `transfer_rules`, and `failure_modes` from `references/course_package.json`.
- Use `references/text_distillation/evidence_cards.jsonl` to separate direct source cards from your own synthesis.
- Use OKF `# Citations` links for readable provenance, and use JSON/script lookup when exact source spans are required.
- Use `scripts/fetch_course_evidence.py` with a chunk, card, claim, capability, rule, task, rubric, or assessment ID when exact provenance matters.
- In multi-course packages, preserve `source_course` and `source_course_id` distinctions. If sources disagree, report the disagreement instead of flattening it into one claim.
- Label adapted recommendations as inference. Do not present generic model knowledge or unsupported extrapolation as course content.

## Response Rules

{rules}

{mentor_runtime}

## General Boundaries

- Keep professional boundaries: this skill supports study, review, knowledge retrieval, and course-grounded application; it does not replace domain-specific professional advice.
- Do not present generic model knowledge as if it came from the course.
- When adapting course material to a new situation, label the adaptation as inference.

## Course Note

{description}
"""
    destination.write_text(content, encoding="utf-8")


def build_search_script(destination: Path) -> None:
    content = '''#!/usr/bin/env python3
"""Keyword search over packaged course references and evidence cards."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        if not line.strip():
            continue
        item = json.loads(line)
        if isinstance(item, dict):
            rows.append(item)
    return rows


def card_text(card: dict) -> str:
    return " ".join(str(card.get(key) or "") for key in ["card_type", "title", "summary", "quote", "source_ref", "chunk_id"])


def main() -> None:
    parser = argparse.ArgumentParser(description="Search course reference files.")
    parser.add_argument("query", help="Keyword to search for.")
    parser.add_argument("--references-dir", default="../references", help="Reference directory relative to this script.")
    parser.add_argument("--type", dest="card_type", help="Filter evidence cards by card_type, e.g. method, diagnostic, rubric.")
    args = parser.parse_args()

    base = (Path(__file__).resolve().parent / args.references_dir).resolve()
    query = args.query.lower()
    matches = []

    cards = read_jsonl(base / "text_distillation" / "evidence_cards.jsonl")
    for card in cards:
        if args.card_type and card.get("card_type") != args.card_type:
            continue
        text = card_text(card)
        if query in text.lower():
            source = card.get("source_ref", "")
            chunk = card.get("chunk_id", "")
            title = card.get("title", "")
            summary = card.get("quote") or card.get("summary", "")
            print(f"card:{card.get('card_id', '')}:{card.get('card_type', '')}:{source}:{chunk}: {title} {summary}".strip())

    for path in sorted(base.rglob("*")):
        if not path.is_file():
            continue
        if path.name == "evidence_cards.jsonl" and args.card_type:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for line_no, line in enumerate(text.splitlines(), start=1):
            if query in line.lower():
                matches.append((path.relative_to(base), line_no, line.strip()))

    for rel_path, line_no, line in matches[:80]:
        print(f"{rel_path}:{line_no}: {line}")

    if len(matches) > 80:
        print(f"... {len(matches) - 80} more matches")


if __name__ == "__main__":
    main()
'''
    destination.write_text(content, encoding="utf-8")
    destination.chmod(0o755)


def build_fetch_evidence_script(destination: Path) -> None:
    source = Path(__file__).resolve().parent / "fetch_course_evidence.py"
    shutil.copy2(source, destination)
    destination.chmod(0o755)


def ensure_mentor_artifacts(
    source_dir: Path,
    *,
    apprenticeship: str,
    evidence: str,
    practice_depth: str,
) -> dict[str, object]:
    package = load_course_package(source_dir / "course_package.json")
    write_json(source_dir / "course_package.json", package)
    teacher = build_teacher_model(package)
    graph = build_capability_graph(package)
    practice = build_practice_bank(package, graph, depth=practice_depth)
    assessment = build_assessment_bank(package, graph)
    write_json(source_dir / "teacher_model.json", teacher)
    write_json(source_dir / "capability_graph.json", graph)
    write_json(source_dir / "practice_bank.json", practice)
    write_json(source_dir / "assessment_bank.json", assessment)
    mentor = build_mentor_package(source_dir, requested_mode=apprenticeship, evidence_strategy=evidence)
    audit = load_schema_json(source_dir / "mentor_readiness_audit.json")
    package["quality"]["coverage"]["teacher_model_coverage"] = teacher["quality"]["record_count"]
    package["quality"]["coverage"]["practice_coverage"] = practice["quality"]["capability_coverage"]
    package["quality"]["coverage"]["assessment_coverage"] = assessment["quality"]["capability_coverage"]
    package["quality"]["mentor_readiness"] = {
        "status": audit["status"],
        "missing_requirements": audit["blockers"],
        "human_review_required": audit["human_review_required"],
    }
    write_json(source_dir / "course_package.json", package)
    return {"mentor_package": mentor, "readiness": audit}


def copy_mentor_runtime(source_dir: Path, references_dir: Path, scripts_dir: Path, assets_dir: Path) -> dict[str, str]:
    statuses: dict[str, str] = {}
    for filename in MENTOR_ARTIFACTS:
        source = source_dir / filename
        if source.exists():
            shutil.copy2(source, references_dir / filename)
            statuses[filename] = "copied"
    packaged_mentor_path = references_dir / "mentor_package.json"
    packaged_course_path = references_dir / "course_package.json"
    if packaged_mentor_path.exists() and packaged_course_path.exists():
        packaged_mentor = load_schema_json(packaged_mentor_path)
        packaged_mentor.setdefault("manifest", {}).setdefault("package_hashes", {})["course_package.json"] = content_hash(
            load_schema_json(packaged_course_path)
        )
        write_json(packaged_mentor_path, packaged_mentor)
    schema_dir = references_dir / "schemas"
    schema_dir.mkdir(parents=True, exist_ok=True)
    for filename in [
        "apprenticeship_state.schema.json",
        "practice_episode.schema.json",
        "mastery_state.schema.json",
        "personal_skill_candidate.schema.json",
    ]:
        shutil.copy2(Path(__file__).resolve().parents[1] / "references" / "schemas" / filename, schema_dir / filename)
        statuses[f"schemas/{filename}"] = "copied"
    for filename in RUNTIME_SCRIPTS:
        shutil.copy2(Path(__file__).resolve().parent / filename, scripts_dir / filename)
        (scripts_dir / filename).chmod(0o755)
        statuses[f"scripts/{filename}"] = "copied"
    assets_dir.mkdir(parents=True, exist_ok=True)
    mentor = load_schema_json(packaged_mentor_path)
    templates = {
        "learning_contract.template.json": mentor["learning_contract_template"],
        "practice_episode.template.json": {
            "schema_version": "1.0",
            "episode_id": "episode_<stable-id>",
            "mentor_package_id": mentor["manifest"]["mentor_package_id"],
            "learner_id": "<host-private-id>",
            "timestamp_start": "<ISO-8601>",
            "timestamp_end": None,
            "stage": "coached_practice",
            "task_id": "<task-id>",
            "capability_ids": ["<capability-id>"],
            "context": {"project": "", "environment": "", "constraints": []},
            "prediction": {"learner_prediction": "", "confidence_before": None},
            "attempts": [{"attempt_number": 1, "artifact_ref": "", "content_summary": "", "timestamp": "<ISO-8601>"}],
            "hints": [],
            "feedback": {"rubric_results": [], "source_evidence": [], "mentor_inference": "", "next_revision": ""},
            "outcome": {"task_result": "insufficient_evidence", "real_world_result": None, "confidence_after": None, "learner_reflection": ""},
            "errors": [],
            "mastery_events": [],
            "next_actions": [],
            "provenance": "learner_observation",
        },
    }
    for filename, payload in templates.items():
        write_json(assets_dir / filename, payload)
        statuses[f"assets/{filename}"] = "generated"
    (assets_dir / "graduation_report.template.md").write_text(
        "# Graduation Record\n\n## Capabilities\n\n## Delayed retention evidence\n\n## Transfer contexts\n\n## Independent artifacts\n\n## Boundaries and remaining gaps\n\n## Personal Skill candidates\n\n## Differences from teacher methods\n\n## Continuing practice\n",
        encoding="utf-8",
    )
    statuses["assets/graduation_report.template.md"] = "generated"
    return statuses


def yaml_quote(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def build_agent_metadata(course_name: str, skill_name: str, modes: list[str], agents_dir: Path) -> None:
    agents_dir.mkdir(parents=True, exist_ok=True)
    mode_labels = ", ".join(MODE_SPECS[mode]["label"] for mode in modes)
    display_name = f"{course_name} Course Skill"
    short_description = "Source-grounded cognitive apprenticeship and course evidence."
    default_prompt = f"Use ${skill_name} to help me form an independent capability from {course_name} through source-grounded practice, feedback, retrieval, and transfer."

    openai_yaml = "\n".join(
        [
            "interface:",
            f"  display_name: {yaml_quote(display_name)}",
            f"  short_description: {yaml_quote(short_description)}",
            f"  default_prompt: {yaml_quote(default_prompt)}",
            "",
            "policy:",
            "  allow_implicit_invocation: true",
            "",
        ]
    )
    (agents_dir / "openai.yaml").write_text(openai_yaml, encoding="utf-8")

    openclaw_yaml = "\n".join(
        [
            "interface:",
            f"  display_name: {yaml_quote(display_name)}",
            f"  short_description: {yaml_quote(short_description)}",
            f"  default_prompt: {yaml_quote(default_prompt.replace('$', ''))}",
            "",
            "# Trust surface:",
            "#   - Reads packaged course reference files under references/.",
            "#   - Runs local scripts/search_course_notes.py for lightweight keyword lookup.",
            "#   - Reads and writes learner state only in a host-provided external private directory.",
            "#   - Never treats learner evidence as a mutation of the immutable teacher package.",
            "#   - Does not call external services unless the host agent chooses to enrich or rebuild materials.",
            f"#   - Active role(s): {mode_labels}.",
            "",
        ]
    )
    (agents_dir / "openclaw.yaml").write_text(openclaw_yaml, encoding="utf-8")


def write_extra_reference(destination: Path, value: object) -> str:
    if destination.exists():
        return "exists"
    if isinstance(value, dict):
        destination.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    else:
        title = destination.stem.replace("_", " ").replace("-", " ").title()
        destination.write_text(f"# {title}\n\n{value}\n", encoding="utf-8")
    return "generated"


def write_mode_references(references_dir: Path, modes: list[str]) -> dict[str, str]:
    statuses = {}
    for mode in modes:
        for filename, value in MODE_SPECS[mode]["extra_refs"].items():
            statuses[filename] = write_extra_reference(references_dir / filename, value)
    return statuses


def build_lineage_manifest(
    course_name: str,
    skill_name: str,
    modes: list[str],
    source_dir: Path,
    statuses: dict[str, str],
    options: dict[str, str],
    mentor_package: dict[str, object] | None = None,
) -> dict[str, object]:
    generated_at = dt.datetime.now().isoformat(timespec="seconds")
    package_hashes = {
        name: content_hash(load_schema_json(source_dir / name))
        for name in [
            "course_package.json",
            "teacher_model.json",
            "capability_graph.json",
            "practice_bank.json",
            "assessment_bank.json",
            "mentor_package.json",
        ]
        if (source_dir / name).exists()
    }
    return {
        "schema_version": GENERATOR_SCHEMA_VERSION,
        "course_name": course_name,
        "skill_name": skill_name,
        "roles": modes,
        "modes": modes,
        "scope": options["scope"],
        "evidence_strategy": options["evidence"],
        "progress_strategy": options["progress"],
        "pipeline_progress_strategy": options["progress"],
        "learner_state_strategy": options.get("learner_state", "external" if "mentor" in modes else "none"),
        "source_artifacts_included": options.get("include_source_artifacts") == "true",
        "apprenticeship_mode": (mentor_package or {}).get("manifest", {}).get("apprenticeship_mode", "none"),
        "source_dir": "<withheld-local-path>",
        "generated_at": generated_at,
        "generated_by": {
            "id": GENERATOR_ID,
            "repository": GENERATOR_REPOSITORY,
            "script": GENERATOR_SCRIPT,
        },
        "provenance": {
            "watermark": PROVENANCE_WATERMARK,
            "watermark_visibility": "manifest-only",
            "source_package": "references/course_package.json",
            "note": "This packaged course Skill was generated from course materials by lineage-skill.",
        },
        "reference_status": statuses,
        "package_schemas": {
            "course_package": "1.0",
            "teacher_model": "1.0" if mentor_package else None,
            "capability_graph": "1.0" if mentor_package else None,
            "practice_bank": "1.0" if mentor_package else None,
            "assessment_bank": "1.0" if mentor_package else None,
            "mentor_package": "1.0" if mentor_package else None,
        },
        "package_hashes": package_hashes,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Package prepared course materials as a Codex skill.")
    parser.add_argument("--course-name", required=True, help="Human-readable course name.")
    parser.add_argument("--skill-name", help="Skill directory/name. Defaults to <course-slug>-<role>-lineage.")
    parser.add_argument(
        "--mode",
        default="mentor",
        help="Skill role or comma-separated roles. Valid: " + ", ".join(sorted(MODE_SPECS)),
    )
    parser.add_argument("--scope", default="auto", help="Course scope metadata. Valid: auto, single-course, multi-course, fused.")
    parser.add_argument("--evidence", default="standard", help="Evidence strategy metadata. Valid: standard, strict.")
    parser.add_argument("--progress", default="auto", help="Progress strategy metadata. Valid: auto, none, tracked.")
    parser.add_argument("--apprenticeship", choices=sorted(VALID_APPRENTICESHIP), default="full", help="Requested apprenticeship mode for mentor roles.")
    parser.add_argument("--practice-depth", choices=["standard", "deep"], default="standard")
    parser.add_argument("--learner-state", choices=["external", "none"], default="external")
    parser.add_argument(
        "--include-source-artifacts",
        action="store_true",
        help="Opt in to copying transcripts, OCR, analyses, text sources, selected keyframes, and source-course directories.",
    )
    parser.add_argument(
        "--mentor-audit-mode",
        choices=["auto", "strict"],
        default="auto",
        help="Strict mode refuses a requested full apprenticeship when readiness would require a downgrade.",
    )
    parser.add_argument("--skip-validate-skill", action="store_true")
    parser.add_argument("--reuse-mentor-artifacts", action="store_true", help="Package existing mentor artifacts without rebuilding compiler stages.")
    parser.add_argument("--source-dir", required=True, help="Directory containing prepared course notes and indexes.")
    parser.add_argument("--output-dir", required=True, help="Directory where the generated skill should be written.")
    parser.add_argument("--description", default="Packaged from prepared course distillation materials.", help="Short note added to SKILL.md.")
    parser.add_argument("--force", action="store_true", help="Overwrite an existing generated skill directory.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    source_dir = Path(args.source_dir).expanduser().resolve()
    output_dir = Path(args.output_dir).expanduser().resolve()
    modes = parse_modes(args.mode)
    options = resolve_options(source_dir, modes, args.mode, args.scope, args.evidence, args.progress)
    options["learner_state"] = args.learner_state
    options["include_source_artifacts"] = "true" if args.include_source_artifacts else "false"
    skill_name = args.skill_name or default_skill_name(args.course_name, modes)
    final_skill_dir = output_dir / skill_name

    if not source_dir.exists() or not source_dir.is_dir():
        raise SystemExit(f"source dir does not exist: {source_dir}")

    if final_skill_dir.exists():
        if not args.force:
            raise SystemExit(f"skill dir already exists: {final_skill_dir} (use --force to overwrite)")

    package_path = source_dir / "course_package.json"
    if not package_path.exists():
        write_json(package_path, build_package(args.course_name, source_dir))
    else:
        write_json(package_path, load_course_package(package_path))

    mentor_info: dict[str, object] | None = None
    requested_apprenticeship = args.apprenticeship if "mentor" in modes else "none"
    if "mentor" in modes:
        if args.reuse_mentor_artifacts:
            missing = [name for name in MENTOR_ARTIFACTS if not (source_dir / name).exists()]
            if missing:
                raise SystemExit(f"cannot reuse mentor artifacts; missing: {', '.join(missing)}")
            mentor_info = {
                "mentor_package": load_schema_json(source_dir / "mentor_package.json"),
                "readiness": load_schema_json(source_dir / "mentor_readiness_audit.json"),
            }
        else:
            mentor_info = ensure_mentor_artifacts(
                source_dir,
                apprenticeship=requested_apprenticeship,
                evidence=args.evidence,
                practice_depth=args.practice_depth,
            )

    output_dir.mkdir(parents=True, exist_ok=True)
    skill_dir = output_dir / f".{skill_name}.lineage-build"
    if skill_dir.exists():
        shutil.rmtree(skill_dir)

    references_dir = skill_dir / "references"
    scripts_dir = skill_dir / "scripts"
    agents_dir = skill_dir / "agents"
    assets_dir = skill_dir / "assets"
    references_dir.mkdir(parents=True, exist_ok=True)
    scripts_dir.mkdir(parents=True, exist_ok=True)

    actual_apprenticeship = (
        mentor_info.get("mentor_package", {}).get("manifest", {}).get("apprenticeship_mode", "none")
        if mentor_info
        else "none"
    )
    if (
        args.mentor_audit_mode == "strict"
        and requested_apprenticeship == "full"
        and actual_apprenticeship != "full"
    ):
        readiness = mentor_info.get("readiness", {}) if mentor_info else {}
        raise SystemExit(
            "strict mentor audit refused full apprenticeship: "
            + "; ".join(readiness.get("blockers", []) or ["mentor readiness is not ready"])
        )
    build_skill_md(
        args.course_name,
        skill_name,
        args.description,
        modes,
        skill_dir / "SKILL.md",
        apprenticeship_mode=str(actual_apprenticeship),
    )
    build_agent_metadata(args.course_name, skill_name, modes, agents_dir)

    statuses = {}
    statuses["course_package.json"] = copy_course_package(
        source_dir,
        references_dir / "course_package.json",
        include_source_artifacts=args.include_source_artifacts,
    )
    statuses["course_digest.md"] = copy_or_stub(
        find_course_distillation_md(source_dir),
        references_dir / "course_digest.md",
        "Course Digest",
        "No standalone digest was present. Use course_package.json and the evidence indexes; do not infer missing course structure.",
    )
    statuses["full_transcript.md"] = copy_or_stub(
        find_first_existing(source_dir, ["full_transcript.md"]) if args.include_source_artifacts else None,
        references_dir / "full_transcript.md",
        "Full Transcript",
        "No combined transcript was present. Use transcript files and evidence_map.json when available.",
    )
    statuses["concept_glossary.md"] = write_derived_markdown(
        source_dir,
        references_dir / "concept_glossary.md",
        "Concept Glossary",
        ["关键概念", "概念词汇", "词汇表"],
        "No glossary section was extracted. Resolve terms through CoursePackage claims and source evidence.",
    )
    statuses["quote_index.md"] = write_derived_markdown(
        source_dir,
        references_dir / "quote_index.md",
        "Quote Index",
        ["核心金句", "金句"],
        "No quote index was extracted. Do not invent teacher quotations.",
    )
    statuses["study_paths.md"] = write_derived_markdown(
        source_dir,
        references_dir / "study_paths.md",
        "Study Paths",
        ["可执行行动", "学习路径", "行动清单"],
        "No source-specific study path was extracted. Use the capability graph and practice bank for sequencing.",
    )
    statuses["lesson_index.json"] = build_lesson_index(source_dir, references_dir / "lesson_index.json")
    statuses["evidence_map.json"] = build_evidence_map(
        source_dir,
        references_dir / "evidence_map.json",
        include_source_artifacts=args.include_source_artifacts,
    )
    statuses.update(copy_optional_reference_files(source_dir, references_dir))
    if args.include_source_artifacts:
        statuses.update(copy_optional_reference_dirs(source_dir, references_dir))
        statuses.update(copy_source_courses_from_package(source_dir, references_dir))
    statuses.update(write_mode_references(references_dir, modes))
    if mentor_info:
        statuses.update(copy_mentor_runtime(source_dir, references_dir, scripts_dir, assets_dir))
    okf_result = build_okf_bundle(course_dir=references_dir, output_dir=references_dir / "okf", course_name=args.course_name)
    statuses["okf/"] = f"generated {okf_result['concept_count']} concepts, {okf_result['evidence_count']} evidence chunks"

    build_search_script(scripts_dir / "search_course_notes.py")
    statuses["scripts/search_course_notes.py"] = "generated"
    build_fetch_evidence_script(scripts_dir / "fetch_course_evidence.py")
    statuses["scripts/fetch_course_evidence.py"] = "copied"

    mentor_package = mentor_info.get("mentor_package") if mentor_info else None
    manifest = build_lineage_manifest(args.course_name, skill_name, modes, source_dir, statuses, options, mentor_package)
    manifest["package_hashes"] = {
        name: content_hash(load_schema_json(path))
        for name in [
            "course_package.json",
            "teacher_model.json",
            "capability_graph.json",
            "practice_bank.json",
            "assessment_bank.json",
            "mentor_package.json",
        ]
        if (path := references_dir / name).exists()
    }
    write_json(skill_dir / "lineage_manifest.json", manifest)
    if mentor_package:
        write_json(
            skill_dir / "mentor_manifest.json",
            {
                "schema_version": "1.0",
                "mentor_package_id": mentor_package["manifest"]["mentor_package_id"],
                "apprenticeship_mode": mentor_package["manifest"]["apprenticeship_mode"],
                "requested_apprenticeship_mode": mentor_package["manifest"]["requested_apprenticeship_mode"],
                "learner_state": "external",
                "state_contract": "references/schemas/apprenticeship_state.schema.json",
                "episode_contract": "references/schemas/practice_episode.schema.json",
            },
        )

    if not args.skip_validate_skill:
        validation = validate_skill(skill_dir)
        validation["skill_dir"] = "."
        write_json(skill_dir / "validation_report.json", validation)
        if not validation["valid"]:
            raise SystemExit("generated Skill validation failed:\n" + json.dumps(validation, ensure_ascii=False, indent=2))

    if final_skill_dir.exists():
        shutil.rmtree(final_skill_dir)
    skill_dir.rename(final_skill_dir)

    print(f"Generated skill: {final_skill_dir}")
    if mentor_info:
        print(f"- mentor readiness: {mentor_info['readiness']['status']}")
        print(f"- apprenticeship requested/actual: {requested_apprenticeship}/{actual_apprenticeship}")
    for name, status in statuses.items():
        print(f"- {name}: {status}")


if __name__ == "__main__":
    main()
