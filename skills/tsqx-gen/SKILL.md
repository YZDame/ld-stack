---
name: tsqx-gen
description: Generate TSQX geometry code from Chinese or English problem statements, diagram descriptions, or provided images; use when the user wants a fast, repeatable workflow from natural language or figure content to valid TSQX, including semantic theme tokens, geometric invariant assertions, and automated compile + visual checks via local tsqx and asymptote toolchains.
---

# TSQX Generator

Convert geometry problems, figure descriptions, or diagram images into clean, verifiable, theme-ready TSQX source (`tsqx -> asy -> pdf`).

- Read [references/idioms.md](references/idioms.md) for the geometry parsing checklist, construction priorities, `ldgeo.asy` semantic tokens & helpers, parser traps, and raw-Asymptote boundaries.
- Read [references/few-shot.md](references/few-shot.md) for canonical themed patterns and preserved Evan Chen handout examples.

## Core Workflow

1. **Parse geometry facts**:
   - Extract named points, free vs. derived points, collinear/parallel/perpendicular/tangent/cyclic relations, and label visibility constraints (see [references/idioms.md](references/idioms.md)).
   - Strictly separate **stated mathematical facts** from diagram-only visual guesses. Do not add proof auxiliary lines unless the user asks for a solution diagram.
2. **Choose construction order (prefer pure TSQX + `ldgeo.asy` helpers)**:
   - Free anchor points (`~triangle A B C`, `dir`, or explicit coordinates when metrics require it).
   - Standard derived points (`incenter`, `orthocenter`, `circumcenter`, `centroid`, `excenter`, `midpoint`, `foot`, `extension`).
   - Safe intersections & perpendicular/parallel/tangent helpers from `ldgeo.asy`: use `otherPt w A B` or `other c l X` instead of guessing `OP`; use `perpPt`, `paraPt`, `bisectorPt`, `tangentPt`, `tangentPtR`, `radicalAxis`.
   - Drop to raw Asymptote (`!`) only for reusable `!path` variables, numeric solvers, or custom geometry not expressible by built-ins.
3. **Apply the Style, Scale, and Assertion Contracts**:
   - **Zero-boilerplate semantic styling**: Do **not** write `!import ldgeo;` in the `.tsqx` file. Use the unparenthesized `ldgeo.asy` semantic tokens (`given`, `aux`, `aux2`, `key`, `accent`, `circ`, `circ2`, `mark`, `fill1`, `fill2`, `fillkey`) so the figure switches seamlessly across `classic`, `print`, `flexoki`, `colormath`, and `slides` themes at compile time. Limit highlights to at most 2 focus roles per figure.
   - **Scale parity**: Recommend one of three physical canvas sizes (`compact` = `5.5cm`, `standard` = `7.5cm`, `wide` = `11.5cm`) and match LaTeX `\includegraphics` width 1:1 so label font size stays consistent.
   - **Invariant assertions**: Append 1–3 lightweight checks (`!check_perp`, `!check_parallel`, `!check_collinear`, `!check_cyclic`, `!check_on_circle`, `!check_equal_dist`) verifying the key constraints from the statement.
4. **Output format**:
   - Return clean, ready-to-compile `.tsqx` code plus a brief note on recommended `--scale` / `--theme` and any nontrivial coordinate assumptions or unresolved ambiguities.
   - Distinguish three independent verification results: **toolchain compilation**, **invariant assertions**, and **rendered visual inspection**. Never claim a diagram is geometrically correct solely because `asy` exited 0.

## Local Verification

Run the bundled compiler helper from this Skill's directory:

```bash
python3 "<SKILL_DIR>/scripts/verify_tsqx_pipeline.py" /path/to/figure.tsqx \
  --pre --theme classic --scale standard --check-png --output-dir /path/to/out
```

- Pass `--standalone` when exporting a self-contained `.asy` with `ldgeo.asy` inlined for external sharing.
- Inspect the rendered PNG (or check any aspect-ratio `[WARN]` emitted by the script) to confirm no label collisions, clipped arcs, or runaway intersections before finalizing.
- If compilation or assertions fail, fix the construction and re-run; if blocked by missing local tools or ambiguous geometry, report the exact blocker.
