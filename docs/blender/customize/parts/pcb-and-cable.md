# PCB slot, USB opening and cable holder

Three things in the case bottom are about the electronics: the slot the main board sits in, the USB opening, and an optional part that clamps the USB cable inside the case.

## PCB slot

The board drops into a slot in the case bottom. Judging by the parameter names and how the slot changes, it rests on a ledge around its edge, with a deeper pocket underneath for the components on its underside. The slot's outline is a fixed shape of the board (object `pcb cutout` in the `source` scene). The depths and fits are parameters.

**Where:** controls panel › PCB AND BATTERY › `… pcb cutout paramters` › `pcb cutout parameters`.

| Input | What it changes |
|---|---|
| `PCB thickness` | depth of the slot for the board itself |
| `PCB below height` | depth of the pocket under the board for its components |
| `PCB support edge` | width of the ledge the board rests on |
| `PCB tolerance XY` | gap around the board |

On shell bodies the board sits in the middle plate instead, and these values shape the plate's pocket.

To fit a different board outline, edit the mesh of `pcb cutout`; it is half of the board, mirrored.

## USB opening

The USB opening is a fixed shape, not a parameter. The global `cable holder` picks between two versions: a wider one that takes the cable holder, and a plain one.

## Cable holder

A small part that sits in the USB opening and clamps the cable, probably as strain relief. It has teeth that grip the cable, and its outside follows the case shape of the current variant.

**Where:** this part has no variant preset. Its size is the node **`cable size.001`** (labelled "pwnage paracord") inside the group `cable holder parameters`, shared by both variants:

| Input | What it changes |
|---|---|
| `width`, `height` | the cable plug size the holder is made for |

The other node in that group, `cable size`, is not used. To fit your cable, measure its plug and set `cable size.001`.

## Export

Both "Parts" presets export the cable holder as `cable_holder.stl`.
