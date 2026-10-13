# Triggers (L2/R2) and back paddles (L4/R4)

R2 is the main trigger and R4 is the back paddle below it. L2 and L4 are mirror copies of them. All four use the same arch design: the trigger is a curved bar that runs along a circular arc and slides in a matching curved opening in the case bottom. When you pull it, it moves along the arc and presses a switch on the board. There is no hinge and no screw. So the arc decides how the trigger moves, and the length, width and tip decide how it feels.

Each trigger is placed relative to its switch on the board (the objects `R2_pcb_button` and `R4_pcb_button`). Moving the trigger therefore means moving it along or away from the switch, and the case opening always follows.

**Where:** controls panel › R2R4 › `… R2 parameters` and `… R4 parameters` › `trigger parameters`. On GripX each preset has two `trigger parameters` nodes, frame "GripX" for the xbox style and "GripD" for dualsense. Edit the one for the style you use. On GripV, the node in frame "SNES" is an unconnected alternative.

## How it moves

| Input | What it changes |
|---|---|
| `trigger radius` | radius of the arc the trigger slides on. Larger is a flatter path, smaller a tighter curve. |
| `button pressed height` | height offset of the trigger above its switch |
| `action` | shows the trigger pressed, to check it. Preview only. |

## Shape

| Input | What it changes |
|---|---|
| `trigger length` | length of the trigger, measured along the arc |
| `width` | width of the bar (left to right) |
| `height` | thickness of the bar |
| `tip angle offset`, `tip shear` | tilt and lean of the finger end |
| `top bevel` | rounding of the finger end |
| `bevel`, `bevel cutoff` | rounding of the long edges. `bevel cutoff` cuts the rounding off at a point. |
| `bevel subd` | smoothness of that rounding. Keep it at 1: 2 adds mesh defects (see below). |
| `stopper length`, `stopper height` | a stop on the bar, probably what limits how far the trigger slides. The case opening has a slot for it. |
| `subdivision length` | mesh density along the arc (smaller is smoother); the shape does not change |

## Position

| Input | What it changes |
|---|---|
| `button radius offset` | moves the trigger away from the switch, outward from the arc centre |
| `x offset` | moves it sideways |
| `button rotation` | turns it about the vertical axis (radians) |
| `shift z` | slides it along the arc |

All of these move the case opening with the trigger.

## Fit

| Input | What it changes |
|---|---|
| `x tolerance`, `radius tolerance` | play sideways and across the arc in the opening. They come from the global `tolerance` through a `tolerance set`. |
| `button press tolerance` | trims the end of the trigger that presses the switch, which probably sets the free play before the click. It comes from the global `press tolerance` through a `tolerance set`. |

## Good to know

- The trigger meshes are not perfectly closed, and `bevel subd` = 2 makes that worse. Slicers usually repair it. In one Blender build an unlucky `shift z` value made the whole case bottom vanish. If that happens after a trigger edit, nudge the value.
- `marks` (global) engraves a letter on the triggers ([Marks](marks-and-logos.md)).

## Export

The "Triggers" preset exports L2, R2, L4 and R4 at each `tolerance` × `press tolerance` (and, on GripX, per style).
