# 3. Fit and tolerances

Grip is printed in many separate parts that slide, click or clip into each other. How well they work depends on the gaps between them, and those depend on your printer, filament and slicer profile. Every gap in the file is a parameter, so you can tune the design to your printer instead of sanding parts.

The values in the file were tuned for a Bambu Lab A1 with a 0.4 mm nozzle and 0.16 mm layers (the profile used by the OrcaSlicer projects in `orca_slicer/`). If your printer makes holes smaller or pins fatter than that, raise the tolerances; if parts wobble, lower them.

## Two kinds of tolerance

**Switchable fits (tight / default / loose).** The three global menus pick one of three values that each part stores for itself:

| Global menu | What it controls |
|---|---|
| `tolerance` | how loosely the button shafts slide in their case holes, and how loosely the triggers slide in their openings (side to side and along the arc) |
| `press tolerance` | how much press travel the triggers (and the GripV bumpers) have before they hit the switch |
| `cap tolerance` | how firmly the caps clip onto the button shafts |

The three values sit on a `tolerance set` node inside each part's preset group (for example in `GripV abxy`), next to the constructor it feeds. To change what "tight" means for a part, edit that node. The export presets write all three versions of the affected parts into separate folders, so you can print all three and keep the one that fits.

**Fixed fits.** All other gaps are plain numbers on the constructors. The important ones:

| Part | Input | What it is |
|---|---|---|
| caps | `cap case tolerance` | gap between each cap and its hole in the case top, per side |
| caps | `caps fit Z tolerance` | vertical play of the cap on its shaft |
| sticks | `shaft tolerance` | fit of the stick on the joystick module's shaft |
| capacitive | `capacitive plate tolerance` | gap around the capacitive plate |
| bumpers | `stem tolerance`, `bumper Z tolerance`, `X tolerance`, `overlap tolerance` | play around the pivot stem, under, beside and over the bumper |
| battery cover | `x tolerance`, `y tolerance`, `compression offset` | gap around the cover, and how hard it presses the battery |
| scroll wheel | `scroll wheel tolerance` | side play of the wheel in its slot |
| pins | `xy tol`, `z tol` | play of the alignment pins in their holes |
| PCB slot | `PCB tolerance XY` | gap around the board |
| D-pad stick | `stick tolerance`, `hook z tolerance` | fit of the cap on the stick |
| middle plate (shell bodies) | `xy tolerance`, `Z tolerance`, `fit Z tolerance`, `inner …`, `pcb pocket tolerance` | fit between the middle plate, the shells and the board |

## How the numbers act

- A tolerance is usually the **total** difference between part and hole. A button `tolerance` of 0.16 makes the shaft 0.16 mm narrower than its hole, which is 0.08 mm per side. The same holds for the pin and scroll wheel tolerances.
- Most tolerances shrink the **part**, not the hole, so after changing one you only need to reprint the part. The exceptions are `PCB tolerance XY`, which enlarges the slot in the case bottom, and the bumper `overlap tolerance` and `bumper Z tolerance`, which also move the case edge around the bumper slightly.
- `cap case tolerance` is per side: +0.2 makes the cap 0.4 mm smaller.
- `caps fit tolerance` (from `cap tolerance`) is the other way round: a higher value is a **tighter** cap.
- Size and position inputs (widths, `shift …`, `position`, `X`/`Y`/`Z`) usually move or resize the opening in the case as well, so changing them needs a new case print.

## Things to know

- GripX caps use the same value for tight, default and loose, and the GripX trigger `default` and `loose` values are equal. The GripX export folders for those are therefore identical. See [Exporting](05-exporting.md#known-problems).
- The GripX bumpers do not follow `press tolerance` at all. Their `tolerance set` is not connected. Change `button press tol` on the two GripX bumper nodes directly.
- Exported parts carry a mark, but it does not say which tolerance they were made with. See [Marks](parts/marks-and-logos.md).
