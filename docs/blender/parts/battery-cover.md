# Battery cover and battery compartment

The battery sits in a compartment in the underside of the case bottom, closed by a printed cover that clips in with flexible lips [inferred from the names and shapes]. The cover and the compartment are generated from the same `cover` preset, so they always fit each other [wiring].

| What | Object / group | Notes |
|---|---|---|
| the cover part | object `battery cover` (collection `battery cover`), modifier group `cover` with `bool` = off | `cover` → `battery bool and cover` |
| the compartment cut into the case bottom | the group `coVer base` placed inside `bottom bools` | a copy of `battery bool and cover` with the output fixed to the cutter |
| the compartment in the middle plate (shell bodies) | `plate bools` → `battery bool and cover` | |
| the battery face of shell bodies | `battery face` reads the object `battery bool` (collection `battery cutout` in `source`, group `cover` with `bool` = on, plus a Bevel) | |

[wiring]. For the `hollow` and `lattice` bodies the case bottom uses the flat version of the cutter (output `no extrude`); for `standard` and `indent` the extruded one, together with the fixed `battery wire space` [wiring]. `coVer base` and `battery bool and cover` are two copies of the same logic (51 and 53 nodes; the copy only lacks the `bool` switch), so a fix in one has to be repeated in the other ([Issues](../09-issues.md) D9).

## How it is built

`battery bool and cover` [wiring]:

1. `separate cover basic` and `cover outputs` unpack the preset. `cover outputs` passes `lip hook height` on as `hook height`, and has an extra output `battery stick out` fixed to off.
2. **Battery block**: a box of `battery length` × `battery width` × `battery height`, moved along Y by `shift Y`.
3. **Cover plate** (`cover base plate`): a plate `cover base thickness` thick that overlaps the opening by `cover base overlap`; with `curved cover` on it follows the curved underside of the case.
4. **Lips** (`cover lips`, 113 nodes): flexible tongues `flex width` wide with lips of `lip height` and `lip width` and a hook of `lip hook height` that snaps into the case.
5. **Fits**: `x tolerance` and `y tolerance` (the `basic cover parameters`) shrink the cover against the opening; `compression offset` makes the cover thinner so it presses the battery [inferred from the name; measured: the cover gets thinner].
6. **Nail cut** (`nail cut`): a fixed cylinder (radius 8, 13.9 deep, 34 mm along Y) that makes a finger notch to open the cover; it has no parameter.
7. **Appendix**: an optional extension of the compartment (`appendix`, `appendix length`, `appendix height`, `appendix gap`) [inferred from the names; measured: on adds 21–24 mm³ to the case bottom].
8. **Battery wire cut**: a slot for the battery wire in the cover (`battery wire cut`) [inferred; measured: removes 1–2 mm³ from the cover].

## Presets

GripV has one pair of nodes; GripX has two pairs, and only the frame **"old cover"** is connected. The frame "battery" holds a second set that nothing reads ([Issues](../09-issues.md) C2) [wiring; measured: every input of the "battery" frame had no effect].

| Input | GripV | GripX (live, "old cover") | GripX "battery" (not connected) |
|---|---|---|---|
| x tolerance | 0.2 | 0.15 | 0.15 |
| y tolerance | 0.15 | 0.15 | 0.15 |
| battery length | 63.3 | 62.85 | 63.5 |
| battery width | 35.4 | 35.4 | 35.4 |
| battery height | 4.8 | 5.2 | 5.2 |
| shift Y | −48 | −48 | −48 |
| cover base thickness | 1 | 1.5 | 1 |
| cover base overlap | 0.5 | 0.75 | 0.5 |
| curved cover | **on** | off | off |
| flex width | 1 | 1.05 | 1 |
| lip height | 2.6 | 3.2 | 3.2 |
| lip width | 0.7 | 0.35 | 0.5 |
| lip hook height | 2 | 1.9 | 2 |
| compression offset | 0 | 0.1 | 0.1 |
| battery wire cut | 0 | 6 | 6 |
| appendix | off | off | off |
| appendix height / length / gap | 0.95 / 31.6 / 2.7 | same | same |
| test parameter | 0 | 0 | 0 |

## What each input does

One change at a time with the saved settings [measured]. "Cover" is the part, "case" the case bottom (mm³). GripV unless noted; GripX ("old cover") reacted the same way unless a second value is given.

| Input | Cover | Case bottom |
|---|---|---|
| `battery length` +10 % | 6.3 longer (centred), +254 (X +328) | −2,017 (X −2,076): the compartment grows |
| `battery width` +10 % | 3.5 wider, +227 (X +333) | −1,713 (X −1,873) |
| `battery height` +10 % | moves down by the step, no shape change | +48 (X +25) |
| `shift Y` +10 % (−48 → −43.2) | moves 4.8 forward | +1,313 (X +1,420): the compartment moves |
| `cover base thickness` +0.2 | 0.2 thicker (downwards), +484 (X +465) | — |
| `cover base overlap` +0.2 | 0.4 wider (V) / 0.35 wider (X), +44 / +38 | −57 / −48 |
| `curved cover` | GripV on → off: 0.6 narrower, 0.97 thinner, −167; GripX off → on: 2.45 wider, 0.97 thicker, +351 | −98 / −87 |
| `flex width` +0.2 | 0.4 wider, +110 (X +74) | −207 (X −161) |
| `lip height` +10 % | 0.26 taller (X 0.32), +30 (X +37) | +1.5 |
| `lip width` +0.2 | +34 (X: 0.75 wider, +106) | −36 (X −126) |
| `lip hook height` +0.2 | +12 (X +6) | −14 (X −6) |
| `x tolerance` +0.2 | −44 (X: 0.2 narrower, −75) | — |
| `y tolerance` +0.2 | 0.2 shorter in Y, −8 (X −11) | — |
| `compression offset` +0.2 | 0.2 thinner, −23 | — |
| `battery wire cut` +0.2 / +0.6 | −0.9 (V) / −2.1 (X) | — |
| `appendix` off → on | — | +21 (X +24) |
| `appendix height`, `appendix length`, `appendix gap` | no effect while `appendix` is off (as saved) | |
| `test parameter` | **no effect** | |

With the hollow body, `battery length` also cut 83 mm³ from the middle plate, which carries the same compartment [measured]. On GripX with the hollow body the cover part changes exactly as above, while the case bottom changes less, because the shell has less material around the compartment: `battery length` −1,188 (standard −2,076), `battery width` −1,095 (−1,873), `shift Y` +245 (+1,420), `flex width` −71 (−161), `lip width` −126 (same) [measured].

## Sizes as saved

| | GripV | GripX |
|---|---|---|
| battery cover (mm) | 39.40 × 63.15 × 4.57 | 38.05 × 62.70 × 4.60 |
| volume (mm³) | 2,969 | 3,900 |
| vertices | 344 (curved) | 78 (flat) |
| position (Z) | 26.6 to 31.1 | 26.6 to 31.2 |

[measured]. Both "Parts" presets export it, as `battery cover.stl` on disk ([Issues](../09-issues.md) A7).
