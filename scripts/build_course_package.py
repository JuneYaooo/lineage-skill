#!/usr/bin/env python3
"""Normalize distilled course outputs into a generic CoursePackage JSON."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
from pathlib import Path


SECTION_ALIASES = {
    "concepts": ["关键概念", "概念词汇", "词汇表", "术语"],
    "topics": ["跨课程主题", "主题图谱", "课程体系", "体系图"],
    "methods": ["方法", "框架", "行动清单", "可执行行动"],
    "quotes": ["核心金句", "金句", "重要原话"],
    "study_paths": ["学习路径", "复习路径", "行动清单", "可执行行动"],
    "boundaries": ["边界", "风险", "注意事项", "限制"],
}


def read_text(path: Path | None) -> str:
    if not path or not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="ignore")


def load_json(path: Path | None) -> object | None:
    if not path or not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


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
    for path in sorted(source_dir.glob("course_distillation_*.*")):
        rows.append({"type": "distillation", "path": str(path.relative_to(source_dir)), "granularity": "file"})
    for path in sorted(source_dir.glob("documents/**/*.md")):
        rows.append({"type": "document_ocr", "path": str(path.relative_to(source_dir)), "granularity": "file"})
    for path in sorted(source_dir.glob("documents/**/*.json")):
        rows.append({"type": "document_manifest", "path": str(path.relative_to(source_dir)), "granularity": "file"})
    return rows


def package_quality(package: dict) -> dict:
    counts = {
        "lessons": len(package["lessons"]),
        "concepts": len(package["concepts"]),
        "topics": len(package["topics"]),
        "methods": len(package["methods"]),
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


def build_package(course_name: str, source_dir: Path) -> dict:
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
        "learning_checks": [],
        "quotes": bullets(sections["quotes"]),
        "evidence": build_evidence(source_dir),
        "study_paths": bullets(sections["study_paths"]),
        "boundaries": bullets(sections["boundaries"]),
    }
    package["quality"] = package_quality(package)
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
    output.write_text(json.dumps(package, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {output}")
    print(json.dumps(package["quality"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
