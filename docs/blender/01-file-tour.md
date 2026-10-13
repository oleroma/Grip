# 1. File tour: what is inside `Grip.blend`

This page is the map: scenes, collections, objects and the other data blocks in `blender/Grip.blend`, and what each one is for. Everything here was read from a copy of the file in headless Blender 5.2.0 LTS; nothing was saved back.

Tags used on all pages: **[measured]** means I changed or evaluated the model on a copy and observed it, **[wiring]** means read directly from node links and stored values (deterministic, but not executed), **[inferred]** means an interpretation of intent that I could not prove.

## 1.1 Basic facts

| Item | Value |
|---|---|
| Saved with | Blender 5.2 (file version 5.2.44) [wiring] |
| Units | Metric, unit scale 0.001, length unit millimetres. One Blender unit is one millimetre, so exported STL coordinates are millimetres [wiring] |
| Scenes | `GripV`, `GripX`, `source` [wiring] |
| Workspaces | `GripV`, `GripX`, `source`, each pinned to the scene of the same name; the file opens on `GripV` [wiring] |
| Objects | 298 (206 meshes, 45 curves, 41 empties, 4 lights, 2 cameras) [wiring] |
| Node groups | 511, all Geometry Nodes; 64 are used directly by modifiers, 437 are reachable from the objects in the `GripV`/`GripX` scenes [wiring] |
| Collections | 190 [wiring] |
| Materials | 15 (`case`, `button`, `button smd`, `stick`, `stick smd`, `trigger`, `scroll`, `led`, `pcb` and a few spare ones); they only matter for rendering [wiring] |
| Fonts | 11, all loaded from Windows system font paths (`C:\Windows\Fonts\…` or a relative path that climbs to it) [wiring] |
| Text blocks | `Auto sync workspaces` (embedded) and `rename.py` (points at `//..\scripts\rename.py`) [wiring] |

## 1.2 The three scenes

The three scenes share their collections: a collection such as `parts` is one data block linked into several scenes, so editing a part in one scene edits it everywhere [wiring].

**`GripV`** (68 objects, all meshes) holds what is exported for the GripV shape: the GripV basemesh, the case top and bottom, the case middle plate, and all the parts. **`GripX`** (69 objects) is the same set with the two GripX basemeshes (`basemesh_X_style`, `basemesh_D_style`) instead of the GripV one, `reinforcers` instead of the middle plate [wiring].

| In GripV only | In GripX only |
|---|---|
| `basemesh GripV`, `case_middle_plate` | `basemesh_X_style`, `basemesh_D_style`, `reinforcers` |

**`source`** (298 objects) is the workshop: every object in the file, including 227 that appear in no other scene. These are the building blocks the node trees read through *Object Info* and *Collection Info* nodes (cutter shapes, hand-modelled meshes, empties used as placement markers, logo curves), plus older variants (`basemesh GripR1`, `basemesh GripS`), work in progress, tests, render setups and an archive [wiring]. Its view layers are `whole`, `case`, `parts top` and `parts bottom`, each excluding a different part of the tree [wiring].

### View layers and what gets evaluated

`GripV` and `GripX` each have one view layer, `whole`. In both, the basemesh collections and `references` are **excluded**; the basemesh is still evaluated because the case pulls it in through *Collection Info* [measured: the case changes when the basemesh subdivision changes]. In `GripV`, the `case middle plate` collection is **excluded** too, which matters for export (see [Export](08-export-and-tracking.md) and [Issues](09-issues.md)) [wiring].

In the saved file, most part objects of `GripV` are hidden with the eye icon in the viewport; nothing is eye-hidden in `GripX`. The eye only affects the viewport: the exporter un-hides eye-hidden objects while it writes them [wiring, from `combi_export/stl.py`].

## 1.3 Collection layout (GripV and GripX scenes)

```
basemesh GripV                      (GripV)  basemesh GripV            ← excluded in the view layer
basemesh GripX                      (GripX)  ├ basemesh xbox style     ← basemesh_X_style
                                             └ basemesh dualsense style ← basemesh_D_style (render-hidden)
case middle plate                   (GripV)  case_middle_plate         ← excluded in the view layer
case                                         ├ case top     ← case_top
                                             └ case bottom  ← case_bottom
parts
├ caps      ├ home cap   ← home cap
│           ├ abxy caps  ← abxy cap up / down / left / right
│           ├ select caps← select cap top left / top right / down left / down right
│           └ dpad caps  ← dpad cap up / down / left / right
├ buttons   ├ home ← home button   ├ abxy ← abxy button   ├ select ← select button   └ dpad ← dpad button
├ triggers      ← L2, R2, L4, R4
├ bumpers       ← L1, R1
├ capacitive    ← capacitive
├ dpad stick    ← rocker ball, rocker support, rocker, stick, dpad stick cap, ball support
├ sticks        ← StickL, StickR
├ scrollwheel   ← scrollwheel, scrollwheel core, scrollwheel holder
├ battery cover ← battery cover
├ cable holder  ← cable holder
├ pins          ← pin
└ nut lock      ← nut lock
reinforcers                         (GripX)  reinforcers
references   (excluded)  other (reference controllers, PCB scans), marmota, board (PCB + SMD parts), screws DIN912
```

Only one button object of each kind exists (`abxy button`, `dpad button`, …): it is the shared switch shaft for its group of caps. The caps are separate objects, one per position [wiring].

## 1.4 The printable objects and their modifier inputs

Each printable object carries one Geometry Nodes modifier (some add a Bevel modifier or a second Geometry Nodes modifier). The modifier inputs that differ per object are listed here; every other dimension comes from the parameter system described in [2. Parameter system](02-parameter-system.md) [wiring].

| Object(s) | Modifier group | Per-object inputs |
|---|---|---|
| `case_top`, `case_bottom` | `case` | `case part` = top / bottom |
| `case_middle_plate` | `middle plate` | none |
| `abxy button`, `abxy cap up/down/left/right` | `abxy button` (+ `logo`) | `button` (always on), `cap` (on for caps), `Collection` = which `abxy cap curve …` collection; `logo`: depth, bump, type (text or custom curves), logo collection |
| `dpad button`, `dpad cap …` | `dpad button` (+ `logo` on the button, disabled in the viewport) | same pattern |
| `select button`, `select cap …` | `select button` (+ `logo` on the button) | same pattern |
| `home button`, `home cap` | `home button` (+ `logo`) | same pattern; also two menu inputs `tolerance` and `cap tolerance` that are not connected to anything |
| `L2`, `R2`, `L4`, `R4` | `trigger` | `part` = R2 or R4, `button` = on, `SMD button` = the PCB switch object, `left` = mirror to the left side |
| `L1`, `R1` | `lever R1L1` (+ Bevel `r1 front bevel`) | `marks` = on, `left` |
| `capacitive` | `capacitive plate` | `plate` = on |
| `rocker ball`, `rocker support`, `rocker`, `stick`, `dpad stick cap`, `ball support` | `dpad stick` | `Menu` = which piece, `bool` = off |
| `StickL`, `StickR` | `stick module` → 2 Bevel → `top module` → `extra` | `Menu` = `stick L` / `stick R`, `hole` = off |
| `scrollwheel`, `scrollwheel core` | `scrollwheel`, `scrollwheel stem` | none |
| `scrollwheel holder` | a Geometry Nodes modifier with **no node group** (passes its plain mesh through) | none |
| `battery cover` | `cover` | `bool` = off |
| `cable holder` | `MirrorX` → `cable hole` | none |
| `pin` | `pins` + 4 Bevel modifiers | `bool` = off |
| `nut lock`, `reinforcers` | `screws` | `nut lock` / `reinforcer` flags |
| basemeshes | `MirrorX` → `subdivision surface` (GripV) or `subd` (GripX) | none |

The same modifier groups are reused on the **cutter objects** in the `source` scene, with the flags flipped (`button` off, `bool` on, `hole` on, `plate` off). The case subtracts those cutters, so a part and the hole it sits in are generated from the same numbers [wiring]. See [5. Case](05-case.md).

### Baseline sizes as saved

Measured on a copy with the saved settings (variant switched to match the scene, everything else untouched) [measured]. Sizes are bounding-box dimensions in millimetres, volume in mm³.

| Object | GripV size (X × Y × Z) | GripV volume | GripX size (xbox style) | GripX volume |
|---|---|---|---|---|
| basemesh | 165.80 × 86.46 × 74.31 | 432,220 | 175.47 × 99.45 × 54.33 | 393,923 |
| case_top | 162.38 × 77.60 × 19.04 | 130,394 | 168.23 × 88.63 × 18.00 | 125,979 |
| case_bottom | 165.80 × 86.46 × 55.27 | 180,761 | 175.47 × 99.24 × 36.33 | 153,843 |
| abxy button | 6.48 × 7.68 × 16.56 | 634 | 6.84 × 8.84 × 15.32 | 671 |
| abxy cap (each) | 11.40 × 11.40 × 2.72 | ≈181 | 11.00 × 11.00 × 3.04 | ≈160 |
| dpad cap (each) | 8.44 × 11.89 × 2.72 | 144 | 8.64 × 12.34 × 3.04 | 173 |
| select cap (each) | 8.96 × 8.96 × 2.72 | 111 | 9.10 × 9.10 × 3.04 | 124 |
| home cap | 10.92 × 11.69 × 2.72 | 175 | 9.57 × 10.32 × 3.04 | 133 |
| L2 / R2 | 23.01 × 18.39 × 21.94 | 2,913 | 8.98 × 26.45 × 18.18 | 2,497 |
| L4 / R4 | 23.99 × 27.29 × 33.64 | 4,739 | 17.98 × 12.34 × 16.38 | 1,891 |
| L1 / R1 | 46.53 × 11.54 × 12.32 | 1,870 | 29.90 × 13.14 × 14.00 | 2,416 |
| StickL | 20.74 × 20.74 × 14.24 | 1,123 | 22.01 × 22.01 × 15.95 | 2,066 |
| StickR | 20.74 × 20.74 × 16.22 | 1,290 | 20.26 × 20.26 × 12.64 | 858 |
| capacitive | 11.40 × 11.40 × 17.14 (knob) | 1,030 | 37.60 × 37.60 × 15.00 (plate) | 1,678 |
| battery cover | 39.40 × 63.15 × 4.57 | 2,969 | 38.05 × 62.70 × 4.60 | 3,900 |
| cable holder | 22.70 × 16.44 × 11.00 | 1,425 | 22.70 × 16.44 × 11.00 | 1,939 |
| pin | 3.90 × 3.90 × 7.50 | 103 | 3.90 × 3.90 × 7.50 | 103 |

As saved, the six dpad-stick pieces are **empty** (0 vertices) in both scenes because the dpad stick is switched off, and `case_middle_plate` (GripV) is empty because its collection is excluded from the view layer, so it is never evaluated; with the collection included it is a 156.1 × 71.0 × 10.8 mm plate of 8,483 mm³ for every body type [measured]. The full table with vertex counts and positions is in [reference/measurements.md](reference/measurements.md).

## 1.5 Text blocks

**`Auto sync workspaces`** is a small script that, once run, listens for workspace changes and sets the `variant` input of the `global parameters` node (inside the `global` node group) to `GripX` or `GripV` to match the workspace name [wiring]. It is not registered as a module (`use_module` is off), so it does nothing until someone runs it in the session [wiring]. The scenes also store settings of an add-on called `w2g` that maps workspaces `GripV`, `GripX` and `Project` to values of the same `variant` input [wiring]; that add-on is not in this repository [inferred: it is the installed replacement for the script].

**`rename.py`** renames every group node to the name of its node group. It is an external text pointing at `scripts/rename.py` in the repository [wiring].

## 1.6 Add-on data stored in the file

| Stored on | Property prefix | Add-on | Notes |
|---|---|---|---|
| `GripV`, `GripX` scenes | `batch_stl_*` | `combi_export` (in `extensions/`) | 6 export presets per scene; identical to `blender/GripV_preset.json` and `blender/GripX_preset.json` apart from fields left at their defaults [measured by comparison] |
| `source` scene | `geonodes_json_exporter_*` | `blender_tracking` (in `extensions/`) | tracks `GripV controls`, `GripX contols` (depth 1, groups only) and the `basemesh` collection; writes `blender/tracking.json` on save |
| all scenes | `w2g_*` | not in the repo | workspace → `variant` mapping (see 1.5) |
| all scenes | `renaming_*`, `mcr`, `NW*`, `mmu_paint`, `cycles` | other add-ons (a renamer, Node Wrangler, a paint tool) | no effect on geometry |

`blender/tracking.json` matches the current file: all 1,881 tracked input values agree with the node values in the file [measured by comparison].

## 1.7 Where to look next

- How the numbers reach the geometry: [2. Parameter system](02-parameter-system.md)
- The top-level switches: [3. Global switches](03-global-switches.md)
- GripV, GripX, styles: [4. Variants and styles](04-variants-and-styles.md)
- Changing things: [10. Editing guide](10-editing.md)
- Everything that looks wrong: [9. Issues](09-issues.md)
- The full index: [README](README.md)
