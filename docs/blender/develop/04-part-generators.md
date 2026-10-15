# 4. Part generators

Every generator follows the same pattern:

```
modifier group on the object (flags: part / cutter, left / right, which piece)
└─ selector (part = this part's slot)  →  … outputs (named values)
   └─ geometry group(s)               →  part, or the cutter when the part flag is off
```

This page goes through the generators one by one. For each it gives the steps and what they achieve. The meaning of individual parameters is in the [customize guide](../customize/README.md#parts).

## Buttons and caps

**Groups:** `abxy button` / `dpad button` / `select button` / `home button` → `abxy` / `dpad` / … → `button and caps`.

The family group (`abxy`, …) unpacks the preset with `button outputs`, `caps outputs` and `base curve outputs`, and calls `button and caps`. That group builds every piece of a button from one outline:

| Subgroup | Builds | Purpose |
|---|---|---|
| `base shape` | the 2D outline from `width`, fillets and tolerances, or the custom curve | one outline drives shaft, cap and hole, so they always match |
| `button` | the shaft: extruded outline, stopper collar, bevels | shrunk by `button tolerance` so it slides in the hole |
| `caps` | the cap: outline grown by `caps offset`, the hook and flex cut, the fit to the shaft | placed from the top face of the basemesh, so the caps follow the case surface |
| `cutoff` | the case hole | made from the same outline, without the tolerance |
| `marks` | the identification letter | see Marks below |

The object flags pick the output: `button` on and `cap` off gives the shaft, `cap` on gives a cap, and `button` off gives the cutter. `Collection` supplies the custom cap outline.

The global `horizontal buttons` is read in 16 places. It fixes the top bevel and the outline fillet to one segment, turns off the custom base curve for ABXY and D-pad, and switches the bottom bevel profile. Off, the results jump between two shapes for some inputs, which looks like a boolean that fails.

`dpad button` outputs nothing while the D-pad stick is on, so the two D-pad designs cannot both appear.

## Capacitive plate

**Groups:** `capacitive plate` → `plate base` → `capacitive plate geometry`, `stem`.

The ABXY preset's `capacitive plate parameters` turns its menu (disabled, plate, knob) into two booleans, `capacitive` and `knob`. `plate base` builds the knob or the plate around the ABXY outline (it reads the ABXY cap values, so the plate follows the buttons), plus the stem. With `plate` off it gives the cutter.

## Sticks

**Modifier stack:** `stick module` → Bevel → Bevel → `top module` → `extra`, each reading the stick slot through `selector` (`Menu` = stick L / stick R).

| Stage | Groups | What it does |
|---|---|---|
| `stick module` → `stick` | `stick base`, `thumbstick shaft`, `shield`, `stick hole`, `morphed square`, `XY correction` | the body: base on the module shaft, neck shaped for the tilt range, skirt; with `hole` on, the case hole instead |
| 2 Bevel modifiers | — | edge rounding, limited by weight, so only the marked top and middle edges are rounded |
| `top module` → `texture` | `convex top`, `flat`, `to circle`, `extrude texture`, ico sphere and grid frames | the thumb surface: curvature, outline, texture |
| `extra` → `extra operations` | `XY corr`, `stick action` | final offset and the tilted preview |

The stick's height is taken from the top face of the basemesh (`basemesh top face position`), so it follows the case. The texture runs as a separate modifier after the bevels, probably so the bevel does not round the texture.

## D-pad stick

**Group:** `dpad stick` (`Menu` = which piece, `bool` = cutter).

One group builds all six pieces from one preset, with subgroups `rocker`, `ball`, `ball support`, `rocker support`, `stem base` (the stick and its hook) and `cap`. The `Menu` input picks which piece the object shows. Because the pieces share the numbers, the stick, rocker, ball and cap always fit. The stick reaches up to the basemesh top face. The `dpad stick` switch lives in the shared constructor `dpad stick parameters`, which is why the export presets can switch it for both variants at once.

## Triggers

**Groups:** `trigger` → `trigger base` (frames "front" and "back").

1. **Arc body** (`trigger base geo`, front and back): a bar on a circle of radius `trigger radius`, `width` × `height` in section, with a stopper, bevels and one ring per `subdivision length` mm. The tolerances come in here.
2. **Length and tip** (`trigger cut`): the arc is cut to `trigger length` along the arc, minus the top bevel. The tip is tilted by `tip angle offset` and sheared by `tip shear`. For the cutter the length gets 6 mm extra (`boolean length offset`), so the opening always reaches out of the case.
3. **Press cut** (`final cut`): trims the part by `button press tolerance`.
4. **Top face**: the front outline is filled and bevelled.
5. **Marks.**
6. **Placement** (`trigger align`): the part is built around the arc centre, then moved onto the board switch object given in the modifier (`SMD button`). It goes down by 1.6 + `button pressed height`, along the arc by `shift z`, away from the switch by `button radius offset`, sideways by `x offset`, and is turned by `button rotation`. With `action` on it is also rotated about the arc centre, which draws it pressed.

*Why this way:* the trigger is defined by where its switch is and by the path it moves along. The same definition then gives a part that presses the switch, and an opening that matches its motion. `left` mirrors the result for L2/L4.

`R4 bool` uses the older group `R4`, a copy of `trigger` with the part fixed to R4. `trigger cap`, `R4R2 parameters` and `topoff` are not connected.

## Bumpers

**Groups:** `lever R1L1` → `lever R1L1 base` (349 nodes).

`lever R1L1` reads the slot, calls `lever R1L1 base`, adds marks, mirrors with `flipX` for L1 (`left`), and nudges the part down by 0.001 mm. With the global `stock bumpers` it outputs the fixed `R1 stock` / `L1 stock` meshes instead.

`lever R1L1 base` works from 2D profile meshes in the collection `R1L1 profiles`:

- **Profile:** `R1 lever profile`, or `R1 flex profile` when `R1L1 flex` is on. The cutter uses the matching `… bool profile`.
- **Body:** the profile is extruded to `width` and shaped by moving the vertices at the extremes of each axis (`height`, `overlap`, `overlap slant`, `top bevel`). *Why:* the profile carries the hand-designed cross-section, and the parameters only stretch it, so it keeps its shape at any size.
- **Stem** (`R1 stem`): the pivot.
- **Press face:** the insert at the front and the press fit.
- **Curved option:** the outline comes from a curve per variant and style (`custom shape  gripV`, `custom shape gripD`, `custom shape gripX`), picked with `part variant switching`.
- **Placement** (`R1L1 xgrip position`): moves the result to `X`, `Y`, `Z`.
- **Shell outputs:** `for sdf top`, `for sdf bottom` and `middle plate` give the shapes that shell bodies keep solid or clear around the bumper, grown by the constant `sdf thickness` = 2.

## Battery cover

**Groups:** `cover` → `battery bool and cover`. The case bottom uses a copy, `coVer base`.

1. Unpack the preset (`separate cover basic`, `cover outputs`).
2. **Battery block:** `battery length` × `width` × `height`, moved by `shift Y`.
3. **Cover plate** (`cover base plate`): `cover base thickness` thick, overlapping the opening by `cover base overlap`, curved to the case underside with `curved cover`.
4. **Lips** (`cover lips`): flexible tongues with hooks.
5. **Fits:** `x tolerance`, `y tolerance` and `compression offset` shrink the cover against the opening.
6. **Nail cut:** a constant cylinder for the finger notch.
7. **Appendix** and **wire cut**.

With `bool` on the group returns the compartment instead of the cover. Shell bodies use the flat `no extrude` output. `coVer base` duplicates this logic for the case bottom, so a fix has to be made twice (or the copy replaced by the original group).

## Screws

**Groups:** `screws` → `screw` (151 nodes) per definition, with `MirrorX`.

`screws` places two `selector` nodes on the `screw` slot, `part index` 0 (FRONT) and 1 (BACK). It builds each with `screw` and mirrors both across X = 0, so two definitions give four screws. Its flags pick the output:

| Flags | Output | Used by |
|---|---|---|
| none | holes, head recesses, nut pockets | `screw bools` (case top), `bottom bools` |
| `sdf` | solid bosses | `button shafts sdf` in shell bodies |
| `nut lock` | a wedge for the front nut, built at the origin and not mirrored | object `nut lock` |
| `reinforcer` | sleeves around the screws (frame "REINFORCER" in `screw`) | object `reinforcers` (GripX) |

`screw` reads the current basemesh (`basemesh variant`) and contains the constant 40 twice. The geometry is therefore tied to the split height and the basemesh top, but exactly how has not been traced.

## Pins

**Groups:** `pins` → `pin base`.

A box `pin width` × `pin width` × `pin height` centred on `X`, `Y`, `Z`. With `bool` off it is shrunk by `xy tol` and `z tol` (the part). With `bool` on it is used at full size and mirrored with `MirrorX` (the holes). So one pin object is printed twice, and the holes exist on both sides.

## Scroll wheel

**Groups:** `scrollwheel`, `scrollwheel stem`, `scroll bool`.

The wheel, core and holder are hand-modelled meshes. The groups do not build geometry; they move vertices that carry named attributes:

| Attribute | Moved by |
|---|---|
| `scroll` | `scroll radius offset`, outward |
| `wid` | `scroll width offset` minus half of `scroll wheel tolerance`, on both faces |
| `shift x` (`shift X` in `scroll bool`) | `scroll wheel shift X` |

*Why:* the wheel's rib pattern and axle are easier to model than to generate, and only the sizes that matter for fit need to be parameters. To make a new shape parametric, tag its vertices with the same attributes. `scrollwheel holder` has a Geometry Nodes modifier with no group, so it is used as modelled.

## PCB slot and cable holder

- **PCB:** the object `pcb cutout` is half of the board outline. The group `GripX pcb` (used by both variants) calls `pcb`, which grows the outline by the tolerance, mirrors it, and builds the slot, the pocket below and the ledge. The `supports` collection is subtracted from this cutter, so the support blocks stay in the case.
- **Cable holder:** `MirrorX` → `cable hole`. The holder's own half mesh is mirrored, a box the size of the cable plug is subtracted (`cable holder usb bool`, reading `cable holder parameters`), the `cable holder teeth` object is added, and the current basemesh is subtracted so the part follows the outer shell. `cable holder parameters` is a plain group with no inputs, shared by all variants.

## Marks and logos

- **`marks`** takes the part, the part's bundle and the flags `marks` and `mirror`. It writes text or curves onto the face at the minimum or maximum of the chosen axis. With `type` = `parameter` the text is built from the bundle values named in `parameters`, so a part can print its own tolerance. The font is fixed to Segoe UI Bold inside `marks parameters`. The custom letter comes from an *Index Switch* (`T`/`D`/`L`) whose index is typed, not linked to a tolerance menu.
- **`logo`** (second modifier on caps) engraves the curves of a collection (`type` = custom) or a text. It is gated by the global `button logo`.

## Case and middle plate

See [Case pipeline](03-case-pipeline.md).
