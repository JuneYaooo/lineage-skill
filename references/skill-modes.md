# Skill Roles And Orthogonal Options

Default role: `mentor`.

Roles describe what the generated Skill should do for the user. Scope, evidence strictness, and progress tracking are separate metadata/options; do not encode them as parallel roles.

## Roles

| Role | Use When | Adds |
| --- | --- | --- |
| `mentor` | Guided learning, practice, review, progress-aware study, and course-backed application | `mentor_playbook.md`, `mentor_sessions.md`, `learner_progress.json` |
| `expert` | Course Q&A, concept explanation, lesson lookup, source-backed answers | Base references only |
| `consultant` | Private consulting, scenario diagnosis, option comparison, course-grounded advice | `consulting_playbook.md`, `scenario_templates.md` |
| `practitioner` | Work output, SOPs, checklists, playbooks, templates, drafts, workflows | `playbooks.md`, `checklists.md`, `templates.md`, `case_index.json` |
| `custom` | User-defined role or workflow not covered above | `custom_role.md`, `custom_workflows.md` |

## Scope

Scope is derived from the package, not from the role name.

| Scope | Meaning |
| --- | --- |
| `single-course` | One source course. |
| `multi-course` | Multiple courses kept distinguishable. |
| `fused` | Multiple courses intentionally synthesized into a unified system. |

For multi-course or fused packages, preserve `source_course` and `source_course_id` when answering.

## Evidence Strategy

| Evidence | Meaning |
| --- | --- |
| `standard` | Normal course-grounded citation and synthesis. |
| `strict` | Strong source lookup, fewer unsupported inferences, explicit evidence gaps. |

Strict evidence is not a role. It can apply to `mentor`, `expert`, `consultant`, `practitioner`, or `custom`.

## Progress Strategy

| Progress | Meaning |
| --- | --- |
| `none` | No learner progress state. |
| `tracked` | Use progress logs, weak-point records, review queues, and plan adjustments when the host workflow supports persistent updates. |

Progress tracking is most common for `mentor`, but can also apply to a custom role.

`build_course_skill.py` writes these choices into `lineage_manifest.json` as `scope`, `evidence_strategy`, and `progress_strategy`.

## Selection Rules

- Use `mentor` by default when the user wants a dedicated course tutor/mentor or has not specified a narrower role.
- Use `expert` when the user only wants course Q&A, concept explanation, or lesson lookup.
- Use `consultant` when the user wants the course to analyze their personal/business/project situation.
- Use `practitioner` when the user wants the course to help produce concrete work artifacts.
- Use `custom` when the user describes a specialized course-backed workflow.
- Use `evidence=strict` when the user emphasizes exact wording, auditability, quotes, or source verification.
- Use `scope=multi-course` or `scope=fused` when the combined package contains multiple source courses.

## Command Pattern

```bash
python scripts/build_course_skill.py \
  --course-name <course-name> \
  --mode mentor \
  --scope auto \
  --progress auto \
  --source-dir <course-dir> \
  --output-dir ./dist
```
