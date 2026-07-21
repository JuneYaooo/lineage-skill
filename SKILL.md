---
name: lineage-skill
description: Turn courses, books, video, audio, PDFs, slides, transcripts, OCR, notes, and long-form materials into source-grounded learning Skills that explain, demonstrate, ask the learner to try first, give focused feedback, schedule review, test transfer, and support independent work. Also use for CoursePackage migration, teacher-method extraction, learning paths, practice and assessment libraries, private learner-state workflows, reusable personal methods, and graduation evaluation.
---

# Lineage Skill

Compile source material into a learning Skill that can cite the source, demonstrate the teacher's method, guide practice, correct mistakes, and gradually reduce the learner's dependence on help.

Use this method:

**Capture → Cite → Compress → Connect → Codify → Coach → Practice → Consolidate → Transfer → Graduate**

Preserve evidence before synthesis. Require observable learner work before mastery. Keep immutable teacher assets separate from private learner state.

## Read when needed

- Pipeline, providers, schemas, recovery, and output layouts: [references/runtime.md](references/runtime.md)
- Session routing, attempt-first, feedback, and fading: [references/apprenticeship-protocol.md](references/apprenticeship-protocol.md)
- Claim and feedback provenance: [references/provenance-policy.md](references/provenance-policy.md)
- Mastery transitions and review scheduling: [references/mastery-policy.md](references/mastery-policy.md)
- Graduation evidence: [references/graduation-policy.md](references/graduation-policy.md)
- External learner-state boundary: [references/external-learner-store-contract.md](references/external-learner-store-contract.md)

## Product invariants

- Trace teacher claims to source, lesson, timestamp, chunk, card, keyframe, or page.
- Distinguish `direct_source`, `source_grounded_synthesis`, `cross_source_synthesis`, `mentor_inference`, learner evidence, external knowledge, and unsupported content.
- Preserve conflicting sources and their conditions; never flatten disagreement into false consensus.
- Treat TeacherModel as source-supported domain behavior, not a personality or consciousness clone.
- Treat recognition, fluency, lesson completion, and one success as insufficient mastery evidence.
- Require an observable attempt before updating capability state.
- Advance at most one mastery state per successful episode.
- Require changed-context H0 performance for transfer and delayed parallel-form success for retention.
- Keep PracticeEpisodes append-only and rebuild MasteryState from events.
- Store real learner data only in a host-provided external private directory.
- Require explicit learner approval before promoting or installing a Personal Skill.
- Keep high-risk learning educational, source-bounded, and distinct from professional qualification.

## Detect source state

Choose the smallest workflow that preserves the requested evidence:

1. Raw video/audio: run capture, visual analysis for video, model-selected keyframes, distillation, audit, compilation, generation, and validation.
2. Video plus PDFs: include document parsing or reuse existing OCR.
3. Markdown/TXT/books/notes/OCR: skip media capture; build text chunks and evidence cards before compilation.
4. Existing transcripts, analyses, documents, or distillation: resume from the narrowest missing stage.
5. Existing CoursePackage 0.x: migrate to 1.0 before building teacher/runtime assets.
6. Existing CoursePackage 1.0: compile missing TeacherModel, graph, banks, MentorPackage, and Skill.
7. Multiple CoursePackages: migrate each, merge with namespaced IDs, preserve conflicts, then compile.

Do not rerun expensive capture when stable artifacts already exist and inputs have not changed.

## Configure providers

Separate capability from configuration. Report missing configuration and the smallest viable fallback.

- Audio transcription: `AUDIO_TRANSCRIBE_API_KEY`, `AUDIO_TRANSCRIBE_BASE_URL`, `AUDIO_TRANSCRIBE_MODEL`.
- Video/vision: `LINEAGE_VISION_API_KEY`, `LINEAGE_VISION_BASE_URL`, `LINEAGE_VISION_MODEL`.
- Text distillation: `LINEAGE_TEXT_API_KEY`, `LINEAGE_TEXT_BASE_URL`, `LINEAGE_TEXT_MODEL` when LLM distillation is enabled.
- PDF/OCR submission: `MINERU_API_TOKEN`, unless existing OCR is reused.
- Local media: `ffmpeg` and `ffprobe`.

If raw media needs an unavailable provider, stop before that capture stage. If transcripts, OCR, notes, or packages already exist, continue from them and report excluded modalities. Never store secrets in the repository or commit `.env`.

## Run the full compiler

For media and documents:

```bash
python scripts/run_course_pipeline.py \
  --input-dir <course-media> \
  --documents-input <pdf-or-directory> \
  --notes-input <notes> \
  --course-name <course-name> \
  --skill-name <skill-name> \
  --mode mentor \
  --apprenticeship full \
  --practice-depth deep \
  --learner-state external \
  --output-dir ./dist
```

For text or books:

```bash
python scripts/run_course_pipeline.py \
  --text-input <markdown-txt-or-directory> \
  --course-name <course-name> \
  --mode mentor \
  --apprenticeship full \
  --output-dir ./dist
```

Use `--text-no-llm` for deterministic explicit-label extraction. Treat implicit teacher cognition from ordinary exposition as medium/low confidence and require review.

## Compile existing materials

Build or migrate CoursePackage:

```bash
python scripts/build_course_package.py \
  --course-name <course-name> \
  --source-dir <course-workspace>

python scripts/migrate_course_package.py \
  <legacy-course-package.json>
```

Compile the apprenticeship assets in dependency order:

```bash
python scripts/build_teacher_model.py --source-dir <course-workspace>
python scripts/build_capability_graph.py --source-dir <course-workspace>
python scripts/build_practice_bank.py --source-dir <course-workspace> --practice-depth deep
python scripts/build_assessment_bank.py --source-dir <course-workspace>
python scripts/build_mentor_package.py --source-dir <course-workspace> --apprenticeship full
python scripts/build_mentor_readiness_audit.py --source-dir <course-workspace>
```

Then generate and validate:

```bash
python scripts/build_course_skill.py \
  --course-name <course-name> \
  --skill-name <skill-name> \
  --mode mentor \
  --apprenticeship full \
  --learner-state external \
  --source-dir <course-workspace> \
  --output-dir ./dist
```

The builder uses a temporary directory and installs the target only after validation.

## Merge courses

```bash
python scripts/build_multi_course_package.py \
  --course <course-a-package-or-dir> \
  --course <course-b-package-or-dir> \
  --combined-name <combined-name> \
  --output-dir <combined-workspace>
```

Migrate each package to an in-memory 1.0 form, namespace colliding IDs, keep source-course identity, record semantic conflicts, and route those conflicts into comparison rather than consensus.

## Choose role and apprenticeship

- Default to `mentor` when the user wants capability formation.
- Use `expert` for source lookup, course Q&A, explanation, and citations.
- Use `consultant` for course-grounded diagnosis, option comparison, and advice.
- Use `practitioner` for playbooks, checklists, templates, workflows, and artifacts.
- Use `custom` for a user-defined source-bounded role.

Treat role, scope, evidence strategy, apprenticeship mode, and learner-state strategy as separate dimensions. Mentor requests default to full apprenticeship; downgrade to guided or none when readiness is insufficient and report every blocker.

## Validate readiness

Require the following for full apprenticeship:

- valid TeacherModel with source-supported cues, decisions, demonstrations, feedback, and graduation signals;
- acyclic CapabilityGraph with complete references and prerequisites;
- at least one practice task and one assessment for each target capability;
- behaviorally anchored rubrics and ordered H0–H4 hints;
- retrieval, transfer, boundary, production, and graduation assessment coverage;
- a complete Mentor protocol and graduation policy;
- source audit that does not block core capabilities;
- no duplicate IDs, dangling references, private learner data, or empty runtime files.

Use guided mode when useful training assets exist but full teacher evidence does not. Do not hide gaps.

## Run Mentor Runtime

First route the request as source lookup, direct explanation, diagnostic learning, guided practice, artifact feedback, real-world application, retrieval review, transfer test, or graduation test.

- Answer explicit lookup directly; do not update mastery.
- Honor explicit quick answers but label them as non-mastery evidence.
- For learning, review, transfer, and graduation, collect a prediction or attempt first.
- Evaluate criterion-level rubric evidence, name one primary bottleneck, give the minimum effective hint, and request one concrete revision.
- Record prediction, confidence, attempts, hints, rubric results, source evidence, inference, errors, outcome, reflection, mastery events, and next actions.
- Explain why the next task was selected.
- Fade only one support dimension after repeated success.

Read the detailed protocol and policies before operating a generated Mentor Skill.

## Keep learner state external

Resolve the host-provided store as:

```text
{learner_store_root}/apprenticeships/{mentor_package_id}/
```

Initialize, append, rebuild, schedule, select, validate, and build candidates with the generated runtime scripts. If the host cannot write, return a complete state patch and say it was not persisted. Never generate real `learner_progress.json` or apprenticeship state under Skill `references/`.

## Build Personal Skills and graduate

Generate a candidate only after:

- three successful practices;
- two distinct contexts;
- one H0 execution;
- one failure, error, or counterexample;
- clear trigger, preconditions, procedure, output, evaluator, and failure modes;
- separable teacher lineage and personal adaptation.

Promote only after regression tests, a new-context success, no material capability regression, copyright/privacy review, Skill validation, and explicit learner approval.

Graduate only with delayed retention, unseen-case diagnosis, independent production, changed-context transfer, boundary recognition, critical comparison, personal adaptation evidence, and Personal Skill regression. After graduation, reduce Mentor behavior to source consultant, counterexample provider, advanced sparring partner, and source-update notifier.

## Verify outputs

Run:

```bash
python -m pytest -q -c /dev/null --rootdir=. -o cache_dir=.pytest_cache tests
python scripts/validate_lineage_package.py --package <course_package.json>
python scripts/validate_mentor_package.py --package <mentor_package.json>
python scripts/validate_generated_skill.py --skill-dir <generated-skill>
python "${CODEX_HOME:-$HOME/.codex}/skills/.system/skill-creator/scripts/quick_validate.py" .
git diff --check
```

Report source state, workflow, generated path, visual evidence mode, source readiness, mentor readiness, runtime readiness, apprenticeship downgrade, human-review needs, test results, and remaining risks.

## Complete the user handoff

Generation is not complete while the learner still does not know how to use the new Skill.

After validation:

1. Give a plain-language inventory of the material that was processed and anything that was missing or unreadable.
2. State whether the result supports full coaching, guided learning, or source lookup only, and explain any downgrade without internal jargon.
3. State whether raw source bodies or private learner records entered the generated Skill. Default to neither.
4. When the user asked to enable the generated Skill, place the validated Skill in the current host's active Skill location only after checking for an unrelated name collision. Do not overwrite an unrelated Skill. If the host cannot reload it immediately, tell the user that one restart is required.
5. End with one ready-to-send first-session request that collects the learner's goal, current level, available time, and real application before selecting one baseline task.
6. For later updates, preserve external learner history and rebuild only the stages affected by new or changed source material.

Do not expose compiler commands, schema names, runtime object names, or validation internals in the normal user handoff unless the user explicitly asks for developer details.

Do not commit private transcripts, images, OCR, learner state, or copyrighted bodies unless the user explicitly authorizes publication.
