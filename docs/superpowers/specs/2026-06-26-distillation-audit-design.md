# Distillation Audit Design

## Goal

Add a final, source-grounded audit layer to course distillation so every run records whether transcripts, multimodal video analysis, courseware/OCR, and text manuscripts were captured correctly, whether evidence sources agree with each other, and which parts need human review before the generated Skill is trusted.

The audit must support two audiences:

- Humans reviewing the course build need a readable report with missing evidence, transcription risks, terminology risks, and manual proofreading recommendations.
- Scripts and generated Skills need machine-readable status so answers can distinguish high-confidence claims, cross-checked claims, single-source claims, and unsupported synthesis.

## Artifacts

The course workspace gets two final audit files:

- `distillation_audit.json`: normalized audit data for tooling and generated Skills.
- `distillation_audit.md`: human-readable review report.

Generated Skills copy both files into `references/` when present:

- `references/distillation_audit.json`
- `references/distillation_audit.md`

`course_package.json` keeps a compact `quality.distillation_audit` summary with counts and report paths. Detailed per-lesson notes stay in the audit files so the normalized package remains manageable.

## Audit Model

The JSON report records course-level and lesson-level findings.

Course-level fields:

- `source_inventory`: counts and paths for transcripts, visual analyses, selected keyframes, screenshots, documents, text sources, OCR outputs, lesson summaries, and package files.
- `coverage_summary`: expected lesson count when inferable, available transcript count, available visual-analysis count, available document/text count, and missing-source counts.
- `cross_validation_summary`: counts for multi-source support, transcript-only claims, visual-only claims, document-only claims, source conflicts, and items needing manual review.
- `manual_review`: prioritized course-wide review notes.

Lesson-level fields:

- `lesson_id`, `title`, `media_ref`, and source paths.
- `transcript_status`: present/missing, duration, text length, empty or short transcript flags, probable truncation flags, and terms needing review.
- `visual_status`: present/missing, keyframe count, screenshot-marker count, visual coverage notes, and whether the analysis appears to include slides, board writing, demos, diagrams, tables, or software screens.
- `document_status`: related courseware/OCR/manuscript paths when inferable, plus extraction status and suspicious empty/short text flags.
- `cross_validation`: source support, mismatches, source-only claims, conflicting terminology, and review recommendations.
- `traceability`: links to transcript JSON, `full_transcript.md`, visual analysis Markdown, keyframe manifests, document paths, text chunks, evidence cards, and lesson summary entries.

## Cross Validation

When multiple evidence sources exist for the same lesson or topic, the audit records whether they support or challenge each other.

Initial validation is conservative and file-based:

- Match transcript and video analysis by normalized media stem.
- Associate documents and text chunks by filename, explicit lesson numbering, or manifest metadata when available.
- Flag missing pairings instead of pretending they are equivalent.

The audit flags these cases:

- `supported_by_multiple_sources`: a topic, term, or lesson has transcript plus visual or document support.
- `transcript_visual_mismatch`: visual analysis names slides, diagrams, demos, or board content that are absent from transcript-derived summaries.
- `slides_not_mentioned_in_transcript`: visual/document material appears important but has no spoken counterpart.
- `spoken_but_not_in_slides`: transcript contains important methods, cases, or terminology without visual/document support.
- `terminology_needs_review`: likely ASR/OCR terminology ambiguity, wrong homophones, inconsistent names, or suspicious rare terms.
- `manual_review_required`: missing, conflicting, or low-confidence evidence should be checked by a person.

The first implementation can rely on deterministic heuristics and existing distillation cards. If a configured text model is available later, it can enrich the same schema with deeper semantic comparison without changing downstream consumers.

## Layered Distillation

Final distilled content should be progressive rather than a flat summary.

The package and generated Skill should preserve these layers:

- `overview`: course-level essence, scope, core thesis, and high-value takeaways.
- `lesson_digest`: per-lesson summaries with source references.
- `structured_knowledge`: concepts, methods, cases, workflows, diagnostics, rubrics, templates, transfer rules, boundaries, and failure modes.
- `evidence_refs`: transcript segments, visual analysis sections, selected keyframes, OCR/text chunks, document paths, and direct quotes that support each distilled item.
- `source_trace`: enough path and id information to return to the original transcript, image evidence, OCR text, or courseware.

Generated Skills must instruct agents to answer from the highest useful layer first, then cite or fetch lower-level evidence when the user asks for details, exact wording, visual support, or verification.

## Pipeline Integration

Add a final audit stage after transcript capture, visual analysis, keyframe selection, document/text distillation, course distillation, and package building. The stage should be resumable and cheap to rerun.

`scripts/run_course_pipeline.py` should run the audit stage near the end of the pipeline and record it in `lineage_progress.json`.

`scripts/build_course_package.py` should read `distillation_audit.json` when present and add a compact audit summary to `quality`.

`scripts/build_course_skill.py` should copy audit artifacts into `references/` and mention them in the generated `SKILL.md` reference order.

The stage should not require private source files to be committed. It records local paths and evidence ids, matching the existing repository rule that transcripts, screenshots, OCR output, and course artifacts stay private unless the user explicitly publishes them.

## Reliability

The audit must never silently upgrade confidence. If a source is absent, ambiguous, too short, empty, or unmatched, the report states that plainly.

The Markdown report should include a clear manual-review section with wording such as:

- "人工校对建议：请复核专业术语、专名、同音误识别、OCR 错字，以及转录与课件不一致处。"
- "本报告为自动审计结果，不能替代对原始课程材料的人工核对。"

The JSON report should use stable keys and avoid prose-only status so tests can validate coverage and downstream tools can depend on it.

## Testing

Add focused tests for:

- Building an audit from a fixture course with transcript, visual analysis, keyframe manifest, document text, and evidence cards.
- Flagging missing transcript, missing visual analysis, short transcript, and unmatched document evidence.
- Recording cross-validation statuses when transcript, visual analysis, and documents exist for the same lesson.
- Adding compact audit summary paths and counts to `course_package.quality`.
- Copying audit files into generated Skill `references/`.

## Scope

This design does not require a new UI, embeddings, vector search, or mandatory LLM calls. It also does not attempt to prove semantic equivalence perfectly. The first version creates a durable audit structure, conservative cross-source checks, and explicit human-review guidance. Deeper model-based comparison can be added later using the same schema.
