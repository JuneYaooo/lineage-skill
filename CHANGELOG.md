# Changelog

## 1.0.0 — 2026-07-21

### Added

- CoursePackage 1.0 schemas, deterministic stable IDs, integrity validation, and an explicit 0.x migration command with ID mapping.
- Source-grounded TeacherModel, CapabilityGraph, PracticeBank, AssessmentBank, and MentorPackage compiler stages.
- A complete cognitive-apprenticeship protocol covering orientation, modeling, imitation, coached practice, independent practice, transfer, graduation, and continued development.
- H0–H4 hint ladders, behaviorally anchored rubrics, retrieval/production/transfer/boundary assessments, and readiness audits.
- External learner-state runtime tools for initialization, append-only PracticeEpisodes, rebuildable MasteryState, retrieval scheduling, next-task selection, learner-state validation, and Personal Skill candidates.
- Package, MentorPackage, generated-Skill, privacy, reference-integrity, duplicate-ID, cycle, and content-hash validators.
- Three original light-theme SVG diagrams for the README: product overview, four-layer architecture, and apprenticeship lifecycle.

### Changed

- The full pipeline now compiles teacher, capability, practice, assessment, mentor, validation, and catalog stages after evidence distillation.
- Strict TeacherModel and mentor audit modes now fail closed; automatic mode explicitly downgrades insufficient packages to guided or none.
- Multi-course builds preserve source boundaries and unresolved teacher conflicts instead of flattening them.
- Evidence lookup supports claim, capability, teacher-rule, task, rubric, chunk, and card identifiers.
- Generated Skills are built in a temporary directory, validated, and only then installed at the target path.
- README, installation guidance, runtime reference, examples, and agent metadata now document the 1.0 architecture and CLI.

### Privacy and safety

- Raw transcripts, OCR, analyses, text sources, selected keyframes, private learner state, and host-local paths are excluded from generated Skills by default.
- `--include-source-artifacts` is an explicit opt-in for authorized offline source packaging.
- Local paths are replaced with `withheld://` evidence references, while stable IDs and hashes preserve traceability.
- Expanded ignore rules prevent local media, learner stores, PracticeEpisodes, review queues, and Personal Skill candidates from entering Git.
- High-risk educational boundaries and provenance labels remain attached to generated practice and assessment artifacts.

### Validation

- Added migration, compiler, runtime, privacy, multi-course conflict, stable-ID, media segmentation, keyframe selection, and end-to-end regression coverage.
- The project Skill, CoursePackage, MentorPackage, and generated Mentor Skill validators pass with the 1.0 fixtures.
