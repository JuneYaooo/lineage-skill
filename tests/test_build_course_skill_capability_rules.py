from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_generated_skill_includes_capability_rules_and_evidence_fetcher(tmp_path: Path) -> None:
    course_dir = tmp_path / "course"
    course_dir.mkdir()
    package = {
        "schema_version": "0.2",
        "manifest": {"course_name": "Demo Book", "source_dir": str(course_dir)},
        "lessons": [],
        "concepts": ["核心概念"],
        "topics": [],
        "cases": [],
        "methods": ["核心方法"],
        "diagnostics": ["诊断规则"],
        "workflows": ["执行流程"],
        "rubrics": ["质量标准"],
        "templates": ["输出模板"],
        "transfer_rules": ["迁移规则"],
        "failure_modes": ["失效条件"],
        "learning_checks": [],
        "quotes": [],
        "evidence": [],
        "study_paths": [],
        "boundaries": [],
    }
    (course_dir / "course_package.json").write_text(json.dumps(package, ensure_ascii=False), encoding="utf-8")

    output_dir = tmp_path / "dist"
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "build_course_skill.py"),
            "--course-name",
            "Demo Book",
            "--skill-name",
            "demo-book-lineage",
            "--mode",
            "expert,practitioner",
            "--source-dir",
            str(course_dir),
            "--output-dir",
            str(output_dir),
        ],
        check=True,
        cwd=ROOT,
    )

    skill_dir = output_dir / "demo-book-lineage"
    skill_md = (skill_dir / "SKILL.md").read_text(encoding="utf-8")

    assert "Capability Reading Strategy" in skill_md
    assert "diagnostics" in skill_md
    assert "workflows" in skill_md
    assert "rubrics" in skill_md
    assert "fetch_course_evidence.py" in skill_md
    assert (skill_dir / "scripts" / "fetch_course_evidence.py").exists()
    assert (skill_dir / "scripts" / "search_course_notes.py").exists()


def test_generated_skill_includes_okf_bundle_for_progressive_reading(tmp_path: Path) -> None:
    course_dir = tmp_path / "course"
    course_dir.mkdir()
    package = {
        "schema_version": "0.2",
        "manifest": {"course_name": "Demo Book", "source_dir": str(course_dir)},
        "concepts": ["证据优先：先保留来源再综合。"],
        "workflows": ["三步执行：界定目标、拆出动作、按结果复盘。"],
        "methods": [],
        "lessons": [],
        "topics": [],
        "cases": [],
        "diagnostics": [],
        "rubrics": [],
        "templates": [],
        "transfer_rules": [],
        "failure_modes": [],
        "learning_checks": [],
        "quotes": [],
        "evidence": [],
        "study_paths": [],
        "boundaries": [],
    }
    (course_dir / "course_package.json").write_text(json.dumps(package, ensure_ascii=False), encoding="utf-8")

    output_dir = tmp_path / "dist"
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "build_course_skill.py"),
            "--course-name",
            "Demo Book",
            "--skill-name",
            "demo-book-lineage",
            "--mode",
            "expert",
            "--source-dir",
            str(course_dir),
            "--output-dir",
            str(output_dir),
        ],
        check=True,
        cwd=ROOT,
    )

    skill_dir = output_dir / "demo-book-lineage"
    skill_md = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
    okf_index = skill_dir / "references" / "okf" / "index.md"

    assert okf_index.exists()
    assert "references/okf/index.md" in skill_md
    assert "OKF" in okf_index.read_text(encoding="utf-8")
