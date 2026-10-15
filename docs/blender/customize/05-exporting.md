# 5. Exporting

Parts are exported with the `combi_export` extension, from presets stored in each scene. A preset knows which objects to export, which settings to override while exporting (variant, smoothness, tolerances, styles, options) and how to name the files. One click can write a whole family of variants, such as every button at every tolerance.

## How to export

1. Switch to the `GripV` or `GripX` scene.
2. Open the `combi_export` panel and pick a preset.
3. **Check the export folder.** The presets point at `D:\Grip\orca_slicer\GripV\` and `D:\Grip\orca_slicer\GripX\`. On another machine, change the root to your own `orca_slicer` folder first.
4. Export. Objects with overrides are written by a second, headless Blender in the background, so the export takes a while for the case presets.

You do not need to set `variant`, the subdivision level or the voxel resolution yourself. The presets set them for the export only; your open file is not changed.

## What each preset writes

| Preset | GripV | GripX |
|---|---|---|
| **Case standard** | `case_top` and `case_bottom`, smooth (subdivision very high). The top comes with the D-pad stick opening or the D-pad caps, and with the capacitive plate or the knob opening (4 tops). The GripV top is a shell (`hollow top`). | the same for both styles, in `xbox_style/` and `dualsense_style/` |
| **Case hollow** | the shell case at high voxel resolution, tops as above | — |
| **Parts** | capacitive (plate and knob), bumpers (at each press tolerance), the six D-pad stick pieces, battery cover, cable holder, pin | capacitive, D-pad stick, battery cover, cable holder, pin |
| **Sticks** | the left stick in every combination of top shape, curvature, texture and tilt range (10 to 20°) | both sticks in their named presets |
| **Buttons** | the ABXY shaft at each `tolerance`, and one cap of each shape at each `tolerance` × `cap tolerance` | the same |
| **Triggers** | L2, R2, L4, R4 at each `tolerance` × `press tolerance` | the same, per style |
| **Bumpers** | (in "Parts") | L1, R1 per style at each `press tolerance` |

Folder and file names come from the preset. A tolerance gets a folder (`tight/`, `press_loose/`, `cap_default/`), and an option gets a tag in the file name (`_dpad_stick`, `_cap_plate`, `_14_deg`). Which of the exported files make up one controller is in the [print list](../../../orca_slicer/README.md).

## Changing a preset

Each preset lists collections and objects, and overrides at four levels (whole scene, preset, collection, object). An override sets a node input or modifier input while that preset exports. It can be a fixed value, a list (one file per value) or a sweep (every menu item, both boolean states, or a number range). To export a part you added, add its collection to a preset. To add a tolerance sweep, add an override on the matching global menu. The presets are also saved as `blender/GripV_preset.json` and `blender/GripX_preset.json`.

## Not exported by any preset

`StickR` on GripV, the scroll wheel parts and `nut lock` on GripX (GripV writes them to `parts/scrollwheel/` and `parts/misc/`), `reinforcers` (GripX) and `case_middle_plate`. Of the caps, the four ABXY caps (one per symbol), one D-pad cap, one Select cap and the Home cap are exported; the four D-pad caps share one outline turned four ways. Add objects to a preset if you need them.

## Known problems

| Problem | Effect | What to do |
|---|---|---|
| The GripV view layer excludes the `case middle plate` collection | "Case hollow" silently skips the middle plate | include the collection in the view layer before exporting |
| The GripX `capacitive_knob.stl` in `orca_slicer/` was exported before the preset was fixed | it is really the plate | re-run the GripX "Parts" preset |
| The GripX bumpers do not read `press tolerance` | the three GripX `pres_*` bumper folders are identical | see [Bumpers](parts/bumpers.md) |
| GripX caps have one cap tolerance for all three settings | the three GripX `cap_*` folders are identical | give tight and loose their own values |
| GripX triggers: `default` = `loose` | two identical folders | give loose its own value |
| The GripX bumpers use `pres_*` folders; the GripV bumpers and all triggers use `press_*` | two spellings for the same setting | pick one |
| Text marks need the Windows font Segoe UI Bold | exports on macOS/Linux have no letters | see [Marks](parts/marks-and-logos.md) |
