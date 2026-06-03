# Configuration

`lineage-skill` reads configuration from environment variables. The recommended workflow is:

```text
copy .env.example -> .env
fill only the providers you use
never commit .env
```

## Audio Transcription

Used by `scripts/transcribe_video.py`.

| Variable | Required | Description |
| --- | --- | --- |
| `AUDIO_TRANSCRIBE_API_KEY` | Yes | API key for an OpenAI-compatible `/audio/transcriptions` endpoint. |
| `AUDIO_TRANSCRIBE_BASE_URL` | Yes | Base URL, for example `https://api.openai.com/v1` or a compatible relay. |
| `AUDIO_TRANSCRIBE_MODEL` | Yes | Transcription model name. |

Model notes:

- Chinese courses: consider `SenseVoiceSmall` / FunASR-compatible services when local or Chinese-optimized ASR is preferred.
- English or multilingual courses: consider Whisper-compatible models such as `whisper-1`, or newer OpenAI transcription models such as `gpt-4o-transcribe` / `gpt-4o-mini-transcribe` when available in your endpoint.
- Pick ASR by domain vocabulary, punctuation quality, long-audio stability, timestamp support, and whether you need speaker diarization.

## Vision Analysis

Used by `scripts/analyze_videos.py`.

| Variable | Required | Description |
| --- | --- | --- |
| `LINEAGE_VISION_API_KEY` | Yes | API key for a vision-capable OpenAI-compatible chat endpoint. |
| `LINEAGE_VISION_BASE_URL` | Yes | Base URL for the vision endpoint. |
| `LINEAGE_VISION_MODEL` | Yes | Vision model name. |
| `LINEAGE_VISION_TIMEOUT` | No | Request timeout in seconds. |

Model notes:

- Use a model that handles slides, boards, screenshots, software screens, tables, diagrams, and long video context well.
- Gemini-class video understanding models can be strong for video courses, but the current scripts expect an OpenAI-compatible chat endpoint or an adapter/relay.
- For screen-heavy courses, visual analysis should complement transcription instead of replacing it. The transcript captures speech; the vision model captures what is only visible on screen.

## Text Distillation

Used by `scripts/distill_course.py`.

| Variable | Required | Description |
| --- | --- | --- |
| `LINEAGE_TEXT_API_KEY` | Required when `DISTILL_USE_LLM=1` | API key for the text model. |
| `LINEAGE_TEXT_BASE_URL` | Required when `DISTILL_USE_LLM=1` | Base URL for the text model. |
| `LINEAGE_TEXT_MODEL` | Required when `DISTILL_USE_LLM=1` | Text model name. |
| `LINEAGE_TEXT_MAX_TOKENS` | No | Max output tokens. |
| `LINEAGE_TEXT_TIMEOUT` | No | Request timeout in seconds. |
| `DISTILL_USE_LLM` | No | Set to `0` for local extractive fallback. |
| `DISTILL_CHUNK_SIZE` | No | Text chunk size for distillation. |
| `DISTILL_CHUNK_OVERLAP` | No | Chunk overlap size. |

Model notes:

- Prefer long-context text models that produce stable structured output.
- The text model should be good at Chinese if the course is Chinese, and should handle terminology consistently.
- You can use cheaper models for first-pass extraction and stronger models for final synthesis when quality matters.

## MinerU / OCR

Used by `scripts/parse_mineru_documents.py`.

| Variable | Required | Description |
| --- | --- | --- |
| `MINERU_API_TOKEN` | Required unless using `--skip-submit` | MinerU API token. |
| `MINERU_API_BASE` | No | Defaults to `https://mineru.net/api/v4`. |
| `MINERU_MODEL_VERSION` | No | Defaults to `vlm`. |
| `MINERU_ENABLE_FORMULA` | No | `true` / `false`. |
| `MINERU_ENABLE_TABLE` | No | `true` / `false`. |
| `MINERU_LANGUAGE` | No | Defaults to `ch`. |

OCR notes:

- Use direct text extraction for clean text PDFs when possible.
- Use MinerU or another OCR/document parser for scanned PDFs, image PDFs, slide exports, formulas, tables, and complex layouts.
- OCR output is evidence, not guaranteed truth. Review poor scans, formulas, tables, and diagrams before relying on them for final course conclusions.

## Local Tool Overrides

| Variable | Required | Description |
| --- | --- | --- |
| `FFMPEG` | No | Custom `ffmpeg` path. |
| `FFPROBE` | No | Custom `ffprobe` path. |

## Security Rules

- Do not commit `.env`.
- Do not put real keys in README, examples, or docs.
- Do not hardcode private local paths.
- Do not commit generated transcripts, screenshots, OCR outputs, or course distillation artifacts unless they are intentionally public.
- Use `.env.example` only for variable names and safe placeholders.
