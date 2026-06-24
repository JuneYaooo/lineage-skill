from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from distill_text_course import build_local_cards, distill_text_course


def test_build_local_cards_extracts_structured_course_evidence() -> None:
    chunk = {
        "chunk_id": "chunk-1",
        "source_id": "source-1",
        "source_path": "lesson.md",
        "source_ref": "lesson.md",
        "chunk_index": 0,
        "char_start": 0,
        "char_end": 80,
        "content_sha256": "a" * 64,
        "text": "\n".join(
            [
                "概念：复利增长是长期积累后的非线性结果。",
                "方法：先定义目标，再拆解约束，最后设计行动。",
                "案例：老师用三个月复盘项目说明节奏管理。",
                "边界：没有数据时不要假装精确。",
                "金句：慢就是快。",
                "任务：每周复盘一次。",
            ]
        ),
    }

    cards = build_local_cards(chunk)

    assert {card["card_type"] for card in cards} >= {
        "concept",
        "method",
        "case",
        "boundary",
        "quote",
        "task",
    }
    assert all(card["source_ref"] == "lesson.md" for card in cards)
    assert all(card["chunk_id"] == "chunk-1" for card in cards)
    quote = next(card for card in cards if card["card_type"] == "quote")
    assert quote["quote"] == "慢就是快。"


def test_build_local_cards_extracts_capability_evidence() -> None:
    chunk = {
        "chunk_id": "chunk-1",
        "source_id": "source-1",
        "source_path": "book.md",
        "source_ref": "book.md",
        "chunk_index": 0,
        "char_start": 0,
        "char_end": 120,
        "content_sha256": "a" * 64,
        "text": "\n".join(
            [
                "诊断：先定位目标、资源、反馈哪一处断裂。",
                "工作流：界定目标、拆动作、按结果复盘。",
                "标准：产出必须具体、可检查、能复用。",
                "模板：事实、判断、动作、下次检查。",
                "迁移：先找相同约束，再替换领域变量。",
                "误用：脱离适用条件直接套用结论。",
            ]
        ),
    }

    cards = build_local_cards(chunk)

    assert {card["card_type"] for card in cards} >= {
        "diagnostic",
        "workflow",
        "rubric",
        "template",
        "transfer",
        "failure_mode",
    }


def test_distill_text_course_writes_cards_synthesis_and_quality(tmp_path: Path) -> None:
    material = tmp_path / "notes.md"
    material.write_text(
        "\n".join(
            [
                "# 课程笔记",
                "概念：证据优先。",
                "方法：先保留来源，再做综合。",
                "案例：PDF 讲义补充了视频没有讲清楚的定义。",
            ]
        ),
        encoding="utf-8",
    )
    course_dir = tmp_path / "course"

    result = distill_text_course(
        course_name="Demo",
        course_dir=course_dir,
        input_paths=[material],
        include_existing_documents=False,
        use_llm=False,
        max_chars=200,
        overlap_chars=0,
    )

    cards_path = course_dir / "text_distillation" / "evidence_cards.jsonl"
    quality_path = course_dir / "text_distillation" / "text_distillation_quality.json"
    synthesis_path = course_dir / "text_distillation" / "text_course_synthesis.md"

    cards = [json.loads(line) for line in cards_path.read_text(encoding="utf-8").splitlines()]
    quality = json.loads(quality_path.read_text(encoding="utf-8"))
    synthesis = synthesis_path.read_text(encoding="utf-8")

    assert result["card_count"] == len(cards)
    assert quality["source_count"] == 1
    assert quality["card_count"] >= 3
    assert quality["llm_used"] is False
    assert "## 关键概念" in synthesis
    assert "证据优先" in synthesis
