#!/usr/bin/env python3
"""Schedule configurable short, medium, and long retrieval reviews."""

from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path

from runtime_state import read_json, write_json


def parse_time(value: str | None) -> dt.datetime:
    if not value:
        return dt.datetime.now(dt.timezone.utc)
    parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=dt.timezone.utc)


def schedule(capability_id: str, *, base_time: dt.datetime, intervals: list[int], last_result: str, high_confidence_error: bool) -> list[dict]:
    adjusted = [max(1, value // 2) for value in intervals] if last_result != "pass" or high_confidence_error else intervals
    forms = ["free_reconstruction", "parallel_case", "changed_context", "long_delay_boundary_check"]
    return [
        {
            "review_id": f"review-{capability_id}-{index + 1}",
            "capability_id": capability_id,
            "due_at": (base_time + dt.timedelta(days=days)).isoformat(timespec="seconds"),
            "retrieval_form": forms[min(index, len(forms) - 1)],
            "last_result": last_result,
            "priority": "high" if high_confidence_error else "normal",
            "status": "due" if days <= 0 else "scheduled",
            "scheduler_version": "lineage-spacing-1.0",
        }
        for index, days in enumerate(adjusted)
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description="Add retrieval items to review_queue.json.")
    parser.add_argument("--state-dir", required=True)
    parser.add_argument("--capability-id", required=True)
    parser.add_argument("--last-result", choices=["pass", "revise", "fail", "insufficient_evidence"], default="pass")
    parser.add_argument("--high-confidence-error", action="store_true")
    parser.add_argument("--interval-days", default="1,7,30,90")
    parser.add_argument("--base-time")
    args = parser.parse_args()
    state_dir = Path(args.state_dir).expanduser().resolve()
    queue = read_json(state_dir / "review_queue.json", {"schema_version": "1.0", "items": []})
    intervals = [int(value) for value in args.interval_days.split(",") if value.strip()]
    new_items = schedule(args.capability_id, base_time=parse_time(args.base_time), intervals=intervals, last_result=args.last_result, high_confidence_error=args.high_confidence_error)
    existing = {item["review_id"]: item for item in queue.get("items", [])}
    existing.update({item["review_id"]: item for item in new_items})
    queue["items"] = sorted(existing.values(), key=lambda item: (item["due_at"], item["review_id"]))
    queue["scheduler"] = {"version": "lineage-spacing-1.0", "interval_days": intervals}
    write_json(state_dir / "review_queue.json", queue)
    print(json.dumps({"scheduled": len(new_items), "queue": str(state_dir / "review_queue.json")}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
