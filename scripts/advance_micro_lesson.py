#!/usr/bin/env python3
"""Persist together-by-default or one-at-a-time micro-lesson pacing."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from runtime_state import read_json, utc_now, write_json


PHASES = [
    "teaching",
    "awaiting_answers",
    "feedback_batch",
    "awaiting_answer_1",
    "feedback_1",
    "ready_question_2",
    "awaiting_answer_2",
    "feedback_2",
    "complete",
]


def state_path(state_dir: Path) -> Path:
    return state_dir.expanduser().resolve() / "apprenticeship_state.json"


def load_state(state_dir: Path) -> tuple[Path, dict[str, Any]]:
    path = state_path(state_dir)
    if not path.exists():
        raise ValueError(f"missing apprenticeship state: {path}")
    return path, read_json(path, {})


def start(
    state: dict[str, Any],
    *,
    unit_id: str,
    capability_id: str,
    question_ids: list[str],
    pacing: str = "together",
) -> None:
    if len(question_ids) != 2 or len(set(question_ids)) != 2:
        raise ValueError("a micro-lesson requires exactly two distinct question IDs")
    if pacing not in {"together", "one-at-a-time"}:
        raise ValueError(f"unsupported question pacing: {pacing}")
    active = state.get("active_learning_unit")
    if isinstance(active, dict) and active.get("phase") not in {"complete"}:
        raise ValueError(f"cannot replace active micro-lesson in phase {active.get('phase')}")
    state["active_learning_unit"] = {
        "unit_id": unit_id,
        "capability_id": capability_id,
        "phase": "teaching",
        "pacing": pacing,
        "question_ids": question_ids,
        "current_question_index": 0,
        "answered_question_ids": [],
        "last_answered_question_ids": [],
        "diagram_refs": [],
        "started_at": utc_now(),
        "updated_at": utc_now(),
    }


def active_unit(state: dict[str, Any]) -> dict[str, Any]:
    active = state.get("active_learning_unit")
    if not isinstance(active, dict):
        raise ValueError("no active micro-lesson; start one first")
    if active.get("phase") not in PHASES:
        raise ValueError(f"invalid micro-lesson phase: {active.get('phase')}")
    if len(active.get("question_ids") or []) != 2:
        raise ValueError("active micro-lesson must contain exactly two questions")
    return active


def normalize_indexes(question_index: int | list[int] | None) -> list[int]:
    values = question_index if isinstance(question_index, list) else [] if question_index is None else [question_index]
    if any(value not in {1, 2} for value in values) or len(values) != len(set(values)):
        raise ValueError(f"question indexes must be distinct values from 1 and 2: {values}")
    return values


def transition(
    state: dict[str, Any],
    *,
    event: str,
    question_index: int | list[int] | None,
    diagram_ref: str | None,
) -> None:
    active = active_unit(state)
    phase = active["phase"]
    indexes = normalize_indexes(question_index)
    pacing = active.get("pacing") or "one-at-a-time"
    if pacing == "together":
        if event == "present":
            if phase != "teaching" or indexes:
                raise ValueError(f"cannot present the two-question set from phase {phase}")
            active["current_question_index"] = 0
            active["phase"] = "awaiting_answers"
        elif event == "answer":
            if phase != "awaiting_answers" or not indexes:
                raise ValueError(f"cannot record answers {indexes} from phase {phase}")
            question_ids = [active["question_ids"][index - 1] for index in indexes]
            new_ids = [question_id for question_id in question_ids if question_id not in active["answered_question_ids"]]
            if not new_ids:
                raise ValueError("all supplied question answers were already recorded")
            active["answered_question_ids"].extend(new_ids)
            active["last_answered_question_ids"] = new_ids
            active["phase"] = "feedback_batch"
        elif event == "finish-feedback":
            if phase != "feedback_batch" or indexes:
                raise ValueError(f"cannot finish batch feedback from phase {phase}")
            active["last_answered_question_ids"] = []
            if len(active["answered_question_ids"]) == 2:
                active["phase"] = "complete"
                active["completed_at"] = utc_now()
            else:
                active["phase"] = "awaiting_answers"
        else:
            raise ValueError(f"unsupported event: {event}")
    else:
        index = indexes[0] if len(indexes) == 1 else None
        if event == "present":
            expected = 1 if phase == "teaching" else 2 if phase == "ready_question_2" else None
            if index != expected:
                raise ValueError(f"cannot present question {index} from phase {phase}")
            active["current_question_index"] = index
            active["phase"] = f"awaiting_answer_{index}"
        elif event == "answer":
            if index not in {1, 2} or phase != f"awaiting_answer_{index}":
                raise ValueError(f"cannot record answer {index} from phase {phase}")
            question_id = active["question_ids"][index - 1]
            if question_id not in active["answered_question_ids"]:
                active["answered_question_ids"].append(question_id)
            active["last_answered_question_ids"] = [question_id]
            active["phase"] = f"feedback_{index}"
        elif event == "finish-feedback":
            if index not in {1, 2} or phase != f"feedback_{index}":
                raise ValueError(f"cannot finish feedback {index} from phase {phase}")
            active["last_answered_question_ids"] = []
            active["phase"] = "ready_question_2" if index == 1 else "complete"
            if index == 2:
                active["completed_at"] = utc_now()
        else:
            raise ValueError(f"unsupported event: {event}")
    if diagram_ref and diagram_ref not in active["diagram_refs"]:
        active["diagram_refs"].append(diagram_ref)
    active["updated_at"] = utc_now()


def main() -> None:
    parser = argparse.ArgumentParser(description="Advance a two-question micro-lesson state machine.")
    parser.add_argument("--state-dir", required=True)
    parser.add_argument("--event", choices=["start", "present", "answer", "finish-feedback"], required=True)
    parser.add_argument("--unit-id")
    parser.add_argument("--capability-id")
    parser.add_argument("--question-id", action="append", default=[])
    parser.add_argument("--question-index", type=int, choices=[1, 2], action="append")
    parser.add_argument("--pacing", choices=["together", "one-at-a-time"], default="together")
    parser.add_argument("--diagram-ref")
    args = parser.parse_args()

    path, state = load_state(Path(args.state_dir))
    if args.event == "start":
        if not args.unit_id or not args.capability_id:
            raise SystemExit("start requires --unit-id and --capability-id")
        start(state, unit_id=args.unit_id, capability_id=args.capability_id, question_ids=args.question_id, pacing=args.pacing)
    else:
        transition(state, event=args.event, question_index=args.question_index, diagram_ref=args.diagram_ref)
    state["updated_at"] = utc_now()
    write_json(path, state)
    print(json.dumps({"active_learning_unit": state["active_learning_unit"], "state": str(path)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
