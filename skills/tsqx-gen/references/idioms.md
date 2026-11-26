# TSQX Idioms, Parsing Checklist, Semantic Themes & Parser Traps

This reference aligns with upstream `vEnhance/tsqx` (`tsqx/__main__.py`), the bundled `assets/ldgeo.asy` library, and the Chinese TSQX Handbook.

---

## 1. Geometry Parsing Checklist

Before writing TSQX, extract from the problem statement and/or reference image:

- Named points (keep exact problem labels; use `P'` for $P'$, `P&` for $P^*$, `A_1` for $A_1$)
- Free anchor points vs. derived points
- Exact relations: collinear, parallel, perpendicular, tangent, cyclic, equal length, equal angle
- Circles, rays/extensions, and shaded regions
- Purpose: problem-statement figure (no proof spoilers) vs. solution/step figure

Check before coding:
1. Are all stated relations encoded constructively (not faked visually)?
2. Does the chosen free configuration avoid accidental collinearity, degeneracy, or crowded overlaps (e.g., avoid equilateral/isosceles triangles unless stated; prefer `A = dir 112`, `B = dir 210`, `C = dir 330` or `dir 118` when separating feet and midpoints)?
3. Which 1–3 constraints should be locked with `!check_*` assertions?

---

## 2. Verified Built-ins vs. `ldgeo.asy` Helpers

### Standard `tsqx -p` built-ins (always available)
- Points: `dir a`, `midpoint A--B`, `foot P A B` (note: point first, line next), `extension A B C D`, `incenter A B C`, `circumcenter A B C`, `orthocenter A B C`, `centroid A B C`, `excenter A B C`, `IP p q`, `OP p q`
- Transforms: `(rotate a O)(P)`, `(reflect A B)(P)`, `(scale k O)(P)`, `(shift v)(P)`
- Paths: `circumcircle A B C`, `incircle A B C`, `CP O A`, `CR O r`, `unitcircle`, `Line A B`
- Prefix arithmetic: `plus`, `minus`, `mult`, `divide`

### Bundled `assets/ldgeo.asy` helpers (injected automatically via `--theme <name>`)
Do **not** use undocumented `olympiad.asy` names (`bisectorpoint`, `tangent`, `pathticks`, 3-arg `IP`, `intersect`). Use these verified `ldgeo.asy` functions instead:

- `otherPt w A B` — second intersection of line `AB` with curve `w` excluding known point `A` (auto-extends ray beyond bounding box). **Always prefer `otherPt` or `other c l X` over guessing `OP`.**
- `other c l X` — intersection of paths `c` and `l` farthest from `X`.
- `perpPt P A B` / `paraPt P A B` — helper point on the line through `P` perpendicular/parallel to `AB` (combine with `extension`).
- `bisectorPt A B C` / `extBisectorPt A B C` — unit-distance point on internal/external bisector of $\angle ABC$.
- `tangentPt P O A 1` (or `2`) — tangent point from `P` to circle centered at `O` through `A`.
- `tangentPtR P O r 1` (or `2`) — tangent point from `P` to circle `(O, r)` (distinct name prevents Asymptote `int` overload ambiguity).
- `rightanglemark A B C` / `anglemark A B C` / `pathtick A B n` — geometric markers drawn with `/ mark`.
- `radicalAxis O1 r1 O2 r2 halfLen` — radical axis segment path.

### Geometric Invariant Assertions (`ldgeo.asy`)
- `!check_perp(A, B, C, D, "AB perp CD");`
- `!check_parallel(A, B, C, D, "AB para CD");`
- `!check_collinear(A, B, C, "A-B-C collinear");`
- `!check_cyclic(A, B, C, D, "A,B,C,D cyclic");`
- `!check_on_circle(P, O, A, "P on circle(O,A)");`
- `!check_equal_dist(A, B, C, D, "AB = CD");`

---

## 3. CSS-Like Semantic Style & Scale Contract

Keep `.tsqx` files **zero-boilerplate** (no `!import ldgeo;`). Style objects by logical role using unparenthesized `ldgeo.asy` tokens:

| Token | Role | Typical objects |
| --- | --- | --- |
| `given` | Known skeleton | Main triangle, given polygon |
| `aux` | Primary dashed auxiliary | Altitudes, medians, angle bisectors, extensions |
| `aux2` | Secondary dotted auxiliary | Radii to tangent points, foot connectors, midlines |
| `key` | Primary conclusion / focus (bold) | Target concurrency/collinearity, Euler line, radical axis |
| `accent` | Secondary focus | Tangents, orthic triangle, second key locus |
| `circ` / `circ2` | Primary / secondary circle | Circumcircle / incircle or nine-point circle |
| `mark` | Geometric annotations | `rightanglemark`, `anglemark`, `pathtick` |
| `fill1` / `fill2` / `fillkey` | Subtle fills | Base triangle / secondary region / key region |

Themes switchable via one flag (`--theme` or VS Code `tsqx.theme`):
- `classic` (default handouts), `print` (monochrome laser exams), `flexoki` (warm ink-on-paper), `colormath` (ColorMath LaTeX palette), `slides` (bold classroom projection).

Scale parity (match LaTeX `\includegraphics` 1:1):
- `compact` = `5.5cm` (two-column / side-by-side / small problems)
- `standard` = `7.5cm` (standard single-column problem figure)
- `wide` = `11.5cm` (dense multi-circle or radical-axis diagrams)

---

## 4. Label & Dot Conventions

- Modifiers: `=` (dot + label), `:=` (hidden helper), `.=` (dot only), `;=` (label only).
- Directions: compass (`NE`, `SW`), angle (`45`, `270`), linear offset (`2S3E`), radial offset (`1.5R30`).
- Always assign explicit directions to interior points (`I`, `H`, `O`, `G`) and points lying on lines (`D`, `M`, `E`, `F`).

---

## 5. Four TSQX Parser Traps to Never Trigger

1. **Missing `/` before pen styles**: Never write `A--B dashed blue` (compiles to invalid `draw(A--B, dashed, blue);`). Always write `A--B / aux` or `A--B / dashed blue`.
2. **Parenthesized pen calls after `/`**: Never write `A--B / gray(0.5)`, `A--B / linewidth(1.5) red`, or `A--B / rgb("...")` — TSQX tokenizes `(` and `)` and produces invalid `gray(+0.5+)`. Always use semantic tokens or `!draw(...)`.
3. **Spaces around infix arithmetic or complex nested parens**: Never write `P = 2*A - B` (produces `2*A(-B)`). Write `P = 2*A-B`, `P = minus (2*A) B`, or compute `!pair pP = ...;` and assign `P 270 = pP`.
4. **Parenthesized expressions joined directly with `--`**: Never write `(foot A B C)--(foot B C A)` (produces broken `foot(...)*-(-)*foot(...)`). Assign intermediate variables (`D := foot A B C`, `E := foot B C A`) then draw `D--E`.
5. **Never assume `OP` picks the "other" intersection**: `IP` and `OP` merely return index `0` and `1` of `intersectionpoints`, which depends on path parameterization. Always use `otherPt w A B` or `other c l X`.
