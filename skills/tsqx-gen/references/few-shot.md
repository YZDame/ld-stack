# Few-Shot Patterns

Use these tested examples as style and construction anchors. Copy the semantic layering and assertion discipline rather than freezing coordinates blindly.

## 1. Triangle + Incenter + Incircle (Themed + Asserted)

```tsqx
~triangle A B C
I 45 = incenter A B C
D 270 = foot I B C
E 30 = foot I C A
F 150 = foot I A B
!check_perp(I, D, B, C, "ID perp BC");
!check_equal_dist(I, D, I, E, "ID = IE");

A--B--C--cycle / fill1 / given
incircle A B C / fill2 / circ2
A--I / aux
B--I / aux
C--I / aux
I--D / key
I--E / key
I--F / key
rightanglemark I D C / mark
```

## 2. Orthocenter + Orthic Triangle + Euler Line

```tsqx
A = dir 105
B = dir 215
C = dir 330
O 15 = circumcenter A B C
H 165 = orthocenter A B C
G 290 = centroid A B C
D 270 = foot H B C
E 30 = foot H C A
F 150 = foot H A B
!check_perp(A, D, B, C, "AD perp BC");
!check_collinear(O, G, H, "Euler line O-G-H");

circumcircle A B C / circ
A--B--C--cycle / fill1 / given
D--E--F--cycle / fill2 / accent
A--D / aux
B--E / aux
C--F / aux
O--H / key
rightanglemark A D C / mark
```

## 3. Symmedian, Tangents & Safe Second Intersection (`perpPt` + `otherPt`)

```tsqx
A = dir 112
B = dir 210
C = dir 330
O 15 = circumcenter A B C
M 235 = midpoint B--C
!path w = circumcircle(A, B, C);
T 270 = extension B (perpPt B O B) C (perpPt C O C)
K 245 = otherPt w A T
D 300 = otherPt w A M
!check_perp(O, B, B, T, "OB perp BT");
!check_on_circle(K, O, A, "K on circumcircle");

w / circ
A--B--C--cycle / fill1 / given
O--B / aux2
O--C / aux2
B--T--C / accent
A--T / key
A--D / aux
rightanglemark O B T / mark
pathtick B M 1 / mark
pathtick M C 1 / mark
```

## 4. External Tangents & Harmonic Polar (`tangentPtR` + `otherPt`)

```tsqx
O 220 = (0, 0)
P 0 = (2.35, 0)
A 110 = tangentPtR P O 1 1
B 250 = tangentPtR P O 1 2
C 155 = dir 155
!path w = unitcircle;
D 60 = otherPt w C P
Q 125 = extension A B C D
!check_perp(O, A, A, P, "OA perp AP");
!check_collinear(P, D, C, "P-D-C collinear");

w / fill1 / circ
P--A / accent
P--B / accent
A--B / key
P--C / given
O--A / aux
O--B / aux
rightanglemark O A P / mark
```

## 5. Implicit Angle Constraint via Raw-Asymptote Bisection + Assertion

```tsqx
A = dir 140
B = dir 200
C = dir 340
!real angleDeg(pair U, pair V, pair W) {
!  real c = dot(unit(U-V), unit(W-V));
!  return degrees(acos(max(-1, min(1, c))));
!}
!real f(real t) {
!  pair X = B + t*(C - B);
!  return angleDeg(B, A, X) - 2*angleDeg(A, C, B);
!}
!real lo = 0.01, hi = 0.99;
!for (int i = 0; i < 60; ++i) {
!  real mid = 0.5*(lo + hi);
!  if (f(lo)*f(mid) <= 0) hi = mid; else lo = mid;
!}
!pair pP = B + 0.5*(lo + hi)*(C - B);
P 270 = pP
!assert(abs(angleDeg(B, A, P) - 2*angleDeg(A, C, B)) < 1e-6, "angle BAP = 2 angle ACB");

A--B--C--cycle / fill1 / given
A--P / key
anglemark B A P / accent
anglemark A C B / circ
```

## 6. Preserved Evan Chen Handout Anchors (Vanilla TSQX)

These preserved handout snippets (`testdata/cases/GeoSlang-*.tsqx`) show Evan Chen's concise declarative style when using vanilla TSQX without themes (`--theme none`):

```tsqx
# GeoSlang-03 (Iran Incenter Lemma)
A = dir 115
B = dir 210
C = dir 330
I 315 = incenter A B C
D = foot I B C
E 15 = foot I C A
F 165 = foot I A B
M = midpoint B--C
N = midpoint A--C
K = extension M N E F

A--B--C--cycle / 0.1 lightcyan / blue
incircle A B C / blue
E--K / red
M--K / red
B--I / deepgreen
I--K / deepgreen
```
