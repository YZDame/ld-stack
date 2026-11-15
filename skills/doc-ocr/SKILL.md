---
name: doc-ocr
description: >
  General multi-provider document and handwritten math OCR skill routing across PaddleOCR-VL, MinerU, Mistral OCR, and Gemini, plus pagewise assembly of OCR Markdown and figure crops. Use when extracting Markdown, LaTeX equations, tables, and figure assets from PDFs, scanned pages, handwritten board photos, or mixed lecture materials. 中文触发：文档 OCR、PDF 转 Markdown、手写板书识别、公式识别、多引擎 OCR 路由、Mistral OCR、PaddleOCR、MinerU、分片 OCR 组装。
---

# Document OCR (Multi-Provider Router & Direct Clients)

Extract source-faithful Markdown, LaTeX formulas, tables, and cropped figure images from PDFs, scanned documents, photos, and public URLs. Treat OCR output as a **faithful intermediate extraction artifact**—preserve uncertainty markers and original images; do not invent missing math or declare final publication approval from OCR alone.

---

## Available Tools & Backends

| Backend | Best For | Env / Binary Required |
| --- | --- | --- |
| `paddleocr` (`PaddleOCR-VL-1.6`) | Handwritten boards, smartphone photos, skewed or low-quality scans | `PADDLE_OCR_API_KEY` |
| `mineru` (`mineru-open-api`) | Printed math/physics PDFs, dense inline/display formulas, tables | `mineru-open-api` CLI + `MINERU_TOKEN` (or `flash` mode) |
| `mistral` (`mistral-ocr-latest`) | Scanned multi-page PDFs, structured tables, multilingual docs, public URLs | `MISTRAL_API_KEY` |
| `gemini` (`gemini-3.5-flash`) | Complex diagrams mixed with text, quick visual page transcription | `GEMINI_API_KEY` |

---

## Workflow

1. **Check available backends (no upload)**:
   ```bash
   python3 "<SKILL_DIR>/scripts/doc_ocr.py" doctor
   ```
2. **Inspect document & rank backends**:
   ```bash
   python3 "<SKILL_DIR>/scripts/doc_ocr.py" route path/to/input.pdf --material handwritten --formula-density high
   ```
   Supported `--material`: `auto`, `printed_pdf`, `scanned_pdf`, `photo`, `handwritten`, `mixed`.
   Optional flags: `--language zh`, `--formula-density low|medium|high`, `--tables`, `--diagrams`, `--poor-quality`.
3. **Run multi-provider OCR (with automatic fallback)**:
   ```bash
   python3 "<SKILL_DIR>/scripts/doc_ocr.py" run path/to/input.pdf \
     --project-id my-doc \
     --material scanned_pdf \
     --allow-upload
   ```
   Use `--backend mistral|paddleocr|mineru|gemini` to pin a backend, `--dry-run` to preview the readiness plan without uploading, and `--run-root <dir>` to control output placement.
   Outputs are written under `<run-root>/ocr/<backend>/<timestamp>/`:
   - `output.md`: page-anchored Markdown (`<!-- page: NNN -->`)
   - `raw_response.json`: raw API / CLI output
   - `metadata.json`: provenance, SHA-256 hash, route scores, and errors
   - `assets/`: extracted cropped figures and layout images
4. **Assemble multi-chunk / pagewise OCR runs** (especially PaddleOCR chunks named `pages-001-010.pdf`, etc.):
   ```bash
   python3 "<SKILL_DIR>/scripts/doc_ocr.py" assemble <ocr_root> <out_root>
   ```
   Merges chunks in page order, remaps image references cleanly, and produces `combined.md` + `pages/page-NNN.md` + `assets/` + `document_manifest.json` (or use `--layout lecture` for `extraction/ocr/` + `figures/inventory/inventory.json` compatibility).
5. **Direct Mistral OCR helper** (no third-party packages; supports public HTTP(S) URLs, `--pages`, `--table-format`, `--include-blocks`, `--confidence`):
   ```bash
   python3 "<SKILL_DIR>/scripts/mistral_ocr.py" "path/to/doc_or_url" --output "./mistral-out"
   ```

---

## Privacy & Safety Rules

- **Never log, echo, or commit API keys** (`PADDLE_OCR_API_KEY`, `MINERU_TOKEN`, `MISTRAL_API_KEY`, `GEMINI_API_KEY`). Check presence only (`test -n "${KEY:-}"`).
- Passing `--allow-upload` (or invoking `mistral_ocr.py` without `--no-upload`) confirms uploading only the targeted document to the selected OCR provider. If the user explicitly mandates local-only offline processing, do not upload to cloud APIs; report the local-only constraint.
- **Faithfulness boundary**: Keep `[?]` or `[UNCLEAR: ...]` markers intact when passing OCR text downstream to `math-exposition` or `LaTeX` editing workflows.
