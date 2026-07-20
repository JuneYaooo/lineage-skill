#!/usr/bin/env python3
"""Build the stable MentorPackage runtime contract and protocol artifacts."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import shutil
from pathlib import Path
from typing import Any

from build_mentor_readiness_audit import audit_markdown, build_readiness_audit
from schema_utils import load_json, write_json
from stable_ids import content_hash, stable_id


ROOT = Path(__file__).resolve().parents[1]


def graduation_policy(assessment_bank: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "policy_id": stable_id("assessment", assessment_bank.get("course_package_id"), "graduation-policy"),
        "required_assessment_types": assessment_bank.get("graduation_matrix", {}).get("required_assessment_types", []),
        "requirements": assessment_bank.get("graduation_matrix", {}).get("requirements", []),
        "evidence_requirements": {
            "independent_execution": True,
            "novel_context_transfer": True,
            "delayed_retention": True,
            "boundary_recognition": True,
            "real_world_artifact": True,
            "personal_skill_regression": True,
            "learner_approval": True,
        },
        "anti_shortcuts": [
            "Lesson completion, streaks, self-reported understanding, and one successful attempt are insufficient.",
            "Practice scores do not replace blind assessment results.",
            "Graduation from a course method is not professional licensure or certification.",
        ],
        "post_graduation_role": ["source consultant", "counterexample provider", "advanced sparring partner", "source update notifier"],
    }


def build_mentor_package(source_dir: Path, *, requested_mode: str = "full", evidence_strategy: str = "standard") -> dict[str, Any]:
    package = load_json(source_dir / "course_package.json")
    teacher = load_json(source_dir / "teacher_model.json")
    assessment = load_json(source_dir / "assessment_bank.json")
    protocol_source = ROOT / "references" / "apprenticeship-protocol.md"
    shutil.copy2(protocol_source, source_dir / "mentor_protocol.md")
    policy = graduation_policy(assessment)
    write_json(source_dir / "graduation_policy.json", policy)
    audit = build_readiness_audit(source_dir)
    write_json(source_dir / "mentor_readiness_audit.json", audit)
    (source_dir / "mentor_readiness_audit.md").write_text(audit_markdown(audit), encoding="utf-8")
    allowed = audit["apprenticeship_mode_allowed"]
    actual_mode = requested_mode if requested_mode == "none" else ("full" if requested_mode == "full" and allowed == "full" else "guided" if allowed in {"full", "guided"} else "none")
    mentor_id = stable_id("mentor_package", package["manifest"]["package_id"], teacher["teacher_id"], actual_mode, evidence_strategy)
    payload = {
        "schema_version": "1.0",
        "manifest": {
            "mentor_package_id": mentor_id,
            "course_package_id": package["manifest"]["package_id"],
            "teacher_model_id": teacher["teacher_id"],
            "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
            "generator_version": "lineage-skill-1.0",
            "evidence_strategy": evidence_strategy,
            "apprenticeship_mode": actual_mode,
            "requested_apprenticeship_mode": requested_mode,
            "downgraded": requested_mode != actual_mode,
            "package_hashes": {
                name: content_hash(load_json(source_dir / name))
                for name in ["course_package.json", "teacher_model.json", "capability_graph.json", "practice_bank.json", "assessment_bank.json"]
            },
        },
        "learning_contract_template": {
            "desired_capabilities": [],
            "real_project": "",
            "constraints": {"time": "", "tools": [], "risk": [], "access": []},
            "expected_artifacts": [],
            "graduation_target": policy["evidence_requirements"],
            "baseline_diagnostic_required": True,
        },
        "capability_graph_ref": "capability_graph.json",
        "teacher_model_ref": "teacher_model.json",
        "practice_bank_ref": "practice_bank.json",
        "assessment_bank_ref": "assessment_bank.json",
        "mentor_protocol_ref": "mentor_protocol.md",
        "graduation_policy_ref": "graduation_policy.json",
        "learner_state_schema_ref": "schemas/apprenticeship_state.schema.json",
        "episode_schema_ref": "schemas/practice_episode.schema.json",
        "personal_skill_schema_ref": "schemas/personal_skill_candidate.schema.json",
        "quality": {
            "mentor_readiness": audit["status"],
            "runtime_readiness": "ready" if actual_mode != "none" else "blocked",
            "blockers": audit["blockers"],
            "human_review_required": audit["human_review_required"],
        },
    }
    write_json(source_dir / "mentor_package.json", payload)
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description="Build MentorPackage 1.0.")
    parser.add_argument("--source-dir", required=True)
    parser.add_argument("--apprenticeship", choices=["none", "guided", "full"], default="full")
    parser.add_argument("--evidence", choices=["standard", "strict"], default="standard")
    parser.add_argument("--output")
    args = parser.parse_args()
    source_dir = Path(args.source_dir).expanduser().resolve()
    payload = build_mentor_package(source_dir, requested_mode=args.apprenticeship, evidence_strategy=args.evidence)
    if args.output:
        write_json(Path(args.output).expanduser().resolve(), payload)
    print(json.dumps({"output": str(source_dir / "mentor_package.json"), "manifest": payload["manifest"], "quality": payload["quality"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
