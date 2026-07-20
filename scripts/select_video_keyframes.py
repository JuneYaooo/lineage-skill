#!/usr/bin/env python3
"""Model-selected keyframes from dense video candidate frames.

This stage is intentionally separate from fixed-interval visual analysis:
fixed intervals create only a candidate pool; a vision model selects the final
keyframes from labeled contact sheets. All outputs are resumable by manifest.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw

from llm_client import analyze_images_with_vision_model


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BASE_DIR = ROOT / ".lineage" / "courses"
FFMPEG = os.getenv("FFMPEG") or shutil.which("ffmpeg") or "ffmpeg"
FFPROBE = os.getenv("FFPROBE") or shutil.which("ffprobe") or "ffprobe"

VIDEO_SUFFIXES = {".mp4", ".mov", ".mkv", ".webm"}

PROMPT = """This contact sheet contains candidate frames from a course video.
Each tile label includes the frame filename and approximate timestamp.

Select only the frames worth preserving as evidence for later course distillation.

Selection criteria:
1. Slide, board, document, UI, diagram, table, formula, demo, or visual state changes materially.
2. The frame captures a complete or clearer teaching artifact than nearby frames.
3. It is useful for source-backed explanation, review, or verification.
4. Drop lecturer-only, blank, blurred, blocked, duplicate, intro/outro, and low-information frames.

Return JSON only:
{
  "selected": [
    {"frame": "frame_0001.jpg", "timestamp": "00:00", "reason": "why this is a keyframe", "keywords": ["keyword"]}
  ],
  "dropped_summary": "brief summary of why other frames were dropped"
}

Select at most 8 frames per contact sheet. If none are valuable, return an empty selected array."""


def media_name(path: Path, input_dir: Path) -> str:
    rel = path.relative_to(input_dir)
    if len(rel.parts) == 1:
        return path.stem
    return "_".join([*rel.parts[:-1], path.stem])


def frame_count(path: Path) -> int:
    return len(list(path.glob("*.jpg"))) if path.is_dir() else 0


def parse_fps(value: str, default: float = 25.0) -> float:
    value = (value or "").strip()
    try:
        if "/" in value:
            numerator, denominator = value.split("/", 1)
            den = float(denominator)
            return float(numerator) / den if den else default
        return float(value)
    except (TypeError, ValueError, ZeroDivisionError):
        return default


def video_fps(video: Path) -> float:
    command = [
        FFPROBE,
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=avg_frame_rate",
        "-of",
        "default=nw=1:nk=1",
        str(video),
    ]
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
    except (OSError, subprocess.CalledProcessError):
        return 25.0
    return parse_fps(result.stdout, 25.0)


def build_extract_command(
    video: Path,
    output_pattern: Path,
    *,
    mode: str,
    fps: float,
    interval_seconds: int,
    width: int,
    scene_threshold: float,
) -> list[str]:
    if mode == "scene":
        every_n = max(1, round(fps * interval_seconds))
        vf = f"select='gt(scene,{scene_threshold})+not(mod(n,{every_n}))',showinfo,scale={width}:-1"
        return [
            FFMPEG,
            "-hide_banner",
            "-loglevel",
            "info",
            "-i",
            str(video),
            "-vf",
            vf,
            "-vsync",
            "vfr",
            "-q:v",
            "3",
            str(output_pattern),
        ]
    return [
        FFMPEG,
        "-hide_banner",
        "-loglevel",
        "error",
        "-i",
        str(video),
        "-vf",
        f"fps=1/{interval_seconds},scale={width}:-1",
        "-q:v",
        "3",
        str(output_pattern),
    ]


def map_showinfo_timestamps(frames: list[Path], stderr: str) -> dict[str, float]:
    values = [float(match.group(1)) for match in re.finditer(r"pts_time:([0-9.]+)", stderr or "")]
    return {frame.name: values[index] for index, frame in enumerate(frames) if index < len(values)}


def fixed_interval_timestamps(frames: list[Path], interval_seconds: int) -> dict[str, float]:
    return {frame.name: float(index * interval_seconds) for index, frame in enumerate(frames)}


def write_timestamp_map(output_dir: Path, timestamp_map: dict[str, float]) -> None:
    (output_dir / "frame_timestamps.json").write_text(
        json.dumps(timestamp_map, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def read_timestamp_map(output_dir: Path, interval_seconds: int) -> dict[str, float]:
    path = output_dir / "frame_timestamps.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return fixed_interval_timestamps(sorted(output_dir.glob("*.jpg")), interval_seconds)


def timestamp_for_frame(path: Path, interval_seconds: int, timestamp_map: dict[str, float] | None = None) -> str:
    if timestamp_map and path.name in timestamp_map:
        seconds = int(round(float(timestamp_map[path.name])))
        return f"{seconds // 60:02d}:{seconds % 60:02d}"
    match = re.search(r"frame_(\d+)\.jpg$", path.name)
    index = int(match.group(1)) - 1 if match else 0
    seconds = index * interval_seconds
    return f"{seconds // 60:02d}:{seconds % 60:02d}"


def _image_signature(path: Path, size: int = 16) -> list[tuple[int, int, int]]:
    with Image.open(path) as image:
        return list(image.convert("RGB").resize((size, size), Image.Resampling.BILINEAR).getdata())


def _pct_diff(a: list[tuple[int, int, int]], b: list[tuple[int, int, int]], tolerance: int = 25) -> float:
    changed = sum(
        max(abs(left[0] - right[0]), abs(left[1] - right[1]), abs(left[2] - right[2])) > tolerance
        for left, right in zip(a, b)
    )
    return 100.0 * changed / len(a)


def deduplicate_candidates(
    output_dir: Path,
    timestamp_map: dict[str, float],
    *,
    threshold: float,
    window: int,
    max_candidates: int,
) -> dict[str, Any]:
    frames = sorted(output_dir.glob("*.jpg"))
    raw_count = len(frames)
    kept: list[Path] = []
    recent: list[list[tuple[int, int, int]]] = []
    records: list[dict[str, Any]] = []

    for frame in frames:
        signature = _image_signature(frame)
        distance = min((_pct_diff(signature, item) for item in recent), default=None)
        if distance is None or distance > threshold:
            kept.append(frame)
            recent.append(signature)
            if len(recent) > max(1, window):
                recent.pop(0)
            records.append({"name": frame.name, "distance": distance, "kept": True})
        else:
            frame.unlink()
            records.append({"name": frame.name, "distance": distance, "kept": False})

    if max_candidates > 0 and len(kept) > max_candidates:
        step = len(kept) / max_candidates
        keep_indexes = {int(index * step) for index in range(max_candidates)}
        capped = []
        for index, frame in enumerate(kept):
            if index in keep_indexes:
                capped.append(frame)
            else:
                if frame.exists():
                    frame.unlink()
                for record in records:
                    if record["name"] == frame.name:
                        record["kept"] = False
                        record["capped"] = True
        kept = capped

    new_timestamp_map: dict[str, float] = {}
    rename_pairs: list[tuple[Path, Path, str]] = []
    for index, frame in enumerate(kept, 1):
        final_name = f"frame_{index:04d}.jpg"
        tmp = output_dir / f"tmp_{index:04d}.jpg"
        frame.rename(tmp)
        rename_pairs.append((tmp, output_dir / final_name, frame.name))

    for tmp, final, original_name in rename_pairs:
        tmp.rename(final)
        new_timestamp_map[final.name] = float(timestamp_map.get(original_name, 0.0))
        for record in records:
            if record["name"] == original_name and record.get("kept"):
                record["name"] = final.name

    write_timestamp_map(output_dir, new_timestamp_map)
    return {
        "raw_candidate_count": raw_count,
        "candidate_count": len(kept),
        "timestamp_map": new_timestamp_map,
        "dedup_records": records,
    }


def extract_candidates(
    video: Path,
    output_dir: Path,
    interval_seconds: int,
    width: int,
    force: bool,
    *,
    mode: str = "scene",
    scene_threshold: float = 0.3,
    dedup_threshold: float = 8.0,
    dedup_window: int = 4,
    max_candidates: int = 300,
) -> dict[str, Any]:
    existing = frame_count(output_dir)
    if existing and not force:
        timestamp_map = read_timestamp_map(output_dir, interval_seconds)
        return {
            "raw_candidate_count": existing,
            "candidate_count": existing,
            "timestamp_map": timestamp_map,
            "dedup_records": [],
        }
    output_dir.mkdir(parents=True, exist_ok=True)
    if force:
        for old in output_dir.glob("*.jpg"):
            old.unlink()
        timestamp_file = output_dir / "frame_timestamps.json"
        if timestamp_file.exists():
            timestamp_file.unlink()

    fps = video_fps(video)
    command = build_extract_command(
        video,
        output_dir / "frame_%04d.jpg",
        mode=mode,
        fps=fps,
        interval_seconds=interval_seconds,
        width=width,
        scene_threshold=scene_threshold,
    )
    result = subprocess.run(command, check=True, capture_output=True, text=True)
    frames = sorted(output_dir.glob("*.jpg"))
    if mode == "scene":
        timestamp_map = map_showinfo_timestamps(frames, result.stderr)
        if len(timestamp_map) != len(frames):
            timestamp_map = fixed_interval_timestamps(frames, interval_seconds)
    else:
        timestamp_map = fixed_interval_timestamps(frames, interval_seconds)
    write_timestamp_map(output_dir, timestamp_map)
    return deduplicate_candidates(
        output_dir,
        timestamp_map,
        threshold=dedup_threshold,
        window=dedup_window,
        max_candidates=max_candidates,
    )


def make_sheet(
    frames: list[Path],
    output: Path,
    interval_seconds: int,
    columns: int,
    thumb_width: int,
    timestamp_map: dict[str, float] | None = None,
) -> None:
    thumbs = []
    label_height = 26
    for frame in frames:
        with Image.open(frame) as image:
            img = image.convert("RGB")
            ratio = thumb_width / img.width
            thumb_height = int(img.height * ratio)
            thumb = img.resize((thumb_width, thumb_height), Image.Resampling.LANCZOS)
        canvas = Image.new("RGB", (thumb_width, thumb.height + label_height), "white")
        canvas.paste(thumb, (0, label_height))
        draw = ImageDraw.Draw(canvas)
        draw.text((4, 6), f"{frame.name} {timestamp_for_frame(frame, interval_seconds, timestamp_map)}", fill=(0, 0, 0))
        thumbs.append(canvas)

    rows = (len(thumbs) + columns - 1) // columns
    cell_height = max(thumb.height for thumb in thumbs)
    sheet = Image.new("RGB", (columns * thumb_width, rows * cell_height), "white")
    for index, thumb in enumerate(thumbs):
        x = (index % columns) * thumb_width
        y = (index // columns) * cell_height
        sheet.paste(thumb, (x, y))
    output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output, quality=88)


def parse_json_response(text: str) -> dict[str, Any]:
    match = re.search(r"\{[\s\S]*\}", text or "")
    if not match:
        return {"selected": [], "dropped_summary": "model returned non-json content", "raw": text}
    try:
        data = json.loads(match.group(0))
    except json.JSONDecodeError:
        return {"selected": [], "dropped_summary": "model returned invalid json", "raw": text}
    if not isinstance(data.get("selected"), list):
        data["selected"] = []
    return data


def select_video(
    video: Path,
    input_dir: Path,
    course_dir: Path,
    *,
    interval_seconds: int,
    width: int,
    candidate_mode: str,
    scene_threshold: float,
    dedup_threshold: float,
    dedup_window: int,
    max_candidates: int,
    frames_per_sheet: int,
    columns: int,
    thumb_width: int,
    force: bool,
) -> dict[str, Any]:
    name = media_name(video, input_dir)
    candidates_root = course_dir / "keyframe_candidates"
    selected_root = course_dir / "keyframes_model_selected"
    selection_root = course_dir / "keyframe_selection"
    sheet_root = selection_root / "sheets"

    candidate_dir = candidates_root / name
    selected_dir = selected_root / name
    manifest_path = selection_root / f"{name}_model_keyframes_manifest.json"

    if manifest_path.exists() and not force:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        print(f"skip {name}: selected {manifest.get('selected_count', 0)} keyframes")
        return manifest

    candidate_stats = extract_candidates(
        video,
        candidate_dir,
        interval_seconds,
        width,
        force,
        mode=candidate_mode,
        scene_threshold=scene_threshold,
        dedup_threshold=dedup_threshold,
        dedup_window=dedup_window,
        max_candidates=max_candidates,
    )
    count = int(candidate_stats["candidate_count"])
    timestamp_map = candidate_stats["timestamp_map"]
    frames = sorted(candidate_dir.glob("*.jpg"))
    selected_dir.mkdir(parents=True, exist_ok=True)
    if force:
        for old in selected_dir.glob("*.jpg"):
            old.unlink()

    selected_by_name: dict[str, dict[str, Any]] = {}
    sheet_results = []
    for start in range(0, len(frames), frames_per_sheet):
        chunk = frames[start : start + frames_per_sheet]
        sheet_index = start // frames_per_sheet + 1
        sheet = sheet_root / name / f"{name}_sheet_{sheet_index:02d}.jpg"
        result_path = selection_root / name / f"{name}_sheet_{sheet_index:02d}_selection.json"
        if result_path.exists() and not force:
            data = json.loads(result_path.read_text(encoding="utf-8"))
        else:
            make_sheet(chunk, sheet, interval_seconds, columns, thumb_width, timestamp_map)
            print(f"select {name} sheet {sheet_index}: {len(chunk)} candidates", flush=True)
            result = analyze_images_with_vision_model([str(sheet)], PROMPT)
            data = parse_json_response(result.get("content") or "")
            data.update(
                {
                    "sheet": str(sheet.relative_to(course_dir)),
                    "success": result.get("success", False),
                    "error": result.get("error"),
                }
            )
            result_path.parent.mkdir(parents=True, exist_ok=True)
            result_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

        valid_names = {path.name for path in chunk}
        for item in data.get("selected") or []:
            frame_name = item.get("frame")
            if frame_name in valid_names:
                selected_by_name[frame_name] = {
                    "frame": frame_name,
                    "timestamp": timestamp_for_frame(candidate_dir / frame_name, interval_seconds, timestamp_map),
                    "reason": item.get("reason", ""),
                    "keywords": item.get("keywords") or [],
                    "candidate_source": str((candidate_dir / frame_name).relative_to(course_dir)),
                }
        sheet_results.append(data)

    selected = []
    for frame_name, item in sorted(selected_by_name.items()):
        src = candidate_dir / frame_name
        dst = selected_dir / frame_name
        if force or not dst.exists():
            shutil.copy2(src, dst)
        item["selected_path"] = str(dst.relative_to(course_dir))
        selected.append(item)

    manifest = {
        "media": name,
        "video_path": str(video),
        "candidate_extraction_mode": candidate_mode,
        "candidate_interval_seconds": interval_seconds,
        "candidate_width": width,
        "scene_threshold": scene_threshold if candidate_mode == "scene" else None,
        "dedup_threshold": dedup_threshold,
        "dedup_window": dedup_window,
        "max_candidates": max_candidates,
        "raw_candidate_count": candidate_stats["raw_candidate_count"],
        "candidate_count": count,
        "candidate_dir": str(candidate_dir.relative_to(course_dir)),
        "selected_count": len(selected),
        "selected_dir": str(selected_dir.relative_to(course_dir)),
        "selected": selected,
        "sheets": sheet_results,
        "dedup_records": candidate_stats["dedup_records"],
    }
    selection_root.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{name}: selected {len(selected)}/{count}")
    return manifest


def write_summary(course_dir: Path, manifests: list[dict[str, Any]]) -> None:
    out = course_dir / "keyframe_selection"
    total_candidates = sum(item.get("candidate_count", 0) for item in manifests)
    total_selected = sum(item.get("selected_count", 0) for item in manifests)
    lines = [
        "# Model-Selected Keyframe Summary",
        "",
        "## Method",
        "- Dense candidate frames are extracted as a candidate pool, using scene-change detection plus a density floor by default.",
        "- Near-duplicate candidate frames are removed before contact-sheet review.",
        "- A vision model reviews labeled contact sheets and selects the final keyframes.",
        "- Selection favors meaningful teaching visuals and drops duplicate, blank, blurred, blocked, or lecturer-only frames.",
        "",
        "## Totals",
        f"- Candidate frames: {total_candidates}",
        f"- Model-selected keyframes: {total_selected}",
        "",
        "## Media",
    ]
    for manifest in manifests:
        lines.append(f"### {manifest['media']}")
        if manifest.get("candidate_extraction_mode"):
            lines.append(f"- Candidate mode: {manifest['candidate_extraction_mode']}")
        if manifest.get("raw_candidate_count") is not None:
            lines.append(f"- Raw candidates before dedup/cap: {manifest['raw_candidate_count']}")
        lines.append(f"- Candidates: {manifest['candidate_count']}")
        lines.append(f"- Selected: {manifest['selected_count']}")
        lines.append(f"- Selected dir: `{manifest['selected_dir']}`")
        for item in manifest.get("selected") or []:
            keywords = ", ".join(item.get("keywords") or [])
            lines.append(f"- {item['timestamp']} `{item['selected_path']}` {keywords} {item.get('reason', '')}".rstrip())
        lines.append("")
    out.mkdir(parents=True, exist_ok=True)
    (out / "model_keyframe_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    index = [
        {
            "media": item["media"],
            "candidate_extraction_mode": item.get("candidate_extraction_mode"),
            "raw_candidate_count": item.get("raw_candidate_count"),
            "candidate_count": item["candidate_count"],
            "selected_count": item["selected_count"],
            "selected_dir": item["selected_dir"],
        }
        for item in manifests
    ]
    (out / "model_keyframe_index.json").write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Select keyframes from course videos with a vision model.")
    parser.add_argument("--input-dir", required=True)
    parser.add_argument("--course-name", required=True)
    parser.add_argument("--base-dir", default=str(DEFAULT_BASE_DIR))
    parser.add_argument("--interval-seconds", type=int, default=60)
    parser.add_argument("--width", type=int, default=768)
    parser.add_argument("--candidate-mode", choices=["scene", "fixed"], default="scene")
    parser.add_argument("--scene-threshold", type=float, default=0.3)
    parser.add_argument("--dedup-threshold", type=float, default=8.0)
    parser.add_argument("--dedup-window", type=int, default=4)
    parser.add_argument("--max-candidates", type=int, default=300, help="Cap deduplicated candidate frames per video; use 0 for no cap.")
    parser.add_argument("--frames-per-sheet", type=int, default=48)
    parser.add_argument("--columns", type=int, default=6)
    parser.add_argument("--thumb-width", type=int, default=300)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args()

    input_dir = Path(args.input_dir).expanduser().resolve()
    course_dir = Path(args.base_dir).expanduser().resolve() / args.course_name
    videos = sorted(path for path in input_dir.rglob("*") if path.is_file() and path.suffix.lower() in VIDEO_SUFFIXES)
    if args.limit > 0:
        videos = videos[: args.limit]

    course_dir.mkdir(parents=True, exist_ok=True)
    if not videos:
        print("no video files found; keyframe selection skipped")
        write_summary(course_dir, [])
        return

    manifests = []
    for video in videos:
        manifests.append(
            select_video(
                video,
                input_dir,
                course_dir,
                interval_seconds=args.interval_seconds,
                width=args.width,
                candidate_mode=args.candidate_mode,
                scene_threshold=args.scene_threshold,
                dedup_threshold=args.dedup_threshold,
                dedup_window=args.dedup_window,
                max_candidates=args.max_candidates,
                frames_per_sheet=args.frames_per_sheet,
                columns=args.columns,
                thumb_width=args.thumb_width,
                force=args.force,
            )
        )
    write_summary(course_dir, manifests)


if __name__ == "__main__":
    main()
