#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
汇总转录 + 视频分析 → LLM 蒸馏 → 结构化课程笔记
"""

import os
import sys
import json
import argparse
import signal
import re
from collections import Counter
from datetime import datetime

from dotenv import load_dotenv
from llm_client import call_text_llm

load_dotenv()

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

COMMON_STOPWORDS = {
    "这个", "一个", "我们", "你们", "他们", "就是", "所以", "因为", "如果", "然后", "现在",
    "可以", "没有", "不是", "什么", "这个时候", "一样", "起来", "出来", "进去", "老师",
    "时候", "的时候", "对不对", "有没有", "懂不懂", "好了", "哎呀", "的话", "还有呢",
    "第一个", "第二个", "第三个", "一下", "这里", "那里", "里面", "外面", "这样", "那样",
    "诸位", "大家", "今天", "开始", "知道", "看到", "注意", "为什么", "不是说",
}

DOMAIN_TERMS = [
    "框架", "模型", "方法", "方法论", "原则", "路径", "步骤", "流程", "系统",
    "案例", "用户", "产品", "增长", "转化", "运营", "内容", "商业", "数据",
    "指标", "定位", "策略", "风险", "边界", "复盘", "执行", "实践", "工具",
    "结构", "逻辑", "认知", "决策", "问题", "方案", "目标", "结果", "行动",
]


def call_llm(messages: list) -> str:
    import time as _time
    timeout = int(os.getenv("DISTILL_LLM_TIMEOUT", "240"))
    old_handler = signal.getsignal(signal.SIGALRM)

    def _raise_timeout(signum, frame):
        raise TimeoutError(f"LLM 调用超过 {timeout}s")

    for attempt in range(5):
        try:
            signal.signal(signal.SIGALRM, _raise_timeout)
            signal.alarm(timeout)
            try:
                return call_text_llm(messages)
            finally:
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old_handler)
        except Exception as e:
            err = str(e)
            if "429" in err or "rate" in err.lower():
                wait = min(2 ** attempt, 60)
                print(f"  限流，{wait}s 后重试 {attempt+1}/5 ...")
                _time.sleep(wait)
            elif attempt < 2:
                print(f"  LLM 失败 (attempt {attempt+1}): {e}")
                _time.sleep(5)
            else:
                print(f"  LLM 调用失败: {e}")
                return f"[LLM 错误: {e}]"
    print(f"  LLM 调用失败: 已达最大重试次数")
    return "[LLM 错误: 重试耗尽]"


def llm_enabled() -> bool:
    if os.getenv("DISTILL_USE_LLM", "1").strip().lower() in {"0", "false", "no"}:
        return False
    return bool(os.getenv("LINEAGE_TEXT_API_KEY"))


def chunk_text(text: str, chunk_size: int | None = None, overlap: int | None = None) -> list[str]:
    if chunk_size is None:
        chunk_size = int(os.getenv("DISTILL_CHUNK_SIZE", "6000"))
    if overlap is None:
        overlap = int(os.getenv("DISTILL_CHUNK_OVERLAP", "500"))
    if len(text) <= chunk_size:
        return [text]
    chunks = []
    start = 0
    while start < len(text):
        end = min(len(text), start + chunk_size)
        chunks.append(text[start:end])
        if end >= len(text):
            break
        start = max(0, end - overlap)
    return chunks


def split_sentences(text: str) -> list[str]:
    cleaned = re.sub(r"\s+", "", text or "")
    pieces = re.split(r"(?<=[。！？!?；;])", cleaned)
    sentences = []
    for piece in pieces:
        piece = piece.strip()
        if 18 <= len(piece) <= 180:
            sentences.append(piece)
    if sentences:
        return sentences
    return [cleaned[i : i + 120] for i in range(0, min(len(cleaned), 1200), 120) if cleaned[i : i + 120]]


def extract_keywords(text: str, limit: int = 18) -> list[str]:
    scores = Counter()
    for term in DOMAIN_TERMS:
        count = text.count(term)
        if count:
            scores[term] += count * (3 if len(term) >= 2 else 1)
    if scores:
        return [word for word, _ in scores.most_common(limit)]
    for word in re.findall(r"[\u4e00-\u9fff]{2,6}", text):
        if word in COMMON_STOPWORDS:
            continue
        scores[word] += 1
    return [word for word, _ in scores.most_common(limit)]


def media_lesson_stem(value: str) -> str:
    text = os.path.splitext(os.path.basename(value or ""))[0]
    text = re.sub(r"(_transcript|_analysis|_model_keyframes_manifest)$", "", text)
    if "_" in text:
        prefix, suffix = text.rsplit("_", 1)
        if "、" in prefix or "课" in prefix or re.match(r"^\d+", prefix):
            return suffix
    return text


def normalize_media_key(value: str) -> str:
    text = media_lesson_stem(value)
    return re.sub(r"[^0-9A-Za-z\u4e00-\u9fff]+", "", text).lower()


def media_aliases(value: str) -> list[str]:
    aliases = []
    for candidate in (value, media_lesson_stem(value)):
        if not candidate:
            continue
        key = normalize_media_key(candidate)
        if key and key not in aliases:
            aliases.append(key)
    return aliases


def local_lesson_summary(video: str, text: str, duration_minutes: float) -> str:
    sentences = split_sentences(text)
    keywords = extract_keywords(text, 12)
    lead = " ".join(sentences[:3])
    scored: list[tuple[float, int, str]] = []
    for idx, sentence in enumerate(sentences):
        score = 0.0
        for term in DOMAIN_TERMS:
            if term in sentence:
                score += 4 if len(term) >= 2 else 1
        for keyword in keywords[:8]:
            if keyword in sentence:
                score += 2
        if any(mark in sentence for mark in ("重点", "核心", "关键", "原则", "方法", "步骤", "案例", "注意")):
            score += 1.5
        score += min(len(sentence), 120) / 120
        if score:
            scored.append((score, idx, sentence))
    picked = sorted(sorted(scored, reverse=True)[:8], key=lambda item: item[1])
    if not picked:
        picked = [(0, idx, s) for idx, s in enumerate(sentences[:6])]

    key_sentences = [s for _, _, s in picked]
    points = "\n".join(f"- {s}" for s in key_sentences[:5])
    keyword_text = "、".join(keywords[:10]) if keywords else "（未抽取到稳定关键词）"
    return f"""### {video}
本课为文本转写抽取式摘要，课程时长约 {duration_minutes:.1f} 分钟。开头脉络：{lead}

关键词：{keyword_text}

核心摘录：
{points}

整理说明：以上根据讲话转写自动抽取高权重主题句，适合作为后续人工校订和检索入口。"""


def local_course_digest(transcripts: list, summaries: list, course_name: str, text_synthesis: str = "") -> str:
    total_dur = sum(t.get("duration", 0) for t in transcripts)
    all_text = "\n".join(t.get("full_text", "") for t in transcripts)
    keywords = extract_keywords(all_text, 24)
    lesson_items = []
    for s in summaries:
        summary = re.sub(r"^#+\s*[^\n]+\n?", "", s["summary"].strip())
        summary = re.sub(r"\*\*", "", summary)
        summary = re.sub(r"\s+", " ", summary)
        lesson_items.append(f"- {s['video']}：{summary[:180]}...")
    lesson_lines = "\n".join(lesson_items)
    modules = [
        ("课程主线", "按课程顺序复盘讲者反复出现的核心问题、关键词和判断框架。"),
        ("概念与方法", "提取课程中的关键概念、操作步骤、模型和原则，作为后续检索入口。"),
        ("案例与应用", "整理课程中的案例、示范、数据、工具或实操场景，连接到具体课时。"),
        ("复习与迁移", "把逐课摘要转为可执行复习顺序，并提示哪些结论需要回到原文核对。"),
    ]
    module_text = "\n".join(f"- **{name}**：{desc}" for name, desc in modules)
    glossary = "\n".join(f"- **{kw}**：本课程反复出现的关键词，需结合逐课转写语境理解。" for kw in keywords[:18])
    actions = "\n".join(
        f"{i}. 复习 `{s['video']}`，先读逐课摘要，再回到完整转写核对原话。"
        for i, s in enumerate(summaries[:15], start=1)
    )
    quotes = []
    for t in transcripts:
        for sentence in split_sentences(t.get("full_text", "")):
            if any(term in sentence for term in ("重点", "核心", "关键", "原则", "方法", "一定要", "不要")):
                quotes.append((t.get("video", "Unknown"), sentence))
                break
        if len(quotes) >= 12:
            break
    quote_text = "\n".join(f"- {quote}（{video}）" for video, quote in quotes)
    text_section = ""
    if text_synthesis.strip():
        text_section = f"""
## 八、文字资料补充
以下内容来自课程讲义、OCR、Markdown/TXT 笔记或其他纯文字资料，已通过 text_distillation 证据卡片流程整理。

{text_synthesis.strip()}
"""

    return f"""## 一、课程概览
《{course_name}》共 {len(transcripts)} 课，总时长约 {total_dur/3600:.1f} 小时。本轮为文本优先蒸馏，已基于转写内容生成逐课摘要、关键词、主题入口和复习路径。

以下内容来自逐课转写摘要与关键词抽取，用作 Skill 检索和学习入口。若需要引用原话或验证细节，应回到 `full_transcript.md` 与对应转录 JSON。

## 二、课程体系图
{module_text}

## 三、逐课精要
{lesson_lines}

## 四、跨课程主题图谱
- **核心关键词**：{"、".join(keywords[:24])}
- **高频主题**：优先围绕高频关键词回查逐课摘要，确认课程的主干问题。
- **案例线索**：含有“案例、数据、示范、操作、复盘”等词的课时适合作为应用入口。
- **方法线索**：含有“框架、模型、原则、步骤、路径”等词的课时适合作为体系化复习入口。

## 五、关键概念词汇表
{glossary}

## 六、可执行行动清单
{actions}

## 七、核心金句集
{quote_text}
{text_section}
"""


def load_transcripts(course_dir: str) -> list:
    td = os.path.join(course_dir, "transcripts")
    if not os.path.isdir(td):
        print(f"ℹ️ 无转录目录: {td}")
        return []
    transcripts = []
    for f in sorted(os.listdir(td)):
        if f.endswith(".json"):
            with open(os.path.join(td, f), encoding="utf-8") as fp:
                transcripts.append(json.load(fp))
    print(f"📄 {len(transcripts)} 个转录")
    return transcripts


def load_analyses(course_dir: str) -> list:
    ad = os.path.join(course_dir, "analysis")
    if not os.path.isdir(ad):
        print(f"⚠️ 无分析目录: {ad}")
        return []
    analyses = []
    for f in sorted(os.listdir(ad)):
        if f.endswith("_analysis.md"):
            with open(os.path.join(ad, f), encoding="utf-8") as fp:
                analyses.append({"video": f.replace("_analysis.md", ""), "content": fp.read()})
    print(f"📄 {len(analyses)} 个分析")
    return analyses


def load_keyframe_summary(course_dir: str, max_chars: int = 20000) -> str:
    path = os.path.join(course_dir, "keyframe_selection", "model_keyframe_summary.md")
    if not os.path.exists(path):
        return ""
    with open(path, encoding="utf-8") as fp:
        text = fp.read()
    if len(text) > max_chars:
        return text[:max_chars] + "\n\n[已截断]"
    return text


def load_text_synthesis(course_dir: str, max_chars: int = 30000) -> str:
    path = os.path.join(course_dir, "text_distillation", "text_course_synthesis.md")
    if not os.path.exists(path):
        return ""
    with open(path, encoding="utf-8") as fp:
        text = fp.read()
    if len(text) > max_chars:
        return text[:max_chars] + "\n\n[已截断]"
    return text


def load_keyframe_manifest(course_dir: str, video_name: str) -> dict:
    keyframe_dir = os.path.join(course_dir, "keyframe_selection")
    candidates = [os.path.join(keyframe_dir, f"{video_name}_model_keyframes_manifest.json")]
    if os.path.isdir(keyframe_dir):
        aliases = set(media_aliases(video_name))
        for filename in sorted(os.listdir(keyframe_dir)):
            if filename.endswith("_model_keyframes_manifest.json") and aliases & set(media_aliases(filename)):
                candidates.append(os.path.join(keyframe_dir, filename))
    for path in candidates:
        if not os.path.exists(path):
            continue
        try:
            with open(path, encoding="utf-8") as fp:
                data = json.load(fp)
        except Exception:
            continue
        return data if isinstance(data, dict) else {}
    return {}


def build_analysis_lookup(analyses: list) -> dict[str, str]:
    lookup: dict[str, str] = {}
    for item in analyses:
        video = item.get("video", "")
        content = item.get("content", "")
        for alias in media_aliases(video):
            lookup.setdefault(alias, content)
    return lookup


def lookup_analysis(analysis_lookup: dict[str, str], video_name: str) -> str:
    for alias in media_aliases(video_name):
        if alias in analysis_lookup:
            return analysis_lookup[alias]
    return ""


def screenshot_count_for_video(course_dir: str, video_name: str) -> int:
    screenshot_root = os.path.join(course_dir, "analysis", "screenshots")
    candidates = [os.path.join(screenshot_root, video_name)]
    if os.path.isdir(screenshot_root):
        aliases = set(media_aliases(video_name))
        for dirname in sorted(os.listdir(screenshot_root)):
            path = os.path.join(screenshot_root, dirname)
            if os.path.isdir(path) and aliases & set(media_aliases(dirname)):
                candidates.append(path)
    seen = set()
    count = 0
    for directory in candidates:
        if not os.path.isdir(directory) or directory in seen:
            continue
        seen.add(directory)
        count += len([name for name in os.listdir(directory) if not name.startswith(".")])
    return count


def format_keyframe_manifest(manifest: dict, limit: int = 24) -> str:
    if not manifest:
        return "（无模型精选关键帧 manifest）"
    selected = manifest.get("selected") or []
    if not selected:
        return (
            f"候选帧 {manifest.get('candidate_count', 0)} 张，"
            "模型未选择可作为证据的关键帧。"
        )
    lines = [
        f"候选帧 {manifest.get('candidate_count', 0)} 张，模型精选 {manifest.get('selected_count', len(selected))} 张。",
        f"Manifest: `keyframe_selection/{manifest.get('media', '')}_model_keyframes_manifest.json`",
    ]
    for item in selected[:limit]:
        keywords = "、".join(str(k) for k in (item.get("keywords") or []) if k)
        reason = item.get("reason") or ""
        path = item.get("selected_path") or item.get("candidate_source") or ""
        prefix = f"- {item.get('timestamp', '')} `{path}`"
        if keywords:
            prefix += f" [{keywords}]"
        lines.append(f"{prefix}: {reason}".rstrip())
    if len(selected) > limit:
        lines.append(f"- 另有 {len(selected) - limit} 张精选关键帧，见 manifest。")
    return "\n".join(lines)


def build_per_lesson_summaries(
    transcripts: list,
    analyses: list,
    course_dir: str,
    summary_path: str | None = None,
) -> list:
    print(f"\n📝 逐课摘要 ...")
    amap = build_analysis_lookup(analyses)
    summaries = []
    done: dict[str, dict] = {}
    if summary_path and os.path.exists(summary_path):
        with open(summary_path, encoding="utf-8") as f:
            existing = json.load(f)
        done = {s.get("video", ""): s for s in existing}
        summaries.extend(s for s in existing if s.get("video"))
        print(f"📄 续用已有摘要: {len(done)} 个")
    for i, t in enumerate(transcripts):
        vn = t.get("video", f"video_{i}")
        if vn in done:
            print(f"  ⏭ 已有摘要: {vn}")
            continue
        text = t.get("full_text", "")
        dur = t.get("duration", 0)
        if not llm_enabled():
            print(f"  [{i+1}/{len(transcripts)}] {vn} ... 本地抽取式摘要")
            summaries.append({
                "video": vn,
                "duration_minutes": round(dur / 60, 1),
                "summary": local_lesson_summary(vn, text, round(dur / 60, 1)),
            })
            if summary_path:
                with open(summary_path, "w", encoding="utf-8") as f:
                    json.dump(summaries, f, ensure_ascii=False, indent=2)
                print(f"  💾 checkpoint: {summary_path}")
            continue
        text_chunks = chunk_text(text)
        if len(text_chunks) > 1:
            print(f"    分块摘要: {len(text_chunks)} 段, {len(text)} 字")
            chunk_summaries = []
            for ci, chunk in enumerate(text_chunks, start=1):
                chunk_prompt = f"""请摘要以下课程转写片段，保留具体主题、案例、关键概念、方法步骤、重要原话。

**视频名称**: {vn}
**片段**: {ci}/{len(text_chunks)}

## 转写片段
{chunk}

输出 200-350 字中文摘要，不要扩展未出现的内容。"""
                chunk_summaries.append(call_llm([{"role": "user", "content": chunk_prompt}]))
                import time as _t
                _t.sleep(1)
            snippet = "\n\n".join(
                f"### 片段 {ci}\n{summary}"
                for ci, summary in enumerate(chunk_summaries, start=1)
            )
            transcript_label = "讲话转录分块摘要"
        else:
            snippet = text
            transcript_label = "讲话转录"
        analysis = lookup_analysis(amap, vn)
        if len(analysis) > 12000:
            analysis = analysis[:12000] + "\n\n[已截断]"

        # 截图数量
        ss_count = screenshot_count_for_video(course_dir, vn)
        keyframe_manifest = load_keyframe_manifest(course_dir, vn)
        keyframe_text = format_keyframe_manifest(keyframe_manifest)
        keyframe_count = keyframe_manifest.get("selected_count", 0) if keyframe_manifest else 0

        print(f"  [{i+1}/{len(transcripts)}] {vn} ...")

        prompt = f"""请为以下课程视频内容生成摘要（2-3段中文，约300-500字）：

**视频名称**: {vn}
**时长**: {dur/60:.1f} 分钟
**模型精选关键帧**: {keyframe_count} 张
**补充截图标记**: {ss_count} 张

## {transcript_label}
{snippet}

## 模型精选关键帧（优先视觉证据）
{keyframe_text}

## 视频画面分析（含补充截图标记）
{analysis if analysis else "（无画面分析数据）"}

生成格式：
### {vn}
[2-3段摘要]

要求：概括核心主题、提取3-5个知识点或观点、引用1-2句金句。优先综合讲话转录、视频画面分析和模型精选关键帧；补充截图标记只作为辅助线索，不要把等间隔候选帧当作最终证据。"""

        s = call_llm([{"role": "user", "content": prompt}])
        summaries.append({"video": vn, "duration_minutes": round(dur / 60, 1), "summary": s})
        if summary_path:
            with open(summary_path, "w", encoding="utf-8") as f:
                json.dump(summaries, f, ensure_ascii=False, indent=2)
            print(f"  💾 checkpoint: {summary_path}")
        # 避免触发限流
        import time as _t
        _t.sleep(2)
    return summaries


def build_course_digest(transcripts: list, summaries: list, course_name: str, course_dir: str) -> dict:
    print(f"\n🧠 课程蒸馏 ...")
    total_dur = sum(t.get("duration", 0) for t in transcripts)
    total_chars = sum(len(t.get("full_text", "")) for t in transcripts)

    summary_text = "\n\n".join(
        f"### {s['video']} ({s['duration_minutes']}分钟)\n{s['summary']}"
        for s in summaries
    )
    keyframe_summary = load_keyframe_summary(course_dir)
    text_synthesis = load_text_synthesis(course_dir)
    full_transcript = "\n\n".join(
        f"# {t.get('video', 'Unknown')}\n{t.get('full_text', '')}"
        for t in transcripts
    )

    if not llm_enabled():
        digest = local_course_digest(transcripts, summaries, course_name, text_synthesis=text_synthesis)
        return {
            "course_title": course_name,
            "total_lessons": len(transcripts),
            "total_duration_seconds": round(total_dur),
            "total_duration_hours": round(total_dur / 3600, 1),
            "total_transcript_chars": total_chars,
            "lesson_summaries": summaries,
            "distillation_markdown": digest,
            "full_transcript": full_transcript,
            "generated_at": datetime.now().isoformat(),
        }

    prompt = f"""你是一位课程内容策划专家。请根据课程所有视频的摘要，生成完整的课程蒸馏笔记。

**课程名称**: {course_name}
**总视频数**: {len(transcripts)} 课
**总时长**: {total_dur/3600:.1f} 小时
**总转录字数**: {total_chars} 字

## 所有课程摘要

{summary_text}

## 模型精选关键帧总览

{keyframe_summary if keyframe_summary else "（无模型精选关键帧总览；如课程含视频，应检查 keyframe_selection/model_keyframe_summary.md）"}

## 文字资料证据卡片综合

{text_synthesis if text_synthesis else "（无纯文字资料蒸馏结果；如课程含 PDF OCR、Markdown、TXT 或笔记，应检查 text_distillation/text_course_synthesis.md）"}

请生成以下结构化内容（Markdown 格式）：

---

## 一、课程概览
课程主题、目标受众、课程结构（1-2段）

## 二、课程体系图
- 核心模块划分（3-5个模块）
- 每个模块下对应的课程
- 模块之间的递进关系

## 三、逐课精要
为每一课写1-2句核心要点

## 四、跨课程主题图谱
识别反复出现的核心主题，每个说明出现位置和核心观点

## 五、关键概念词汇表
10-20 个最重要的概念/术语及定义要点

## 六、可执行行动清单
15-20条，按优先级排序（高/中/低）

## 七、核心金句集
10-15条金句或观点，标注出自哪一课

## 八、老师首先关注的线索
只整理摘要、问答、讲评或画面明确支持的观察线索、干扰因素与后续诊断问题；缺证据时写明缺口

## 九、问题定性与诊断问题
整理老师如何定义问题、先问什么、如何排除相邻问题

## 十、决策规则与替代方法
用“何时使用 / 为什么 / 何时不用 / 替代方法”整理来源支持的规则

## 十一、完整示范与讲评案例
保留情境、观察、问题框定、选择、推理步骤、执行、自检和边界；不能从普通讲解臆造完整示范

## 十二、反馈纠错模式
整理老师明确指出的典型错误、最小纠偏动作、修订要求和退回先修的条件

## 十三、进阶与出师信号
整理来源支持的练习递进、独立完成标准和质量信号

## 十四、不可复制背景与边界
区分方法的适用条件、老师个人经验或资源背景、争议、禁忌和不可照搬部分

请确保基于真实摘要内容和已列出的视觉证据，不要编造。涉及画面、板书、PPT、图表、软件界面的判断，优先引用模型精选关键帧路径或对应课时。老师隐性判断若只能从普通讲解推断，必须明确标记为“课程证据综合/中低置信”，不得冒充老师直接表达；通用 Mentor 行为不能归到老师本人。"""

    digest = call_llm([{"role": "user", "content": prompt}])

    return {
        "course_title": course_name,
        "total_lessons": len(transcripts),
        "total_duration_seconds": round(total_dur),
        "total_duration_hours": round(total_dur / 3600, 1),
        "total_transcript_chars": total_chars,
        "lesson_summaries": summaries,
        "distillation_markdown": digest,
        "full_transcript": full_transcript,
        "generated_at": datetime.now().isoformat(),
    }


def main():
    parser = argparse.ArgumentParser(description="蒸馏课程内容")
    parser.add_argument("--course-name", required=True, help="课程名称（对应 BASE_DIR 下的子目录）")
    parser.add_argument("--base-dir", default=BASE_DIR, help="课程输出根目录，默认当前项目目录")
    parser.add_argument("--skip-summaries", action="store_true", help="复用已有逐课摘要")
    args = parser.parse_args()

    course_dir = os.path.join(args.base_dir, args.course_name)
    timestamp = datetime.now().strftime("%Y-%m-%d")
    os.makedirs(course_dir, exist_ok=True)

    print("=" * 60)
    print(f"📚 {args.course_name} 蒸馏")
    print("=" * 60)

    transcripts = load_transcripts(course_dir)
    analyses = load_analyses(course_dir)
    text_synthesis = load_text_synthesis(course_dir)

    if not transcripts and not text_synthesis:
        print("❌ 无转录数据，也无纯文字蒸馏结果")
        sys.exit(1)

    summary_path = os.path.join(course_dir, "lesson_summaries.json")

    if not transcripts:
        summaries = []
    elif args.skip_summaries and os.path.exists(summary_path):
        print(f"📄 加载已有摘要: {summary_path}")
        with open(summary_path, encoding="utf-8") as f:
            summaries = json.load(f)
    else:
        summaries = build_per_lesson_summaries(transcripts, analyses, course_dir, summary_path)
        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump(summaries, f, ensure_ascii=False, indent=2)
        print(f"  💾 {summary_path}")

    digest = build_course_digest(transcripts, summaries, args.course_name, course_dir)

    # Markdown
    md_path = os.path.join(course_dir, f"course_distillation_{timestamp}.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(f"# {digest['course_title']} — 课程蒸馏笔记\n\n")
        f.write(f"**生成时间**: {digest['generated_at']}\n\n")
        f.write(f"**课程规模**: {digest['total_lessons']} 课, "
                f"{digest['total_duration_hours']} 小时\n\n")
        f.write("---\n\n")
        f.write(digest["distillation_markdown"])
        f.write("\n\n---\n\n## 附录：逐课摘要\n\n")
        for s in digest["lesson_summaries"]:
            f.write(f"### {s['video']} ({s['duration_minutes']}分钟)\n\n{s['summary']}\n\n")
    print(f"  💾 {md_path}")

    # JSON（不含完整转录）
    json_path = os.path.join(course_dir, f"course_distillation_{timestamp}.json")
    digest_json = {k: v for k, v in digest.items() if k != "full_transcript"}
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(digest_json, f, ensure_ascii=False, indent=2)
    print(f"  💾 {json_path}")

    # 完整转录
    ft_path = os.path.join(course_dir, "full_transcript.md")
    with open(ft_path, "w", encoding="utf-8") as f:
        f.write(f"# {digest['course_title']} — 完整转录\n\n{digest['full_transcript']}")
    print(f"  💾 {ft_path}")

    print(f"\n✅ 完成！{md_path}")


if __name__ == "__main__":
    main()
