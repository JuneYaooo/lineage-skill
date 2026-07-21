from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from build_personal_skill_candidate import build_candidate, eligible
from initialize_apprenticeship import initialize
from runtime_state import append_jsonl, rebuild_mastery, write_json
from schedule_retrieval import schedule
from select_next_practice import select_task
from validate_learner_state import validate


def episode(
    episode_id: str,
    mentor_id: str,
    capability_id: str,
    *,
    result: str = "pass",
    stage: str = "independent_practice",
    project: str = "project-a",
    hint: str = "H0",
    errors: list[str] | None = None,
) -> dict:
    return {
        "schema_version": "1.0",
        "episode_id": episode_id,
        "mentor_package_id": mentor_id,
        "learner_id": "learner-private",
        "timestamp_start": f"2026-01-0{episode_id[-1]}T00:00:00+00:00",
        "timestamp_end": None,
        "stage": stage,
        "task_id": "task_1",
        "capability_ids": [capability_id],
        "context": {"project": project, "environment": "test", "constraints": []},
        "prediction": {"learner_prediction": "attempt", "confidence_before": 85},
        "attempts": [{"attempt_number": 1, "artifact_ref": "artifact://authorized", "content_summary": "observable attempt", "timestamp": "2026-01-01T00:00:00+00:00"}],
        "hints": [] if hint == "H0" else [{"level": hint, "content": "minimal cue"}],
        "feedback": {"rubric_results": [{"criterion_id": "criterion_1", "score": 3, "passed": result == "pass", "critical": True}], "source_evidence": ["card_1"], "mentor_inference": "", "next_revision": ""},
        "outcome": {"task_result": result, "real_world_result": "worked" if result == "pass" else None, "confidence_after": 80, "learner_reflection": "reflection"},
        "errors": errors or [],
        "mastery_events": [],
        "next_actions": [],
        "provenance": "learner_observation",
    }


def test_external_state_is_rebuildable_and_advances_at_most_one_level(tmp_path: Path) -> None:
    mentor_id = "mentor_123"
    capability_id = "cap_123"
    mentor = {
        "manifest": {"mentor_package_id": mentor_id},
        "learning_contract_template": {"graduation_target": {"transfer": True}},
    }
    mentor_path = tmp_path / "references" / "mentor_package.json"
    write_json(mentor_path, mentor)
    state_dir = initialize(mentor_path, tmp_path / "private", "learner-private", capabilities=[capability_id], project="real project")

    first = episode("episode_1", mentor_id, capability_id)
    append_jsonl(state_dir / "practice_episodes.jsonl", first, unique_key="episode_id")
    mastery = rebuild_mastery([first], mentor_package_id=mentor_id, learner_id="learner-private")

    assert mastery["capabilities"][0]["state"] == "recognized"
    write_json(state_dir / "mastery_state.json", mastery)
    assert validate(state_dir)["valid"] is True
    assert not (tmp_path / "references" / "apprenticeship_state.json").exists()


def test_transfer_retrieval_selection_and_personal_skill_candidate(tmp_path: Path) -> None:
    mentor_id = "mentor_123"
    capability_id = "cap_123"
    episodes = [
        episode("episode_1", mentor_id, capability_id, result="fail", errors=["error_boundary"]),
        episode("episode_2", mentor_id, capability_id, project="project-a"),
        episode("episode_3", mentor_id, capability_id, project="project-b", stage="transfer"),
        episode("episode_4", mentor_id, capability_id, project="project-b"),
    ]
    ok, reasons, _ = eligible(episodes, capability_id)
    assert ok is True and reasons == []

    graph = {"nodes": [{"id": capability_id, "name": "Frame a decision", "description": "Frame an observable decision.", "observable_outputs": ["Decision brief"], "prerequisites": [], "source_evidence": ["card_1"]}]}
    practice = {"tasks": [{"id": "task_1", "capability_ids": [capability_id], "difficulty": 2, "stage": "transfer"}]}
    references = tmp_path / "references"
    write_json(references / "practice_bank.json", practice)
    write_json(references / "capability_graph.json", graph)
    write_json(tmp_path / "mastery_state.json", rebuild_mastery(episodes, mentor_package_id=mentor_id, learner_id="learner-private"))
    write_json(tmp_path / "review_queue.json", {"schema_version": "1.0", "items": schedule(capability_id, base_time=dt.datetime(2020, 1, 1, tzinfo=dt.timezone.utc), intervals=[1], last_result="pass", high_confidence_error=False)})
    write_json(tmp_path / "error_library.json", {"schema_version": "1.0", "errors": []})

    selected = select_task(tmp_path, references, [])
    candidate = build_candidate({"manifest": {"mentor_package_id": mentor_id}}, graph, episodes, capability_id, "My Decision Practice")

    assert "overdue retrieval" in selected["selection_reasons"]
    assert candidate["source_lineage"]["mentor_package_id"] == mentor_id
    assert set(candidate["personal_adaptations"]["episode_evidence"]) == {item["episode_id"] for item in episodes}
    assert candidate["promotion_status"] == "watch"
