from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from distill_course import (
    build_analysis_lookup,
    build_course_digest,
    load_keyframe_manifest,
    load_text_synthesis,
    local_course_digest,
    lookup_analysis,
    screenshot_count_for_video,
)
from run_course_pipeline import build_text_distill_command, should_run_media_capture


def test_load_text_synthesis_reads_distillation_artifact(tmp_path: Path) -> None:
    course_dir = tmp_path / "course"
    artifact = course_dir / "text_distillation" / "text_course_synthesis.md"
    artifact.parent.mkdir(parents=True)
    artifact.write_text("# Text\n\n## 关键概念\n- 证据优先", encoding="utf-8")

    assert "证据优先" in load_text_synthesis(str(course_dir))


def test_local_course_digest_includes_text_synthesis() -> None:
    transcripts = [{"duration": 60, "full_text": "老师讲了课程主线。", "video": "lesson1"}]
    summaries = [{"video": "lesson1", "summary": "本课讲课程主线。"}]
    text_synthesis = "## 关键概念\n- 证据优先（notes.md#0）"

    digest = local_course_digest(transcripts, summaries, "Demo", text_synthesis=text_synthesis)

    assert "文字资料补充" in digest
    assert "证据优先" in digest


def test_distill_course_matches_visual_evidence_when_transcript_has_parent_prefix(tmp_path: Path) -> None:
    course_dir = tmp_path / "course"
    analyses = [
        {
            "video": "需求挖掘与分析（1）-需求定义（1）",
            "content": "PPT 展示需求定义、用户场景和需求边界。",
        }
    ]

    lookup = build_analysis_lookup(analyses)

    transcript_video = "4、需求采集与挖掘_需求挖掘与分析（1）-需求定义（1）"
    assert lookup_analysis(lookup, transcript_video) == "PPT 展示需求定义、用户场景和需求边界。"

    manifest_dir = course_dir / "keyframe_selection"
    manifest_dir.mkdir(parents=True)
    manifest_dir.joinpath(
        "4、需求采集与挖掘_需求挖掘与分析（1）-需求定义（1）_model_keyframes_manifest.json"
    ).write_text('{"media": "4、需求采集与挖掘_需求挖掘与分析（1）-需求定义（1）", "selected_count": 3}', encoding="utf-8")
    assert load_keyframe_manifest(str(course_dir), "需求挖掘与分析（1）-需求定义（1）")["selected_count"] == 3

    screenshot_dir = course_dir / "analysis" / "screenshots" / "需求挖掘与分析（1）-需求定义（1）"
    screenshot_dir.mkdir(parents=True)
    screenshot_dir.joinpath("00_10_需求定义.jpg").write_text("fake", encoding="utf-8")
    assert screenshot_count_for_video(str(course_dir), transcript_video) == 1


def test_distill_course_matches_axure_parent_prefix(tmp_path: Path) -> None:
    course_dir = tmp_path / "course"
    analyses = [{"video": "Axure基础课程1", "content": "软件界面展示 Axure 组件。"}]

    lookup = build_analysis_lookup(analyses)

    transcript_video = "AXURE基础课_Axure基础课程1"
    assert lookup_analysis(lookup, transcript_video) == "软件界面展示 Axure 组件。"

    manifest_dir = course_dir / "keyframe_selection"
    manifest_dir.mkdir(parents=True)
    manifest_dir.joinpath("AXURE基础课_Axure基础课程1_model_keyframes_manifest.json").write_text(
        '{"media": "AXURE基础课_Axure基础课程1", "selected_count": 2}',
        encoding="utf-8",
    )
    assert load_keyframe_manifest(str(course_dir), "Axure基础课程1")["selected_count"] == 2


def test_build_course_digest_supports_text_only_course(tmp_path: Path, monkeypatch) -> None:
    course_dir = tmp_path / "course"
    artifact = course_dir / "text_distillation" / "text_course_synthesis.md"
    artifact.parent.mkdir(parents=True)
    artifact.write_text("## 方法流程\n- 先证据，后综合", encoding="utf-8")
    monkeypatch.setenv("DISTILL_USE_LLM", "0")

    digest = build_course_digest([], [], "Demo", str(course_dir))

    assert digest["total_lessons"] == 0
    assert "先证据，后综合" in digest["distillation_markdown"]


def test_build_text_distill_command_includes_text_and_notes_inputs(tmp_path: Path) -> None:
    args = argparse.Namespace(
        course_name="Demo",
        text_input=["/tmp/handout.md"],
        notes_input=["/tmp/notes"],
        include_existing_documents=True,
        text_max_chars=4000,
        text_overlap_chars=200,
        text_no_llm=True,
    )

    cmd = build_text_distill_command(
        py="python",
        root=tmp_path,
        args=args,
        base_dir=tmp_path / ".lineage" / "courses",
    )

    assert "distill_text_course.py" in " ".join(cmd)
    assert cmd.count("--input") == 2
    assert "--include-existing-documents" in cmd
    assert "--no-llm" in cmd
    assert ["--max-chars", "4000"] == [cmd[cmd.index("--max-chars")], cmd[cmd.index("--max-chars") + 1]]


def test_media_capture_is_optional_for_text_only_pipeline() -> None:
    args = argparse.Namespace(input_dir=None)

    assert should_run_media_capture(args) is False
