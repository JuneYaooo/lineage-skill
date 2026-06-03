# Outputs And Resume Rules

Use this reference when deciding what has already been built, where outputs belong, and how to continue a course-distillation run without mixing courses.

## Output Roots

- Course build state belongs under `<base-dir>/<course-name>/`; the default full-pipeline base dir is `.lineage/courses`.
- Generated Skills belong under `<output-dir>/<skill-name>/`; the default full-pipeline output dir is `dist`.
- Do not mix multiple source courses in one `<course-name>` directory unless the user explicitly requests a combined course package.

## Course Workspace

Expected course workspace:

```text
<course-name>/
├── transcripts/
├── analysis/
│   └── screenshots/
├── documents/
├── full_transcript.md
├── lesson_summaries.json
├── course_distillation_<date>.md
├── course_distillation_<date>.json
├── course_package.json
└── lineage_progress.json
```

The workspace root should also contain `course_catalog.json` after a full pipeline or catalog build.

## Generated Skill

Expected generated Skill:

```text
<skill-name>/
├── SKILL.md
├── agents/
├── references/
├── scripts/
└── lineage_manifest.json
```

## Resume Matrix

| Stage | Existing artifact | Resume rule |
| --- | --- | --- |
| Transcription | `transcripts/<video>_transcript.json` | Skip that video unless `--force` is requested. |
| Visual analysis | `analysis/<video>_analysis.md` | Skip that video unless `--force` is requested. |
| OCR | `documents/mineru_manifest.json`, `documents/mineru/`, `documents/mineru_supplement.md` | Use `--skip-submit` to rebuild supplement from existing MinerU output. |
| Lesson summaries | `lesson_summaries.json` | Reuse existing lesson summaries as checkpoint. |
| Course distillation | `course_distillation_<date>.md/json` | Prefer the newest distillation unless the user asks to regenerate. |
| CoursePackage | `course_package.json` | Rebuild when upstream artifacts changed. |
| Generated Skill | `<output-dir>/<skill-name>/` | Refuse overwrite unless `--force` is explicitly requested. |
| Catalog | `<base-dir>/course_catalog.json` | Rebuild after course or Skill changes. |

## Execution Rules

- Prefer the smallest workflow that advances from existing artifacts.
- Do not rerun expensive ASR, vision, or OCR stages when their outputs already exist and the user did not ask for regeneration.
- Use stage skip flags in `run_course_pipeline.py` when upstream artifacts are already present.
- Use `--force` only when the user asks to rebuild stale outputs or when a previous output is known bad.
- If a stage fails, preserve completed stage outputs and report the next command that can resume.
- Treat stdout progress as ephemeral; durable progress is represented by `lineage_progress.json` and artifacts on disk.
- Run `python scripts/build_course_catalog.py` after adding or rebuilding courses when the full pipeline did not already run it.

## Multi-Course Rules

- One source course should map to one course workspace and one `CoursePackage`.
- Multiple generated modes can share the same `CoursePackage`.
- Multiple source courses should normally generate separate Skills.
- Use `<base-dir>/course_catalog.json` to inspect all course workspaces before creating new combined outputs.
- Use `knowledge-base` or `domain-expert` only when the user explicitly wants cross-course organization or domain synthesis.
- To create one Skill from multiple courses, first run `scripts/build_multi_course_package.py`, then build a `knowledge-base` or `domain-expert` Skill from the combined workspace.
- Preserve `source_course` and `source_course_id` fields when answering from a combined package.

## Naming Rules

- If no skill name is specified, use the builder default suffix for the mode.
- Single-course default: `<course-slug>-course-expert`.
- Study mode: `<course-slug>-study-coach`.
- Practitioner mode: `<course-slug>-practitioner`.
- Citation mode: `<course-slug>-citation-archive`.
- Multi-course knowledge base: `<combined-slug>-knowledge-base`.
- Multi-course domain expert: `<combined-slug>-domain-expert`.
