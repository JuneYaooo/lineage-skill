# Theoretical Foundation

`lineage-skill` is a practical engineering project, but its architecture is grounded in established learning, knowledge management, and retrieval ideas.

This document separates source authority into three levels:

- **Primary / canonical**: original papers, books, publishers, or institutions directly associated with the model.
- **Scholarly secondary**: peer-reviewed reviews, indexing pages, or academic summaries.
- **Practical secondary**: university teaching centers or implementation guides. Useful for explanation, not the core authority.

The short version:

```text
Instructional Design
  + Cognitive Apprenticeship
  + Knowledge Management
  + Multimedia Learning
  + Retrieval-Augmented Generation
  + Skill Packaging
= General Course Distillation
```

## 1. ADDIE and C5

ADDIE is a common instructional design model: Analysis, Design, Development, Implementation, Evaluation.

Primary institutional reference: Florida State University's Learning Systems Institute states that its faculty developed ADDIE for the U.S. Army in 1975 and that it remains a standard framework for education and training programs.

Reference: https://lsi.fsu.edu/about-lsi/our-experience

`lineage-skill` uses C5 as an AI-native adaptation:

| ADDIE | C5 | Project layer |
| --- | --- | --- |
| Analysis | Capture | Gather source materials and preserve context |
| Design | Connect | Rebuild course structure, topics, and learning paths |
| Development | Compress | Produce summaries, concepts, cases, and methods |
| Implementation | Codify | Package the course as a usable Skill |
| Evaluation | Quality | Score package completeness and citation strength |

Current implementation includes basic package quality checks in `course_package.json`. Deeper evaluation should later include citation accuracy, exercise coverage, learner feedback, and source granularity.

## 2. Merrill's First Principles and Course Application

Merrill's First Principles of Instruction is a more directly actionable instructional design theory than ADDIE for deciding what a course Skill should help a learner do: problem-centered learning, activation, demonstration, application, and integration.

Primary paper: M. David Merrill, "First principles of instruction," Educational Technology Research and Development, 2002.

Reference: https://cir.nii.ac.jp/crid/1364233269496581120

Project mapping:

| Merrill principle | Project implication |
| --- | --- |
| Problem-centered | Extract cases, tasks, and real scenarios |
| Activation | Connect new lessons to prior concepts and prerequisites |
| Demonstration | Preserve screenshots, demos, examples, and teacher walkthroughs |
| Application | Generate checklists, prompts, learning checks, and templates when appropriate |
| Integration | Support study plans, reflection, and real-world application |

This is especially important for `mentor`, `consultant`, and `practitioner` roles.

## 3. Cognitive Apprenticeship

Cognitive apprenticeship focuses on making expert thinking visible: modeling, coaching, scaffolding, articulation, reflection, and exploration.

Canonical reference: Collins, Brown, and Newman, "Cognitive Apprenticeship." PhilPapers indexes the original journal metadata.

Reference: https://philpapers.org/rec/COLCA-2

This is the core meaning of "lineage" in this project. A course is not only a transcript. It also contains:

- how the teacher frames problems
- how concepts are defined
- which examples are selected
- which mistakes or boundaries are emphasized
- how methods are applied in context

The corresponding CoursePackage fields are:

```text
methods
cases
quotes
boundaries
study_paths
```

## 4. SECI Knowledge Conversion

The SECI model describes knowledge conversion between tacit and explicit forms: Socialization, Externalization, Combination, Internalization.

Canonical book: Nonaka and Takeuchi, *The Knowledge-Creating Company*, 1995. A scholarly review and operationalization discussion is available from Frontiers in Psychology.

Reference: https://www.frontiersin.org/articles/10.3389/fpsyg.2019.02730/full

In this project:

| SECI | Course distillation step |
| --- | --- |
| Socialization | Teacher demonstrates and explains inside the course |
| Externalization | Transcripts, screenshots, analyses, quotes |
| Combination | CoursePackage combines lessons, concepts, evidence, methods |
| Internalization | Study Coach and Practitioner skills help users review and apply |

`course_package.json` is the explicit knowledge asset produced by this conversion.

## 5. Multimedia Learning

Mayer's multimedia learning principles explain why learning from combined words and pictures can be stronger than words alone.

Canonical publisher reference: Richard Mayer, *Multimedia Learning*, Cambridge University Press.

Reference: https://www.cambridge.org/core/books/multimedia-learning/7A62F072A71289E1E262980CB026A3F9

This project keeps multiple course channels:

```text
audio/transcript      -> verbal channel
PPT/board/screenshots -> visual channel
visual analysis       -> semantic bridge
evidence map          -> source memory
```

That is why the pipeline includes video frame analysis and key screenshot extraction instead of only transcription.

## 6. Retrieval-Augmented Generation

RAG combines a generative model with retrieved external memory for knowledge-intensive tasks.

Primary paper: Lewis et al., "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks," NeurIPS 2020.

Reference: https://papers.neurips.cc/paper/2020/file/6b493230205f780e1bc26945df7481e5-Paper.pdf

Generated Skills should answer from packaged course memory:

```text
question
  -> SKILL.md behavior rules
  -> references/course_package.json
  -> references/evidence_map.json
  -> references/*.md
  -> grounded answer
```

The important rule is not "answer more"; it is "answer with the strongest available course evidence."

## 7. Bloom's Taxonomy and Skill Roles

Bloom's revised taxonomy is commonly used to describe levels of learning objectives: remember, understand, apply, analyze, evaluate, create.

Canonical works are Bloom's original taxonomy and Anderson & Krathwohl's 2001 revision. For a concise practical reference, use a university teaching center such as University of Florida's Center for Teaching Excellence.

Reference: https://teach.ufl.edu/resource-library/blooms-taxonomy/

Skill roles map to different cognitive depths:

| Role | Learning depth |
| --- | --- |
| `mentor` | understand, apply, evaluate |
| `expert` | understand, analyze |
| `consultant` | analyze, evaluate |
| `practitioner` | apply, create |
| `custom` | depends on requested workflow |

This is why one CoursePackage can produce several different Skills.

## 8. Architecture Implications

The theory leads to four engineering requirements:

1. Preserve evidence before summarizing.
2. Normalize course knowledge into a reusable package.
3. Separate course memory from Skill behavior.
4. Evaluate quality and source coverage.

Current implementation:

```text
raw course materials
  -> transcripts / visual analysis / screenshots
  -> course_distillation_*.md/json
  -> course_package.json
  -> role-specific Skill
```

## 9. Why These Sources

These sources are more appropriate than generic blog posts because they cover three necessary layers:

- **Instructional design**: ADDIE and Merrill explain how instruction is designed and turned into practice.
- **Expert knowledge transfer**: Cognitive apprenticeship and SECI explain why "teacher thinking" and tacit knowledge must be externalized, not merely summarized.
- **AI implementation**: Multimedia learning and RAG justify multimodal evidence and retrieval-grounded answering.

No single theory is sufficient. The project needs the stack because it is both a learning system and an AI retrieval system.

## 10. Known Gaps

The current project is useful, but not theoretically complete yet.

- Evaluation is still basic.
- Evidence is mostly file-level, not timestamp-level.
- Learning checks are intentionally optional and should only be generated for courses where they fit.
- Learner feedback does not yet flow back into CoursePackage.
- Multi-course concept alignment is still a future layer.

These gaps should guide future roadmap work.
