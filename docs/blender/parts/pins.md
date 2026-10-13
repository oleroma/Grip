# Alignment pins

`pin` is a small square peg that sits in matching holes in the case top and the case bottom, so that the two halves line up when they are screwed together [inferred from the shape and the holes]. The object `pin` uses the modifier group `pins` with `bool` = off, followed by four Bevel modifiers; the cutter `pin bool` (collection `pin comp` in `source`) uses the same group with `bool` = on [wiring]. The case subtracts `pin bool` in `common bools`, except for the `hollow` body [wiring].

## How it is built

`pins` → `pin base` [wiring]:

1. `selector` (part `pin`) reads the variant's pin preset: `GripV pins parameters` or `GripX pins`.
2. A box of `pin width` × `pin width` × `pin height`, centred on the position `X`, `Y`, `Z` from `pins postion` (sic). Since `Z` is 40, the pin straddles the split plane: half of it in each case half [measured: pin height +0.81 moved the pin's underside down by 0.405].
3. For the part (`bool` off) the box is shrunk by the tolerances: `xy tol` from the width and `z tol` from the height. For the cutter the full size is used [measured, below].
4. `MirrorX` mirrors the cutter, so there is one hole pair on each side; the part is a single pin (print two) [wiring; measured: the part is one object, 3.9 × 3.9 × 7.5 mm, on the right side].

With `body type` = hollow, the pin holes are not cut and the `pin` inputs do not change the case: shell bodies get alignment pins of their own from `align pins` inside `shell structure`, placed at the empties of the collection `align cut` [wiring; measured: in the GripV and GripX hollow contexts every pin input changed only the pin part]. With `lattice` the holes are still cut, because that exclusion is written as `lattice AND False` ([Issues](../09-issues.md) C10) [wiring].

## Presets

| Input | GripV | GripX |
|---|---|---|
| `pin width` | 4 | 4 |
| `pin height` | 8.1 | 8.1 |
| `xy tol` | 0.1 | 0.1 |
| `z tol` | 0.6 | 0.6 |
| `bevel` | 1 | 1 |
| `X` / `Y` / `Z` | 69 / −43.01 / 40 | 70.42 / −55.51 / 40 |

[wiring]. The part therefore measures 3.9 × 3.9 × 7.5 mm in both variants, 102.6 mm³ after its bevels [measured].

## What each input does

GripV, saved settings, one change at a time [measured]; GripX behaves the same where tested.

| Input | Pin | Case |
|---|---|---|
| `pin width` 4 → 4.4 | 0.4 wider in X and Y, +24 mm³ | holes larger: top −27, bottom −27 mm³ |
| `pin height` 8.1 → 8.91 | 0.81 taller (0.405 each way), +11.5 | holes deeper: top −13, bottom −13 |
| `xy tol` 0.1 → 0.3 | 0.2 narrower, −11 | none |
| `z tol` 0.6 → 0.8 | 0.2 shorter (0.1 each end), −2.8 | none |
| `bevel` 1 → 1.2 | −4.7 | none |
| `X` +10 % | moves by the step | holes follow (GripV +14 / +26; GripX no volume change) |
| `Y` +10 % | moves by the step | holes follow |
| `Z` 40 → 44 | moves up 4 | 128 mm³ of hole moves from the top half to the bottom |

So the fit is: hole = `pin width` × `pin width` × `pin height`, pin = (`pin width` − `xy tol`) × (`pin width` − `xy tol`) × (`pin height` − `z tol`); the clearance is `xy tol` / 2 per side and `z tol` / 2 at each end [measured].

The bevel comes from the `bevel` input inside the group and from the four Bevel modifiers on the object [wiring].

## Export

Both "Parts" presets export `pin` [wiring].
