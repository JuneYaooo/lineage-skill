# 模型接口

`lineage-skill` 主要按 OpenAI-compatible 接口接入语音、视觉和文本模型。如果模型服务不是这个接口形态，可以通过兼容网关或适配层接入。

## 需要哪些模型

| 接口 | 负责什么 | 备注 |
| --- | --- | --- |
| 语音转文字模型 | 还原“老师说了什么” | 中文课程可以优先试 `SenseVoiceSmall` / FunASR 体系；英文或多语言课程可以用 `whisper-1`、`gpt-4o-transcribe`、`gpt-4o-mini-transcribe`。 |
| 视频 / 视觉模型 | 理解“画面里讲了什么” | 建议选择对长视频、PPT、板书、软件界面和截图理解能力强的模型。 |
| 文本蒸馏模型 | 把转录、视觉分析、OCR 和笔记压缩成课程知识结构 | 建议使用长上下文、结构化输出稳定、中文理解好的模型。 |
| OCR / 文档解析 | 处理扫描 PDF、图片 PDF、复杂排版讲义 | 普通文本 PDF 可以直接提取；扫描件、公式、表格和图文混排建议用 MinerU 等工具，并人工抽查关键内容。 |

## 相关配置

- 环境变量和 OpenAI-compatible 接口配置见 [configuration.md](./configuration.md)。
- PDF / OCR 流程见 [mineru-ocr.md](./mineru-ocr.md)。
