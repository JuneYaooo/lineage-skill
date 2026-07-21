<div align="center">

<img src="./docs/img/lineage-apprenticeship-hero.svg" alt="Lineage Skill：师承，不是代做" width="100%">

# Lineage Skill

**把课程变成会带你练、会纠错、最终让你独立完成的学习 Skill**

它不只总结内容，还会保留出处、整理老师解决问题的方法、设计循序练习，并检查你能不能在真实场景中独立使用。

[![License](https://img.shields.io/badge/license-PolyForm%20Noncommercial%201.0.0-C46B35.svg)](./LICENSE)

[English](./README.en.md) · [安装说明](./docs/install.md) · [更新记录](./CHANGELOG.md) · [Skill 入口](./SKILL.md)

</div>

## 它解决什么

普通课程摘要能回答“老师讲了什么”，但不能证明学习者会做。普通 AI 导师又很容易直接代做，让“听懂”替代能力。

Lineage Skill 1.0 把“有材料”变成“真的会用”：

1. 保存原文位置、转录、讲义和关键画面，让每个重要结论都能回查出处。
2. 整理老师遇到问题时先看什么、怎么判断、何时使用或放弃一种方法。
3. 把方法拆成循序渐进的练习、明确的评价标准和出师要求。
4. 学习时先让你动手，再针对具体问题给提示和反馈，并在新场景里验证你是否真的掌握。

最终目标不是让你永久依赖 AI 导师，而是形成一套有来源、经过实践验证、属于你自己的可复用方法。

## 四层架构

<img src="./docs/img/lineage-system-architecture.svg" alt="Lineage Skill 四层架构" width="100%">

| 层 | 包含什么 | 对用户的价值 |
| --- | --- | --- |
| 来源证据 | 原文位置、转录、讲义、关键画面 | 知道每个重要结论从哪里来 |
| 老师方法 | 判断线索、决策规则、完整示范、适用边界 | 学到老师怎么解决问题，而不只是记结论 |
| 带教过程 | 摸底、练习、提示、反馈、复习、换场景应用 | 让“听懂”逐步变成“会做” |
| 个人成长 | 每次尝试、常见错误、复习计划、现实结果 | 私下保存成长证据，最终沉淀成自己的方法 |

老师包与生成 Skill 是只读、可版本化资产；学习者状态是外置、私有、可追加的数据。重新生成或删除 Skill 不会删除个人尝试记录。

## 师承生命周期

<img src="./docs/img/apprenticeship-lifecycle.svg" alt="Lineage Skill 师承生命周期" width="100%">

完整生命周期是：

```text
拜师定向 → 师傅示范 → 临帖模仿 → 对练纠偏
→ 独立实战 → 跨境迁移 → 出师评测 → 持续精进
```

系统默认这样带你练：

- 查原话：直接回查证据，不强迫你做练习，也不把一次查询算成“已经掌握”。
- 真学习：先收集预测、判断、解释或产物，再展示反馈。
- 给反馈：只聚焦当前最关键的问题，对照明确标准，给刚好够用的提示。
- 要修订：保存第一次尝试、反馈、第二次尝试与反思，而不是只留下最终答案。
- 做巩固：安排平行题、延迟检索、交错练习和变化约束的新场景。
- 逐步放手：随着你越来越熟练，逐渐减少模板、提示和导师介入。
- 检查出师：只有在你能无提示完成、隔一段时间仍会、换场景也能用并知道边界时，才算真正掌握。

## 给开发者的核心数据结构

### 课程知识包（CoursePackage 1.0）

它把课程出处、章节、概念、方法、案例和练习整理到一个统一文件中。1.0 为这些内容分配稳定 ID，方便更新后继续追踪旧引用和学习记录。

```text
course_package.json
├── sources / lessons / evidence / claims
├── concepts / methods / cases / boundaries
├── diagnostics / workflows / rubrics / templates
├── transfer_rules / failure_modes / learning_checks
└── quality.coverage / integrity / mentor_readiness
```

旧 0.1/0.x 包可显式迁移，默认不覆盖原文件：

```bash
python scripts/migrate_course_package.py path/to/course_package.json
```

需要原地迁移时会先创建 `.bak`：

```bash
python scripts/migrate_course_package.py path/to/course_package.json --in-place
```

迁移报告会保存旧 ID → 1.0 稳定 ID 的 `id_map`，供外部 learner state、复习队列和历史 episode 迁移使用。

### 老师怎么判断问题（TeacherModel 1.0）

这部分不复制老师人格或意识，只整理材料中有证据支持的做事方法：

- 首先注意哪些信号；
- 怎样给问题定性、追问和排除干扰；
- 何时选择或拒绝一种方法；
- 如何完整示范与自检；
- 如何识别典型错误并纠偏；
- 哪些背景不可复制，哪些场景不适用；
- 什么证据表明学习者可以独立。

普通讲解推断出的“隐性判断”不能标为高置信。没有示范、点评或问答证据时，系统会报告 `missing_teacher_evidence`。

### 能力路线、练习库和评测库

- 能力路线（CapabilityGraph）：说明先练什么、后练什么，以及哪些能力互相依赖。
- 练习库（PracticeBank）：为每项能力准备可执行任务、期望产物、逐级提示、常见错误和明确评价标准。
- 评测库（AssessmentBank）：用新题和新场景检查你能否回忆、产出、迁移、识别边界并达到出师标准。

一次成功最多让能力前进一个证据状态：

```text
unseen → recognized → reconstructed → applied_with_support
→ applied_independently → transferred → retained → graduated
```

### 可运行的带教方案（MentorPackage 1.0）

它把老师方法、学习顺序、练习、反馈标准和出师要求组合成一套可运行的带教方案。只有材料足以支持完整示范、练习和评测时，系统才会开启完整带教模式。

材料较薄时会显式降级到 `guided` 或 `none`，并生成 `mentor_readiness_audit.json/.md`；不会用空 playbook 冒充完整导师。

## 支持的输入

| 输入 | 处理 | 主要产物 |
| --- | --- | --- |
| `.mp4` / 视频 | 提取音频、转录、视频视觉理解、模型精选关键帧 | `transcripts/`、`analysis/`、`keyframe_selection/` |
| `.mp3` / `.wav` / `.m4a` 等 | 长音频分段、失败段递归拆分、转录 | `transcripts/` |
| PDF / 扫描讲义 | MinerU/OCR 或复用已有 OCR | `documents/` |
| Markdown / TXT / 书籍章节 / 笔记 | 分块、证据卡、课程综合 | `text_sources/`、`text_distillation/` |
| 旧 CoursePackage | 0.x → 1.0 显式迁移 | `course_package.v1.json`、迁移报告 |
| 多课程包 | 逐包迁移、namespace-safe 合并、保留冲突 | combined CoursePackage 1.0 |

模型选帧使用“场景变化 + 密度下限”建立候选池，再用视觉模型选择证据帧。等间隔只用于候选生成，不被当作最终关键帧规则。

## 快速开始

### 安装

```bash
git clone https://github.com/JuneYaooo/lineage-skill.git
cd lineage-skill
python -m pip install -r requirements.txt
```

处理媒体还需要 `ffmpeg` 和 `ffprobe`。

### 配置 provider

复制 `.env.example`，只填写实际会使用的 provider。不要提交 `.env` 或真实 API key。

```bash
AUDIO_TRANSCRIBE_API_KEY=
AUDIO_TRANSCRIBE_BASE_URL=
AUDIO_TRANSCRIBE_MODEL=

LINEAGE_VISION_API_KEY=
LINEAGE_VISION_BASE_URL=
LINEAGE_VISION_MODEL=

LINEAGE_TEXT_API_KEY=
LINEAGE_TEXT_BASE_URL=
LINEAGE_TEXT_MODEL=

MINERU_API_TOKEN=
```

### 一次性生成完整师承 Skill

视频 + PDF + 笔记：

```bash
python scripts/run_course_pipeline.py \
  --input-dir /path/to/course-media \
  --documents-input /path/to/handouts \
  --notes-input /path/to/notes \
  --course-name product-discovery \
  --skill-name product-discovery-mentor-lineage \
  --mode mentor,practitioner \
  --apprenticeship full \
  --practice-depth deep \
  --learner-state external \
  --output-dir ./dist
```

纯文字 / 书籍：

```bash
DISTILL_USE_LLM=0 python scripts/run_course_pipeline.py \
  --text-input /path/to/book-or-notes \
  --course-name evidence-first-delivery \
  --mode mentor \
  --apprenticeship full \
  --text-no-llm \
  --output-dir ./dist
```

本地抽取适合可识别标签的材料；更复杂的隐含关系与结构化输出建议配置长上下文文本模型，并通过 readiness audit 人工复核高影响规则。

## 最终生成结构

```text
{course}-mentor-lineage/
├── SKILL.md
├── agents/
├── lineage_manifest.json
├── mentor_manifest.json
├── references/
│   ├── course_package.json
│   ├── teacher_model.json
│   ├── capability_graph.json
│   ├── practice_bank.json
│   ├── assessment_bank.json
│   ├── mentor_package.json
│   ├── mentor_protocol.md
│   ├── graduation_policy.json
│   ├── mentor_readiness_audit.json
│   ├── schemas/
│   ├── okf/
│   └── source evidence when available
├── scripts/
│   ├── search_course_notes.py
│   ├── fetch_course_evidence.py
│   ├── initialize_apprenticeship.py
│   ├── record_practice_episode.py
│   ├── rebuild_mastery_state.py
│   ├── select_next_practice.py
│   ├── schedule_retrieval.py
│   ├── validate_learner_state.py
│   └── build_personal_skill_candidate.py
└── assets/
    ├── learning_contract.template.json
    ├── practice_episode.template.json
    └── graduation_report.template.md
```

生成过程使用临时目录，验证通过后再原子替换目标 Skill。密集关键帧候选、真实 learner state 和私有原始材料不会被默认打包。

只有在确认拥有材料分发权限并明确需要离线原文时，才使用 `--include-source-artifacts`；它会选择性加入转录、OCR、分析、文本源和模型精选关键帧。默认模式只保留结构化知识、稳定证据 ID 和脱敏后的 `withheld://` 引用。

## 个人学习记录放在哪里

你的练习、错误、复习安排和现实结果保存在你选择的外部私有目录，而不是写进课程 Skill：

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

每次练习记录只追加、不覆盖；掌握情况可以随时从历史练习重新计算。只有经过多次成功、不同场景、无提示完成和失败复盘后，系统才会建议沉淀为个人方法，而且必须由用户明确批准。

外部 host 通过版本化 JSON contract 交换必要状态，不直接 import Lineage 内部 Python，也不能修改不可变老师包。详见 [External learner store contract](./references/external-learner-store-contract.md)。

## 角色与请求路由

| 角色 | 用途 |
| --- | --- |
| `mentor` | 完整或 guided 师承：诊断、练习、反馈、检索、迁移、出师 |
| `expert` | 课程问答、原意回查、概念解释和证据引用 |
| `consultant` | 基于课程方法的情境诊断、权衡与建议 |
| `practitioner` | playbook、checklist、template、流程与工作产物 |
| `custom` | 用户定义的来源受限工作流 |

角色可以组合。scope、evidence strictness、apprenticeship 和 learner state 是独立维度，不伪装成角色。

## 验证

```bash
python -m pytest -q -c /dev/null --rootdir=. -o cache_dir=.pytest_cache tests
python scripts/validate_lineage_package.py --package path/to/course_package.json
python scripts/validate_mentor_package.py --package path/to/mentor_package.json
python scripts/validate_generated_skill.py --skill-dir path/to/generated-skill
python "${CODEX_HOME:-$HOME/.codex}/skills/.system/skill-creator/scripts/quick_validate.py" .
git diff --check
```

完整流水线会分别告诉你：材料是否够完整、是否足以进行完整带教、生成的 Skill 是否能正常运行。严格模式会拒绝证据不足的完整带教；自动模式会明确降级为引导学习或仅做资料查询。

## 来源、安全与版权

- `[老师原意]`、`[课程证据综合]`、`[Mentor 推断]`、`[你的假设]` 和 `[你的现实证据]` 必须分层。
- 多位老师冲突时保留各自条件、证据和来源，不生成虚假统一意见。
- 不声称复制老师意识、人格或完整思维。
- 医学、法律、金融、投资等高风险材料保持教育性和来源边界；课程出师不是职业资质。
- 不默认提交转录、截图、OCR、课程视频、learner state 或受保护全文。
- Personal Skill 只保存程序、个人改造、必要证据指针和已知失败。

## 已有示例

[nihaisha-tcm](https://github.com/JuneYaooo/nihaisha-tcm) 使用本项目的证据蒸馏路线组织 100GB+ 中医课程材料，支持课程检索、方证穴位学习、板书证据与专门领域 Skill。

## 致谢

- [Datawhale](https://github.com/datawhalechina) — AI 教育、开源课程与学习者社区实践。
- [rfeng1016](https://github.com/rfeng1016) — 对 OKF 渐进知识包方向的建议。
- [LINUX DO](https://linux.do/) — 中文开发者社区的讨论与反馈。

## License

本项目采用 [PolyForm Noncommercial License 1.0.0](./LICENSE)。商业使用或合作请联系 <juneyaooo@gmail.com>。
