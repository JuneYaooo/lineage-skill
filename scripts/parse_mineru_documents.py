#!/usr/bin/env python3
"""Parse course PDFs with MinerU and collect OCR Markdown outputs."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import time
import zipfile
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_API_BASE = "https://mineru.net/api/v4"


def env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def safe_id(path: Path) -> str:
    stem = re.sub(r"[^0-9A-Za-z\u4e00-\u9fff._-]+", "_", path.stem).strip("_")
    return stem[:100] or "document"


def collect_pdfs(paths: list[str]) -> list[Path]:
    files: list[Path] = []
    for value in paths:
        path = Path(value).expanduser().resolve()
        if path.is_file() and path.suffix.lower() == ".pdf":
            files.append(path)
        elif path.is_dir():
            files.extend(sorted(item for item in path.rglob("*.pdf") if item.is_file()))
        else:
            raise SystemExit(f"not a PDF file or directory: {path}")
    unique = []
    seen = set()
    for path in files:
        if path not in seen:
            unique.append(path)
            seen.add(path)
    return unique


def mineru_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


def request_upload_urls(api_base: str, token: str, pdfs: list[Path], model_version: str, language: str) -> dict[str, Any]:
    payload = {
        "enable_formula": env_bool("MINERU_ENABLE_FORMULA", False),
        "enable_table": env_bool("MINERU_ENABLE_TABLE", False),
        "language": language,
        "model_version": model_version,
        "files": [
            {
                "name": f"{safe_id(path)}.pdf",
                "is_ocr": True,
                "data_id": safe_id(path),
            }
            for path in pdfs
        ],
    }
    response = requests.post(
        f"{api_base.rstrip('/')}/file-urls/batch",
        headers=mineru_headers(token),
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        timeout=60,
    )
    response.raise_for_status()
    result = response.json()
    if result.get("code") != 0:
        raise RuntimeError(f"MinerU upload-url request failed: {result}")
    return result["data"]


def upload_pdf(upload_url: str, path: Path) -> None:
    with path.open("rb") as fh:
        response = requests.put(upload_url, data=fh, timeout=600)
    response.raise_for_status()


def poll_results(api_base: str, token: str, batch_id: str, timeout: int, poll_interval: int) -> list[dict[str, Any]]:
    url = f"{api_base.rstrip('/')}/extract-results/batch/{batch_id}"
    started = time.time()
    last_summary = ""
    while True:
        if timeout > 0 and time.time() - started > timeout:
            raise TimeoutError(f"MinerU parse timeout after {timeout}s: {batch_id}")
        response = requests.get(url, headers=mineru_headers(token), timeout=60)
        response.raise_for_status()
        result = response.json()
        if result.get("code") != 0:
            raise RuntimeError(f"MinerU result request failed: {result}")
        extracts = result.get("data", {}).get("extract_result", [])
        states: dict[str, int] = {}
        for item in extracts:
            states[item.get("state", "unknown")] = states.get(item.get("state", "unknown"), 0) + 1
        summary = ", ".join(f"{key}:{value}" for key, value in sorted(states.items()))
        if summary and summary != last_summary:
            print(f"MinerU states: {summary}", flush=True)
            last_summary = summary
        if extracts and all(item.get("state") == "done" for item in extracts):
            return extracts
        failed = [item for item in extracts if item.get("state") == "failed"]
        if failed:
            raise RuntimeError(f"MinerU parse failed: {failed}")
        time.sleep(poll_interval)


def download_and_extract(item: dict[str, Any], output_dir: Path) -> Path:
    data_id = item["data_id"]
    target_dir = output_dir / "mineru" / data_id
    target_dir.mkdir(parents=True, exist_ok=True)
    zip_url = item.get("full_zip_url")
    if not zip_url:
        raise RuntimeError(f"missing full_zip_url for {data_id}")
    zip_path = target_dir / "full.zip"
    if not zip_path.exists():
        response = requests.get(zip_url, timeout=600)
        response.raise_for_status()
        zip_path.write_bytes(response.content)
    marker = target_dir / ".extracted"
    if not marker.exists():
        with zipfile.ZipFile(zip_path) as zf:
            zf.extractall(target_dir)
        marker.write_text(dt.datetime.now().isoformat(timespec="seconds"), encoding="utf-8")
    return target_dir


def find_markdown(root: Path) -> list[Path]:
    return sorted(path for path in root.rglob("*.md") if path.is_file())


def build_supplement(documents_dir: Path, source_map: dict[str, str]) -> Path:
    lines = [
        "# MinerU Document OCR Supplement",
        "",
        f"Generated at: {dt.datetime.now().isoformat(timespec='seconds')}",
        "",
        "This file collects OCR Markdown outputs for course distillation. It contains parsed document text only; use source paths for citation.",
        "",
    ]
    mineru_root = documents_dir / "mineru"
    for item_dir in sorted(path for path in mineru_root.iterdir() if path.is_dir()) if mineru_root.exists() else []:
        data_id = item_dir.name
        lines.append(f"## {data_id}")
        lines.append("")
        if data_id in source_map:
            lines.append(f"Source: `{source_map[data_id]}`")
            lines.append("")
        md_files = find_markdown(item_dir)
        if not md_files:
            lines.append("(No Markdown output found.)")
            lines.append("")
            continue
        for md_path in md_files:
            text = md_path.read_text(encoding="utf-8", errors="ignore").strip()
            if text:
                lines.append(text)
                lines.append("")
    output = documents_dir / "mineru_supplement.md"
    output.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return output


def main() -> None:
    load_dotenv()
    parser = argparse.ArgumentParser(description="Parse course PDFs with MinerU and collect OCR Markdown outputs.")
    parser.add_argument("--input", action="append", help="PDF file or directory. Repeatable.")
    parser.add_argument("--course-name", required=True)
    parser.add_argument("--base-dir", default=str(ROOT), help="Course output root. Defaults to this repo.")
    parser.add_argument("--model-version", default=os.getenv("MINERU_MODEL_VERSION", "vlm"))
    parser.add_argument("--language", default=os.getenv("MINERU_LANGUAGE", "ch"))
    parser.add_argument("--timeout", type=int, default=7200)
    parser.add_argument("--poll-interval", type=int, default=20)
    parser.add_argument("--skip-submit", action="store_true", help="Only rebuild supplement from existing MinerU output.")
    args = parser.parse_args()

    course_dir = Path(args.base_dir).expanduser().resolve() / args.course_name
    documents_dir = course_dir / "documents"
    documents_dir.mkdir(parents=True, exist_ok=True)

    source_map: dict[str, str] = {}
    if not args.skip_submit:
        if not args.input:
            raise SystemExit("--input is required unless --skip-submit is used")
        token = os.getenv("MINERU_API_TOKEN")
        api_base = os.getenv("MINERU_API_BASE", DEFAULT_API_BASE)
        if not token:
            raise SystemExit("MINERU_API_TOKEN is required unless --skip-submit is used")
        pdfs = collect_pdfs(args.input)
        if not pdfs:
            raise SystemExit("no PDF files found")
        upload_data = request_upload_urls(api_base, token, pdfs, args.model_version, args.language)
        batch_id = upload_data["batch_id"]
        upload_urls = upload_data.get("file_urls") or []
        if len(upload_urls) != len(pdfs):
            raise RuntimeError(f"upload URL count mismatch: {len(upload_urls)} urls for {len(pdfs)} PDFs")
        for path, item in zip(pdfs, upload_urls):
            data_id = item.get("data_id") or safe_id(path)
            source_map[data_id] = str(path)
            print(f"upload {path.name}", flush=True)
            upload_pdf(item["upload_url"], path)
        results = poll_results(api_base, token, batch_id, args.timeout, args.poll_interval)
        for item in results:
            download_and_extract(item, documents_dir)
        (documents_dir / "mineru_manifest.json").write_text(
            json.dumps(
                {
                    "batch_id": batch_id,
                    "generated_at": dt.datetime.now().isoformat(timespec="seconds"),
                    "sources": source_map,
                    "results": results,
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
    else:
        manifest = documents_dir / "mineru_manifest.json"
        if manifest.exists():
            data = json.loads(manifest.read_text(encoding="utf-8"))
            source_map = data.get("sources", {})

    supplement = build_supplement(documents_dir, source_map)
    print(f"wrote {supplement}")


if __name__ == "__main__":
    main()
