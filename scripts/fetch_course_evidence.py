#!/usr/bin/env python3
"""Fetch source-grounded evidence from packaged course references."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        if not line.strip():
            continue
        item = json.loads(line)
        if isinstance(item, dict):
            rows.append(item)
    return rows


def compact_chunk(chunk: dict[str, Any], *, context_chars: int) -> dict[str, Any]:
    text = str(chunk.get("text") or "")
    if context_chars > 0 and len(text) > context_chars:
        text = text[:context_chars].rstrip() + "..."
    return {
        "chunk_id": chunk.get("chunk_id"),
        "source_id": chunk.get("source_id"),
        "source_path": chunk.get("source_path"),
        "source_ref": chunk.get("source_ref"),
        "chunk_index": chunk.get("chunk_index"),
        "char_start": chunk.get("char_start"),
        "char_end": chunk.get("char_end"),
        "content_sha256": chunk.get("content_sha256"),
        "text": text,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch a source chunk and related evidence cards.")
    parser.add_argument("--references-dir", default="../references", help="Generated Skill references directory.")
    parser.add_argument("--chunk-id", help="Text source chunk id to fetch.")
    parser.add_argument("--card-id", help="Evidence card id to fetch.")
    parser.add_argument("--context-chars", type=int, default=4000, help="Maximum source text chars to print.")
    args = parser.parse_args()

    references_dir = Path(args.references_dir).expanduser().resolve()
    cards = read_jsonl(references_dir / "text_distillation" / "evidence_cards.jsonl")
    chunks = read_jsonl(references_dir / "text_sources" / "chunks.jsonl")

    if not args.chunk_id and not args.card_id:
        raise SystemExit("provide --chunk-id or --card-id")

    matched_cards = cards
    chunk_id = args.chunk_id
    if args.card_id:
        matched_cards = [card for card in cards if card.get("card_id") == args.card_id]
        if not matched_cards:
            raise SystemExit(f"card not found: {args.card_id}")
        chunk_id = str(matched_cards[0].get("chunk_id") or chunk_id or "")

    if chunk_id:
        matched_cards = [card for card in matched_cards if card.get("chunk_id") == chunk_id or not args.chunk_id]

    chunk = next((row for row in chunks if row.get("chunk_id") == chunk_id), None)
    if not chunk:
        raise SystemExit(f"chunk not found: {chunk_id}")

    payload = {
        "chunk": compact_chunk(chunk, context_chars=args.context_chars),
        "cards": matched_cards,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
