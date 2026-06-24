from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from build_multi_course_package import merge_packages


def test_merge_packages_preserves_capability_fields(tmp_path: Path) -> None:
    source_a = tmp_path / "a"
    source_b = tmp_path / "b"
    source_a.mkdir()
    source_b.mkdir()
    package_a = {
        "manifest": {"course_name": "Course A", "source_dir": str(source_a)},
        "diagnostics": ["诊断 A"],
        "workflows": ["流程 A"],
        "rubrics": ["标准 A"],
        "templates": ["模板 A"],
        "transfer_rules": ["迁移 A"],
        "failure_modes": ["误用 A"],
    }
    package_b = {
        "manifest": {"course_name": "Course B", "source_dir": str(source_b)},
        "diagnostics": ["诊断 B"],
    }

    merged = merge_packages([(source_a / "course_package.json", package_a), (source_b / "course_package.json", package_b)], "Combined")

    assert len(merged["diagnostics"]) == 2
    assert merged["diagnostics"][0]["source_course"] == "Course A"
    assert merged["diagnostics"][1]["source_course"] == "Course B"
    assert merged["workflows"][0]["value"] == "流程 A"
    assert merged["rubrics"][0]["value"] == "标准 A"
    assert merged["templates"][0]["value"] == "模板 A"
    assert merged["transfer_rules"][0]["value"] == "迁移 A"
    assert merged["failure_modes"][0]["value"] == "误用 A"
