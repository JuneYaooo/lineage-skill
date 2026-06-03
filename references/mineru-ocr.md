# MinerU OCR

Use this only when course materials include PDFs, scans, handouts, or slide exports that should become evidence.

## Workflow

1. Check `MINERU_API_TOKEN`.
2. Run document parsing through the full pipeline, or call `scripts/parse_mineru_documents.py` directly.
3. Confirm `documents/mineru_manifest.json` and `documents/mineru_supplement.md` exist.
4. Rebuild `course_package.json`.
5. Rebuild the target Skill.

## Full Pipeline Example

```bash
python scripts/run_course_pipeline.py \
  --input-dir <course-video-dir> \
  --documents-input <pdf-or-pdf-dir> \
  --course-name <course-name> \
  --skill-name <skill-name> \
  --mode mentor,practitioner \
  --output-dir ./dist
```

## Existing OCR Output

If MinerU output already exists and the user only wants to rebuild references, use the script's skip/rebuild options instead of submitting PDFs again.

## Evidence Behavior

- OCR Markdown becomes an evidence layer.
- OCR quality depends on source PDF quality.
- Poor scans, formulas, tables, and diagrams may need manual review.
- Do not commit OCR outputs if the documents are private or copyrighted.
