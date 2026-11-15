# TSQX Idioms, Parsing Checklist & Style Guide

Combine careful geometric parsing with concise, standard TSQX constructions before considering raw Asymptote (`!`).

---

## 1. Geometry Parsing Checklist

Before writing TSQX, extract from the problem statement and/or reference image:

- Named points (keep exact problem labels) and free vs. constructed points
- Collinear, parallel, perpendicular, equal-length, and equal-angle relations
- Circles, tangencies, and concyclic points
- Midpoints, feet of altitudes/perpendiculars, centroids, circumcenters, incenters, orthocenters
- Extension points on rays or lines (`extension A B C D`)
- Shaded or highlighted regions and label positions that must remain collision-free

Verify:
1. Which points are primitive (`dir` angles or explicit coordinates) and which are derived?
2. Which relations are mathematically exact vs. merely incidental in a sketch? Do not encode unstated equalities or perpendicularities.
3. Does the chosen primitive configuration avoid accidental collinearities or awkward obtuse overlaps?

---

## 2. Construction Priorities

Prefer these layers in order:

1. **Free anchor points**: `A = dir 110`, `B = dir 210`, `C = dir 330` (on unit circle) or explicit coordinates when exact constraints demand it.
2. **Standard TSQX built-ins**:
   - `midpoint A--B`
   - `foot P A B`
   - `incenter A B C`, `orthocenter A B C`, `circumcenter A B C`, `centroid A B C`
   - `extension A B C D`
   - `incircle A B C`, `circumcircle A B C`
3. **Line/circle intersections**:
   - `IP (Line A B) (Line C D)`
   - `OP path (Line A B)` (the *other* intersection besides a shared vertex)
4. **Drawing & visual hierarchy**: Draw the main polygon first, auxiliary segments in `grey`/`gray` or `dashed`, then circles and highlighted loci sparingly in `blue`/`red`/`deepgreen`.
5. **Raw Asymptote escape hatch (`!`)**: Use `!pair` or `!path` helpers only when pure TSQX built-ins cannot express the step (e.g., `rotate(90)*(B-H)` for perpendicular lines, explicit tangent helpers).

---

## 3. Evan Chen Style & Label Conventions

- Prefer compact declarative TSQX (`dir` points -> derived centers/feet -> extensions -> clean path strokes) over coordinate-heavy algebra.
- Add direction hints (angles `0`–`359` or `N`/`NW`/`SE`) on points whenever labels risk overlapping lines or circles:
  - `I 315 = incenter A B C`
  - `H NW = orthocenter A B C`
  - `D 220 ;= midpoint B--C` (`:=` / `;=` to suppress or style dots/labels appropriately)
- Typical drawing patterns:
  ```tsqx
  A--B--C--cycle / 0.1 lightcyan / blue
  incircle A B C / blue
  M--K / red
  N--P--M / red dashed
  ```
- Keep code compact yet readable; isolate nontrivial vector math in short `!` helpers:
  ```tsqx
  !path circleO = circumcircle(A, I, B);
  P 180 = OP circleO (Line C A)
  !pair pBH = H + rotate(90)*(B-H);
  D 140 ;= extension A B H pBH
  ```

---

## 4. Common Failure Modes to Avoid

- Encoding a diagram guess as a hard geometric constraint
- Choosing free angles (`dir ...`) that create unintended degeneracy or cluttered label intersections
- Reaching for `!pair`/`!path` boilerplate when `incircle`, `foot`, `midpoint`, or `extension` already handles it cleanly
- Reproducing a proof's auxiliary lines when the prompt only asks for the problem figure (unless explicitly requested)
