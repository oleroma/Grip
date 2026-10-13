# Thumbsticks

`StickL` and `StickR` are the two thumbstick caps. Each has a modifier stack of five: `stick module` (Geometry Nodes, builds the stick), two Bevel modifiers (top and middle edges, weight-limited), `top module` (Geometry Nodes, adds the top texture) and `extra` (Geometry Nodes, final operations). Their `Menu` input is `stick L` or `stick R`, which is the preset slot they read [wiring]. The case holes come from `StickL hole` and `Stick R hole` in `source` (the same groups with `hole` on) plus fixed cutout meshes (see [Case](../05-case.md)) [wiring].

Positions: StickL at X −23.5, Y −52.5, Z 45.2; StickR at X 34, Y −52, Z 45.2 (object origins) [wiring]. The stick's height is measured from the top of the current basemesh (`basemesh top face position` = highest Z of the subdivided basemesh), so the subdivision level shifts it very slightly [wiring; at "high" and "very high" StickR changed by 8 vertices and 0.001 mm³, measured].

## Presets

**GripV** has one preset per stick: `GripV stick L parameters` (square top, concave, grid texture) and `GripV stick R parameters` (circle top, convex, icosahedron texture) [wiring].

**GripX** has several presets per stick, chosen by a *Menu Switch* inside the group; the menu value comes from a separate *Menu* node (`stick menu` in frame "STICK VARIANT" for StickL) [wiring]:

| Stick | Options (frame label in brackets where it differs) | Saved |
|---|---|---|
| StickL | Xbox cap easy print tall, Xbox cap, Octagonal 18d range (frame "Convex/concave"), Xbox Elite2 stick base, Xbox cap easy print short (60%) | Xbox cap easy print short (60%) |
| StickR | normal (frame "Convex/concave/flat"), small round, small square, 8 dir | normal |

A sixth set of StickL nodes (unlabelled frame) is not connected to the menu [wiring]. The export preset overrides the *Menu Switch* directly (removing its link to the *Menu* node while it exports) [wiring].

Measured sizes of every GripX stick preset are in [reference/measurements.md](../reference/measurements.md#gripx-stick-presets).

## Parameters

A stick preset is a *Join Bundle* of six constructors. Measured effects are for GripV StickR / StickL with the saved settings unless noted [measured]; the full per-value results for both variants are in the preset tables.

### `basic stick parameters`

| Input | What it does |
|---|---|
| stick top radius | radius of the cap top: +0.7 → stick 0.38 taller, +141 mm³ |
| stick heght (sic) | height of the stick above the case: +0.7 → stick exactly 0.7 taller |
| range degrees | tilt range the stick must clear: +1.8° → −82 mm³, reshaped neck |
| contact top offset, contact bottom offset, topmost offset | shape of the rim that touches the case hole at full tilt (a few mm³ each) [inferred from names; effects measured] |
| base size, base height | the part that grips the joystick module's shaft (+26 / −38 mm³) |
| action | on: shows the stick tilted by `action rotation` (StickR 2.9 mm taller bounding box, moved sideways); off as saved |
| action rotation | direction of that tilt, radians; no effect while `action` is off |
| top bevel | top edge rounding: +0.2 → 0.10 lower, −14.5 mm³ |
| middle bevel | no effect on GripV sticks; on GripX StickL (short preset) +0.2 → −4 mm³ |
| shaft tolerance | clearance of the hole for the joystick shaft: +0.2 → −7.7 mm³ |
| shaft Z offset | depth of that hole: +0.2 → +2.4 mm³ |

### `advanced stick parameters`

| Input | What it does |
|---|---|
| contact angle | angle of the contact surface between stick and case hole: +2.3 → stick −3 mm³, case top +8 mm³ |
| hole bevel | bevel of the case hole only |
| hole radius | radius of the case hole and the matching stick neck: −0.9 → stick −116 mm³, case top +164 mm³ |
| stick subdivision | resolution of the stick (vertex count) |
| stick hole subdivision | resolution of the case hole |
| stick  XY correction (two spaces) | on: shifts the stick by (`X correction`, `Y correction`); off as saved, and then those two values do nothing |
| X correction, Y correction | see above (turning the switch on moved StickR by exactly +0.05 / +1.0 = its X and Y correction) |
| shaft X correction, shaft Y correction | no effect in any tested setting |
| case cutout thickness | GripX only: thickness of the adjusted case cutout around the stick (+0.2 → case top +53 to +96 mm³); no effect on GripV, whose cutouts are fixed meshes |
| swap stick rotation | rotates the stick's mesh layout by a step (vertex changes only) |

### `stick top parameters`

| Input | Options | What it does |
|---|---|---|
| top shape | circle, square | outline of the top (GripV StickR circle → square +106 mm³) |
| swap top rotation | | rotates the top texture/outline |
| extrude texture | | on: the texture is raised (+0.34 mm, +33 mm³ on GripV StickR) |
| top curvature | concave, convex, flat | dish of the top (GripV StickR convex → concave −196 mm³, 2.18 mm lower) |
| texture type | grid, icosahedron | pattern on the top |
| square top subd, square morph | | only for square tops: corner subdivision and how much the square bulges |

### `icosahedron texture parameters` and `grid texture parameters`

Only the set matching `texture type` has an effect. Icosahedron: `texture height`, `texture sharpness`, `icosahedron subdivisions`, `icosahedron curvature offset`. Grid: `texture height`, `texture subdivisions`, `texture sharpness`, `grid curvature offset`, `scale`, `bottom xy correction`, `bottom z correction`, `z offset` [measured: grid values did nothing on GripV StickR (icosahedron) and did change GripV StickL (grid)].

### `shield parameters`

| Input | What it does |
|---|---|
| sheild (sic) | the skirt that covers the case hole; off removes it (StickR −291 mm³, 6.7 mm narrower, 2 mm lower) |
| sheild height | height of the skirt (+1.24 → 2.9 mm wider, +119 mm³) |
| shield cutoff height | where the skirt is cut off (+0.68 → −40 mm³) |
| sheild radius offset | skirt radius (+0.2 → 0.22 mm narrower) |
| FDM shield thickness, FDM Z correction | print-oriented thickening of the skirt and its height correction (+22 / +26 mm³) |

## Values

| Constructor › input | V L | V R | X L Octagonal 18d range | X L Xbox cap | X L easy print tall | X L Elite2 base | X L easy print short (60%) | X R normal | X R small round | X R small square | X R 8 dir |
|---|---|---|---|---|---|---|---|---|---|---|---|
| basic › stick top radius | 7 | 7 | 6.8 | 8.3 | 8.3 | 2.98 | 8.3 | 5.75 | 4.5 | 4.5 | 4.5 |
| basic › stick heght | 7 | 7 | 6.7 | 9.2 | 10.2 | 4 | 8.9 | 5.6 | 4.4 | 4.8 | 4.4 |
| basic › range degrees | 18 | 18 | 18 | 16 | 17 | 15.3 | 11 | 18 | 18 | 18 | 14 |
| basic › contact top offset | 0.4 | 0.4 | 1.5 | 3.1 | 1.9 | −3.5 | 1.9 | 1.1 | 1.1 | 1.1 | 1.1 |
| basic › contact bottom offset | 1.2 | 1.2 | 2.6 | 2.6 | 2.6 | 5 | 2.6 | 2.48 | 2.48 | 2.48 | 2.48 |
| basic › topmost offset | 1.3 | 1.3 | 0.5 | 4.4 | 4.2 | 4.9 | 3.9 | 0.6 | 0.6 | 0.6 | 0.6 |
| basic › base size | 4.2 | 4.2 | 4.2 | 4.2 | 4.2 | 4.2 | 4.2 | 4.2 | 4.2 | 4.2 | 4.2 |
| basic › base height | 8.8 | 8.8 | 9.3 | 9.3 | 9.3 | 9.3 | 9.3 | 9.3 | 9.3 | 9.3 | 9.3 |
| basic › top bevel | 0.6 | 0.6 | 0.2 | 0.4 | 0.4 | 0.3 | 0.4 | 0.4 | 0.4 | 0.4 | 0.4 |
| basic › middle bevel | 1.2 | 1.2 | 1.2 | 0 | 2 | 1.2 | 1 | 1 | 1 | 1 | 1 |
| basic › shaft tolerance | 0.2 | 0.2 | 0.2 | 0.2 | 0.2 | 0.2 | 0.2 | 0.2 | 0.2 | 0.2 | 0.2 |
| basic › shaft Z offset | −0.5 | −0.5 | −0.5 | −0.5 | −0.5 | −0.5 | −0.5 | −0.5 | −0.5 | −0.5 | −0.5 |
| advanced › contact angle | 23 | 23 | 18 | 16 | 17 | 20 | 11 | 18 | 18 | 18 | 14 |
| advanced › hole bevel | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 2 | 2 | 2 | 2 |
| advanced › hole radius | 9 | 9 | 8.3 | 8.3 | 8.3 | 8.3 | 8.3 | 8 | 8 | 8 | 8 |
| advanced › stick subdivision | 128 | 128 | 128 | 128 | 128 | 128 | 128 | 128 | 128 | 256 | 8 |
| advanced › stick hole subdivision | 128 | 128 | 8 | 8 | 8 | 8 | 8 | 8 | 8 | 8 | 8 |
| advanced › stick XY correction | off | off | off | off | off | off | off | off | on | on | on |
| advanced › X / Y correction | 0.05 / 1 | 0.05 / 1 | 0.05 / 0.8 | 0.05 / 0.8 | 0.05 / 0.7 | 0.05 / 0.8 | 0.05 / 0.8 | 0.2 / −0.1 | 0.2 / −0.1 | 0.2 / −0.1 | 0.2 / −0.1 |
| advanced › case cutout thickness | 2.5 | 2.5 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 |
| advanced › swap stick rotation | on | off | off | off | off | off | off | off | off | off | off |
| top › top shape | square | circle | circle | circle | circle | circle | circle | circle | circle | square | square |
| top › top curvature | concave | convex | convex | flat | flat | flat | flat | convex | convex | convex | flat |
| top › texture type | grid | icosahedron | icosahedron | icosahedron | icosahedron | icosahedron | icosahedron | icosahedron | icosahedron | grid | grid |
| top › extrude texture | on | on | on | off | off | off | off | on | on | on | on |
| top › swap top rotation | on | on | off | off | off | off | off | off | off | on | on |
| top › square morph | 0.08 | 0.08 | 0.25 | 0.25 | 0.25 | 0.25 | 0.25 | 0.08 | 0.08 | 0.08 | 0.08 |
| shield › sheild | on | on | on | on | on | on | on | on | on | on | on |
| shield › sheild height | 12.4 | 12.4 | 13.195 | 13.195 | 13.195 | 13.195 | 13.195 | 13.195 | 13.195 | 13.195 | 13.195 |
| shield › shield cutoff height | 6.8 | 6.8 | 5.75 | 5.75 | 5.75 | 5.75 | 5.75 | 7.5 | 7.5 | 7.5 | 8.4 |
| shield › sheild radius offset | 0 | 0 | 1.34 | 1.34 | 1.34 | 1.34 | 1.34 | 1.34 | 1.34 | 1.34 | 1.34 |
| shield › FDM shield thickness | 0.2 | 0.2 | 0.2 | 0.2 | 0.2 | 0.2 | 0.2 | 0.2 | 0.2 | 0.2 | 0.2 |
| shield › FDM Z correction | 1.8 | 1.8 | 2.3 | 2.3 | 2.3 | 2.3 | 2.3 | 2.3 | 2.3 | 2.3 | 2.3 |

Texture values (icosahedron and grid) per preset are in the preset tables ([GripV](../reference/preset-values-GripV.md), [GripX](../reference/preset-values-GripX.md)).

## Export

GripV exports only **StickL**, as `stick`, and sweeps its top shape, curvature, texture type and range (10 to 20° in steps of 2): 72 files [wiring]. StickR is not exported on GripV. GripX exports StickL in its five presets and StickR as `normal` × 3 curvatures plus the three other presets [wiring].
