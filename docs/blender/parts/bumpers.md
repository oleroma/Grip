# Bumpers (L1, R1)

`L1` and `R1` are the shoulder bumpers. Both objects use the modifier group `lever R1L1` with `marks` = on and `left` = on for L1, followed by a Bevel modifier `r1 front bevel` [wiring]. Their numbers come from the `R1L1` slot of the variant: `GripV  lever R1L1` (two spaces) or `GripX lever R1L1` [wiring]. The case openings are cut by the object `R1L1 bool` (collection `R1L1 cutouts` in `source`), which uses the group `lever R1L1 bool` on the same preset, so the opening always follows the bumper [wiring].

## How a bumper is built

`lever R1L1` [wiring]:

1. `selector` (part `R1L1`) picks the variant's bumper bundle; `lever R1L1 base` builds the right bumper from it.
2. `marks` engraves `R` or `L` (see [Marks](marks-and-logos.md)).
3. With `left` on, `flipX` mirrors the part to the left side.
4. A tiny Z shift (−0.001 mm) is applied.
5. With the global `stock bumpers` on, the generated part is replaced by the fixed meshes `R1 stock` / `L1 stock` (296 vertices each).

`lever R1L1 base` (349 nodes, no frames) works from 2D profile meshes in the collection `R1L1 profiles` [wiring; the step reading is inferred from the node order and the measurements below]:

- **Profile.** `R1 lever profile` (9 vertices), or `R1 flex profile` when `R1L1 flex` is on; the cutter uses `R1 lever bool profile` / `R1 flex bool profile`.
- **Body.** The profile is extruded to `wdith` and shaped by moving the vertices at the extremes of each axis (`height`, `overlap`, `overlap slant`, `top bevel`, `bevel inner`).
- **Stem.** `R1 stem` adds the pivot stem (`stem radius`, `stem tolerance`).
- **Press face.** The button insert at the front (`button height`, `depth`, `insert depth`, `button inset offset`, `button front shift X`) and the press fit `button press tol`.
- **Curved option.** With `curved R1L1` on, the outline comes from a curve per variant: collection `custom shape  gripV` (`bumper curve gripV`) for GripV, `custom shape gripD` (`bumper curve gripD`) for GripX dualsense, and `custom shape gripX`, which is **empty**, for GripX xbox [wiring].
- **Placement.** `R1L1 xgrip position` moves the result to `X`, `Y`, `Z`.
- **Shell outputs.** Extra outputs (`for sdf top`, `for sdf bottom`, `middle plate`) give the shapes that hollow and lattice bodies keep clear, grown by the constant `sdf thickness` = 2 from `lever R1L1 outputs` ([6.5](../06-body-types.md#65-hollow-the-sdf-shell)).

**`R1L1 flex`** switches between two bumper designs. On (GripV), the bumper has an extra arm about 17 mm long towards the centre of the controller: turning it off made GripV L1/R1 17 mm shorter in X and 77 mm³ lighter, and turning it on for GripX xbox made them 17 mm longer and 78 mm³ heavier [measured]. I read the arm as a flexure that lets the bumper bend instead of pivoting on the stem [inferred from the name and the shape].

## Presets

Saved values of the live nodes [wiring]. GripX has two nodes, frame "GripX" for xbox and frame "GripD" for dualsense, picked by the global `style`.

| Input | GripV | GripX xbox | GripX dualsense |
|---|---|---|---|
| top bevel | 2.5 | 2.5 | 2.7 |
| stem tolerance | −0.025 | 0.1 | 0.1 |
| wdith (sic) | 20 | 21 | 21 |
| height | 8.16 | 10.6 | 10.6 |
| stem radius | **2**, from a *Value* node (the input itself shows 3) | 3 | 3 |
| bumper Z tolerance | 0.52 | 0.3 | 0.3 |
| X tolerance | 1 | 1 | 1 |
| bevel inner | 3 | 4 | 4 |
| bevel inner sbdiv | 2 | 2 | 2 |
| overlap | −5.16 | −4 | −3.6 |
| overlap tolerance | 0.48 | 0.3 | 0.3 |
| button height | 0 | 2.4 | 2.4 |
| depth | 2 | 1.8 | 1.8 |
| insert depth | 5 | 2.5 | 2.5 |
| button inset offset | 1 | 1 | 1 |
| overlap slant | 2.9 | 3 | 3 |
| button front shift X | 18 | 17 | 18 |
| curved R1L1 | off | off | off |
| curved button thickness / slant / depth tolerance / bevel | 6.1 / −1 / 1 / 1 | same | same |
| X / Y / Z | 28 / −14 / 40 | 28 / −14 / 40 | 28 / −14 / 40 |
| R1L1 flex | on | off | off |
| button press tol | tolerance set on `press tolerance`: −0.1 / 0 / 0.1 | 0, typed | 0, typed |

In `GripX lever R1L1` a `tolerance set` (0 / 0 / 0) exists but is not connected, so the GripX bumpers do not follow the global `press tolerance` [wiring]. Measured: `press tolerance` = tight made the GripV bumpers 0.1 mm longer in Y (+5.6 mm³ each) and changed the GripX triggers, but not the GripX bumpers [measured]. That is why the GripX `pres_tight`, `pres_default` and `pres_loose` export folders hold identical bumpers ([Issues](../09-issues.md) A3).

The GripV `stem radius` input is linked from a *Value* node set to 2. The number 3 shown on the input (and recorded in `tracking.json`) is not used [wiring]. Changing the *Value* node from 2 to 2.2 made each bumper 0.2 mm longer in X (+17 mm³) and removed 35 mm³ from the case top [measured].

## What each input does

Each input changed once (+10 %, at least +0.2; booleans flipped) with the saved settings, on GripV and on GripX xbox; per bumper, case changes in mm³ [measured]. "Longer in X" is along the bumper (left to right), Y is front to back, Z is up.

| Input | GripV | GripX xbox | Case |
|---|---|---|---|
| `wdith` | +2: 1.0 longer in X, +125 mm³ | +2.1: 1.05 longer, +147 | opening follows (V top −178, bottom −71) |
| `height` | +0.82: 0.82 taller, +172 | +1.06: 1.06 taller, +228 | top −531 (V), −588 (X) |
| `stem radius` | *Value* 2 → 2.2: 0.2 longer in X, +17 | 3 → 3.3: 0.3 larger in X and Y, +47 | top −35 (V), −97 (X) |
| `stem tolerance` | +0.2: 0.2 shorter in X, −75 | +0.2: 0.2 smaller in X and Y, −28 | none |
| `top bevel` | +0.25: −18 | +0.25: −20 | none |
| `bumper Z tolerance` | +0.2: 0.2 lower, −42 | same, −43 | top +4.5 (V) |
| `X tolerance` | +0.2: 0.1 shorter in X, −12.5 | same, −14 | none |
| `overlap` | +0.52: underside moves up 0.52, −49 | +0.4: up 0.4, −38 | bottom +80 (V), +49 (X) |
| `overlap tolerance` | +0.2: underside up 0.2, −26 | same, −29 | bottom +8, top +12 to +14 |
| `overlap slant` | +0.29: −6 | +0.3: −7 | none |
| `button height` | 0 → 0.2: 0.2 deeper in Y, +46 | +0.24: 0.24 deeper, +67 | none |
| `depth` | +0.2: +20 | +0.2: +22 | bottom −19 / −16, top −33 / −25 |
| `insert depth` | +0.5: +77 | +0.25: +39 | bottom −103 / −42, top −93 / −34 |
| `button inset offset` | +0.2: −31 | +0.2: −32 | none |
| `button front shift X` | +1.8: 1.8 longer in X, +6 | +1.7: 1.7 longer | bottom +26 / +17, top −62 / +35 |
| `button press tol` | default value 0 → 0.2: 0.2 shorter in Y, −11 | typed 0 → 0.2: −19 | none |
| `X` | +2.8: both bumpers move 2.8 outwards | same | top +119 / +190, bottom +49 / +33 |
| `Y` | +1.4: the back moves 1.4 forward (the front stays at the case), −101 | same, −172 | top +188 / +405 |
| `Z` | +4: both move up 4 | same | bottom +651 / +507, top −593 / −540 |
| `R1L1 flex` | on → off: 17 shorter in X, −77 | off → on: 17 longer, +78 | top +574 (V off), −721 (X on) |
| `curved R1L1` | off → on: 11.4 longer in X, 2.8 deeper, +455 | off → on: **3.7 lower, 2.6 shorter, −1,095** (empty outline collection) | V top −346, bottom −260; X top +929, bottom +506 |
| `bevel inner`, `bevel inner sbdiv` | no effect (also with flex off) | no effect | |
| `curved button thickness` | no effect, also with `curved R1L1` on | no effect | |
| `curved button slant` | only with `curved R1L1` on: +0.2 → +34 | | bottom −39 |
| `curved button depth tolerance` | only with `curved R1L1` on: +0.2 → 0.2 shorter in X, 0.4 in Y, −165 | | none |
| `curved button bevel` | only with `curved R1L1` on: +0.2 → −14 | | none |

With `style` = xbox, edits to the "GripD" node change nothing; with dualsense the "GripD" node drives both bumpers [measured]. Input for input, the dualsense node gives the same bumper changes as the xbox node within a few mm³ (`wdith` +2.1: +141.5; `height` +1.06: +227, case top −569; `stem radius` +0.3: +47, case top −97) [measured]. The one real difference is `curved R1L1`: on dualsense it works, because `custom shape gripD` has a curve. The bumpers became 10.9 mm longer and 1.2 mm deeper, +508 mm³ each; case top −800, bottom −139 [measured].

### With shell bodies

With `body type` = `hollow` (GripX xbox), each bumper changes exactly as with the standard body, but the case does not: the shell keeps a solid zone around the bumper (the `for sdf top` / `for sdf bottom` outputs), so a larger bumper can add case material instead of removing it [measured]:

| Input (GripX xbox) | Case, standard body | Case, hollow body |
|---|---|---|
| `stem radius` +0.3 | top −97 | top +319 |
| `X` +2.8 | top +190, bottom +33 | top −254, bottom −5 |
| `Y` +1.4 | top +405 | top +82 |
| `Z` +4 | top −540, bottom +507 | top −713, bottom +96 |
| `height` +1.06 | top −588 | top −358 |
| `insert depth` +0.25 | top −34, bottom −42 | top +93, bottom +1 |
| `R1L1 flex` off → on | top −721 | top +348 |
| `curved R1L1` off → on (empty outline, see above) | top +929, bottom +506 | top +1,259, bottom +506 |

The global `stock bumpers` replaces the generated bumpers: on GripV, L1/R1 became 14.2 mm shorter in X and +119 mm³, the case top −1,471 and the case bottom +799 [measured], matching the values in [3. Global switches](../03-global-switches.md#stock-bumpers).

## Sizes as saved

| | GripV | GripX xbox | GripX dualsense |
|---|---|---|---|
| L1 / R1 (mm) | 46.53 × 11.54 × 12.32 | 29.90 × 13.14 × 14.00 | 30.9 × 13.1 × 13.6 |
| volume (mm³) | 1,870.7 | 2,416 | 2,362 |
| non-manifold edges | 0 | 0 | 0 |

[measured; the GripX dualsense size is from [4.3](../04-variants-and-styles.md#43-gripv-versus-gripx)].

## Marks

The bumpers carry `R` and `L` from their own `marks parameters` node (`L-R side` on), switched by the `marks` input on the modifier, which is on as saved [wiring]. On Windows the letters add 12 (L) and 415 (R) vertices [measured in the earlier run]. On a machine without the Windows font Segoe UI Bold the letters are not generated at all (L1 and R1 came out identical, 364 vertices) [measured in the cloud run], so the marks inputs could not be measured there. See [Marks](marks-and-logos.md) and [Issues](../09-issues.md) B7.

## Export

The GripV "Parts" preset exports L1 and R1 with `press tolerance` swept (folders `press_*`); the GripX "Bumpers" preset exports them per style with `press tolerance` swept (folders `pres_*`), which gives identical files (see above) [wiring]. Neither preset exports the stock bumpers.
