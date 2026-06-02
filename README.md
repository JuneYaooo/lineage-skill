<div align="center">

# 师承.skill / Lineage Skill

**把一整套课，炼成一个能被 Agent 调用的专家 Skill。**

不是只做课程总结，而是把视频、PDF、板书、截图、转录和笔记整理成一套可追问、可检索、可溯源、可复用的知识系统。

面向 Codex / Claude Code / OpenClaw / Hermes / 自定义 Agent。

[![License](https://img.shields.io/badge/license-PolyForm%20Noncommercial%201.0.0-orange.svg)](./LICENSE)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/)
[![Skill](https://img.shields.io/badge/AI%20Agent-Skill-orange.svg)](./SKILL.md)

```text
Course videos / PDFs / notes
  -> transcripts + OCR + visual evidence
  -> CoursePackage
  -> grounded expert Skill
```

</div>

---

## 你会得到什么

如果你手上有一套视频课、训练营、讲座、PDF 讲义或长期学习笔记，`lineage-skill` 可以把它变成一个专门服务这套课程的 Agent Skill。

它能帮你得到：

- 一个能回答课程问题的专家助手：问“老师在哪一课讲过这个概念”，它会优先回到课程材料里找。
- 一套可复习的课程索引：课时、概念、主题、案例、方法、金句、学习路径都能被整理出来。
- 一张证据地图：转录、截图、OCR 文档和课程蒸馏结果会被保留下来，回答时能尽量指出来源。
- 一组可复用的实战材料：playbook、checklist、template、案例库和边界规则可以从课程方法里生成。
- 一个能装进 Agent 的 Skill：生成后的 `SKILL.md`、`references/` 和检索脚本可以被 Codex 等 Agent 调用。

一句话：**把“我学过一套课”变成“我有一个能随时调用的课程专家”。**

## 适合谁

适合这些场景：

- 你有几十小时甚至上百小时视频课，想把它沉淀成可复习、可提问的知识库。
- 你不想只要摘要，而是希望保留“这句话、这个图、这个案例来自哪里”。
- 你想把课程里的方法变成可执行的流程、模板、清单和判断规则。
- 你正在为某个领域构建长期可复用的个人或团队知识 Skill。
- 你已经有 transcripts、OCR、课程笔记或蒸馏结果，想直接打包成 Agent Skill。

## 它怎么工作

```text
1. Capture  采集证据
   视频转录、画面分析、关键截图、PDF/OCR、已有笔记

2. Cite     保留来源
   记录 transcript、analysis、screenshot、document、distillation 文件

3. Compress 课程蒸馏
   提炼课时摘要、概念、主题、案例、方法、金句和学习路径

4. Connect  结构化
   生成标准 CoursePackage，作为课程知识的中间层

5. Codify   技能化
   生成可被 Agent 调用的 mode-specific Skill

6. Evaluate 评估边界
   标记缺失字段、证据强度、适用范围和不确定内容
```

核心中间层是 `course_package.json`。它让课程内容先被标准化，再根据用途生成不同类型的 Skill。

## 快速开始

### 方式一：让 Agent 安装并使用

把这段话发给你的 Agent：

```text
帮我安装 lineage-skill：
https://github.com/JuneYaooo/lineage-skill

安装后请检查需要配置的环境变量，并告诉我下一步怎么把我的课程目录生成 Skill。
```

然后直接描述你的材料：

```text
我有一个视频课程目录和一批 PDF 讲义。
请把它们蒸馏成 course-expert,practitioner 组合模式的 Skill。
要求保留来源，能回答课程问题，也能输出实操清单。
```

### 方式二：本地跑完整视频课程流水线

```bash
pip install -r requirements.txt

python scripts/run_course_pipeline.py \
  --input-dir <course-video-dir> \
  --course-name <course-name> \
  --skill-name <skill-name> \
  --mode course-expert \
  --output-dir ./dist
```

包含 PDF / OCR：

```bash
python scripts/run_course_pipeline.py \
  --input-dir <course-video-dir> \
  --documents-input <pdf-or-pdf-dir> \
  --course-name <course-name> \
  --skill-name <skill-name> \
  --mode course-expert,practitioner \
  --output-dir ./dist
```

### 方式三：已有课程材料，直接打包 Skill

如果你已经有 `transcripts/`、`analysis/`、`lesson_summaries.json`、`course_distillation_*.md/json` 等文件，可以跳过采集和蒸馏：

```bash
python scripts/build_course_package.py \
  --course-name <course-name> \
  --source-dir <course-dir>

python scripts/build_course_skill.py \
  --course-name <course-name> \
  --skill-name <skill-name> \
  --mode course-expert,practitioner \
  --source-dir <course-dir> \
  --output-dir ./dist
```

## 生成后的样子

```text
<generated-skill>/
├── SKILL.md
├── lineage_manifest.json
├── references/
│   ├── course_package.json
│   ├── course_digest.md
│   ├── full_transcript.md
│   ├── lesson_index.json
│   ├── concept_glossary.md
│   ├── evidence_map.json
│   ├── quote_index.md
│   └── study_paths.md
└── scripts/
    └── search_course_notes.py
```

`SKILL.md` 告诉 Agent 什么时候触发、如何回答、如何引用、如何处理边界。`references/` 保存课程索引和证据材料。`search_course_notes.py` 提供轻量本地关键词检索。

## Skill 模式

同一份 CoursePackage 可以生成不同用途的 Skill，也可以组合：

```text
course-expert,practitioner
```

| Mode | 适合什么 |
| --- | --- |
| `course-expert` | 课程问答、概念解释、课时回查、来源引用 |
| `study-coach` | 学习计划、复习路径、回忆提示、反思提示 |
| `practitioner` | playbook、checklist、template、实操流程 |
| `citation-archive` | 强引用、原话检索、证据档案、可审计笔记 |
| `knowledge-base` | 面向多课程组织的目录、概念别名、主题索引 |
| `domain-expert` | 面向领域沉淀的方法库、案例库、边界规则 |

说明：`knowledge-base` 和 `domain-expert` 当前可以生成对应 Skill 结构和占位引用文件；自动多课程合并、跨课程语义检索仍在路线图中。

## 当前能力与边界

| 能力 | 当前状态 |
| --- | --- |
| 视频转录 | 支持 `.mp4` 课程目录，依赖 OpenAI-compatible transcription endpoint |
| 视频画面分析 | 支持分片分析、关键截图、PPT/板书/软件界面提取 |
| PDF / MinerU OCR | 已接入主流水线，可把 OCR 文档纳入证据层 |
| 课程级蒸馏 | 支持 LLM 蒸馏，也支持本地抽取式 fallback |
| CoursePackage 构建 | 支持从蒸馏结果和已有材料生成标准知识包 |
| 多模式 Skill 生成 | 支持 `course-expert`、`study-coach`、`practitioner` 等模式 |
| 本地关键词检索 | 支持生成轻量 `search_course_notes.py` |

当前边界：

- 证据地图默认还是文件级，时间点级、主题级证据仍需增强。
- OCR 结果可以进入 CoursePackage，但 OCR 到概念/案例/方法的精细映射仍在改进。
- 语义检索、向量索引和自动多课程合并仍在路线图中。
- 高风险领域必须保留课程边界，不应把模型自己的泛化当成课程原意。

## 配置与安全

复制 `.env.example` 为 `.env`，只填实际使用的服务：

- 音频转录：`AUDIO_TRANSCRIBE_*`
- 视觉分析：`LINEAGE_VISION_*`
- 文本蒸馏：`LINEAGE_TEXT_*`
- PDF / OCR：`MINERU_*`

安全原则：

- `.env` 不入库
- 不写死真实 token
- 不写死私有目录
- 不写死历史课程内容
- 转录、截图、OCR、蒸馏产物默认被 `.gitignore` 忽略

## 真实案例

[JuneYaooo/nihaixia](https://github.com/JuneYaooo/nihaixia) 是通过这类课程蒸馏流程沉淀出来的真实 Skill 项目，来源包含 **100GB+ 视频课程材料**，最终整理成可触发、可检索、可溯源的专门领域 Skill。

## 文档

- [SKILL.md](./SKILL.md) — Agent 使用入口和执行规则
- [docs/capabilities.md](./docs/capabilities.md) — 当前能力、边界和路线
- [docs/configuration.md](./docs/configuration.md) — 环境变量说明
- [docs/mineru-ocr.md](./docs/mineru-ocr.md) — PDF / MinerU / OCR 工作流
- [docs/course-package.md](./docs/course-package.md) — CoursePackage 结构
- [METHODOLOGY.md](./METHODOLOGY.md) — C5 + Evaluate 方法论
- [THEORETICAL_FOUNDATION.md](./THEORETICAL_FOUNDATION.md) — 理论基础
- [SKILL_MODES.md](./SKILL_MODES.md) — 多模式 Skill 设计
- [ROADMAP.md](./ROADMAP.md) — 后续路线图

## License

This project is licensed under the [PolyForm Noncommercial License 1.0.0](./LICENSE).

Noncommercial use is permitted. Commercial use requires separate authorization.
