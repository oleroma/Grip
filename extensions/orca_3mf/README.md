# Orca Reload

An **Orca** tab in the 3D Viewport sidebar that builds OrcaSlicer projects (`.3mf`) from the STLs Combi Export writes. You set up each project once in Blender: its plates, the parts on each plate, how each part stands on the plate, and the seam drawn on it. **Build** then writes the project, so a new export is one click away from a ready Orca project, seams included.

The setup is saved in the .blend file. The tab is laid out like Combi Export: the roots on top, then a list per level with its buttons on the right.

## The tab

| Panel | What it holds |
| --- | --- |
| Orca Projects | **STL root**: where the parts' paths start. Empty: Combi Export's root. **3MF root**: where the projects are saved, `//../orca_slicer/` by default. Next to it, **Import** (make a project from an Orca file) and **Build** (every ticked project). **Seams**: the width of the painted seam strip and how far a seam line may be from the surface. |
| Info | The log of the last build or import, and a short guide. |
| Projects | One row per 3MF file: its Build button, tick, name and folder. Below the list, the active project's STL folder and **Settings from**. |
| Plates | One row per Orca plate: tick, number, name, **gap** and STL folder. |
| Parts | One row per part: tick, name (as Orca lists it), copies, seam mark and STL path. A red path means the STL is not there. Below the list, the active part's **Up**, **Turn**, **Copies**, **Mirror** and **Seam**. |

A part's STL is found at STL root / project's STL folder / plate's STL folder / the part's path, with `/` between folders. So a project whose STL folder is `GripV/parts` and a plate whose STL folder is `buttons/default` take `cap_default/circle.stl` from `GripV/parts/buttons/default/cap_default/circle.stl`.

The **+** of the Parts list opens a file browser: pick one or more STLs, each becomes a part (Shift + **+** adds an empty one). The folder button next to a part's path picks another file.

## Placing the parts

- **Up**: the part's direction, in Blender as exported, that points up on the plate. `0, 0, 1` prints it as it stands in Blender, `0, 0, -1` upside down, `0, 1, 0` on its front face (Blender's front is −Y).
- **Turn**: then turns it around that axis.
- **Copies**: how many of it go on the plate.
- **Mirror**: mirror the part across its own X axis (a part mirrored in Orca imports with this ticked, and builds back mirrored).

Each plate is nested on its own: parts are stood up, set on the bed, and placed by their footprint, largest first, **gap** apart and half a gap from the edges, as a compact block in the middle of the plate. A part that does not fit stops the build and the log says which. The plates are laid out the way Orca lays them out, so each part lands on its plate.

## Seams

Pick a curve or a mesh in a part's **Seam** field, drawn on that part's surface where the seam should go.

- **Curve**: its splines. Snapping to Face helps to place the points. Bevel and modifiers are ignored.
- **Mesh made of edges only**: all its edges.
- **Mesh with faces**: the edges marked as seam (Edge › Mark Seam). Geometry Nodes can output them too: store a boolean edge attribute named `orca_seam` (or `uv_seam`, Blender's own seam mark).

The line is snapped onto the part's surface within **Snap**, so one line serves the tight, default and loose versions of a part: give all of them the same Seam. Orca puts the seam where each layer's perimeter crosses the painted strip.

## Build

1. Export the STLs with Combi Export.
2. Press the Build button of a project row, or the one next to the 3MF root for every ticked project.

A **new** project takes its printer, process and filament settings from **Settings from**: any Orca project made for your printer. A project added to the list starts with the Settings from of the selected project, or that project's own file. Orca opens a project without settings as bare parts, without its plates, so Build refuses to write one.

An **existing** project is written over, and keeps:

- its printer, process and filament settings, and the files Orca keeps with them
- each part's own settings, matched by shape, then source file, then plate, then name (for example wall loops or infill set on a part in Orca)
- each plate's settings, by name (for example its bed type)
- the painting of a part whose shape did not change (supports, colours, and its seams when it has no Seam line)
- modifiers, negative parts and support blockers made in Orca (their meshes and settings, re-anchored to the part)
- variable layer heights, height range modifiers and brim ears (`layer_heights_profile.txt`, `layer_config_ranges.xml`, `brim_ear_points.txt`), re-keyed to the part's new position
- per-layer custom G-code (`custom_gcode_per_layer.xml`), re-keyed to the plate's new position

Each part's place on the plate is set again by the nesting. Objects made of several STLs are not built, and what Build does not keep yet is listed under Not done yet.

## Import

**Import** makes a project from an existing Orca project: its plates, and each part with its STL, Up, Turn and copies. The STLs are looked for below the STL root. When several files have the part's file name (Orca often keeps only the name, and the tight and loose versions share it), the one with the part's exact shape is taken. The common folders become the project's and plates' STL folders. Build then updates that same file.

## How it works

| File | What it holds |
| --- | --- |
| `build3mf.py` | Writes projects from projects › plates › parts, and reads an existing project's layout for Import. No Blender needed. |
| `layout.py` | Up axis and turn to a rotation, footprints, nesting, and Orca's plate grid. No Blender needed. |
| `reload3mf.py` | Reads Orca projects and reloads STLs into them. Also runs on its own from the command line, see below. No Blender needed. |
| `seams.py` | Seam lines to Orca's seam painting: each triangle near the line is split until the painted strip follows it. No Blender needed. |
| `blender_seams.py` | Reads a seam line from a curve or mesh. |
| `props.py` | What the .blend saves, and how the paths are joined. |
| `operators.py`, `ui.py` | The tab's buttons and panels. |

Orca stores each part's mesh centred on itself, and the part's place and rotation on the build item; plates sit side by side, 1.2 bed widths apart, √(number of plates), rounded up, to a row, rows going towards −Y, and each part belongs to the plate it lies on.

## Not done yet

- Seam blockers (places the seam must avoid).
- Keeping parts where they were placed by hand in Orca: Build always nests.
- Nesting by outline: parts are nested by their bounding box, so L-shaped parts leave space unused.
- Curves made by Geometry Nodes: a curve object's modifiers are ignored. A mesh object with Geometry Nodes works when its nodes output mesh edges (add Curve to Mesh).
- NURBS curves follow their control points, not the smooth curve.
- Scale set in Orca is dropped on Import.
- Bed exclude areas are only warned about, not honoured when nesting; round and non-rectangular beds nest on their bounding box.

## Command line reload

`reload3mf.py` also reloads every STL part of Orca projects from disk without Blender or Orca, like Orca's **Reload from disk** on every part. It needs only Python 3.8 or newer (Blender's own Python works). The original is never overwritten; the result is written as `NAME_reloaded.3mf`.

```
python orca_3mf\reload3mf.py D:\Grip\orca_slicer\GripV\GripV_parts.3mf
python orca_3mf\reload3mf.py D:\Grip\orca_slicer
```

The second line does every `.3mf` under that folder. Options: `-o FILE`, `--out-dir DIR`, `--suffix TEXT`, `--search DIR` (where to look for moved STLs), `--anchor center|origin`, `--no-drop`, `--dry-run`; `--help` explains each. Exit code 0 means all parts were found, 2 some were missing, 1 a project failed.

## Tests

```
python -I orca_3mf/tests/test_build.py
python -I orca_3mf/tests/test_seams.py
blender -b -P orca_3mf/tests/test_blender.py
python -I orca_3mf/tests/test_reload.py
```

`test_blender.py` needs a Python with the `bpy` module (Blender 5.2 or newer); the others need only Python. None of them open Grip.blend.
