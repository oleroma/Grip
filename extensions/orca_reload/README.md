# Orca Reload

An **Orca** tab in the 3D Viewport sidebar. One button updates OrcaSlicer projects (`.3mf`): every part is reloaded from its STL file, and the seams you marked in Blender are painted onto the parts. Seams painted by hand in Orca are lost on every reload; seams marked here are painted again each time.

The reload itself is the same as [tools/orca_reload](../../tools/orca_reload/README.md): orientation, plate placement, copies and settings are kept, and changed parts are put back on the bed.

## Mark a seam

A seam line is a curve or a mesh with **is a seam line** ticked (Orca tab › Seam lines, with the object selected). Draw it on the part's surface where the seam should go.

- **Curve**: add a Bezier or Path curve and place its points on the surface. Snapping to Face helps. Bevel and modifiers are ignored; the splines are used.
- **Mesh made of edges only**: all its edges are used.
- **Mesh with faces**: only the edges marked as seam (Edge › Mark Seam). Geometry Nodes can output them too: store a boolean edge attribute named `orca_seam` (or `uv_seam`, Blender's own seam mark).

A line only needs to lie on the surface within the **Snap distance**. It is snapped onto the surface, so one line works for the tight, default and loose versions of a part. It is painted on every part it lies on, so a line on the standard case is also painted on the hollow case if they have the same outside. To limit it, type part of the file path in **Only for**, for example `case_standard`.

A line is used on a part only when at least half of it lies on that part. A line drawn on one part therefore does not paint the part it touches.

## Update the projects

1. Export the STLs as usual.
2. In the Orca tab, set **Projects** to a project or a folder. The default `//../orca_slicer/` is Grip's `orca_slicer` folder next to `blender/`.
3. Press **Update Orca projects**.

Each changed project is saved next to the original as `NAME_reloaded.3mf`, so you can check it in Orca first. Tick **Replace projects** to save over the originals instead.

The full report is in the text **Orca reload report** (Text Editor). It lists each changed part, the seam lines painted on it, and the share of each line that lies on the part. It also lists the seam lines that lie on no part.

| Setting | What it does |
| --- | --- |
| Projects | A `.3mf`, or a folder: every project under it. STLs that moved are searched for under it. |
| Seam width | Width of the seam strip painted along each line. Orca puts the seam in the middle of the strip on each layer. About one line width (0.6 mm) is enough. |
| Snap distance | How far a line may be from the surface and still be painted onto it. |
| Replace projects | Save over the originals instead of next to them. |

The settings are saved in the .blend file.

## How it works

Orca stores seam painting per triangle as a small subdivision tree (`paint_seam` in the project's mesh files). For every reloaded part, `seams.py` snaps the seam lines onto the new mesh and splits the triangles near them until the painted strip follows the line. A part whose shape did not change keeps its mesh and its other painting (supports, colours); only its seams are replaced. A part with a new shape loses its other painting, as with Orca's own reload.

| File | What it holds |
| --- | --- |
| `reload3mf.py` | Reads and writes the projects. No Blender needed; the command line tool runs it. |
| `seams.py` | Seam lines to Orca's seam painting. No Blender needed. |
| `blender_seams.py` | Reads the seam lines from the scene. |
| `ui.py` | The Orca tab, its settings and the Update button. |

## Not done yet

- Seam blockers (places the seam must avoid).
- Curves made by Geometry Nodes: a curve object's modifiers are ignored. A mesh object with Geometry Nodes works.
- NURBS curves follow their control points, not the smooth curve.

## Tests

```
python -I extensions/orca_reload/tests/test_seams.py
python -I extensions/orca_reload/tests/test_blender.py
python -m unittest discover tools/orca_reload
```

The first and last need only Python. `test_blender.py` needs a Python with the `bpy` module (Blender 5.2 or newer). None of them open Grip.blend.
