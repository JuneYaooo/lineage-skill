#!/usr/bin/env python3
"""Build final quality and cross-validation audit files for a course workspace."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
from pathlib import Path
from typing import Any


SCREENSHOT_RE = re.compile(r"\[SCREENSHOT\s+[^\]]+\]", flags=re.I)
SLIDE_TERMS = ("ppt", "slide", "slides", "课件", "幻灯", "讲义", "courseware")
BOARD_TERMS = ("板书", "白板", "blackboard", "whiteboard")
DEMO_TERMS = ("演示", "demo", "操作", "software", "screen", "screens", "软件")
DIAGRAM_TERMS = ("图表", "diagram", "chart", "流程图", "表格", "table")
TERM_REVIEW_TERMS = ("术语", "专名", "错字", "校对", "同音", "ocr", "asr", "Lineage", "Skill")
AUDIT_MODES = {"auto", "strict", "off"}


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def load_json(path: Path) -> Any:
    return json.loads(read_text(path))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in read_text(path).splitlines():
        if not line.strip():
            continue
        item = json.loads(line)
        if isinstance(item, dict):
            rows.append(item)
    return rows


def rel(path: Path, root: Path) -> str:
    return str(path.relative_to(root))


def normalize_stem(value: str) -> str:
    text = Path(value).stem if value else ""
    text = re.sub(r"(_transcript|_analysis|_model_keyframes_manifest)$", "", text)
    text = re.sub(r"[^0-9A-Za-z\u4e00-\u9fff]+", "", text).lower()
    return text


def media_lesson_stem(value: str) -> str:
    """Return the actual media stem when capture names include a parent-folder prefix.

    The media capture stage prefixes transcript/keyframe names with the parent
    directory to avoid collisions, e.g. `4、需求采集与挖掘_需求挖掘...`.
    Visual analysis files are named from the MP4 stem only. For audit purposes
    these must resolve to the same lesson id.
    """
    text = Path(value).stem if value else ""
    text = re.sub(r"(_transcript|_analysis|_model_keyframes_manifest)$", "", text)
    if "_" in text:
        prefix, suffix = text.rsplit("_", 1)
        if "、" in prefix or "课" in prefix or re.match(r"^\d+", prefix):
            return suffix
    return text


def lesson_id_from_media(value: str) -> str:
    return normalize_stem(media_lesson_stem(value))


def inventory(paths: list[Path], root: Path) -> dict[str, Any]:
    return {"count": len(paths), "paths": [rel(path, root) for path in paths]}


def transcript_id(path: Path, data: dict[str, Any]) -> str:
    return lesson_id_from_media(str(data.get("video_name") or data.get("video") or data.get("media") or path.name))


def analysis_id(path: Path) -> str:
    return lesson_id_from_media(path.name)


def manifest_id(path: Path, data: dict[str, Any]) -> str:
    return lesson_id_from_media(str(data.get("media") or path.name))


def document_id(path: Path) -> str:
    return normalize_stem(path.name)


def collect_transcripts(source_dir: Path) -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    for path in sorted(source_dir.glob("transcripts/**/*.json")):
        try:
            data = load_json(path)
        except Exception:
            data = {}
        if not isinstance(data, dict):
            data = {}
        lesson_id = transcript_id(path, data) or normalize_stem(path.name)
        rows[lesson_id] = {"path": path, "data": data}
    return rows


def collect_analyses(source_dir: Path) -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    for path in sorted(source_dir.glob("analysis/**/*_analysis.md")):
        lesson_id = analysis_id(path)
        rows[lesson_id] = {"path": path, "text": read_text(path)}
    return rows


def collect_manifests(source_dir: Path) -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    for path in sorted(source_dir.glob("keyframe_selection/*_model_keyframes_manifest.json")):
        try:
            data = load_json(path)
        except Exception:
            data = {}
        if not isinstance(data, dict):
            data = {}
        lesson_id = manifest_id(path, data)
        rows[lesson_id] = {"path": path, "data": data}
    return rows


def collect_documents(source_dir: Path) -> dict[str, list[dict[str, Any]]]:
    rows: dict[str, list[dict[str, Any]]] = {}
    for pattern in ("documents/**/*.md", "documents/**/*.txt"):
        for path in sorted(source_dir.glob(pattern)):
            lesson_id = document_id(path)
            rows.setdefault(lesson_id, []).append({"path": path, "text": read_text(path)})
    return rows


def collect_lesson_summaries(source_dir: Path) -> dict[str, dict[str, Any]]:
    path = source_dir / "lesson_summaries.json"
    if not path.exists():
        return {}
    try:
        data = load_json(path)
    except Exception:
        return {}
    items = data if isinstance(data, list) else data.get("lesson_summaries", []) if isinstance(data, dict) else []
    rows: dict[str, dict[str, Any]] = {}
    for idx, item in enumerate(items, 1):
        if not isinstance(item, dict):
            continue
        raw_id = item.get("video") or item.get("source") or item.get("file") or item.get("id") or f"lesson-{idx:03d}"
        rows[lesson_id_from_media(str(raw_id))] = item
    return rows


def contains_any(text: str, terms: tuple[str, ...]) -> bool:
    lowered = text.lower()
    return any(term.lower() in lowered for term in terms)


def numeric_duration_seconds(value: Any) -> float | None:
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str) and re.fullmatch(r"\d+(\.\d+)?", value.strip()):
        return float(value)
    return None


def matching_documents(lesson_id: str, documents: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    matches: list[dict[str, Any]] = []
    for doc_id, rows in documents.items():
        if lesson_id and (lesson_id in doc_id or doc_id in lesson_id):
            matches.extend(rows)
    return matches


def cross_validation_policy(audit_mode: str, source_count: int) -> dict[str, Any]:
    if audit_mode == "off":
        return {
            "mode": audit_mode,
            "required": False,
            "reason": "cross validation disabled by audit mode",
        }
    if audit_mode == "strict":
        return {
            "mode": audit_mode,
            "required": True,
            "reason": "strict audit mode requires review of missing or conflicting sources",
        }
    return {
        "mode": audit_mode,
        "required": source_count >= 2,
        "reason": "auto mode validates across sources only when comparable sources are available",
    }


def related_text_trace(source_dir: Path, lesson_id: str) -> dict[str, list[str]]:
    chunks_path = source_dir / "text_sources" / "chunks.jsonl"
    cards_path = source_dir / "text_distillation" / "evidence_cards.jsonl"
    chunks = load_jsonl(chunks_path)
    cards = load_jsonl(cards_path)
    matched_chunks = []
    for chunk in chunks:
        source_ref = str(chunk.get("source_ref") or chunk.get("source_path") or "")
        if lesson_id and lesson_id in normalize_stem(source_ref):
            matched_chunks.append(rel(chunks_path, source_dir))
            break
    matched_cards = []
    for card in cards:
        source_ref = str(card.get("source_ref") or card.get("source_path") or "")
        title = str(card.get("title") or "")
        if lesson_id and (lesson_id in normalize_stem(source_ref) or lesson_id in normalize_stem(title)):
            matched_cards.append(rel(cards_path, source_dir))
            break
    return {"text_chunks": matched_chunks, "evidence_cards": matched_cards}


def source_inventory(source_dir: Path) -> dict[str, Any]:
    transcripts = sorted(source_dir.glob("transcripts/**/*.json"))
    analyses = sorted(source_dir.glob("analysis/**/*_analysis.md"))
    screenshots = sorted(path for path in source_dir.glob("analysis/screenshots/**/*") if path.is_file())
    manifests = sorted(source_dir.glob("keyframe_selection/*_model_keyframes_manifest.json"))
    keyframes = sorted(path for path in source_dir.glob("keyframes_model_selected/**/*") if path.is_file())
    documents = sorted(source_dir.glob("documents/**/*.md")) + sorted(source_dir.glob("documents/**/*.txt"))
    text_sources = sorted(source_dir.glob("text_sources/**/*.json*"))
    text_distillation = sorted(source_dir.glob("text_distillation/**/*"))
    lesson_summaries = [source_dir / "lesson_summaries.json"] if (source_dir / "lesson_summaries.json").exists() else []
    packages = [source_dir / "course_package.json"] if (source_dir / "course_package.json").exists() else []
    return {
        "transcripts": inventory(transcripts, source_dir),
        "visual_analyses": inventory(analyses, source_dir),
        "screenshots": inventory(screenshots, source_dir),
        "keyframe_manifests": inventory(manifests, source_dir),
        "model_selected_keyframes": inventory(keyframes, source_dir),
        "documents": inventory(documents, source_dir),
        "text_sources": inventory([path for path in text_sources if path.is_file()], source_dir),
        "text_distillation": inventory([path for path in text_distillation if path.is_file()], source_dir),
        "lesson_summaries": inventory(lesson_summaries, source_dir),
        "packages": inventory(packages, source_dir),
    }


def build_lesson(
    lesson_id: str,
    source_dir: Path,
    *,
    transcript: dict[str, Any] | None,
    analysis: dict[str, Any] | None,
    manifest: dict[str, Any] | None,
    documents: list[dict[str, Any]],
    summary: dict[str, Any] | None,
    audit_mode: str,
) -> dict[str, Any]:
    transcript_data = transcript.get("data", {}) if transcript else {}
    transcript_text = str(transcript_data.get("full_text") or transcript_data.get("text") or "")
    transcript_len = len(transcript_text.strip())
    duration = transcript_data.get("duration") or transcript_data.get("duration_seconds")
    numeric_duration = numeric_duration_seconds(duration)
    analysis_text = analysis.get("text", "") if analysis else ""
    document_text_len = sum(len(item["text"].strip()) for item in documents)
    keyframe_count = 0
    if manifest:
        data = manifest.get("data", {})
        keyframe_count = int(data.get("selected_count") or len(data.get("selected") or data.get("keyframes") or []))
    source_count = sum([bool(transcript), bool(analysis), bool(documents)])
    policy = cross_validation_policy(audit_mode, source_count)

    flags: list[str] = []
    if source_count >= 2:
        flags.append("supported_by_multiple_sources")
    elif source_count == 1:
        flags.append("single_source_available")
    if policy["required"] and not transcript:
        flags.append("missing_transcript")
    if policy["required"] and not analysis:
        flags.append("missing_visual_analysis")
    if policy["required"] and analysis and not transcript:
        flags.append("visual_only_claims")
    if policy["required"] and transcript and not analysis:
        flags.append("spoken_but_not_in_slides")
    if policy["required"] and analysis and contains_any(analysis_text, SLIDE_TERMS + DIAGRAM_TERMS + DEMO_TERMS) and not transcript_text:
        flags.append("slides_not_mentioned_in_transcript")
    if policy["required"] and transcript and analysis and contains_any(analysis_text, SLIDE_TERMS + DIAGRAM_TERMS + DEMO_TERMS):
        if not contains_any(transcript_text, ("图", "表", "课件", "ppt", "演示", "软件", "流程")):
            flags.append("transcript_visual_mismatch")
    if transcript_len < 20:
        flags.append("manual_review_required")
    if contains_any(transcript_text + "\n" + analysis_text + "\n" + "\n".join(item["text"] for item in documents), TERM_REVIEW_TERMS):
        flags.append("terminology_needs_review")
    if "terminology_needs_review" in flags or "missing_transcript" in flags or "missing_visual_analysis" in flags:
        flags.append("manual_review_required")

    flags = list(dict.fromkeys(flags))
    review_notes = []
    if "manual_review_required" in flags:
        review_notes.append("请人工复核本课的转录、课件/OCR、画面分析和术语一致性。")
    if "terminology_needs_review" in flags:
        review_notes.append("请重点检查专业术语、专名、同音误识别、ASR/OCR 错字。")

    trace = {
        "transcripts": [rel(transcript["path"], source_dir)] if transcript else [],
        "full_transcript": ["full_transcript.md"] if (source_dir / "full_transcript.md").exists() else [],
        "visual_analyses": [rel(analysis["path"], source_dir)] if analysis else [],
        "keyframe_manifests": [rel(manifest["path"], source_dir)] if manifest else [],
        "documents": [rel(item["path"], source_dir) for item in documents],
        "text_chunks": [],
        "evidence_cards": [],
        "lesson_summaries": ["lesson_summaries.json"] if summary else [],
    }
    trace.update(related_text_trace(source_dir, lesson_id))

    title = ""
    if summary:
        title = str(summary.get("title") or summary.get("lesson_name") or summary.get("video") or "")
    if not title:
        title = str(transcript_data.get("title") or transcript_data.get("video_name") or lesson_id)

    return {
        "lesson_id": lesson_id,
        "title": title,
        "media_ref": str(transcript_data.get("video_name") or lesson_id),
        "transcript_status": {
            "present": bool(transcript),
            "duration_seconds": duration,
            "text_length": transcript_len,
            "empty": bool(transcript and transcript_len == 0),
            "short_text": bool(transcript and transcript_len < 20),
            "probable_truncation": bool(numeric_duration and transcript_len and numeric_duration > 900 and transcript_len < 100),
            "terms_need_review": "terminology_needs_review" in flags,
        },
        "visual_status": {
            "present": bool(analysis),
            "analysis_length": len(analysis_text.strip()),
            "keyframe_count": keyframe_count,
            "screenshot_marker_count": len(SCREENSHOT_RE.findall(analysis_text)),
            "contains_slides_or_courseware": contains_any(analysis_text, SLIDE_TERMS),
            "contains_board_writing": contains_any(analysis_text, BOARD_TERMS),
            "contains_demo_or_software": contains_any(analysis_text, DEMO_TERMS),
            "contains_diagrams_or_tables": contains_any(analysis_text, DIAGRAM_TERMS),
        },
        "document_status": {
            "present": bool(documents),
            "paths": [rel(item["path"], source_dir) for item in documents],
            "text_length": document_text_len,
            "empty_or_short_text": bool(documents and document_text_len < 20),
        },
        "cross_validation": {
            "policy": policy,
            "source_count": source_count,
            "flags": flags,
            "review_recommendations": review_notes,
        },
        "traceability": trace,
    }


def build_audit(course_name: str, source_dir: Path, audit_mode: str = "auto") -> dict[str, Any]:
    source_dir = source_dir.expanduser().resolve()
    if audit_mode not in AUDIT_MODES:
        raise ValueError(f"audit_mode must be one of {sorted(AUDIT_MODES)}")
    transcripts = collect_transcripts(source_dir)
    analyses = collect_analyses(source_dir)
    manifests = collect_manifests(source_dir)
    documents = collect_documents(source_dir)
    summaries = collect_lesson_summaries(source_dir)

    lesson_ids = sorted(set(transcripts) | set(analyses) | set(manifests) | set(summaries))
    lessons = []
    matched_doc_ids: set[str] = set()
    for lesson_id in lesson_ids:
        docs = matching_documents(lesson_id, documents)
        for doc in docs:
            matched_doc_ids.add(document_id(doc["path"]))
        lessons.append(
            build_lesson(
                lesson_id,
                source_dir,
                transcript=transcripts.get(lesson_id),
                analysis=analyses.get(lesson_id),
                manifest=manifests.get(lesson_id),
                documents=docs,
                summary=summaries.get(lesson_id),
                audit_mode=audit_mode,
            )
        )

    unmatched_documents = sum(1 for doc_id in documents if doc_id not in matched_doc_ids)
    manual_review_lessons = [lesson for lesson in lessons if "manual_review_required" in lesson["cross_validation"]["flags"]]
    multi_source_lessons = [lesson for lesson in lessons if "supported_by_multiple_sources" in lesson["cross_validation"]["flags"]]
    source_conflicts = [
        lesson
        for lesson in lessons
        if {"transcript_visual_mismatch", "slides_not_mentioned_in_transcript"} & set(lesson["cross_validation"]["flags"])
    ]
    evidence_cards = load_jsonl(source_dir / "text_distillation" / "evidence_cards.jsonl")
    teacher_card_types = ["attention_cue", "problem_frame", "decision_rule", "demonstration", "feedback_pattern", "progression_rule", "graduation_signal", "non_copyable_context"]
    teacher_counts = {kind: sum(card.get("card_type") == kind for card in evidence_cards) for kind in teacher_card_types}
    mentor_evidence_gaps = [kind for kind, count in teacher_counts.items() if count == 0]

    audit = {
        "schema_version": "1.0",
        "generated_at": dt.datetime.now().isoformat(timespec="seconds"),
        "course_name": course_name,
        "source_dir": str(source_dir),
        "audit_mode": audit_mode,
        "source_inventory": source_inventory(source_dir),
        "coverage_summary": {
            "expected_lessons": len(lesson_ids),
            "available_transcripts": len(transcripts),
            "available_visual_analyses": len(analyses),
            "available_document_groups": len(documents),
            "available_text_sources": len(load_jsonl(source_dir / "text_sources" / "chunks.jsonl")),
            "available_evidence_cards": len(load_jsonl(source_dir / "text_distillation" / "evidence_cards.jsonl")),
            "missing_transcripts": sum(1 for lesson in lessons if not lesson["transcript_status"]["present"]),
            "missing_visual_analyses": sum(1 for lesson in lessons if not lesson["visual_status"]["present"]),
            "unmatched_documents": unmatched_documents,
        },
        "mentor_evidence": {
            "card_counts": teacher_counts,
            "missing_teacher_evidence": mentor_evidence_gaps,
            "status": "ready" if not mentor_evidence_gaps else "partial",
            "note": "A mentor-evidence gap is distinct from source-capture failure. Missing teacher behavior must not be synthesized as teacher fact.",
        },
        "cross_validation_summary": {
            "multi_source_lessons": len(multi_source_lessons),
            "transcript_only_lessons": sum(
                1
                for lesson in lessons
                if lesson["transcript_status"]["present"]
                and not lesson["visual_status"]["present"]
                and not lesson["document_status"]["present"]
            ),
            "visual_only_lessons": sum(
                1 for lesson in lessons if lesson["visual_status"]["present"] and not lesson["transcript_status"]["present"]
            ),
            "document_only_groups": unmatched_documents,
            "source_conflicts": len(source_conflicts),
            "manual_review_required": len(manual_review_lessons) + unmatched_documents,
            "terminology_review_lessons": sum(
                1 for lesson in lessons if "terminology_needs_review" in lesson["cross_validation"]["flags"]
            ),
        },
        "manual_review": [
            "人工校对建议：请复核专业术语、专名、同音误识别、OCR 错字，以及转录与课件不一致处。",
            "本报告为自动审计结果，不能替代对原始课程材料的人工核对。",
        ],
        "lessons": lessons,
    }
    if unmatched_documents:
        audit["manual_review"].append(f"发现 {unmatched_documents} 组未匹配到具体课程的文档/文字稿，请人工确认归属。")
    if mentor_evidence_gaps:
        audit["manual_review"].append("师承证据缺口：" + "、".join(mentor_evidence_gaps) + "。这些字段不得伪装为老师原意。")
    return audit


def render_markdown(audit: dict[str, Any]) -> str:
    coverage = audit["coverage_summary"]
    cross = audit["cross_validation_summary"]
    lines = [
        f"# {audit['course_name']} Distillation Audit",
        "",
        "## Summary",
        "",
        f"- Expected lessons: {coverage['expected_lessons']}",
        f"- Transcripts: {coverage['available_transcripts']}",
        f"- Visual analyses: {coverage['available_visual_analyses']}",
        f"- Document groups: {coverage['available_document_groups']}",
        f"- Multi-source lessons: {cross['multi_source_lessons']}",
        f"- Manual review required: {cross['manual_review_required']}",
        f"- Mentor evidence status: {audit.get('mentor_evidence', {}).get('status', 'unknown')}",
        "",
        "## Manual Review",
        "",
    ]
    lines.extend(f"- {note}" for note in audit.get("manual_review", []))
    lines.extend(["", "## Lessons", ""])
    for lesson in audit.get("lessons", []):
        flags = ", ".join(lesson["cross_validation"]["flags"]) or "none"
        lines.extend(
            [
                f"### {lesson['title'] or lesson['lesson_id']}",
                "",
                f"- Lesson id: `{lesson['lesson_id']}`",
                f"- Transcript: {'present' if lesson['transcript_status']['present'] else 'missing'}; text length {lesson['transcript_status']['text_length']}",
                f"- Visual analysis: {'present' if lesson['visual_status']['present'] else 'missing'}; keyframes {lesson['visual_status']['keyframe_count']}",
                f"- Documents: {'present' if lesson['document_status']['present'] else 'missing'}",
                f"- Cross-validation flags: {flags}",
            ]
        )
        for note in lesson["cross_validation"].get("review_recommendations", []):
            lines.append(f"- Review: {note}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def write_audit(course_name: str, source_dir: Path, audit_mode: str = "auto") -> dict[str, str]:
    audit = build_audit(course_name, source_dir, audit_mode=audit_mode)
    json_path = source_dir / "distillation_audit.json"
    markdown_path = source_dir / "distillation_audit.md"
    json_path.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown_path.write_text(render_markdown(audit), encoding="utf-8")
    return {"json_path": json_path.name, "markdown_path": markdown_path.name}


def main() -> None:
    parser = argparse.ArgumentParser(description="Build final distillation quality and cross-validation audit files.")
    parser.add_argument("--course-name", required=True)
    parser.add_argument("--source-dir", required=True)
    parser.add_argument(
        "--audit-mode",
        choices=sorted(AUDIT_MODES),
        default="auto",
        help="Cross-validation policy: auto validates only when comparable sources exist, strict requires review, off records inventory only.",
    )
    args = parser.parse_args()

    source_dir = Path(args.source_dir).expanduser().resolve()
    if not source_dir.is_dir():
        raise SystemExit(f"source dir does not exist: {source_dir}")
    result = write_audit(args.course_name, source_dir, audit_mode=args.audit_mode)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
