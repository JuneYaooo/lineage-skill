# Changelog

## 1.0.0 — 2026-07-21

### Added

- Courses, books, video, OCR, and long-form notes can now become a learning Skill that cites its sources, demonstrates the teacher's method, guides practice, and helps the learner become independent.
- The generated Skill checks the learner's starting point, asks for an attempt before giving feedback, offers only the hint currently needed, schedules review, and tests the method in a new situation.
- It preserves how the teacher notices problems, makes decisions, demonstrates a method, corrects common mistakes, and explains where the method should not be used.
- Attempts, mistakes, review plans, and real-world results can be kept in an external private state store.
- Existing 0.x course packages can be upgraded to 1.0 without losing historical references or learner records.

### Changed

- One pipeline run now takes source material all the way to a ready-to-use learning Skill with source lookup, demonstrations, practice, feedback, review, transfer checks, and graduation criteria.
- Full coaching is available only when the source can support it. Insufficient material is reported clearly and downgraded to guided learning instead of being presented as complete.
- Multi-course builds preserve each source's conditions and disagreements rather than producing a false consensus.
- Evidence can be traced by claim, capability, teacher rule, task, rubric, chunk, or evidence-card ID.
- Generated Skills are installed only after package and runtime validation succeeds.

### Privacy and safety

- Raw transcripts, OCR, analyses, text sources, selected keyframes, private learner state, and host-local paths are excluded from generated Skills by default.
- `--include-source-artifacts` is an explicit opt-in for authorized offline source packaging.
- Local paths are replaced with `withheld://` evidence references, while stable IDs and hashes preserve traceability.
- High-risk educational boundaries and provenance labels remain attached to generated practice and assessment artifacts.
