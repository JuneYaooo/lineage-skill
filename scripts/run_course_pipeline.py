#!/usr/bin/env python3
"""Run the full Lineage Skill course pipeline.

Stages:
1. transcribe videos
2. analyze video content and optional supplemental screenshot markers
3. select model-reviewed keyframes from dense candidates
4. distill course notes
5. compile teacher, capability, practice, assessment, and Mentor packages
6. package and validate the generated cognitive-apprenticeship Skill
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from build_course_skill import default_skill_name, parse_modes
from progress import write_progress


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BASE_DIR = ROOT / ".lineage" / "courses"
DEFAULT_OUTPUT_DIR = ROOT / "dist"


def build_text_distill_command(
    *,
    py: str,
    root: Path,
    args: argparse.Namespace,
    base_dir: Path,
) -> list[str]:
    cmd = [
        py,
        str(root / "scripts" / "distill_text_course.py"),
        "--course-name",
        args.course_name,
        "--base-dir",
        str(base_dir),
        "--max-chars",
        str(args.text_max_chars),
        "--overlap-chars",
        str(args.text_overlap_chars),
    ]
    for item in (args.text_input or []) + (args.notes_input or []):
        cmd.extend(["--input", item])
    if args.include_existing_documents or args.documents_input:
        cmd.append("--include-existing-documents")
    if args.text_no_llm:
        cmd.append("--no-llm")
    return cmd


def should_run_text_distill(args: argparse.Namespace) -> bool:
    return bool(args.text_input or args.notes_input or args.include_existing_documents or args.documents_input)


def should_run_media_capture(args: argparse.Namespace) -> bool:
    return bool(args.input_dir)


def resolve_audit_mode(args: argparse.Namespace) -> str:
    if args.audit_mode != "auto":
        return args.audit_mode
    if args.evidence == "strict":
        return "strict"
    return "auto"


def skip_stage(
    *,
    stage: str,
    args: argparse.Namespace,
    base_dir: Path,
    output_dir: Path,
    course_dir: Path,
) -> None:
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
        command=[],
    )


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


def readiness_summary(course_dir: Path, skill_dir: Path) -> dict[str, str]:
    """Return the three independent readiness conclusions promised by the CLI."""
    source = {}
    mentor = {}
    validation = {}
    for path, target in [
        (course_dir / "mentor_readiness_audit.json", source),
        (course_dir / "mentor_package.json", mentor),
        (skill_dir / "validation_report.json", validation),
    ]:
        if path.exists():
            try:
                target.update(json.loads(path.read_text(encoding="utf-8")))
            except (OSError, json.JSONDecodeError):
                pass
    runtime_status = (
        "ready"
        if validation.get("valid") is True
        else "blocked"
        if validation.get("valid") is False
        else mentor.get("quality", {}).get("runtime_readiness", "missing")
    )
    return {
        "source_readiness": source.get("source_readiness", {}).get("status", "missing"),
        "mentor_readiness": source.get("status", mentor.get("quality", {}).get("mentor_readiness", "missing")),
        "runtime_readiness": runtime_status,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run transcription, visual analysis, distillation, and skill packaging.")
    parser.add_argument("--input-dir", help="Directory containing course .mp4 video files and/or supported audio files.")
    parser.add_argument("--documents-input", action="append", help="Optional PDF file or directory for MinerU OCR. Repeatable.")
    parser.add_argument("--text-input", action="append", help="Optional Markdown/TXT file or directory for pure-text distillation. Repeatable.")
    parser.add_argument("--notes-input", action="append", help="Alias for additional notes directories/files. Repeatable.")
    parser.add_argument("--include-existing-documents", action="store_true", help="Include existing <course-dir>/documents text/OCR files in text distillation.")
    parser.add_argument("--course-name", required=True, help="Course output directory name.")
    parser.add_argument("--skill-name", help="Generated skill name. Defaults to <course-slug>-<role>-lineage.")
    parser.add_argument("--mode", default="mentor", help="Skill role or comma-separated roles passed to build_course_skill.py.")
    parser.add_argument("--scope", default="auto", help="Course scope metadata passed to build_course_skill.py.")
    parser.add_argument("--evidence", default="standard", help="Evidence strategy metadata passed to build_course_skill.py.")
    parser.add_argument("--progress", default="auto", help="Progress strategy metadata passed to build_course_skill.py.")
    parser.add_argument("--apprenticeship", choices=["none", "guided", "full"], default="full")
    parser.add_argument("--teacher-model", choices=["auto", "strict", "off"], default="auto")
    parser.add_argument("--practice-depth", choices=["standard", "deep"], default="standard")
    parser.add_argument("--learner-state", choices=["external", "none"], default="external")
    parser.add_argument("--include-source-artifacts", action="store_true", help="Opt in to packaging raw transcripts, OCR, analyses, and selected keyframes.")
    parser.add_argument("--mentor-audit-mode", choices=["auto", "strict"], default="auto")
    parser.add_argument("--base-dir", default=str(DEFAULT_BASE_DIR), help="Course workspace root. Defaults to ./.lineage/courses.")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="Generated skill output directory. Defaults to ./dist.")
    parser.add_argument("--chunk-minutes", type=int, default=12, help="Video analysis chunk size.")
    parser.add_argument("--keyframe-interval-seconds", type=int, default=60, help="Dense candidate interval for model-selected keyframes.")
    parser.add_argument("--keyframe-frames-per-sheet", type=int, default=48, help="Candidate frames per contact sheet.")
    parser.add_argument("--text-max-chars", type=int, default=6000, help="Text source chunk size for evidence-card distillation.")
    parser.add_argument("--text-overlap-chars", type=int, default=500, help="Text source chunk overlap for long paragraphs.")
    parser.add_argument("--text-no-llm", action="store_true", help="Use local deterministic text evidence extraction only.")
    parser.add_argument("--force", action="store_true", help="Re-run stages that support overwrite.")
    parser.add_argument("--skip-transcribe", action="store_true")
    parser.add_argument("--skip-analyze", action="store_true")
    parser.add_argument("--skip-keyframes", action="store_true")
    parser.add_argument("--skip-documents", action="store_true")
    parser.add_argument("--skip-text-distill", action="store_true")
    parser.add_argument("--skip-distill", action="store_true")
    parser.add_argument("--skip-summaries", action="store_true", help="Pass through to distill_course.py to reuse lesson_summaries.json.")
    parser.add_argument("--skip-package", action="store_true")
    parser.add_argument("--skip-audit", action="store_true")
    parser.add_argument("--skip-teacher-model", action="store_true")
    parser.add_argument("--skip-capability-graph", action="store_true")
    parser.add_argument("--skip-practice-bank", action="store_true")
    parser.add_argument("--skip-assessment-bank", action="store_true")
    parser.add_argument("--skip-mentor-package", action="store_true")
    parser.add_argument("--skip-mentor-audit", action="store_true")
    parser.add_argument(
        "--audit-mode",
        choices=["auto", "strict", "off"],
        default="auto",
        help="Audit cross-validation policy. auto validates only when comparable sources exist; strict requires missing-source review; off records inventory only. With --evidence strict, auto resolves to strict.",
    )
    parser.add_argument("--skip-build-skill", action="store_true")
    parser.add_argument("--skip-validate-skill", action="store_true")
    parser.add_argument("--limit", type=int, default=0, help="Limit media count for transcribe/analyze smoke runs.")
    args = parser.parse_args()

    if not args.input_dir and not should_run_text_distill(args):
        raise SystemExit("provide --input-dir for media courses, or --text-input/--notes-input/--documents-input for text courses")

    py = sys.executable
    base_dir = Path(args.base_dir).expanduser().resolve()
    output_dir = Path(args.output_dir).expanduser().resolve()
    course_dir = base_dir / args.course_name
    args.skill_name = args.skill_name or default_skill_name(args.course_name, parse_modes(args.mode))
    mentor_requested = "mentor" in parse_modes(args.mode) and args.apprenticeship != "none"
    if args.progress == "tracked":
        print("deprecation: --progress tracked now maps to --learner-state external; compiler progress remains in lineage_progress.json", flush=True)
        args.learner_state = "external"
    audit_mode = resolve_audit_mode(args)
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

    if should_run_media_capture(args):
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
        run(
            [
                py,
                str(ROOT / "scripts" / "select_video_keyframes.py"),
                "--input-dir",
                args.input_dir,
                "--course-name",
                args.course_name,
                "--base-dir",
                str(base_dir),
                "--interval-seconds",
                str(args.keyframe_interval_seconds),
                "--frames-per-sheet",
                str(args.keyframe_frames_per_sheet),
                *force,
                *limit,
            ],
            args.skip_keyframes,
            stage="keyframes",
            args=args,
            base_dir=base_dir,
            output_dir=output_dir,
            course_dir=course_dir,
        )
    else:
        for stage in ["transcribe", "analyze", "keyframes"]:
            skip_stage(stage=stage, args=args, base_dir=base_dir, output_dir=output_dir, course_dir=course_dir)
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
    if should_run_text_distill(args):
        run(
            build_text_distill_command(py=py, root=ROOT, args=args, base_dir=base_dir),
            args.skip_text_distill,
            stage="text_distill",
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
            documents_input=args.documents_input or [],
            stage="text_distill",
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
            *(["--skip-summaries"] if args.skip_summaries else []),
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
            str(ROOT / "scripts" / "build_distillation_audit.py"),
            "--course-name",
            args.course_name,
            "--source-dir",
            str(course_dir),
            "--audit-mode",
            audit_mode,
        ],
        args.skip_audit,
        stage="audit",
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
            str(ROOT / "scripts" / "build_teacher_model.py"),
            "--source-dir",
            str(course_dir),
            *(["--strict"] if args.teacher_model == "strict" else []),
        ],
        args.skip_teacher_model or not mentor_requested or args.teacher_model == "off",
        stage="teacher_model",
        args=args,
        base_dir=base_dir,
        output_dir=output_dir,
        course_dir=course_dir,
    )
    run(
        [py, str(ROOT / "scripts" / "build_capability_graph.py"), "--source-dir", str(course_dir)],
        args.skip_capability_graph or not mentor_requested,
        stage="capability_graph",
        args=args,
        base_dir=base_dir,
        output_dir=output_dir,
        course_dir=course_dir,
    )
    run(
        [py, str(ROOT / "scripts" / "build_practice_bank.py"), "--source-dir", str(course_dir), "--practice-depth", args.practice_depth],
        args.skip_practice_bank or not mentor_requested,
        stage="practice_bank",
        args=args,
        base_dir=base_dir,
        output_dir=output_dir,
        course_dir=course_dir,
    )
    run(
        [py, str(ROOT / "scripts" / "build_assessment_bank.py"), "--source-dir", str(course_dir)],
        args.skip_assessment_bank or not mentor_requested,
        stage="assessment_bank",
        args=args,
        base_dir=base_dir,
        output_dir=output_dir,
        course_dir=course_dir,
    )
    run(
        [
            py,
            str(ROOT / "scripts" / "build_mentor_package.py"),
            "--source-dir",
            str(course_dir),
            "--apprenticeship",
            args.apprenticeship,
            "--evidence",
            args.evidence,
        ],
        args.skip_mentor_package or not mentor_requested,
        stage="mentor_package",
        args=args,
        base_dir=base_dir,
        output_dir=output_dir,
        course_dir=course_dir,
    )
    run(
        [
            py,
            str(ROOT / "scripts" / "build_mentor_readiness_audit.py"),
            "--source-dir",
            str(course_dir),
            "--mode",
            args.mentor_audit_mode,
        ],
        args.skip_mentor_audit or not mentor_requested,
        stage="mentor_audit",
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
            "--apprenticeship",
            args.apprenticeship if mentor_requested else "none",
            "--practice-depth",
            args.practice_depth,
            "--learner-state",
            args.learner_state if mentor_requested else "none",
            "--mentor-audit-mode",
            args.mentor_audit_mode,
            *(["--include-source-artifacts"] if args.include_source_artifacts else []),
            "--source-dir",
            str(course_dir),
            "--output-dir",
            str(output_dir),
            "--description",
            "Generated by the Lineage Skill full course pipeline.",
            *(["--reuse-mentor-artifacts"] if mentor_requested else []),
            *(["--skip-validate-skill"] if args.skip_validate_skill else []),
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
            str(ROOT / "scripts" / "validate_generated_skill.py"),
            "--skill-dir",
            str(output_dir / args.skill_name),
        ],
        args.skip_validate_skill or args.skip_build_skill,
        stage="validate_skill",
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
    print("\n==> Lineage readiness", flush=True)
    print(json.dumps(readiness_summary(course_dir, output_dir / args.skill_name), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
