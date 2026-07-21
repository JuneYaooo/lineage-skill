#!/usr/bin/env python3
"""Build a stable, validated capability graph from CoursePackage 1.0."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from build_teacher_model import load_course_package
from schema_utils import find_prerequisite_cycles, write_json
from stable_ids import stable_id


FIELD_TYPES = {
    "concepts": "concept",
    "diagnostics": "diagnosis",
    "methods": "decision",
    "workflows": "procedure",
    "templates": "production",
    "rubrics": "evaluation",
    "transfer_rules": "transfer",
}


def output_for(node_type: str, title: str) -> str:
    return {
        "concept": f"Explain and distinguish {title} without source cues.",
        "diagnosis": f"Detect the relevant signals and diagnose a case using {title}.",
        "decision": f"Select or reject {title} with explicit conditions and alternatives.",
        "procedure": f"Execute {title} and produce an inspectable artifact.",
        "production": f"Produce a usable artifact with {title}.",
        "evaluation": f"Evaluate an artifact with observable criteria from {title}.",
        "transfer": f"Transfer {title} to a changed context and name its limits.",
    }[node_type]


def build_capability_graph(package: dict[str, Any]) -> dict[str, Any]:
    course_id = package["manifest"]["course_id"]
    nodes: list[dict[str, Any]] = []
    asset_to_capability: dict[str, str] = {}
    previous_by_type: dict[str, str] = {}
    for field, node_type in FIELD_TYPES.items():
        for index, asset in enumerate(package.get(field, [])):
            title = str(asset.get("title") or asset.get("summary") or f"{node_type}-{index + 1}")
            node_id = stable_id("capability", course_id, node_type, asset.get("id"), title)
            prerequisites: list[str] = []
            explicit = [str(item) for item in asset.get("related_capabilities", []) if item in asset_to_capability]
            prerequisites.extend(asset_to_capability[item] for item in explicit)
            if node_type != "concept" and previous_by_type.get("concept"):
                prerequisites.append(previous_by_type["concept"])
            if node_type in {"procedure", "production", "evaluation", "transfer"} and previous_by_type.get("decision"):
                prerequisites.append(previous_by_type["decision"])
            if node_type == "transfer" and previous_by_type.get("procedure"):
                prerequisites.append(previous_by_type["procedure"])
            prerequisites = list(dict.fromkeys(item for item in prerequisites if item != node_id))
            nodes.append(
                {
                    "id": node_id,
                    "name": title,
                    "type": node_type,
                    "description": str(asset.get("summary") or title),
                    "observable_outputs": list(asset.get("outputs") or [output_for(node_type, title)]),
                    "prerequisites": prerequisites,
                    "success_rubrics": [],
                    "common_errors": list(asset.get("failure_modes") or []),
                    "practice_tasks": [],
                    "assessment_items": [],
                    "source_evidence": list(asset.get("evidence") or []),
                    "difficulty_band": min(5, 1 + list(FIELD_TYPES.values()).index(node_type) // 2),
                    "transfer_dimensions": ["domain", "scale", "resources", "risk"] if node_type == "transfer" else [],
                    "human_review": asset.get("human_review", "recommended"),
                    "source_asset_ids": [asset["id"]],
                }
            )
            asset_to_capability[asset["id"]] = node_id
            previous_by_type[node_type] = node_id
    edges: list[dict[str, Any]] = []
    for node in nodes:
        for prerequisite in node["prerequisites"]:
            edges.append(
                {
                    "id": stable_id("edge", course_id, prerequisite, node["id"], "prerequisite_of"),
                    "from": prerequisite,
                    "to": node["id"],
                    "type": "prerequisite_of",
                    "confidence": "medium",
                    "human_review": "recommended",
                }
            )
    cycles = find_prerequisite_cycles(nodes)
    node_ids = {node["id"] for node in nodes}
    dangling = [edge for edge in edges if edge["from"] not in node_ids or edge["to"] not in node_ids]
    uncovered = [node["id"] for node in nodes if not node["source_evidence"]]
    return {
        "schema_version": "1.0",
        "course_package_id": package["manifest"]["package_id"],
        "nodes": nodes,
        "edges": edges,
        "quality": {
            "status": "ready" if nodes and not cycles and not dangling else "blocked",
            "node_count": len(nodes),
            "edge_count": len(edges),
            "cycle_count": len(cycles),
            "cycles": cycles,
            "dangling_reference_count": len(dangling),
            "low_evidence_nodes": uncovered,
            "human_review_required": [node["id"] for node in nodes if node["human_review"] == "required"],
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build CapabilityGraph 1.0.")
    parser.add_argument("--course-package")
    parser.add_argument("--source-dir")
    parser.add_argument("--output")
    args = parser.parse_args()
    source_dir = Path(args.source_dir).expanduser().resolve() if args.source_dir else None
    package_path = Path(args.course_package).expanduser().resolve() if args.course_package else (source_dir / "course_package.json" if source_dir else None)
    if not package_path or not package_path.exists():
        raise SystemExit("provide --course-package or --source-dir")
    output = Path(args.output).expanduser().resolve() if args.output else package_path.parent / "capability_graph.json"
    graph = build_capability_graph(load_course_package(package_path))
    write_json(output, graph)
    print(json.dumps({"output": str(output), "quality": graph["quality"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
