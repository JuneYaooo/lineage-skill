<div align="center">

# 师承.skill / Lineage Skill

**把任意课程蒸馏成可对话、可溯源、可复用的 AI Skill。**

面向 Codex / Claude Code / OpenClaw / Hermes / 自定义 Agent。  
把视频、音频、讲义、PDF、截图证据和已有笔记，沉淀成可检索、可引用、可继续复用的课程专家。

[![GitHub stars](https://img.shields.io/github/stars/JuneYaooo/lineage-skill?style=flat)](https://github.com/JuneYaooo/lineage-skill/stargazers)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](./LICENSE)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/)
[![Skill](https://img.shields.io/badge/AI%20Agent-Skill-orange.svg)](./SKILL.md)

```text
Course materials in, grounded expert skill out.
```

</div>

---

## 一句话

`lineage-skill` 不是课程总结器，而是课程知识系统生成器。

它会帮 Agent 把一门课拆成转录、视觉证据、逐课摘要、概念、案例、方法、金句、边界和 `CoursePackage`，再包装成不同用途的 Skill。

## 真实案例

[JuneYaooo/nihaixia](https://github.com/JuneYaooo/nihaixia) 是通过这类课程蒸馏流程沉淀出来的真实 Skill 项目，来源包含 **100GB+ 视频课程材料**，最终整理成可触发、可检索、可溯源的专门领域 Skill。

## 怎么安装

把下面这段话发给你的 Agent：

```text
帮我安装 lineage-skill：
https://github.com/JuneYaooo/lineage-skill
```

如果你的 Agent 支持读取安装说明，可以直接说：

```text
安装这个课程蒸馏 Skill，并告诉我需要配置哪些环境变量。
```

Agent 会根据自己的运行环境把仓库装成可用 Skill。具体执行细节在 [SKILL.md](./SKILL.md)，README 不展开命令手册。

## 怎么用

安装后直接用自然语言说需求。

### 蒸馏一门视频课

```text
帮我把这个视频课程目录蒸馏成一个 course-expert skill。
课程名叫 example-course，输出到 dist 目录。
```

### 带 PDF / 讲义一起蒸馏

```text
这个课程还有 PDF 讲义。请用 MinerU/OCR 解析 PDF，
再和视频转录、截图分析一起生成 CoursePackage 和 Skill。
```

### 从已有材料生成 Skill

```text
我已经有 transcripts、analysis、lesson_summaries 和 course_distillation 文件。
请直接构建 CoursePackage，并生成一个 course-expert,practitioner 组合模式的 Skill。
```

### 做学习教练

```text
把这门课生成 study-coach 模式。
我希望它能帮我按 7 天复习路径、回忆提示和薄弱点复盘来学习。
```

### 做证据档案

```text
把这门课生成 citation-archive 模式。
回答时必须优先给来源、课时、转录或截图证据。
```

## 能产出什么

| 产物 | 价值 |
| --- | --- |
| `CoursePackage` | 通用课程知识包，统一保存 lessons、concepts、topics、cases、methods、quotes、evidence、boundaries |
| `SKILL.md` | 告诉 Agent 什么时候触发、如何回答、如何引用、如何处理边界 |
| `references/` | 课程总览、课时索引、概念表、证据地图、金句、学习路径 |
| `search_course_notes.py` | 本地关键词检索课程资料 |
| mode-specific references | 根据模式生成学习计划、playbook、citation 规则、多课程索引等 |

## 支持哪些模式

同一门课可以生成不同用途的 Skill：

| Mode | 适合用途 |
| --- | --- |
| `course-expert` | 课程问答、概念解释、课时回查、来源引用 |
| `study-coach` | 学习计划、复习路径、回忆提示、反思提示 |
| `practitioner` | playbook、checklist、template、实操流程 |
| `citation-archive` | 强引用、原话检索、证据档案、可审计笔记 |
| `knowledge-base` | 多课程知识库、概念别名、跨课程主题图谱 |
| `domain-expert` | 多课程沉淀后的领域专家、方法库、案例库、边界规则 |

模式可以组合，例如：

```text
请生成 course-expert,practitioner 两种模式组合的 Skill。
```

详细设计见 [SKILL_MODES.md](./SKILL_MODES.md)。

## 当前能力

| 能力 | 状态 |
| --- | --- |
| 视频转录 | 已支持 |
| 视频画面分析与关键截图 | 已支持 |
| 课程级蒸馏 | 已支持 |
| CoursePackage 构建 | 已支持 |
| 多模式 Skill 生成 | 已支持 |
| PDF / MinerU OCR | 已接入主流水线，可选配置 |
| 本地关键词检索 | 已支持 |

## 需要配置什么

复制 `.env.example` 为 `.env`，只填自己实际使用的服务。

常用配置：

| 场景 | 变量 |
| --- | --- |
| 音频转录 | `AUDIO_TRANSCRIBE_API_KEY`, `AUDIO_TRANSCRIBE_BASE_URL`, `AUDIO_TRANSCRIBE_MODEL` |
| 视觉分析 | `LINEAGE_VISION_API_KEY`, `LINEAGE_VISION_BASE_URL`, `LINEAGE_VISION_MODEL` |
| 文本蒸馏 | `LINEAGE_TEXT_API_KEY`, `LINEAGE_TEXT_BASE_URL`, `LINEAGE_TEXT_MODEL` |
| PDF / OCR | `MINERU_API_TOKEN`, `MINERU_API_BASE`, `MINERU_MODEL_VERSION` |

安全原则：

- `.env` 不入库
- 不写死真实 token
- 不写死私有目录
- 不写死历史课程内容
- 转录、截图、OCR、蒸馏产物默认被 `.gitignore` 忽略

## 为什么可信

方法论来自 C5 + Evaluate：

```text
Capture  →  Cite  →  Compress  →  Connect  →  Codify  →  Evaluate
采集        溯源      压缩          关联         技能化      评估
```

理论基础结合教学设计、认知学徒制、知识管理、多媒体学习和 RAG。详见 [THEORETICAL_FOUNDATION.md](./THEORETICAL_FOUNDATION.md)。

## 适合谁

| 场景 | 适合程度 |
| --- | --- |
| 把一门长视频课变成可问答 Skill | 很适合 |
| 做课程复习、课时回查、概念整理 | 很适合 |
| 沉淀一个老师或课程体系的方法论 | 很适合 |
| 做带来源的课程知识库 | 适合 |
| 多课程合并成领域专家 | 适合，需准备多课程材料 |
| 只想生成一篇普通课程总结 | 可以，但不是本项目的主要价值 |

## 项目文档

- [SKILL.md](./SKILL.md) — Agent 使用入口和执行规则
- [METHODOLOGY.md](./METHODOLOGY.md) — C5 + Evaluate 方法论
- [THEORETICAL_FOUNDATION.md](./THEORETICAL_FOUNDATION.md) — 理论基础
- [SKILL_MODES.md](./SKILL_MODES.md) — 多模式 Skill 设计
- [ROADMAP.md](./ROADMAP.md) — 后续路线图

## License

Apache License 2.0. See [LICENSE](./LICENSE).
