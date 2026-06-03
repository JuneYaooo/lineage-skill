# Outputs, Resume, And Multi-Course Organization

This document explains what gets written to disk, what can be resumed, how progress is recorded, and how to keep multiple course distillations organized.

## Single-Course Output Layout

By default, a course is processed under:

```text
.lineage/courses/<course-name>/
```

Typical structure:

```text
.lineage/courses/<course-name>/
├── transcripts/
│   └── <video>_transcript.json
├── analysis/
│   ├── <video>_analysis.md
│   └── screenshots/
│       └── <video>/*.jpg
├── documents/
│   ├── mineru/
│   │   └── <document-id>/
│   ├── mineru_manifest.json
│   └── mineru_supplement.md
├── full_transcript.md
├── lesson_summaries.json
├── course_distillation_<date>.md
├── course_distillation_<date>.json
├── course_package.json
└── lineage_progress.json
```

The course workspace root also keeps a multi-course catalog:

```text
.lineage/courses/course_catalog.json
```

Generated Skills are written separately:

```text
dist/<skill-name>/
├── SKILL.md
├── agents/
├── references/
├── scripts/
└── lineage_manifest.json
```

Keep source course workspaces and generated Skills separate. A course workspace is the build state; a generated Skill is the deployable product.

## Stage Outputs

| Stage | Script | Main outputs |
| --- | --- | --- |
| Audio transcription | `scripts/transcribe_video.py` | `transcripts/*_transcript.json` |
| Video visual analysis | `scripts/analyze_videos.py` | `analysis/*_analysis.md`, `analysis/screenshots/` |
| PDF/OCR collection | `scripts/parse_mineru_documents.py` | `documents/mineru_manifest.json`, `documents/mineru_supplement.md`, `documents/mineru/` |
| Course distillation | `scripts/distill_course.py` | `lesson_summaries.json`, `full_transcript.md`, `course_distillation_<date>.md/json` |
| CoursePackage build | `scripts/build_course_package.py` | `course_package.json` |
| Skill build | `scripts/build_course_skill.py` | `<output-dir>/<skill-name>/` |
| Course catalog | `scripts/build_course_catalog.py` | `.lineage/courses/course_catalog.json` |

You can rebuild the catalog without rerunning course distillation:

```bash
python scripts/build_course_catalog.py
```

## Resume Behavior

The pipeline is designed to be rerunnable, but resume support is stage-specific.

| Stage | Resume behavior | Force behavior |
| --- | --- | --- |
| Transcription | Skips a video when `transcripts/<video>_transcript.json` already exists. | `--force` retranscribes existing videos. |
| Visual analysis | Skips a video when `analysis/<video>_analysis.md` already exists. | `--force` reruns analysis and screenshot extraction. |
| MinerU/OCR | Reuses downloaded zip/extracted files when present; `--skip-submit` rebuilds the supplement from existing MinerU output. | No broad force flag; rerun with fresh inputs or remove the specific document output if needed. |
| Distillation | `lesson_summaries.json` is used as a checkpoint; existing lesson summaries are reused. `--skip-summaries` reuses the whole summary file. | Rerun without `--skip-summaries` or remove stale distillation files when a clean regeneration is needed. |
| CoursePackage | Rebuilds `course_package.json` from current source files. | Rebuild by running the command again. |
| Skill build | Refuses to overwrite an existing generated Skill directory. | `--force` deletes and rebuilds the generated Skill directory. |

The full pipeline also supports stage-level skip flags:

```text
--skip-transcribe
--skip-analyze
--skip-documents
--skip-distill
--skip-package
--skip-build-skill
```

Use these when upstream artifacts already exist and you only want to continue from a later stage.

## Progress Records

Current progress is recorded through concrete artifacts rather than one global progress database.

| Record | Meaning |
| --- | --- |
| Existing transcript JSON | That video has completed ASR. |
| Existing analysis Markdown | That video has completed visual analysis. |
| Existing screenshot files | Key visual evidence has been extracted. |
| `documents/mineru_manifest.json` | MinerU batch metadata and source mapping. |
| `documents/mineru_supplement.md` | OCR text collected for distillation. |
| `lesson_summaries.json` | Per-lesson distillation checkpoint. |
| `course_package.json` | Normalized course package is available. |
| `lineage_progress.json` | Durable stage status, artifacts, paths, and next stage for one course. |
| `.lineage/courses/course_catalog.json` | Multi-course catalog across course workspaces and generated Skills. |
| `dist/<skill-name>/lineage_manifest.json` | Generated Skill provenance and build metadata. |

Roadmap work: add richer build reports with source quality warnings, failed-file lists, and recommended next actions.

## Multi-Course Organization

For multiple course distillations, use one isolated course workspace per course:

```text
.lineage/courses/
├── course_catalog.json
├── course-a/
│   ├── transcripts/
│   ├── analysis/
│   ├── documents/
│   └── course_package.json
├── course-b/
│   ├── transcripts/
│   ├── analysis/
│   ├── documents/
│   └── course_package.json
└── course-c/
    └── ...
```

Generated Skills should also be separate by default:

```text
dist/
├── course-a-mentor-lineage/
├── course-b-expert-lineage/
└── course-c-practitioner-lineage/
```

Recommended naming:

- `course-name`: stable, human-readable course workspace name.
- `skill-name`: unique deployable Skill name, usually `<topic-or-domain-slug>-<role>-lineage`.
- Do not put `single`, `multi`, or `fused` in the Skill name by default; scope can change over time and belongs in metadata.
- Generated Skill metadata records `scope`, `evidence_strategy`, and `progress_strategy` in `lineage_manifest.json`.
- Do not reuse one `course-name` for different source courses.
- Do not overwrite a generated Skill unless you intentionally pass `--force`.

## Multi-Course Skills

The project supports a basic multi-course merge workflow. Multi-course and fused packages can generate any role: `mentor`, `expert`, `consultant`, `practitioner`, or `custom`.

Current safe options:

- Generate one Skill per course.
- Generate multiple role projections from one `CoursePackage`.
- Build a combined CoursePackage with `scripts/build_multi_course_package.py`, then generate the role the user needs.

Example:

```bash
python scripts/build_multi_course_package.py \
  --course course-a \
  --course course-b \
  --combined-name "my-domain-courses" \
  --output-dir .lineage/courses/my-domain-courses

python scripts/build_course_skill.py \
  --course-name "my-domain-courses" \
  --source-dir .lineage/courses/my-domain-courses \
  --mode consultant \
  --output-dir ./dist
```

The combined package preserves `source_course` and `source_course_id` fields so the generated Skill can distinguish where each lesson, method, quote, or evidence item came from.

## Skill Naming

If you do not specify a Skill name, the builder uses a suffix based on the selected role:

| Role | Default pattern |
| --- | --- |
| `mentor` | `<course-slug>-mentor-lineage` |
| `expert` | `<course-slug>-expert-lineage` |
| `consultant` | `<course-slug>-consultant-lineage` |
| `practitioner` | `<course-slug>-practitioner-lineage` |
| `custom` | `<course-slug>-custom-lineage` |

For multiple courses, use a combined name that describes the collection or domain, then generate the role the user needs.

Future target:

- cross-course topic maps
- concept alias normalization
- source-course conflict tracking
- multi-course evidence maps
