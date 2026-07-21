#!/usr/bin/env python3
"""Validate and append a PracticeEpisode without mutating prior events."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from runtime_state import append_jsonl, read_json


REQUIRED = ["schema_version", "episode_id", "mentor_package_id", "learner_id", "timestamp_start", "stage", "task_id", "capability_ids", "prediction", "attempts", "hints", "feedback", "outcome", "errors", "mastery_events", "next_actions", "provenance"]


def validate_episode(episode: dict) -> list[str]:
    errors = [f"missing required field: {field}" for field in REQUIRED if field not in episode]
    if episode.get("schema_version") != "1.0":
        errors.append("schema_version must be 1.0")
    if not episode.get("capability_ids"):
        errors.append("capability_ids must not be empty")
    if not episode.get("attempts"):
        errors.append("an observable attempt is required")
    if episode.get("outcome", {}).get("task_result") not in {"pass", "revise", "fail", "insufficient_evidence"}:
        errors.append("outcome.task_result is invalid")
    return errors


def main() -> None:
    parser = argparse.ArgumentParser(description="Append a PracticeEpisode to an external learner store.")
    parser.add_argument("--state-dir", required=True)
    parser.add_argument("--episode", required=True)
    args = parser.parse_args()
    state_dir = Path(args.state_dir).expanduser().resolve()
    episode = read_json(Path(args.episode).expanduser().resolve(), {})
    errors = validate_episode(episode)
    state = read_json(state_dir / "apprenticeship_state.json", {})
    if episode.get("mentor_package_id") != state.get("mentor_package_id") or episode.get("learner_id") != state.get("learner_id"):
        errors.append("episode learner/mentor identity does not match apprenticeship state")
    if errors:
        print(json.dumps({"valid": False, "errors": errors}, ensure_ascii=False, indent=2))
        raise SystemExit(1)
    append_jsonl(state_dir / "practice_episodes.jsonl", episode, unique_key="episode_id")
    print(json.dumps({"valid": True, "episode_id": episode["episode_id"], "log": str(state_dir / "practice_episodes.jsonl")}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
