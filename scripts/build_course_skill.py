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
GENERATOR_SCHEMA_VERSION = "0.1"
PROVENANCE_WATERMARK = "lineage-skill:course-skill-builder:v0.1"

MODE_SPECS = {
    "mentor": {
        "label": "Mentor",
        "description": "a source-grounded course mentor that guides learning, practice, review, and application",
        "focus": [
            "Act as a course-specific mentor grounded in the packaged course materials.",
            "Guide the user through learning plans, practice, review, weak-point diagnosis, and course-backed application.",
            "Ask clarifying or diagnostic questions when the user's goal, level, schedule, or application context is unclear.",
        ],
        "rules": [
            "Use course references first, and distinguish direct course content from mentor-style synthesis.",
            "Guide the learner toward understanding, recall, application, and review instead of only giving summaries.",
            "When progress tracking is available, update plans based on completed lessons, weak areas, and review needs.",
            "If the course materials do not support a claim, say what is missing.",
        ],
        "extra_refs": {
            "mentor_playbook.md": "Add mentor behaviors, coaching patterns, diagnostic questions, planning rules, and review routines derived from the course.",
            "mentor_sessions.md": "Add reusable session flows for daily study, review, application, and source lookup.",
            "learner_progress.json": {"profile": {}, "completed": [], "weak_points": [], "review_queue": [], "notes": "Optional learner progress state when the host workflow supports persistent updates."},
        },
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
            "consulting_playbook.md": "Add diagnostic prompts, intake questions, decision frames, and advisory workflows derived from course methods.",
            "scenario_templates.md": "Add reusable templates for user situation analysis, option comparison, and recommendation memos.",
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
            "playbooks.md": "Add reusable workflows and operating procedures derived from course methods.",
            "checklists.md": "Add checklists for common course-backed tasks.",
            "templates.md": "Add reusable templates, scripts, tables, or worksheets.",
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
            "custom_role.md": "Define the custom Skill role, use cases, output formats, and boundaries requested by the user.",
            "custom_workflows.md": "Add workflow steps and reusable prompts for the custom role.",
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
    return "stubbed"


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
    return "stubbed"


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
    return "generated" if lessons else "stubbed"


def build_evidence_map(source_dir: Path, destination: Path) -> str:
    existing = find_first_existing(source_dir, ["evidence_map.json"])
    if existing:
        shutil.copy2(existing, destination)
        return "copied"

    transcript_files = sorted(str(p.relative_to(source_dir)) for p in source_dir.glob("transcripts/**/*.json"))
    analysis_files = sorted(str(p.relative_to(source_dir)) for p in source_dir.glob("analysis/**/*_analysis.md"))
    screenshot_files = sorted(str(p.relative_to(source_dir)) for p in source_dir.glob("analysis/screenshots/**/*") if p.is_file())
    course_distillations = sorted(str(p.relative_to(source_dir)) for p in source_dir.glob("course_distillation_*.*"))
    document_files = sorted(str(p.relative_to(source_dir)) for p in source_dir.glob("documents/**/*") if p.is_file())
    payload = {
        "generated_at": dt.datetime.now().isoformat(timespec="seconds"),
        "source_dir": str(source_dir),
        "transcripts": transcript_files,
        "analysis_files": analysis_files,
        "screenshots": screenshot_files,
        "course_distillations": course_distillations,
        "documents": document_files,
        "notes": [
            "Evidence entries are file-level by default.",
            "Add timestamps and topic labels after deeper course distillation.",
        ],
    }
    destination.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return "generated"


def copy_course_package(source_dir: Path, destination: Path) -> str:
    existing = find_first_existing(source_dir, ["course_package.json"])
    if existing:
        shutil.copy2(existing, destination)
        return "copied"
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
        "learning_checks": [],
        "quotes": [],
        "evidence": [],
        "study_paths": [],
        "boundaries": [],
    }
    destination.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return "stubbed"


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


def build_skill_md(course_name: str, skill_name: str, description: str, modes: list[str], destination: Path) -> None:
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

## Role Focus

{focus_lines}

## Reference Priority

1. `references/course_digest.md` for the course-level framework.
2. `references/lesson_index.json` for lesson lookup and sequencing.
3. `references/concept_glossary.md` for terms and definitions.
4. `references/evidence_map.json` for source files, screenshots, transcripts, and confidence notes.
5. `references/quote_index.md` for memorable course statements.
6. `references/study_paths.md` for review plans and learning routes.
7. `references/course_package.json` for normalized package objects when structured lookup is needed.
8. `references/full_transcript.md` for original wording when detailed citation is required.

## Response Rules

{rules}

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
"""Tiny keyword search over packaged course references."""

from __future__ import annotations

import argparse
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Search course reference files.")
    parser.add_argument("query", help="Keyword to search for.")
    parser.add_argument("--references-dir", default="../references", help="Reference directory relative to this script.")
    args = parser.parse_args()

    base = (Path(__file__).resolve().parent / args.references_dir).resolve()
    query = args.query.lower()
    matches = []

    for path in sorted(base.rglob("*")):
        if not path.is_file():
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


def yaml_quote(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def build_agent_metadata(course_name: str, skill_name: str, modes: list[str], agents_dir: Path) -> None:
    agents_dir.mkdir(parents=True, exist_ok=True)
    mode_labels = ", ".join(MODE_SPECS[mode]["label"] for mode in modes)
    display_name = f"{course_name} Course Skill"
    short_description = "Source-grounded course Q&A, review, and workflows."
    default_prompt = f"Use ${skill_name} to answer questions about {course_name} and cite the course sources."

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
    return "stubbed"


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
) -> dict[str, object]:
    generated_at = dt.datetime.now().isoformat(timespec="seconds")
    return {
        "schema_version": GENERATOR_SCHEMA_VERSION,
        "course_name": course_name,
        "skill_name": skill_name,
        "roles": modes,
        "modes": modes,
        "scope": options["scope"],
        "evidence_strategy": options["evidence"],
        "progress_strategy": options["progress"],
        "source_dir": str(source_dir),
        "generated_at": generated_at,
        "generated_by": {
            "id": GENERATOR_ID,
            "repository": GENERATOR_REPOSITORY,
            "script": GENERATOR_SCRIPT,
        },
        "provenance": {
            "watermark": PROVENANCE_WATERMARK,
            "watermark_visibility": "manifest-only",
            "source_package": str(source_dir / "course_package.json"),
            "note": "This packaged course Skill was generated from course materials by lineage-skill.",
        },
        "reference_status": statuses,
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
    skill_name = args.skill_name or default_skill_name(args.course_name, modes)
    skill_dir = output_dir / skill_name

    if not source_dir.exists() or not source_dir.is_dir():
        raise SystemExit(f"source dir does not exist: {source_dir}")

    if skill_dir.exists():
        if not args.force:
            raise SystemExit(f"skill dir already exists: {skill_dir} (use --force to overwrite)")
        shutil.rmtree(skill_dir)

    references_dir = skill_dir / "references"
    scripts_dir = skill_dir / "scripts"
    agents_dir = skill_dir / "agents"
    references_dir.mkdir(parents=True, exist_ok=True)
    scripts_dir.mkdir(parents=True, exist_ok=True)

    build_skill_md(args.course_name, skill_name, args.description, modes, skill_dir / "SKILL.md")
    build_agent_metadata(args.course_name, skill_name, modes, agents_dir)

    statuses = {}
    statuses["course_package.json"] = copy_course_package(source_dir, references_dir / "course_package.json")
    statuses["course_digest.md"] = copy_or_stub(
        find_course_distillation_md(source_dir),
        references_dir / "course_digest.md",
        "Course Digest",
        "Add the course-level framework, key principles, and module summary here.",
    )
    statuses["full_transcript.md"] = copy_or_stub(
        find_first_existing(source_dir, ["full_transcript.md"]),
        references_dir / "full_transcript.md",
        "Full Transcript",
        "Add transcript text here, or keep transcript JSON files linked from evidence_map.json.",
    )
    statuses["concept_glossary.md"] = write_derived_markdown(
        source_dir,
        references_dir / "concept_glossary.md",
        "Concept Glossary",
        ["关键概念", "概念词汇", "词汇表"],
        "Add course terms, definitions, aliases, and source lessons here.",
    )
    statuses["quote_index.md"] = write_derived_markdown(
        source_dir,
        references_dir / "quote_index.md",
        "Quote Index",
        ["核心金句", "金句"],
        "Add memorable statements with lesson/source references here.",
    )
    statuses["study_paths.md"] = write_derived_markdown(
        source_dir,
        references_dir / "study_paths.md",
        "Study Paths",
        ["可执行行动", "学习路径", "行动清单"],
        "Add beginner, review, exam, and topical learning paths here.",
    )
    statuses["lesson_index.json"] = build_lesson_index(source_dir, references_dir / "lesson_index.json")
    statuses["evidence_map.json"] = build_evidence_map(source_dir, references_dir / "evidence_map.json")
    statuses.update(write_mode_references(references_dir, modes))

    build_search_script(scripts_dir / "search_course_notes.py")

    manifest = build_lineage_manifest(args.course_name, skill_name, modes, source_dir, statuses, options)
    (skill_dir / "lineage_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Generated skill: {skill_dir}")
    for name, status in statuses.items():
        print(f"- {name}: {status}")


if __name__ == "__main__":
    main()
