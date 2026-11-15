# Few-Shot Patterns

Use these examples as style anchors. Copy the construction strategy and visual hierarchy rather than blindly freezing coordinates.

## 1. Triangle + Incenter + Incircle

```tsqx
A = dir 110
B = dir 210
C = dir 330
I 45 = incenter A B C

A--B--C--cycle / 0.12 lightcyan / blue
incircle A B C / 0.15 lightgreen / darkgreen
A--I / red
B--I / red
C--I / red
```

Use when the figure centers on a standard triangle center and canonical circle.

## 2. Orthocenter + Pedal Triangle

```tsqx
A = dir 95
B = dir 215
C = dir 330
H = orthocenter A B C
D = foot H B C
E = foot H C A
F = foot H A B

A--B--C--cycle / 0.08 lightyellow / blue
D--E--F--cycle / 0.15 lightcyan / red
A--D / gray
B--E / gray
C--F / gray
```

## 3. Circle Through Given Points Meeting Lines Again (`!path` + `OP`)

```tsqx
C = dir 110
A = dir 200
B = dir 320
I N = incenter A B C
O 90 = circumcenter A I B
!path circleO = circumcircle(A, I, B);
P 180 = OP circleO (Line C A)
Q 0 = OP circleO (Line C B)
```

## 4. Perpendicular Helper Line Via Raw Asymptote (`!pair` + `rotate(90)`)

```tsqx
H 270 ;= orthocenter A B C
!pair pBH = H + rotate(90)*(B-H);
D 140 ;= extension A B H pBH
```

## 5. Evan Handout: The Iran Incenter Lemma (`GeoSlang-03`)

Source context: Evan Chen `GeoSlang` handout — incenter $I$, contact points $D, E, F$, midpoints $M, N$, intersection $K = MN \cap EF$ with $BK \perp CK$.

```tsqx
A = dir 130
B = dir 210
C = dir 330
I 315 = incenter A B C
D = foot I B C
E 70 = foot I C A
F = foot I A B
M = midpoint B--C
N = midpoint C--A
K = extension M N E F
A--B--C--cycle / 0.1 lightcyan / blue
incircle A B C / blue
M--K / red
F--K / red
B--K--C / red
```

## 6. Evan Handout: The Shooting Lemma / Death Star Lemma (`GeoSlang-04`)

Source context: Evan Chen `GeoSlang` handout — chord $AB$ of the unit circle, midpoint $M$ of minor arc $AB$, point $T$ on major arc, $K = MT \cap AB$, and tangent circle `CP P K`.

```tsqx
A = dir 170
B = dir 10
M = dir 270
T = dir 55
K 315 = extension M T A B
unitcircle / 0.1 cyan / blue
V := K+dir(90)
P = extension origin T K V
CP P K / 0.1 yellow / deepgreen
A--B / blue
M--T / red
B--M--A / grey
```
