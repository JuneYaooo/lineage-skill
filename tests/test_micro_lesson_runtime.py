from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from advance_micro_lesson import start, transition  # noqa: E402
from build_practice_bank import build_practice_bank  # noqa: E402
from render_learning_svg import parse_edges, parse_nodes, render  # noqa: E402


class MicroLessonBankTests(unittest.TestCase):
    def setUp(self) -> None:
        self.package = {"manifest": {"course_id": "course_demo", "package_id": "package_demo"}}
        self.graph = {
            "nodes": [
                {
                    "id": "cap_observe",
                    "name": "Observe before deciding",
                    "type": "concept",
                    "description": "Separate observable cues from conclusions.",
                    "prerequisites": [],
                    "source_evidence": ["claim_observe"],
                    "difficulty_band": 1,
                },
                {
                    "id": "cap_decide",
                    "name": "Make a bounded decision",
                    "type": "decision",
                    "description": "Choose an action with an explicit reversal condition.",
                    "prerequisites": ["cap_observe"],
                    "source_evidence": ["claim_decide"],
                    "difficulty_band": 2,
                },
            ]
        }

    def test_each_capability_gets_two_questions_presented_together(self) -> None:
        bank = build_practice_bank(self.package, self.graph, depth="deep")
        self.assertEqual(len(bank["learning_units"]), len(self.graph["nodes"]))
        self.assertEqual(bank["quality"]["two_question_unit_count"], 2)
        task_ids = {task["id"] for task in bank["tasks"]}
        for unit in bank["learning_units"]:
            self.assertEqual(len(unit["questions"]), 2)
            self.assertEqual(unit["questions"][0]["unlock_after"], "teaching_complete")
            self.assertEqual(unit["questions"][1]["unlock_after"], "teaching_complete")
            self.assertTrue(all(question["present_together"] for question in unit["questions"]))
            self.assertTrue(all(question["wait_for_response"] for question in unit["questions"]))
            self.assertEqual(unit["completion_policy"]["question_pacing_default"], "together")
            self.assertIn("mermaid_code_unless_the_host_renderer_is_confirmed", unit["visual_strategy"]["avoid"])
            self.assertTrue(all(question["task_id"] in task_ids for question in unit["questions"]))
            question_tasks = {task["id"]: task for task in bank["tasks"]}
            first_prompt = question_tasks[unit["questions"][0]["task_id"]]["learner_prompt"]
            second_prompt = question_tasks[unit["questions"][1]["task_id"]]["learner_prompt"]
            self.assertNotEqual(first_prompt, second_prompt)
            if unit["capability_id"] == "cap_observe":
                self.assertIn("concrete case", second_prompt.lower())

    def test_deep_transfer_task_is_not_a_third_micro_lesson_question(self) -> None:
        bank = build_practice_bank(self.package, self.graph, depth="deep")
        self.assertTrue(any(task["stage"] == "transfer" for task in bank["tasks"]))
        self.assertTrue(all(len(unit["questions"]) == 2 for unit in bank["learning_units"]))


class MicroLessonStateTests(unittest.TestCase):
    def initial_state(self) -> dict:
        return {"active_learning_unit": None}

    def test_default_pacing_accepts_both_answers_together(self) -> None:
        state = self.initial_state()
        start(state, unit_id="unit_1", capability_id="cap_1", question_ids=["task_1", "task_2"])
        transition(state, event="present", question_index=None, diagram_ref="diagram.svg")
        self.assertEqual(state["active_learning_unit"]["phase"], "awaiting_answers")
        transition(state, event="answer", question_index=[1, 2], diagram_ref=None)
        self.assertEqual(state["active_learning_unit"]["phase"], "feedback_batch")
        transition(state, event="finish-feedback", question_index=None, diagram_ref=None)
        active = state["active_learning_unit"]
        self.assertEqual(active["phase"], "complete")
        self.assertEqual(active["pacing"], "together")
        self.assertEqual(active["answered_question_ids"], ["task_1", "task_2"])
        self.assertEqual(active["diagram_refs"], ["diagram.svg"])

    def test_together_pacing_waits_for_an_unanswered_number(self) -> None:
        state = self.initial_state()
        start(state, unit_id="unit_1", capability_id="cap_1", question_ids=["task_1", "task_2"])
        transition(state, event="present", question_index=None, diagram_ref=None)
        transition(state, event="answer", question_index=1, diagram_ref=None)
        transition(state, event="finish-feedback", question_index=None, diagram_ref=None)
        self.assertEqual(state["active_learning_unit"]["phase"], "awaiting_answers")
        transition(state, event="answer", question_index=2, diagram_ref=None)
        transition(state, event="finish-feedback", question_index=None, diagram_ref=None)
        self.assertEqual(state["active_learning_unit"]["phase"], "complete")

    def test_one_at_a_time_pacing_remains_available(self) -> None:
        state = self.initial_state()
        start(state, unit_id="unit_1", capability_id="cap_1", question_ids=["task_1", "task_2"], pacing="one-at-a-time")
        transition(state, event="present", question_index=1, diagram_ref=None)
        transition(state, event="answer", question_index=1, diagram_ref=None)
        transition(state, event="finish-feedback", question_index=1, diagram_ref=None)
        transition(state, event="present", question_index=2, diagram_ref=None)
        transition(state, event="answer", question_index=2, diagram_ref=None)
        transition(state, event="finish-feedback", question_index=2, diagram_ref=None)
        self.assertEqual(state["active_learning_unit"]["phase"], "complete")

    def test_start_rejects_any_count_other_than_two(self) -> None:
        with self.assertRaises(ValueError):
            start(self.initial_state(), unit_id="unit_1", capability_id="cap_1", question_ids=["task_1"])


class LearningSvgTests(unittest.TestCase):
    def test_svg_is_accessible_static_and_escapes_text(self) -> None:
        nodes = parse_nodes(["a|Observe <script>|Evidence & cues", "b|Decide|Apply a rule"])
        edges = parse_edges(["a|b|then"], {"a", "b"})
        svg = render("flow", "A < B", "A safe teaching diagram", nodes, edges)
        self.assertIn("<title id=\"diagram-title\">A &lt; B</title>", svg)
        self.assertIn("<desc id=\"diagram-desc\">", svg)
        self.assertNotIn("<script>", svg)
        self.assertNotIn("<foreignObject", svg)
        self.assertNotIn("javascript:", svg.lower())
        self.assertIn("Observe &lt;script&gt;", svg)

    def test_svg_can_be_written_as_a_standalone_file(self) -> None:
        nodes = parse_nodes(["a|Observe|Evidence", "b|Decide|Rule", "c|Verify|Result"])
        svg = render("cycle", "Decision cycle", "Observe, decide, and verify", nodes, [])
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "diagram.svg"
            path.write_text(svg, encoding="utf-8")
            self.assertTrue(path.read_text(encoding="utf-8").startswith("<svg"))

    def test_malformed_hierarchy_cycle_still_renders_bounded_output(self) -> None:
        nodes = parse_nodes(["a|A|First", "b|B|Second"])
        edges = parse_edges(["a|b|", "b|a|"], {"a", "b"})
        svg = render("hierarchy", "Cycle fallback", "A malformed hierarchy", nodes, edges)
        self.assertLess(len(svg), 20_000)
        self.assertIn("node-a", svg)
        self.assertIn("node-b", svg)


class GeneratedSkillIntegrationTests(unittest.TestCase):
    def asset(self, asset_id: str, title: str, **extra: object) -> dict:
        return {
            "id": asset_id,
            "title": title,
            "summary": title,
            "provenance": "direct_source",
            "confidence": "high",
            "evidence": ["evidence_1"],
            **extra,
        }

    def package(self) -> dict:
        return {
            "schema_version": "1.0",
            "manifest": {"course_id": "course_demo", "package_id": "package_demo", "course_name": "Demo Course"},
            "sources": [{"id": "source_1", "path": "demo.md", "kind": "markdown"}],
            "lessons": [{"id": "lesson_1", "title": "Demo Lesson"}],
            "claims": [{"id": "claim_1", "text": "Observe before deciding.", "provenance": "direct_source", "evidence": ["evidence_1"]}],
            "concepts": [self.asset("concept_1", "Observable evidence")],
            "topics": [],
            "cases": [self.asset("case_1", "Worked case", steps=["Observe", "Decide", "Verify"])],
            "methods": [self.asset("method_1", "Bounded decision", conditions=["Evidence is observable"])],
            "diagnostics": [self.asset("diagnostic_1", "Cue check", conditions=["Before choosing a method"])],
            "workflows": [self.asset("workflow_1", "Observe decide verify", steps=["Observe", "Decide", "Verify"])],
            "rubrics": [self.asset("rubric_1", "Decision quality")],
            "templates": [],
            "transfer_rules": [],
            "failure_modes": [self.asset("failure_1", "Jumping to conclusions")],
            "boundaries": [self.asset("boundary_1", "Stop when evidence is missing")],
            "quotes": [],
            "learning_checks": [],
            "study_paths": [],
            "teacher_model_ref": "teacher_model.json",
            "capability_graph_ref": "capability_graph.json",
            "practice_bank_ref": "practice_bank.json",
            "assessment_bank_ref": "assessment_bank.json",
            "evidence": [{"id": "evidence_1", "source_id": "source_1", "path": "demo.md#L1", "confidence": "high", "evidence_kind": "text"}],
            "quality": {
                "coverage": {},
                "integrity": {"dangling_reference_count": 0, "unsupported_claim_count": 0},
                "mentor_readiness": {"status": "pending", "missing_requirements": [], "human_review_required": []},
            },
        }

    def test_generated_mentor_contains_and_validates_micro_lesson_runtime(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source"
            output = root / "dist"
            source.mkdir()
            (source / "course_package.json").write_text(json.dumps(self.package(), ensure_ascii=False), encoding="utf-8")
            env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "build_course_skill.py"),
                    "--course-name",
                    "Demo Course",
                    "--skill-name",
                    "demo-course-mentor",
                    "--mode",
                    "mentor",
                    "--source-dir",
                    str(source),
                    "--output-dir",
                    str(output),
                ],
                cwd=ROOT,
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            skill = output / "demo-course-mentor"
            self.assertTrue((skill / "references" / "micro_lesson_protocol.md").exists())
            self.assertTrue((skill / "scripts" / "advance_micro_lesson.py").exists())
            self.assertTrue((skill / "scripts" / "render_learning_svg.py").exists())
            bank = json.loads((skill / "references" / "practice_bank.json").read_text(encoding="utf-8"))
            self.assertTrue(bank["learning_units"])
            self.assertTrue(all(len(unit["questions"]) == 2 for unit in bank["learning_units"]))
            report = json.loads((skill / "validation_report.json").read_text(encoding="utf-8"))
            self.assertTrue(report["valid"], report)


if __name__ == "__main__":
    unittest.main()
