#!/usr/bin/env python3
"""Shared external learner-state primitives copied into generated Mentor Skills."""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
from typing import Any, Iterable


MASTERY_STATES = [
    "unseen",
    "recognized",
    "reconstructed",
    "applied_with_support",
    "applied_independently",
    "transferred",
    "retained",
    "graduated",
]
LIFECYCLE_STAGES = ["orientation", "modeling", "imitation", "coached_practice", "independent_practice", "transfer", "graduation", "alumni"]
HINT_LEVELS = ["H0", "H1", "H2", "H3", "H4"]


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def read_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def append_jsonl(path: Path, payload: dict[str, Any], *, unique_key: str | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if unique_key and any(item.get(unique_key) == payload.get(unique_key) for item in read_jsonl(path)):
        raise ValueError(f"duplicate {unique_key}: {payload.get(unique_key)}")
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")


def store_dir(root: Path, mentor_package_id: str) -> Path:
    return root.expanduser().resolve() / "apprenticeships" / mentor_package_id


def highest_hint(episode: dict[str, Any]) -> str:
    values = [item.get("level") for item in episode.get("hints", []) if item.get("level") in HINT_LEVELS]
    return max(values, key=HINT_LEVELS.index) if values else "H0"


def target_state(episode: dict[str, Any]) -> str | None:
    if episode.get("outcome", {}).get("task_result") != "pass":
        return None
    stage = episode.get("stage")
    hint = highest_hint(episode)
    if stage == "graduation" and hint == "H0":
        return "graduated"
    if episode.get("outcome", {}).get("retention_check") and hint == "H0":
        return "retained"
    if stage == "transfer" and hint == "H0":
        return "transferred"
    if stage == "independent_practice" and hint in {"H0", "H1"}:
        return "applied_independently"
    if stage in {"imitation", "coached_practice", "independent_practice"}:
        return "applied_with_support"
    if stage == "modeling":
        return "reconstructed"
    return "recognized"


def advance_one(current: str, target: str) -> str:
    current_index = MASTERY_STATES.index(current) if current in MASTERY_STATES else 0
    target_index = MASTERY_STATES.index(target)
    return MASTERY_STATES[min(target_index, current_index + 1)]


def episode_context_key(episode: dict[str, Any]) -> str:
    context = episode.get("context", {})
    return str(context.get("project") or context.get("environment") or context.get("transfer_dimension") or "unspecified")


def critical_failed(episode: dict[str, Any]) -> bool:
    for row in episode.get("feedback", {}).get("rubric_results", []):
        if row.get("critical") and (row.get("passed") is False or int(row.get("score", 0)) < 2):
            return True
    return False


def rebuild_mastery(episodes: Iterable[dict[str, Any]], *, mentor_package_id: str, learner_id: str) -> dict[str, Any]:
    states: dict[str, dict[str, Any]] = {}
    for episode in sorted(episodes, key=lambda item: (item.get("timestamp_start", ""), item.get("episode_id", ""))):
        for capability_id in episode.get("capability_ids", []):
            state = states.setdefault(
                capability_id,
                {
                    "capability_id": capability_id,
                    "state": "unseen",
                    "evidence_for": [],
                    "evidence_against": [],
                    "last_success_at": None,
                    "last_failure_at": None,
                    "highest_independent_stage": None,
                    "lowest_hint_level_success": None,
                    "transfer_contexts": [],
                    "retention_checks": [],
                    "confidence_calibration": {"high_confidence_errors": 0, "low_confidence_successes": 0},
                    "review_due_at": None,
                },
            )
            passed = episode.get("outcome", {}).get("task_result") == "pass" and not critical_failed(episode)
            confidence = episode.get("prediction", {}).get("confidence_before")
            if passed:
                state["evidence_for"].append(episode["episode_id"])
                state["last_success_at"] = episode.get("timestamp_end") or episode.get("timestamp_start")
                target = target_state(episode)
                if target:
                    state["state"] = advance_one(state["state"], target)
                hint = highest_hint(episode)
                if state["lowest_hint_level_success"] is None or HINT_LEVELS.index(hint) < HINT_LEVELS.index(state["lowest_hint_level_success"]):
                    state["lowest_hint_level_success"] = hint
                if episode.get("stage") in {"independent_practice", "transfer", "graduation"}:
                    state["highest_independent_stage"] = episode.get("stage")
                if episode.get("stage") == "transfer":
                    key = episode_context_key(episode)
                    if key not in state["transfer_contexts"]:
                        state["transfer_contexts"].append(key)
                if episode.get("outcome", {}).get("retention_check"):
                    state["retention_checks"].append(episode["episode_id"])
                if confidence is not None and float(confidence) < 40:
                    state["confidence_calibration"]["low_confidence_successes"] += 1
            else:
                state["evidence_against"].append(episode["episode_id"])
                state["last_failure_at"] = episode.get("timestamp_end") or episode.get("timestamp_start")
                if confidence is not None and float(confidence) >= 80:
                    state["confidence_calibration"]["high_confidence_errors"] += 1
                if state["state"] in {"transferred", "retained", "graduated"}:
                    state["state"] = MASTERY_STATES[max(0, MASTERY_STATES.index(state["state"]) - 1)]
            for action in episode.get("next_actions", []):
                if isinstance(action, dict) and action.get("review_due_at"):
                    state["review_due_at"] = action["review_due_at"]
    return {
        "schema_version": "1.0",
        "mentor_package_id": mentor_package_id,
        "learner_id": learner_id,
        "rebuilt_at": utc_now(),
        "capabilities": sorted(states.values(), key=lambda item: item["capability_id"]),
    }
