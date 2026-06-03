---
name: lineage-skill
description: Distills course materials into source-grounded AI agent skills. Use when the user wants to convert videos, audio, PDFs, slides, transcripts, OCR output, notes, or existing course distillation files into a CoursePackage and generated mentor, expert, consultant, practitioner, or custom Skill.
---

# Lineage Skill

Turn course materials into reusable, source-grounded AI Skills.

Core method: **Capture -> Cite -> Compress -> Connect -> Codify -> Evaluate**.
Use this as an evidence-first workflow: preserve source material before summarizing, cite sources before synthesizing, and mark unsupported gaps.

## Read When Needed

- Method and evidence rules: [references/methodology.md](references/methodology.md)
- CoursePackage schema: [references/course-package.md](references/course-package.md)
- Role selection: [references/skill-modes.md](references/skill-modes.md)
- Environment variables: [references/configuration.md](references/configuration.md)
- PDF/OCR workflow: [references/mineru-ocr.md](references/mineru-ocr.md)
- Outputs, resume, and multi-course rules: [references/output-and-resume.md](references/output-and-resume.md)

## Trigger Conditions

Use this skill when the user asks to:

- Distill a course, lecture series, workshop, training program, curriculum, or long-form class.
- Convert videos, audio, PDFs, slides, screenshots, notes, transcripts, OCR output, or course summaries into structured course knowledge.
- Generate or update a course-backed Skill.
- Build a course mentor, expert, consultant, practitioner, or custom course-backed Skill.
- Package existing `transcripts/`, `analysis/`, `documents/`, `lesson_summaries.json`, `course_distillation_*.md/json`, or `course_package.json`.

## Capabilities

This Skill owns the course-distillation pipeline. Do not describe transcription, visual analysis, screenshot extraction, OCR collection, distillation, packaging, or generated-Skill creation as work the user must perform manually when suitable source files and configured providers are available.

Supported capabilities:

- Extract audio from `.mp4` course videos and transcribe it through an OpenAI-compatible `/audio/transcriptions` endpoint.
- Split long audio into segments before transcription.
- Analyze video content through a vision-capable model, including PPT, board writing, software screens, diagrams, tables, demonstrations, and other visual teaching material.
- Compress and chunk large videos before visual analysis.
- Parse vision-model `[SCREENSHOT MM:SS]` markers, extract key frames from the original video, and de-duplicate similar screenshots.
- Collect MinerU/OCR Markdown outputs from PDFs or document directories.
- Distill transcripts, visual analyses, screenshots, OCR documents, and user notes into structured course notes.
- Build `course_package.json`, `evidence_map.json`, and `lesson_index.json`.
- Merge multiple `course_package.json` files into one combined multi-course workspace.
- Generate source-grounded course Skills in the requested role.
- Record durable pipeline progress in `lineage_progress.json`.
- Build a multi-course workspace catalog with `scripts/build_course_catalog.py`.

## Provider Requirements

Capability is separate from configuration. If a provider is missing, report the missing configuration and the smallest viable fallback; do not imply the Skill lacks the capability.

- Audio transcription requires `AUDIO_TRANSCRIBE_API_KEY`, `AUDIO_TRANSCRIBE_BASE_URL`, and `AUDIO_TRANSCRIBE_MODEL`.
  - Chinese courses can use SenseVoiceSmall/FunASR-compatible transcription services.
  - English or multilingual courses can use Whisper-compatible or OpenAI transcription models when the endpoint supports them.
- Vision analysis requires `LINEAGE_VISION_API_KEY`, `LINEAGE_VISION_BASE_URL`, and `LINEAGE_VISION_MODEL`.
  - Prefer strong video/vision models for long videos, slides, boards, screenshots, diagrams, and software screens.
  - Gemini-class video models are appropriate when exposed through a compatible endpoint or adapter.
- Text distillation requires `LINEAGE_TEXT_API_KEY`, `LINEAGE_TEXT_BASE_URL`, and `LINEAGE_TEXT_MODEL` when `DISTILL_USE_LLM=1`.
  - Prefer long-context models with stable structured output and good support for the course language.
- PDF/OCR submission requires `MINERU_API_TOKEN` unless reusing existing MinerU output with `--skip-submit`.
- Local media handling requires `ffmpeg` and `ffprobe`, or `FFMPEG` / `FFPROBE` overrides.

When configuration is absent:

- If transcripts, OCR, notes, or previous distillation files already exist, skip the missing capture stage and continue with the smallest viable workflow.
- If only raw videos exist and ASR or vision providers are missing, stop before the affected stage and tell the user exactly which variables or tools are missing.
- If PDFs are present but MinerU is not configured, continue with non-PDF sources and explain that scanned/image PDF evidence was not included unless existing OCR output is available.

## Decision Flow

1. Identify source state:
   - **Videos/audio only**: run the full pipeline.
   - **Videos plus PDFs**: run the full pipeline with document OCR if configured.
   - **Existing transcripts/OCR/notes**: skip capture; build package and Skill.
   - **Existing CoursePackage**: skip distillation; build or update Skill.
2. Choose role:
   - Default: `mentor`.
   - Use `expert` when the user specifically wants narrow course Q&A, concept explanation, or lesson lookup.
   - Use `consultant` when the user wants private consulting, diagnosis, or advice based on the course methods.
   - Use `practitioner` when the user wants checklists, playbooks, templates, workflows, or concrete work outputs.
   - Use `custom` when the user describes a specific role or workflow that does not fit the defaults.
   - Treat single-course, multi-course, and fused/domain packages as scope metadata, not role names.
   - Treat strict citation as an evidence strategy, not a role name.
   - Treat learning progress and daily study planning as a progress strategy, usually attached to `mentor`, not a separate role.
3. Preserve evidence before summarizing.
4. Before rerunning expensive stages, check existing outputs and resume from the smallest viable stage.
5. Generate outputs.
6. Verify expected files exist and report paths.

## Workflows

Default paths:

- Use `.lineage/courses/<course-name>/` for course build state unless the user provides `--base-dir` or a target directory.
- Use `dist/<skill-name>/` for generated Skills unless the user provides `--output-dir`.
- Keep one source course per course workspace.
- If the user does not provide `--skill-name`, use the builder default:
  - `<course-slug>-mentor-lineage` for `mentor`.
  - `<course-slug>-expert-lineage` for `expert`.
  - `<course-slug>-consultant-lineage` for `consultant`.
  - `<course-slug>-practitioner-lineage` for `practitioner`.
  - `<course-slug>-custom-lineage` for `custom`.

### Full Course Pipeline

Use when raw course videos need transcription, visual analysis, distillation, packaging, and Skill generation.

```bash
python scripts/run_course_pipeline.py \
  --input-dir <course-video-dir> \
  --course-name <course-name> \
  --skill-name <skill-name> \
  --mode mentor \
  --scope auto \
  --progress auto \
  --output-dir ./dist
```

With PDFs/OCR:

```bash
python scripts/run_course_pipeline.py \
  --input-dir <course-video-dir> \
  --documents-input <pdf-or-pdf-dir> \
  --course-name <course-name> \
  --skill-name <skill-name> \
  --mode mentor,practitioner \
  --scope auto \
  --progress tracked \
  --output-dir ./dist
```

Before using PDFs, check `MINERU_API_TOKEN`. If it is missing, read [references/mineru-ocr.md](references/mineru-ocr.md) and explain the fallback.

### Existing Materials

Use when the user already has transcripts, OCR, notes, summaries, or distillation outputs.

```bash
python scripts/build_course_package.py \
  --course-name <course-name> \
  --source-dir <course-dir>

python scripts/build_course_skill.py \
  --course-name <course-name> \
  --skill-name <skill-name> \
  --mode <mode> \
  --scope auto \
  --source-dir <course-dir> \
  --output-dir ./dist
```

### Existing CoursePackage

If `<course-dir>/course_package.json` already exists, run only `build_course_skill.py` unless the user asks to rebuild the package.

### Multi-Course Skill

Use when the user wants one generated Skill from multiple distilled courses.

First merge course packages:

```bash
python scripts/build_multi_course_package.py \
  --course <course-a-dir-or-package> \
  --course <course-b-dir-or-package> \
  --combined-name <combined-course-name> \
  --output-dir .lineage/courses/<combined-course-slug>
```

Then build one Skill:

```bash
python scripts/build_course_skill.py \
  --course-name <combined-course-name> \
  --source-dir .lineage/courses/<combined-course-slug> \
  --mode expert \
  --scope multi-course \
  --output-dir ./dist
```

Use `mentor`, `expert`, `consultant`, `practitioner`, or `custom` according to the user's goal. Preserve source-course distinctions when courses disagree.

## Validation Loop

After generation, verify:

```text
<generated-skill>/
├── SKILL.md
├── agents/
├── references/
├── scripts/search_course_notes.py
└── lineage_manifest.json
```

Check:

- `lineage_manifest.json` exists and includes `generated_by.id: lineage-skill`.
- `lineage_manifest.json` includes `roles`, `scope`, `evidence_strategy`, and `progress_strategy`.
- `references/course_package.json` exists.
- `references/evidence_map.json` exists.
- `references/lesson_index.json` exists.
- Role-specific reference files exist for requested roles.
- `scripts/search_course_notes.py` is executable.
- `<course-dir>/lineage_progress.json` exists after a full pipeline run.
- `<base-dir>/course_catalog.json` is updated after a full pipeline run.

If validation fails, fix the missing artifact and rerun the smallest necessary command.

## Response Rules

- State which source state was detected and which workflow you used.
- Prefer the smallest pipeline that fits the user's materials.
- Name the generated Skill path and important reference files.
- Distinguish direct course content, course-grounded synthesis, and your own inference.
- If support is missing, say what evidence is missing.
- Never write real API keys into repository files or commit `.env`.
- Do not commit private transcripts, screenshots, OCR output, or course distillation artifacts unless the user explicitly wants to publish them.
- For medical, legal, financial, investment, or other high-stakes courses, keep answers educational and source-bounded.
