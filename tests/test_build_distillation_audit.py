from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from build_distillation_audit import build_audit, render_markdown, write_audit


def write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def test_build_audit_records_multisource_lesson_traceability_and_review(tmp_path: Path) -> None:
    course_dir = tmp_path / "course"
    write_json(
        course_dir / "transcripts" / "lesson1_transcript.json",
        {
            "video_name": "lesson1",
            "duration": 3600,
            "full_text": "本节讲证据优先、交叉核验和人工校对。术语 Lineage Skill 需要保持一致。",
        },
    )
    (course_dir / "analysis").mkdir(parents=True)
    (course_dir / "analysis" / "lesson1_analysis.md").write_text(
        "# lesson1\n\nPPT 展示证据优先流程，包含图表、软件 screens 和 [SCREENSHOT 03:21]。",
        encoding="utf-8",
    )
    write_json(
        course_dir / "keyframe_selection" / "lesson1_model_keyframes_manifest.json",
        {
            "media": "lesson1",
            "selected_count": 2,
            "selected": [{"frame": "frame_0001.jpg", "timestamp": "00:10", "reason": "PPT evidence"}],
        },
    )
    (course_dir / "documents").mkdir(parents=True)
    (course_dir / "documents" / "lesson1.md").write_text(
        "# lesson1 courseware\n\n证据优先流程。人工校对专业术语。",
        encoding="utf-8",
    )
    (course_dir / "text_sources").mkdir(parents=True)
    (course_dir / "text_sources" / "chunks.jsonl").write_text(
        json.dumps(
            {
                "chunk_id": "lesson1-chunk-1",
                "source_ref": "documents/lesson1.md",
                "chunk_index": 0,
                "char_start": 0,
                "char_end": 30,
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    (course_dir / "text_distillation").mkdir(parents=True)
    (course_dir / "text_distillation" / "evidence_cards.jsonl").write_text(
        json.dumps(
            {
                "card_id": "card-1",
                "card_type": "method",
                "title": "证据优先",
                "summary": "先保留来源，再交叉核验。",
                "source_ref": "documents/lesson1.md",
                "chunk_index": 0,
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    write_json(
        course_dir / "lesson_summaries.json",
        [
            {
                "video": "lesson1",
                "title": "第一课：证据优先",
                "summary": "讲解证据优先和交叉核验。",
                "keywords": ["证据优先", "交叉核验"],
            }
        ],
    )

    audit = build_audit("Demo Course", course_dir)

    assert audit["course_name"] == "Demo Course"
    assert audit["source_inventory"]["transcripts"]["count"] == 1
    assert audit["source_inventory"]["visual_analyses"]["count"] == 1
    assert audit["source_inventory"]["documents"]["count"] == 1
    assert audit["coverage_summary"]["available_transcripts"] == 1
    assert audit["cross_validation_summary"]["multi_source_lessons"] == 1
    assert audit["cross_validation_summary"]["manual_review_required"] >= 1

    lesson = audit["lessons"][0]
    assert lesson["lesson_id"] == "lesson1"
    assert lesson["transcript_status"]["present"] is True
    assert lesson["visual_status"]["present"] is True
    assert lesson["visual_status"]["keyframe_count"] == 2
    assert lesson["visual_status"]["contains_slides_or_courseware"] is True
    assert lesson["document_status"]["present"] is True
    assert "supported_by_multiple_sources" in lesson["cross_validation"]["flags"]
    assert "terminology_needs_review" in lesson["cross_validation"]["flags"]
    assert "transcripts/lesson1_transcript.json" in lesson["traceability"]["transcripts"]
    assert "analysis/lesson1_analysis.md" in lesson["traceability"]["visual_analyses"]
    assert "documents/lesson1.md" in lesson["traceability"]["documents"]
    assert "text_distillation/evidence_cards.jsonl" in lesson["traceability"]["evidence_cards"]

    markdown = render_markdown(audit)
    assert "人工校对建议" in markdown
    assert "本报告为自动审计结果" in markdown
    assert "第一课：证据优先" in markdown


def test_build_audit_matches_transcript_and_visual_analysis_when_transcript_has_parent_prefix(tmp_path: Path) -> None:
    course_dir = tmp_path / "course"
    write_json(
        course_dir / "transcripts" / "4、需求采集与挖掘_需求挖掘与分析（1）-需求定义（1）_transcript.json",
        {
            "video": "4、需求采集与挖掘_需求挖掘与分析（1）-需求定义（1）",
            "duration": 3600,
            "full_text": "老师讲需求定义、用户场景和需求边界，需要结合课件术语做校对。",
        },
    )
    (course_dir / "analysis").mkdir(parents=True)
    (course_dir / "analysis" / "需求挖掘与分析（1）-需求定义（1）_analysis.md").write_text(
        "# 需求挖掘与分析（1）-需求定义（1）\n\nPPT 展示需求定义、用户场景、需求边界和 [SCREENSHOT 03:21]。",
        encoding="utf-8",
    )
    write_json(
        course_dir
        / "keyframe_selection"
        / "4、需求采集与挖掘_需求挖掘与分析（1）-需求定义（1）_model_keyframes_manifest.json",
        {
            "media": "4、需求采集与挖掘_需求挖掘与分析（1）-需求定义（1）",
            "selected_count": 1,
            "selected": [{"timestamp": "03:21", "reason": "PPT 术语页"}],
        },
    )
    write_json(
        course_dir / "lesson_summaries.json",
        [
            {
                "video": "4、需求采集与挖掘_需求挖掘与分析（1）-需求定义（1）",
                "title": "需求定义",
                "summary": "讲解需求定义。",
            }
        ],
    )

    audit = build_audit("PM Course", course_dir)

    assert audit["coverage_summary"]["expected_lessons"] == 1
    assert audit["coverage_summary"]["missing_transcripts"] == 0
    assert audit["coverage_summary"]["missing_visual_analyses"] == 0
    assert audit["cross_validation_summary"]["multi_source_lessons"] == 1

    lesson = audit["lessons"][0]
    assert lesson["title"] == "需求定义"
    assert lesson["transcript_status"]["present"] is True
    assert lesson["visual_status"]["present"] is True
    assert lesson["visual_status"]["keyframe_count"] == 1
    assert "supported_by_multiple_sources" in lesson["cross_validation"]["flags"]
    assert (
        "transcripts/4、需求采集与挖掘_需求挖掘与分析（1）-需求定义（1）_transcript.json"
        in lesson["traceability"]["transcripts"]
    )
    assert (
        "analysis/需求挖掘与分析（1）-需求定义（1）_analysis.md"
        in lesson["traceability"]["visual_analyses"]
    )


def test_build_audit_matches_axure_parent_prefix(tmp_path: Path) -> None:
    course_dir = tmp_path / "course"
    write_json(
        course_dir / "transcripts" / "AXURE基础课_Axure基础课程1_transcript.json",
        {
            "video": "AXURE基础课_Axure基础课程1",
            "duration": 3600,
            "full_text": "老师讲 Axure 基础组件和原型页面搭建，需要对照软件界面校正术语。",
        },
    )
    (course_dir / "analysis").mkdir(parents=True)
    (course_dir / "analysis" / "Axure基础课程1_analysis.md").write_text(
        "# Axure基础课程1\n\n软件 screen 展示 Axure 基础组件和 [SCREENSHOT 05:00]。",
        encoding="utf-8",
    )
    write_json(
        course_dir / "keyframe_selection" / "AXURE基础课_Axure基础课程1_model_keyframes_manifest.json",
        {
            "media": "AXURE基础课_Axure基础课程1",
            "selected_count": 1,
            "selected": [{"timestamp": "05:00", "reason": "Axure 软件界面"}],
        },
    )

    audit = build_audit("PM Course", course_dir)

    assert audit["coverage_summary"]["expected_lessons"] == 1
    assert audit["coverage_summary"]["missing_transcripts"] == 0
    assert audit["coverage_summary"]["missing_visual_analyses"] == 0
    assert audit["cross_validation_summary"]["multi_source_lessons"] == 1
    assert audit["lessons"][0]["visual_status"]["keyframe_count"] == 1


def test_build_audit_flags_missing_visual_short_transcript_and_unmatched_documents(tmp_path: Path) -> None:
    course_dir = tmp_path / "course"
    write_json(
        course_dir / "transcripts" / "lesson2_transcript.json",
        {"video_name": "lesson2", "duration": 1800, "full_text": "太短"},
    )
    (course_dir / "documents").mkdir(parents=True)
    (course_dir / "documents" / "unmatched-handout.md").write_text("未匹配讲义内容", encoding="utf-8")

    audit = build_audit("Sparse Course", course_dir)

    lesson = audit["lessons"][0]
    assert lesson["lesson_id"] == "lesson2"
    assert lesson["transcript_status"]["short_text"] is True
    assert lesson["visual_status"]["present"] is False
    assert "missing_visual_analysis" not in lesson["cross_validation"]["flags"]
    assert "manual_review_required" in lesson["cross_validation"]["flags"]
    assert audit["coverage_summary"]["unmatched_documents"] == 1


def test_build_audit_auto_mode_does_not_require_visual_analysis_for_transcript_only_materials(tmp_path: Path) -> None:
    course_dir = tmp_path / "course"
    write_json(
        course_dir / "transcripts" / "lesson1_transcript.json",
        {
            "video_name": "lesson1",
            "duration": 1800,
            "full_text": "这是一段完整的音频课程转录，资料里没有提供视频画面分析。",
        },
    )

    audit = build_audit("Audio Course", course_dir)

    lesson = audit["lessons"][0]
    assert lesson["cross_validation"]["policy"]["required"] is False
    assert "missing_visual_analysis" not in lesson["cross_validation"]["flags"]
    assert "manual_review_required" not in lesson["cross_validation"]["flags"]
    assert "single_source_available" in lesson["cross_validation"]["flags"]


def test_build_audit_strict_mode_requires_cross_source_review(tmp_path: Path) -> None:
    course_dir = tmp_path / "course"
    write_json(
        course_dir / "transcripts" / "lesson1_transcript.json",
        {
            "video_name": "lesson1",
            "duration": 1800,
            "full_text": "这是一段完整的课程转录，但严格模式要求检查是否缺少其他来源。",
        },
    )

    audit = build_audit("Strict Course", course_dir, audit_mode="strict")

    lesson = audit["lessons"][0]
    assert lesson["cross_validation"]["policy"]["required"] is True
    assert "missing_visual_analysis" in lesson["cross_validation"]["flags"]
    assert "manual_review_required" in lesson["cross_validation"]["flags"]


def test_write_audit_creates_json_and_markdown(tmp_path: Path) -> None:
    course_dir = tmp_path / "course"
    write_json(course_dir / "transcripts" / "lesson1_transcript.json", {"video_name": "lesson1", "full_text": "证据"})

    result = write_audit("Demo", course_dir)

    assert result["json_path"] == "distillation_audit.json"
    assert result["markdown_path"] == "distillation_audit.md"
    assert (course_dir / "distillation_audit.json").exists()
    assert (course_dir / "distillation_audit.md").exists()


def test_build_audit_tolerates_timestamp_duration_strings(tmp_path: Path) -> None:
    course_dir = tmp_path / "course"
    write_json(
        course_dir / "transcripts" / "lesson1_transcript.json",
        {"video_name": "lesson1", "duration": "01:02", "full_text": "这是一段足够长的课程转录内容。"},
    )

    audit = build_audit("Demo", course_dir)

    assert audit["lessons"][0]["transcript_status"]["duration_seconds"] == "01:02"
    assert audit["lessons"][0]["transcript_status"]["probable_truncation"] is False
