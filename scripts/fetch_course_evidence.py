#!/usr/bin/env python3
"""Resolve a complete provenance chain for Lineage source and runtime IDs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def read_json(path: Path, default: Any = None) -> Any:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8", errors="ignore").splitlines() if line.strip()]


def compact_chunk(chunk: dict[str, Any], context_chars: int) -> dict[str, Any]:
    row = dict(chunk)
    text = str(row.get("text") or "")
    if context_chars > 0 and len(text) > context_chars:
        row["text"] = text[:context_chars].rstrip() + "..."
    return row


def find_by_id(rows: list[Any], value: str) -> dict[str, Any] | None:
    return next((row for row in rows if isinstance(row, dict) and (row.get("id") == value or row.get("card_id") == value or row.get("chunk_id") == value)), None)


def object_index(refs: Path) -> dict[str, tuple[str, dict[str, Any]]]:
    sources = {
        "course_package.json": ["claims", "concepts", "topics", "cases", "methods", "diagnostics", "workflows", "rubrics", "templates", "transfer_rules", "failure_modes", "boundaries", "quotes", "learning_checks", "study_paths", "evidence"],
        "teacher_model.json": [],
        "capability_graph.json": ["nodes", "edges"],
        "practice_bank.json": ["tasks", "rubrics", "error_patterns"],
        "assessment_bank.json": ["items"],
    }
    index: dict[str, tuple[str, dict[str, Any]]] = {}
    for filename, fields in sources.items():
        data = read_json(refs / filename, {}) or {}
        if filename == "teacher_model.json":
            fields_with_rows = {
                "attention_cues": data.get("epistemic_model", {}).get("attention_cues", []),
                "problem_frames": data.get("epistemic_model", {}).get("problem_frames", []),
                "decision_rules": data.get("epistemic_model", {}).get("decision_rules", []),
                "demonstrations": data.get("practice_model", {}).get("demonstrations", []),
                "feedback_patterns": data.get("practice_model", {}).get("feedback_patterns", []),
            }
        else:
            fields_with_rows = {field: data.get(field, []) for field in fields}
        for field, rows in fields_with_rows.items():
            for row in rows if isinstance(rows, list) else []:
                if isinstance(row, dict) and row.get("id"):
                    index[str(row["id"])] = (f"{filename}:{field}", row)
    return index


def evidence_ids(row: dict[str, Any]) -> list[str]:
    values: list[str] = []
    for field in ["evidence", "source_evidence"]:
        for item in row.get(field, []) if isinstance(row.get(field), list) else []:
            value = item.get("id") if isinstance(item, dict) else item
            if value and str(value) not in values:
                values.append(str(value))
    answer = row.get("evidence_answer") if isinstance(row.get("evidence_answer"), dict) else {}
    for item in answer.get("evidence", []) if isinstance(answer.get("evidence"), list) else []:
        if str(item) not in values:
            values.append(str(item))
    return values


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch Lineage evidence by source or runtime ID.")
    parser.add_argument("--references-dir", default="../references")
    parser.add_argument("--chunk-id")
    parser.add_argument("--card-id")
    parser.add_argument("--claim-id")
    parser.add_argument("--capability-id")
    parser.add_argument("--rule-id")
    parser.add_argument("--task-id")
    parser.add_argument("--rubric-id")
    parser.add_argument("--assessment-id")
    parser.add_argument("--context-chars", type=int, default=4000)
    args = parser.parse_args()
    refs = Path(args.references_dir).expanduser().resolve()
    requested = next((value for value in [args.claim_id, args.capability_id, args.rule_id, args.task_id, args.rubric_id, args.assessment_id] if value), None)
    if not requested and not args.chunk_id and not args.card_id:
        raise SystemExit("provide a chunk, card, claim, capability, rule, task, rubric, or assessment ID")

    chunks = read_jsonl(refs / "text_sources" / "chunks.jsonl")
    cards = read_jsonl(refs / "text_distillation" / "evidence_cards.jsonl")
    package = read_json(refs / "course_package.json", {}) or {}
    pointers = package.get("evidence", []) if isinstance(package.get("evidence"), list) else []
    selected: dict[str, Any] | None = None
    location = ""
    ids: list[str] = []
    if requested:
        location, selected = object_index(refs).get(requested, ("", None))
        if not selected:
            raise SystemExit(f"object not found: {requested}")
        ids = evidence_ids(selected)
    matched_cards: list[dict[str, Any]] = []
    chunk_id = args.chunk_id
    if args.card_id:
        card = next((row for row in cards if row.get("card_id") == args.card_id), None)
        if not card:
            raise SystemExit(f"card not found: {args.card_id}")
        matched_cards = [card]
        chunk_id = str(card.get("chunk_id") or "")
        ids.append(args.card_id)
    matched_pointers = [row for row in pointers if row.get("id") in ids or row.get("card_id") in ids or row.get("chunk_id") in ids]
    if chunk_id:
        matched_cards = [row for row in cards if row.get("chunk_id") == chunk_id]
    elif matched_pointers:
        chunk_ids = {row.get("chunk_id") for row in matched_pointers if row.get("chunk_id")}
        card_ids = {row.get("card_id") for row in matched_pointers if row.get("card_id")}
        matched_cards = [row for row in cards if row.get("chunk_id") in chunk_ids or row.get("card_id") in card_ids]
        chunk_id = next(iter(chunk_ids), None)
    chunk = next((row for row in chunks if row.get("chunk_id") == chunk_id), None)
    conflicts = [row for row in package.get("manifest", {}).get("conflicts", []) if requested and requested in row.get("item_ids", [])]
    payload = {
        "requested_id": requested or args.card_id or args.chunk_id,
        "object_location": location or None,
        "object": selected,
        "provenance": selected.get("provenance") if selected else (matched_cards[0].get("provenance") if matched_cards else None),
        "evidence_pointers": matched_pointers,
        "chunk": compact_chunk(chunk, args.context_chars) if chunk else None,
        "cards": matched_cards,
        "source_conflicts": conflicts,
        "chain_complete": bool(matched_pointers or chunk or matched_cards),
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
