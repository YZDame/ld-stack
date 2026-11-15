---
name: tsqx-gen
description: Generate TSQX geometry code from Chinese or English problem statements, diagram descriptions, or provided images; use when the user wants a fast, repeatable workflow from natural language or figure content to valid TSQX, including normalization, ambiguity handling, and optional compile-check against local tsqx and asymptote toolchains.
---

# TSQX Generator

Convert geometry problems, figure descriptions, or diagram images into clean, verifiable TSQX source (`tsqx -> asy -> pdf`).

- Read [references/idioms.md](references/idioms.md) for construction priorities, geometry parsing checklist, Evan Chen style conventions, and when to drop down to raw Asymptote (`!`).
- Read [references/few-shot.md](references/few-shot.md) for canonical patterns and preserved Evan handout examples.

## Core Workflow

1. **Parse geometry facts**: Extract named points, primitive vs. derived points, collinear/parallel/perpendicular/tangent/cyclic relations, and label visibility constraints (see the checklist in [references/idioms.md](references/idioms.md)). Separate **stated facts** from diagram-only guesses.
2. **Choose construction order**:
   - base free points (`dir` or explicit coordinates)
   - standard derived points (`incenter`, `orthocenter`, `circumcenter`, `centroid`, `midpoint`, `foot`, `extension`)
   - circle-line / circle-circle intersections (`IP`, `OP`)
   - draw main figure, auxiliary segments, and highlighted relations sparingly
3. **Prefer pure TSQX built-ins** before injecting raw Asymptote (`!pair`, `!path`). Treat raw Asymptote as an escape hatch when built-ins cannot express the construction (e.g., perpendicular helpers via `rotate(90)`).
4. **Output format**:
   - Return clean, ready-to-compile TSQX code (and briefly note any non-obvious coordinate choices or unresolved ambiguities). Do **not** wrap simple diagram requests in heavy multi-heading reports unless the caller asks for full audit notes.
   - When embedding in LaTeX handouts, include the compile check command (`python3 scripts/tsqx.py -p < figure.tsqx > figure.asy && asy -f pdf figure.asy` or `tsqx -p`).

## Local Verification

Run the bundled compiler helper from this Skill's directory:

```bash
python3 "<SKILL_DIR>/scripts/verify_tsqx_pipeline.py" /path/to/figure.tsqx --pre --output-dir /path/to/out
```

Before introducing a nontrivial combined color or line-style modifier, test a minimal one-line fixture with `tsqx -p` and `asy -f pdf`. If compilation fails, fix syntax/label collisions and re-run; if blocked by missing local tools or ambiguous geometry, report the exact blocker.
