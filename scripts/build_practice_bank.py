#!/usr/bin/env python3
"""Compile observable practice tasks, rubrics, hints, and error patterns."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from schema_utils import load_json, write_json
from stable_ids import stable_id


HINT_LADDER = [
    {"level": "H0", "action": "Restate the task constraints; reveal no method or answer."},
    {"level": "H1", "action": "Name one observation dimension without identifying the conclusion."},
    {"level": "H2", "action": "Name the relevant capability and one decision question."},
    {"level": "H3", "action": "Provide a partial structure with the decisive step left blank."},
    {"level": "H4", "action": "Show a complete source-grounded demonstration, then require a fresh redo."},
]


def rubric_for_node(node: dict[str, Any], course_id: str) -> dict[str, Any]:
    rubric_id = stable_id("rubric", course_id, node["id"], "observable-performance")
    return {
        "id": rubric_id,
        "name": f"{node['name']} observable performance",
        "capability_ids": [node["id"]],
        "criteria": [
            {
                "criterion_id": stable_id("rubric", rubric_id, "cue-and-frame"),
                "description": "Detects relevant cues and frames the actual problem before selecting a method.",
                "observable_evidence": "The artifact names concrete cues, constraints, and a falsifiable problem frame.",
                "levels": {
                    "0": "No cues or frame are observable.",
                    "1": "Repeats labels but does not connect them to case evidence.",
                    "2": "Names some relevant cues but misses a decisive constraint or confound.",
                    "3": "Uses the relevant cues and constraints to form a defensible problem frame.",
                    "4": "Also tests alternatives, uncertainty, and counterevidence before committing.",
                },
                "critical": True,
            },
            {
                "criterion_id": stable_id("rubric", rubric_id, "execution"),
                "description": "Executes or explains the capability as an inspectable sequence rather than a slogan.",
                "observable_evidence": "The output contains ordered decisions/actions and an artifact that another person can inspect.",
                "levels": {
                    "0": "No executable sequence or artifact is present.",
                    "1": "Provides a generic conclusion with no operational detail.",
                    "2": "Provides a partial sequence but omits an input, decision, or check.",
                    "3": "Completes the sequence with required inputs, decisions, and checks.",
                    "4": "Adapts the sequence while preserving invariants and explains the adaptation.",
                },
                "critical": True,
            },
            {
                "criterion_id": stable_id("rubric", rubric_id, "boundary"),
                "description": "Names applicability limits, uncertainty, and at least one failure condition.",
                "observable_evidence": "The output states when the method should not be used or what evidence would change the decision.",
                "levels": {
                    "0": "Claims universal applicability.",
                    "1": "Uses a vague caution with no actionable boundary.",
                    "2": "Names one limit but cannot connect it to the current case.",
                    "3": "Names relevant limits and the evidence needed to proceed safely.",
                    "4": "Compares counterexamples and proposes a safe fallback or escalation.",
                },
                "critical": True,
            },
        ],
        "failure_conditions": [
            "Any critical criterion scores below 2.",
            "The answer is fluent but contains no observable attempt or artifact.",
            "Unsupported inference is presented as teacher/source content.",
        ],
        "source_evidence": list(node.get("source_evidence") or []),
        "scoring_policy": {"aggregation": "all-critical-pass", "uncertainty": "Use insufficient_evidence when the artifact cannot support a criterion."},
    }


def task_shape(node_type: str) -> tuple[str, str, str]:
    return {
        "concept": ("imitation", "apply", "Apply the capability to a concrete case: identify what fits, what does not, and what conclusion or action the distinction supports."),
        "discrimination": ("coached", "compare", "Compare two plausible options, select one, and explain why the other does not apply."),
        "diagnosis": ("coached", "diagnose", "Diagnose the case from observable cues before naming a method."),
        "decision": ("coached", "predict", "Commit to a decision and confidence level, then list the evidence that would reverse it."),
        "procedure": ("independent", "produce", "Produce an inspectable artifact by executing the procedure without seeing the steps."),
        "production": ("independent", "produce", "Produce the requested work artifact and include a self-check against source-grounded criteria."),
        "evaluation": ("independent", "critique", "Critique an artifact criterion by criterion and request the smallest decisive revision."),
        "transfer": ("transfer", "experiment", "Apply the invariant to a changed context, state what changed, and run a safe real-world test."),
        "metacognition": ("transfer", "critique", "Compare confidence with evidence, name likely blind spots, and design a falsification check."),
    }.get(node_type, ("coached", "produce", "Create an observable output that demonstrates this capability."))


def error_pattern(node: dict[str, Any], course_id: str) -> dict[str, Any]:
    error_type = {
        "concept": "concept_boundary",
        "diagnosis": "cue_detection",
        "decision": "method_selection",
        "procedure": "procedure_execution",
        "production": "quality_evaluation",
        "evaluation": "quality_evaluation",
        "transfer": "transfer",
    }.get(node["type"], "relationship")
    return {
        "id": stable_id("error", course_id, node["id"], error_type),
        "type": error_type,
        "capability_ids": [node["id"]],
        "trigger": f"The learner claims {node['name']} but the output lacks its observable behavior.",
        "likely_prerequisite_gap": list(node.get("prerequisites") or []),
        "preferred_intervention": "Use the lowest hint level that points to the missing observation or decision; require a revision.",
        "resolved_by": "A later no-hint attempt satisfies all critical rubric criteria.",
    }


def practice_task(node: dict[str, Any], rubric: dict[str, Any], error: dict[str, Any], course_id: str) -> dict[str, Any]:
    stage, task_type, action = task_shape(node["type"])
    task_id = stable_id("task", course_id, node["id"], stage, task_type)
    return {
        "id": task_id,
        "title": f"Practice: {node['name']}",
        "capability_ids": [node["id"]],
        "prerequisite_ids": list(node.get("prerequisites") or []),
        "stage": stage,
        "task_type": task_type,
        "difficulty": int(node.get("difficulty_band") or 2),
        "estimated_cognitive_load": "medium" if int(node.get("difficulty_band") or 2) < 4 else "high",
        "context": f"Use a case or project that requires {node['description']}",
        "learner_prompt": f"Question 2 of 2 — Application. {action} Submit the artifact, your reasoning, and confidence (0-100).",
        "inputs": ["A relevant case or real project", "Known constraints", "Any source index explicitly allowed by the Mentor"],
        "expected_output": {
            "type": "mixed" if task_type in {"produce", "experiment"} else "text",
            "requirements": ["Observable attempt", "Reasoning tied to case evidence", "Confidence before feedback", "Boundary or failure condition"],
        },
        "rubric_ids": [rubric["id"]],
        "hint_ladder": HINT_LADDER,
        "common_errors": [error["id"]],
        "feedback_rules": [
            "Describe the learner's actual attempt without inflation.",
            "Name one effective behavior and one primary bottleneck.",
            "Cite the rubric criterion and source evidence before giving the smallest hint.",
            "Require a concrete revision; do not count a direct-answer substitution as mastery evidence.",
        ],
        "revision_required": True,
        "transfer_variants": [],
        "evidence_answer": {
            "provenance": "source_grounded_synthesis",
            "evidence": list(node.get("source_evidence") or []),
            "scoring_notes": f"Evaluate observable performance of {node['name']}; do not compare wording alone.",
        },
        "safety": {
            "high_risk_policy": "Keep medical, legal, financial, investment, and other high-risk practice educational and non-operational unless appropriately supervised.",
            "source_boundary": "Label teacher content, synthesis, Mentor inference, learner hypothesis, and real-world evidence separately.",
        },
        "micro_lesson": {"question_index": 2, "purpose": "application", "present_together": True, "wait_for_response": True},
    }


def understanding_task(node: dict[str, Any], rubric: dict[str, Any], error: dict[str, Any], course_id: str) -> dict[str, Any]:
    task_id = stable_id("task", course_id, node["id"], "micro-lesson-question-1")
    return {
        "id": task_id,
        "title": f"Understanding check: {node['name']}",
        "capability_ids": [node["id"]],
        "prerequisite_ids": list(node.get("prerequisites") or []),
        "stage": "imitation",
        "task_type": "explain",
        "difficulty": max(1, int(node.get("difficulty_band") or 2) - 1),
        "estimated_cognitive_load": "low",
        "context": f"Check the learner's mental model of {node['description']} after the micro-lesson explanation.",
        "learner_prompt": (
            f"Question 1 of 2 — Understanding. Explain {node['name']} in your own words, "
            "identify the most important relationship or distinction, and give one case where it would not apply."
        ),
        "inputs": ["The completed micro-lesson explanation and its source-grounded visual"],
        "expected_output": {
            "type": "text",
            "requirements": ["Own-words explanation", "Key relationship or distinction", "Boundary or counterexample"],
        },
        "rubric_ids": [rubric["id"]],
        "hint_ladder": HINT_LADDER,
        "common_errors": [error["id"]],
        "feedback_rules": [
            "Describe the learner's actual mental model before correcting it.",
            "Name one effective idea and one primary misconception or missing distinction.",
            "Give the smallest source-grounded correction without repeating the full lesson; evaluate question 2 separately.",
        ],
        "revision_required": False,
        "transfer_variants": [],
        "evidence_answer": {
            "provenance": "source_grounded_synthesis",
            "evidence": list(node.get("source_evidence") or []),
            "scoring_notes": f"Check the learner's mental model of {node['name']}; wording need not match the source.",
        },
        "safety": {
            "high_risk_policy": "Keep medical, legal, financial, investment, and other high-risk checks educational and non-operational unless appropriately supervised.",
            "source_boundary": "Label teacher content, synthesis, Mentor inference, learner hypothesis, and real-world evidence separately.",
        },
        "micro_lesson": {"question_index": 1, "purpose": "understanding", "present_together": True, "wait_for_response": True},
    }


def micro_lesson_unit(node: dict[str, Any], question_one: dict[str, Any], question_two: dict[str, Any], course_id: str) -> dict[str, Any]:
    unit_id = stable_id("learning_unit", course_id, node["id"], "micro-lesson")
    return {
        "id": unit_id,
        "capability_id": node["id"],
        "title": f"Micro-lesson: {node['name']}",
        "objective": node["description"],
        "prerequisite_ids": list(node.get("prerequisites") or []),
        "source_evidence": list(node.get("source_evidence") or []),
        "teaching_sequence": [
            {"stage": "orientation", "instruction": "State why this idea matters and connect it to one learner goal or familiar situation."},
            {"stage": "prerequisite_bridge", "instruction": "Recall only the prerequisite needed for this idea; diagnose first if that prerequisite is uncertain."},
            {"stage": "plain_language_model", "instruction": "Give a short intuitive explanation before introducing precise terminology."},
            {"stage": "precise_model", "instruction": "State the source-grounded definition, mechanism, conditions, and important distinction."},
            {"stage": "visual_model", "instruction": "Use a source visual, compact ASCII diagram, or generated SVG when relationships are easier to see than read."},
            {"stage": "worked_example", "instruction": "Walk through one concrete example step by step and point back to the visual."},
            {"stage": "counterexample", "instruction": "Show one plausible non-example, boundary, or common confusion."},
            {"stage": "recap", "instruction": "End with no more than three takeaways before showing the two-question check."},
        ],
        "visual_strategy": {
            "priority": ["source_visual", "ascii", "svg", "text_only"],
            "svg_when": [
                "three or more entities or stages interact",
                "a cycle, hierarchy, comparison, or causal flow is central",
                "spatial grouping materially reduces explanation length",
            ],
            "allowed_svg_kinds": ["flow", "cycle", "compare", "hierarchy"],
            "accessibility": ["title", "description", "high_contrast", "text_fallback"],
            "avoid": ["mermaid_code_unless_the_host_renderer_is_confirmed"],
        },
        "questions": [
            {
                "order": 1,
                "task_id": question_one["id"],
                "purpose": "understanding",
                "unlock_after": "teaching_complete",
                "present_together": True,
                "wait_for_response": True,
            },
            {
                "order": 2,
                "task_id": question_two["id"],
                "purpose": "application",
                "unlock_after": "teaching_complete",
                "present_together": True,
                "wait_for_response": True,
            },
        ],
        "completion_policy": {
            "required_answer_count": 2,
            "question_pacing_default": "together",
            "question_pacing_allowed": ["together", "one-at-a-time"],
            "present_both_after_teaching": True,
            "feedback_per_numbered_answer": True,
            "advance_only_after_both_answers_feedback": True,
            "formative_checks_alone_do_not_prove_mastery": True,
        },
    }


def build_practice_bank(package: dict[str, Any], graph: dict[str, Any], *, depth: str = "standard") -> dict[str, Any]:
    course_id = package["manifest"]["course_id"]
    rubrics: list[dict[str, Any]] = []
    tasks: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    learning_units: list[dict[str, Any]] = []
    for node in graph.get("nodes", []):
        rubric = rubric_for_node(node, course_id)
        error = error_pattern(node, course_id)
        question_one = understanding_task(node, rubric, error, course_id)
        task = practice_task(node, rubric, error, course_id)
        unit = micro_lesson_unit(node, question_one, task, course_id)
        question_one["micro_lesson"]["unit_id"] = unit["id"]
        task["micro_lesson"]["unit_id"] = unit["id"]
        rubrics.append(rubric)
        errors.append(error)
        tasks.append(question_one)
        tasks.append(task)
        learning_units.append(unit)
        node["success_rubrics"] = [rubric["id"]]
        node["practice_tasks"] = [question_one["id"], task["id"]]
        if depth == "deep" and node["type"] != "transfer":
            transfer_task = dict(task)
            transfer_task["id"] = stable_id("task", course_id, node["id"], "transfer-variant")
            transfer_task["title"] = f"Transfer practice: {node['name']}"
            transfer_task["stage"] = "transfer"
            transfer_task["difficulty"] = min(5, task["difficulty"] + 1)
            transfer_task["learner_prompt"] = f"Apply {node['name']} in a context that changes at least one of domain, scale, time, resources, audience, or risk. Explain what transfers, what does not, and provide a counterexample."
            transfer_task["transfer_variants"] = [task["id"]]
            transfer_task.pop("micro_lesson", None)
            task["transfer_variants"] = [transfer_task["id"]]
            tasks.append(transfer_task)
            node["practice_tasks"].append(transfer_task["id"])
    return {
        "schema_version": "1.0",
        "course_package_id": package["manifest"]["package_id"],
        "practice_depth": depth,
        "learning_units": learning_units,
        "rubrics": rubrics,
        "tasks": tasks,
        "error_patterns": errors,
        "quality": {
            "status": "ready" if tasks and learning_units and all(task["hint_ladder"] == HINT_LADDER for task in tasks) and all(
                len(unit["questions"]) == 2
                and all(question.get("unlock_after") == "teaching_complete" and question.get("present_together") is True for question in unit["questions"])
                and unit["completion_policy"].get("question_pacing_default") == "together"
                for unit in learning_units
            ) else "blocked",
            "learning_unit_count": len(learning_units),
            "two_question_unit_count": sum(len(unit["questions"]) == 2 for unit in learning_units),
            "task_count": len(tasks),
            "rubric_count": len(rubrics),
            "error_pattern_count": len(errors),
            "capability_coverage": len({cap for task in tasks for cap in task["capability_ids"]}),
            "placeholder_count": 0,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build PracticeBank 1.0.")
    parser.add_argument("--source-dir", required=True)
    parser.add_argument("--practice-depth", choices=["standard", "deep"], default="standard")
    parser.add_argument("--output")
    args = parser.parse_args()
    source_dir = Path(args.source_dir).expanduser().resolve()
    package = load_json(source_dir / "course_package.json")
    graph = load_json(source_dir / "capability_graph.json")
    bank = build_practice_bank(package, graph, depth=args.practice_depth)
    output = Path(args.output).expanduser().resolve() if args.output else source_dir / "practice_bank.json"
    write_json(output, bank)
    write_json(source_dir / "capability_graph.json", graph)
    print(json.dumps({"output": str(output), "quality": bank["quality"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
