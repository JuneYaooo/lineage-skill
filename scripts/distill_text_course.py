#!/usr/bin/env python3
"""Distill pure text sources into structured evidence cards."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
from pathlib import Path
from typing import Any

from text_sources import stable_id, write_jsonl, write_text_source_artifacts


CARD_PREFIXES = {
    "concept": ["概念", "关键概念", "术语", "定义", "concept", "term"],
    "method": ["方法", "步骤", "流程", "框架", "原则", "method", "framework", "process"],
    "case": ["案例", "例子", "示例", "故事", "case", "example"],
    "boundary": ["边界", "限制", "风险", "注意", "误区", "boundary", "risk", "limit"],
    "quote": ["金句", "原话", "引用", "quote"],
    "task": ["任务", "练习", "作业", "行动", "清单", "task", "exercise", "action"],
    "open_question": ["问题", "疑问", "待确认", "question"],
    "diagnostic": ["诊断", "判断", "辨别", "定位", "diagnostic", "diagnosis"],
    "workflow": ["工作流", "执行流程", "操作流程", "作业流程", "workflow"],
    "rubric": ["标准", "评分", "质检", "评价", "rubric", "criteria"],
    "template": ["模板", "话术", "表格", "worksheet", "template"],
    "transfer": ["迁移", "应用", "套用", "转化", "transfer", "application"],
    "failure_mode": ["失效", "误用", "反例", "失败", "failure", "anti-pattern"],
}

SECTION_TITLES = {
    "concept": "关键概念",
    "method": "方法流程",
    "case": "案例线索",
    "boundary": "边界与风险",
    "quote": "核心引用",
    "task": "练习与行动",
    "open_question": "待确认问题",
    "diagnostic": "诊断判断",
    "workflow": "执行流程",
    "rubric": "质量标准",
    "template": "模板资产",
    "transfer": "迁移规则",
    "failure_mode": "失效与误用",
}


def llm_enabled() -> bool:
    return os.getenv("DISTILL_USE_LLM", "1").strip().lower() not in {"0", "false", "no"}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def clean_value(value: str) -> str:
    value = re.sub(r"^[：:：\-\s]+", "", value.strip())
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def split_title_summary(value: str) -> tuple[str, str]:
    value = clean_value(value)
    if not value:
        return "", ""
    for sep in ["：", ":", "——", " - ", "，", "。"]:
        if sep in value:
            title, rest = value.split(sep, 1)
            title = title.strip(" -*`#")
            rest = rest.strip()
            if title and rest:
                return title[:80], rest
    return value[:40], value


def detect_card_type(line: str) -> tuple[str | None, str]:
    stripped = line.strip().lstrip("-*0123456789.、)） ")
    for card_type, prefixes in CARD_PREFIXES.items():
        for prefix in prefixes:
            pattern = rf"^{re.escape(prefix)}\s*[：:]?\s*(.*)$"
            match = re.match(pattern, stripped, flags=re.I)
            if match:
                return card_type, match.group(1) or stripped
    return None, stripped


def make_card(chunk: dict[str, Any], card_type: str, value: str) -> dict[str, Any] | None:
    title, summary = split_title_summary(value)
    if not title and not summary:
        return None
    payload = {
        "card_id": stable_id(chunk["chunk_id"], card_type, value),
        "card_type": card_type,
        "title": title or SECTION_TITLES.get(card_type, card_type),
        "summary": summary,
        "source_id": chunk["source_id"],
        "source_path": chunk["source_path"],
        "source_ref": chunk["source_ref"],
        "chunk_id": chunk["chunk_id"],
        "chunk_index": chunk["chunk_index"],
        "char_start": chunk["char_start"],
        "char_end": chunk["char_end"],
        "content_sha256": chunk["content_sha256"],
        "confidence": "medium",
        "extraction": "local",
    }
    if card_type == "quote":
        payload["quote"] = summary or title
    return payload


def build_local_cards(chunk: dict[str, Any]) -> list[dict[str, Any]]:
    cards: list[dict[str, Any]] = []
    for raw_line in chunk.get("text", "").splitlines():
        line = raw_line.strip()
        if not line or len(line) < 4:
            continue
        card_type, value = detect_card_type(line)
        if not card_type:
            continue
        card = make_card(chunk, card_type, value)
        if card:
            cards.append(card)
    return cards


def build_llm_cards(chunk: dict[str, Any]) -> list[dict[str, Any]]:
    if not llm_enabled() or not os.getenv("LINEAGE_TEXT_API_KEY"):
        return []
    from llm_client import call_text_llm

    prompt = f"""请从以下课程文字片段中抽取证据卡片。只返回 JSON，不要 Markdown。

每张卡片字段：
- card_type: concept/method/case/boundary/quote/task/open_question/diagnostic/workflow/rubric/template/transfer/failure_mode
- title
- summary
- quote: 仅 quote 类型需要
- confidence: high/medium/low

要求：
- 只抽取片段明确支持的内容，不要扩展。
- 方法、诊断、流程、质量标准、模板、迁移规则、案例、边界、原话要优先保留。
- 最多 12 张。

来源：{chunk['source_ref']} chunk {chunk['chunk_index']}

片段：
{chunk['text']}
"""
    text = call_text_llm([{"role": "user", "content": prompt}])
    match = re.search(r"\{[\s\S]*\}|\[[\s\S]*\]", text)
    if not match:
        return []
    data = json.loads(match.group(0))
    items = data.get("cards", data) if isinstance(data, dict) else data
    if not isinstance(items, list):
        return []
    cards = []
    for item in items:
        if not isinstance(item, dict):
            continue
        card_type = item.get("card_type")
        if card_type not in CARD_PREFIXES:
            continue
        value = item.get("summary") or item.get("quote") or item.get("title") or ""
        card = make_card(chunk, card_type, value)
        if not card:
            continue
        card.update({key: item[key] for key in ["title", "summary", "quote", "confidence"] if key in item})
        card["extraction"] = "llm"
        cards.append(card)
    return cards


def dedupe_cards(cards: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[tuple[str, str, str]] = set()
    out = []
    for card in cards:
        key = (card.get("card_type", ""), card.get("title", ""), card.get("summary") or card.get("quote", ""))
        if key in seen:
            continue
        seen.add(key)
        out.append(card)
    return out


def source_summaries(chunks: list[dict[str, Any]], cards: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_source: dict[str, dict[str, Any]] = {}
    for chunk in chunks:
        row = by_source.setdefault(
            chunk["source_id"],
            {
                "source_id": chunk["source_id"],
                "source_path": chunk["source_path"],
                "source_ref": chunk["source_ref"],
                "chunk_count": 0,
                "card_count": 0,
                "card_types": {},
            },
        )
        row["chunk_count"] += 1
    for card in cards:
        row = by_source.setdefault(
            card["source_id"],
            {
                "source_id": card["source_id"],
                "source_path": card["source_path"],
                "source_ref": card["source_ref"],
                "chunk_count": 0,
                "card_count": 0,
                "card_types": {},
            },
        )
        row["card_count"] += 1
        row["card_types"][card["card_type"]] = row["card_types"].get(card["card_type"], 0) + 1
    return list(by_source.values())


def format_card(card: dict[str, Any]) -> str:
    content = card.get("quote") if card.get("card_type") == "quote" else card.get("summary", "")
    if card.get("title") and content and card["title"] not in content:
        content = f"{card['title']}：{content}"
    return f"- {content or card.get('title', '')}（{card.get('source_ref', '')}#{card.get('chunk_index', 0)}）"


def write_synthesis(course_name: str, cards: list[dict[str, Any]], output: Path) -> None:
    by_type: dict[str, list[dict[str, Any]]] = {}
    for card in cards:
        by_type.setdefault(card["card_type"], []).append(card)
    lines = [
        f"# {course_name} — Text Course Synthesis",
        "",
        "This synthesis is generated from pure-text sources and OCR/notes artifacts.",
        "",
    ]
    for card_type in [
        "concept",
        "method",
        "diagnostic",
        "workflow",
        "rubric",
        "template",
        "transfer",
        "failure_mode",
        "case",
        "boundary",
        "quote",
        "task",
        "open_question",
    ]:
        rows = by_type.get(card_type, [])
        if not rows:
            continue
        lines.append(f"## {SECTION_TITLES[card_type]}")
        lines.append("")
        lines.extend(format_card(card) for card in rows[:80])
        lines.append("")
    output.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def quality_report(
    *,
    sources: int,
    chunks: list[dict[str, Any]],
    cards: list[dict[str, Any]],
    llm_used: bool,
    llm_failures: int,
) -> dict[str, Any]:
    counts: dict[str, int] = {}
    for card in cards:
        counts[card["card_type"]] = counts.get(card["card_type"], 0) + 1
    return {
        "schema_version": "0.1",
        "generated_at": dt.datetime.now().isoformat(timespec="seconds"),
        "source_count": sources,
        "chunk_count": len(chunks),
        "card_count": len(cards),
        "card_counts": dict(sorted(counts.items())),
        "empty_chunk_count": sum(1 for chunk in chunks if not chunk.get("text", "").strip()),
        "llm_used": llm_used,
        "llm_failures": llm_failures,
        "status": "usable" if cards else "thin",
    }


def document_inputs(course_dir: Path) -> list[Path]:
    documents = course_dir / "documents"
    if not documents.exists():
        return []
    return sorted(path for path in documents.rglob("*") if path.suffix.lower() in {".md", ".txt", ".text", ".markdown"})


def distill_text_course(
    *,
    course_name: str,
    course_dir: str | Path,
    input_paths: list[str | Path] | None = None,
    include_existing_documents: bool = True,
    use_llm: bool | None = None,
    max_chars: int = 6000,
    overlap_chars: int = 500,
) -> dict[str, Any]:
    course_path = Path(course_dir).expanduser().resolve()
    inputs = [Path(path) for path in (input_paths or [])]
    if include_existing_documents:
        inputs.extend(document_inputs(course_path))
    if not inputs:
        raise SystemExit("no text inputs found")

    source_result = write_text_source_artifacts(
        input_paths=inputs,
        course_dir=course_path,
        base_dir=course_path.parent,
        max_chars=max_chars,
        overlap_chars=overlap_chars,
    )
    chunks = read_jsonl(course_path / "text_sources" / "chunks.jsonl")
    cards: list[dict[str, Any]] = []
    llm_requested = bool(use_llm) if use_llm is not None else llm_enabled()
    llm_failures = 0
    for chunk in chunks:
        chunk_cards: list[dict[str, Any]] = []
        if llm_requested and os.getenv("LINEAGE_TEXT_API_KEY"):
            try:
                chunk_cards = build_llm_cards(chunk)
            except Exception:
                llm_failures += 1
                chunk_cards = []
        if not chunk_cards:
            chunk_cards = build_local_cards(chunk)
        cards.extend(chunk_cards)
    cards = dedupe_cards(cards)

    out = course_path / "text_distillation"
    out.mkdir(parents=True, exist_ok=True)
    write_jsonl(out / "evidence_cards.jsonl", cards)
    summaries = source_summaries(chunks, cards)
    (out / "source_summaries.json").write_text(json.dumps(summaries, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_synthesis(course_name, cards, out / "text_course_synthesis.md")
    quality = quality_report(
        sources=source_result["source_count"],
        chunks=chunks,
        cards=cards,
        llm_used=llm_requested and bool(os.getenv("LINEAGE_TEXT_API_KEY")) and llm_failures == 0,
        llm_failures=llm_failures,
    )
    (out / "text_distillation_quality.json").write_text(json.dumps(quality, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {
        **source_result,
        "card_count": len(cards),
        "cards_path": str(out / "evidence_cards.jsonl"),
        "quality_path": str(out / "text_distillation_quality.json"),
        "synthesis_path": str(out / "text_course_synthesis.md"),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Distill pure text course materials into evidence cards.")
    parser.add_argument("--course-name", required=True)
    parser.add_argument("--base-dir", default=".", help="Course workspace root.")
    parser.add_argument("--input", action="append", help="Text file or directory. Repeatable.")
    parser.add_argument("--include-existing-documents", action="store_true", help="Include <course-dir>/documents text/OCR files.")
    parser.add_argument("--no-llm", action="store_true", help="Use deterministic local extraction only.")
    parser.add_argument("--max-chars", type=int, default=6000)
    parser.add_argument("--overlap-chars", type=int, default=500)
    args = parser.parse_args()

    base_dir = Path(args.base_dir).expanduser().resolve()
    result = distill_text_course(
        course_name=args.course_name,
        course_dir=base_dir / args.course_name,
        input_paths=args.input or [],
        include_existing_documents=args.include_existing_documents,
        use_llm=not args.no_llm,
        max_chars=args.max_chars,
        overlap_chars=args.overlap_chars,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
