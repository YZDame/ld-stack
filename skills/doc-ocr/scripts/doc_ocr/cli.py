from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .providers import PROVIDERS, ProviderError
from .router import BACKENDS, choose_backends, inspect_document


DEFAULT_CONFIG = Path(__file__).with_name("ocr-router.example.json")
PAGE_RE = re.compile(r"<!--\s*[Pp]age:\s*(\d+)\s*-->")
IMAGE_RE = re.compile(r'(?:src="|]\()(?:assets/)?imgs/([^")]+)')
CHUNK_RE = re.compile(r"pages-(\d+)-(\d+)\.pdf$")


def load_config(path: Path | None) -> dict[str, Any]:
    candidate = path or DEFAULT_CONFIG
    if not candidate.exists():
        return {"providers": {}}
    with candidate.open(encoding="utf-8") as handle:
        return json.load(handle)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="doc-ocr", description="Unified document OCR router and assembler")
    parser.add_argument("--config", type=Path, help="JSON configuration file")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("doctor", help="check provider configuration without uploading files")

    route = subparsers.add_parser("route", help="inspect a file and explain backend ranking")
    _add_profile_arguments(route)

    run = subparsers.add_parser("run", help="route and run OCR")
    _add_profile_arguments(run)
    run.add_argument("--backend", choices=("auto",) + BACKENDS, default="auto")
    run.add_argument("--fallbacks", type=int, default=1, choices=range(0, 4))
    run.add_argument("--project-id", "--craft-id", dest="project_id", required=True)
    run.add_argument("--output-root", type=Path, default=Path("projects"))
    run.add_argument(
        "--run-root",
        type=Path,
        help="write timestamped runs directly below this directory (for example, project/runs/full)",
    )
    run.add_argument("--allow-upload", action="store_true", help="confirm third-party upload")
    run.add_argument("--dry-run", action="store_true")

    assemble = subparsers.add_parser("assemble", help="assemble pagewise/chunked OCR runs into unified Markdown")
    assemble.add_argument("ocr_root", type=Path, help="Directory containing timestamped or per-backend OCR runs")
    assemble.add_argument("output_root", type=Path, help="Destination root directory for assembled outputs")
    assemble.add_argument(
        "--layout",
        choices=("standard", "lecture"),
        default="standard",
        help="Output layout: standard (combined.md + assets/) or lecture (extraction/ocr/ + figures/)",
    )
    return parser


def _add_profile_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("input", type=Path)
    parser.add_argument(
        "--material",
        choices=("auto", "printed_pdf", "scanned_pdf", "photo", "handwritten", "mixed"),
        default="auto",
    )
    parser.add_argument("--language", default="zh")
    parser.add_argument("--formula-density", choices=("low", "medium", "high"), default="medium")
    parser.add_argument("--tables", action="store_true")
    parser.add_argument("--diagrams", action="store_true")
    parser.add_argument("--poor-quality", action="store_true")


def _profile(args: argparse.Namespace):
    return inspect_document(
        args.input,
        material=args.material,
        language=args.language,
        formula_density=args.formula_density,
        has_tables=args.tables,
        has_diagrams=args.diagrams,
        poor_quality=args.poor_quality,
    )


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _split_pages(markdown: str) -> list[tuple[int, str]]:
    matches = list(PAGE_RE.finditer(markdown))
    if not matches:
        return [(1, markdown.strip() + "\n")] if markdown.strip() else []
    pages: list[tuple[int, str]] = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(markdown)
        pages.append((int(match.group(1)), markdown[match.start():end].strip() + "\n"))
    return pages


def _discover_runs(ocr_root: Path) -> list[tuple[int, int, Path, dict[str, Any]]]:
    metadata_files = sorted(ocr_root.rglob("metadata.json"))
    chunked: list[tuple[int, int, Path, dict[str, Any]]] = []
    sequential: list[tuple[str, Path, dict[str, Any]]] = []
    for metadata_path in metadata_files:
        run_dir = metadata_path.parent
        if not (run_dir / "output.md").is_file():
            continue
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        source_path = Path(metadata.get("source", {}).get("path", ""))
        match = CHUNK_RE.search(source_path.name)
        if match:
            chunked.append((int(match.group(1)), int(match.group(2)), run_dir, metadata))
        else:
            sequential.append((metadata.get("created_at", run_dir.name), run_dir, metadata))

    if chunked:
        chunked.sort(key=lambda item: (item[0], item[1]))
        return chunked

    if not sequential:
        raise RuntimeError(f"no OCR runs with metadata.json + output.md found under {ocr_root}")

    runs: list[tuple[int, int, Path, dict[str, Any]]] = []
    cursor = 1
    for _, run_dir, metadata in sorted(sequential, key=lambda item: item[0]):
        text = (run_dir / "output.md").read_text(encoding="utf-8")
        pages = _split_pages(text)
        count = max(len(pages), 1)
        runs.append((cursor, cursor + count - 1, run_dir, metadata))
        cursor += count
    return runs


def _cmd_assemble(ocr_root: Path, output_root: Path, layout: str) -> int:
    if not ocr_root.exists():
        raise FileNotFoundError(f"OCR root does not exist: {ocr_root}")

    if layout == "lecture":
        page_dir = output_root / "extraction" / "ocr" / "pages"
        chunk_dir = output_root / "extraction" / "ocr" / "chunks"
        figure_root = output_root / "figures" / "source-images"
        combined_path = output_root / "extraction" / "ocr" / "text.md"
        manifest_path = output_root / "figures" / "inventory" / "inventory.json"
    else:
        page_dir = output_root / "pages"
        chunk_dir = output_root / "chunks"
        figure_root = output_root / "assets"
        combined_path = output_root / "combined.md"
        manifest_path = output_root / "document_manifest.json"

    for directory in (page_dir, chunk_dir, figure_root, manifest_path.parent):
        directory.mkdir(parents=True, exist_ok=True)

    runs = _discover_runs(ocr_root)
    inventory: list[dict[str, Any]] = []
    merged_pages: list[str] = []
    seen_pages: set[int] = set()

    for chunk_start, chunk_end, run_dir, _ in runs:
        markdown_path = run_dir / "output.md"
        markdown = markdown_path.read_text(encoding="utf-8")
        shutil.copy2(markdown_path, chunk_dir / f"pages-{chunk_start:03d}-{chunk_end:03d}.md")
        local_pages = _split_pages(markdown)
        expected = chunk_end - chunk_start + 1
        if len(local_pages) != expected:
            raise RuntimeError(f"{run_dir.name}: expected {expected} pages, found {len(local_pages)}")

        for local_page, page_text in local_pages:
            global_page = chunk_start + local_page - 1
            if global_page in seen_pages:
                raise RuntimeError(f"duplicate global page {global_page}")
            seen_pages.add(global_page)
            page_figure_dir = figure_root / f"page-{global_page:03d}"
            page_figure_dir.mkdir(parents=True, exist_ok=True)

            names = IMAGE_RE.findall(page_text)
            for name in names:
                source = run_dir / "assets" / "imgs" / name
                if not source.exists():
                    alt_source = run_dir / "assets" / name
                    if alt_source.exists():
                        source = alt_source
                    else:
                        raise FileNotFoundError(source)
                target = page_figure_dir / Path(name).name
                shutil.copy2(source, target)
                inventory.append(
                    {
                        "id": f"p{global_page:03d}-{target.stem}",
                        "page": global_page,
                        "filename": target.name,
                        "path": str(target.relative_to(output_root)),
                        "sha256": _sha256(target),
                        "status": "PENDING_VECTOR_REVIEW",
                    }
                )

            header = f"<!-- page: {global_page:03d} -->"
            base_text = (
                PAGE_RE.sub(header, page_text, count=1)
                if PAGE_RE.search(page_text)
                else f"{header}\n\n{page_text}"
            )
            page_rel_prefix = "../../../figures/source-images" if layout == "lecture" else "../assets"
            merged_rel_prefix = "../../figures/source-images" if layout == "lecture" else "assets"

            def _rewrite(prefix: str, text: str) -> str:
                return IMAGE_RE.sub(
                    lambda match: (
                        f'src="{prefix}/page-{global_page:03d}/{Path(match.group(1)).name}"'
                        if 'src="' in match.group(0)
                        else f']({prefix}/page-{global_page:03d}/{Path(match.group(1)).name})'
                    ),
                    text,
                )

            (page_dir / f"page-{global_page:03d}.md").write_text(
                _rewrite(page_rel_prefix, base_text), encoding="utf-8"
            )
            merged_pages.append(_rewrite(merged_rel_prefix, base_text).rstrip())

    expected_pages = set(range(runs[0][0], runs[-1][1] + 1))
    if seen_pages != expected_pages:
        raise RuntimeError(f"page coverage mismatch: {sorted(seen_pages)}")

    combined_path.write_text("\n\n".join(merged_pages) + "\n", encoding="utf-8")
    manifest_path.write_text(json.dumps(inventory, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "status": "ok",
                "layout": layout,
                "pages": len(seen_pages),
                "figures": len(inventory),
                "combined_markdown": str(combined_path),
                "manifest": str(manifest_path),
            },
            ensure_ascii=False,
        )
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "assemble":
        try:
            return _cmd_assemble(args.ocr_root.expanduser(), args.output_root.expanduser(), args.layout)
        except (OSError, RuntimeError, ValueError) as exc:
            print(json.dumps({"status": "failed", "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
            return 1

    config = load_config(args.config)
    provider_configs = config.get("providers", {})

    if args.command == "doctor":
        rows = []
        for name in BACKENDS:
            available, detail = PROVIDERS[name].available(provider_configs.get(name, {}))
            rows.append({"backend": name, "ready": available, "detail": detail})
        print(json.dumps(rows, ensure_ascii=False, indent=2))
        return 0 if any(row["ready"] for row in rows) else 2

    profile = _profile(args)
    decision = choose_backends(profile)
    if args.command == "route":
        print(json.dumps({"profile": profile.to_dict(), "decision": decision.to_dict()}, ensure_ascii=False, indent=2))
        return 0

    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,79}", args.project_id):
        parser.error("--project-id must use 1-80 ASCII letters, digits, dots, underscores, or hyphens")
    selected = [args.backend] if args.backend != "auto" else list(decision.ranked_backends)
    readiness = {}
    for backend in selected:
        available, detail = PROVIDERS[backend].available(provider_configs.get(backend, {}))
        readiness[backend] = {"ready": available, "detail": detail}
    ready_order = [backend for backend in selected if readiness[backend]["ready"]]
    max_attempts = 1 if args.backend != "auto" else 1 + args.fallbacks
    plan = {
        "profile": profile.to_dict(),
        "decision": decision.to_dict(),
        "provider_readiness": readiness,
        "attempt_order": ready_order[:max_attempts],
    }
    if args.dry_run:
        print(json.dumps(plan, ensure_ascii=False, indent=2))
        return 0
    if not args.allow_upload:
        parser.error("run uploads source material; pass --allow-upload after confirming permission")

    errors: list[dict[str, str]] = []
    attempts = 0
    for backend in selected:
        provider = PROVIDERS[backend]
        backend_config = provider_configs.get(backend, {})
        available, detail = provider.available(backend_config)
        if not available:
            errors.append({"backend": backend, "error": f"not ready: {detail}"})
            continue
        if attempts >= max_attempts:
            break
        attempts += 1
        try:
            result = provider.run(args.input.resolve(), backend_config)
        except (ProviderError, OSError, TimeoutError) as exc:
            errors.append({"backend": backend, "error": str(exc)})
            continue
        output_dir = _save_result(args, backend, profile.to_dict(), decision.to_dict(), result, errors)
        print(json.dumps({"status": "ok", "backend": backend, "output_dir": str(output_dir)}, ensure_ascii=False))
        return 0
    print(json.dumps({"status": "failed", "errors": errors}, ensure_ascii=False, indent=2), file=sys.stderr)
    return 1


def _save_result(args, backend, profile, decision, result, prior_errors):
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_root = args.run_root or (args.output_root / args.project_id)
    output_dir = run_root / "ocr" / backend / run_id
    assets_dir = output_dir / "assets"
    output_dir.mkdir(parents=True, exist_ok=False)
    if result.assets:
        assets_dir.mkdir()
        for name, content in result.assets:
            asset_path = assets_dir / name
            asset_path.parent.mkdir(parents=True, exist_ok=True)
            asset_path.write_bytes(content)
    source_hash = hashlib.sha256(args.input.read_bytes()).hexdigest()
    metadata = {
        "schema_version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "backend": backend,
        "source": {**profile, "sha256": source_hash},
        "route": decision,
        "prior_attempt_errors": prior_errors,
        "provider": result.metadata,
        "environment_keys_present": {
            name: bool(os.getenv(name))
            for name in (
                "PADDLE_OCR_API_KEY",
                "MINERU_TOKEN",
                "MINERU_API_TOKEN",
                "MISTRAL_API_KEY",
                "GEMINI_API_KEY",
            )
        },
    }
    (output_dir / "output.md").write_text(result.markdown.rstrip() + "\n", encoding="utf-8")
    (output_dir / "raw_response.json").write_text(
        json.dumps(result.raw, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (output_dir / "metadata.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return output_dir


if __name__ == "__main__":
    raise SystemExit(main())
