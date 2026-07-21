# Lineage Skill 1.0 Runtime Reference

Use this reference for provider setup, compiler stages, contracts, recovery, compatibility, generated layouts, and validation. Read the focused references for Mentor behavior, provenance, mastery, graduation, and external learner-state exchange.

## Contents

1. Compiler method and stages
2. Workspace and artifacts
3. Provider and fallback policy
4. CoursePackage 1.0
5. Teacher and training assets
6. MentorPackage and readiness
7. External learner runtime
8. Migration and multi-course compatibility
9. Recovery, idempotency, and privacy
10. Validation and failure strategy

## Compiler method and stages

```text
Capture → Cite → Compress → Connect → Codify
→ Coach → Practice → Consolidate → Transfer → Graduate
```

The full stage order is:

```text
transcribe
analyze
keyframes
documents
text_distill
distill
audit
package
teacher_model
capability_graph
practice_bank
assessment_bank
mentor_package
mentor_audit
build_skill
validate_skill
catalog
```

Each stage writes compiler status to `lineage_progress.json`. `pipeline_progress_strategy` refers only to compilation; it never represents learner mastery.

| Stage | Inputs | Outputs | Reuse / failure behavior |
| --- | --- | --- | --- |
| transcribe | video/audio, ASR, ffmpeg | transcript JSON | reuse valid output; split long or failed segments |
| analyze | video, vision provider | visual analysis, optional screenshot markers | skip for audio/text; reuse unless forced |
| keyframes | video, vision, ffmpeg/ffprobe | candidate manifests and selected frames | candidates are cache; selected frames are evidence |
| documents | PDFs/scans or OCR | document text and manifests | continue without scanned evidence when OCR is unavailable |
| text_distill | text/OCR/notes | spans, cards, synthesis, quality | deterministic local fallback is supported |
| distill | captured evidence | lesson/course synthesis | preserve source and confidence boundaries |
| audit | source artifacts | distillation audit JSON/Markdown | mentor evidence gaps are separate from capture failure |
| package | distilled assets | CoursePackage 1.0 | write 1.0; keep 0.x migration explicit |
| teacher_model | CoursePackage | TeacherModel 1.0 | thin evidence yields partial/blocked, never invented behavior |
| capability_graph | CoursePackage | nodes, edges, graph audit | reject cycles and dangling references |
| practice_bank | package + graph | tasks, rubrics, hints, errors | tasks must be standalone and observable |
| assessment_bank | graph + rubrics | blind retrieval/transfer/graduation items | practice scores do not replace assessment |
| mentor_package | compiler assets | runtime contract and policies | full mode only when ready |
| mentor_audit | mentor assets | readiness JSON/Markdown | report ready, partial, or blocked |
| build_skill | compiled workspace | generated Skill | build in temp; install after validation |
| validate_skill | generated Skill | validation report | reject private state and empty runtime assets |
| catalog | workspaces/Skills | course catalog | never expose private learner state |

## Workspace and artifacts

```text
.lineage/courses/{course-name}/
├── transcripts/
├── analysis/
│   └── screenshots/
├── keyframe_candidates/
├── keyframe_selection/
├── keyframes_model_selected/
├── documents/
├── text_sources/
├── text_distillation/
├── index/
├── lesson_summaries.json
├── course_distillation_*.md
├── course_distillation_*.json
├── distillation_audit.json
├── distillation_audit.md
├── course_package.json
├── teacher_model.json
├── capability_graph.json
├── practice_bank.json
├── assessment_bank.json
├── mentor_package.json
├── mentor_protocol.md
├── graduation_policy.json
├── mentor_readiness_audit.json
├── mentor_readiness_audit.md
└── lineage_progress.json
```

Generated Skills default to `dist/{skill-name}/`.

## Provider and fallback policy

```bash
AUDIO_TRANSCRIBE_API_KEY=
AUDIO_TRANSCRIBE_BASE_URL=
AUDIO_TRANSCRIBE_MODEL=

LINEAGE_VISION_API_KEY=
LINEAGE_VISION_BASE_URL=
LINEAGE_VISION_MODEL=
LINEAGE_VISION_TIMEOUT=600

LINEAGE_TEXT_API_KEY=
LINEAGE_TEXT_BASE_URL=
LINEAGE_TEXT_MODEL=
LINEAGE_TEXT_MAX_TOKENS=4096
LINEAGE_TEXT_TIMEOUT=300

DISTILL_USE_LLM=1
DISTILL_CHUNK_SIZE=6000
DISTILL_CHUNK_OVERLAP=500

MINERU_API_TOKEN=
```

- Raw media without ASR: stop before transcription and report required variables/tools.
- Raw video without vision: stop before visual analysis, or continue transcript-only only when the user accepts evidence loss.
- PDF without OCR: reuse existing OCR/text and identify excluded scanned evidence.
- Existing transcripts/OCR/notes/packages: skip unavailable capture providers and continue from stable artifacts.
- Text-only local extraction: set `DISTILL_USE_LLM=0` or use `--text-no-llm`.

Never log secrets. Logs may record provider/model names and configuration hashes.

## CoursePackage 1.0

Required top-level shape:

```json
{
  "schema_version": "1.0",
  "manifest": {},
  "sources": [],
  "lessons": [],
  "claims": [],
  "concepts": [],
  "topics": [],
  "cases": [],
  "methods": [],
  "diagnostics": [],
  "workflows": [],
  "rubrics": [],
  "templates": [],
  "transfer_rules": [],
  "failure_modes": [],
  "boundaries": [],
  "quotes": [],
  "learning_checks": [],
  "study_paths": [],
  "teacher_model_ref": "teacher_model.json",
  "capability_graph_ref": "capability_graph.json",
  "practice_bank_ref": "practice_bank.json",
  "assessment_bank_ref": "assessment_bank.json",
  "evidence": [],
  "quality": {}
}
```

Structured assets carry `id`, `title`, `summary`, `details`, `conditions`, `inputs`, `outputs`, `steps`, evidence IDs, provenance, confidence, source courses, related capabilities, failure modes, and human-review status. Legacy strings survive migration as `legacy_text`; do not guess missing structure.

### Stable IDs

```text
src_ lesson_ chunk_ card_ claim_ cap_ edge_ rule_
rubric_ task_ assess_ demo_ episode_ error_ candidate_
```

Never use array position as a long-lived ID. Identical content/configuration must produce identical IDs.

### Provenance

```text
direct_source
source_grounded_synthesis
cross_source_synthesis
mentor_inference
learner_hypothesis
learner_observation
real_world_evidence
external_general_knowledge
unsupported
```

See [provenance-policy.md](provenance-policy.md).

### Quality

`quality.coverage` records source, lesson, modality, capability, teacher-model, practice, and assessment coverage. `quality.integrity` records dangling references, unsupported claims, source conflicts, placeholders, and duplicate IDs. `quality.mentor_readiness` records status, missing requirements, and human-review items.

## Teacher and training assets

TeacherModel contains identity/source boundary; attention cues, frames, diagnostic questions, decision/trade-off/uncertainty rules; demonstrations, feedback/correction/progression patterns, graduation signals; applicability, non-copyable context, contraindications, controversies, conflicts; and quality.

Extract teacher-specific behavior from demonstrations, case critiques, homework reviews, Q&A, and explicit alternative rejection. Keep generic cognitive-apprenticeship behavior in the system protocol.

Capability node types are `concept`, `discrimination`, `diagnosis`, `decision`, `procedure`, `production`, `evaluation`, `transfer`, and `metacognition`. Edge types include `prerequisite_of`, `part_of`, `contrasts_with`, `applies_to`, `evaluated_by`, `fails_when`, `demonstrated_by`, `transfers_to`, and `commonly_confused_with`.

Each target needs observable outputs, prerequisites, source evidence, practice, rubrics, and assessment. Graduation capabilities need transfer assessment.

PracticeTask carries stage, task type, difficulty, cognitive load, context, standalone prompt, inputs, expected output, rubric IDs, H0–H4 hints, error IDs, feedback rules, revision requirement, transfer variants, evidence answer, and safety. Rubric criteria use observable 0–4 anchors.

AssessmentItem carries type, novelty dimensions, allowed support, blindness rule, rubric IDs, evidence answer, and parallel-form group. Do not show demonstrations, answers, or rubric anchors before a blind attempt.

## MentorPackage and readiness

MentorPackage links package IDs/hashes, evidence strategy, actual/requested apprenticeship mode, learning-contract template, graph/model/bank refs, Mentor protocol, graduation policy, learner schemas, and readiness.

Full mode requires:

1. ready TeacherModel;
2. valid acyclic capability dependencies;
3. practice and assessment coverage for every core capability;
4. anchored rubrics and complete hint ladders;
5. retrieval, production, transfer, boundary, and graduation coverage;
6. non-empty protocol and graduation policy;
7. no blocking source audit, duplicate IDs, dangling references, or private learner data.

When requested full mode cannot pass, emit guided or none and record the downgrade.

## External learner runtime

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

Generated scripts initialize state, append episodes, rebuild mastery, schedule retrieval, select the next task, validate state, and build Personal Skill candidates.

PracticeEpisodes are immutable events. Correct an old event by appending a correction event. MasteryState is derived and may decrease with counterevidence.

Next-task priority is: overdue retrieval, current project need, blocking prerequisite, repeated high-confidence error, unverified promotion, missing transfer, cognitive load, and task-type interleaving. Return selection reasons.

## Migration and multi-course compatibility

Readers support 0.x and 1.0; writers emit 1.0. Migration defaults to a new file/report. `--in-place` writes a backup first. Unreliable parsing remains `legacy_text`. Migration cannot create missing teacher evidence.

For multiple courses, migrate each independently, namespace colliding IDs, preserve teacher identity/source course, retain semantic conflicts, and let the Mentor compare conditions instead of inventing consensus.

When a Skill changes, preserve its old manifest and an ID map so external learner state can migrate without losing episodes.

## Recovery, idempotency, and privacy

- Write stage `running` before work and a terminal state afterward.
- Preserve bounded error summaries and command arguments without secrets.
- Reuse artifacts when input/config hashes are unchanged.
- Invalidate only downstream dependencies.
- Use stable JSON ordering and separate timestamps from content hashes.
- Build Skills in a temporary directory and replace atomically after validation.
- Never delete external learner state during `--force` rebuild.
- Do not package raw media, dense candidates, real learner state, or private source bodies by default.
- Personal Skills contain procedures, personal evidence, lineage pointers, and failures—not protected source bodies.

## Validation and failure strategy

```bash
python scripts/validate_lineage_package.py --package <course_package.json>
python scripts/validate_mentor_package.py --package <mentor_package.json>
python scripts/validate_generated_skill.py --skill-dir <generated-skill>
python -m pytest -q -c /dev/null --rootdir=. -o cache_dir=.pytest_cache tests
python "${CODEX_HOME:-$HOME/.codex}/skills/.system/skill-creator/scripts/quick_validate.py" .
git diff --check
```

Schema errors, duplicate IDs, dangling references, prerequisite cycles, private state in a generated Skill, unsupported high-confidence teacher claims, missing critical rubrics, or false full readiness are blocking.

Source incompleteness, thin teacher evidence, and unresolved conflicts are visible guided/blocked readiness with human-review items.
