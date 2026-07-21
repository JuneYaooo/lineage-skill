# lineage-skill 安装指南（给 AI agent 读）

> 这份文档是给 Claude Code / Codex / OpenClaw / Hermes / 自定义 Agent 自动安装 `lineage-skill` 用的。人类用户只需要把这个 URL 发给 Agent。

## 项目一句话介绍

`lineage-skill` 能把课程、书籍、视频、音频、PDF、讲义和笔记整理成一个会带你学习的 Skill：它能引用原文、示范老师的方法、先让你动手尝试、按明确标准纠错，并逐步检查你能否在真实场景中独立使用。个人练习记录默认保存在 Skill 外部的私有目录。

仓库：https://github.com/JuneYaooo/lineage-skill

## 前置依赖

- 必需：`git`、`python3`、`pip`
- 建议：Python 3.11+
- 处理原始媒体时必需：`ffmpeg` / `ffprobe`，用于视频音频提取、媒体时长读取、压缩、切分和截图

如果缺少 `git`、`python3` 或 `pip`，先用系统包管理器安装。只从已有转录、OCR、笔记打包 Skill 时可以暂不安装 `ffmpeg`；一旦要处理 `.mp4` 视频或原始音频文件，就需要先安装 `ffmpeg` / `ffprobe`。

## 安装步骤

### 1. 克隆仓库到临时目录

```bash
git clone https://github.com/JuneYaooo/lineage-skill.git /tmp/lineage-skill
cd /tmp/lineage-skill
```

### 2. 运行安装脚本

```bash
# Claude Code
bash install_as_skill.sh --target claude

# Codex
bash install_as_skill.sh --target codex

# OpenClaw
bash install_as_skill.sh --target openclaw
```

安装脚本会：

- 把仓库复制到对应 Agent 的 skill 目录
- 排除 `.git`、`.env`、本地输出、缓存和课程生成材料
- 安装 `requirements.txt` 中的 Python 依赖
- 如果目标目录已有 `.env`，覆盖安装前会先备份并恢复

生成课程 Skill 时默认排除原始转录、OCR、分析、文本源和关键帧。只有在用户明确确认拥有分发权限并要求离线打包原料时，才传入 `--include-source-artifacts`。

脚本是交互式的：如果目标目录已存在，会询问是否覆盖。Agent 可以先检查目录状态；需要自动覆盖时可使用 `yes | bash install_as_skill.sh --target codex`。

## 配置环境变量

不要把真实 API key 写进用户业务项目的 `.env`。优先通过当前 Agent 框架或系统环境变量注入。

常用变量：

```bash
# Audio transcription
AUDIO_TRANSCRIBE_API_KEY=
AUDIO_TRANSCRIBE_BASE_URL=https://api.siliconflow.cn/v1
AUDIO_TRANSCRIBE_MODEL=FunAudioLLM/SenseVoiceSmall

# Vision analysis: use a model with video-understanding support
LINEAGE_VISION_API_KEY=
LINEAGE_VISION_BASE_URL=https://your-openai-compatible-vision-endpoint/v1
LINEAGE_VISION_MODEL=gemini-3.1-pro-preview

# Text distillation
LINEAGE_TEXT_API_KEY=
LINEAGE_TEXT_BASE_URL=https://api.openai.com/v1
LINEAGE_TEXT_MODEL=gpt5.5

# Optional PDF OCR
MINERU_API_TOKEN=
```

如果用户只想从已有转录、OCR 文档和课程笔记打包 Skill，可能不需要配置转录或视觉分析变量。

## 安装后提示用户

安装完成后告诉用户：

> 已安装完成。请重启当前 Agent，让它重新加载 Skills。重启后可以直接说：“用 Lineage Skill 把这套课程材料整理成一个能回查出处、会带我练习的课程 Skill。原始材料和个人学习记录保持私有；完成后启用新 Skill，并告诉我怎样开始第一课。”

## 冒烟测试

重启 Agent 后，让用户用自然语言测试：

```text
用 lineage-skill 检查一下我现在有哪些课程材料可以整理成 Skill。
```

如果用户已经有课程材料：

```text
用 lineage-skill 把这个课程目录整理成一个既能回查出处、又能带我练习和解决真实问题的课程 Skill。原始材料和个人学习记录保持私有；完成后启用新 Skill，并告诉我怎样开始第一课。
```

## 完成标志

以下条件满足即可认为安装成功：

1. 对应安装目录下存在 `SKILL.md`
2. `scripts/` 和 `requirements.txt` 已复制到安装目录
3. 依赖安装完成
4. Agent 重启后，用户自然语言请求整理课程时能触发 `lineage-skill`
5. 根 Skill 通过 quick validator，生成 Mentor Skill 能通过 `scripts/validate_generated_skill.py`
