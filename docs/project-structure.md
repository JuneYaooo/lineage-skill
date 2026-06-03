# Project Structure

`lineage-skill` is not just a course summarizer. It is a meta Skill for turning course materials into source-grounded course Skills.

The project has four layers:

```text
user-facing docs
  -> agent-facing Skill spec
  -> pipeline scripts
  -> generated course Skill
```

## 1. User-Facing Layer

These files explain the project to people.

| Path | Purpose |
| --- | --- |
| `README.md` | Project value, positioning, quick start, and high-level capabilities. |
| `docs/install.md` | Installation and setup for users. |
| `docs/configuration.md` | Environment variables and model/provider configuration. |
| `docs/capabilities.md` | What the current implementation supports and what remains roadmap work. |
| `docs/methodology.md` | C5 course distillation methodology. |
| `docs/theoretical-foundation.md` | Theoretical background for the methodology. |
| `docs/course-package.md` | User-facing explanation of the `CoursePackage` middle layer. |
| `docs/skill-modes.md` | Explanation of generated Skill modes. |
| `docs/mineru-ocr.md` | User-facing PDF/OCR workflow. |
| `docs/output-and-resume.md` | Output layout, resume behavior, progress records, and multi-course organization. |
| `docs/roadmap.md` | Development roadmap. |

Use this layer for product explanation, setup instructions, project value, and human-readable documentation.

## 2. Agent-Facing Layer

These files are read by Agents when the Skill is installed or invoked.

| Path | Purpose |
| --- | --- |
| `SKILL.md` | Main Skill contract: trigger conditions, capabilities, provider requirements, workflows, validation, and response rules. |
| `references/methodology.md` | Runtime methodology reference for Agents. |
| `references/configuration.md` | Runtime environment variable quick reference. |
| `references/course-package.md` | Runtime `CoursePackage` schema reference. |
| `references/skill-modes.md` | Runtime mode-selection reference. |
| `references/mineru-ocr.md` | Runtime OCR workflow reference. |
| `references/output-and-resume.md` | Runtime output, resume, and multi-course rules. |

Use this layer for execution rules, decision logic, validation rules, provider checks, and compact references that help an Agent run the workflow correctly.

Do not put marketing copy or long user onboarding text here.

## 3. Pipeline Implementation Layer

These scripts implement the course-to-Skill pipeline.

| Script | Role |
| --- | --- |
| `scripts/run_course_pipeline.py` | Orchestrates the full pipeline from videos/documents to generated Skill. |
| `scripts/transcribe_video.py` | Extracts audio from `.mp4` files and transcribes via an OpenAI-compatible audio endpoint. |
| `scripts/analyze_videos.py` | Runs visual analysis, handles large-video compression/chunking, extracts key screenshots, and de-duplicates them. |
| `scripts/parse_mineru_documents.py` | Collects MinerU/OCR outputs for PDF and document evidence. |
| `scripts/distill_course.py` | Distills transcripts, visual analysis, OCR, and notes into course-level structured notes. |
| `scripts/build_course_package.py` | Normalizes prepared course materials into `course_package.json`. |
| `scripts/build_multi_course_package.py` | Merges multiple `course_package.json` files into one combined multi-course workspace. |
| `scripts/build_course_skill.py` | Builds the generated course-backed Skill directory. |
| `scripts/build_course_catalog.py` | Builds `.lineage/courses/course_catalog.json` across multiple course workspaces. |
| `scripts/progress.py` | Writes and updates durable per-course pipeline progress records. |
| `scripts/llm_client.py` | Shared OpenAI-compatible text, audio, and vision model clients. |

Use this layer for behavior changes. User documentation should describe these scripts, but not duplicate their internal logic.

## 4. Generated Skill Layer

The final output is a separate Skill generated from one course package.

Typical output:

```text
<generated-skill>/
├── SKILL.md
├── agents/
├── references/
│   ├── course_package.json
│   ├── course_digest.md
│   ├── full_transcript.md
│   ├── lesson_index.json
│   ├── concept_glossary.md
│   ├── evidence_map.json
│   ├── quote_index.md
│   └── study_paths.md
├── scripts/
│   └── search_course_notes.py
└── lineage_manifest.json
```

This generated Skill is the actual course mentor. It should answer from course evidence first, distinguish direct source content from synthesis, and expose source gaps.

## Data Flow

```text
course materials
  -> transcripts / visual analysis / screenshots / OCR / notes
  -> course distillation
  -> course_package.json
  -> generated course Skill
  -> course mentor for Q&A, study, citation lookup, and practical work
```

## Where New Content Should Go

| Content | Put it in |
| --- | --- |
| Project value, positioning, public explanation | `README.md` |
| User setup, model configuration, usage docs | `docs/` |
| Agent execution rules, decision logic, validation rules | `SKILL.md` |
| Compact runtime references for Agents | `references/` |
| Pipeline behavior or file generation logic | `scripts/` |
| Example command output or generated structure | `examples/` |
| Course build state | `.lineage/courses/<course-name>/` by default |
| Generated course-specific Skills | `dist/<skill-name>/` by default, or a separate generated Skill repo |

## Current Product Boundary

The current project can:

- process `.mp4` video courses;
- transcribe audio through a configured ASR endpoint;
- analyze video content with a configured vision model;
- compress and chunk large videos;
- extract and de-duplicate key screenshots;
- collect OCR/document outputs;
- distill course materials into structured notes;
- build a normalized `CoursePackage`;
- merge multiple `CoursePackage` files into one combined package;
- generate course-backed Skills in multiple modes;
- record per-course pipeline progress;
- build a multi-course catalog across course workspaces.

The current project does not yet fully provide:

- timestamp-level citation accuracy for every claim;
- semantic/vector retrieval;
- semantic cross-course conflict analysis;
- automated feedback loops from generated Skill usage back into `CoursePackage`.
