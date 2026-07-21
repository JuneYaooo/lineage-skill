<div align="center">

# 师承.skill / Lineage Skill

**把一整套高密度课程、书籍或长文档，蒸馏成可溯源、可迁移、可产出的私人方法系统。**

从视频、书籍、讲义、板书、转录和笔记里抽取判断框架、案例经验、操作流程和质量标准，
让 Agent 带着老师的方法参与你的学习、决策和工作产出。

面向 Codex / Claude Code / OpenClaw / Hermes / 自定义 Agent。

[![License](https://img.shields.io/badge/license-PolyForm%20Noncommercial%201.0.0-orange.svg)](./LICENSE)
[![Skill](https://img.shields.io/badge/AI%20Agent-Skill-orange.svg)](./SKILL.md)
[![BundleDex](https://bundledex.net/badge/lineage-skill.svg)](https://bundledex.net/bundles/lineage-skill/)

[English](./README.en.md)

</div>

---

## 2026-06-24 更新

这次更新把 `lineage-skill` 从“课程导师生成器”进一步补强为“课程/书籍/长文档方法系统生成器”：

- **支持书籍和长文档**：书籍、章节 Markdown、OCR 文本和课程材料都可以走同一套蒸馏流程。
- **新增能力资产抽取**：除了概念、方法、案例、引用，现在会抽取 `diagnostics`、`workflows`、`rubrics`、`templates`、`transfer_rules`、`failure_modes`。
- **新增 OKF 兼容知识包**：生成 Skill 时会在 `references/okf/` 输出 Markdown + frontmatter 的渐进式知识目录，便于人读、Agent 逐层读取、跨工具交换和图谱化。
- **增强溯源链路**：新增 `scripts/fetch_course_evidence.py`，可以通过 `chunk_id` 或 `card_id` 回到原始 source chunk 和相关证据卡。
- **多课程合并保留能力字段**：跨课程包会继续保留来源边界，避免把不同课程/书籍的判断压平成一个无来源结论。

### “能力资产抽取”是什么意思？

普通摘要回答的是“这本书/这门课讲了什么”。能力资产抽取更进一步，目标是让 Agent 能调用书或课背后的方法来做事：

| 字段 | 含义 | 用途 |
| --- | --- | --- |
| `diagnostics` | 诊断规则 | 判断问题卡在哪里，例如目标不清、资源不足、反馈缺失或执行断裂。 |
| `workflows` | 执行流程 | 把老师/作者的方法整理成可以照着做的步骤。 |
| `rubrics` | 质量标准 | 判断一个方案、文章、流程或决策结果好不好的检查标准。 |
| `templates` | 模板资产 | 可复用的表格、话术、结构、清单或工作纸。 |
| `transfer_rules` | 迁移规则 | 指导如何把书中案例或课程方法迁移到你的真实场景。 |
| `failure_modes` | 失效条件 / 常见误用 | 说明什么时候不能用、怎么用会错，以及哪些条件缺失时要谨慎。 |

因此，蒸馏后的 Skill 不只是能复述内容，而是能辅助诊断、设计流程、产出模板、检查质量、迁移应用，并标出误用风险。

## 这是什么

`lineage-skill` 是一个给 Agent 使用的课程/书籍蒸馏 Skill。它把一整套视频课、训练营、讲座、书籍、PDF 讲义、板书、截图、转录和学习笔记，转化成一个可安装、可调用、可溯源的导师或方法 Skill。

它不是“把课总结一下”，而是把课程沉淀成一套能长期使用的知识资产：

- 保留来源原意：重要结论尽量能回到课时、章节、原文、截图或讲义。
- 重建材料结构：把分散的视频、书籍章节、讲义、案例和笔记整理成概念、方法、章节/课时索引和证据图谱。
- 生成可用导师：让 Agent 基于这套材料回答、追问、复习、演练、回查出处。
- 产出工作资产：把老师或作者的方法变成 checklist、playbook、template、方案初稿和质检规则。

一句话：**把“我买过、看过、学过一套课/一本书”变成“我拥有一个能随时陪练、指导和产出的私人方法系统”。**

## 蒸馏后的核心价值

一套课或一本好书真正贵的地方，通常不在“知识点列表”，而在老师/作者长期积累出来的判断框架、问题分解方式、案例经验和隐性标准。

`lineage-skill` 的目标是把这些东西从几十小时、上百小时的视频里抽出来，变成 Agent 可以反复调用的能力：

| 价值 | 课程/书籍蒸馏后变成什么 |
| --- | --- |
| **从内容消费变成方法资产** | 不只是“我看过这套课/这本书”，而是沉淀出概念体系、判断标准、操作流程、案例库和模板库。 |
| **从一次学习变成长期陪练** | Agent 可以按你的学习进度追问、复盘、找薄弱点，把材料变成持续训练系统。 |
| **从模糊记忆变成可溯源知识库** | 重要结论可以回到课时、原文、截图或讲义，避免把自己的理解误当成老师原意。 |
| **从听懂道理变成实际产出** | 把老师的方法迁移到真实场景，生成方案、检查方案、设计流程、写模板、做决策辅助。 |

换句话说，它解决的不是“帮我总结一下这门课/这本书”，而是：

> 我怎样把一套高密度课程、一本书或一组长文档，变成一个能长期参与学习、判断和工作的私人方法系统？

## 典型产出场景

| 场景 | 你真正想要的结果 | 示例 |
| --- | --- | --- |
| **学透一套课/一本书** | 找出主线、难点、误区和薄弱环节，让 Agent 像导师一样持续追问 | “我学完前 5 课/前 3 章了，按作者体系检查我哪里没理解到位。” |
| **查回课程原意** | 快速定位某个观点、案例、方法出自哪里，有没有原文或截图依据 | “这个判断是不是老师讲过？如果讲过，在哪一课、原话大意是什么？” |
| **迁移老师/作者的方法** | 把课程或书里的框架用到你的具体问题，而不是停留在复述概念 | “按这套材料的方法，分析我这个业务场景，指出关键判断和缺口。” |
| **生产可复用资产** | 生成以后能反复使用的 checklist、playbook、template、方案草稿和质检标准 | “把老师的方法整理成我每次做项目都能用的流程和检查表。” |

## 可选角色

你可以直接告诉 Agent 想要哪种用途，也可以让它自己判断。课程范围、证据严格度、是否记录学习进度是另外的维度，不和角色混在一起。

| 角色 | 适合什么 |
| --- | --- |
| `mentor` | 学习内化：追问、复盘、纠偏、阶段计划，把课程变成长期训练系统 |
| `expert` | 证据回查：概念解释、课时定位、观点核对、来源引用 |
| `consultant` | 情境决策：把老师的方法迁移到你的真实问题，给出判断、风险和建议 |
| `practitioner` | 资产生产：沉淀 playbook、checklist、template、流程和质检规则 |
| `custom` | 自定义工作流：按你的具体业务、研究、写作或训练流程生成 Skill |

其他维度：

| 维度 | 可选项 |
| --- | --- |
| 材料范围 | 单课/单书、多来源保留边界、多来源融合 |
| 证据策略 | 标准引用、严格溯源 |
| 学习进度 | 不记录、记录进度并调整计划 |

也可以组合使用：

```text
请把这套课/这本书整理成 mentor,practitioner 角色。
既能像导师一样陪我学习，也能输出实操清单。
```

## 用 lineage-skill 蒸馏出的项目

以下项目是基于 `lineage-skill` 流水线，从真实课程材料蒸馏出的专门领域 Skill。

| 项目 | 简介 | 展示 | Stars |
| --- | --- | --- | --- |
| [nihaisha-tcm](https://github.com/JuneYaooo/nihaisha-tcm) | 倪海厦中医课程资料的 Agent Skill。来源包含 **100GB+ 视频课程材料**，最终沉淀成可触发、可检索、可溯源的专门领域 Skill，支持课程检索、方证穴位辨析、学习笔记整理与板书截图证据索引。 | ![nihaisha-tcm preview](https://opengraph.githubassets.com/lineage-skill/JuneYaooo/nihaisha-tcm) | ![GitHub Repo stars](https://img.shields.io/github/stars/JuneYaooo/nihaisha-tcm?style=social) |

## 它如何实现这些价值

这些价值不是靠一次性总结实现的，而是靠一条保留证据、压缩结构、再固化为能力的蒸馏路径。

![lineage-skill 方法论价值路径](./docs/img/lineage-methodology-value-zh.png)

`lineage-skill` 按 `Capture -> Cite -> Compress -> Connect -> Codify -> Evaluate` 工作：先保留证据，再压缩蒸馏；先区分课时、讲义、板书、案例和笔记，再整理成概念、方法、步骤、模板和导师能力。

- **Capture**：采集视频、音频、讲义、截图、OCR、转录和笔记。
- **Cite**：保留课时、时间戳、原文、截图和文档来源。
- **Compress**：把长材料压缩成结构化摘要和课程脉络。
- **Connect**：连接概念、案例、方法、课时和使用场景。
- **Codify**：把老师的方法固化成流程、清单、模板和判断标准。
- **Evaluate**：用课程标准做复盘、质检、追问和应用检查。

## 它具备哪些能力

这套 Skill 本身就包含课程/书籍蒸馏所需的主要流水线。你不需要自己设计“怎么把视频课或书籍变成方法导师”，只需要提供源材料，并配置合适的模型接口。

| 能力 | 它会做什么 | 产物 |
| --- | --- | --- |
| 视频 / 音频转录 | 从 `.mp4` 提取音频，或直接转录 `.mp3`、`.wav`、`.m4a` 等音频；长音频会自动分段 | `transcripts/*.json` |
| 视频视觉理解 | 调用视觉模型分析 PPT、板书、软件界面、图表、动作示范和关键画面 | `analysis/*_analysis.md` |
| 大视频处理 | 对大视频压缩、按时间分片，降低模型上传和理解压力 | 分片分析结果 |
| 模型精选关键帧 | 先生成密集候选帧，再让多模态视觉模型从 contact sheet 中选择真正有证据价值的关键帧；等间隔只作为候选池，不作为最终证据规则 | `keyframe_selection/`、`keyframes_model_selected/` |
| PDF / 文档解析 | 接入 MinerU 等 OCR / 文档解析结果，把扫描 PDF、图片 PDF、讲义纳入证据 | `documents/`、`mineru_supplement.md` |
| 纯文字/书籍蒸馏 | 把 Markdown、TXT、OCR Markdown、手工笔记、书籍章节和讲义分块成可溯源证据卡片，再合并进课程/书籍结构 | `text_sources/`、`text_distillation/evidence_cards.jsonl` |
| 能力资产抽取 | 从书和课中抽取诊断规则、执行流程、质量标准、模板、迁移规则和失效条件 | `course_package.json` 中的 capability fields |
| 课程/书籍蒸馏 | 整合转录、画面分析、模型精选关键帧、OCR 和笔记，提炼概念、方法、案例、引用 | `course_distillation_*.md/json` |
| CoursePackage 构建 | 把蒸馏结果变成统一结构，保留 evidence map、lesson index 和质量信息 | `course_package.json` |
| OKF 知识包导出 | 把结构化能力资产导出成 Markdown + frontmatter 的渐进式知识目录 | `references/okf/` |
| 多课程合并 | 把多个课程包合成一个跨课程 Skill 的输入 | combined `course_package.json` |
| 专属导师 Skill 生成 | 默认生成 `mentor`，也可按用途生成其他角色 | 可安装/调用的课程 Skill |
| 断点与进度记录 | 记录每个阶段状态、已有产物和下一步，可从已有产物继续 | `lineage_progress.json` |
| 多课程目录索引 | 扫描多个课程工作区和已生成 Skill，形成总目录 | `course_catalog.json` |

## 怎么使用

### 1. 让 Agent 安装这个 Skill

把这段话发给你的 Agent：

```text
请安装这个 Skill：
https://raw.githubusercontent.com/JuneYaooo/lineage-skill/main/docs/install.md

安装后请告诉我可以怎样把我的课程/书籍材料整理成方法专家。
```

### 2. 配置需要的材料、工具和模型接口

你只需要先准备课程/书籍材料、本地基础工具和模型接口。常用配置直接看这一节即可；`docs/install.md` 只保留给 Agent 自动安装用。

#### 2.1 课程/书籍材料

把材料放在一个本地目录里即可，不要求提前整理成固定格式：

- 视频：`.mp4`
- 音频：`.mp3`、`.wav`、`.m4a`、`.aac`、`.flac`、`.ogg`、`.opus`
- 文档：PDF、讲义、截图、OCR Markdown
- 已有文本：转录、课程笔记、书籍章节 Markdown、学习总结、案例整理

如果你已经有转录、OCR 文档或笔记，可以跳过重新转录和视觉分析，直接进入课程蒸馏和 Skill 生成。

#### 2.2 本地工具

基础依赖：

```bash
git
python3
pip
```

处理视频或原始音频时还需要：

```bash
ffmpeg
ffprobe
```

macOS 可以用：

```bash
brew install ffmpeg
```

Ubuntu / Debian 可以用：

```bash
sudo apt-get update
sudo apt-get install -y ffmpeg
```

只从已有转录、OCR 和笔记打包 Skill 时，可以暂时不装 `ffmpeg`。

#### 2.3 模型接口

`lineage-skill` 默认按 OpenAI-compatible 接口读取环境变量。推荐通过当前 Agent 的环境变量配置、系统环境变量或私有 `.env` 注入，不要把真实 key 写进 README、示例文件或公开仓库。

如果你用本仓库脚本直跑，可以复制 `.env.example` 为 `.env`，只填写实际会用到的 provider：

```bash
cp .env.example .env
```

常用变量如下：

```bash
# 语音转文字：处理视频 / 音频时需要
AUDIO_TRANSCRIBE_API_KEY=
AUDIO_TRANSCRIBE_BASE_URL=https://api.siliconflow.cn/v1
AUDIO_TRANSCRIBE_MODEL=FunAudioLLM/SenseVoiceSmall

# 视频 / 视觉理解：需要有视频理解能力的模型
LINEAGE_VISION_API_KEY=
LINEAGE_VISION_BASE_URL=https://your-openai-compatible-vision-endpoint/v1
LINEAGE_VISION_MODEL=gemini-3.1-pro-preview
LINEAGE_VISION_TIMEOUT=600

# 文本蒸馏：把转录、视觉分析、OCR 和笔记整理成课程知识结构时建议配置
LINEAGE_TEXT_API_KEY=
LINEAGE_TEXT_BASE_URL=https://api.openai.com/v1
LINEAGE_TEXT_MODEL=gpt5.5
LINEAGE_TEXT_MAX_TOKENS=4096
LINEAGE_TEXT_TIMEOUT=300

# 可选：PDF / OCR 文档解析。只有扫描 PDF、图片 PDF、复杂讲义需要提交给 MinerU 时才填
MINERU_API_TOKEN=
```

最小配置按你的材料决定：

| 你的材料 | 至少需要配置 |
| --- | --- |
| 已有转录、OCR、笔记 | `LINEAGE_TEXT_*`；如果只做本地抽取式整理，可把 `DISTILL_USE_LLM=0` |
| 纯 Markdown / TXT / 书籍章节 / 笔记材料 | `LINEAGE_TEXT_*`；也可先用 `DISTILL_USE_LLM=0` 跑本地证据卡片抽取 |
| 音频课程 | `AUDIO_TRANSCRIBE_*`、`LINEAGE_TEXT_*`，并安装 `ffmpeg` |
| 视频课程，只关心老师说了什么 | `AUDIO_TRANSCRIBE_*`、`LINEAGE_TEXT_*`，并安装 `ffmpeg` |
| 视频课程，还要理解 PPT / 板书 / 软件操作 | `AUDIO_TRANSCRIBE_*`、`LINEAGE_VISION_*`、`LINEAGE_TEXT_*`，并安装 `ffmpeg` |
| 扫描 PDF / 图片 PDF / 复杂讲义 | 上面对应配置，加 `MINERU_API_TOKEN`；如果已有 OCR 结果，可以不配 MinerU |

模型选择建议：

- 语音转文字示例使用 SiliconFlow 的 `FunAudioLLM/SenseVoiceSmall`，适合先跑中文课程。
- 视频 / 视觉理解模型必须支持视频输入，示例使用 `gemini-3.1-pro-preview`。
- 文本蒸馏模型建议选长上下文、中文理解好、结构化输出稳定的模型。
- OCR 结果只是证据层，扫描质量差、公式、表格和关键图示建议人工抽查。

### 3. 告诉 Agent 你的材料在哪里

例如：

```text
我有一个视频/音频课程目录，还有一批 PDF 讲义。
请用 lineage-skill 把它们整理成一个课程专家 Skill。
回答时要尽量保留来源，方便我以后回查。
```

如果你已经有转录或笔记：

```text
我已经有课程转录文本、OCR 文档和课程笔记。
请跳过重新采集，直接整理成可问答、可复习、可检索的课程 Skill。
```

如果这套材料本身就是纯文字资料：

```text
我只有 Markdown / TXT 讲义和学习笔记，没有视频。
请用 lineage-skill 做纯文字蒸馏，把概念、方法、案例、金句和边界整理成有来源的方法 Skill。
```

如果材料是一本文字书或一组长文档：

```text
我有一本书的章节 Markdown / OCR 文本。
请用 lineage-skill 把它蒸馏成可溯源、可迁移、可产出的方法 Skill。
重点抽取诊断规则、执行流程、质量标准、模板、迁移规则和常见误用。
```

### 4. 用自然语言调用它

整理完成后，它就像一个只围绕这套材料工作的专属导师/方法系统。你可以这样问：

```text
我学完前 5 课了。请按老师的体系复盘我的理解，追问我最可能漏掉的关键判断。
```

```text
按这套材料的方法，分析我下面这个真实项目，指出关键假设、判断步骤和风险。
```

```text
把老师的方法整理成一个可复用 playbook：适用场景、输入材料、操作步骤、检查标准、常见误区。
```

```text
这个结论是不是原材料支持的？请给出课时/章节、原文大意、证据强弱，以及哪些部分是合理推断。
```

```text
用老师的判断标准检查我这份方案，告诉我哪里跳步、哪里证据不足、哪里偏离课程方法。
```

## 开源引用

如果你使用 `lineage-skill` 蒸馏课程并开源生成的 Skill，建议在生成项目的 README 或说明中引用本仓库，方便后来者追溯生成方法和工具来源。

也欢迎在本仓库的 Issue 里分享你蒸馏出来的优质开源 Skill 或课程知识项目。

## 致谢

- [Datawhale](https://github.com/datawhalechina) — 感谢 Datawhale 开源社区长期在 AI 教育、开源课程和学习者社区建设上的投入与启发。
- 马老师 — 感谢马老师组织和推动开源学习，持续连接学习者、开源项目与实践交流。也欢迎关注他的公众号：LSGOGROUP。

  <img src="./docs/img/lsgogroup-wechat-public-code.jpg" alt="LSGOGROUP 公众号二维码" width="160">

- [rfeng1016](https://github.com/rfeng1016) — 感谢他对 OKF 的提醒和推荐，促成了本项目加入 OKF 兼容知识包。
- [LINUX DO — 中文开发者社区](https://linux.do/) — 感谢 LINUX DO 社区的讨论、反馈和传播支持，也欢迎大家在社区里交流课程/书籍蒸馏与 Agent Skill 实践。

[![OKF BundleDex](https://bundledex.net/static-badge.svg)](https://bundledex.net)

## License

本项目采用 [PolyForm Noncommercial License 1.0.0](./LICENSE) 授权。

商业使用或者商务合作请联系 <juneyaooo@gmail.com>。
