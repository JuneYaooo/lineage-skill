---
name: lineage-skill
description: Distills course, book, and long-form learning materials into source-grounded AI agent skills. Use when the user wants to convert videos, audio, PDFs, ebooks, books, slides, transcripts, OCR output, notes, or existing course/book distillation files into a CoursePackage and generated mentor, expert, consultant, practitioner, or custom Skill.
---

# Lineage Skill

Turn course, book, and long-form learning materials into reusable, source-grounded AI Skills.

Core method: **Capture -> Cite -> Compress -> Connect -> Codify -> Evaluate**.
Use this as an evidence-first workflow: preserve source material before summarizing, cite sources before synthesizing, and mark unsupported gaps.

This is a generic methodology Skill. Do not put any specific course's concepts,
lesson names, keyframes, summaries, or domain content into this Skill. Course
content belongs only in that course workspace and generated course Skill.

## Read When Needed

- Runtime reference: [references/runtime.md](references/runtime.md)

## Trigger Conditions

Use this skill when the user asks to:

- Distill a course, book, ebook, lecture series, workshop, training program, curriculum, long-form class, or method-heavy document collection.
- Convert videos, audio, PDFs, ebooks, chaptered Markdown, slides, screenshots, notes, transcripts, OCR output, or course/book summaries into structured source-grounded knowledge.
- Generate or update a course-backed or book-backed Skill.
- Build a course/book mentor, expert, consultant, practitioner, or custom source-backed Skill.
- Package existing `transcripts/`, `analysis/`, `documents/`, `lesson_summaries.json`, `course_distillation_*.md/json`, or `course_package.json`.

## Capabilities

This Skill owns the course-distillation pipeline. Do not describe transcription, visual analysis, screenshot extraction, OCR collection, distillation, packaging, or generated-Skill creation as work the user must perform manually when suitable source files and configured providers are available.

Supported capabilities:

- Extract audio from `.mp4` course videos and transcribe it through an OpenAI-compatible `/audio/transcriptions` endpoint.
- Directly transcribe standalone `.mp3`, `.wav`, `.m4a`, `.aac`, `.flac`, `.ogg`, and `.opus` course audio files.
- Split long audio into segments before transcription.
- Analyze video content through a vision-capable model, including PPT, board writing, software screens, diagrams, tables, demonstrations, and other visual teaching material.
- Compress and chunk large videos before visual analysis.
- Select keyframes with a multimodal vision model: first create a dense candidate pool, then have the model choose keyframes from labeled contact sheets. Fixed intervals are allowed only as candidate generation, not as the final evidence selection rule.
- Parse vision-model `[SCREENSHOT MM:SS]` markers when produced by video analysis, but treat them as supplemental to model-selected keyframes.
- Collect MinerU/OCR Markdown outputs from PDFs or document directories.
- Distill transcripts, visual analyses, screenshots, OCR documents, and user notes into structured course notes.
- Distill pure text materials into source-grounded evidence cards before synthesis, including Markdown notes, TXT exports, handouts, and existing OCR Markdown.
- Extract capability cards from books and courses: diagnostics, workflows, rubrics, templates, transfer rules, and failure modes in addition to concepts, methods, cases, quotes, tasks, and boundaries.
- Build `course_package.json`, `evidence_map.json`, and `lesson_index.json`.
- Build an OKF-style Markdown knowledge bundle under `references/okf/` for progressive reading, human review, cross-agent exchange, and concept graph navigation.
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
- Local media handling requires installed `ffmpeg` and `ffprobe`.

When configuration is absent:

- If transcripts, OCR, notes, or previous distillation files already exist, skip the missing capture stage and continue with the smallest viable workflow.
- If raw audio or videos need transcription and ASR is missing, stop before transcription and tell the user exactly which variables or tools are missing.
- If raw videos need visual analysis and vision configuration is missing, stop before visual analysis or skip it only when the user accepts transcript-only processing.
- If PDFs are present but MinerU is not configured, continue with non-PDF sources and explain that scanned/image PDF evidence was not included unless existing OCR output is available.

Standalone audio files are transcribed by the capture stage, but they do not produce visual analysis or screenshots.

## Decision Flow

1. Identify source state:
   - **Videos/audio only**: run the full pipeline.
   - **Videos plus PDFs**: run the full pipeline with document OCR if configured.
   - **Existing transcripts/OCR/notes/books/text**: skip capture; build package and Skill.
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
4. For videos, run visual analysis and model-selected keyframes. Do not present equal-interval frames as final keyframes unless a vision model has selected or validated them.
5. Before rerunning expensive stages, check existing outputs and resume from the smallest viable stage.
6. Generate outputs.
7. Verify expected files exist and report paths.

## Workflows

Default paths:

- Use `.lineage/courses/<course-name>/` for course build state unless the user provides `--base-dir` or a target directory.
- Use `dist/<skill-name>/` for generated Skills unless the user provides `--output-dir`.
- Keep one source course per course workspace.
- Use stable stage directories so interruption can resume without mixing artifacts:
  - `transcripts/` for ASR outputs.
  - `analysis/` for video visual analysis and optional screenshot markers.
  - `keyframe_candidates/` for dense candidate frames; this is an intermediate cache and should not be packaged by default.
  - `keyframe_selection/` for model selection manifests, contact-sheet decisions, and `model_keyframe_summary.md`.
  - `keyframes_model_selected/` for final selected image evidence.
  - `documents/` for OCR, handouts, slides, and document manifests.
  - `text_sources/` for stable source manifests and text chunks.
  - `text_distillation/` for evidence cards, text-source synthesis, source summaries, and quality audits.
  - `index/` for coverage audits, evidence path guides, and searchable inventories when available.
- If the user does not provide `--skill-name`, use the builder default:
  - `<course-slug>-mentor-lineage` for `mentor`.
  - `<course-slug>-expert-lineage` for `expert`.
  - `<course-slug>-consultant-lineage` for `consultant`.
  - `<course-slug>-practitioner-lineage` for `practitioner`.
  - `<course-slug>-custom-lineage` for `custom`.

### Full Course Pipeline

Use when raw course videos and/or audio files need transcription, visual analysis where video exists, distillation, packaging, and Skill generation.

```bash
python scripts/run_course_pipeline.py \
  --input-dir <course-media-dir> \
  --course-name <course-name> \
  --skill-name <skill-name> \
  --mode mentor \
  --scope auto \
  --progress auto \
  --output-dir ./dist
```

The full pipeline now includes `select_video_keyframes.py` after video analysis. It writes resumable manifests under `keyframe_selection/` and copies only model-selected keyframes into `keyframes_model_selected/`.

With PDFs/OCR:

```bash
python scripts/run_course_pipeline.py \
  --input-dir <course-media-dir> \
  --documents-input <pdf-or-pdf-dir> \
  --course-name <course-name> \
  --skill-name <skill-name> \
  --mode mentor,practitioner \
  --scope auto \
  --progress tracked \
  --output-dir ./dist
```

Before using PDFs, check `MINERU_API_TOKEN`. If it is missing, read [references/runtime.md](references/runtime.md) and explain the fallback.

For books, ebooks, pure text courses, or notes-only sources:

```bash
python scripts/run_course_pipeline.py \
  --text-input <markdown-or-text-file-or-dir> \
  --notes-input <optional-notes-dir> \
  --course-name <course-name> \
  --skill-name <skill-name> \
  --mode mentor,expert \
  --output-dir ./dist
```

This skips media capture when `--input-dir` is absent. The text stage writes `text_sources/` and `text_distillation/`, then the package builder merges evidence cards into concepts, methods, cases, quotes, boundaries, learning checks, diagnostics, workflows, rubrics, templates, transfer rules, and failure modes.

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
- `references/okf/index.md` exists.
- `references/okf/log.md` exists.
- `references/evidence_map.json` exists.
- If videos were present, `references/keyframe_selection/model_keyframe_summary.md` exists or the pipeline explicitly recorded that no video files were found.
- If videos were present, selected images live under `references/keyframes_model_selected/`; raw candidate frames should not be required in the generated Skill.
- `references/lesson_index.json` exists.
- Role-specific reference files exist for requested roles.
- `scripts/search_course_notes.py` is executable.
- `scripts/fetch_course_evidence.py` is executable.
- `references/course_package.json` includes capability fields when available: `diagnostics`, `workflows`, `rubrics`, `templates`, `transfer_rules`, and `failure_modes`.
- `<course-dir>/lineage_progress.json` exists after a full pipeline run.
- `lineage_progress.json` includes the `keyframes` stage and artifact counts for candidates, selected keyframes, manifests, and keyframe summaries.
- `<base-dir>/course_catalog.json` is updated after a full pipeline run.

If validation fails, fix the missing artifact and rerun the smallest necessary command.

## Response Rules

- State which source state was detected and which workflow you used.
- Prefer the smallest pipeline that fits the user's materials.
- Name the generated Skill path and important reference files.
- Report whether visual evidence came from model-selected keyframes, supplemental screenshot markers, or transcript-only fallback.
- Distinguish direct course content, course-grounded synthesis, and your own inference.
- If support is missing, say what evidence is missing.
- Never write real API keys into repository files or commit `.env`.
- Do not commit private transcripts, screenshots, OCR output, or course distillation artifacts unless the user explicitly wants to publish them.
- For medical, legal, financial, investment, or other high-stakes courses, keep answers educational and source-bounded.
