# 师承.skill 路线图

## 当前状态

当前仓库已经完成的是视频课程到 Skill 的主链路：

- C5 课程炼化框架
- 课程 Skill 标准结构
- 视频语音转录脚本
- 视频画面分析与干货截图脚本
- 课程级蒸馏脚本
- `scripts/build_course_skill.py`
- `scripts/run_course_pipeline.py`
- `SKILL.md` 自动生成
- `references/` 文件复制或占位
- `course_distillation_*.md/json` 派生 references
- `lesson_index.json` 生成
- `evidence_map.json` 文件级索引
- 轻量关键词搜索脚本
- `.env.example` 已预留 PDF / OCR / MinerU 配置
- `scripts/parse_mineru_documents.py` 已接入 PDF / MinerU OCR
- 外部 OCR/MinerU 产物可进入 CoursePackage 与 Skill 生成层

还没有完全通用化的是：

- OCR 结果到 CoursePackage 的标准映射
- 语义检索
- 多课程索引

## v0.1：品牌与方法论整理

目标：把项目从“脚本集合”整理成“师承.skill”产品概念。

产物：

- README.md
- METHODOLOGY.md
- ROADMAP.md
- examples/

## v0.2：Course Skill Builder

目标：从已有课程蒸馏结果生成一个独立 Skill。

当前命令：

```bash
python scripts/build_course_skill.py \
  --course-name <课程名称> \
  --skill-name <skill名称> \
  --source-dir <课程材料目录> \
  --output-dir <skills目录>
```

生成：

```text
<skill-name>/
├── SKILL.md
├── lineage_manifest.json
├── references/
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

增强计划：

- 校验输入材料质量
- 支持更多 course_distillation JSON 结构
- 输出构建报告

## v0.3：Video Course Pipeline

目标：从课程视频生成蒸馏笔记和 Skill。

当前命令：

```bash
python scripts/run_course_pipeline.py \
  --input-dir <视频目录> \
  --course-name <课程名称> \
  --skill-name <skill名称> \
  --output-dir <skills目录>
```

已包含：

- OpenAI-compatible 音频转录
- OpenAI-compatible 视觉分析
- 大视频压缩、分片
- 干货截图抽帧与去重
- LLM 课程蒸馏
- 本地抽取式 fallback

## v0.4：证据地图

目标：回答时能明确指出来源。

证据字段：

- course_name
- lesson_name
- transcript_file
- analysis_file
- screenshot_files
- timestamp
- topic
- confidence

当前 `evidence_map.json` 已支持文件级索引，后续要升级为片段级、主题级、时间点级证据。

## v0.5：检索与问答

目标：生成的 Skill 能检索课程内容。

能力：

- 按关键词查原文
- 按概念查课
- 按主题查截图
- 按课程查摘要
- 输出带来源回答

当前已有轻量关键词搜索脚本，语义检索和问答编排仍在规划中。

## v0.6：多课程师承库

目标：支持多个老师、多门课、多套知识体系。

能力：

- 多课程索引
- 跨课程对比
- 老师风格总结
- 主题专题包
- 个人知识 Skill 库
