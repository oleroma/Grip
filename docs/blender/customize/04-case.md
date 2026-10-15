# 4. Case and body types

The case is two printed halves, `case_top` and `case_bottom`. Shell bodies on GripV add a third part, `case_middle_plate`. They are generated from three things:

1. the **basemesh**, the hand-modelled outer shape;
2. the **body type**, which decides what the inside looks like;
3. the **openings** of all parts. Every button, stick, trigger and screw cuts its own opening, generated from that part's preset. That is why a part change often changes the case.

## The outer shape: the basemesh

The outside of the controller is not parametric. It is a mesh you model by hand:

| Variant | Basemesh object |
|---|---|
| GripV | `basemesh GripV` |
| GripX xbox | `basemesh_X_style` |
| GripX dualsense | `basemesh_D_style` |

Each basemesh is **half** of the controller. A `MirrorX` modifier mirrors it across the centre line and welds the seam. A subdivision modifier then smooths it to the global `subdivision level`. Edge creases (the `crease_edge` attribute) keep chosen edges sharp through that smoothing. To change the grip shape, edit the basemesh in Edit Mode: move, add or crease edges on the half. Everything else (case halves, shells, patterns, the cable holder, the stick heights) follows from it.

The case is split into top and bottom at the height **Z = 40 mm**. That height is fixed in the nodes, not a parameter, so keep the basemesh's parting line there.

Openings that are fixed meshes do not follow the basemesh: the GripV stick cutouts, the USB opening, wire channels and the clearances for parts on the board. If you move the shape far, check that they still sit where they should.

## Body types

The global `body type` chooses one of four ways to build the inside:

| Body | What you get | Choose it for |
|---|---|---|
| `standard` | solid halves | the simplest, strongest print; works with every option |
| `indent` | solid halves with a 3D pattern pressed into the outer surface | grip texture and looks. The pattern is chosen with `fill type`. |
| `hollow` | a thin shell with a solid top face, inner ribs, solid bosses around every opening and screw, and a ledge that holds a separate middle plate | much less material and weight; also suits resin and powder printing |
| `lattice` | like `hollow`, but the outer wall is replaced by strips that follow drawn curves | an open, see-through look. GripV only in practice, see below. |

On GripV, `standard` + `hollow top` gives a shell top on a solid bottom, which is what the GripV "Case standard" export produces.

### Hollow

The shell is computed as a distance field (voxels) from the basemesh, so it is smooth but slow to compute. Its settings are in the `shell` frame of the controls panel, in `GripV hollow parameters` / `GripX hollow parameters`:

| Input | What it changes |
|---|---|
| `shell thickness` | wall thickness of the shell |
| `top thickness` | thickness of the solid layer under the flat top face of the controller |
| `top grid` | perforates that top layer with a pattern instead of leaving it solid (on for GripX) |
| `grid thickness`, `smooth grid` | thickness and smoothness of that pattern |
| `stick offset`, `parts offset` | width of the solid rings the pattern keeps around the stick holes and around the button, LED, scroll-wheel and capacitive openings |
| `protect geometry` | thickness of the solid bosses grown around every opening and screw. These are what the openings are cut through, so they decide how strong the walls around buttons and screws are. |
| `band remesh width` | technical; leave it |
| `voxel remesh size` | linked to the global `voxel resolution`; change that instead |
| `smooth sdf` | does nothing |

Global settings that matter for shells: `ribs` (stiffening ribs in the top half), `screws hollow` (screw bosses; turn it on for shells), `voxel resolution`.

### The middle plate (shell bodies)

With `hollow` and `lattice` bodies the two shells clip onto a flat **middle plate** that carries the board and the battery compartment. The plate is printed separately. Its settings shape the plate and the ledge inside the shells together, so they always fit. They are in `GripV middle plate parameters` / `GripX shell middle plate parameters` (frame `shell`):

| Input | What it changes |
|---|---|
| `inset width` | how far inside the outer wall the plate and its ledge sit |
| `insert height` | plate thickness |
| `plate inset width` | width of the plate's rim |
| `hook inset`, `hook height`, `slant height` | the snap hook between plate and shell |
| `rim slant height`, `rim slant outset` | the slope of the ledge inside the shell |
| `pcb pocket thickness`, `pcb pocket tolerance` | the pocket the board sits in |
| `xy tolerance`, `Z tolerance`, `fit Z tolerance`, `inner xy tolerance`, `inner Z tolerance` | fits of the plate in the shells |
| `hook to top` | does nothing |

GripX has no middle plate object yet. Its middle plate settings still shape the ledge inside the GripX shells.

**The GripV plate is not exported at the moment**, because its collection is excluded from the GripV view layer. See [Exporting](05-exporting.md#known-problems).

### Indent

The case stays solid, and pockets up to a set depth are pressed into the outer surface wherever the pattern is "empty". This leaves ridges in the pattern's shape. `fill type` picks the pattern, and each pattern has its own preset in the `pattern` (GripX: `FILL`) frame. In each preset:

| Input | What it changes |
|---|---|
| `scale` | pattern frequency: larger is a finer, denser pattern |
| `thickness` | width of the ridges that stay |
| `fill depth` | depth of the pockets |
| `fill depth smooth` | rounding of the pocket floors |
| `boundary offset`, `boundary smooth` | how the pattern blends into the outer surface |
| `limit geometry smooth` | how it blends where the pattern stops |
| `rotate`, `translate`, `scale axis` | orientation, position and per-axis stretch of the pattern |
| `droop height`, `droop depth`, `droop multiplier` | bend the pattern with the surface |
| `voxel size` | resolution of the outer surface calculation |

The other inputs in these presets (shell, protect, rim, flat-surface and sharp settings) do nothing for `indent`. The pattern is kept away from the bumper, USB, screw and trigger openings automatically. The `cubic` pattern also reads `… cubic hollow array parameters` (three plane families, each with spacing, rotation and offset).

### Lattice

The outer wall becomes strips of skin that follow 24 curves drawn on the GripV surface (collection `creases and curves`). Two inputs matter, in the lattice slot (`GripV lattice parameters`, GripX `GripX cubic hollow parameters`): `voxel size` (resolution) and `insert rim height` (height of the closed band where the halves meet). The rest of that preset does nothing. The top face, ribs, bosses and middle plate work as for `hollow`.

The curves are projected onto the GripV basemesh only, so a **GripX lattice case does not follow the GripX shape**. Treat lattice as GripV-only until that is fixed.

## Options that cut or add to the case

These are global settings ([Global settings](02-global-settings.md)): `screws` / `screws hollow`, `pillars`, `cable holder` (USB opening shape), `stock bumpers`, `top wire cutouts`, `R4 wire cutouts`. The capacitive mode and the D-pad stick switch also change the openings in the case top.
