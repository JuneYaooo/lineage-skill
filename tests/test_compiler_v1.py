from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from build_assessment_bank import build_assessment_bank
from build_capability_graph import build_capability_graph
from build_mentor_package import build_mentor_package
from build_practice_bank import HINT_LADDER, build_practice_bank
from build_teacher_model import build_teacher_model
from migrate_course_package import migrate_package
from schema_utils import write_json


ROOT = Path(__file__).resolve().parents[1]


def source_package() -> dict:
    raw = json.loads((ROOT / "tests" / "fixtures" / "course-package-0.1" / "course_package.json").read_text(encoding="utf-8"))
    package, _ = migrate_package(raw)
    evidence_id = package["evidence"][0]["id"]
    for field in ["methods", "diagnostics", "workflows", "rubrics", "transfer_rules", "failure_modes", "boundaries"]:
        for item in package[field]:
            item["evidence"] = [evidence_id]
            item["confidence"] = "medium"
    package["cases"] = [
        {
            "id": "case_0123456789abcdef",
            "title": "Worked diagnosis",
            "summary": "Observe constraints, frame the gap, select a small experiment, and self-check.",
            "details": {},
            "conditions": [],
            "inputs": ["case cues"],
            "outputs": ["diagnosis"],
            "steps": ["observe", "frame", "choose", "check"],
            "evidence": [evidence_id],
            "provenance": "direct_source",
            "confidence": "medium",
            "source_courses": [package["manifest"]["course_id"]],
            "related_capabilities": [],
            "failure_modes": [],
            "human_review": "none"
        }
    ]
    return package


def test_compiler_builds_graph_tasks_assessments_and_full_mentor(tmp_path: Path) -> None:
    package = source_package()
    teacher = build_teacher_model(package)
    graph = build_capability_graph(package)
    practice = build_practice_bank(package, graph, depth="deep")
    assessment = build_assessment_bank(package, graph)

    assert teacher["quality"]["status"] == "ready"
    assert graph["quality"]["cycle_count"] == 0
    assert all(node["practice_tasks"] and node["assessment_items"] for node in graph["nodes"])
    assert all(task["hint_ladder"] == HINT_LADDER for task in practice["tasks"])
    assert {"retrieval", "transfer", "production", "boundary", "graduation"}.issubset(assessment["quality"]["types"])
    assert all(len(criterion["levels"]) == 5 for rubric in practice["rubrics"] for criterion in rubric["criteria"])

    write_json(tmp_path / "course_package.json", package)
    write_json(tmp_path / "teacher_model.json", teacher)
    write_json(tmp_path / "capability_graph.json", graph)
    write_json(tmp_path / "practice_bank.json", practice)
    write_json(tmp_path / "assessment_bank.json", assessment)
    mentor = build_mentor_package(tmp_path, requested_mode="full")

    assert mentor["manifest"]["apprenticeship_mode"] == "full"
    assert mentor["quality"]["mentor_readiness"] == "ready"


def test_teacher_model_caps_inferred_high_confidence() -> None:
    package = source_package()
    package["methods"][0]["provenance"] = "mentor_inference"
    package["methods"][0]["confidence"] = "high"

    teacher = build_teacher_model(package)
    matched = next(item for item in teacher["epistemic_model"]["decision_rules"] if item["provenance"] == "mentor_inference")

    assert matched["confidence"] == "medium"


def test_teacher_model_strict_cli_rejects_partial_model(tmp_path: Path) -> None:
    package = source_package()
    package["cases"] = []
    package["methods"] = []
    package["rubrics"] = []
    write_json(tmp_path / "course_package.json", package)

    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "build_teacher_model.py"), "--source-dir", str(tmp_path), "--strict"],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 2
    assert '"status": "partial"' in result.stdout
