from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")


def test_fetch_course_evidence_returns_source_chunk_by_chunk_id(tmp_path: Path) -> None:
    refs = tmp_path / "references"
    write_jsonl(
        refs / "text_sources" / "chunks.jsonl",
        [
            {
                "chunk_id": "chunk-1",
                "source_id": "source-1",
                "source_path": "book.md",
                "source_ref": "book.md",
                "chunk_index": 0,
                "char_start": 10,
                "char_end": 44,
                "text": "先判断问题卡在目标、资源还是反馈，然后再行动。",
            }
        ],
    )
    write_jsonl(
        refs / "text_distillation" / "evidence_cards.jsonl",
        [
            {
                "card_id": "card-1",
                "card_type": "diagnostic",
                "title": "定位卡点",
                "summary": "先判断问题卡在目标、资源还是反馈。",
                "source_ref": "book.md",
                "chunk_id": "chunk-1",
                "chunk_index": 0,
            }
        ],
    )

    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "fetch_course_evidence.py"),
            "--references-dir",
            str(refs),
            "--chunk-id",
            "chunk-1",
        ],
        check=True,
        cwd=ROOT,
        text=True,
        capture_output=True,
    )

    payload = json.loads(result.stdout)
    assert payload["chunk"]["source_path"] == "book.md"
    assert payload["chunk"]["char_start"] == 10
    assert "目标、资源还是反馈" in payload["chunk"]["text"]
    assert payload["cards"][0]["card_type"] == "diagnostic"
