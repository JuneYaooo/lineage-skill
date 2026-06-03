#!/usr/bin/env python3
"""Run the full Lineage Skill course pipeline.

Stages:
1. transcribe videos
2. analyze video frames and screenshots
3. distill course notes
4. package the result as a Codex skill
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from build_course_skill import default_skill_name, parse_modes
from progress import write_progress


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BASE_DIR = ROOT / ".lineage" / "courses"
DEFAULT_OUTPUT_DIR = ROOT / "dist"


def run(
    cmd: list[str],
    skip: bool,
    *,
    stage: str,
    args: argparse.Namespace,
    base_dir: Path,
    output_dir: Path,
    course_dir: Path,
) -> None:
    if skip:
        print(f"skip: {' '.join(cmd)}")
        write_progress(
            course_dir,
            course_name=args.course_name,
            skill_name=args.skill_name,
            base_dir=base_dir,
            output_dir=output_dir,
            mode=args.mode,
            scope=args.scope,
            evidence=args.evidence,
            progress_strategy=args.progress,
            input_dir=args.input_dir,
            documents_input=args.documents_input or [],
            stage=stage,
            status="skipped",
            command=cmd,
        )
        return
    print(f"\n==> {' '.join(cmd)}", flush=True)
    write_progress(
        course_dir,
        course_name=args.course_name,
        skill_name=args.skill_name,
        base_dir=base_dir,
        output_dir=output_dir,
        mode=args.mode,
        scope=args.scope,
        evidence=args.evidence,
        progress_strategy=args.progress,
        input_dir=args.input_dir,
        documents_input=args.documents_input or [],
        stage=stage,
        status="running",
        command=cmd,
    )
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as exc:
        write_progress(
            course_dir,
            course_name=args.course_name,
            skill_name=args.skill_name,
            base_dir=base_dir,
            output_dir=output_dir,
            mode=args.mode,
            scope=args.scope,
            evidence=args.evidence,
            progress_strategy=args.progress,
            input_dir=args.input_dir,
            documents_input=args.documents_input or [],
            stage=stage,
            status="failed",
            command=cmd,
            error=f"exit code {exc.returncode}",
        )
        raise
    write_progress(
        course_dir,
        course_name=args.course_name,
        skill_name=args.skill_name,
        base_dir=base_dir,
        output_dir=output_dir,
        mode=args.mode,
        scope=args.scope,
        evidence=args.evidence,
        progress_strategy=args.progress,
        input_dir=args.input_dir,
        documents_input=args.documents_input or [],
        stage=stage,
        status="completed",
        command=cmd,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Run transcription, visual analysis, distillation, and skill packaging.")
    parser.add_argument("--input-dir", required=True, help="Directory containing course .mp4 files.")
    parser.add_argument("--documents-input", action="append", help="Optional PDF file or directory for MinerU OCR. Repeatable.")
    parser.add_argument("--course-name", required=True, help="Course output directory name.")
    parser.add_argument("--skill-name", help="Generated skill name. Defaults to <course-slug>-<role>-lineage.")
    parser.add_argument("--mode", default="mentor", help="Skill role or comma-separated roles passed to build_course_skill.py.")
    parser.add_argument("--scope", default="auto", help="Course scope metadata passed to build_course_skill.py.")
    parser.add_argument("--evidence", default="standard", help="Evidence strategy metadata passed to build_course_skill.py.")
    parser.add_argument("--progress", default="auto", help="Progress strategy metadata passed to build_course_skill.py.")
    parser.add_argument("--base-dir", default=str(DEFAULT_BASE_DIR), help="Course workspace root. Defaults to ./.lineage/courses.")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="Generated skill output directory. Defaults to ./dist.")
    parser.add_argument("--chunk-minutes", type=int, default=12, help="Video analysis chunk size.")
    parser.add_argument("--force", action="store_true", help="Re-run stages that support overwrite.")
    parser.add_argument("--skip-transcribe", action="store_true")
    parser.add_argument("--skip-analyze", action="store_true")
    parser.add_argument("--skip-documents", action="store_true")
    parser.add_argument("--skip-distill", action="store_true")
    parser.add_argument("--skip-package", action="store_true")
    parser.add_argument("--skip-build-skill", action="store_true")
    parser.add_argument("--limit", type=int, default=0, help="Limit video count for transcribe/analyze smoke runs.")
    args = parser.parse_args()

    py = sys.executable
    base_dir = Path(args.base_dir).expanduser().resolve()
    output_dir = Path(args.output_dir).expanduser().resolve()
    course_dir = base_dir / args.course_name
    args.skill_name = args.skill_name or default_skill_name(args.course_name, parse_modes(args.mode))
    force = ["--force"] if args.force else []
    limit = ["--limit", str(args.limit)] if args.limit > 0 else []

    write_progress(
        course_dir,
        course_name=args.course_name,
        skill_name=args.skill_name,
        base_dir=base_dir,
        output_dir=output_dir,
        mode=args.mode,
        scope=args.scope,
        evidence=args.evidence,
        progress_strategy=args.progress,
        input_dir=args.input_dir,
        documents_input=args.documents_input or [],
    )

    run(
        [
            py,
            str(ROOT / "scripts" / "transcribe_video.py"),
            "--input-dir",
            args.input_dir,
            "--course-name",
            args.course_name,
            "--base-dir",
            str(base_dir),
            *force,
            *limit,
        ],
        args.skip_transcribe,
        stage="transcribe",
        args=args,
        base_dir=base_dir,
        output_dir=output_dir,
        course_dir=course_dir,
    )
    run(
        [
            py,
            str(ROOT / "scripts" / "analyze_videos.py"),
            "--input-dir",
            args.input_dir,
            "--course-name",
            args.course_name,
            "--base-dir",
            str(base_dir),
            "--chunk-minutes",
            str(args.chunk_minutes),
            *force,
            *limit,
        ],
        args.skip_analyze,
        stage="analyze",
        args=args,
        base_dir=base_dir,
        output_dir=output_dir,
        course_dir=course_dir,
    )
    if args.documents_input:
        doc_cmd = [
            py,
            str(ROOT / "scripts" / "parse_mineru_documents.py"),
            "--course-name",
            args.course_name,
            "--base-dir",
            str(base_dir),
        ]
        for item in args.documents_input:
            doc_cmd.extend(["--input", item])
        run(
            doc_cmd,
            args.skip_documents,
            stage="documents",
            args=args,
            base_dir=base_dir,
            output_dir=output_dir,
            course_dir=course_dir,
        )
    else:
        write_progress(
            course_dir,
            course_name=args.course_name,
            skill_name=args.skill_name,
            base_dir=base_dir,
            output_dir=output_dir,
            mode=args.mode,
            scope=args.scope,
            evidence=args.evidence,
            progress_strategy=args.progress,
            input_dir=args.input_dir,
            documents_input=[],
            stage="documents",
            status="skipped",
            command=[],
        )
    run(
        [
            py,
            str(ROOT / "scripts" / "distill_course.py"),
            "--course-name",
            args.course_name,
            "--base-dir",
            str(base_dir),
        ],
        args.skip_distill,
        stage="distill",
        args=args,
        base_dir=base_dir,
        output_dir=output_dir,
        course_dir=course_dir,
    )
    run(
        [
            py,
            str(ROOT / "scripts" / "build_course_package.py"),
            "--course-name",
            args.course_name,
            "--source-dir",
            str(course_dir),
        ],
        args.skip_package,
        stage="package",
        args=args,
        base_dir=base_dir,
        output_dir=output_dir,
        course_dir=course_dir,
    )
    run(
        [
            py,
            str(ROOT / "scripts" / "build_course_skill.py"),
            "--course-name",
            args.course_name,
            "--skill-name",
            args.skill_name,
            "--mode",
            args.mode,
            "--scope",
            args.scope,
            "--evidence",
            args.evidence,
            "--progress",
            args.progress,
            "--source-dir",
            str(course_dir),
            "--output-dir",
            str(output_dir),
            "--description",
            "Generated by the Lineage Skill full course pipeline.",
            *force,
        ],
        args.skip_build_skill,
        stage="build_skill",
        args=args,
        base_dir=base_dir,
        output_dir=output_dir,
        course_dir=course_dir,
    )
    run(
        [
            py,
            str(ROOT / "scripts" / "build_course_catalog.py"),
            "--base-dir",
            str(base_dir),
            "--output-dir",
            str(output_dir),
        ],
        False,
        stage="catalog",
        args=args,
        base_dir=base_dir,
        output_dir=output_dir,
        course_dir=course_dir,
    )


if __name__ == "__main__":
    main()
