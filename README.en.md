<div align="center">

# Lineage Skill

**Turn a full course into a long-lived AI mentor for learning and practice.**

Convert videos, handouts, whiteboards, transcripts, screenshots, and notes into
traceable course knowledge, then let an Agent answer questions, review lessons,
run drills, locate sources, and generate practical outputs from that course.

For Codex / Claude Code / OpenClaw / Hermes / custom Agents.

[![License](https://img.shields.io/badge/license-PolyForm%20Noncommercial%201.0.0-orange.svg)](./LICENSE)
[![Skill](https://img.shields.io/badge/AI%20Agent-Skill-orange.svg)](./SKILL.md)

[中文](./README.md)

</div>

---

## What Is This?

`lineage-skill` is an Agent Skill for turning a complete set of course materials
into a dedicated course mentor.

Its core value has two layers:

1. **Course distillation**: organize videos, bootcamps, lectures, PDF handouts,
   whiteboards, screenshots, transcripts, and learning notes into a structured,
   source-backed course knowledge system.
2. **Dedicated mentor**: let an Agent do more than summarize the course. It can
   answer from the course's original intent, ask follow-up questions, plan review,
   locate sources, and generate checklists, playbooks, and templates.

In one sentence: turn "I bought, watched, or studied a course" into "I have a
course mentor I can call on at any time."

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

- **Keep the teacher's intent**: important claims can trace back to lessons, source text, screenshots, or handouts.
- **Go beyond review**: ask questions, look up sources, follow up, and find gaps until the course actually sticks.
- **Go beyond learning**: turn the teacher's method into SOPs, checklists, playbooks, briefs, drafts, and quality checks.
- **Stop rewatching from scratch**: let the Agent carry the course method into your daily work.

## Capabilities

This Skill includes the main pipeline needed for course distillation. You do not
need to design the whole "video course to mentor" workflow yourself. Provide the
course materials and configure suitable model interfaces.

| Capability | What It Does | Output |
| --- | --- | --- |
| Video / audio transcription | Extracts audio from `.mp4`, or transcribes `.mp3`, `.wav`, `.m4a`, and similar files; long audio is split automatically | `transcripts/*.json` |
| Video visual understanding | Uses a vision model to analyze slides, whiteboards, software screens, charts, demos, and key frames | `analysis/*_analysis.md` |
| Large video handling | Compresses and chunks large videos to reduce upload and analysis pressure | Chunked analysis results |
| Useful screenshot extraction | Lets a vision model mark valuable frames, extracts them from source videos, and deduplicates similar screenshots | `analysis/screenshots/` |
| PDF / document parsing | Integrates MinerU or other OCR/document parsing outputs for scanned PDFs, image PDFs, and handouts | `documents/`, `mineru_supplement.md` |
| Course distillation | Combines transcripts, visual analysis, screenshot evidence, OCR, and notes into concepts, methods, cases, and citations | `course_distillation_*.md/json` |
| CoursePackage build | Converts distillation results into a unified structure with evidence map, lesson index, and quality metadata | `course_package.json` |
| Multi-course merge | Combines multiple course packages into one cross-course Skill input | combined `course_package.json` |
| Dedicated mentor Skill generation | Generates `mentor` by default; other roles are also supported | Installable/callable course Skill |
| Resume and progress tracking | Records stage state, existing artifacts, and next steps so runs can resume | `lineage_progress.json` |
| Multi-course catalog | Scans multiple course workspaces and generated Skills into one catalog | `course_catalog.json` |

## Requirements

You need three things:

- **Course materials**: videos, audio, PDFs, handouts, screenshots, transcripts, OCR output, and notes.
- **Local tools**: `ffmpeg` / `ffprobe` when processing videos or raw audio.
- **Model interfaces**: speech-to-text, video / vision understanding, text distillation, and optional OCR / document parsing. See [docs/model-interfaces.en.md](./docs/model-interfaces.en.md).

## Usage

### 1. Ask Your Agent to Install This Skill

Send this to your Agent:

```text
Please install this Skill:
https://raw.githubusercontent.com/JuneYaooo/lineage-skill/main/docs/install.md

After installation, tell me how I can turn my course materials into a course expert.
```

### 2. Tell the Agent Where Your Materials Are

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

### 3. Use Natural Language

After the Skill is generated, it behaves like a mentor focused on this course:

```text
How does this course explain positioning?
```

```text
I just finished lessons 1-5. Review the key points and quiz me on likely confusions.
```

```text
Turn the practical method from the course into a checklist I can follow.
```

```text
Find three cases from the course and explain which method each one illustrates.
```

```text
Which lesson does this quote or claim come from? Is there source evidence?
```

## What Can The Mentor Do?

| Use Case | Example Prompt |
| --- | --- |
| Course Q&A | "How does this course explain X?" |
| Lesson lookup | "Which lesson covers X?" |
| Concept clarification | "Explain the differences between these concepts." |
| Learning drill | "Ask me 10 questions based on the course." |
| Review plan | "Give me a 7-day review path." |
| Case organization | "Group the course cases by theme." |
| Practical checklist | "Turn the teacher's method into a checklist." |
| Template generation | "Create a reusable template based on the course method." |
| Citation check | "Is this conclusion supported by course evidence?" |
| Applied reasoning | "Use the teacher's method to analyze this concrete scenario." |
| Work output | "Draft a plan using this course's method." |
| Quality check | "Use the teacher's criteria to check what is missing in this plan." |

## Optional Roles

You can specify the intended use, or let the Agent choose. Course scope, evidence
strictness, and learning progress are separate dimensions.

| Role | Best For |
| --- | --- |
| `mentor` | Default dedicated mentor: Q&A, follow-up drills, review, application guidance, source lookup |
| `expert` | Course expert: concept explanation, lesson lookup, course Q&A, citations |
| `consultant` | Personal consultant: apply course methods to concrete situations |
| `practitioner` | Playbooks, checklists, templates, and practical workflows |
| `custom` | A custom role for your workflow |

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

## How To Describe Your Materials

You do not need to organize everything perfectly in advance. Just tell the Agent
what you have:

```text
Materials:
- Video course directory with mp4 files
- PDF handout directory
- My own study notes

Goal:
- Answer according to the course's original intent
- Keep sources
- Organize cases and practical steps
```

For large materials:

```text
First inspect the material structure. Tell me what is missing, what can be done,
and which part you recommend processing first.
```

## Boundaries

This Skill should answer primarily from your course materials. If the course does
not clearly cover something, the Agent should say so instead of presenting model
inference as the course's intent.

For medical, legal, financial, investment, or other high-risk domains, the Skill
is for learning organization and source lookup only. It is not a substitute for
professional advice.

## Real Example

[nihaisha-tcm](https://github.com/JuneYaooo/nihaisha-tcm) is a real Skill project
created through this kind of course distillation flow. Its sources include
**100GB+ of video course materials**, ultimately organized into a triggerable,
searchable, and source-backed domain Skill.

## Open Source Attribution

If you use `lineage-skill` to distill a course and open-source the generated
Skill, consider citing this repository in the generated project's README or notes
so others can trace the method and tooling.

You are also welcome to share high-quality open-source Skills or course knowledge
projects in this repository's Issues.

## License

This project is licensed under the
[PolyForm Noncommercial License 1.0.0](./LICENSE).

For commercial use or business collaboration, contact <juneyaooo@gmail.com>.
