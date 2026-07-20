#!/usr/bin/env python3
"""Rebuild derived MasteryState from append-only PracticeEpisodes."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from runtime_state import read_json, read_jsonl, rebuild_mastery, write_json


def main() -> None:
    parser = argparse.ArgumentParser(description="Rebuild mastery_state.json from practice_episodes.jsonl.")
    parser.add_argument("--state-dir", required=True)
    args = parser.parse_args()
    state_dir = Path(args.state_dir).expanduser().resolve()
    state = read_json(state_dir / "apprenticeship_state.json", {})
    mastery = rebuild_mastery(
        read_jsonl(state_dir / "practice_episodes.jsonl"),
        mentor_package_id=state["mentor_package_id"],
        learner_id=state["learner_id"],
    )
    write_json(state_dir / "mastery_state.json", mastery)
    print(json.dumps({"output": str(state_dir / "mastery_state.json"), "capability_count": len(mastery["capabilities"])}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
