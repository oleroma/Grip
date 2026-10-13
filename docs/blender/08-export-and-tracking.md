# 8. Export and tracking

How the STL files in `orca_slicer/` are produced from `Grip.blend`, and what `blender/tracking.json` records.

## 8.1 The exporter: `combi_export`

The `combi_export` extension (folder `extensions/combi_export/`, synced from its own repository) stores **export presets** on each scene and writes binary STL files [wiring, from the add-on source]. Each preset lists collections; each collection lists its objects (with an *export* tick, an optional output name, sub-folder and filename tag); and at four levels (global, preset, collection, object) it can hold **overrides**: values for node inputs or modifier inputs that are applied only while that preset exports.

What one export does [wiring, `export_operator.py`, `headless.py`, `stl.py`]:

1. Objects that have no overrides are written directly by the running Blender.
2. For objects with overrides, the add-on saves a temporary copy of the file and starts a second, headless Blender on it (`--factory-startup`, with auto-run scripts on only if your preferences allow it).
3. The worker enumerates every **combination** of override values. A value list gives one file per value; a *sweep* turns a menu into all its items, a boolean into True and False, a number into start/step/count.
4. For each combination it writes the values into the node sockets. If a socket is linked, the link is **removed** first and restored afterwards; this is how the presets can force `dpad stick` or the capacitive menu inside shared groups such as `dpad stick parameters` [wiring].
5. It updates the view layer, takes each object's evaluated mesh in world space, and writes it as binary STL. Coordinates are Blender units, which in this file are millimetres [wiring].
6. Collections that are excluded or disabled in the view layer are skipped without an error; objects hidden with the eye are briefly un-hidden [wiring, `targets.py` `live_collection_names`, `stl.py` `eye_unhidden`].

**Naming** [wiring, `naming.py`]: folder = preset prefix / collection sub-folder / object sub-folder / one folder per override value that has its folder template on; file = object name (or its output-name override) followed by `_tag` for every override value whose tag template is on. `*` in a template is replaced by the value. Spaces in names become underscores.

## 8.2 The presets stored in the file

Export root: `D:\Grip\orca_slicer\GripV\` for the `GripV` scene and `D:\Grip\orca_slicer\GripX\` for `GripX` (absolute paths) [wiring]. Global override for each scene: `variant` = the scene name [wiring]. The presets below are exactly those in `blender/GripV_preset.json` and `blender/GripX_preset.json` [measured by comparison].

### GripV scene

| Preset | What it exports | Overrides | Files |
|---|---|---|---|
| **Case standard** → `case_standard/` | `case_top`, `case_bottom` | preset: body type `standard`, subdivision `very high`, voxel resolution `high`; on `case_top` only: **`hollow top` on**, `dpad stick` on/off (tag `dpad_stick`), capacitive `plate`/`knob` (tag `cap_*`) | `case_bottom.stl` and 4 tops: `case_top[_dpad_stick]_cap_{plate,knob}.stl` |
| **Case hollow** → `case_hollow/` | `case_top`, `case_bottom` (+ `case_middle_plate`, see below) | subdivision `very high`; on the collection: body type `hollow`, voxel `high`; tops as above | same 5 names |
| **Parts** → `parts/…` | capacitive, bumpers, dpad stick (6 pieces), battery cover, cable holder, pin | capacitive `plate`/`knob` through **`GripV abxy`** (tag); bumpers: `press tolerance` swept, folder `press_*`; dpad stick forced on | 17 files |
| **Sticks** → `parts/sticks/` | `StickL` named `stick` (`StickR` not exported) | `GripV stick L parameters`: top shape, top curvature, texture type all swept (folders), `range degrees` swept 10 → 20 step 2 (tag `*_deg`) | 72 files: `{circle,square}/{concave,convex,flat}/{grid,icosahedron}/stick_{10…20}_deg.stl` |
| **Buttons** → `parts/buttons/` | `abxy button` named `button`; one cap of each shape: `abxy cap left` = square, `abxy cap down` = cross, `abxy cap right` = circle, `abxy cap up` = triangle, `dpad cap right` = dpad, `select cap down right` = select, `home cap` = home | button: `tolerance` swept (folder); caps: `tolerance` swept (folder) × `cap tolerance` swept (folder `cap_*`) | 66 files |
| **Triggers** → `parts/triggers/` | `L2`, `R2`, `L4`, `R4` | `tolerance` × `press tolerance` swept (folders `*` / `press_*`) | 36 files |

### GripX scene

| Preset | What it exports | Overrides | Files |
|---|---|---|---|
| **Case standard** | `case_top`, `case_bottom` | as GripV but without `hollow top`, plus `style` = dualsense / xbox (folder `*_style`) | 10: `{xbox,dualsense}_style/case_…` |
| **Parts** | capacitive, dpad stick, battery cover, cable holder, pin | capacitive through **`GripV abxy`** (see issue below) | 11 |
| **Buttons** | as GripV | as GripV | 66 |
| **Sticks** | `StickL`, `StickR` (sub-folders `StickL`, `StickR`) | `GripX stick L parameters` → *Menu Switch*: 5 named presets (tags); `GripX stick R parameters` → *Menu Switch*: `normal` (folder) × top curvature swept, plus `small round`, `small square`, `8 dir` | 11 |
| **Triggers** | `L2`, `R2`, `L4`, `R4` | style folder × `tolerance` × `press tolerance` | 72 |
| **Bumpers** | `L1`, `R1` | style folder × `press tolerance` (folder `pres_*`, spelled differently from GripV's `press_*`) | 12 |

### Verified against the repository

A dry run of all presets with the add-on's own code (no files written) produced 201 paths for GripV and 182 for GripX, and every one of them exists in `orca_slicer/` except six per scene that differ only by spaces versus underscores: the files on disk are called `battery cover.stl`, `cable holder.stl`, `ball support.stl`, `dpad stick cap.stl`, `rocker ball.stl`, `rocker support.stl`, while the current add-on writes `battery_cover.stl` and so on [measured]. So those six were written by an older add-on version, and the next export will add underscore copies next to them.

Comparing file contents (MD5) of the committed STLs [measured]:

| Identical files | Why |
|---|---|
| GripX `capacitive_knob.stl` = `capacitive_plate.stl` | the GripX preset switches the capacitive part through `GripV abxy`, which GripX never reads |
| GripX bumpers `pres_tight` = `pres_default` = `pres_loose` (both styles) | `press tolerance` does not reach the GripX bumpers (see [Bumpers](parts/bumpers.md)) |
| GripX caps `cap_tight` = `cap_default` = `cap_loose` | GripX uses −0.16 for all three cap tolerances |
| GripX triggers `default/*` = `loose/*` | the GripX trigger `tolerance` set has the same value for default and loose (see [Tolerances](07-tolerances.md)) |
| `rocker`, `rocker ball`, `rocker support`, `ball support` identical between GripV and GripX | both variants use the same dpad stick numbers for those pieces |

All export problems are collected in [9. Issues](09-issues.md#a-exports).

### Things the presets do that are easy to miss

- **GripV "Case standard" exports a hollow top.** The object-level override `hollow top = on` on `case_top` means the released `case_standard/case_top_*.stl` are shell tops, while `case_bottom.stl` is solid [wiring]. On a copy, `hollow top` on cut the case top volume from 130,394 to 34,161 mm³ at the saved settings [measured].
- **"Case hollow" skips the middle plate.** The preset lists the `case middle plate` collection, but the `GripV` view layer excludes that collection, so the exporter silently leaves it out; the dry run confirms it, and `orca_slicer/GripV/case_hollow/` has no middle plate STL [measured]. `GripV_case_hollow.3mf` does contain a `case_middle_plate` object from an earlier export [measured, read from the 3MF].
- Not exported by any preset: `StickR` (GripV), `scrollwheel`, `scrollwheel core`, `scrollwheel holder`, `nut lock`, `reinforcers`, `case_middle_plate`, and the extra caps (only one cap per shape) [wiring].

## 8.3 OrcaSlicer projects

`orca_slicer/GripV/*.3mf` and `orca_slicer/dongle_case/*.3mf` are OrcaSlicer projects for a Bambu Lab A1 with a 0.4 mm nozzle at 0.16 mm layers (profile "0.16mm High Quality @BBL A1"), outer brim, elephant-foot compensation 0.075, supports on for the cases [measured, read from `Metadata/project_settings.config`]. Wall loops: 2 for `case_standard` and parts, 3 for `case_hollow` and `case_za3tarani`. They reference objects by STL name, including some that no current preset exports (`nut_lock`, `scrollwheel*`, `case_middle_plate`) [measured].

## 8.4 Tracking: `blender_tracking` and `tracking.json`

`blender_tracking` (folder `extensions/blender_tracking/`) writes `blender/tracking.json` every time the file is saved, if tracking is enabled on the scene [wiring]. Its settings live on the `source` scene: it tracks the node groups `GripV controls` and `GripX contols` to depth 1 (group nodes only) and the collection `basemesh` [wiring]. The JSON holds:

- `tracked_inputs`: every input value of the preset groups placed in the two controls panels, nested one level deep;
- `modifiers`: modifier inputs of objects that use those trees (empty here, no object uses them);
- `meshes`: an MD5 hash per basemesh object of its world transform, vertex positions and topology;
- `all_node_trees`: the link list of all 511 node groups.

Its purpose is a git-diffable record of parameter changes. All 1,881 values in the current `tracking.json` match the file [measured].
