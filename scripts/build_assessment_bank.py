#!/usr/bin/env python3
"""Build retrieval, transfer, boundary, production, and graduation assessments."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from schema_utils import load_json, write_json
from stable_ids import stable_id


def assessment_item(node: dict[str, Any], rubric_ids: list[str], course_id: str, assessment_type: str) -> dict[str, Any]:
    prompts = {
        "retrieval": f"Without opening the course notes, reconstruct {node['name']}: cues, decision/action sequence, self-check, and one limit.",
        "transfer": f"Use {node['name']} in an unseen case where domain, scale, resources, time, audience, or risk differs. State structural similarities, differences, and a counterexample.",
        "boundary": f"Given a plausible case, decide whether {node['name']} should not be used. Name the decisive evidence, contraindication, and safe alternative.",
        "production": f"Independently produce a real artifact that demonstrates {node['name']}; include inputs, decisions, output, self-evaluation, and real-world result when available.",
        "graduation": f"Independently diagnose, choose, execute, evaluate, and defend a real-world use of {node['name']} with no method hints.",
    }
    novelty = {
        "retrieval": ["delayed", "new surface form"],
        "transfer": ["domain", "constraints", "risk"],
        "boundary": ["counterexample", "contraindication"],
        "production": ["real artifact", "independent execution"],
        "graduation": ["unseen case", "no hints", "real-world evidence"],
    }
    support = "none" if assessment_type in {"retrieval", "transfer", "graduation"} else "source-index"
    return {
        "id": stable_id("assessment", course_id, node["id"], assessment_type),
        "capability_ids": [node["id"]],
        "assessment_type": assessment_type,
        "prompt": prompts[assessment_type],
        "novelty_dimensions": novelty[assessment_type],
        "allowed_support": support,
        "time_condition": "Run after a delay for retention evidence." if assessment_type == "retrieval" else None,
        "rubric_ids": rubric_ids,
        "blindness_rule": "Do not show the teacher demonstration, answer evidence, method name, or rubric anchors before the first submission.",
        "evidence_answer": {
            "provenance": "source_grounded_synthesis",
            "evidence": list(node.get("source_evidence") or []),
            "evaluator_note": "Score observable behavior and boundary recognition, not lexical similarity to source wording.",
        },
        "parallel_form_group": stable_id("assessment", course_id, node["id"], "parallel"),
    }


def build_assessment_bank(package: dict[str, Any], graph: dict[str, Any]) -> dict[str, Any]:
    course_id = package["manifest"]["course_id"]
    items: list[dict[str, Any]] = []
    for node in graph.get("nodes", []):
        types = ["retrieval", "boundary"]
        if node["type"] in {"procedure", "production", "evaluation", "transfer", "decision", "diagnosis"}:
            types.extend(["production", "transfer", "graduation"])
        else:
            types.append("transfer")
        node_items = [assessment_item(node, list(node.get("success_rubrics") or []), course_id, item_type) for item_type in types]
        items.extend(node_items)
        node["assessment_items"] = [item["id"] for item in node_items]
    required_types = ["retrieval", "transfer", "production", "boundary", "graduation"]
    present = {item["assessment_type"] for item in items}
    return {
        "schema_version": "1.0",
        "course_package_id": package["manifest"]["package_id"],
        "items": items,
        "graduation_matrix": {
            "required_assessment_types": required_types,
            "requirements": [
                "Delayed no-hint retrieval succeeds on a parallel form.",
                "An unseen case is diagnosed and completed independently.",
                "A real artifact satisfies every critical rubric criterion.",
                "The learner identifies boundaries, contraindications, and a counterexample.",
                "The learner compares the teacher method with a personal adaptation and cites evidence for the change.",
                "A Personal Skill candidate passes regression tests and receives explicit learner approval before promotion.",
            ],
            "single_success_is_sufficient": False,
            "requires_retention_and_transfer": True,
        },
        "quality": {
            "status": "ready" if set(required_types).issubset(present) and all(item["rubric_ids"] for item in items) else "blocked",
            "assessment_count": len(items),
            "types": sorted(present),
            "missing_types": sorted(set(required_types) - present),
            "capability_coverage": len({cap for item in items for cap in item["capability_ids"]}),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build AssessmentBank 1.0.")
    parser.add_argument("--source-dir", required=True)
    parser.add_argument("--output")
    args = parser.parse_args()
    source_dir = Path(args.source_dir).expanduser().resolve()
    package = load_json(source_dir / "course_package.json")
    graph = load_json(source_dir / "capability_graph.json")
    bank = build_assessment_bank(package, graph)
    output = Path(args.output).expanduser().resolve() if args.output else source_dir / "assessment_bank.json"
    write_json(output, bank)
    write_json(source_dir / "capability_graph.json", graph)
    print(json.dumps({"output": str(output), "quality": bank["quality"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
