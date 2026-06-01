---
name: lineage-skill
description: Use this skill when the user wants to distill a course, training program, lecture series, video/audio course, PDF/slides course material, or existing course notes into a CoursePackage and generate one or more AI Agent Skills from it.
---

# Lineage Skill

You help users turn course materials into reusable, source-grounded AI Skills.

## When To Use

Use this skill when the user asks to:

- distill a course, training program, lecture series, workshop, or curriculum
- convert videos, audio, slides, PDFs, notes, or screenshots into course knowledge
- build a course expert, study coach, practitioner, citation archive, knowledge base, or domain expert skill
- create or update a `CoursePackage`
- package distilled course materials into a new Skill

## Core Workflow

1. Clarify source material type:
   - videos/audio
   - PDFs/slides/docs
   - existing transcripts/notes
   - existing course distillation outputs
2. Preserve evidence before summarizing.
3. Build or update course artifacts:
   - `transcripts/`
   - `analysis/`
   - `documents/`
   - `lesson_summaries.json`
   - `course_distillation_<date>.md/json`
   - `full_transcript.md`
4. Build `course_package.json`.
5. Generate a mode-specific Skill.

## Skill Modes

Default to `course-expert` unless the user asks for another mode.

- `course-expert`: course Q&A, concept explanation, lesson lookup, source-backed notes
- `study-coach`: learning plans, review prompts, reflection prompts, weak-point review
- `practitioner`: playbooks, checklists, templates, workflows
- `citation-archive`: strict source lookup, quotes, auditable references
- `knowledge-base`: multi-course catalog, topic map, concept aliases
- `domain-expert`: domain map, method library, case library, boundary rules

Modes can be combined with commas, for example `course-expert,practitioner`.

## Commands

Use these scripts from the repository root.

### Full video pipeline

```bash
python scripts/run_course_pipeline.py \
  --input-dir <course-video-dir> \
  --course-name <course-name> \
  --skill-name <skill-name> \
  --mode course-expert \
  --output-dir ./dist
```

### Include PDFs with MinerU

Only run this when the user has configured `MINERU_API_TOKEN` and asks to include PDFs.

```bash
python scripts/run_course_pipeline.py \
  --input-dir <course-video-dir> \
  --documents-input <pdf-or-pdf-dir> \
  --course-name <course-name> \
  --skill-name <skill-name> \
  --mode course-expert \
  --output-dir ./dist
```

### Existing materials to Skill

```bash
python scripts/build_course_package.py \
  --course-name <course-name> \
  --source-dir <course-dir>

python scripts/build_course_skill.py \
  --course-name <course-name> \
  --skill-name <skill-name> \
  --mode <mode> \
  --source-dir <course-dir> \
  --output-dir ./dist
```

## Security Rules

- Never write real API keys into repository files.
- Never commit `.env`.
- Never hardcode private local paths, course names, or historical distilled content into reusable scripts.
- Keep generated transcripts, screenshots, OCR outputs, and distillation artifacts out of git unless the user explicitly wants to publish them.
- If a course contains copyrighted or private material, package only indexes and local references unless the user explicitly confirms what can be published.

## Response Rules

- Explain what source materials are needed.
- Prefer the smallest pipeline that fits the user's current materials.
- State what was generated and where.
- If external APIs are missing, tell the user which environment variables are required.
- For high-stakes course domains, preserve boundaries and source references.

