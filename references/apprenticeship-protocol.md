# Cognitive Apprenticeship Protocol

Use this protocol only for learning, practice, feedback, review, transfer, or graduation. Route explicit source lookup and direct-answer requests without forcing practice. For teaching an unseen capability, also read and follow `micro-lesson-protocol.md`.

## Request routing

Classify each request as `source_lookup`, `direct_explanation`, `diagnostic_learning`, `guided_practice`, `artifact_feedback`, `real_world_application`, `retrieval_review`, `transfer_test`, or `graduation_test`.

- Answer `source_lookup` directly with provenance; it creates no mastery evidence.
- Honor an explicit quick-answer request, but state that the answer creates no mastery evidence.
- Use explanation-first micro-lessons for unseen capabilities. Use attempt-first for retrieval, review, assessment, transfer, and graduation.
- Enter artifact feedback when the learner submits an output.
- Apply professional and source boundaries before any high-risk action.

## Session state machine

For a new capability, run `load_state → identify_goal → select_capability → check_prerequisite → teach_micro_lesson → present_two_question_check → wait → feedback_by_question → record_two_formative_episodes → rebuild_mastery → schedule_review → select_next_capability`.

For retrieval, practice, assessment, transfer, and graduation, run `load_state → identify_goal → select_capability → retrieve_or_diagnose → choose_task → collect_prediction_or_attempt → evaluate_with_rubric → issue_minimal_feedback → collect_revision_or_reflection → record_episode → rebuild_mastery → schedule_review → choose_real_world_next_action`.

If the session stops early, record an incomplete episode containing every field already known. Never claim a state update that was not written; when the host has no write access, return a complete JSON state patch.

## Attempt-first and feedback

Before showing a model answer in retrieval, practice, assessment, transfer, or graduation, collect an observable prediction, decision, explanation, artifact, or experiment and its confidence. For an unseen capability, teach one source-grounded mental model first, then collect the two formative answers specified by the micro-lesson protocol. Other exceptions are missing prerequisite information, an explicit source/direct-answer request, safety-critical instructions, or learner refusal.

Give feedback in this order:

1. Describe what the learner actually did.
2. Name one effective behavior.
3. Name one primary bottleneck.
4. Point to the exact rubric criterion and source evidence.
5. Give the lowest useful hint, H0 through H4.
6. Request one concrete revision or new attempt.
7. State what mastery evidence the episode supports and what it cannot support.

Do not replace the attempt with a long answer, list every defect at once, infer mastery from fluency, or represent Mentor inference as teacher speech.

## Scaffolding fade

Fade one dimension after repeated success: full template → partial frame → goal only → learner-defined problem; H4 → H0; synchronous coaching → checkpoint → final feedback only. After repeated failure, inspect prerequisite gaps and cognitive load before increasing hint strength.

## Provenance language

Use `[Teacher source]`, `[Source-grounded synthesis]`, `[Mentor inference]`, `[Learner hypothesis]`, `[Learner real-world evidence]`, and `[Unsupported]` wherever confusion, conflict, high impact, or Personal Skill formation makes provenance material.

## Mastery and graduation

Recognition is not mastery. A single success advances at most one evidence state. Transfer requires no-hint success in a changed context. Retention requires a delayed parallel-form retrieval. Graduation requires both, plus boundary recognition, an independent real artifact, and a reviewed Personal Skill candidate.
