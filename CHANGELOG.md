# Changelog

## 1.0.0 — 2026-07-21

### Added

- Courses, books, video, OCR, and long-form notes can now be compiled into a complete cognitive-apprenticeship Skill instead of only a searchable summary.
- Generated Mentor Skills can diagnose a learner's baseline, require an attempt before feedback, give progressively smaller hints, schedule retrieval, test transfer, and evaluate graduation evidence.
- Course-specific attention cues, decision rules, demonstrations, feedback patterns, capability dependencies, practice tasks, rubrics, and assessments are now first-class artifacts.
- Learner attempts, mastery evidence, review queues, real-world results, and Personal Skill candidates can be maintained in an external private state store.
- Existing CoursePackage 0.x data can be migrated to 1.0 with stable ID mapping for historical references and learner records.

### Changed

- The full pipeline now continues from evidence distillation through teacher modeling, capability mapping, practice generation, assessment, Mentor packaging, and readiness reporting.
- Full apprenticeship is available only when the source can support it. Insufficient material is reported clearly and downgraded to guided mode instead of being presented as complete.
- Multi-course builds preserve each source's conditions and disagreements rather than producing a false consensus.
- Evidence can be traced by claim, capability, teacher rule, task, rubric, chunk, or evidence-card ID.
- Generated Skills are installed only after package and runtime validation succeeds.

### Privacy and safety

- Raw transcripts, OCR, analyses, text sources, selected keyframes, private learner state, and host-local paths are excluded from generated Skills by default.
- `--include-source-artifacts` is an explicit opt-in for authorized offline source packaging.
- Local paths are replaced with `withheld://` evidence references, while stable IDs and hashes preserve traceability.
- High-risk educational boundaries and provenance labels remain attached to generated practice and assessment artifacts.
