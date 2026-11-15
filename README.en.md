# LD Stack

Focused reusable Agent Skills for mathematical exposition, document OCR, geometry diagram synthesis, and olympiad reasoning.

[中文](README.md)

LD Stack (streamlined from `ta-skills`) keeps workspace-specific rules (directory layout, template paths, PR conventions) inside each repository's `AGENTS.md`, while packaging 4 high-signal, cross-project Skills.

## Core Skills (4 total)

| Skill | Origin | Purpose |
| --- | --- | --- |
| [`math-exposition`](skills/math-exposition/) | Original (merged) | Textbook-grade Chinese mathematics handouts and mini-papers: mathematical main thread, anti-AI-prose style, LaTeX typesetting, and 2025 `evan.sty` support. |
| [`doc-ocr`](skills/doc-ocr/) | Original (upgraded) | Multi-provider OCR router and chunk assembler across PaddleOCR-VL, MinerU, Mistral OCR, and Gemini (pure Python standard library). |
| [`tsqx-gen`](skills/tsqx-gen/) | Original (streamlined) | Declarative olympiad geometry diagram generation (`tsqx -> asy -> pdf`) with Evan Chen handout idioms and few-shots. |
| [`math-olympiad`](skills/math-olympiad/) | Upstream external | Competition math solving and proof verification sourced from Anthropic's official plugin repository under Apache-2.0 ([`UPSTREAM.md`](skills/math-olympiad/UPSTREAM.md)). |

See [THIRD_PARTY.md](THIRD_PARTY.md) for third-party attribution and licensing details.

## Installation

Mount directly via relative symlinks in your workspace `.agents/skills/`:

```bash
ln -sfn ../../ld-stack/skills/math-exposition .agents/skills/math-exposition
ln -sfn ../../ld-stack/skills/doc-ocr .agents/skills/doc-ocr
ln -sfn ../../ld-stack/skills/tsqx-gen .agents/skills/tsqx-gen
ln -sfn ../../ld-stack/skills/math-olympiad .agents/skills/math-olympiad
```

Or install via Plugins / Skills CLI:

```bash
npx plugins add YZDame/ld-stack
npx skills add YZDame/ld-stack --skill math-exposition
```

## Layout

```text
ld-stack/
├── .codex-plugin/plugin.json
├── .claude-plugin/plugin.json
├── skills/
│   ├── math-exposition/
│   ├── doc-ocr/
│   ├── tsqx-gen/
│   └── math-olympiad/
├── README.md
├── README.en.md
├── LICENSE
└── THIRD_PARTY.md
```

## License

First-party content is licensed under the [Apache License 2.0](LICENSE). Third-party skills and `evan.sty` keep their original licenses (see [THIRD_PARTY.md](THIRD_PARTY.md)).
