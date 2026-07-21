<div align="center">

<img src="./docs/img/lineage-apprenticeship-hero.svg" alt="Lineage Skill: apprenticeship, not answer outsourcing" width="100%">

# Lineage Skill

**Turn long-form learning materials into a coach that helps you practice, improve, and become independent**

It does more than summarize: it keeps source links, reconstructs how the teacher solves problems, creates step-by-step practice, and checks whether the learner can use the method independently.

[![License](https://img.shields.io/badge/license-PolyForm%20Noncommercial%201.0.0-C46B35.svg)](./LICENSE)

[中文](./README.md) · [Installation](./docs/install.md) · [Changelog](./CHANGELOG.md) · [Skill entry](./SKILL.md)

</div>

## What it solves

A summary can tell you what a teacher said, but it cannot show that a learner can act. A generic AI tutor often makes this worse by doing the decisive cognitive work for the learner.

Lineage Skill 1.0 turns “I have the material” into “I can use the method”:

1. Keep source locations, transcripts, handouts, and key visuals so important claims can be checked.
2. Organize what the teacher notices first, how a problem is judged, and when a method should or should not be used.
3. Turn the method into a learning path, practical exercises, clear feedback criteria, and graduation requirements.
4. Ask the learner to try first, then give focused feedback and verify the skill again in a different situation.

The goal is not permanent dependence on an AI tutor. It is a reusable personal method that remains linked to its sources and has been tested in real work.

## Four-layer architecture

<img src="./docs/img/lineage-system-architecture.svg" alt="Lineage Skill four-layer architecture" width="100%">

| Layer | What it contains | Why it matters |
| --- | --- | --- |
| Source evidence | source locations, transcripts, handouts, key visuals | Show where every important claim comes from |
| Teacher's method | judgment cues, decision rules, demonstrations, boundaries | Teach how the teacher works, not only what the teacher said |
| Coaching | baseline check, practice, hints, feedback, review, transfer | Turn understanding into independent performance |
| Learner growth | attempts, recurring mistakes, review plans, real-world results | Keep private evidence of progress and form a personal method |

Teacher packages and generated Skills are immutable, versioned assets. Learner state is private, external, and append-only. Regenerating or deleting a Skill never deletes learner attempts.

## Apprenticeship lifecycle

<img src="./docs/img/apprenticeship-lifecycle.svg" alt="Eight stages of a Lineage apprenticeship" width="100%">

```text
orientation → modeling → imitation → coached practice
→ independent practice → transfer → graduation → alumni
```

The Skill coaches in a concrete way:

- Source lookup is answered directly and is not counted as proof of mastery.
- Learning and review collect a prediction, judgment, explanation, artifact, or experiment before showing an answer.
- Feedback identifies what worked, names the most important current problem, and gives only the hint needed for the next revision.
- The learner revises; the system preserves attempt one, feedback, attempt two, reflection, and real-world outcome.
- Parallel forms, delayed retrieval, interleaving, and changed constraints test retention and transfer.
- Templates, hints, and tutor intervention gradually fade as the learner improves.
- Graduation requires no-hint execution, delayed retention, changed-context transfer, boundary recognition, and a real artifact.

## Core data structures for developers

### Course knowledge package (CoursePackage 1.0)

This file organizes sources, lessons, concepts, methods, cases, and exercises in one place. Version 1.0 gives each item a stable ID so updates can preserve old references and learner history.

```text
course_package.json
├── sources / lessons / evidence / claims
├── concepts / methods / cases / boundaries
├── diagnostics / workflows / rubrics / templates
├── transfer_rules / failure_modes / learning_checks
└── quality.coverage / integrity / mentor_readiness
```

Migrate 0.x packages without overwriting the original:

```bash
python scripts/migrate_course_package.py path/to/course_package.json
```

`--in-place` creates a `.bak` first.

The migration report preserves an old-ID → stable-1.0-ID `id_map` for external learner state, review queues, and historical episodes.

### How the teacher approaches problems (TeacherModel 1.0)

This does not clone a teacher's personality or consciousness. It organizes only the working methods supported by the source:

- what signals the teacher notices first;
- how a problem is framed and diagnosed;
- when a method is selected or rejected;
- how a complete worked example proceeds;
- how common errors are recognized and corrected;
- which context is non-copyable or contraindicated;
- what evidence indicates independent performance.

Implicit reasoning inferred from ordinary explanation is capped at medium confidence. Missing demonstrations, critiques, Q&A, or graduation signals are reported as `missing_teacher_evidence`.

### Learning path, practice library, and assessment library

- Learning path (CapabilityGraph): shows what to learn first, what comes next, and which abilities depend on others.
- Practice library (PracticeBank): provides practical tasks, expected outputs, progressive hints, common mistakes, and clear feedback criteria.
- Assessment library (AssessmentBank): checks recall, production, transfer to a new situation, boundary recognition, and graduation readiness.

Mastery is evidence state, not a fake percentage:

```text
unseen → recognized → reconstructed → applied_with_support
→ applied_independently → transferred → retained → graduated
```

One successful episode advances at most one state. Transfer requires H0 performance in a changed context; retention requires delayed success on a parallel form.

### Runnable coaching plan (MentorPackage 1.0)

This combines the teacher's method, learning order, exercises, feedback criteria, and graduation requirements into a runnable coaching plan. Full coaching is enabled only when the material supports complete demonstrations, practice, and assessment.

Thin materials are explicitly downgraded to `guided` or `none`. `mentor_readiness_audit.json/.md` explains every blocker; the builder never emits an empty mentor playbook and calls it complete.

## Inputs and capture

| Input | Processing | Main artifacts |
| --- | --- | --- |
| Video | audio extraction, transcription, visual analysis, model-selected keyframes | `transcripts/`, `analysis/`, `keyframe_selection/` |
| Audio | duration-aware segmentation, recursive retry, transcription | `transcripts/` |
| PDF / scans | MinerU/OCR or reuse existing OCR | `documents/` |
| Markdown / TXT / chapters / notes | source spans, evidence cards, text synthesis | `text_sources/`, `text_distillation/` |
| Legacy CoursePackage | explicit 0.x → 1.0 migration | v1 package and migration report |
| Multiple courses | per-package migration, namespaced IDs, explicit conflicts | combined CoursePackage 1.0 |

Keyframe capture combines scene changes with a density floor to build candidates, then asks a vision model to choose evidence-worthy frames. Fixed intervals are candidate generation only, never the final evidence rule.

## Quick start

```bash
git clone https://github.com/JuneYaooo/lineage-skill.git
cd lineage-skill
python -m pip install -r requirements.txt
```

Media processing also requires `ffmpeg` and `ffprobe`. Copy `.env.example` and configure only the providers you need; never commit real secrets.

```bash
AUDIO_TRANSCRIBE_API_KEY=
AUDIO_TRANSCRIBE_BASE_URL=
AUDIO_TRANSCRIBE_MODEL=

LINEAGE_VISION_API_KEY=
LINEAGE_VISION_BASE_URL=
LINEAGE_VISION_MODEL=

LINEAGE_TEXT_API_KEY=
LINEAGE_TEXT_BASE_URL=
LINEAGE_TEXT_MODEL=

MINERU_API_TOKEN=
```

### Full multimedia apprenticeship

```bash
python scripts/run_course_pipeline.py \
  --input-dir /path/to/course-media \
  --documents-input /path/to/handouts \
  --notes-input /path/to/notes \
  --course-name product-discovery \
  --skill-name product-discovery-mentor-lineage \
  --mode mentor,practitioner \
  --apprenticeship full \
  --practice-depth deep \
  --learner-state external \
  --output-dir ./dist
```

### Text or book apprenticeship

```bash
DISTILL_USE_LLM=0 python scripts/run_course_pipeline.py \
  --text-input /path/to/book-or-notes \
  --course-name evidence-first-delivery \
  --mode mentor \
  --apprenticeship full \
  --text-no-llm \
  --output-dir ./dist
```

The deterministic extractor works well for explicitly labeled material. Use a strong long-context text model for implicit relationships, then review high-impact rules through the readiness audit.

## Generated Skill

```text
{course}-mentor-lineage/
├── SKILL.md
├── agents/
├── lineage_manifest.json
├── mentor_manifest.json
├── references/
│   ├── course_package.json
│   ├── teacher_model.json
│   ├── capability_graph.json
│   ├── practice_bank.json
│   ├── assessment_bank.json
│   ├── mentor_package.json
│   ├── mentor_protocol.md
│   ├── graduation_policy.json
│   ├── mentor_readiness_audit.json
│   ├── schemas/
│   ├── okf/
│   └── available source evidence
├── scripts/
│   ├── search_course_notes.py
│   ├── fetch_course_evidence.py
│   ├── initialize_apprenticeship.py
│   ├── record_practice_episode.py
│   ├── rebuild_mastery_state.py
│   ├── select_next_practice.py
│   ├── schedule_retrieval.py
│   ├── validate_learner_state.py
│   └── build_personal_skill_candidate.py
└── assets/
    ├── learning_contract.template.json
    ├── practice_episode.template.json
    └── graduation_report.template.md
```

Generation happens in a temporary directory and replaces the target atomically only after validation. Dense keyframe candidates, real learner state, and private raw materials are not packaged by default.

Use `--include-source-artifacts` only when source redistribution is authorized and offline source bodies are genuinely required. It opts in to transcripts, OCR, analyses, text sources, and model-selected keyframes. The default retains structured knowledge, stable evidence IDs, and redacted `withheld://` references only.

## Where personal learning records live

Attempts, mistakes, review plans, and real-world results stay in a private external directory chosen by the learner, rather than inside the course Skill:

```text
{learner_store_root}/apprenticeships/{mentor_package_id}/
├── apprenticeship_state.json
├── mastery_state.json
├── practice_episodes.jsonl
├── error_library.json
├── review_queue.json
├── artifact_index.json
├── graduation_record.json
└── personal_skill_candidates/
```

Practice history is appended rather than overwritten, and progress can be recalculated from that history. The system suggests a reusable personal method only after repeated success, different contexts, an unaided attempt, and reflection on a failure or counterexample. Promotion always requires explicit learner approval.

External hosts exchange only the necessary state through versioned JSON contracts. They do not import Lineage Python internals or mutate immutable teacher packages. See [the contract](./references/external-learner-store-contract.md).

## Roles

| Role | Purpose |
| --- | --- |
| `mentor` | Full or guided apprenticeship: diagnosis, practice, feedback, retrieval, transfer, graduation |
| `expert` | Source Q&A, original-claim lookup, explanation, and evidence |
| `consultant` | Course-grounded situational diagnosis, trade-offs, and recommendations |
| `practitioner` | Playbooks, checklists, templates, workflows, and work artifacts |
| `custom` | A user-defined source-bounded workflow |

Roles can be combined. Scope, evidence strictness, apprenticeship mode, and learner-state strategy remain independent dimensions.

## Validation

```bash
python -m pytest -q -c /dev/null --rootdir=. -o cache_dir=.pytest_cache tests
python scripts/validate_lineage_package.py --package path/to/course_package.json
python scripts/validate_mentor_package.py --package path/to/mentor_package.json
python scripts/validate_generated_skill.py --skill-dir path/to/generated-skill
python "${CODEX_HOME:-$HOME/.codex}/skills/.system/skill-creator/scripts/quick_validate.py" .
git diff --check
```

The full pipeline reports whether the material is complete enough, whether it can support full coaching, and whether the generated Skill can run. Strict mode rejects unsupported full coaching; automatic mode clearly downgrades to guided learning or source lookup only.

## Provenance, safety, and copyright

- Keep teacher source, source-grounded synthesis, Mentor inference, learner hypothesis, and real-world evidence distinct.
- Preserve conflicting teachers and their conditions instead of manufacturing consensus.
- Never claim to clone a teacher's mind, personality, or complete reasoning.
- Keep medical, legal, financial, investment, and other high-risk material educational and source-bounded. Graduation is not professional licensure.
- Do not commit transcripts, screenshots, OCR output, course media, learner state, or protected source bodies by default.
- Personal Skills retain procedures, personal adaptations, necessary evidence pointers, and known failures—not copyrighted source bodies.

## Example

[nihaisha-tcm](https://github.com/JuneYaooo/nihaisha-tcm) uses the evidence-distillation path on more than 100GB of TCM course material for source lookup, formula-pattern and acupoint study, board evidence, and a specialized domain Skill.

## License

Licensed under [PolyForm Noncommercial License 1.0.0](./LICENSE). For commercial use or collaboration, contact <juneyaooo@gmail.com>.
