# Scroll wheel

A small wheel between the right stick and the face buttons, on its own axle [inferred from the shape and position]. Three objects in the collection `scrollwheel`, all with their origin at X 20.03, Y −51.5, Z 51.0 [wiring]:

| Object | Modifier | Built from | GripV size (mm), volume | GripX |
|---|---|---|---|---|
| `scrollwheel` (rotated 180° about X) | group `scrollwheel` | its own hand-made mesh (460 vertices) | 4.00 × 20.76 × 20.76, 1,091 mm³ | 3.50 × 20.76 × 20.76, 937 mm³ |
| `scrollwheel core` (rotated 180° about X) | group `scrollwheel stem` | its own mesh (470 vertices) | 10.25 × 9.08 × 5.44, 129 mm³ | 127 mm³ |
| `scrollwheel holder` | a Geometry Nodes modifier **with no node group** | its own mesh, unchanged | 9.77 × 8.79 × 15.15, 257 mm³ | same |

[wiring; sizes measured]. The case top opening is cut by `Wheel cutout (B)` (collection `wheel comp` in `source`, group `scroll bool`, plus a Bevel modifier) [wiring].

## How it works

The generators do not build the wheel; they **move tagged vertices** of the hand-made meshes [wiring]:

| Group | Named attribute (vertex tag) | Moved by |
|---|---|---|
| `scrollwheel` | `scroll` | `scroll radius offset` (outward, so the wheel diameter grows by twice the value) |
| `scrollwheel` | `wid` | `scroll width offset` minus half of `scroll wheel tolerance`, on both faces |
| `scrollwheel` | `shift x` | `scroll wheel shift X` |
| `scrollwheel stem` | `wid` | the same width rule, for the core |
| `scroll bool` | `shift X` (capital X) | `scroll wheel shift X`, and the width and radius offsets for the opening |

The values come from the `scrollwheel` slot (`GripV scrollwheel` / `GripX scrollwheel` › `scroll parameters`) [wiring]. Because the shapes are hand-made, anything other than these four adjustments (axle diameter, rib pattern, holder shape) is edited in the meshes themselves, in the `source` objects.

## Presets

| Input | GripV | GripX |
|---|---|---|
| `scroll radius offset` | −1.15 | −1.15 |
| `scroll width offset` | 0 | 0 |
| `scroll wheel tolerance` | 0.6 | 0.7 |
| `scroll wheel shift X` | −3.2 | −3.6 |

[wiring]. The GripX wheel is 0.5 mm narrower than the GripV one: 0.1 from the larger tolerance and 0.4 from the shift [measured sizes; the split is inferred from the effects below].

## What each input does

GripV, saved settings [measured]; GripX gave the same result for the tolerance.

| Input | Wheel | Core | Case top |
|---|---|---|---|
| `scroll radius offset` −1.15 → −0.95 | 0.4 larger diameter, +51 mm³ | — | −6.5 (opening grows) |
| `scroll width offset` 0 → 0.2 | 0.4 wider (0.2 per face), +114 | +7.6 | −27 |
| `scroll wheel tolerance` 0.6 → 0.8 | 0.2 narrower (0.1 per face), −57 | −3.8 | — |
| `scroll wheel shift X` −3.2 → −2.88 | 0.32 wider (one face moves), +100 | — | −21 |

So the clearance between the wheel and its opening is set by `scroll wheel tolerance` (half per side), and the other three inputs move the wheel and its opening together [measured].

## Export

No preset exports the scroll wheel parts. The OrcaSlicer projects reference `scrollwheel*` objects from an earlier export [wiring, 3MF contents measured]. See [Issues](../09-issues.md) A8 and D4.
