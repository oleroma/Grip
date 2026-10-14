# Capacitive plate

A part in the middle of the ABXY cluster, probably a touch surface for a capacitive sensor on the board. It comes in two forms, and the case top gets the matching opening:

| Mode | What you get |
|---|---|
| `knob` | a small round knob between the face buttons |
| `plate` | a plate around the face buttons |
| `disabled` | no part; the case only keeps clear of the sensor on the board |

**Where:** controls panel › BUTTONS › `… abxy` › `capacitive plate parameters`.

| Input | What it changes |
|---|---|
| `capacitive` | the mode above |
| `screw hole` | a hole through the part, probably for a screw that connects it to the sensor |
| `capacitive plate tolerance` | plate mode: gap between the plate and the case |
| `plate button offset` | plate mode: how far the plate reaches out around the buttons (its opening in the case grows with it) |
| `capacitive plate stem tolerance` | does nothing |

## Export

The case-top exports write every top twice, as `…_cap_plate` and `…_cap_knob`, so pick the top that matches the part you print. The "Parts" preset exports the part in both modes. The GripX `capacitive_knob.stl` currently in `orca_slicer/` was exported while the GripX preset still pointed at the GripV settings, so it is the plate until the GripX "Parts" preset is run again ([Exporting](../05-exporting.md#known-problems)).
