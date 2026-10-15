# Grip.blend documentation

`blender/Grip.blend` generates every printed part of the Grip controller with Geometry Nodes. That includes the case halves, the buttons and their caps, the thumbsticks, triggers and bumpers, and the small parts. Almost every dimension is a parameter, so you can adapt a part to your hand, your printer or your hardware and export new STL files.

There are two guides, for two different jobs:

| Guide | For you if… |
|---|---|
| **[Customize and export](customize/README.md)** | you want to change a part (a tighter button, a taller stick, a different trigger) and print it. It explains what each setting changes in the design, where to find it and how to export. You do not need to know how the nodes work. |
| **[Work on the node system](develop/README.md)** | you want to fix, extend or clean up the file. It explains how the file is organised, how a number travels from a preset to the geometry, how each part and the case are built, and what each piece of that structure is for. |

The guides do not list current values. Every preset value is recorded in `blender/tracking.json`, which the `blender_tracking` add-on rewrites each time the file is saved, so its git history shows every change.

## Words used in both guides

| Term | Meaning |
|---|---|
| variant | a controller shape: **GripV** or **GripX**. GripR1 is an older variant that is still in the file but not released. |
| style | GripX only: the **xbox** or **dualsense** case shape |
| global settings | the switches for the whole file (variant, body type, tolerances, …), on the node `global parameters` inside the group `global` |
| preset group | the group that holds one part's numbers for one variant, for example `GripV abxy` or `GripX R2 parameters` |
| constructor | a node inside a preset group whose inputs are the numbers, for example `button parameters` or `trigger parameters` |
| controls panel | `GripV controls` and `GripX controls`: one node group that shows the global settings and every preset group of a variant, sorted into frames |
| cutter | a hidden object in the `source` scene that cuts a part's opening into the case. It is made by the same generator and preset as the part, so part and opening always match. |
| basemesh | the hand-modelled outer shape of the controller that the case is made from |
| body type | how the inside of the case is built: solid, patterned, a thin shell or a lattice |

Names are written exactly as they are spelled in the file, so you can search for them in Blender. The node group and input typos were fixed on 2026-10-15; a few names people rarely see still carry theirs ([Known issues](develop/07-known-issues.md#d-leftovers-and-naming)).

Some descriptions of what a part is *for* were reconstructed from the file itself. Where that is a guess rather than something the file shows, the text says "probably".
