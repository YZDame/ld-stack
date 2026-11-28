# TSQX Gen Skill

A compact, self-contained Agent Skill for turning Chinese or English geometry problem statements, figure descriptions, or reference images into clean, assertion-checked, theme-ready TSQX source and compiled PDF/PNG figures.

## Contents

```text
tsqx-gen/
├── SKILL.md
├── LICENSE
├── README.md
├── agents/openai.yaml
├── assets/
│   └── ldgeo.asy                 # Semantic themes (classic/print/flexoki/colormath/slides), helpers & assertions
├── references/
│   ├── idioms.md                 # Parsing checklist, verified built-ins, semantic tokens & parser traps
│   └── few-shot.md               # Themed olympiad anchors + preserved Evan Chen handout examples
├── scripts/
│   └── verify_tsqx_pipeline.py   # Deterministic tsqx -> asy -> pdf (+ PNG & bbox check) verifier
├── testdata/cases/               # Regression dataset (Evan handouts + 8 olympiad constructions)
└── tests/
    └── test_verify_tsqx_pipeline.py
```

## Local Validation

```bash
# Auto-detects ldgeo tokens/helpers and injects classic theme; exports PNG for visual check
python3 scripts/verify_tsqx_pipeline.py \
  testdata/cases/fig2.tsqx \
  --pre --theme classic --scale standard --check-png \
  --output-dir /tmp/tsqx-skill-check

# Export monochrome print-ready exam diagram + standalone self-contained ASY
python3 scripts/verify_tsqx_pipeline.py \
  testdata/cases/fig2.tsqx \
  --pre --theme print --scale compact --standalone \
  --output-dir /tmp/tsqx-skill-print

# Run regression suite
pytest tests/test_verify_tsqx_pipeline.py
```

Requires `tsqx` (`python3 -m tsqx` or `tsqx`) and `asy` (Asymptote) for PDF verification, plus optional `pdftoppm` / `pdfinfo` (Poppler) for PNG visual inspection and aspect-ratio warnings.

## License

First-party content is licensed under the [Apache License 2.0](../../LICENSE).
