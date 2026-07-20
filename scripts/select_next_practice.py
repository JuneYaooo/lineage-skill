#!/usr/bin/env python3
"""Select the next practice task with an explainable priority trace."""

from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path

from runtime_state import MASTERY_STATES, read_json


def due(value: str | None, now: dt.datetime) -> bool:
    if not value:
        return False
    parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    if not parsed.tzinfo:
        parsed = parsed.replace(tzinfo=dt.timezone.utc)
    return parsed <= now


def select_task(state_dir: Path, references_dir: Path, project_capabilities: list[str]) -> dict:
    practice = read_json(references_dir / "practice_bank.json", {})
    graph = read_json(references_dir / "capability_graph.json", {})
    mastery = read_json(state_dir / "mastery_state.json", {"capabilities": []})
    queue = read_json(state_dir / "review_queue.json", {"items": []})
    errors = read_json(state_dir / "error_library.json", {"errors": []})
    now = dt.datetime.now(dt.timezone.utc)
    mastery_map = {item["capability_id"]: item for item in mastery.get("capabilities", [])}
    due_caps = {item["capability_id"] for item in queue.get("items", []) if item.get("status") != "completed" and due(item.get("due_at"), now)}
    high_error_caps = {cap for item in errors.get("errors", []) if item.get("high_confidence") and not item.get("resolved") for cap in item.get("capability_ids", [])}
    node_map = {node["id"]: node for node in graph.get("nodes", [])}
    scored = []
    for task in practice.get("tasks", []):
        cap = task.get("capability_ids", [None])[0]
        if not cap:
            continue
        state = mastery_map.get(cap, {"state": "unseen", "evidence_against": [], "transfer_contexts": []})
        score = 0
        reasons = []
        if cap in due_caps:
            score += 100
            reasons.append("overdue retrieval")
        if cap in project_capabilities:
            score += 80
            reasons.append("needed by current real project")
        dependents = sum(cap in node.get("prerequisites", []) for node in graph.get("nodes", []))
        if state["state"] in {"unseen", "recognized"} and dependents:
            score += 50 + dependents
            reasons.append(f"blocking prerequisite for {dependents} downstream capabilities")
        if cap in high_error_caps:
            score += 60
            reasons.append("repeated high-confidence error")
        if state["state"] in {"applied_independently", "transferred"}:
            score += 35
            reasons.append("recent promotion needs verification")
        if state["state"] == "applied_independently" and task.get("stage") == "transfer":
            score += 45
            reasons.append("independent success lacks transfer evidence")
        gap = max(0, MASTERY_STATES.index("retained") - MASTERY_STATES.index(state["state"]))
        score += gap
        if not reasons:
            reasons.append("nearest unmastered capability with suitable cognitive load")
        scored.append((score, task["difficulty"], task["id"], task, reasons, node_map.get(cap, {})))
    if not scored:
        raise ValueError("no practice tasks available")
    _, _, _, task, reasons, node = sorted(scored, key=lambda item: (-item[0], item[1], item[2]))[0]
    return {"task": task, "capability": node, "selection_reasons": reasons, "selected_at": now.isoformat(timespec="seconds")}


def main() -> None:
    parser = argparse.ArgumentParser(description="Select the next explainable practice task.")
    parser.add_argument("--state-dir", required=True)
    parser.add_argument("--references-dir", default="../references")
    parser.add_argument("--project-capability", action="append", default=[])
    args = parser.parse_args()
    references = (Path(__file__).resolve().parent / args.references_dir).resolve() if not Path(args.references_dir).is_absolute() else Path(args.references_dir)
    result = select_task(Path(args.state_dir).expanduser().resolve(), references, args.project_capability)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
