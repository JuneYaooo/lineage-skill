# Capabilities

This document lists what `lineage-skill` can do today, what is partially supported, and what remains roadmap work.

## Current Pipeline

```text
course materials
  -> transcripts / visual analysis / OCR documents
  -> course distillation
  -> course_package.json
  -> mode-specific Skill
```

## Supported Inputs

| Input | Status | Notes |
| --- | --- | --- |
| Video files | Supported | `.mp4` discovery is built into the current scripts. |
| Audio inside video | Supported | Extracted with `ffmpeg`, then sent to an OpenAI-compatible transcription endpoint. |
| Long videos | Supported | Visual analysis supports compression and chunking. |
| PPT / board / software screens | Supported through video analysis | Key frames are identified by the vision model and extracted as screenshots. |
| PDF files | Supported through MinerU | `parse_mineru_documents.py` parses PDFs and collects OCR Markdown outputs. |
| Existing transcripts / summaries | Supported | Can skip earlier stages and build `CoursePackage` directly. |
| Existing course distillation files | Supported | `build_course_package.py` and `build_course_skill.py` reuse them. |

## Main Capabilities

| Capability | Script | Status |
| --- | --- | --- |
| Video transcription | `scripts/transcribe_video.py` | Supported |
| Long-audio segmentation | `scripts/transcribe_video.py` | Supported |
| Video visual analysis | `scripts/analyze_videos.py` | Supported |
| Large-video compression and chunking | `scripts/analyze_videos.py` | Supported |
| Key screenshot extraction | `scripts/analyze_videos.py` | Supported |
| Screenshot de-duplication | `scripts/analyze_videos.py` | Supported |
| MinerU PDF OCR collection | `scripts/parse_mineru_documents.py` | Supported |
| Course distillation | `scripts/distill_course.py` | Supported |
| CoursePackage construction | `scripts/build_course_package.py` | Supported |
| Multi-course CoursePackage merge | `scripts/build_multi_course_package.py` | Supported |
| Skill generation | `scripts/build_course_skill.py` | Supported |
| Full pipeline orchestration | `scripts/run_course_pipeline.py` | Supported |
| Per-course progress record | `scripts/progress.py` | Supported |
| Multi-course workspace catalog | `scripts/build_course_catalog.py` | Supported |
| Local keyword search | generated `scripts/search_course_notes.py` | Supported |

## Skill Modes

| Mode | Output Focus |
| --- | --- |
| `course-expert` | Course Q&A, concept explanation, lesson lookup, source-backed notes |
| `study-coach` | Study paths, review prompts, reflection prompts |
| `practitioner` | Checklists, playbooks, templates, workflows |
| `citation-archive` | Evidence-first lookup, quote retrieval, auditable references |
| `knowledge-base` | Multi-course catalog, aliases, topic mapping |
| `domain-expert` | Domain map, method library, case library, boundary rules |

More detail: [skill-modes.md](./skill-modes.md)

## Quality And Boundaries

`course_package.json` includes a `quality` field with basic completeness counts.

Current quality checks cover:

- lesson count
- concept count
- topic count
- method count
- quote count
- evidence count
- study path count
- missing recommended fields

Still limited:

- evidence is mostly file-level
- OCR quality is not deeply scored
- citation accuracy is not automatically verified
- user feedback does not yet update the package

## Roadmap

- timestamp-level evidence
- stronger OCR-to-CoursePackage mapping
- semantic retrieval / vector index
- semantic cross-course merge and conflict analysis
- feedback loop from Skill usage back into CoursePackage
