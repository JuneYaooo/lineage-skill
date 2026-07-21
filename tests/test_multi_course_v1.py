from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from build_multi_course_package import merge_packages
from migrate_course_package import migrate_package


ROOT = Path(__file__).resolve().parents[1]


def legacy_with_method(course_name: str, summary: str) -> dict:
    raw = json.loads((ROOT / "tests" / "fixtures" / "course-package-0.1" / "course_package.json").read_text(encoding="utf-8"))
    raw["manifest"]["course_name"] = course_name
    raw["manifest"]["course_id"] = f"legacy-{course_name}"
    raw["methods"][0] = {"id": f"legacy-method-{course_name}", "title": "Shared decision rule", "summary": summary}
    return raw


def test_multi_course_merge_preserves_conflicting_teacher_methods(tmp_path: Path) -> None:
    first, _ = migrate_package(legacy_with_method("course-a", "Choose speed first."))
    second, _ = migrate_package(legacy_with_method("course-b", "Choose safety first."))

    merged = merge_packages([(tmp_path / "a.json", first), (tmp_path / "b.json", second)], "combined")
    matching = [item for item in merged["methods"] if item["title"] == "Shared decision rule"]

    assert {item["summary"] for item in matching} == {"Choose speed first.", "Choose safety first."}
    assert len({item["id"] for item in matching}) == 2
    assert merged["manifest"]["conflicts"][0]["status"] == "unresolved"
    assert merged["quality"]["integrity"]["source_conflict_count"] == 1
