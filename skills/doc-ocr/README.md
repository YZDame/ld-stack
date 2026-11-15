# Doc OCR Skill

General-purpose multi-backend document & handwritten math OCR router and assembler (pure Python standard library).

## Features

- **`doc_ocr.py doctor`**: Checks local configuration for `paddleocr`, `mineru`, `mistral`, and `gemini` without uploading any files.
- **`doc_ocr.py route`**: Inspects a PDF or image and ranks the best backend based on `--material`, `--formula-density`, `--tables`, `--diagrams`, `--poor-quality`, and `--language`.
- **`doc_ocr.py run`**: Executes the top ready backend (with configurable `--fallbacks`) and stores `output.md`, `raw_response.json`, `metadata.json`, and extracted `assets/`.
- **`doc_ocr.py assemble`**: Merges multi-chunk or sequential OCR run folders into `combined.md`, per-page Markdown files, remapped `assets/`, and `document_manifest.json` (with `--layout lecture` option for LaTeX lecture project directory layout).
- **`mistral_ocr.py`**: Direct standalone client for Mistral's `/v1/ocr` endpoint (supports HTTP URLs, zero-based `--pages`, `--table-format`, `--include-blocks`, `--confidence`).

## Environment Variables

Set only the providers you intend to use:

- `PADDLE_OCR_API_KEY`: PaddleOCR AIStudio API key (`PaddleOCR-VL-1.6`)
- `MINERU_TOKEN` (or `mineru-open-api auth`): MinerU precision CLI token
- `MISTRAL_API_KEY`: Mistral API key (`mistral-ocr-latest`)
- `GEMINI_API_KEY`: Google Gemini API key (`gemini-3.5-flash`)
