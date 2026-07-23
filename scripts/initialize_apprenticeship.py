#!/usr/bin/env python3
"""Initialize a private external learner store for one MentorPackage."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from runtime_state import store_dir, utc_now, write_json


def initialize(mentor_package_path: Path, learner_store_root: Path, learner_id: str, *, capabilities: list[str], project: str) -> Path:
    mentor = json.loads(mentor_package_path.read_text(encoding="utf-8"))
    mentor_id = mentor["manifest"]["mentor_package_id"]
    root = store_dir(learner_store_root, mentor_id)
    root.mkdir(parents=True, exist_ok=True)
    timestamp = utc_now()
    state = {
        "schema_version": "1.0",
        "learner_id": learner_id,
        "mentor_package_id": mentor_id,
        "created_at": timestamp,
        "updated_at": timestamp,
        "learning_contract": {
            "desired_capabilities": capabilities,
            "real_project": project,
            "constraints": {"time": "", "tools": [], "risk": [], "access": []},
            "teaching_preferences": mentor["learning_contract_template"].get(
                "teaching_preferences",
                {"explanation_density": "normal", "visual_mode": "auto", "svg": "when-useful", "formative_question_count": 2, "question_pacing": "together"},
            ),
            "expected_artifacts": [],
            "graduation_target": mentor["learning_contract_template"]["graduation_target"],
        },
        "profile": {"prior_experience": "", "preferred_language": "", "accessibility_needs": None, "explanation_density": "normal", "visual_preference": "auto"},
        "current_stage": "orientation",
        "active_capabilities": capabilities,
        "active_learning_unit": None,
        "mastery_state_ref": "mastery_state.json",
        "review_queue_ref": "review_queue.json",
        "episode_log_ref": "practice_episodes.jsonl",
        "autonomy": {"default_hint_ceiling": "H2", "mentor_intervention_policy": "minimal-effective-hint", "recent_hint_trend": "unknown"},
        "status": "active",
    }
    write_json(root / "apprenticeship_state.json", state)
    write_json(root / "mastery_state.json", {"schema_version": "1.0", "mentor_package_id": mentor_id, "learner_id": learner_id, "rebuilt_at": timestamp, "capabilities": []})
    write_json(root / "error_library.json", {"schema_version": "1.0", "errors": []})
    write_json(root / "review_queue.json", {"schema_version": "1.0", "items": []})
    write_json(root / "artifact_index.json", {"schema_version": "1.0", "artifacts": []})
    (root / "practice_episodes.jsonl").touch(exist_ok=True)
    (root / "artifacts" / "diagrams").mkdir(parents=True, exist_ok=True)
    (root / "personal_skill_candidates").mkdir(exist_ok=True)
    return root


def main() -> None:
    parser = argparse.ArgumentParser(description="Initialize external apprenticeship state.")
    parser.add_argument("--mentor-package", default="../references/mentor_package.json")
    parser.add_argument("--learner-store-root", required=True)
    parser.add_argument("--learner-id", required=True)
    parser.add_argument("--capability", action="append", default=[])
    parser.add_argument("--project", default="")
    args = parser.parse_args()
    mentor = (Path(__file__).resolve().parent / args.mentor_package).resolve() if not Path(args.mentor_package).is_absolute() else Path(args.mentor_package)
    root = initialize(mentor, Path(args.learner_store_root), args.learner_id, capabilities=args.capability, project=args.project)
    print(json.dumps({"learner_state_dir": str(root)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
