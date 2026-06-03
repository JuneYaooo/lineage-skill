# Model Interfaces

`lineage-skill` mainly uses OpenAI-compatible interfaces for speech, vision, and text models. If a provider does not expose that shape directly, use a compatible gateway or adapter layer.

## Required Interfaces

| Interface | Role | Notes |
| --- | --- | --- |
| Speech-to-text model | Restores what the teacher said | Chinese courses may work well with `SenseVoiceSmall` / FunASR; English or multilingual courses can use `whisper-1`, `gpt-4o-transcribe`, or `gpt-4o-mini-transcribe`. |
| Video / vision model | Understands what appears on screen | Prefer models that handle long videos, slides, whiteboards, software interfaces, and screenshots well. |
| Text distillation model | Compresses transcripts, visual analysis, OCR, and notes into a course knowledge structure | Prefer long-context models with stable structured output and strong language understanding. |
| OCR / document parser | Handles scanned PDFs, image PDFs, and complex handouts | Plain-text PDFs can be extracted directly; scanned files, formulas, tables, and complex layouts should use MinerU or a similar parser, with manual checks where needed. |

## Related Configuration

- Environment variables and OpenAI-compatible setup: [configuration.md](./configuration.md).
- PDF / OCR workflow: [mineru-ocr.md](./mineru-ocr.md).
