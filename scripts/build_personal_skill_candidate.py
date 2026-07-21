#!/usr/bin/env python3
"""Build a provenance-preserving Personal Skill candidate from repeated episodes."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

from runtime_state import highest_hint, read_json, read_jsonl, write_json


def slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")[:63] or "personal-practice"


def eligible(episodes: list[dict], capability_id: str) -> tuple[bool, list[str], list[dict]]:
    relevant = [item for item in episodes if capability_id in item.get("capability_ids", [])]
    successes = [item for item in relevant if item.get("outcome", {}).get("task_result") == "pass"]
    contexts = {str(item.get("context", {}).get("project") or item.get("context", {}).get("environment") or "") for item in successes}
    failures = [item for item in relevant if item.get("outcome", {}).get("task_result") in {"revise", "fail"}]
    reasons = []
    if len(successes) < 3:
        reasons.append("requires at least three successful practices")
    if len({item for item in contexts if item}) < 2:
        reasons.append("requires at least two distinct contexts")
    if not any(highest_hint(item) == "H0" for item in successes):
        reasons.append("requires at least one no-hint execution")
    if not failures and not any(item.get("errors") for item in relevant):
        reasons.append("requires a failure, counterexample, or recorded error")
    return not reasons, reasons, relevant


def build_candidate(mentor: dict, graph: dict, episodes: list[dict], capability_id: str, name: str) -> dict:
    ok, reasons, relevant = eligible(episodes, capability_id)
    if not ok:
        raise ValueError("; ".join(reasons))
    node = next(item for item in graph.get("nodes", []) if item["id"] == capability_id)
    successes = [item for item in relevant if item.get("outcome", {}).get("task_result") == "pass"]
    failures = [item for item in relevant if item.get("outcome", {}).get("task_result") != "pass" or item.get("errors")]
    candidate_name = slugify(name)
    episode_ids = [item["episode_id"] for item in relevant]
    return {
        "schema_version": "1.0",
        "candidate_id": "candidate_" + hashlib.sha256(
            "\x1f".join([mentor["manifest"]["mentor_package_id"], capability_id, *episode_ids]).encode("utf-8")
        ).hexdigest()[:16],
        "name": candidate_name,
        "purpose": node["description"],
        "triggers": [f"Use when the user needs to {output.lower()}" for output in node.get("observable_outputs", [])[:3]],
        "preconditions": [f"Capability evidence for {item}" for item in node.get("prerequisites", [])],
        "procedure": ["Inspect the real context and constraints", "Select and execute the learned capability", "Evaluate the output against observable criteria", "Record boundary conditions and real-world result"],
        "tools": [],
        "outputs": node.get("observable_outputs", []),
        "evaluator": {"critical_invariants": ["observable artifact", "source/personal provenance separation", "known failure handled"], "evidence_episodes": [item["episode_id"] for item in successes]},
        "failure_modes": [error for item in failures for error in item.get("errors", [])] or ["Fails when applicability conditions or required evidence are absent"],
        "source_lineage": {"mentor_package_id": mentor["manifest"]["mentor_package_id"], "teacher_rules_used": [], "evidence_pointers": node.get("source_evidence", [])},
        "personal_adaptations": {"changes": [], "rationale": "To be completed and approved by the learner before promotion.", "episode_evidence": episode_ids},
        "real_world_evidence": [item.get("outcome", {}).get("real_world_result") for item in successes if item.get("outcome", {}).get("real_world_result")],
        "regression_tests": [
            {"prompt": f"Apply {node['name']} in a familiar context without hints.", "expected_invariants": ["observable output", "all critical criteria pass"]},
            {"prompt": f"Apply {node['name']} after one major constraint changes.", "expected_invariants": ["transfer rationale", "boundary named", "no unsupported teacher claim"]},
            {"prompt": f"Identify a case where {node['name']} should not be used.", "expected_invariants": ["contraindication", "safe alternative"]},
        ],
        "confidence": "candidate",
        "promotion_status": "watch",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a Personal Skill candidate from external episodes.")
    parser.add_argument("--state-dir", required=True)
    parser.add_argument("--references-dir", default="../references")
    parser.add_argument("--capability-id", required=True)
    parser.add_argument("--name", required=True)
    args = parser.parse_args()
    state_dir = Path(args.state_dir).expanduser().resolve()
    references = (Path(__file__).resolve().parent / args.references_dir).resolve() if not Path(args.references_dir).is_absolute() else Path(args.references_dir)
    try:
        candidate = build_candidate(read_json(references / "mentor_package.json", {}), read_json(references / "capability_graph.json", {}), read_jsonl(state_dir / "practice_episodes.jsonl"), args.capability_id, args.name)
    except ValueError as exc:
        print(json.dumps({"eligible": False, "reason": str(exc)}, ensure_ascii=False, indent=2))
        raise SystemExit(1)
    output = state_dir / "personal_skill_candidates" / f"{candidate['name']}.json"
    write_json(output, candidate)
    print(json.dumps({"eligible": True, "output": str(output), "promotion_status": candidate["promotion_status"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
