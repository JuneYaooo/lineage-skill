<div align="center">

<img src="./docs/img/lineage-apprenticeship-hero.svg" alt="Lineage Skill: apprenticeship, not answer outsourcing" width="100%">

# Lineage Skill

**A source-grounded lineage compiler and cognitive-apprenticeship runtime generator**

Compile courses, books, video, handouts, and long-form learning materials into Agent Skills that can model, diagnose, coach, assess, transfer, and graduate—without replacing the learner's work.

[![License](https://img.shields.io/badge/license-PolyForm%20Noncommercial%201.0.0-C46B35.svg)](./LICENSE)
[![CoursePackage](https://img.shields.io/badge/CoursePackage-1.0-177E74.svg)](./references/schemas/course_package.schema.json)
[![Apprenticeship](https://img.shields.io/badge/cognitive-apprenticeship-7654A7.svg)](./references/apprenticeship-protocol.md)

[中文](./README.md) · [Installation](./docs/install.md) · [Changelog](./CHANGELOG.md) · [Skill entry](./SKILL.md)

</div>

## What it solves

A summary can tell you what a teacher said, but it cannot show that a learner can act. A generic AI tutor often makes this worse by doing the decisive cognitive work for the learner.

Lineage Skill 1.0 connects evidence compilation with actual capability formation:

1. Preserve transcripts, OCR, text spans, model-selected keyframes, lesson structure, and source quality.
2. Reconstruct only source-supported teacher attention cues, problem frames, decision rules, demonstrations, feedback patterns, and boundaries.
3. Compile those assets into a capability graph, executable practice tasks, behaviorally anchored rubrics, blind assessments, and graduation criteria.
4. Generate an attempt-first Mentor Skill that forms capability through observable artifacts, correction, delayed retrieval, changed-context transfer, and real-world results.

The goal is not permanent dependence on a tutor. It is an independent Personal Skill with visible teacher lineage, explicit personal adaptation, counterexamples, and real-world evidence.

## Four-layer architecture

<img src="./docs/img/lineage-system-architecture.svg" alt="Lineage Skill four-layer architecture" width="100%">

| Layer | First-class artifacts | Responsibility |
| --- | --- | --- |
| Evidence | transcripts, OCR, keyframes, evidence cards, audits | Preserve sources, locations, and evidence strength |
| Teacher Lineage | CoursePackage, TeacherModel, CapabilityGraph, PracticeBank, AssessmentBank | Compile source-bounded methods, dependencies, practice, and measurement |
| Mentor Runtime | MentorPackage, mentor protocol, graduation policy | Diagnose, require attempts, give minimum hints, schedule retrieval, test transfer, and graduate |
| Learner Evolution | PracticeEpisodes, MasteryState, ReviewQueue, Personal Skill candidates | Keep private, evolving learner evidence in an external learner-state host |

Teacher packages and generated Skills are immutable, versioned assets. Learner state is private, external, and append-only. Regenerating or deleting a Skill never deletes learner attempts.

## Apprenticeship lifecycle

<img src="./docs/img/apprenticeship-lifecycle.svg" alt="Eight stages of a Lineage apprenticeship" width="100%">

```text
orientation → modeling → imitation → coached practice
→ independent practice → transfer → graduation → alumni
```

Runtime behavior is concrete:

- Source lookup is answered directly and creates no mastery evidence.
- Learning and review collect a prediction, judgment, explanation, artifact, or experiment before showing an answer.
- Feedback names one effective behavior and one primary bottleneck, ties both to a rubric and source, then gives the lowest useful H0–H4 hint.
- The learner revises; the system preserves attempt one, feedback, attempt two, reflection, and real-world outcome.
- Parallel forms, delayed retrieval, interleaving, and changed constraints test retention and transfer.
- Templates, hint strength, and intervention timing fade one dimension at a time.
- Graduation requires no-hint execution, delayed retention, changed-context transfer, boundary recognition, and a real artifact.

## First-class packages

### CoursePackage 1.0

CoursePackage is the normalized evidence and capability layer. Version 1.0 replaces loose string assets with stable-ID objects carrying provenance, evidence, conditions, inputs, outputs, steps, confidence, source courses, and human-review status.

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

### TeacherModel 1.0

TeacherModel does not clone personality or consciousness. It represents source-supported domain behavior:

- what signals the teacher notices first;
- how a problem is framed and diagnosed;
- when a method is selected or rejected;
- how a complete worked example proceeds;
- how common errors are recognized and corrected;
- which context is non-copyable or contraindicated;
- what evidence indicates independent performance.

Implicit reasoning inferred from ordinary explanation is capped at medium confidence. Missing demonstrations, critiques, Q&A, or graduation signals are reported as `missing_teacher_evidence`.

### CapabilityGraph, PracticeBank, and AssessmentBank

- CapabilityGraph uses stable `cap_` IDs, explicit prerequisites, and cycle/dangling-reference validation.
- PracticeBank provides standalone prompts, expected artifacts, five hint levels, common errors, feedback rules, and behaviorally anchored rubrics.
- AssessmentBank separates learning from measurement and covers retrieval, production, transfer, boundary, and graduation.

Mastery is evidence state, not a fake percentage:

```text
unseen → recognized → reconstructed → applied_with_support
→ applied_independently → transferred → retained → graduated
```

One successful episode advances at most one state. Transfer requires H0 performance in a changed context; retention requires delayed success on a parallel form.

### MentorPackage 1.0

MentorPackage is the stable runtime contract between teacher assets and a generated Mentor Skill. `apprenticeship_mode: full` is allowed only when teacher evidence, prerequisites, practice coverage, anchored rubrics, assessments, protocols, and source audits pass readiness checks.

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

## External learner state

The learner-selected external state host owns:

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

PracticeEpisodes are append-only; MasteryState is rebuildable. A Personal Skill candidate requires at least three successes, two contexts, one H0 execution, and one failure or counterexample. Promotion or installation always requires explicit learner approval.

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

The full pipeline reports `source_readiness`, `mentor_readiness`, and `runtime_readiness` separately. `--teacher-model strict` blocks a non-ready TeacherModel. `--mentor-audit-mode strict` refuses to present insufficient evidence as full apprenticeship; auto mode downgrades explicitly to guided or none.

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
