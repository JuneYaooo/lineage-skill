from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from build_okf_bundle import build_okf_bundle


def write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")


def test_build_okf_bundle_writes_progressive_markdown_concepts(tmp_path: Path) -> None:
    course_dir = tmp_path / "course"
    course_dir.mkdir()
    package = {
        "schema_version": "0.2",
        "manifest": {"course_name": "Demo Book", "source_dir": str(course_dir)},
        "concepts": ["证据优先：先保留来源再综合。"],
        "workflows": [
            {
                "card_id": "card-workflow",
                "card_type": "workflow",
                "title": "三步执行",
                "summary": "界定目标、拆出动作、按结果复盘。",
                "source_ref": "book.md",
                "chunk_id": "chunk-1",
                "chunk_index": 0,
            }
        ],
        "rubrics": ["质量标准：产出必须具体、可检查、能复用。"],
    }
    (course_dir / "course_package.json").write_text(json.dumps(package, ensure_ascii=False), encoding="utf-8")
    write_jsonl(
        course_dir / "text_sources" / "chunks.jsonl",
        [
            {
                "chunk_id": "chunk-1",
                "source_path": "book.md",
                "source_ref": "book.md",
                "chunk_index": 0,
                "char_start": 0,
                "char_end": 24,
                "text": "界定目标、拆出动作、按结果复盘。",
            }
        ],
    )

    output_dir = tmp_path / "okf"
    result = build_okf_bundle(course_dir=course_dir, output_dir=output_dir, course_name="Demo Book")

    assert result["concept_count"] == 3
    assert result["evidence_count"] == 1
    root_index = (output_dir / "index.md").read_text(encoding="utf-8")
    workflow_files = list((output_dir / "workflows").glob("*.md"))
    workflow = workflow_files[0].read_text(encoding="utf-8")
    evidence = (output_dir / "evidence" / "chunk-1.md").read_text(encoding="utf-8")

    assert "## Workflows" in root_index
    assert "type: Workflow" in workflow
    assert "title: 三步执行" in workflow
    assert "[Source chunk](../evidence/chunk-1.md)" in workflow
    assert "type: Evidence Chunk" in evidence
    assert "source_ref: book.md" in evidence
