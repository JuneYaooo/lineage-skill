# External Learner Store Contract

Lineage packages are immutable, versioned teacher assets. An external learner-state host owns private learner identity, goals, practice episodes, errors, review queues, real-world results, and Personal Skill promotion.

Exchange only versioned JSON objects and stable `source`, `capability`, `task`, `rubric`, and `assessment` IDs. Lineage must not import host internals; the host must not mutate teacher packages.

The host may add private context to a PracticeEpisode, but only task/capability IDs, an authorized artifact reference or summary, rubric results, hints used, real-world result, learner reflection, and permitted next-context fields should return to Mentor Runtime. Private journals, identity details, credentials, and unrelated personal records remain local by default.

Regenerating or deleting a Skill must never delete external learner state. When IDs change, publish an ID map and preserve append-only episodes. Personal Skill candidates may be generated automatically but require explicit learner approval before installation or promotion.
