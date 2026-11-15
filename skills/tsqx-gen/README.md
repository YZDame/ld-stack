# TSQX Gen Skill

A compact Agent Skill for turning geometry problem statements, figure descriptions, or reference images into clean TSQX code and compiled PDF figures.

## Contents

```text
tsqx-gen/
├── SKILL.md
├── LICENSE
├── README.md
├── agents/openai.yaml
├── references/
│   ├── idioms.md        # Parsing checklist, TSQX idioms, Evan style rules, raw-Asymptote boundaries
│   └── few-shot.md      # Canonical patterns + Evan handout examples (GeoSlang-03 / GeoSlang-04)
└── scripts/
    └── verify_tsqx_pipeline.py
```

## Local Validation

```bash
python3 scripts/verify_tsqx_pipeline.py \
  /path/to/example.tsqx \
  --pre \
  --output-dir /tmp/tsqx-skill-check
```

Requires `tsqx` (`python3 -m tsqx` or `tsqx`) and `asy` (Asymptote) for PDF verification; works for TSQX generation even without local compilation tools.

## License

First-party content is licensed under the [Apache License 2.0](../../LICENSE).
