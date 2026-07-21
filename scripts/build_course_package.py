#!/usr/bin/env python3
"""Normalize distilled course outputs into a generic CoursePackage JSON."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
from pathlib import Path

from migrate_course_package import migrate_package
from schema_utils import issues_payload, load_json as load_schema_json, validate_schema, write_json


SECTION_ALIASES = {
    "concepts": ["关键概念", "概念词汇", "词汇表", "术语"],
    "topics": ["跨课程主题", "主题图谱", "课程体系", "体系图"],
    "cases": ["完整示范", "讲评案例", "案例示范", "案例"],
    "methods": ["方法", "框架", "行动清单", "可执行行动"],
    "diagnostics": ["老师首先关注", "问题定性与诊断", "诊断判断", "诊断", "判断标准", "问题定位"],
    "workflows": ["执行流程", "工作流", "操作流程", "作业流程"],
    "rubrics": ["反馈纠错", "进阶与出师", "质量标准", "评价标准", "评分标准", "质检规则"],
    "templates": ["模板资产", "模板", "话术", "表格"],
    "transfer_rules": ["迁移规则", "应用迁移", "场景迁移"],
    "failure_modes": ["失效与误用", "失效", "误用", "反例"],
    "quotes": ["核心金句", "金句", "重要原话"],
    "study_paths": ["进阶与出师", "学习路径", "复习路径", "行动清单", "可执行行动"],
    "boundaries": ["不可复制背景", "边界", "风险", "注意事项", "限制"],
}

CARD_TYPE_TO_PACKAGE_FIELD = {
    "concept": "concepts",
    "method": "methods",
    "diagnostic": "diagnostics",
    "workflow": "workflows",
    "rubric": "rubrics",
    "template": "templates",
    "transfer": "transfer_rules",
    "failure_mode": "failure_modes",
    "quote": "quotes",
    "boundary": "boundaries",
    "attention_cue": "diagnostics",
    "problem_frame": "diagnostics",
    "decision_rule": "methods",
    "demonstration": "cases",
    "feedback_pattern": "rubrics",
    "progression_rule": "study_paths",
    "graduation_signal": "rubrics",
    "non_copyable_context": "boundaries",
}


class AssetRecord(dict):
    """Structured 1.0 asset with legacy substring-membership compatibility."""

    def __contains__(self, key: object) -> bool:
        if super().__contains__(key):
            return True
        if isinstance(key, str):
            return any(key in str(self.get(field) or "") for field in ["title", "summary", "legacy_text", "value"])
        return False


def read_text(path: Path | None) -> str:
    if not path or not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="ignore")


def load_json(path: Path | None) -> object | None:
    if not path or not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        item = json.loads(line)
        if isinstance(item, dict):
            rows.append(item)
    return rows


def newest(source_dir: Path, pattern: str) -> Path | None:
    matches = sorted(source_dir.glob(pattern), key=lambda path: path.stat().st_mtime, reverse=True)
    return matches[0] if matches else None


def section(text: str, aliases: list[str]) -> str:
    for alias in aliases:
        pattern = rf"(^##+\s*[^\n]*{re.escape(alias)}[^\n]*\n)([\s\S]*?)(?=^##+\s+|\Z)"
        match = re.search(pattern, text, flags=re.M)
        if match:
            return match.group(0).strip()
    return ""


def bullets(text: str, limit: int = 80) -> list[str]:
    rows = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith(("- ", "* ")):
            value = stripped[2:].strip()
        elif re.match(r"^\d+[.)]\s+", stripped):
            value = re.sub(r"^\d+[.)]\s+", "", stripped).strip()
        else:
            continue
        if value:
            rows.append(value)
        if len(rows) >= limit:
            break
    return rows


def add_unique(rows: list[str], value: str, limit: int = 120) -> None:
    value = value.strip()
    if not value or value in rows or len(rows) >= limit:
        return
    rows.append(value)


def card_value(card: dict) -> str:
    title = str(card.get("title") or "").strip()
    body = str(card.get("quote") or card.get("summary") or "").strip()
    source = str(card.get("source_ref") or card.get("source_path") or "").strip()
    chunk = card.get("chunk_index")
    if title and body and title not in body:
        value = f"{title}：{body}"
    else:
        value = body or title
    if source:
        suffix = f"{source}#{chunk}" if chunk is not None else source
        value = f"{value}（{suffix}）"
    return value


def load_text_cards(source_dir: Path) -> list[dict]:
    return load_jsonl(source_dir / "text_distillation" / "evidence_cards.jsonl")


def merge_text_cards(package: dict, cards: list[dict]) -> None:
    for card in cards:
        card_type = card.get("card_type")
        value = card_value(card)
        target = CARD_TYPE_TO_PACKAGE_FIELD.get(card_type)
        if target:
            row = dict(card)
            row.setdefault("summary", row.get("quote") or value)
            row.setdefault("provenance", "direct_source" if card_type in {"quote", "demonstration"} else "source_grounded_synthesis")
            signature = (row.get("card_id"), row.get("title"), row.get("summary"))
            if not any(
                isinstance(existing, dict)
                and (existing.get("card_id"), existing.get("title"), existing.get("summary")) == signature
                for existing in package[target]
            ):
                package[target].append(row)
        elif card_type == "case":
            package["cases"].append(card)
        elif card_type in {"task", "open_question"}:
            package["learning_checks"].append(card)


def normalize_lessons(data: object | None) -> list[dict]:
    if isinstance(data, list):
        items = data
    elif isinstance(data, dict):
        items = data.get("lesson_summaries") or data.get("lessons") or []
    else:
        items = []
    lessons = []
    for idx, item in enumerate(items, 1):
        if not isinstance(item, dict):
            lessons.append({"id": f"lesson-{idx:03d}", "title": str(item), "summary": "", "topics": [], "source": ""})
            continue
        title = item.get("title") or item.get("lesson_name") or item.get("video") or item.get("name") or f"Lesson {idx}"
        lessons.append(
            {
                "id": item.get("id") or f"lesson-{idx:03d}",
                "title": title,
                "duration_minutes": item.get("duration_minutes"),
                "summary": item.get("summary") or item.get("abstract") or "",
                "topics": item.get("topics") or item.get("keywords") or [],
                "source": item.get("source") or item.get("file") or "",
            }
        )
    return lessons


def build_evidence(source_dir: Path) -> list[dict]:
    rows = []
    for path in sorted(source_dir.glob("transcripts/**/*.json")):
        rows.append({"type": "transcript", "path": str(path.relative_to(source_dir)), "granularity": "file"})
    for path in sorted(source_dir.glob("analysis/**/*_analysis.md")):
        rows.append({"type": "visual_analysis", "path": str(path.relative_to(source_dir)), "granularity": "file"})
    for path in sorted(source_dir.glob("analysis/screenshots/**/*")):
        if path.is_file():
            rows.append({"type": "screenshot", "path": str(path.relative_to(source_dir)), "granularity": "file"})
    for path in sorted(source_dir.glob("keyframe_selection/*_model_keyframes_manifest.json")):
        rows.append({"type": "model_keyframe_manifest", "path": str(path.relative_to(source_dir)), "granularity": "media"})
    for path in sorted(source_dir.glob("keyframe_selection/model_keyframe_summary.md")):
        rows.append({"type": "model_keyframe_summary", "path": str(path.relative_to(source_dir)), "granularity": "course"})
    for path in sorted(source_dir.glob("keyframes_model_selected/**/*")):
        if path.is_file():
            rows.append({"type": "model_selected_keyframe", "path": str(path.relative_to(source_dir)), "granularity": "frame"})
    for path in sorted(source_dir.glob("course_distillation_*.*")):
        rows.append({"type": "distillation", "path": str(path.relative_to(source_dir)), "granularity": "file"})
    for path in sorted(source_dir.glob("documents/**/*.md")):
        rows.append({"type": "document_ocr", "path": str(path.relative_to(source_dir)), "granularity": "file"})
    for path in sorted(source_dir.glob("documents/**/*.json")):
        rows.append({"type": "document_manifest", "path": str(path.relative_to(source_dir)), "granularity": "file"})
    for path in sorted(source_dir.glob("documents/**/*.html")) + sorted(source_dir.glob("documents/**/*.htm")):
        rows.append({"type": "document_raw_html", "path": str(path.relative_to(source_dir)), "granularity": "file"})
    for path in sorted(source_dir.glob("documents/**/*.txt")):
        rows.append({"type": "document_raw_text", "path": str(path.relative_to(source_dir)), "granularity": "file"})
    for path in sorted(source_dir.glob("text_sources/source_manifest.json")):
        rows.append({"type": "text_source_manifest", "path": str(path.relative_to(source_dir)), "granularity": "course"})
    for path in sorted(source_dir.glob("text_sources/chunks.jsonl")):
        rows.append({"type": "text_source_chunks", "path": str(path.relative_to(source_dir)), "granularity": "chunk"})
    for path in sorted(source_dir.glob("text_distillation/evidence_cards.jsonl")):
        rows.append({"type": "text_evidence_card", "path": str(path.relative_to(source_dir)), "granularity": "card"})
        for card in load_jsonl(path):
            rows.append(
                {
                    "id": card.get("card_id"),
                    "type": "text",
                    "path": card.get("source_ref") or card.get("source_path") or str(path.relative_to(source_dir)),
                    "granularity": "card",
                    "source_id": card.get("source_id"),
                    "chunk_id": card.get("chunk_id"),
                    "card_id": card.get("card_id"),
                    "quote_summary": card.get("quote") or card.get("summary") or "",
                    "confidence": card.get("confidence", "medium"),
                }
            )
    for path in sorted(source_dir.glob("text_distillation/text_course_synthesis.md")):
        rows.append({"type": "text_course_synthesis", "path": str(path.relative_to(source_dir)), "granularity": "course"})
    for path in sorted(source_dir.glob("text_distillation/text_distillation_quality.json")):
        rows.append({"type": "text_distillation_quality", "path": str(path.relative_to(source_dir)), "granularity": "course"})
    return rows


def package_quality(package: dict) -> dict:
    counts = {
        "lessons": len(package["lessons"]),
        "concepts": len(package["concepts"]),
        "topics": len(package["topics"]),
        "methods": len(package["methods"]),
        "diagnostics": len(package["diagnostics"]),
        "workflows": len(package["workflows"]),
        "rubrics": len(package["rubrics"]),
        "templates": len(package["templates"]),
        "transfer_rules": len(package["transfer_rules"]),
        "failure_modes": len(package["failure_modes"]),
        "quotes": len(package["quotes"]),
        "evidence": len(package["evidence"]),
        "study_paths": len(package["study_paths"]),
        "boundaries": len(package["boundaries"]),
    }
    missing = [key for key, value in counts.items() if value == 0 and key not in {"boundaries"}]
    return {
        "counts": counts,
        "missing_recommended_fields": missing,
        "status": "usable" if counts["lessons"] or counts["evidence"] else "thin",
    }


def distillation_audit_summary(source_dir: Path) -> dict | None:
    path = source_dir / "distillation_audit.json"
    if not path.exists():
        return None
    data = load_json(path)
    if not isinstance(data, dict):
        return None
    return {
        "json_path": "distillation_audit.json",
        "markdown_path": "distillation_audit.md" if (source_dir / "distillation_audit.md").exists() else "",
        "lesson_count": len(data.get("lessons") or []),
        "manual_review_required": (data.get("cross_validation_summary") or {}).get("manual_review_required", 0),
        "coverage_summary": data.get("coverage_summary") or {},
        "cross_validation_summary": data.get("cross_validation_summary") or {},
    }


def build_legacy_package(course_name: str, source_dir: Path) -> dict:
    distillation_md = newest(source_dir, "course_distillation_*.md")
    distillation_json = newest(source_dir, "course_distillation_*.json")
    lesson_json = source_dir / "lesson_summaries.json"
    digest_text = read_text(distillation_md or source_dir / "course_digest.md")
    distillation_data = load_json(distillation_json)
    lessons = normalize_lessons(load_json(lesson_json) or distillation_data)

    sections = {key: section(digest_text, aliases) for key, aliases in SECTION_ALIASES.items()}
    package = {
        "schema_version": "0.1",
        "manifest": {
            "course_name": course_name,
            "source_dir": str(source_dir),
            "generated_at": dt.datetime.now().isoformat(timespec="seconds"),
            "distillation_markdown": str(distillation_md.relative_to(source_dir)) if distillation_md else "",
            "distillation_json": str(distillation_json.relative_to(source_dir)) if distillation_json else "",
        },
        "lessons": lessons,
        "concepts": bullets(sections["concepts"]),
        "topics": bullets(sections["topics"]),
        "cases": [],
        "methods": bullets(sections["methods"]),
        "diagnostics": bullets(sections["diagnostics"]),
        "workflows": bullets(sections["workflows"]),
        "rubrics": bullets(sections["rubrics"]),
        "templates": bullets(sections["templates"]),
        "transfer_rules": bullets(sections["transfer_rules"]),
        "failure_modes": bullets(sections["failure_modes"]),
        "learning_checks": [],
        "quotes": bullets(sections["quotes"]),
        "evidence": build_evidence(source_dir),
        "study_paths": bullets(sections["study_paths"]),
        "boundaries": bullets(sections["boundaries"]),
    }
    merge_text_cards(package, load_text_cards(source_dir))
    package["quality"] = package_quality(package)
    audit_summary = distillation_audit_summary(source_dir)
    if audit_summary:
        package["quality"]["distillation_audit"] = audit_summary
    return package


def build_package(course_name: str, source_dir: Path) -> dict:
    """Build the canonical CoursePackage 1.0 while retaining legacy inputs."""
    legacy = build_legacy_package(course_name, source_dir)
    package, report = migrate_package(legacy, source_path=source_dir / "course_package.json")
    audit_summary = distillation_audit_summary(source_dir)
    if audit_summary:
        package["quality"]["distillation_audit"] = audit_summary
    package["manifest"]["build_report"] = {
        "migrator_version": report["target_schema_version"],
        "legacy_text_count": report["legacy_text_count"],
        "human_review_count": report["human_review_count"],
    }
    for field in ["concepts", "topics", "cases", "methods", "diagnostics", "workflows", "rubrics", "templates", "transfer_rules", "failure_modes", "boundaries", "quotes", "study_paths"]:
        package[field] = [AssetRecord(item) if isinstance(item, dict) else item for item in package[field]]
    return package


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a generic CoursePackage from distilled course outputs.")
    parser.add_argument("--course-name", required=True)
    parser.add_argument("--source-dir", required=True)
    parser.add_argument("--output", help="Output JSON path. Defaults to <source-dir>/course_package.json.")
    args = parser.parse_args()

    source_dir = Path(args.source_dir).expanduser().resolve()
    if not source_dir.is_dir():
        raise SystemExit(f"source dir does not exist: {source_dir}")
    output = Path(args.output).expanduser().resolve() if args.output else source_dir / "course_package.json"
    package = build_package(args.course_name, source_dir)
    schema = load_schema_json(Path(__file__).resolve().parents[1] / "references" / "schemas" / "course_package.schema.json")
    validation = issues_payload(validate_schema(package, schema))
    if not validation["valid"]:
        raise SystemExit(json.dumps(validation, ensure_ascii=False, indent=2))
    write_json(output, package)
    write_json(source_dir / "course_package_build_report.json", {"schema_version": "1.0", "validation": validation})
    print(f"wrote {output}")
    print(json.dumps(package["quality"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
