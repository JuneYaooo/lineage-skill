#!/usr/bin/env python3
"""Compile source-grounded teaching and judgment patterns into TeacherModel 1.0."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from migrate_course_package import migrate_package
from schema_utils import load_json, write_json
from stable_ids import stable_id


def load_course_package(path: Path) -> dict[str, Any]:
    package = load_json(path)
    if package.get("schema_version") != "1.0":
        package, _ = migrate_package(package, source_path=path)
    return package


def asset_text(item: dict[str, Any]) -> str:
    return str(item.get("summary") or item.get("title") or "").strip()


def evidence_confidence(item: dict[str, Any]) -> str:
    confidence = item.get("confidence") if item.get("confidence") in {"high", "medium", "low"} else "low"
    if item.get("provenance") not in {"direct_source", "source_grounded_synthesis"} and confidence == "high":
        return "medium"
    return confidence


def teacher_record(kind: str, item: dict[str, Any], course_id: str, **values: Any) -> dict[str, Any]:
    text = asset_text(item)
    return {
        "id": stable_id(kind, course_id, item.get("id"), text),
        **values,
        "provenance": item.get("provenance", "source_grounded_synthesis"),
        "confidence": evidence_confidence(item),
        "evidence": list(item.get("evidence") or []),
        "human_review": item.get("human_review", "recommended"),
    }


def build_teacher_model(package: dict[str, Any]) -> dict[str, Any]:
    manifest = package["manifest"]
    course_id = manifest["course_id"]
    source_courses = manifest.get("source_courses") or [{"id": course_id, "name": manifest.get("course_name", "Course")}]
    course_ids = [str(item.get("id") or item.get("source_course_id") or course_id) for item in source_courses if isinstance(item, dict)]
    if not course_ids:
        course_ids = [course_id]

    diagnostics = package.get("diagnostics", [])
    methods = package.get("methods", [])
    workflows = package.get("workflows", [])
    rubrics = package.get("rubrics", [])
    cases = package.get("cases", [])
    failures = package.get("failure_modes", [])
    boundaries = package.get("boundaries", [])
    transfer = package.get("transfer_rules", [])

    attention_cues = [
        teacher_record(
            "rule",
            item,
            course_id,
            signal=asset_text(item),
            context=(item.get("conditions") or ["When diagnosing a relevant course problem"])[0],
            interpretation=asset_text(item),
            confounds=list(item.get("failure_modes") or []),
            next_question=f"What observable evidence supports or contradicts: {item.get('title', asset_text(item))}?",
            capability_ids=list(item.get("related_capabilities") or []),
        )
        for item in diagnostics
    ]
    problem_frames = [
        teacher_record(
            "rule",
            item,
            course_id,
            name=item.get("title") or "Problem frame",
            frame=asset_text(item),
            conditions=list(item.get("conditions") or []),
        )
        for item in diagnostics + methods[:3]
    ]
    diagnostic_questions = [
        teacher_record(
            "rule",
            item,
            course_id,
            question=f"Which observable condition in “{item.get('title', asset_text(item))}” is present, absent, or uncertain?",
            purpose=asset_text(item),
        )
        for item in diagnostics
    ]
    decision_rules = [
        teacher_record(
            "rule",
            item,
            course_id,
            name=item.get("title") or "Decision rule",
            when=list(item.get("conditions") or ["When the method's stated inputs and applicability conditions are met"]),
            then=asset_text(item),
            because=asset_text(item),
            unless=list(item.get("failure_modes") or []),
            alternatives=[],
            observable_signals=[],
            rubric_ids=[],
            failure_mode_ids=list(item.get("failure_modes") or []),
        )
        for item in methods + workflows
    ]
    tradeoff_rules = [
        teacher_record(
            "rule",
            item,
            course_id,
            name=item.get("title") or "Transfer trade-off",
            rule=asset_text(item),
            preserve=list(item.get("conditions") or []),
            change=list(item.get("inputs") or []),
        )
        for item in transfer
    ]
    uncertainty_rules = [
        teacher_record(
            "rule",
            item,
            course_id,
            name=item.get("title") or "Boundary rule",
            uncertainty=asset_text(item),
            action="Stop, request missing evidence, or label the conclusion as inference.",
        )
        for item in boundaries
    ]
    demonstrations = [
        teacher_record(
            "demonstration",
            item,
            course_id,
            title=item.get("title") or "Course demonstration",
            context=(item.get("conditions") or ["Course case"])[0],
            goal=(item.get("outputs") or [asset_text(item)])[0],
            observations=list(item.get("inputs") or []),
            problem_frame=asset_text(item),
            options_considered=[],
            decision=asset_text(item),
            reasoning_steps=list(item.get("steps") or []),
            execution_steps=list(item.get("steps") or []),
            self_check=[],
            boundary_notes=list(item.get("failure_modes") or []),
        )
        for item in cases
    ]
    feedback_patterns = [
        teacher_record(
            "rule",
            item,
            course_id,
            error_signature=asset_text(item),
            diagnosis=f"The learner output violates or cannot demonstrate: {item.get('title', asset_text(item))}.",
            first_response="Name the single observable gap and ask for one targeted revision.",
            hint_ladder=[
                {"level": "H0", "action": "Restate the constraint without revealing the answer."},
                {"level": "H1", "action": "Point to the observation dimension."},
                {"level": "H2", "action": "Point to the relevant decision question."},
                {"level": "H3", "action": "Provide a partial structure."},
                {"level": "H4", "action": "Show a source-grounded demonstration and require a redo."},
            ],
            revision_request="Revise the artifact and explain which observable behavior changed.",
            escalation="Return to the prerequisite capability after repeated recurrence.",
        )
        for item in failures + rubrics
    ]
    graduation_signals = [
        teacher_record(
            "rule",
            item,
            course_id,
            signal=f"The learner independently satisfies the observable criteria for {item.get('title', 'the rubric')} in a novel context.",
            criteria=asset_text(item),
        )
        for item in rubrics
    ]
    missing = []
    for name, rows in {
        "attention_cues": attention_cues,
        "decision_rules": decision_rules,
        "demonstrations": demonstrations,
        "feedback_patterns": feedback_patterns,
        "graduation_signals": graduation_signals,
    }.items():
        if not rows:
            missing.append(name)
    evidence_ids = sorted({evidence_id for rows in [attention_cues, decision_rules, demonstrations, feedback_patterns, graduation_signals] for row in rows for evidence_id in row.get("evidence", [])})
    grounded = sum(bool(row.get("evidence")) for rows in [attention_cues, decision_rules, demonstrations, feedback_patterns] for row in rows)
    total = sum(len(rows) for rows in [attention_cues, decision_rules, demonstrations, feedback_patterns])
    grounded_ratio = grounded / total if total else 0.0
    status = "ready" if not missing and grounded_ratio >= 0.5 else "partial" if total else "blocked"
    return {
        "schema_version": "1.0",
        "teacher_id": stable_id("teacher", *course_ids, manifest.get("course_name")),
        "course_ids": course_ids,
        "identity": {
            "name": manifest.get("teacher_name") or manifest.get("author_name") or "Packaged source teacher/author",
            "domain": manifest.get("domain") or manifest.get("course_name") or "Packaged course domain",
            "claimed_scope": manifest.get("scope") or "Only the methods supported by the packaged sources",
            "source_boundary": "This model reconstructs source-supported attention, judgment, demonstration, feedback, and boundaries; it does not clone personality or consciousness.",
        },
        "epistemic_model": {
            "attention_cues": attention_cues,
            "problem_frames": problem_frames,
            "diagnostic_questions": diagnostic_questions,
            "decision_rules": decision_rules,
            "tradeoff_rules": tradeoff_rules,
            "uncertainty_rules": uncertainty_rules,
        },
        "practice_model": {
            "demonstrations": demonstrations,
            "coaching_patterns": feedback_patterns,
            "feedback_patterns": feedback_patterns,
            "progression_rules": [],
            "correction_sequences": feedback_patterns,
            "graduation_signals": graduation_signals,
        },
        "boundaries": {
            "applicability_conditions": [asset_text(item) for item in boundaries if asset_text(item)],
            "non_copyable_context": [asset_text(item) for item in boundaries if "经验" in asset_text(item) or "背景" in asset_text(item)],
            "contraindications": [asset_text(item) for item in failures if asset_text(item)],
            "controversies": [],
            "source_conflicts": list(manifest.get("conflicts") or []),
        },
        "evidence_index": evidence_ids,
        "quality": {
            "status": status,
            "missing_teacher_evidence": missing,
            "source_grounded_record_count": grounded,
            "record_count": total,
            "grounded_ratio": round(grounded_ratio, 3),
            "high_confidence_inference_count": 0,
            "human_review_required": sorted({row["id"] for rows in [attention_cues, decision_rules, demonstrations, feedback_patterns] for row in rows if row.get("human_review") == "required"}),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build TeacherModel 1.0 from CoursePackage 1.0.")
    parser.add_argument("--course-package", help="CoursePackage path")
    parser.add_argument("--source-dir", help="Course workspace containing course_package.json")
    parser.add_argument("--output", help="Output teacher_model.json")
    parser.add_argument("--strict", action="store_true", help="Exit non-zero unless TeacherModel quality is ready.")
    args = parser.parse_args()
    source_dir = Path(args.source_dir).expanduser().resolve() if args.source_dir else None
    package_path = Path(args.course_package).expanduser().resolve() if args.course_package else (source_dir / "course_package.json" if source_dir else None)
    if not package_path or not package_path.exists():
        raise SystemExit("provide --course-package or --source-dir with course_package.json")
    output = Path(args.output).expanduser().resolve() if args.output else package_path.parent / "teacher_model.json"
    model = build_teacher_model(load_course_package(package_path))
    write_json(output, model)
    print(json.dumps({"output": str(output), "quality": model["quality"]}, ensure_ascii=False, indent=2))
    if args.strict and model["quality"]["status"] != "ready":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
