from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from migrate_course_package import migrate_package
from validate_lineage_package import validate_package


ROOT = Path(__file__).resolve().parents[1]


def test_migrate_legacy_package_to_valid_v1(tmp_path: Path) -> None:
    source = ROOT / "tests" / "fixtures" / "course-package-0.1" / "course_package.json"
    migrated, report = migrate_package(json.loads(source.read_text(encoding="utf-8")), source_path=source)
    output = tmp_path / "course_package.json"
    output.write_text(json.dumps(migrated, ensure_ascii=False), encoding="utf-8")

    assert migrated["schema_version"] == "1.0"
    assert migrated["manifest"]["migrated_from"] == "0.1"
    assert migrated["concepts"][0]["legacy_text"].startswith("Evidence first")
    assert migrated["concepts"][0]["id"].startswith("concept_")
    assert report["legacy_text_count"] >= 1
    assert report["id_map"]
    assert report["unmapped_legacy_id_count"] == 0
    assert validate_package(output)["valid"] is True


def test_repeated_migration_keeps_stable_ids() -> None:
    source = ROOT / "tests" / "fixtures" / "course-package-0.1" / "course_package.json"
    raw = json.loads(source.read_text(encoding="utf-8"))
    first, _ = migrate_package(raw, source_path=source)
    second, _ = migrate_package(raw, source_path=source)

    assert [item["id"] for item in first["concepts"]] == [item["id"] for item in second["concepts"]]
    assert [item["id"] for item in first["evidence"]] == [item["id"] for item in second["evidence"]]
