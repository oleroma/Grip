# Triggers (L2, R2, L4, R4)

R2 is the main trigger, R4 the back paddle under it [inferred from the names and positions]. All four objects use the modifier group `trigger` with a `part` menu (`R2` or `R4`), `button` = on, `SMD button` = the PCB switch object (`R2_pcb_button`, `R4_pcb_button`) and `left` = on for L2 and L4, which mirrors the part in X and flips its normals [wiring]. The case openings come from `R2 bool` (group `trigger`, `button` off) and `R4 bool` (the older group `R4`, `button` off), both in collection `R2R4 cutouts` with a Mirror modifier [wiring].

## How a trigger is built

`trigger base` does the work [wiring]:

1. **Arc body** (`trigger base geo`, twice: front and back): a curved bar on a circle of radius `trigger radius`, `width` wide (X) and `height` tall, with a stopper (`stopper length`, `stopper height`), rounded edges (`bevel`, `bevel subd`, `bevel cutoff`) and a mesh density of one ring per `subdivision length` mm. The fits `x tolerance` and `radius tolerance` come from the tolerance set.
2. **Length and tip** (`trigger cut`, front and back): the arc is cut to `trigger length` measured along the arc, minus the `top bevel`; the tip face is tilted by `tip angle offset` and sheared by `tip shear`. For the case cutter (`button` off) the length gets 6 mm extra (`boolean length offset`).
3. **Press cut** (`final cut`): trims the part by `button press tolerance` (from the press tolerance set), using `shift z`, `width` and `trigger radius`.
4. **Top face**: the front outline is filled, extruded and bevelled by `top bevel`.
5. **Marks** (`marks`, global `marks`).
6. **Placement** (`trigger align`): the part is built around the arc centre, then moved so that it rests on the PCB switch object: to the switch location, down by 1.6 + `button pressed height`, along the arc by `shift z`, away from the switch by `button radius offset`, sideways by `x offset`, and rotated about Z by `button rotation`. With `action` on, it is also rotated about the arc centre by the press travel, i.e. drawn pressed [inferred from the wiring: `action` only moves the part].

## Presets

Each variant fills the `R2` and `R4` slots from `GripV R2 parameters` / `GripV R4 parameters` and `GripX R2 parameters` / `GripX R4 parameters` [wiring]. In GripV only one `trigger parameters` node per preset is live (frame "more inward" for R2, "default" for R4); the other one (frame "SNES") is disconnected and has `button rotation` = 90, which would be 90 radians (≈ 5,157°), probably typed as degrees [wiring; the interpretation is inferred]. In GripX each preset has two live nodes, frame "GripX" (xbox) and "GripD" (dualsense), picked by the global `style` [wiring]. Two disconnected *Value* nodes in a frame "za3tarani" sit in the GripV presets [wiring].

Saved values of the live nodes (angles in radians, degrees in brackets) [wiring]:

| Input | GripV R2 | GripV R4 | GripX xbox R2 | GripX xbox R4 | GripX dualsense R2 | GripX dualsense R4 |
|---|---|---|---|---|---|---|
| `trigger length` | 28 | 40 | 30.5 | 21.2 | 30.15 | 24.1 |
| `trigger radius` | 30 | 80 | 40.7 | 24.6 | 40.7 | 37.4 |
| `width` | 12.96 | 12.96 | 9.2 | 11 | 10.8 | 10.9 |
| `height` | 11 | 11 | 14.4 | 12 | 14.4 | 12 |
| `tip angle offset` | −0.349 (−20°) | −0.524 (−30°) | −0.175 (−10°) | −0.585 (−33°) | −0.201 (−12°) | −0.508 (−29°) |
| `tip shear` | −0.349 (−20°) | 0.175 (10°) | 0 | 0.064 (4°) | −0.105 (−6°) | −0.208 (−12°) |
| `top bevel` | 1 | 1 | 1 | 0.7 | 1 | 0.7 |
| `bevel` | 2.6 | 2.6 | 2 | 2 | 2 | 2 |
| `bevel subd` | 1 | 1 | 1 | 1 | 1 | 1 |
| `bevel cutoff` | 0.5 | 0.5 | 0.5 | 0.5 | 0.5 | 0.5 |
| `stopper length` | 15 | 20 | 21.7 | 15.001 | 21.7 | 15.001 |
| `stopper height` | 2 | 2 | 1 | 2 | 1 | 2 |
| `button rotation` | 1.047 (60°) | 0.654 (37.5°) | 0 | 1.466 (84°) | −0.024 (−1.4°) | 1.728 (99°) |
| `shift z` | 5 | 25 | 20.6 | 4.2 | 20.6 | 2.5 |
| `button radius offset` | 5 | 2 | 1 | 2 | 1 | 2 |
| `button pressed height` | 1.29 | 1.29 | 1.29 | 1.29 | 1.29 | 1.29 |
| `x offset` | 0 | 0 | 0 | 0 | 0 | 0 |
| `subdivision length` | 0.5 | 0.5 | 1 | 1 | 1 | 1 |
| `action` | off | off | off | off | off | off |
| `x tolerance`, `radius tolerance` | tolerance set (`tolerance`) | | | | | |
| `button press tolerance` | tolerance set (`press tolerance`) | | | | | |

The tolerance-set values are in [7. Tolerances](../07-tolerances.md).

## What each input does

Measured by changing each input once (+10 %, +0.2, +0.1 rad or flipped) on the GripV presets and on both GripX styles; numbers are for GripV R4 unless noted [measured].

| Input | Effect on the trigger | Effect on the case bottom |
|---|---|---|
| `trigger length` | longer: +40 → 44 gives +468 mm³, 2.4 mm taller (GripV R2 +2.8: +287) | none |
| `trigger radius` | flatter arc: 80 → 88 gives +72 mm³, 1.5 mm taller | opening follows (−197) |
| `width` | +10 %: +522 mm³, about 1 mm wider | opening follows (−947) |
| `height` | +10 %: +412 mm³ | opening follows (−731) |
| `tip angle offset`, `tip shear` | tilt and shear the tip; a few mm³ | none |
| `top bevel` | rounder top edge; −6 mm³ | none |
| `bevel` | rounder long edges; −89 mm³ | none |
| `bevel subd` | 1 → 2: +130 mm³, +306 vertices, and more non-manifold edges | none |
| `bevel cutoff` | +36 mm³ | none |
| `stopper length`, `stopper height` | +44 / +31 mm³ | opening follows (−88 / −59) |
| `subdivision length` | mesh density only: 0.5 → 0.7 removes 179 vertices, volume unchanged | density only |
| `button rotation` | turns the part about Z; no volume change | opening follows (+199) |
| `shift z` | moves it along the arc; −38 mm³ | opening follows (+129) |
| `button radius offset`, `x offset`, `button pressed height` | move the part (exactly by the step, in Y, X or Z); no shape change | opening follows |
| `action` | moves the part (drawn pressed), no shape change | none |
| `x tolerance` / `radius tolerance` (default set 0.24 → 0.44) | −153 mm³, 0.21 mm narrower | none |
| `button press tolerance` (default set 0.55 → 0.75) | −27 mm³, 0.15 mm shorter | none |

GripV R2 and the GripX presets react the same way [measured]. With `style` = xbox only the "GripX" node acts and with dualsense only "GripD" [measured]. The `marks parameters` inputs of the trigger presets do nothing while the global `marks` is off (see [Marks](marks-and-logos.md)).

The case opening is built with the same preset, but its shape does not depend on the tip and bevel inputs or on `trigger length` (the cutter is 6 mm longer and, by the measurements, already reaches out of the case) [measured].

## Sizes and mesh quality

As saved (bounding box in mm, volume in mm³) [measured]:

| | GripV | GripX xbox | GripX dualsense |
|---|---|---|---|
| L2 / R2 | 23.0 × 18.4 × 21.9, 2,913 | 9.0 × 26.5 × 18.2, 2,497 | 11.1 × 26.8 × 18.1, 2,923 |
| L4 / R4 | 24.0 × 27.3 × 33.6, 4,739 | 18.0 × 12.3 × 16.4, 1,891 | 17.1 × 12.8 × 23.2, 2,532 |
| non-manifold edges L2/R2 | 0 | 4 | 4 |
| non-manifold edges L4/R4 | 2 | 6 | 1 |

The non-manifold edges are small defects of the generated mesh; `bevel subd` = 2 adds more on every preset (up to 10) [measured]. They matter for two reasons: a slicer may complain, and the case is cut with the *Manifold* boolean solver, which needs closed inputs [inferred]. One measured consequence: with GripX xbox, setting R4 `shift z` from 4.2 to 4.62 made the **whole case bottom empty** (0 vertices), also at subdivision level very high, while 4.0, 4.3, 4.4, 4.5 and 5.0 were fine [measured with Blender 5.2.0 on Windows]. The same change gave a normal case bottom with bpy 5.2.2 on Linux [measured], so whether it happens depends on the Blender build. If a trigger change makes the case bottom disappear, nudge the trigger value; see [Issues](../09-issues.md) B1.

## Leftovers

- `R2 tip` and `R4 tip` (collection `R2R4 tip`) carry trigger modifiers but nothing reads them and no preset exports them [wiring].
- The group `R4` (used by `R4 bool` and `R4 tip`) is an older copy of `trigger` with its `part` fixed to R4 and 16 marks inputs that are not connected to anything [wiring].
- `R4R2 parameters`, `topoff` and `trigger cap` (a separate trigger cap with pad and tip offsets) are not connected to any object [wiring].
