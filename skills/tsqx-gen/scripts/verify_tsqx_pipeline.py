#!/usr/bin/env python3
"""
Compile and verify a TSQX file through the local tsqx -> asy -> pdf (+ PNG) pipeline.

Supports zero-boilerplate CSS-like ldgeo.asy theme injection, standalone ASY export,
PDF bounding-box sanity checks, and optional PNG rendering for visual inspection.
"""

from __future__ import annotations

import argparse
import os
import re
import shlex
import shutil
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

SKILL_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_LDGEO = SKILL_ROOT / "assets" / "ldgeo.asy"

VALID_THEMES = ("none", "classic", "print", "flexoki", "colormath", "slides")
SCALE_SIZES = {
    "compact": "5.5cm",
    "standard": "7.5cm",
    "wide": "11.5cm",
}

SEMANTIC_TOKEN_RE = re.compile(
    r"(?:/\s*[^#\n]*\b(?:given|aux|aux2|key|accent|circ|circ2|mark|fill1|fill2|fillkey)\b)"
    r"|\b(?:otherPt|other|perpPt|paraPt|bisectorPt|extBisectorPt|tangentPt|tangentPtR|"
    r"rightanglemark|anglemark|pathtick|radicalAxis|"
    r"check_perp|check_parallel|check_collinear|check_cyclic|check_on_circle|check_equal_dist)\b"
)
PDFINFO_PAGE_SIZE_RE = re.compile(r"Page size:\s*([0-9.]+)\s*x\s*([0-9.]+)\s*pts")


def run(
    cmd: list[str],
    *,
    stdin_path: Path | None = None,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    if stdin_path is None:
        return subprocess.run(cmd, cwd=cwd, env=env, text=True, capture_output=True, check=False)
    with stdin_path.open("r", encoding="utf-8") as fh:
        return subprocess.run(cmd, stdin=fh, cwd=cwd, env=env, text=True, capture_output=True, check=False)


def uses_ldgeo_features(source_text: str) -> bool:
    return bool(SEMANTIC_TOKEN_RE.search(source_text))


def inline_ldgeo_into_asy(asy_source: str, ldgeo_path: Path, theme: str) -> str:
    ldgeo_code = ldgeo_path.read_text(encoding="utf-8").strip()
    ldgeo_code = re.sub(
        r"applytheme\(_ldgeo_init_theme\(\)\);",
        f'applytheme("{theme}");',
        ldgeo_code,
    )
    block = (
        f"\n// --- Begin inlined ldgeo.asy (theme: {theme}) ---\n"
        f"{ldgeo_code}\n"
        f"// --- End inlined ldgeo.asy ---\n"
    )
    size_match = re.search(r"^size\([^)]*\);\s*$", asy_source, flags=re.MULTILINE)
    if size_match:
        return asy_source[: size_match.end()] + block + asy_source[size_match.end() :]
    return block + "\n" + asy_source


def inspect_pdf_geometry(pdf_path: Path) -> list[str]:
    warnings: list[str] = []
    if shutil.which("pdfinfo") is None:
        return warnings
    proc = run(["pdfinfo", str(pdf_path)])
    if proc.returncode != 0:
        return warnings
    match = PDFINFO_PAGE_SIZE_RE.search(proc.stdout)
    if not match:
        return warnings
    w_pt, h_pt = float(match.group(1)), float(match.group(2))
    if w_pt <= 0 or h_pt <= 0:
        warnings.append(f"Degenerate PDF dimensions: {w_pt:.1f}x{h_pt:.1f} pt")
        return warnings
    ratio = max(w_pt, h_pt) / min(w_pt, h_pt)
    if ratio > 4.0:
        warnings.append(
            f"Extreme PDF aspect ratio ({ratio:.2f}:1, {w_pt:.0f}x{h_pt:.0f} pt); "
            "check for runaway intersections or overly long extensions."
        )
    if min(w_pt, h_pt) < 25:
        warnings.append(f"Very narrow PDF dimension ({min(w_pt, h_pt):.1f} pt); possible collinear degeneracy.")
    return warnings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verify a TSQX file with local tools.")
    parser.add_argument("input", help="Path to the .tsqx file")
    parser.add_argument("--tsqx-cmd", default="python3 -m tsqx", help="Command used to run tsqx")
    parser.add_argument("--asy-cmd", default="asy", help="Command used to run Asymptote")
    parser.add_argument(
        "--output-dir",
        help="Directory for generated .asy/.pdf/.png files; defaults to the input file directory",
    )
    parser.add_argument("--no-pdf", action="store_true", help="Stop after generating .asy")
    parser.add_argument("--pre", action="store_true", help="Pass -p/--pre to tsqx")
    parser.add_argument(
        "--theme",
        choices=("auto", *VALID_THEMES),
        default="auto",
        help="ldgeo.asy theme preset ('auto' injects 'classic' when ldgeo tokens/helpers appear)",
    )
    parser.add_argument(
        "--ldgeo",
        default=str(DEFAULT_LDGEO),
        help="Path to ldgeo.asy (defaults to bundled assets/ldgeo.asy)",
    )
    parser.add_argument(
        "--scale",
        choices=tuple(SCALE_SIZES.keys()),
        default=None,
        help="Preset physical canvas width (compact=5.5cm, standard=7.5cm, wide=11.5cm)",
    )
    parser.add_argument("--size", default=None, help="Explicit -s/--size value for tsqx")
    parser.add_argument(
        "--standalone",
        action="store_true",
        help="Inline ldgeo.asy and the selected theme into the generated .asy file",
    )
    parser.add_argument(
        "--check-png",
        action="store_true",
        help="Render a 180 DPI PNG alongside the PDF for visual inspection",
    )
    args = parser.parse_args(argv)

    input_path = Path(args.input).expanduser().resolve()
    if not input_path.exists():
        print(f"[ERROR] Input not found: {input_path}", file=sys.stderr)
        return 1

    source_text = input_path.read_text(encoding="utf-8")
    if args.theme == "auto":
        effective_theme = "classic" if uses_ldgeo_features(source_text) else "none"
    else:
        effective_theme = args.theme

    use_ldgeo = effective_theme != "none"
    ldgeo_path = Path(args.ldgeo).expanduser().resolve()
    if use_ldgeo and not ldgeo_path.is_file():
        print(f"[ERROR] ldgeo.asy not found: {ldgeo_path}", file=sys.stderr)
        return 1

    output_dir = (
        Path(args.output_dir).expanduser().resolve()
        if args.output_dir
        else input_path.parent
    )
    output_dir.mkdir(parents=True, exist_ok=True)

    out_asy = output_dir / f"{input_path.stem}.asy"
    out_pdf = output_dir / f"{input_path.stem}.pdf"
    out_png = output_dir / f"{input_path.stem}.png"

    try:
        tsqx_cmd = shlex.split(args.tsqx_cmd)
        asy_cmd = shlex.split(args.asy_cmd)
    except ValueError as error:
        print(f"[ERROR] Invalid command argument: {error}", file=sys.stderr)
        return 1

    if not tsqx_cmd or shutil.which(tsqx_cmd[0]) is None:
        print(f"[ERROR] tsqx command not found: {args.tsqx_cmd}", file=sys.stderr)
        return 1
    if not args.no_pdf and (not asy_cmd or shutil.which(asy_cmd[0]) is None):
        print(f"[ERROR] asy command not found: {args.asy_cmd}", file=sys.stderr)
        return 1

    size = args.size or (SCALE_SIZES[args.scale] if args.scale else None)

    with TemporaryDirectory(prefix=f".{input_path.stem}-verify-", dir=output_dir) as workdir:
        staging = Path(workdir)
        staged_asy = staging / f"{input_path.stem}.asy"
        staged_pdf = staging / f"{input_path.stem}.pdf"

        tsqx_full = [*tsqx_cmd]
        if args.pre:
            tsqx_full.append("-p")
        if size:
            tsqx_full.extend(["-s", size])
        tsqx_result = run(tsqx_full, stdin_path=input_path)
        if tsqx_result.returncode != 0:
            print("[ERROR] tsqx step failed", file=sys.stderr)
            if tsqx_result.stderr.strip():
                print(tsqx_result.stderr.strip(), file=sys.stderr)
            return tsqx_result.returncode

        asy_text = tsqx_result.stdout
        if not asy_text.strip():
            print("[ERROR] tsqx reported success but generated empty ASY", file=sys.stderr)
            return 1

        if use_ldgeo and args.standalone:
            asy_text = inline_ldgeo_into_asy(asy_text, ldgeo_path, effective_theme)

        staged_asy.write_text(asy_text, encoding="utf-8")

        if not args.no_pdf:
            env = os.environ.copy()
            asy_full = [*asy_cmd]
            if use_ldgeo and not args.standalone:
                existing = env.get("ASYMPTOTE_DIR", "")
                ldgeo_dir = str(ldgeo_path.parent)
                env["ASYMPTOTE_DIR"] = f"{ldgeo_dir}{os.pathsep}{existing}" if existing else ldgeo_dir
                asy_full.extend(["-autoimport", ldgeo_path.stem, "-u", effective_theme])

            asy_full.extend(["-f", "pdf", "-o", str(staged_pdf.with_suffix("")), str(staged_asy)])
            asy_result = run(asy_full, cwd=input_path.parent, env=env)
            if asy_result.returncode != 0:
                print("[ERROR] asy step failed", file=sys.stderr)
                detail = (asy_result.stderr or asy_result.stdout).strip()
                if detail:
                    print(detail, file=sys.stderr)
                return asy_result.returncode
            if not staged_pdf.is_file() or staged_pdf.stat().st_size == 0:
                print("[ERROR] asy reported success but did not produce a nonempty PDF", file=sys.stderr)
                return 1
            with staged_pdf.open("rb") as stream:
                if stream.read(5) != b"%PDF-":
                    print("[ERROR] generated file is not a PDF", file=sys.stderr)
                    return 1

            for warning in inspect_pdf_geometry(staged_pdf):
                print(f"[WARN] {warning}", file=sys.stderr)

        staged_asy.replace(out_asy)
        print(f"[OK] Generated ASY ({effective_theme}): {out_asy}")
        if not args.no_pdf:
            staged_pdf.replace(out_pdf)
            print(f"[OK] Generated PDF ({effective_theme}): {out_pdf}")

            if args.check_png:
                if shutil.which("pdftoppm") is None:
                    print("[WARN] pdftoppm not found; skipped PNG rendering.", file=sys.stderr)
                else:
                    png_res = run(["pdftoppm", "-png", "-r", "180", "-singlefile", str(out_pdf), str(out_png.with_suffix(""))])
                    if png_res.returncode != 0:
                        print(f"[WARN] pdftoppm failed: {png_res.stderr.strip()}", file=sys.stderr)
                    else:
                        print(f"[OK] Generated PNG: {out_png}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
