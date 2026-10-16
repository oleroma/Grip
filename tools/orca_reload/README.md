# Orca reload

Updates the meshes inside OrcaSlicer project files (`.3mf`) from the STL files on disk: every part, in every project you give it, in one run. It gives the same result as Orca's **Reload from disk**, without opening Orca, and it tells you which parts changed.

It keeps:

- each object's orientation (rotation) and its place on its plate
- copies (instances), plates, plate names and the arrangement
- per-object and per-part settings, filaments and print settings

It changes:

- the mesh of every part whose STL changed
- the object's height, so it still sits on the bed (Orca does the same after a reload)
- the source offset Orca stores for the part, so a later reload lines up

The original project is never overwritten. The result is written next to it as `NAME_reloaded.3mf`.

> Inside Orca, right-clicking a plate and choosing **Reload All** reloads every part of the open project. This tool is for doing many projects at once, or without opening Orca.

In Blender, the [Orca Reload extension](../../extensions/orca_reload/README.md) goes further: it builds whole projects from plates and parts set up in Blender, nests the parts and paints seams drawn as curves. This command only reloads; its code lives in that extension (`extensions/orca_reload/reload3mf.py`) and runs here without Blender.

## Use

You need Python 3.8 or newer, with no extra packages. If Python is not installed on Windows, Blender's own Python works:
`"C:\Program Files\Blender Foundation\Blender 5.2\5.2\python\bin\python.exe"`.

```
python tools\orca_reload\orca_reload.py D:\Grip\orca_slicer\GripV\GripV_parts.3mf
python tools\orca_reload\orca_reload.py D:\Grip\orca_slicer
```

The second line updates every `.3mf` under that folder. Open each `_reloaded.3mf` in Orca, check it, then save it over the original (or rename it).

The report lists every part that is not unchanged:

```
GripV_parts.3mf -> D:\Grip\orca_slicer\GripV\GripV_parts_reloaded.3mf
  updated   R4.stl                             plate 5      1320 -> 1320 triangles, size 23.99x27.29x33.64 -> 28.79x27.29x43.73 mm, moved +1.903 mm in Z to sit on the bed
            from D:\Grip\orca_slicer\GripV\parts\triggers\default\press_default\R4.stl
  missing   StickL.stl                         plate 2      D:\Grip\orca_slicer\GripV\parts\StickL.stl (file not found)
  1 updated, 35 unchanged, 1 missing
```

| Option | What it does |
| --- | --- |
| `-o FILE` | Output file name (single project only). |
| `--out-dir DIR` | Put the outputs in this folder instead of next to each project. |
| `--suffix TEXT` | Text added to output names (default `_reloaded`). |
| `--search DIR` | Where to look for STLs that are no longer at their saved path. Can be repeated. |
| `--anchor center` | Default. A changed part keeps its bounding-box centre, like Orca. |
| `--anchor origin` | A changed part keeps the STL's own coordinate origin instead (see below). |
| `--no-drop` | Do not move objects up or down to sit on the bed. |
| `--dry-run` | Only print the report and write nothing. |

The exit code is 0 when everything was found, 2 when some parts were missing or failed, and 1 when a project could not be processed at all.

## Where a changed part ends up

**Default (`--anchor center`).** This matches Orca 2.x's Reload from disk. The new mesh is centred where the old mesh's bounding-box centre was, in the part's own frame. Then the object's rotation and plate position are applied as before, and the object is moved up or down so it sits on the bed. If an object was deliberately sunk into the bed, it is left at its height. A part that grows or shrinks therefore stays in its spot on the plate with the same rotation. A part that only moved inside the STL (the same shape at a different origin) counts as unchanged.

**`--anchor origin`.** The new mesh keeps the STL's coordinate origin where the old one was. A part that grew in one direction in Blender grows in that direction on the plate too. Use it for objects assembled from several STLs that share one coordinate system, where the parts must stay aligned.

This mode relies on the source offset Orca records when it first imports an STL. Orca's own Reload from disk does not update that value. So on a project that was reloaded inside Orca, the first `origin` run can shift parts by however far they moved since the import. The report notes `centre moved X mm` for each part, so check those numbers.

## How the STLs are found

1. The path saved in the project. Orca saves the full path, for example `D:\Grip\orca_slicer\GripV\parts\pin.stl`.
2. The same path ending under the project's folder and each `--search` folder. For example, `parts\pin.stl` next to the project.
3. A file with the same name anywhere under the `--search` folders, if there is exactly one.

A part whose STL is missing, or matches several files, is listed and left as it was. The other parts are still updated.

## What it does not do

- It only reloads parts loaded from STL files. Parts from OBJ, STEP or 3MF files, Orca's built-in shapes and text are skipped.
- It skips objects that were cut in Orca, because reloading would put the uncut STL back.
- It skips parts that Orca converted from inches or meters.
- It removes painted supports, seams or colours from a part whose shape changed, and notes this in the report. The Blender extension paints seams back on.
- It leaves the plate thumbnails showing the old shapes until the project is saved in Orca.

It was built and tested against OrcaSlicer 2.4 project files. Bambu Studio uses the same project format, so it should work there too, but that is untested.

## Tests

```
python -m unittest discover tools/orca_reload
```
