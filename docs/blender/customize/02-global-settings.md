# 2. Global settings

The node `global parameters` inside the group `global` holds the switches that apply to the whole controller. You find it at the top of the controls panel. The export presets override several of them while they export (variant, subdivision, voxel resolution, body type, tolerances), so what you set here mostly matters for what you see while editing.

## Which controller

| Setting | What it decides |
|---|---|
| `variant` | GripV or GripX (GripR1 is legacy). It picks the basemesh and the preset of every part. It must match the scene you are in; see [Getting started](01-getting-started.md#choose-the-controller). |
| `style` | GripX only: `xbox` or `dualsense`. It changes the case shape and picks the style-specific trigger, bumper and back-screw settings. Buttons, sticks and small parts are the same for both styles. Ignored for GripV. |

## How the case is built

| Setting | What it decides |
|---|---|
| `body type` | the inside of the case: `standard` (solid), `indent` (solid with a pattern pressed into the surface), `hollow` (a thin shell with ribs and bosses, clipped onto a middle plate) or `lattice` (a shell whose outer wall is replaced by strips). See [Case and body types](04-case.md). |
| `hollow top` | GripV with a `standard` body only: makes the top half a shell while the bottom stays solid. This is a lighter top on a solid bottom. The GripV "Case standard" export turns it on, so the released GripV standard tops are shells. |
| `fill type` | the pattern of the `indent` body: Gyroid, FischerKoch S, FischerKoch CY, Voronoi, Diamond, Primitive or cubic. `manual` is unfinished and destroys the case; do not use it. Ignored by other bodies. |
| `ribs` | shell bodies: adds stiffening ribs inside the top half. |
| `pillars` | adds support pillars inside the case bottom. Not used by the `hollow` body. |
| `screws` | solid bodies (`standard`, `indent`): cuts the screw holes and nut pockets. Turn it off only if you hold the case together another way. |
| `screws hollow` | shell bodies (`hollow`, `lattice`): adds solid bosses around the screws so the screws have something to bite into. |
| `subdivision level` | how smooth the case surface is (low to very high). Keep it low while editing; the case exports use very high. |
| `voxel resolution` | how fine the shell of `hollow`, `lattice` and `hollow top` bodies is (low, medium or high voxel size). Higher is smoother but much slower. The case exports use high. |

## Features

| Setting | What it decides |
|---|---|
| `cable holder` | which USB opening is cut. On: a wider opening that takes the printed [cable holder](parts/pcb-and-cable.md#cable-holder), which clamps the cable inside the case. Off: a plain USB opening. |
| `stock bumpers` | replaces the generated L1/R1 bumpers and their case openings with fixed, hand-modelled bumpers. Use it if you do not want to tune bumpers. |
| `top wire cutouts` | cuts wire channels into the case top. |
| `R4 wire cutouts` | cuts a wire channel into both halves, probably for the back-paddle (R4/L4) switch wiring. |
| `horizontal buttons` | which button shaft design is used. On (as saved and released) is the current design, probably made to be printed lying down. Off is an older design that gives unstable results; leave it on. |
| `button logo` | engraves the symbols on the ABXY caps and the Home cap. |
| `marks` | engraves an identification letter on the button shafts and triggers (the bumpers have their own switch). See [Marks and logos](parts/marks-and-logos.md). |

## Fit

| Setting | What it decides |
|---|---|
| `tolerance` | tight, default or loose fit of the button shafts in the case and of the triggers in their openings |
| `press tolerance` | tight, default or loose press travel of the triggers and the GripV bumpers |
| `cap tolerance` | tight, default or loose fit of the caps on the button shafts (GripV; GripX has the same value for all three) |

Each part decides what "tight", "default" and "loose" mean for itself. See [Fit and tolerances](03-fit-and-tolerances.md).
