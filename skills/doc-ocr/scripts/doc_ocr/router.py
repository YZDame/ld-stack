from __future__ import annotations

import mimetypes
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path


BACKENDS = ("paddleocr", "mineru", "mistral", "gemini")


@dataclass(frozen=True)
class DocumentProfile:
    path: str
    mime_type: str
    size_bytes: int
    pages: int | None = None
    material: str = "auto"
    language: str = "zh"
    formula_density: str = "medium"
    has_tables: bool = False
    has_diagrams: bool = False
    poor_quality: bool = False

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class RouteDecision:
    ranked_backends: tuple[str, ...]
    scores: dict[str, int]
    reasons: dict[str, list[str]]

    def to_dict(self) -> dict:
        return {
            "ranked_backends": list(self.ranked_backends),
            "scores": self.scores,
            "reasons": self.reasons,
        }


def inspect_document(
    path: Path,
    *,
    material: str = "auto",
    language: str = "zh",
    formula_density: str = "medium",
    has_tables: bool = False,
    has_diagrams: bool = False,
    poor_quality: bool = False,
) -> DocumentProfile:
    if not path.is_file():
        raise FileNotFoundError(path)
    mime_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    pages = _pdf_pages(path) if mime_type == "application/pdf" else 1
    return DocumentProfile(
        path=str(path.resolve()),
        mime_type=mime_type,
        size_bytes=path.stat().st_size,
        pages=pages,
        material=material,
        language=language,
        formula_density=formula_density,
        has_tables=has_tables,
        has_diagrams=has_diagrams,
        poor_quality=poor_quality,
    )


def _pdf_pages(path: Path) -> int | None:
    try:
        result = subprocess.run(
            ["pdfinfo", str(path)], capture_output=True, text=True, timeout=10, check=False
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    for line in result.stdout.splitlines():
        if line.startswith("Pages:"):
            try:
                return int(line.split(":", 1)[1].strip())
            except ValueError:
                return None
    return None


def choose_backends(profile: DocumentProfile) -> RouteDecision:
    scores = {name: 0 for name in BACKENDS}
    reasons: dict[str, list[str]] = {name: [] for name in BACKENDS}

    def add(name: str, points: int, reason: str) -> None:
        scores[name] += points
        reasons[name].append(reason)

    is_pdf = profile.mime_type == "application/pdf"
    is_image = profile.mime_type.startswith("image/")

    if is_pdf:
        add("mineru", 4, "PDF 文档结构解析")
        add("mistral", 3, "PDF 原生 OCR 接口")
        add("gemini", 2, "PDF 视觉理解")
    if is_image:
        add("paddleocr", 4, "单页图片文字识别")
        add("gemini", 2, "单页视觉理解")
        add("mistral", 2, "图片 OCR")

    if profile.material in {"photo", "handwritten"}:
        add("paddleocr", 5, "拍摄或手写材料")
        add("gemini", 4, "疑难视觉内容")
    elif profile.material == "scanned_pdf":
        add("mistral", 4, "规范扫描文档")
        add("mineru", 3, "扫描 PDF 版面恢复")
    elif profile.material == "printed_pdf":
        add("mineru", 4, "印刷型完整文档")
        add("mistral", 3, "清晰印刷文档")
    elif profile.material == "mixed":
        add("gemini", 4, "图文混排页面")
        add("mineru", 3, "复杂版面结构")

    if profile.formula_density == "high":
        add("mineru", 6, "高密度数学公式")
        add("mistral", 3, "公式与 Markdown 输出")
    elif profile.formula_density == "low":
        add("paddleocr", 1, "以普通文本为主")

    if profile.has_tables:
        add("mineru", 4, "表格抽取")
        add("mistral", 3, "结构化表格输出")
    if profile.has_diagrams:
        add("gemini", 5, "图形与页面语义理解")
        add("mineru", 2, "图片区域抽取")
    if profile.poor_quality:
        add("paddleocr", 5, "低质量、倾斜或阴影页面")
        add("gemini", 3, "低质量页面补救")
    if profile.language not in {"zh", "ch", "zh-cn"}:
        add("mistral", 3, "多语言文档")

    ranked = tuple(sorted(BACKENDS, key=lambda name: (-scores[name], BACKENDS.index(name))))
    return RouteDecision(ranked, scores, reasons)
