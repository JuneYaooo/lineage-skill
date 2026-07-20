#!/usr/bin/env python3
"""Migrate legacy CoursePackage 0.x payloads to the Lineage 1.0 contract."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import shutil
from pathlib import Path
from typing import Any

from schema_utils import issues_payload, load_json, validate_schema, write_json
from stable_ids import content_hash, ensure_stable_id, stable_id


ASSET_FIELDS = [
    "concepts",
    "topics",
    "cases",
    "methods",
    "diagnostics",
    "workflows",
    "rubrics",
    "templates",
    "transfer_rules",
    "failure_modes",
    "boundaries",
    "quotes",
    "study_paths",
]
PROVENANCE = {
    "direct_source",
    "source_grounded_synthesis",
    "cross_source_synthesis",
    "mentor_inference",
    "learner_hypothesis",
    "learner_observation",
    "real_world_evidence",
    "external_general_knowledge",
    "unsupported",
}


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def source_course_id(manifest: dict[str, Any]) -> str:
    return str(manifest.get("course_id") or stable_id("course", manifest.get("course_name") or manifest.get("source_dir") or "course"))


def normalize_evidence(raw: Any, *, course_id: str) -> list[dict[str, Any]]:
    rows = raw if isinstance(raw, list) else []
    result: list[dict[str, Any]] = []
    for index, item in enumerate(rows):
        row = dict(item) if isinstance(item, dict) else {"path": str(item)}
        path = str(row.get("path") or row.get("source") or "")
        kind = str(row.get("evidence_kind") or row.get("type") or "note")
        source_id = str(row.get("source_id") or stable_id("source", course_id, path or kind))
        result.append(
            {
                "id": str(row.get("id") or row.get("evidence_id") or stable_id("card", course_id, path, index, kind)),
                "source_id": source_id,
                "lesson_id": row.get("lesson_id"),
                "chunk_id": row.get("chunk_id"),
                "card_id": row.get("card_id"),
                "path": path,
                "timestamp_start": row.get("timestamp_start"),
                "timestamp_end": row.get("timestamp_end"),
                "page": row.get("page"),
                "quote_summary": str(row.get("quote_summary") or row.get("summary") or ""),
                "confidence": row.get("confidence") if row.get("confidence") in {"high", "medium", "low"} else "medium",
                "evidence_kind": kind,
                "type": str(row.get("type") or kind),
                "granularity": row.get("granularity", "file"),
                **({"source_course": row["source_course"]} if row.get("source_course") else {}),
                **({"source_course_id": row["source_course_id"]} if row.get("source_course_id") else {}),
            }
        )
    return result


def normalize_sources(evidence: list[dict[str, Any]], manifest: dict[str, Any]) -> list[dict[str, Any]]:
    sources: dict[str, dict[str, Any]] = {}
    for pointer in evidence:
        source_id = pointer["source_id"]
        sources.setdefault(
            source_id,
            {
                "id": source_id,
                "path": pointer.get("path", ""),
                "kind": pointer.get("evidence_kind", "note"),
                "course_id": manifest["course_id"],
                "content_hash": content_hash([pointer.get("path"), pointer.get("evidence_kind")]),
            },
        )
    return sorted(sources.values(), key=lambda item: item["id"])


def normalize_lessons(raw: Any, *, course_id: str) -> list[dict[str, Any]]:
    rows = raw if isinstance(raw, list) else []
    result: list[dict[str, Any]] = []
    for index, item in enumerate(rows):
        row = dict(item) if isinstance(item, dict) else {"title": str(item)}
        title = str(row.get("title") or row.get("name") or row.get("lesson_name") or f"Lesson {index + 1}")
        result.append(
            {
                "id": ensure_stable_id(row.get("id"), "lesson", course_id, title, row.get("source") or index),
                "title": title,
                "summary": str(row.get("summary") or row.get("abstract") or ""),
                "topics": list(row.get("topics") or row.get("keywords") or []),
                "source": str(row.get("source") or row.get("file") or ""),
                "duration_minutes": row.get("duration_minutes"),
                "source_course_id": str(row.get("source_course_id") or course_id),
            }
        )
    return result


def infer_evidence_ids(row: dict[str, Any], evidence: list[dict[str, Any]]) -> list[str]:
    explicit = row.get("evidence") or row.get("source_evidence")
    if isinstance(explicit, list):
        return [str(item.get("id") if isinstance(item, dict) else item) for item in explicit if item]
    source = str(row.get("source_ref") or row.get("source") or row.get("path") or "")
    chunk_id = row.get("chunk_id")
    matched = [
        pointer["id"]
        for pointer in evidence
        if (source and pointer.get("path") == source) or (chunk_id and pointer.get("chunk_id") == chunk_id)
    ]
    return matched


def normalize_asset(item: Any, *, field: str, course_id: str, index: int, evidence: list[dict[str, Any]]) -> dict[str, Any]:
    row = dict(item) if isinstance(item, dict) else {"legacy_text": str(item)}
    legacy = str(row.get("legacy_text") or row.get("value") or "").strip()
    title = str(row.get("title") or row.get("name") or "").strip()
    summary = str(row.get("summary") or row.get("description") or row.get("quote") or legacy).strip()
    if not title:
        title = summary.split("：", 1)[0].split(":", 1)[0].strip()[:80] or f"{field}-{index + 1}"
    provenance = str(row.get("provenance") or "source_grounded_synthesis")
    if provenance not in PROVENANCE:
        provenance = "source_grounded_synthesis"
    evidence_ids = infer_evidence_ids(row, evidence)
    return {
        "id": ensure_stable_id(row.get("id") or row.get("card_id"), field.rstrip("s"), course_id, field, title, summary),
        "title": title,
        "summary": summary,
        "details": row.get("details") or {},
        "conditions": list(row.get("conditions") or []),
        "inputs": list(row.get("inputs") or []),
        "outputs": list(row.get("outputs") or []),
        "steps": list(row.get("steps") or []),
        "evidence": evidence_ids,
        "provenance": provenance,
        "confidence": row.get("confidence") if row.get("confidence") in {"high", "medium", "low"} else ("medium" if evidence_ids else "low"),
        "source_courses": list(row.get("source_courses") or [row.get("source_course_id") or course_id]),
        "related_capabilities": list(row.get("related_capabilities") or []),
        "failure_modes": list(row.get("failure_modes") or []),
        "human_review": row.get("human_review") or ("recommended" if not evidence_ids else "none"),
        **({"legacy_text": legacy} if legacy else {}),
        **({"value": legacy} if legacy else {}),
        **({"source_course": row["source_course"]} if row.get("source_course") else {}),
        **({"source_course_id": row["source_course_id"]} if row.get("source_course_id") else {}),
    }


def normalize_learning_check(item: Any, *, course_id: str, index: int, evidence: list[dict[str, Any]]) -> dict[str, Any]:
    row = dict(item) if isinstance(item, dict) else {"prompt": str(item)}
    prompt = str(row.get("prompt") or row.get("summary") or row.get("task") or row.get("legacy_text") or "")
    source_evidence = infer_evidence_ids(row, evidence)
    return {
        "id": ensure_stable_id(row.get("id") or row.get("card_id"), "task", course_id, prompt, index),
        "capability_ids": list(row.get("capability_ids") or []),
        "prompt": prompt,
        "task_type": row.get("task_type") or "explain",
        "difficulty": int(row.get("difficulty") or 2),
        "expected_output_type": row.get("expected_output_type") or "text",
        "rubric_ids": list(row.get("rubric_ids") or []),
        "evidence_answer": row.get("evidence_answer") or {"provenance": "source_grounded_synthesis", "evidence": source_evidence},
        "common_errors": list(row.get("common_errors") or []),
        "hint_ladder": list(row.get("hint_ladder") or []),
        "transfer_variant_ids": list(row.get("transfer_variant_ids") or []),
        "source_evidence": source_evidence,
        "human_review": row.get("human_review") or "recommended",
    }


def make_claims(package: dict[str, Any]) -> list[dict[str, Any]]:
    claims: list[dict[str, Any]] = []
    for field in ASSET_FIELDS:
        for item in package.get(field, []):
            if not isinstance(item, dict) or not item.get("summary"):
                continue
            claims.append(
                {
                    "id": stable_id("claim", package["manifest"]["course_id"], item["id"], item["summary"]),
                    "text": item["summary"],
                    "provenance": item["provenance"],
                    "evidence": item["evidence"],
                    "source_courses": item["source_courses"],
                    "confidence": item["confidence"],
                    "conditions": item["conditions"],
                    "counterevidence": [],
                    "conflicts": [],
                    "human_review": item["human_review"],
                }
            )
    return claims


def quality_v1(package: dict[str, Any], legacy_quality: Any) -> dict[str, Any]:
    source_count = len(package["sources"])
    lesson_count = len(package["lessons"])
    capability_count = sum(len(package[field]) for field in ["methods", "diagnostics", "workflows", "rubrics", "transfer_rules"])
    unsupported = sum(claim["provenance"] == "unsupported" for claim in package["claims"])
    duplicate_count = 0
    missing = []
    for field in ["methods", "diagnostics", "workflows", "rubrics", "learning_checks"]:
        if not package.get(field):
            missing.append(field)
    return {
        "coverage": {
            "source_coverage": 1.0 if source_count else 0.0,
            "lesson_coverage": 1.0 if lesson_count else 0.0,
            "modality_coverage": len({item["evidence_kind"] for item in package["evidence"]}),
            "capability_coverage": capability_count,
            "teacher_model_coverage": 0,
            "practice_coverage": len(package["learning_checks"]),
            "assessment_coverage": 0,
        },
        "integrity": {
            "dangling_reference_count": 0,
            "unsupported_claim_count": unsupported,
            "source_conflict_count": len(package.get("conflicts", [])),
            "placeholder_count": 0,
            "duplicate_id_count": duplicate_count,
        },
        "mentor_readiness": {
            "status": "partial",
            "missing_requirements": missing + ["teacher_model", "capability_graph", "practice_bank", "assessment_bank"],
            "human_review_required": [item["id"] for field in ASSET_FIELDS for item in package.get(field, []) if item.get("human_review") == "required"],
        },
        "legacy": legacy_quality if isinstance(legacy_quality, dict) else {},
    }


def migrate_package(package: dict[str, Any], *, source_path: str | Path | None = None) -> tuple[dict[str, Any], dict[str, Any]]:
    original_version = str(package.get("schema_version") or "0.1")
    manifest_in = package.get("manifest") if isinstance(package.get("manifest"), dict) else {}
    course_id = source_course_id(manifest_in)
    course_name = str(manifest_in.get("course_name") or Path(str(manifest_in.get("source_dir") or "course")).name)
    manifest = {
        **manifest_in,
        "course_id": course_id,
        "course_name": course_name,
        "package_id": str(manifest_in.get("package_id") or stable_id("course", course_id, "package-1.0")),
        "migrated_from": original_version if original_version != "1.0" else manifest_in.get("migrated_from"),
        "migration_time": now() if original_version != "1.0" else manifest_in.get("migration_time"),
        "migrator_version": "1.0",
    }
    evidence = normalize_evidence(package.get("evidence"), course_id=course_id)
    result: dict[str, Any] = {
        "schema_version": "1.0",
        "manifest": manifest,
        "sources": normalize_sources(evidence, manifest),
        "lessons": normalize_lessons(package.get("lessons"), course_id=course_id),
        "claims": [],
        "concepts": [],
        "topics": [],
        "cases": [],
        "methods": [],
        "diagnostics": [],
        "workflows": [],
        "rubrics": [],
        "templates": [],
        "transfer_rules": [],
        "failure_modes": [],
        "boundaries": [],
        "quotes": [],
        "learning_checks": [],
        "study_paths": [],
        "teacher_model_ref": "teacher_model.json",
        "capability_graph_ref": "capability_graph.json",
        "practice_bank_ref": "practice_bank.json",
        "assessment_bank_ref": "assessment_bank.json",
        "evidence": evidence,
        "quality": {},
    }
    for field in ASSET_FIELDS:
        raw_items = package.get(field) if isinstance(package.get(field), list) else []
        result[field] = [normalize_asset(item, field=field, course_id=course_id, index=index, evidence=evidence) for index, item in enumerate(raw_items)]
    raw_checks = package.get("learning_checks") if isinstance(package.get("learning_checks"), list) else []
    result["learning_checks"] = [normalize_learning_check(item, course_id=course_id, index=index, evidence=evidence) for index, item in enumerate(raw_checks)]
    result["claims"] = make_claims(result)
    result["quality"] = quality_v1(result, package.get("quality"))
    id_map: dict[str, str] = {}
    for field in ["evidence", "lessons", *ASSET_FIELDS, "learning_checks"]:
        old_rows = package.get(field) if isinstance(package.get(field), list) else []
        new_rows = result.get(field, [])
        for old, new in zip(old_rows, new_rows):
            if not isinstance(old, dict) or not isinstance(new, dict):
                continue
            old_id = old.get("id") or old.get("evidence_id") or old.get("card_id")
            new_id = new.get("id")
            if old_id and new_id:
                id_map[str(old_id)] = str(new_id)
    for key in ["course_id", "package_id"]:
        if manifest_in.get(key):
            id_map[str(manifest_in[key])] = str(manifest[key])
    report = {
        "schema_version": "1.0",
        "source_path": str(source_path or ""),
        "source_schema_version": original_version,
        "target_schema_version": "1.0",
        "migrated_at": manifest.get("migration_time"),
        "counts": {field: len(result.get(field, [])) for field in ["sources", "lessons", "claims", *ASSET_FIELDS, "learning_checks", "evidence"]},
        "legacy_text_count": sum("legacy_text" in item for field in ASSET_FIELDS for item in result[field]),
        "human_review_count": sum(item.get("human_review") != "none" for field in ASSET_FIELDS for item in result[field]),
        "id_map": id_map,
        "unmapped_legacy_id_count": 0,
    }
    return result, report


def schema_path() -> Path:
    return Path(__file__).resolve().parents[1] / "references" / "schemas" / "course_package.schema.json"


def main() -> None:
    parser = argparse.ArgumentParser(description="Migrate CoursePackage 0.x to Lineage CoursePackage 1.0.")
    parser.add_argument("input", help="Legacy course_package.json")
    parser.add_argument("--output", help="Output path; defaults to <input>.v1.json")
    parser.add_argument("--report", help="Migration report path")
    parser.add_argument("--in-place", action="store_true", help="Replace input after writing a .bak copy")
    args = parser.parse_args()

    source = Path(args.input).expanduser().resolve()
    if not source.exists():
        raise SystemExit(f"course package not found: {source}")
    package, report = migrate_package(load_json(source), source_path=source)
    issues = validate_schema(package, load_json(schema_path()))
    report["validation"] = issues_payload(issues)
    if issues:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        raise SystemExit("migration output failed schema validation")
    if args.in_place:
        backup = source.with_suffix(source.suffix + ".bak")
        shutil.copy2(source, backup)
        output = source
        report["backup_path"] = str(backup)
    else:
        output = Path(args.output).expanduser().resolve() if args.output else source.with_name(f"{source.stem}.v1.json")
    report_path = Path(args.report).expanduser().resolve() if args.report else output.with_name("course_package_migration_report.json")
    write_json(output, package)
    write_json(report_path, report)
    print(json.dumps({"output": str(output), "report": str(report_path), **report["validation"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
