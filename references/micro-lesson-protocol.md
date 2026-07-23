# Micro-Lesson Protocol

Use this protocol when the learner asks to learn, understand, continue a lesson, or study a new capability. Do not force it onto explicit source lookup, quick-answer, artifact review, transfer tests, or graduation tests.

## Route before teaching

- For an unseen capability, teach first and then run the two-question check below.
- If a required prerequisite is uncertain, ask one short diagnostic question before teaching; do not turn the entire lesson into a quiz.
- For retrieval, assessment, transfer, and graduation, keep attempt-first behavior and do not reteach before the blind attempt.
- If the learner explicitly requests only an explanation, explain directly and state that no mastery evidence was created.

## One-capability teaching sequence

Teach one capability at a time. Use its `learning_unit` from `references/practice_bank.json` and follow the ordered `teaching_sequence`:

1. State why the capability matters in the learner's goal or a familiar situation.
2. Bridge only the prerequisite needed now.
3. Give a plain-language mental model before precise terminology.
4. State the source-grounded definition, mechanism, conditions, and important distinction.
5. Add one useful visual when relationships are materially easier to see than read.
6. Walk through one concrete example, pointing back to the visual.
7. Show one non-example, boundary, or common confusion.
8. Recap in at most three takeaways.

Prefer short paragraphs, concrete nouns, and one idea per step. Adjust vocabulary and density to the learner profile. Do not dump the complete source summary or several capabilities into one lesson.

## Visual explanation

Use the smallest visual that clarifies the relationship:

- Use a source image or model-selected keyframe when it directly teaches the idea and can be cited.
- Use a terminal-style ASCII diagram for a small linear relationship that must render everywhere.
- Generate SVG for a flow, cycle, comparison, hierarchy, causal model, or three-or-more-part relationship.
- Use text only when a visual would add no explanatory value.

Do not output Mermaid code by default. Many agent hosts display it as raw source instead of a diagram. Use Mermaid only when the current host is known to render it and the learner explicitly prefers it; otherwise use ASCII or a real SVG file.

When generating SVG, use `scripts/render_learning_svg.py`. Store the result under the host-provided external learner artifact directory, normally `{learner_state_dir}/artifacts/diagrams/`; never write personalized diagrams into immutable Skill references. The SVG must be static and self-contained: include `<title>` and `<desc>`, high-contrast labels, a `viewBox`, and no script, animation, external URL, embedded HTML, or remote font. Embed or link the local file in the lesson when the host supports it. Accompany it with a one-sentence text fallback and explicitly explain how to read it. If file rendering is unavailable, show the equivalent ASCII diagram instead.

Example command:

```bash
python scripts/render_learning_svg.py \
  --kind flow \
  --title "Observe, decide, verify" \
  --description "A three-step decision loop" \
  --node 'observe|Observe cues|Collect concrete evidence' \
  --node 'decide|Choose|Apply the decision rule' \
  --node 'verify|Verify|Test the result and boundary' \
  --edge 'observe|decide|evidence' \
  --edge 'decide|verify|action' \
  --output <learner-state-dir>/artifacts/diagrams/decision-loop.svg
```

## Two-question check

After teaching, show the two formative questions listed by the learning unit together by default:

1. Number both questions clearly under one short heading such as `现在判断` or `理解检查`.
2. Make question 1 check understanding, distinction, mechanism, or boundary recognition.
3. Make question 2 check application, explanation, comparison, or transfer in a concrete case.
4. End the turn after both questions and wait. Do not include answers, hints, or the next lesson.
5. When the learner answers both, give separate numbered feedback for question 1 and question 2. For each, describe the answer, name what worked, identify the primary gap, and give the smallest source-grounded correction.
6. Record each numbered answer as its own formative PracticeEpisode, then summarize what the pair supports and does not support before choosing revision, review, or the next capability.

If the learner answers only one question, review that answer and briefly ask for the unanswered number; do not repeat the whole lesson. Use `one-at-a-time` pacing only when the learner requests it, an accessibility need favors shorter turns, or cognitive load is high. Never answer a question on the learner's behalf or introduce the next capability before both answers have received feedback. These questions are formative; they may support recognition or reconstruction evidence but cannot by themselves establish independent application, transfer, retention, or graduation.

## Durable phase state

Use `scripts/advance_micro_lesson.py` to persist the active unit. Default `together` phases are:

```text
teaching
  -> awaiting_answers
  -> feedback_batch
  -> complete
```

The optional `one-at-a-time` mode retains `awaiting_answer_1 → feedback_1 → ready_question_2 → awaiting_answer_2 → feedback_2`. Before yielding, persist the matching waiting phase. In together mode, record which question numbers were answered; after feedback, return to `awaiting_answers` if one is still missing, otherwise complete the unit. If persistence is unavailable, return the equivalent `active_learning_unit` JSON patch and say it was not saved.

## Feedback and continuation

Apply the rubric and evidence rules from `mentor_protocol.md`. Correct only the most consequential current gap. If question 2 exposes a missing prerequisite, pause progression and schedule a smaller bridge unit. Otherwise, complete the unit, rebuild mastery from both formative episodes, schedule review, and select the next capability with an explanation of why it comes next.
