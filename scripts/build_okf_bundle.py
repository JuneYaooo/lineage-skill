#!/usr/bin/env python3
"""Build an OKF-style Markdown bundle from a CoursePackage."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import shutil
from pathlib import Path
from typing import Any


FIELD_SPECS = {
    "concepts": ("Concept", "concepts", "Concepts", ["concept"]),
    "methods": ("Method", "methods", "Methods", ["method"]),
    "diagnostics": ("Diagnostic", "diagnostics", "Diagnostics", ["diagnostic"]),
    "workflows": ("Workflow", "workflows", "Workflows", ["workflow"]),
    "rubrics": ("Rubric", "rubrics", "Rubrics", ["rubric"]),
    "templates": ("Template", "templates", "Templates", ["template"]),
    "transfer_rules": ("Transfer Rule", "transfer-rules", "Transfer Rules", ["transfer"]),
    "failure_modes": ("Failure Mode", "failure-modes", "Failure Modes", ["failure-mode"]),
    "cases": ("Case", "cases", "Cases", ["case"]),
    "quotes": ("Quote", "quotes", "Quotes", ["quote"]),
    "boundaries": ("Boundary", "boundaries", "Boundaries", ["boundary"]),
    "study_paths": ("Study Path", "study-paths", "Study Paths", ["study-path"]),
}


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"not a JSON object: {path}")
    return data


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


def slugify(value: str, fallback: str = "concept") -> str:
    slug = re.sub(r"[^a-zA-Z0-9\u4e00-\u9fff_-]+", "-", value.strip()).strip("-")
    return slug.lower()[:80] or fallback


def yaml_scalar(value: Any) -> str:
    if value is None:
        return '""'
    text = str(value)
    if not text:
        return '""'
    if "\n" in text or "\r" in text:
        return json.dumps(text, ensure_ascii=False)
    if text[0] in "-?:,[]{}#&*!|>'\"%@`" or ": " in text:
        return json.dumps(text, ensure_ascii=False)
    return text


def yaml_list(values: list[str]) -> str:
    return "[" + ", ".join(json.dumps(value, ensure_ascii=False) for value in values) + "]"


def frontmatter(fields: dict[str, Any]) -> str:
    lines = ["---"]
    for key, value in fields.items():
        if isinstance(value, list):
            lines.append(f"{key}: {yaml_list([str(item) for item in value])}")
        else:
            lines.append(f"{key}: {yaml_scalar(value)}")
    lines.append("---")
    return "\n".join(lines)


def split_title_summary(item: Any, fallback_title: str) -> tuple[str, str, dict[str, Any]]:
    if isinstance(item, dict):
        title = str(item.get("title") or item.get("name") or item.get("id") or fallback_title).strip()
        summary = str(item.get("summary") or item.get("quote") or item.get("description") or "").strip()
        return title, summary, item
    text = str(item).strip()
    for sep in ["：", ":", " - ", "——", "。"]:
        if sep in text:
            title, summary = text.split(sep, 1)
            title = title.strip(" -*`#")
            summary = summary.strip()
            if title and summary:
                return title[:80], summary, {}
    return text[:80] or fallback_title, text, {}


def citation_link(meta: dict[str, Any]) -> str:
    chunk_id = meta.get("chunk_id")
    if chunk_id:
        return f"[Source chunk](../evidence/{chunk_id}.md)"
    source_ref = meta.get("source_ref") or meta.get("source") or meta.get("path")
    if source_ref:
        return str(source_ref)
    return ""


def write_concept(
    *,
    output_dir: Path,
    field: str,
    item: Any,
    index: int,
    course_name: str,
    generated_at: str,
) -> Path:
    concept_type, dirname, _, tags = FIELD_SPECS[field]
    title, summary, meta = split_title_summary(item, f"{concept_type} {index}")
    filename = f"{index:03d}-{slugify(title, fallback=field)}.md"
    target_dir = output_dir / dirname
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / filename
    resource_id = meta.get("card_id") or meta.get("id") or f"{field}:{index:03d}"
    source_ref = meta.get("source_ref") or meta.get("source") or meta.get("path")
    fields = {
        "type": concept_type,
        "title": title,
        "description": summary[:240] if summary else title,
        "resource": f"lineage://{slugify(course_name, 'course')}/{resource_id}",
        "tags": ["lineage", *tags],
        "timestamp": generated_at,
    }
    for key in ["card_id", "chunk_id", "chunk_index", "source_ref", "source_course", "source_course_id"]:
        if meta.get(key) is not None:
            fields[key] = meta[key]
    if source_ref and "source_ref" not in fields:
        fields["source_ref"] = source_ref

    citation = citation_link(meta)
    body = [
        frontmatter(fields),
        "",
        f"# {title}",
        "",
        summary or title,
        "",
        "# Use",
        "",
        f"Use this {concept_type.lower()} as a source-grounded capability element from `{course_name}`.",
        "",
    ]
    if citation:
        body.extend(["# Citations", "", f"[1] {citation}", ""])
    target.write_text("\n".join(body).rstrip() + "\n", encoding="utf-8")
    return target


def write_evidence_chunks(course_dir: Path, output_dir: Path, generated_at: str) -> int:
    chunks = read_jsonl(course_dir / "text_sources" / "chunks.jsonl")
    if not chunks:
        return 0
    target_dir = output_dir / "evidence"
    target_dir.mkdir(parents=True, exist_ok=True)
    for chunk in chunks:
        chunk_id = str(chunk.get("chunk_id") or "")
        if not chunk_id:
            continue
        source_ref = chunk.get("source_ref") or chunk.get("source_path") or ""
        fields = {
            "type": "Evidence Chunk",
            "title": f"{source_ref}#{chunk.get('chunk_index', 0)}",
            "description": f"Source chunk from {source_ref}",
            "resource": f"lineage://evidence/{chunk_id}",
            "tags": ["lineage", "evidence"],
            "timestamp": generated_at,
            "chunk_id": chunk_id,
            "source_ref": source_ref,
        }
        for key in ["source_id", "source_path", "chunk_index", "char_start", "char_end", "content_sha256"]:
            if chunk.get(key) is not None:
                fields[key] = chunk[key]
        body = [
            frontmatter(fields),
            "",
            f"# {fields['title']}",
            "",
            "```text",
            str(chunk.get("text") or "").strip(),
            "```",
            "",
        ]
        (target_dir / f"{chunk_id}.md").write_text("\n".join(body), encoding="utf-8")
    return len(chunks)


def write_dir_index(directory: Path, title: str, files: list[Path]) -> None:
    lines = [f"# {title}", ""]
    for path in files:
        text = path.read_text(encoding="utf-8", errors="ignore")
        title_match = re.search(r"^title:\s*(.+)$", text, flags=re.M)
        desc_match = re.search(r"^description:\s*(.+)$", text, flags=re.M)
        item_title = parse_frontmatter_value(title_match.group(1)) if title_match else path.stem
        desc = parse_frontmatter_value(desc_match.group(1)) if desc_match else ""
        lines.append(f"- [{item_title}]({path.name}) - {desc}")
    directory.joinpath("index.md").write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def parse_frontmatter_value(value: str) -> str:
    value = value.strip()
    if value.startswith(('"', "'")):
        try:
            return str(json.loads(value))
        except json.JSONDecodeError:
            return value.strip('"\'')
    return value


def write_root_index(output_dir: Path, course_name: str, sections: list[tuple[str, str, int]], evidence_count: int) -> None:
    lines = [
        f"# {course_name} — OKF Bundle",
        "",
        "This directory is an OKF-style Markdown knowledge bundle generated by lineage-skill.",
        "Use it for progressive reading, human review, cross-agent exchange, and concept graph navigation.",
        "",
    ]
    for dirname, title, count in sections:
        lines.extend([f"## {title}", "", f"- [{title}]({dirname}/) - {count} concept files", ""])
    if evidence_count:
        lines.extend(["## Evidence", "", f"- [Evidence](evidence/) - {evidence_count} source chunk files"])
    lines.extend(
        [
            "",
            "## Reading Order",
            "",
            "1. Start here.",
            "2. Open the relevant capability section index.",
            "3. Read individual concept files.",
            "4. Follow `# Citations` links to evidence chunks when exact source wording matters.",
            "",
        ]
    )
    output_dir.joinpath("index.md").write_text("\n".join(lines), encoding="utf-8")


def write_log(output_dir: Path, generated_at: str, concept_count: int, evidence_count: int) -> None:
    today = generated_at[:10]
    lines = [
        "# OKF Bundle Log",
        "",
        f"## {today}",
        f"- **Created**: Generated {concept_count} OKF concept files.",
        f"- **Created**: Generated {evidence_count} evidence chunk files.",
        "- **Updated**: Rebuilt progressive `index.md` files from `course_package.json`.",
        "",
    ]
    output_dir.joinpath("log.md").write_text("\n".join(lines), encoding="utf-8")


def build_okf_bundle(*, course_dir: str | Path, output_dir: str | Path, course_name: str | None = None) -> dict[str, Any]:
    source = Path(course_dir).expanduser().resolve()
    output = Path(output_dir).expanduser().resolve()
    package = load_json(source / "course_package.json")
    manifest = package.get("manifest") if isinstance(package.get("manifest"), dict) else {}
    resolved_name = course_name or manifest.get("course_name") or source.name
    generated_at = dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True, exist_ok=True)

    concept_count = 0
    sections: list[tuple[str, str, int]] = []
    for field, (_, dirname, title, _) in FIELD_SPECS.items():
        values = package.get(field) or []
        if not isinstance(values, list):
            values = [values]
        files = [
            write_concept(
                output_dir=output,
                field=field,
                item=item,
                index=idx,
                course_name=str(resolved_name),
                generated_at=generated_at,
            )
            for idx, item in enumerate(values, start=1)
            if item
        ]
        if files:
            write_dir_index(output / dirname, title, files)
            sections.append((dirname, title, len(files)))
            concept_count += len(files)

    evidence_count = write_evidence_chunks(source, output, generated_at)
    if evidence_count:
        evidence_files = sorted((output / "evidence").glob("*.md"))
        write_dir_index(output / "evidence", "Evidence", evidence_files)
    write_root_index(output, str(resolved_name), sections, evidence_count)
    write_log(output, generated_at, concept_count, evidence_count)
    return {
        "okf_dir": str(output),
        "concept_count": concept_count,
        "evidence_count": evidence_count,
        "section_count": len(sections),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build an OKF-style Markdown bundle from a CoursePackage.")
    parser.add_argument("--source-dir", required=True, help="Course workspace containing course_package.json.")
    parser.add_argument("--output-dir", required=True, help="Directory to write the OKF bundle.")
    parser.add_argument("--course-name", help="Human-readable course/book name.")
    args = parser.parse_args()
    result = build_okf_bundle(course_dir=args.source_dir, output_dir=args.output_dir, course_name=args.course_name)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
