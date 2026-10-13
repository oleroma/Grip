# 10. Editing guide: how to change things safely

This page turns the rest of the documentation into recipes. It assumes you have read [2. Parameter system](02-parameter-system.md) once. Tags as elsewhere: **[measured]**, **[wiring]**, **[inferred]**.

## 10.1 Before you change anything

1. **Match the variant to the scene.** The global `variant` is one value for the whole file; the `GripV` and `GripX` scenes do not set it ([4.2](04-variants-and-styles.md#42-how-the-variant-is-chosen)). After opening the file, either run the `Auto sync workspaces` text once (Text Editor › Run Script), use the `w2g` add-on if you have it, or set `variant` by hand in `global` › `global parameters`. Otherwise the GripX scene shows GripX objects built from GripV numbers [wiring].
2. **Keep evaluation fast while editing.** Leave `subdivision level` on `low` and `voxel resolution` on `low`, and keep `body type` on `standard` unless you are working on shells. Shell bodies took 7 to 12 s per evaluation at low voxels on a desktop PC, several times more at high [measured]. The export presets switch both settings to their high values on their own [wiring].
3. **Know what gets saved with the file.** Saving writes `blender/tracking.json` through the `blender_tracking` add-on (if it is installed and enabled). That file is the diffable record of every preset value, so review its diff before committing ([8.4](08-export-and-tracking.md#84-tracking-blender_tracking-and-trackingjson)).

## 10.2 Finding the value that controls something

Work from the controls panel, not from the part's modifier:

1. Open the node group `GripV controls` or `GripX contols` (one way in: the object `case_front.002` carries a modifier with the group `controls`, which holds all panels). The panel has frames per area: BUTTONS, STICKS, R2R4, R1L1 LEVER, SCREWS, PINS, PCB AND BATTERY, SCROLLWHEEL, DPAD STICK, pattern, shell [wiring].
2. Tab into the preset group in the right frame (for example `GripV abxy`).
3. Change the value on the constructor node inside it (`button parameters`, `caps parameters`, …). Editing a group node anywhere edits the one shared group, so the panel and the part see the same data [wiring].

Then check three things, because each one makes an edit silently do nothing:

| Check | Why | Examples in the file |
|---|---|---|
| Is the input **linked**? | A linked input ignores the number typed on it. Edit the node it comes from. | every `… tolerance` that comes from a `tolerance set`; GripV bumper `stem radius` comes from a *Value* node (2) while the input itself still shows 3 [wiring] |
| Is the node **live**? | Some presets keep alternative nodes that are not connected to the output. | GripV trigger node in frame "SNES"; GripX cover nodes in frame "battery"; the GripX bumper tolerance set; a sixth GripX StickL set (all [wiring]) |
| Is it the node the **current menu** picks? | GripX keeps two nodes per part for the two styles, and several presets per stick behind a *Menu Switch*. | frames "GripX" (xbox) and "GripD" (dualsense) in the GripX trigger, bumper and screw presets; `stick menu` in `GripX stick L parameters` |

The preset tables ([GripV](reference/preset-values-GripV.md), [GripX](reference/preset-values-GripX.md)) mark disconnected nodes with "(not connected)" and show where each linked input comes from.

## 10.3 Where is the value for…?

All paths are *preset group › constructor node › input*; `…` stands for the variant prefix (`GripV` or `GripX`), and the same input exists in both variants.

| I want to change | Edit | Page |
|---|---|---|
| how tight every button shaft fits in the case | global `tolerance`, or the `tolerance set` values in `GripV abxy` / `dpad` / `select` / `home` | [7](07-tolerances.md) |
| cap size or the gap around a cap | `… abxy` › `caps parameters` › `cap case tolerance` (gap per side), `caps additional size` | [Buttons](parts/buttons-and-caps.md) |
| button outline width | `… abxy` › `curve parameters` › `width` (also resizes the case hole) | [Buttons](parts/buttons-and-caps.md) |
| button height above the case | `… abxy` › `button parameters` › `button height` | [Buttons](parts/buttons-and-caps.md) |
| thumbstick height, top radius, shape | `… stick L/R parameters` › `basic stick parameters` › `stick heght`, `stick top radius`; `stick top parameters` › `top shape`, `top curvature` | [Sticks](parts/sticks.md) |
| stick tilt range | `basic stick parameters` › `range degrees` and `advanced stick parameters` › `contact angle` | [Sticks](parts/sticks.md) |
| trigger length, arc, angle | `… R2/R4 parameters` › `trigger parameters` › `trigger length`, `trigger radius`, `button rotation` | [Triggers](parts/triggers.md) |
| bumper width, height, position | `… lever R1L1` › `R1L1 lever parameters` › `wdith`, `height`, `X`/`Y`/`Z` | [Bumpers](parts/bumpers.md) |
| bumper press fit (GripV) | global `press tolerance`, or the `tolerance set` in `GripV  lever R1L1` | [Bumpers](parts/bumpers.md) |
| battery size | `… cover parameters` › `advanced cover parameters` › `battery length` / `width` / `height` | [Battery cover](parts/battery-cover.md) |
| battery cover fit | `basic cover parameters` › `x tolerance`, `y tolerance` | [Battery cover](parts/battery-cover.md) |
| screw and nut sizes | `… screw paramters` › `screw parameters` (FRONT) and the BACK node: `screw parameters.001` in GripV; in GripX `screw parameters.002` (xbox) and `screw parameters.001` (dualsense) | [Screws](parts/screws.md) |
| screw positions | `… screw paramters` › `screw position` (FRONT) and the BACK node, numbered like the sizes (`.001`, or `.002` for GripX xbox) › `position`, `rotation` | [Screws](parts/screws.md) |
| alignment pin size and fit | `… pins parameters` › `pins params` › `pin width`, `pin height`, `xy tol`, `z tol` | [Pins](parts/pins.md) |
| scroll wheel size and fit | `… scrollwheel` › `scroll parameters` | [Scroll wheel](parts/scroll-wheel.md) |
| PCB slot size | `… pcb cutout paramters` › `pcb cutout parameters` | [PCB and cable](parts/pcb-and-cable.md) |
| USB cable size for the cable holder | `cable holder parameters` › node `cable size.001` ("pwnage paracord") | [PCB and cable](parts/pcb-and-cable.md) |
| shell wall thickness (hollow, lattice) | `… hollow parameters` › `shell thickness` | [6.5](06-body-types.md#65-hollow-the-sdf-shell) |
| middle plate fit (shell bodies) | `… middle plate parameters` | [6.7](06-body-types.md#67-the-middle-plate-and-the-ledge) |
| indent pattern depth and scale | the indent preset for the current `fill type` › `fill parameters.001` › `fill depth`, `scale`, `thickness` | [6.4](06-body-types.md#64-indent-a-pattern-pressed-into-the-surface) |
| the outer shape of the controller | the basemesh object (`basemesh GripV`, `basemesh_X_style`, `basemesh_D_style`); edit it in Edit Mode, it is a half model mirrored by `MirrorX` | [5.1](05-case.md#51-from-basemesh-to-two-halves) |

## 10.4 Recipes

### Change a fit and keep the hole in step

Parts and their case holes are generated from the same preset: the cutter objects in the `source` scene carry the same modifier group with `button`/`bool`/`hole` flipped [wiring]. So changing, say, `curve parameters` › `width` in `GripV abxy` resizes the shaft, the caps and the four holes in the case top together [measured: +1.2 → shaft and caps 1.2 wider, case top −1,407 mm³]. You never edit the cutters by hand. The exceptions are the fixed cutter meshes listed in [5.2](05-case.md#52-what-is-cut-out-and-from-where) (stick cutouts on GripV, wire channels, SMD clearances, stock bumper cutouts): they do not follow any parameter.

### Try a value before committing to it

1. Note the current value (or rely on `tracking.json` to show it in the diff).
2. Change it and look at the part and at `case_top` / `case_bottom`, since most part inputs also move a cutter.
3. For shells, switch `body type` to `hollow` or `lattice` only after the solid version looks right.

### Make a new named variant of a part (GripX pattern)

GripX keeps several stick presets in one group behind a *Menu Switch* [wiring]. To add one:

1. In `GripX stick L parameters`, copy one frame of constructor nodes (the six constructors plus their *Join Bundle*).
2. Add an item to the *Menu Switch* and connect the new *Join Bundle* to it.
3. Pick it with the `stick menu` node, or add it to the export preset (the preset overrides the *Menu Switch* directly).

### Add a value that a part can read

1. Add an input to the constructor group (for example `trigger parameters`) and connect it to the *Combine Bundle*. The key name is the item name on the *Combine Bundle*.
2. Add the same name to the *Separate Bundle* in the matching `… outputs` group (for example `trigger outputs`) and expose it as an output.
3. Use the new output in the geometry group.
4. Type the value in every preset that uses the constructor (both variants, and both GripX style nodes where they exist), because a new input starts at its interface default.

Keys are matched by name. A key that the bundle does not carry comes out of the *Separate Bundle* as the socket's default (zero, off or empty), so a typo in a key name does not stop the evaluation [inferred from how Blender bundles behave; this is how the two missing keys in [Issues](09-issues.md) go unnoticed]. The list of existing keys and renamed keys is in [reference/parameter-groups.md](reference/parameter-groups.md).

### Move a part

| Part | Where its position comes from |
|---|---|
| buttons, caps, sticks, scroll wheel, the triggers' PCB switch objects | the object's own location and rotation, and the matching cutter object in `source` (move both) [wiring] |
| triggers | placed on the PCB switch objects `R2_pcb_button` / `R4_pcb_button`, plus `shift z`, `button radius offset`, `x offset`, `button rotation` [wiring] |
| bumpers | `R1L1 lever parameters` › `X`, `Y`, `Z` (both bumpers and their cutter); `Y` moves only the back of the bumper, the front stays at the case [measured] |
| alignment pins | `pins postion` › `X`, `Y`, `Z` [measured] |
| screws | `screw position` (FRONT) and the BACK `screw position` node › `position`, `rotation`; mirrored to the other side automatically [wiring, measured] |
| battery compartment and cover | `advanced cover parameters` › `shift Y` [measured] |

### Export after a change

Use the `combi_export` presets on each scene. Things to check first ([8](08-export-and-tracking.md)):

- The export root is an absolute Windows path (`D:\Grip\orca_slicer\…`); on another machine change it in the preset.
- The `case middle plate` collection is excluded in the GripV view layer, so "Case hollow" skips the plate unless you include it.
- Six part files on disk use spaces where the current add-on writes underscores; the first export creates duplicates.

### Verify a change from the command line

The measurements in these pages were made with a headless script that evaluates a scene and reads every object's mesh (vertex count, bounding box, volume, non-manifold edges). The same approach works as a regression check after an edit: evaluate before and after and compare. See [11. Method](11-method.md). A whole GripV or GripX scene evaluates in about 2 s with the saved settings on a 4-core machine [measured].

## 10.5 Pitfalls

- **Disappearing case half.** If `case_top` or `case_bottom` suddenly evaluates empty after a part change, a cutter is probably not closed and the *Manifold* boolean failed. It happened with GripX R4 `shift z` = 4.62 in Blender 5.2.0, though not in 5.2.2 [measured]. Nudge the value. See [Issues](09-issues.md) B1.
- **`horizontal buttons` off is unstable.** Unrelated button edits make the ABXY and D-pad parts jump between two shapes [measured]. Keep it on unless you are working on that design.
- **`fill type` = manual** empties the case top [measured].
- **The split height 40 mm is hard-coded in five groups** (`cut basemesh`, `plate`, `offset basemesh and slice`, `insert rim`, `pattern field`) and a constant 40 also sits in `screw` [wiring; that it is the same split height is inferred]. Change all of them together or not at all.
- **Typos are names, not bugs.** `wdith`, `heght`, `stiick`, `sheild`, `paramters`, `contols` and others are the real socket and group names; search for them as spelled. Renaming is safe for links and modifier values (they use identifiers), but `tracking.json` keys and anything that refers to names as text change with them.
- **Shared groups.** Values typed on a constructor node belong to that preset, but whatever sits *inside* a constructor group is shared by every preset that uses it. The export presets rely on that: they override the *Menu Switch* inside `capacitive plate parameters` and the *Combine Bundle* inside `dpad stick parameters`, which switches both variants at once [wiring]. `cable holder parameters` has no inputs at all, so its cable size is one value for every variant [wiring].
