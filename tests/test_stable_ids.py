from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from stable_ids import canonical_json, content_hash, stable_id


def test_stable_ids_are_deterministic_and_namespace_safe() -> None:
    first = stable_id("capability", "course-a", "诊断", {"b": 2, "a": 1})
    second = stable_id("capability", "course-a", "诊断", {"a": 1, "b": 2})
    other = stable_id("capability", "course-b", "诊断", {"a": 1, "b": 2})

    assert first == second
    assert first.startswith("cap_")
    assert first != other
    assert canonical_json({"b": 2, "a": 1}) == '{"a":1,"b":2}'
    assert len(content_hash("same")) == 64
