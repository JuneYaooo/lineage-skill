#!/usr/bin/env python3
"""Validate external learner state without reading private artifact bodies."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from runtime_state import LIFECYCLE_STAGES, MASTERY_STATES, read_json, read_jsonl


MICRO_LESSON_PHASES = {"teaching", "awaiting_answers", "feedback_batch", "awaiting_answer_1", "feedback_1", "ready_question_2", "awaiting_answer_2", "feedback_2", "complete"}


def validate(state_dir: Path) -> dict:
    errors = []
    required = ["apprenticeship_state.json", "mastery_state.json", "practice_episodes.jsonl", "error_library.json", "review_queue.json", "artifact_index.json", "personal_skill_candidates"]
    for name in required:
        if not (state_dir / name).exists():
            errors.append(f"missing {name}")
    state = read_json(state_dir / "apprenticeship_state.json", {})
    mastery = read_json(state_dir / "mastery_state.json", {})
    episodes = read_jsonl(state_dir / "practice_episodes.jsonl")
    if state.get("current_stage") not in LIFECYCLE_STAGES:
        errors.append("invalid current_stage")
    active = state.get("active_learning_unit")
    if isinstance(active, dict):
        if active.get("phase") not in MICRO_LESSON_PHASES:
            errors.append("invalid active_learning_unit phase")
        if active.get("pacing", "one-at-a-time") not in {"together", "one-at-a-time"}:
            errors.append("invalid active_learning_unit pacing")
        if len(active.get("question_ids") or []) != 2:
            errors.append("active_learning_unit must contain exactly two questions")
        if not set(active.get("answered_question_ids") or []).issubset(set(active.get("question_ids") or [])):
            errors.append("active_learning_unit contains an unknown answered question")
    if any(item.get("state") not in MASTERY_STATES for item in mastery.get("capabilities", [])):
        errors.append("invalid mastery state")
    ids = [item.get("episode_id") for item in episodes]
    if len(ids) != len(set(ids)):
        errors.append("duplicate episode_id in append-only log")
    if state.get("mentor_package_id") != mastery.get("mentor_package_id") or state.get("learner_id") != mastery.get("learner_id"):
        errors.append("mastery identity does not match apprenticeship state")
    return {"valid": not errors, "errors": errors, "episode_count": len(episodes), "capability_count": len(mastery.get("capabilities", [])), "privacy": "learner state is external to the generated Skill"}


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate an external learner state directory.")
    parser.add_argument("--state-dir", required=True)
    args = parser.parse_args()
    result = validate(Path(args.state_dir).expanduser().resolve())
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if not result["valid"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
