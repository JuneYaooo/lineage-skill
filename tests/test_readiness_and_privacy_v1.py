from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from build_mentor_readiness_audit import build_readiness_audit
from migrate_course_package import migrate_package
from run_course_pipeline import readiness_summary
from schema_utils import write_json
from validate_generated_skill import validate_skill


ROOT = Path(__file__).resolve().parents[1]


def test_readiness_requires_protocol_and_policy(tmp_path: Path) -> None:
    for name in ["course_package.json", "teacher_model.json", "capability_graph.json", "practice_bank.json", "assessment_bank.json"]:
        (tmp_path / name).write_text("{}", encoding="utf-8")

    audit = build_readiness_audit(tmp_path)

    assert "missing artifact: mentor_protocol" in audit["blockers"]
    assert "missing artifact: graduation_policy" in audit["blockers"]
    assert audit["apprenticeship_mode_allowed"] != "full"


def test_strict_readiness_cli_exits_nonzero_when_not_ready(tmp_path: Path) -> None:
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "build_mentor_readiness_audit.py"), "--source-dir", str(tmp_path), "--mode", "strict"],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 2
    assert '"status": "blocked"' in result.stdout


def test_readiness_summary_keeps_conclusions_separate(tmp_path: Path) -> None:
    course = tmp_path / "course"
    skill = tmp_path / "skill"
    course.mkdir()
    skill.mkdir()
    (course / "mentor_readiness_audit.json").write_text(json.dumps({"status": "partial", "source_readiness": {"status": "ready"}}), encoding="utf-8")
    (course / "mentor_package.json").write_text(json.dumps({"quality": {"runtime_readiness": "ready"}}), encoding="utf-8")
    (skill / "validation_report.json").write_text(json.dumps({"valid": False}), encoding="utf-8")

    assert readiness_summary(course, skill) == {"source_readiness": "ready", "mentor_readiness": "partial", "runtime_readiness": "blocked"}


def test_generated_skill_validator_rejects_private_learner_state(tmp_path: Path) -> None:
    (tmp_path / "lineage_manifest.json").write_text(json.dumps({"roles": [], "generated_by": {"id": "lineage-skill"}}), encoding="utf-8")
    for relative in ["SKILL.md", "agents/openai.yaml", "references/course_package.json", "scripts/search_course_notes.py", "scripts/fetch_course_evidence.py"]:
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("---\nname: demo\ndescription: demo\n---\n" if relative == "SKILL.md" else "{}", encoding="utf-8")
    (tmp_path / "apprenticeship_state.json").write_text("{}", encoding="utf-8")

    result = validate_skill(tmp_path)

    assert result["valid"] is False
    assert any("private learner state" in item["message"] for item in result["issues"])


def test_external_store_contract_declares_versioned_ids_privacy_and_append_only_state() -> None:
    contract = (ROOT / "references" / "external-learner-store-contract.md").read_text(encoding="utf-8")

    for term in ["versioned JSON", "stable `source`, `capability`, `task`, `rubric`, and `assessment` IDs", "append-only episodes", "explicit learner approval"]:
        assert term in contract


def test_generated_skill_withholds_raw_source_artifacts_by_default(tmp_path: Path) -> None:
    raw = json.loads((ROOT / "tests" / "fixtures" / "course-package-0.1" / "course_package.json").read_text(encoding="utf-8"))
    package, _ = migrate_package(raw)
    course = tmp_path / "private-course"
    course.mkdir()
    write_json(course / "course_package.json", package)
    (course / "full_transcript.md").write_text("PRIVATE TRANSCRIPT BODY", encoding="utf-8")
    (course / "transcripts").mkdir()
    (course / "transcripts" / "private.json").write_text('{"full_text":"PRIVATE"}', encoding="utf-8")
    output = tmp_path / "dist"

    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "build_course_skill.py"),
            "--course-name",
            "privacy-demo",
            "--skill-name",
            "privacy-demo-lineage",
            "--mode",
            "expert",
            "--source-dir",
            str(course),
            "--output-dir",
            str(output),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    skill = output / "privacy-demo-lineage"
    manifest = json.loads((skill / "lineage_manifest.json").read_text(encoding="utf-8"))
    packaged = json.loads((skill / "references" / "course_package.json").read_text(encoding="utf-8"))

    assert manifest["source_artifacts_included"] is False
    assert manifest["source_dir"] == "<withheld-local-path>"
    assert not (skill / "references" / "transcripts").exists()
    assert "PRIVATE TRANSCRIPT BODY" not in (skill / "references" / "full_transcript.md").read_text(encoding="utf-8")
    assert all(item["path"].startswith("withheld://") for item in packaged["sources"] + packaged["evidence"])
    for path in skill.rglob("*"):
        if path.is_file():
            assert str(tmp_path) not in path.read_text(encoding="utf-8", errors="ignore")
