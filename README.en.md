<div align="center">

# Lineage Skill

**Turn a dense course, book, or long-form learning source into a source-backed, transferable, output-producing private method system.**

Extract judgment frameworks, case experience, operating processes, and quality
standards from videos, books, handouts, whiteboards, transcripts, and notes, then
let an Agent carry the teacher's or author's method into your learning,
decisions, and work output.

For Codex / Claude Code / OpenClaw / Hermes / custom Agents.

[![License](https://img.shields.io/badge/license-PolyForm%20Noncommercial%201.0.0-orange.svg)](./LICENSE)
[![Skill](https://img.shields.io/badge/AI%20Agent-Skill-orange.svg)](./SKILL.md)

[中文](./README.md)

</div>

---

## 2026-06-24 Update

This update moves `lineage-skill` from a course mentor generator toward a
course/book/long-form method system generator:

- **Book and long-form source support**: books, chaptered Markdown, OCR text,
  notes, and course materials can use the same distillation pipeline.
- **Capability asset extraction**: in addition to concepts, methods, cases, and
  quotes, packages now extract `diagnostics`, `workflows`, `rubrics`,
  `templates`, `transfer_rules`, and `failure_modes`.
- **OKF-compatible knowledge bundle**: generated Skills now include
  `references/okf/`, a Markdown + frontmatter bundle for progressive reading,
  human review, cross-tool exchange, and concept graph navigation.
- **Stronger provenance lookup**: `scripts/fetch_course_evidence.py` can fetch
  source chunks and related evidence cards by `chunk_id` or `card_id`.
- **Multi-course capability preservation**: merged packages keep capability
  fields and source-course boundaries instead of flattening disagreements.

## What Is This?

`lineage-skill` is a course and book distillation Skill for Agents. It turns a
complete set of videos, books, bootcamps, lectures, PDF handouts, whiteboards,
screenshots, transcripts, and learning notes into an installable, callable,
source-backed mentor or method Skill.

It is not "summarize this course." It turns the course into a long-lived
knowledge asset:

- Preserve the teacher's intent: important claims can trace back to lessons,
  source text, screenshots, or handouts.
- Rebuild the course structure: organize scattered videos, handouts, cases, and
  notes into concepts, methods, lesson indexes, and evidence maps.
- Generate a usable mentor: let an Agent answer, quiz, review, rehearse, and
  locate sources from the course.
- Produce work assets: turn the teacher's method into checklists, playbooks,
  templates, drafts, and quality criteria.

In one sentence: turn "I bought, watched, or studied a course/book" into "I have
a private method system I can call on at any time."

## Core Value After Distillation

The expensive part of a serious course or book is usually not the list of facts.
It is the teacher's or author's judgment framework, way of decomposing problems,
case experience, and implicit quality standards.

`lineage-skill` extracts those from tens or hundreds of hours of material and
turns them into Agent-callable capabilities:

| Value | What The Course Becomes |
| --- | --- |
| **From content consumption to method asset** | Not just "I watched the course", but a concept system, decision criteria, operating process, case library, and template library. |
| **From one-time learning to long-term coaching** | The Agent can question, review, and find weak spots according to your progress, turning the course into a training system. |
| **From vague memory to source-backed knowledge** | Important claims can trace back to lessons, source text, screenshots, or handouts, so your interpretation does not silently replace the teacher's intent. |
| **From understanding ideas to producing work** | Apply the teacher's method to real situations: draft plans, check plans, design workflows, write templates, and support decisions. |

In other words, the point is not:

> Summarize this course for me.

The point is:

> Turn a dense course into a private method system that can keep helping me learn, judge, and produce work.

## Typical Output Scenarios

| Scenario | Result You Actually Want | Example |
| --- | --- | --- |
| **Master the course** | Recover the through-line, hard parts, traps, and weak spots; let the Agent challenge you like a mentor | "I finished the first 5 lessons. Check where my understanding is still incomplete according to the teacher's system." |
| **Trace the source intent** | Locate where a claim, case, or method came from, with quote or screenshot evidence when available | "Did the teacher actually say this? If yes, which lesson was it in and what was the original point?" |
| **Transfer the teacher's method** | Apply course frameworks to your concrete situation instead of merely repeating concepts | "Use this course's method to analyze my business scenario and identify the key judgments and gaps." |
| **Produce reusable assets** | Generate checklists, playbooks, templates, drafts, and quality criteria you can use repeatedly | "Turn the teacher's method into a workflow and checklist I can reuse on every project." |

## Optional Roles

You can specify the intended use, or let the Agent choose. Course scope, evidence
strictness, and learning progress are separate dimensions.

| Role | Best For |
| --- | --- |
| `mentor` | Learning internalization: questioning, review, correction, and staged plans that turn the course into a training system |
| `expert` | Source tracing: concept explanation, lesson lookup, claim checking, and citations |
| `consultant` | Situational judgment: transfer the teacher's method to your real problem and surface judgments, risks, and recommendations |
| `practitioner` | Asset production: playbooks, checklists, templates, workflows, and quality rules |
| `custom` | Custom workflows for your business, research, writing, or training process |

Other dimensions:

| Dimension | Options |
| --- | --- |
| Course scope | Single course, multi-course with boundaries, multi-course fusion |
| Evidence strategy | Standard citations, strict source tracing |
| Learning progress | No progress tracking, or track progress and adjust plans |

You can combine roles:

```text
Turn this course into mentor,practitioner roles.
It should help me study like a mentor and also produce practical checklists.
```

## Real Example

| Name | Summary | Preview | Stars |
| --- | --- | --- | --- |
| [nihaisha-tcm](https://github.com/JuneYaooo/nihaisha-tcm) | An Agent Skill distilled from Ni Haixia TCM course materials. The source set includes **100GB+ of video course materials**, organized into a triggerable, searchable, source-backed domain Skill for course lookup, formula-pattern and acupoint study, note organization, and board screenshot evidence. | ![nihaisha-tcm preview](https://opengraph.githubassets.com/lineage-skill/JuneYaooo/nihaisha-tcm) | ![GitHub Repo stars](https://img.shields.io/github/stars/JuneYaooo/nihaisha-tcm?style=social) |

## Why It Matters

Most courses fade after you finish them: videos are too long, handouts are
scattered, cases are hard to find, and the method is hard to reuse when you need
it later.

`lineage-skill` is not a summary tool. It turns a course into a
**queryable, traceable, and executable** knowledge asset.

![lineage-skill methodology value path](./docs/img/lineage-methodology-value-en.png)

It follows `Capture -> Cite -> Compress -> Connect -> Codify -> Evaluate`:
preserve evidence first, then distill it; separate lessons, handouts,
whiteboards, cases, and notes before reorganizing them into concepts, methods,
steps, templates, and mentor capabilities.

- **Capture**: collect videos, audio, handouts, screenshots, OCR, transcripts, and notes.
- **Cite**: preserve lessons, timestamps, quotes, screenshots, and document sources.
- **Compress**: turn long material into structured summaries and course through-lines.
- **Connect**: link concepts, cases, methods, lessons, and use scenarios.
- **Codify**: turn the teacher's method into workflows, checklists, templates, and criteria.
- **Evaluate**: use course standards for review, quality checks, follow-up questions, and applied critique.

## Capabilities

This Skill includes the main pipeline needed for course and book distillation.
You do not need to design the whole "video course/book to method Skill" workflow
yourself. Provide the source materials and configure suitable model interfaces.

| Capability | What It Does | Output |
| --- | --- | --- |
| Video / audio transcription | Extracts audio from `.mp4`, or transcribes `.mp3`, `.wav`, `.m4a`, and similar files; long audio is split automatically | `transcripts/*.json` |
| Video visual understanding | Uses a vision model to analyze slides, whiteboards, software screens, charts, demos, and key frames | `analysis/*_analysis.md` |
| Large video handling | Compresses and chunks large videos to reduce upload and analysis pressure | Chunked analysis results |
| Model-selected keyframes | Builds a dense candidate pool, then asks a multimodal vision model to choose evidence-worthy keyframes from labeled contact sheets; equal intervals are only candidates, not the final evidence rule | `keyframe_selection/`, `keyframes_model_selected/` |
| PDF / document parsing | Integrates MinerU or other OCR/document parsing outputs for scanned PDFs, image PDFs, and handouts | `documents/`, `mineru_supplement.md` |
| Pure text / book distillation | Chunks Markdown, TXT, OCR Markdown, notes, book chapters, and handouts into source-backed evidence cards | `text_sources/`, `text_distillation/evidence_cards.jsonl` |
| Capability asset extraction | Extracts diagnostics, workflows, rubrics, templates, transfer rules, and failure modes from courses and books | capability fields in `course_package.json` |
| Course distillation | Combines transcripts, visual analysis, model-selected keyframes, OCR, and notes into concepts, methods, cases, and citations | `course_distillation_*.md/json` |
| CoursePackage build | Converts distillation results into a unified structure with evidence map, lesson index, and quality metadata | `course_package.json` |
| OKF bundle export | Exports structured capability assets into a progressive Markdown + frontmatter knowledge bundle | `references/okf/` |
| Multi-course merge | Combines multiple course packages into one cross-course Skill input | combined `course_package.json` |
| Dedicated mentor Skill generation | Generates `mentor` by default; other roles are also supported | Installable/callable course Skill |
| Resume and progress tracking | Records stage state, existing artifacts, and next steps so runs can resume | `lineage_progress.json` |
| Multi-course catalog | Scans multiple course workspaces and generated Skills into one catalog | `course_catalog.json` |

## Usage

### 1. Ask Your Agent to Install This Skill

Send this to your Agent:

```text
Please install this Skill:
https://raw.githubusercontent.com/JuneYaooo/lineage-skill/main/docs/install.md

After installation, tell me how I can turn my course materials into a course expert.
```

### 2. Configure Materials, Tools, And Model Interfaces

Everything commonly needed is listed here. `docs/install.md` is kept only for Agent-driven installation.

- **Course/book materials**: videos, audio, books or chaptered Markdown, PDFs, handouts, screenshots, transcripts, OCR output, and notes.
- **Local tools**: `git`, `python3`, `pip`, plus `ffmpeg` / `ffprobe` when processing videos or raw audio.
- **Model interfaces**: OpenAI-compatible speech-to-text, vision, text distillation, and optional MinerU OCR.

If you run the repo scripts directly, copy `.env.example` to `.env` and fill only the providers you use:

```bash
cp .env.example .env
```

Common variables:

```bash
# Audio transcription
AUDIO_TRANSCRIBE_API_KEY=
AUDIO_TRANSCRIBE_BASE_URL=https://api.siliconflow.cn/v1
AUDIO_TRANSCRIBE_MODEL=FunAudioLLM/SenseVoiceSmall

# Vision analysis. Use a model with video-understanding support.
LINEAGE_VISION_API_KEY=
LINEAGE_VISION_BASE_URL=https://your-openai-compatible-vision-endpoint/v1
LINEAGE_VISION_MODEL=gemini-3.1-pro-preview
LINEAGE_VISION_TIMEOUT=600

# Text distillation
LINEAGE_TEXT_API_KEY=
LINEAGE_TEXT_BASE_URL=https://api.openai.com/v1
LINEAGE_TEXT_MODEL=gpt5.5
LINEAGE_TEXT_MAX_TOKENS=4096
LINEAGE_TEXT_TIMEOUT=300

# Optional PDF OCR
MINERU_API_TOKEN=
```

Minimum setup depends on the materials:

| Materials | Minimum setup |
| --- | --- |
| Existing transcripts, OCR, and notes | `LINEAGE_TEXT_*`; use `DISTILL_USE_LLM=0` for local extractive fallback |
| Audio course | `AUDIO_TRANSCRIBE_*`, `LINEAGE_TEXT_*`, and `ffmpeg` |
| Video course, speech only | `AUDIO_TRANSCRIBE_*`, `LINEAGE_TEXT_*`, and `ffmpeg` |
| Video course with slides / boards / screen demos | `AUDIO_TRANSCRIBE_*`, `LINEAGE_VISION_*`, `LINEAGE_TEXT_*`, and `ffmpeg` |
| Scanned PDFs or complex handouts | Add `MINERU_API_TOKEN`; skip it if OCR output already exists |

### 3. Tell the Agent Where Your Materials Are

Example:

```text
I have a video/audio course directory and a set of PDF handouts.
Use lineage-skill to turn them into a course expert Skill.
Keep sources wherever possible so I can trace answers later.
```

If you already have transcripts or notes:

```text
I already have course transcripts, OCR documents, and study notes.
Skip fresh capture and package them directly into a source-backed, reviewable course Skill.
```

### 4. Use Natural Language

After the Skill is generated, it behaves like a mentor focused on this course:

```text
I finished the first 5 lessons. Review my understanding through the teacher's system and challenge the key judgments I may have missed.
```

```text
Use this course's method to analyze the real project below. Identify the key assumptions, judgment steps, and risks.
```

```text
Turn the teacher's method into a reusable playbook: use cases, inputs, steps, review criteria, and common mistakes.
```

```text
Is this conclusion actually grounded in the course? Give me the lesson, source gist, evidence strength, and which parts are inference.
```

```text
Use the teacher's quality criteria to review my plan. Tell me where it skips steps, lacks evidence, or drifts from the course method.
```

## Open Source Attribution

If you use `lineage-skill` to distill a course and open-source the generated
Skill, consider citing this repository in the generated project's README or notes
so others can trace the method and tooling.

You are also welcome to share high-quality open-source Skills or course knowledge
projects in this repository's Issues.

## Acknowledgements

- [Datawhale](https://github.com/datawhalechina) — thanks to the Datawhale open-source community for its long-running work in AI education, open courses, and learner-centered community building.
- [LINUX DO — Chinese Developer Community](https://linux.do/) — thanks to the LINUX DO community for discussion, feedback, and distribution support. The community is also a good place to discuss course distillation and Agent Skill practice.

## License

This project is licensed under the
[PolyForm Noncommercial License 1.0.0](./LICENSE).

For commercial use or business collaboration, contact <juneyaooo@gmail.com>.
