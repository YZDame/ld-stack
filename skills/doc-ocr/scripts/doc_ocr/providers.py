from __future__ import annotations

import base64
import json
import os
import shutil
import subprocess
import tempfile
import time
import urllib.error
import urllib.request
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class ProviderError(RuntimeError):
    pass


@dataclass
class ProviderResult:
    markdown: str
    raw: dict[str, Any]
    metadata: dict[str, Any]
    assets: list[tuple[str, bytes]]


def _json_request(
    url: str,
    *,
    method: str = "POST",
    payload: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    data: bytes | None = None,
    timeout: int = 900,
) -> dict[str, Any]:
    body = data
    request_headers = dict(headers or {})
    if payload is not None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        request_headers.setdefault("Content-Type", "application/json")
    request = urllib.request.Request(url, data=body, headers=request_headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:2000]
        raise ProviderError(f"HTTP {exc.code} from {url}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise ProviderError(f"request failed for {url}: {exc.reason}") from exc
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ProviderError(f"non-JSON response from {url}: {raw[:500]!r}") from exc


def _bytes_request(
    url: str,
    *,
    headers: dict[str, str] | None = None,
    timeout: int = 900,
) -> bytes:
    request = urllib.request.Request(url, headers=dict(headers or {}), method="GET")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.read()
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:2000]
        raise ProviderError(f"HTTP {exc.code} from download URL: {detail}") from exc
    except urllib.error.URLError as exc:
        raise ProviderError(f"download failed: {exc.reason}") from exc


def _strip_markdown_fence(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith("```markdown") and stripped.endswith("```"):
        return stripped[len("```markdown") : -3].strip()
    if stripped.startswith("```") and stripped.endswith("```"):
        return stripped[3:-3].strip()
    return stripped


class PaddleProvider:
    name = "paddleocr"
    default_job_url = "https://paddleocr.aistudio-app.com/api/v2/ocr/jobs"

    def available(self, config: dict[str, Any]) -> tuple[bool, str]:
        key_env = str(config.get("api_key_env", "PADDLE_OCR_API_KEY"))
        return (bool(os.getenv(key_env)), key_env)

    def run(self, path: Path, config: dict[str, Any]) -> ProviderResult:
        key_env = str(config.get("api_key_env", "PADDLE_OCR_API_KEY"))
        key = os.getenv(key_env)
        if not key:
            raise ProviderError(f"{key_env} is not set")
        job_url = str(config.get("job_url", self.default_job_url)).rstrip("/")
        headers = {"Authorization": f"bearer {key}"}
        model = str(config.get("model", "PaddleOCR-VL-1.6"))
        optional_payload = dict(
            config.get(
                "optional_payload",
                {
                    "useDocOrientationClassify": False,
                    "useDocUnwarping": False,
                    "useChartRecognition": False,
                },
            )
        )
        started = time.monotonic()
        submission = self._submit(path, job_url, headers, model, optional_payload)
        try:
            job_id = str(submission["data"]["jobId"])
        except (KeyError, TypeError) as exc:
            raise ProviderError(f"PaddleOCR submission did not return jobId: {submission}") from exc
        poll_interval = float(config.get("poll_interval_seconds", 5))
        poll_timeout = float(config.get("poll_timeout_seconds", 1800))
        polls = 0
        final_status: dict[str, Any] | None = None
        while time.monotonic() - started <= poll_timeout:
            polls += 1
            status = _json_request(f"{job_url}/{job_id}", method="GET", headers=headers)
            try:
                state = status["data"]["state"]
            except (KeyError, TypeError) as exc:
                raise ProviderError(f"PaddleOCR status response has no state: {status}") from exc
            if state == "done":
                final_status = status
                break
            if state == "failed":
                message = status.get("data", {}).get("errorMsg", "unknown error")
                raise ProviderError(f"PaddleOCR job {job_id} failed: {message}")
            if state not in {"pending", "running"}:
                raise ProviderError(f"PaddleOCR job {job_id} returned unknown state: {state}")
            time.sleep(poll_interval)
        if final_status is None:
            raise ProviderError(f"PaddleOCR job {job_id} timed out after {poll_timeout:g} seconds")
        try:
            jsonl_url = str(final_status["data"]["resultUrl"]["jsonUrl"])
        except (KeyError, TypeError) as exc:
            raise ProviderError(f"PaddleOCR job {job_id} returned no JSONL URL") from exc
        jsonl_text = _bytes_request(jsonl_url).decode("utf-8")
        records = []
        for line_number, line in enumerate(jsonl_text.splitlines(), 1):
            if not line.strip():
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ProviderError(f"invalid PaddleOCR JSONL at line {line_number}") from exc
        markdown, assets = _parse_paddle_records(records)
        raw = {
            "submission": submission,
            "final_status": final_status,
            "jsonl_records": records,
        }
        return ProviderResult(
            markdown,
            raw,
            {
                "elapsed_seconds": time.monotonic() - started,
                "job_id": job_id,
                "model": model,
                "poll_count": polls,
                "optional_payload": optional_payload,
            },
            assets,
        )

    def _submit(
        self,
        path: Path,
        job_url: str,
        headers: dict[str, str],
        model: str,
        optional_payload: dict[str, Any],
    ) -> dict[str, Any]:
        boundary = "----lectureocr" + uuid.uuid4().hex
        fields = {
            "model": model,
            "optionalPayload": json.dumps(optional_payload, ensure_ascii=False),
        }
        chunks: list[bytes] = []
        for name, value in fields.items():
            chunks.append(
                (
                    f"--{boundary}\r\nContent-Disposition: form-data; name=\"{name}\"\r\n\r\n"
                    f"{value}\r\n"
                ).encode("utf-8")
            )
        safe_filename = path.name.replace('"', "_")
        chunks.extend(
            [
                (
                    f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; "
                    f"filename=\"{safe_filename}\"\r\nContent-Type: {_mime(path)}\r\n\r\n"
                ).encode("utf-8"),
                path.read_bytes(),
                f"\r\n--{boundary}--\r\n".encode("utf-8"),
            ]
        )
        request_headers = dict(headers)
        request_headers["Content-Type"] = f"multipart/form-data; boundary={boundary}"
        return _json_request(job_url, headers=request_headers, data=b"".join(chunks), timeout=900)


def _parse_paddle_records(records: list[dict[str, Any]]) -> tuple[str, list[tuple[str, bytes]]]:
    pages: list[str] = []
    assets: list[tuple[str, bytes]] = []
    page_number = 0
    for record in records:
        result = record.get("result", {})
        for page in result.get("layoutParsingResults", []):
            page_number += 1
            markdown = page.get("markdown", {})
            pages.append(f"<!-- page: {page_number:03d} -->\n\n{markdown.get('text', '')}")
            for image_path, image_url in markdown.get("images", {}).items():
                safe_path = _safe_asset_path(str(image_path), f"p{page_number:03d}-figure.png")
                assets.append((safe_path, _bytes_request(str(image_url))))
            for image_name, image_url in page.get("outputImages", {}).items():
                safe_name = _safe_asset_path(str(image_name), f"output-{page_number:03d}")
                suffix = Path(safe_name).suffix or ".jpg"
                stem = str(Path(safe_name).with_suffix(""))
                assets.append((f"{stem}-p{page_number:03d}{suffix}", _bytes_request(str(image_url))))
    if not pages:
        raise ProviderError("PaddleOCR JSONL contained no layoutParsingResults")
    return "\n\n".join(pages), assets


def _safe_asset_path(value: str, fallback: str) -> str:
    candidate = Path(value.lstrip("/"))
    if not value or ".." in candidate.parts:
        return fallback
    return str(candidate)


class MinerUProvider:
    name = "mineru"

    def available(self, config: dict[str, Any]) -> tuple[bool, str]:
        executable = shutil.which(str(config.get("executable", "mineru-open-api")))
        mode = str(config.get("mode", "precision"))
        if not executable:
            return False, "mineru-open-api executable"
        if mode == "precision" and not (os.getenv("MINERU_TOKEN") or os.getenv("MINERU_API_TOKEN")):
            check = subprocess.run(
                [executable, "auth", "--show"], capture_output=True, text=True, timeout=10, check=False
            )
            if check.returncode != 0 or "Token source:" not in check.stdout:
                return False, "MINERU_TOKEN or `mineru-open-api auth`"
        return True, executable

    def run(self, path: Path, config: dict[str, Any]) -> ProviderResult:
        executable = shutil.which(str(config.get("executable", "mineru-open-api")))
        if not executable:
            raise ProviderError("mineru-open-api is not installed")
        mode = str(config.get("mode", "precision"))
        with tempfile.TemporaryDirectory(prefix="lecture-ocr-mineru-") as directory:
            temporary_output = Path(directory)
            command = [
                executable,
                "flash-extract" if mode == "flash" else "extract",
                str(path),
                "-o",
                str(temporary_output),
            ]
            if mode != "flash":
                command.extend(["-f", "md", "--ocr", "--formula", "--table"])
                model = str(config.get("model", "pipeline"))
                if model:
                    command.extend(["--model", model])
            command.extend(["--language", str(config.get("language", "ch"))])
            started = time.monotonic()
            result = subprocess.run(
                command, capture_output=True, text=True, timeout=int(config.get("timeout", 1800))
            )
            if result.returncode != 0:
                raise ProviderError(f"MinerU exited {result.returncode}: {result.stderr[-2000:]}")
            markdown_files = sorted(temporary_output.rglob("*.md"))
            markdown = "\n\n".join(file.read_text(encoding="utf-8") for file in markdown_files)
            assets = [
                (str(file.relative_to(temporary_output)), file.read_bytes())
                for file in temporary_output.rglob("*")
                if file.is_file() and file.suffix.lower() != ".md"
            ]
            raw = {
                "command": [part if part != str(temporary_output) else "<output-dir>" for part in command[1:]],
                "stdout": result.stdout,
                "stderr": result.stderr,
                "files": [str(file.relative_to(temporary_output)) for file in temporary_output.rglob("*") if file.is_file()],
            }
            return ProviderResult(
                markdown.strip(),
                raw,
                {"elapsed_seconds": time.monotonic() - started, "mode": mode},
                assets,
            )


class MistralProvider:
    name = "mistral"
    base_url = "https://api.mistral.ai/v1"

    def available(self, config: dict[str, Any]) -> tuple[bool, str]:
        key_env = str(config.get("api_key_env", "MISTRAL_API_KEY"))
        return (bool(os.getenv(key_env)), key_env)

    def run(self, path: Path, config: dict[str, Any]) -> ProviderResult:
        key_env = str(config.get("api_key_env", "MISTRAL_API_KEY"))
        key = os.getenv(key_env)
        if not key:
            raise ProviderError(f"{key_env} is not set")
        headers = {"Authorization": f"Bearer {key}"}
        started = time.monotonic()
        file_id: str | None = None
        cleanup: dict[str, Any] = {"uploaded_file_deleted": None}
        try:
            if path.suffix.lower() == ".pdf":
                uploaded = self._upload(path, headers)
                file_id = str(uploaded["id"])
                signed = _json_request(
                    f"{self.base_url}/files/{file_id}/url?expiry=1", method="GET", headers=headers
                )
                document = {"type": "document_url", "document_url": signed["url"]}
            else:
                mime = _mime(path)
                encoded = base64.b64encode(path.read_bytes()).decode("ascii")
                document = {"type": "image_url", "image_url": f"data:{mime};base64,{encoded}"}
            raw = _json_request(
                f"{self.base_url}/ocr",
                headers=headers,
                payload={
                    "model": config.get("model", "mistral-ocr-latest"),
                    "document": document,
                    "include_image_base64": True,
                    "include_blocks": True,
                    "table_format": "markdown",
                },
            )
        finally:
            if file_id and bool(config.get("delete_uploaded_file", True)):
                try:
                    _json_request(f"{self.base_url}/files/{file_id}", method="DELETE", headers=headers)
                    cleanup["uploaded_file_deleted"] = True
                except ProviderError as exc:
                    cleanup["uploaded_file_deleted"] = False
                    cleanup["delete_error"] = str(exc)
        markdown_parts = []
        assets: list[tuple[str, bytes]] = []
        for index, page in enumerate(raw.get("pages", []), 1):
            markdown_parts.append(f"<!-- page: {index:03d} -->\n\n{page.get('markdown', '')}")
            for image_index, image in enumerate(page.get("images", []), 1):
                encoded = image.get("image_base64") or image.get("base64")
                if encoded:
                    encoded = encoded.split(",", 1)[-1]
                    assets.append((f"p{index:03d}-figure-{image_index:02d}.png", base64.b64decode(encoded)))
        return ProviderResult(
            "\n\n".join(markdown_parts),
            raw,
            {"elapsed_seconds": time.monotonic() - started, "cleanup": cleanup},
            assets,
        )

    def _upload(self, path: Path, headers: dict[str, str]) -> dict[str, Any]:
        boundary = "----lectureocr" + uuid.uuid4().hex
        content = path.read_bytes()
        chunks = [
            f"--{boundary}\r\nContent-Disposition: form-data; name=\"purpose\"\r\n\r\nocr\r\n".encode(),
            (
                f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; "
                f"filename=\"{path.name}\"\r\nContent-Type: {_mime(path)}\r\n\r\n"
            ).encode(),
            content,
            f"\r\n--{boundary}--\r\n".encode(),
        ]
        request_headers = dict(headers)
        request_headers["Content-Type"] = f"multipart/form-data; boundary={boundary}"
        return _json_request(
            f"{self.base_url}/files", headers=request_headers, data=b"".join(chunks), timeout=900
        )


class GeminiProvider:
    name = "gemini"

    def available(self, config: dict[str, Any]) -> tuple[bool, str]:
        key_env = str(config.get("api_key_env", "GEMINI_API_KEY"))
        return (bool(os.getenv(key_env)), key_env)

    def run(self, path: Path, config: dict[str, Any]) -> ProviderResult:
        key_env = str(config.get("api_key_env", "GEMINI_API_KEY"))
        key = os.getenv(key_env)
        if not key:
            raise ProviderError(f"{key_env} is not set")
        if path.stat().st_size > int(config.get("inline_limit_bytes", 50 * 1024 * 1024)):
            raise ProviderError("Gemini inline input exceeds 50 MB; Files API support is required")
        model = str(config.get("model", "gemini-3.5-flash"))
        prompt = str(config.get("prompt", _GEMINI_PROMPT))
        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [
                        {
                            "inline_data": {
                                "mime_type": _mime(path),
                                "data": base64.b64encode(path.read_bytes()).decode("ascii"),
                            }
                        },
                        {"text": prompt},
                    ],
                }
            ],
            "generationConfig": {"temperature": 0},
        }
        started = time.monotonic()
        raw = _json_request(
            f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
            headers={"x-goog-api-key": key},
            payload=payload,
        )
        texts: list[str] = []
        for candidate in raw.get("candidates", []):
            for part in candidate.get("content", {}).get("parts", []):
                if isinstance(part.get("text"), str):
                    texts.append(part["text"])
        if not texts:
            raise ProviderError(f"Gemini returned no text: {json.dumps(raw, ensure_ascii=False)[:1000]}")
        return ProviderResult(
            _strip_markdown_fence("\n".join(texts)),
            raw,
            {"elapsed_seconds": time.monotonic() - started, "model": model},
            [],
        )


_GEMINI_PROMPT = """Transcribe this teaching document into source-faithful Markdown.
Preserve headings, paragraphs, lists, tables, mathematical formulas in LaTeX, and reading order.
Insert `<!-- page: NNN -->` before every page, using three-digit page numbers.
Do not summarize, solve, explain, repair, or silently guess. Mark illegible spans as `[UNCLEAR: ...]`.
Return Markdown only, without a code fence."""


def _mime(path: Path) -> str:
    import mimetypes

    return mimetypes.guess_type(path.name)[0] or "application/octet-stream"


PROVIDERS = {
    "paddleocr": PaddleProvider(),
    "mineru": MinerUProvider(),
    "mistral": MistralProvider(),
    "gemini": GeminiProvider(),
}
