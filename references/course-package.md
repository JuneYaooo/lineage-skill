# CoursePackage

`course_package.json` is the normalized middle layer between course materials and generated Skills.

## Required Shape

```json
{
  "schema_version": "0.1",
  "manifest": {},
  "lessons": [],
  "concepts": [],
  "topics": [],
  "cases": [],
  "methods": [],
  "learning_checks": [],
  "quotes": [],
  "evidence": [],
  "study_paths": [],
  "boundaries": [],
  "quality": {}
}
```

## Field Intent

- `manifest`: course name, source directory, generation time, source files.
- `lessons`: lesson order, titles, summaries, topics, source paths.
- `concepts`: terms, definitions, aliases, source lessons.
- `topics`: cross-lesson themes and relationships.
- `cases`: examples, demos, stories, applications.
- `methods`: frameworks, steps, procedures, decision rules.
- `learning_checks`: optional review prompts, quizzes, drills, or reflection checks.
- `quotes`: memorable statements and source references.
- `evidence`: transcripts, visual analyses, screenshots, OCR documents, distillation files.
- `study_paths`: beginner, review, topical, and time-boxed learning routes.
- `boundaries`: unsupported areas, confidence rules, professional boundaries.
- `quality`: completeness counts and missing recommended fields.

## Build Commands

```bash
python scripts/build_course_package.py \
  --course-name <course-name> \
  --source-dir <course-dir>
```

Then build a Skill:

```bash
python scripts/build_course_skill.py \
  --course-name <course-name> \
  --skill-name <skill-name> \
  --mode <mode> \
  --source-dir <course-dir> \
  --output-dir ./dist
```

Generated Skills include a root `lineage_manifest.json`. Treat it as the provenance watermark for the generated Skill:

- `generated_by.id`: `lineage-skill`
- `generated_by.repository`: generator repository
- `generated_by.script`: generator script
- `provenance.watermark`: stable generator watermark
- `provenance.watermark_visibility`: usually `manifest-only`

## Design Rules

- Keep the package course-agnostic.
- Preserve source paths.
- Treat OCR and summaries as evidence layers, not unquestionable truth.
- Do not force quizzes into courses where they do not fit.
- Let Skill roles decide how to use the same package.
