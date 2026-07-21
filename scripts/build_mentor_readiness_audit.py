#!/usr/bin/env python3
"""Audit whether a workspace can truthfully support full apprenticeship."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from schema_utils import load_json, write_json


PLACEHOLDER_PATTERNS = [
    re.compile(pattern, re.I)
    for pattern in [r"\bTODO\b", r"add .+ here", r"placeholder", r"implement here", r"rest of code", r"similar to above"]
]


def placeholder_hits(paths: list[Path]) -> list[str]:
    hits: list[str] = []
    for path in paths:
        if not path.exists() or not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if not text.strip() or any(pattern.search(text) for pattern in PLACEHOLDER_PATTERNS):
            hits.append(str(path))
    return hits


def build_readiness_audit(source_dir: Path) -> dict[str, Any]:
    required = {
        "course_package": source_dir / "course_package.json",
        "teacher_model": source_dir / "teacher_model.json",
        "capability_graph": source_dir / "capability_graph.json",
        "practice_bank": source_dir / "practice_bank.json",
        "assessment_bank": source_dir / "assessment_bank.json",
        "mentor_protocol": source_dir / "mentor_protocol.md",
        "graduation_policy": source_dir / "graduation_policy.json",
    }
    missing_files = [name for name, path in required.items() if not path.exists()]
    data = {
        name: load_json(path)
        for name, path in required.items()
        if path.exists() and path.suffix == ".json" and name not in {"graduation_policy"}
    }
    teacher_quality = (data.get("teacher_model") or {}).get("quality", {})
    graph_quality = (data.get("capability_graph") or {}).get("quality", {})
    practice_quality = (data.get("practice_bank") or {}).get("quality", {})
    assessment_quality = (data.get("assessment_bank") or {}).get("quality", {})
    graph_nodes = (data.get("capability_graph") or {}).get("nodes", [])
    practice_tasks = (data.get("practice_bank") or {}).get("tasks", [])
    rubrics = (data.get("practice_bank") or {}).get("rubrics", [])
    assessments = (data.get("assessment_bank") or {}).get("items", [])
    blockers: list[str] = []
    blockers.extend(f"missing artifact: {name}" for name in missing_files)
    if teacher_quality.get("status") != "ready":
        blockers.append("TeacherModel lacks complete source-grounded cues, decisions, demonstrations, feedback, or graduation signals")
    if graph_quality.get("status") != "ready" or graph_quality.get("cycle_count") or graph_quality.get("dangling_reference_count"):
        blockers.append("CapabilityGraph is incomplete, cyclic, or contains dangling references")
    if graph_nodes and any(not node.get("practice_tasks") for node in graph_nodes):
        blockers.append("one or more capability nodes have no practice task")
    if graph_nodes and any(not node.get("assessment_items") for node in graph_nodes):
        blockers.append("one or more capability nodes have no assessment")
    if practice_quality.get("status") != "ready" or not practice_tasks or not rubrics:
        blockers.append("PracticeBank lacks complete tasks, rubrics, or hint ladders")
    if assessment_quality.get("status") != "ready" or not assessments:
        blockers.append("AssessmentBank does not cover the graduation matrix")
    placeholder_files = placeholder_hits([source_dir / "mentor_protocol.md", source_dir / "graduation_policy.json"])
    if placeholder_files:
        blockers.append("mentor protocol or graduation policy contains placeholder content")
    package_integrity = ((data.get("course_package") or {}).get("quality") or {}).get("integrity", {})
    if package_integrity.get("dangling_reference_count", 0):
        blockers.append("CoursePackage contains dangling references")

    status = "ready" if not blockers else "partial" if data.get("teacher_model") and graph_nodes else "blocked"
    inferred_records = max(0, int(teacher_quality.get("record_count", 0)) - int(teacher_quality.get("source_grounded_record_count", 0)))
    audit = {
        "schema_version": "1.0",
        "status": status,
        "source_readiness": {
            "status": "ready" if data.get("course_package") and (data["course_package"].get("sources") or data["course_package"].get("evidence")) else "partial",
            "evidence_count": len((data.get("course_package") or {}).get("evidence", [])),
            "unsupported_claim_count": package_integrity.get("unsupported_claim_count", 0),
        },
        "teacher_model": {
            "status": teacher_quality.get("status", "missing"),
            "source_grounded_records": teacher_quality.get("source_grounded_record_count", 0),
            "inferred_records": inferred_records,
            "grounded_ratio": teacher_quality.get("grounded_ratio", 0),
            "missing_teacher_evidence": teacher_quality.get("missing_teacher_evidence", []),
        },
        "capability_graph": {
            "nodes": len(graph_nodes),
            "edges": len((data.get("capability_graph") or {}).get("edges", [])),
            "cycles": graph_quality.get("cycle_count", 0),
            "dangling_references": graph_quality.get("dangling_reference_count", 0),
        },
        "practice": {"tasks": len(practice_tasks), "rubrics": len(rubrics), "capability_coverage": practice_quality.get("capability_coverage", 0)},
        "assessment": {"items": len(assessments), "types": assessment_quality.get("types", []), "missing_types": assessment_quality.get("missing_types", [])},
        "integrity": {
            "placeholder_files": placeholder_files,
            "dangling_references": package_integrity.get("dangling_reference_count", 0) + graph_quality.get("dangling_reference_count", 0),
            "source_conflicts": package_integrity.get("source_conflict_count", 0),
        },
        "blockers": list(dict.fromkeys(blockers)),
        "human_review_required": sorted(set(teacher_quality.get("human_review_required", [])) | set(((data.get("course_package") or {}).get("quality") or {}).get("mentor_readiness", {}).get("human_review_required", []))),
        "apprenticeship_mode_allowed": "full" if status == "ready" else "guided" if status == "partial" else "none",
    }
    return audit


def audit_markdown(audit: dict[str, Any]) -> str:
    lines = [
        "# Mentor Readiness Audit",
        "",
        f"- Status: **{audit['status']}**",
        f"- Allowed apprenticeship mode: **{audit['apprenticeship_mode_allowed']}**",
        f"- Source evidence: {audit['source_readiness']['evidence_count']}",
        f"- Teacher grounded ratio: {audit['teacher_model']['grounded_ratio']}",
        f"- Capability nodes: {audit['capability_graph']['nodes']}",
        f"- Practice tasks / rubrics: {audit['practice']['tasks']} / {audit['practice']['rubrics']}",
        f"- Assessments: {audit['assessment']['items']}",
        "",
        "## Blockers",
        "",
    ]
    lines.extend(f"- {item}" for item in audit["blockers"] or ["None."])
    lines.extend(["", "## Human review", ""])
    lines.extend(f"- `{item}`" for item in audit["human_review_required"] or ["No required items."])
    lines.extend(["", "Full apprenticeship is only emitted when this audit is ready. Guided mode must report the listed evidence gaps.", ""])
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build mentor readiness audit.")
    parser.add_argument("--source-dir", required=True)
    parser.add_argument("--output-json")
    parser.add_argument("--output-markdown")
    parser.add_argument(
        "--mode",
        choices=["auto", "strict"],
        default="auto",
        help="In strict mode, exit non-zero unless full apprenticeship is ready.",
    )
    args = parser.parse_args()
    source_dir = Path(args.source_dir).expanduser().resolve()
    audit = build_readiness_audit(source_dir)
    json_path = Path(args.output_json).expanduser().resolve() if args.output_json else source_dir / "mentor_readiness_audit.json"
    md_path = Path(args.output_markdown).expanduser().resolve() if args.output_markdown else source_dir / "mentor_readiness_audit.md"
    write_json(json_path, audit)
    md_path.write_text(audit_markdown(audit), encoding="utf-8")
    print(json.dumps({"json": str(json_path), "markdown": str(md_path), "status": audit["status"], "allowed": audit["apprenticeship_mode_allowed"]}, ensure_ascii=False, indent=2))
    if args.mode == "strict" and audit["status"] != "ready":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
