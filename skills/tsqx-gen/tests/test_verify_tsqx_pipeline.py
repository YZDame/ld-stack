"""Regression tests for tsqx-gen verify_tsqx_pipeline.py and bundled testdata cases."""

from __future__ import annotations

import importlib.util
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

SKILL_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = SKILL_ROOT / "scripts" / "verify_tsqx_pipeline.py"
CASES_DIR = SKILL_ROOT / "testdata" / "cases"

HAS_TOOLCHAIN = bool(shutil.which("asy")) and (
    bool(shutil.which("tsqx")) or importlib.util.find_spec("tsqx") is not None
)


def run_verifier(*extra_args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *extra_args],
        text=True,
        capture_output=True,
        check=False,
    )


def test_missing_input_fails_cleanly(tmp_path: Path) -> None:
    proc = run_verifier(str(tmp_path / "does-not-exist.tsqx"), "--pre")
    assert proc.returncode != 0
    assert "Input not found" in proc.stderr


@pytest.mark.skipif(not HAS_TOOLCHAIN, reason="requires local tsqx and asymptote")
@pytest.mark.parametrize("case_path", sorted(CASES_DIR.glob("*.tsqx")), ids=lambda p: p.name)
def test_all_regression_cases_compile(case_path: Path, tmp_path: Path) -> None:
    proc = run_verifier(str(case_path), "--pre", "--output-dir", str(tmp_path))
    assert proc.returncode == 0, f"{case_path.name} failed:\n{proc.stderr}\n{proc.stdout}"
    pdf = tmp_path / f"{case_path.stem}.pdf"
    assert pdf.is_file()
    assert pdf.read_bytes().startswith(b"%PDF-")


@pytest.mark.skipif(not HAS_TOOLCHAIN, reason="requires local tsqx and asymptote")
@pytest.mark.parametrize("theme", ["classic", "print", "flexoki", "colormath", "slides"])
def test_all_five_themes_and_standalone(theme: str, tmp_path: Path) -> None:
    src = CASES_DIR / "fig2.tsqx"
    proc = run_verifier(
        str(src),
        "--pre",
        "--theme",
        theme,
        "--scale",
        "compact",
        "--standalone",
        "--output-dir",
        str(tmp_path),
    )
    assert proc.returncode == 0, proc.stderr
    asy_text = (tmp_path / "fig2.asy").read_text(encoding="utf-8")
    assert f'applytheme("{theme}");' in asy_text
    assert (tmp_path / "fig2.pdf").read_bytes().startswith(b"%PDF-")


@pytest.mark.skipif(not HAS_TOOLCHAIN, reason="requires local tsqx and asymptote")
def test_failed_assertion_blocks_pdf_and_preserves_atomic_staging(tmp_path: Path) -> None:
    bad = tmp_path / "bad_perp.tsqx"
    bad.write_text(
        "~triangle A B C\n"
        "D = foot A B C\n"
        '!check_perp(A, D, A, C, "intentionally false");\n'
        "A--B--C--cycle / given\n",
        encoding="utf-8",
    )
    out = tmp_path / "out"
    proc = run_verifier(str(bad), "--pre", "--theme", "classic", "--output-dir", str(out))
    assert proc.returncode != 0
    assert "check_perp failed" in proc.stderr
    assert not (out / "bad_perp.pdf").exists()


@pytest.mark.skipif(
    not (HAS_TOOLCHAIN and shutil.which("pdftoppm")),
    reason="requires tsqx, asymptote, and pdftoppm",
)
def test_check_png_generates_visual_preview(tmp_path: Path) -> None:
    src = CASES_DIR / "fig1.tsqx"
    proc = run_verifier(
        str(src),
        "--pre",
        "--theme",
        "classic",
        "--check-png",
        "--output-dir",
        str(tmp_path),
    )
    assert proc.returncode == 0, proc.stderr
    png = tmp_path / "fig1.png"
    assert png.is_file()
    assert png.read_bytes().startswith(b"\x89PNG")
