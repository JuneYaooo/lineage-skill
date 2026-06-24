from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from build_course_package import build_package


def test_build_package_merges_text_evidence_cards(tmp_path: Path) -> None:
    course_dir = tmp_path / "course"
    cards_dir = course_dir / "text_distillation"
    cards_dir.mkdir(parents=True)
    cards = [
        {
            "card_id": "card-1",
            "card_type": "concept",
            "title": "证据优先",
            "summary": "先保留来源再综合。",
            "source_ref": "notes.md",
            "chunk_id": "chunk-1",
            "confidence": "medium",
        },
        {
            "card_id": "card-2",
            "card_type": "method",
            "title": "三步蒸馏",
            "summary": "采集、引用、压缩。",
            "source_ref": "notes.md",
            "chunk_id": "chunk-1",
            "confidence": "medium",
        },
        {
            "card_id": "card-3",
            "card_type": "quote",
            "title": "慢就是快",
            "quote": "慢就是快。",
            "source_ref": "notes.md",
            "chunk_id": "chunk-2",
            "confidence": "medium",
        },
        {
            "card_id": "card-4",
            "card_type": "boundary",
            "title": "证据边界",
            "summary": "没有来源就标记为推断。",
            "source_ref": "notes.md",
            "chunk_id": "chunk-3",
            "confidence": "medium",
        },
    ]
    (cards_dir / "evidence_cards.jsonl").write_text(
        "\n".join(json.dumps(card, ensure_ascii=False) for card in cards) + "\n",
        encoding="utf-8",
    )

    package = build_package("Demo", course_dir)

    assert any("证据优先" in item for item in package["concepts"])
    assert any("三步蒸馏" in item for item in package["methods"])
    assert any("慢就是快" in item for item in package["quotes"])
    assert any("证据边界" in item for item in package["boundaries"])
    assert any(row["type"] == "text_evidence_card" for row in package["evidence"])


def test_build_package_merges_capability_evidence_cards(tmp_path: Path) -> None:
    course_dir = tmp_path / "course"
    cards_dir = course_dir / "text_distillation"
    cards_dir.mkdir(parents=True)
    cards = [
        {
            "card_id": "card-diagnostic",
            "card_type": "diagnostic",
            "title": "定位卡点",
            "summary": "先判断问题卡在目标、资源还是反馈。",
            "source_ref": "book.md",
            "chunk_index": 2,
        },
        {
            "card_id": "card-workflow",
            "card_type": "workflow",
            "title": "三步执行",
            "summary": "界定目标、拆出动作、按结果复盘。",
            "source_ref": "book.md",
            "chunk_index": 3,
        },
        {
            "card_id": "card-rubric",
            "card_type": "rubric",
            "title": "质量标准",
            "summary": "产出必须具体、可检查、能复用。",
            "source_ref": "book.md",
            "chunk_index": 4,
        },
        {
            "card_id": "card-template",
            "card_type": "template",
            "title": "复盘模板",
            "summary": "事实、判断、动作、下次检查。",
            "source_ref": "book.md",
            "chunk_index": 5,
        },
        {
            "card_id": "card-transfer",
            "card_type": "transfer",
            "title": "迁移规则",
            "summary": "先找相同约束，再替换领域变量。",
            "source_ref": "book.md",
            "chunk_index": 6,
        },
        {
            "card_id": "card-failure",
            "card_type": "failure_mode",
            "title": "常见误用",
            "summary": "把作者结论脱离适用条件直接套用。",
            "source_ref": "book.md",
            "chunk_index": 7,
        },
    ]
    (cards_dir / "evidence_cards.jsonl").write_text(
        "\n".join(json.dumps(card, ensure_ascii=False) for card in cards) + "\n",
        encoding="utf-8",
    )

    package = build_package("Demo", course_dir)

    assert any("定位卡点" in item for item in package["diagnostics"])
    assert any("三步执行" in item for item in package["workflows"])
    assert any("质量标准" in item for item in package["rubrics"])
    assert any("复盘模板" in item for item in package["templates"])
    assert any("迁移规则" in item for item in package["transfer_rules"])
    assert any("常见误用" in item for item in package["failure_modes"])
