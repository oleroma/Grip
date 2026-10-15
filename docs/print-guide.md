# Printing guide (draft)

> **Draft.** This is the first written version, based on the development notes. It covers print settings that matter for fit. Cleaning and assembly are in the [assembly guide](assembly-guide.md) and the hardware in the [bill of materials](bom.md), both drafts; a video guide is still to come. Settings below were tested on FDM printers with PLA unless stated otherwise.

## What to print

Exported files live in `orca_slicer/`, each as `.stl` and, where available, as an OrcaSlicer `.3mf`. The [print list](../orca_slicer/README.md) says which files to print for each shape, how many of each, and which parts are not exported yet.

| Folder | Contents |
| --- | --- |
| `orca_slicer/GripV/case_standard/`, `case_hollow/` | Case parts: bottom, top, and top variants with the capacitive button as a `knob` or a `plate`, with or without the D-pad stick |
| `orca_slicer/GripV/parts/` | Buttons and caps, sticks, triggers, bumpers, D-pad stick, battery cover, cable holder, pins, scroll wheel |
| `orca_slicer/GripX/xbox_style/`, `dualsense_style/` | Case parts, bumpers and triggers for the two classic shapes |
| `orca_slicer/GripX/parts/` | Buttons and caps, sticks, D-pad stick, battery cover, cable holder, pins |

Parts that depend on fit come in a tolerance set. The folders are named for the setting: `tight`, `default` and `loose`, for example `buttons/default/cap_tight` (default button tolerance, tight caps) and `triggers/loose/press_default`. Start with `default`. If a part is too tight or too loose, print the neighbouring variant of that part only; you do not need to reprint the case. The [print list](../orca_slicer/README.md#tolerances) has a table of which folder to try for each problem.

## Solid case

The solid version is held together with screws. M2.5 DIN912 screws and nuts are used; the nut pockets are reinforced on all sides, because PLA can twist or bend while a nut is pressed in. Take your time when installing the nuts.

## PCB slot

The PCB sits on a 1 mm edge around its perimeter.

- Reduce the **XY distance between supports and the part** to about **0.2 mm**, so the edge is properly supported.
- Use a **solid support interface** with no gaps. It greatly improves the surface quality of the PCB slot and the supports come off as one piece.

If the PCB sits slightly shifted in Y (for example sticks that look misaligned), enable the **pillars** option in the global parameters.

## Hollow version

The hollow version has three parts: top case, bottom case and a middle plate that holds the PCB. It needs clean prints, because the geometry is intricate.

- Print as cleanly as possible, with as little stringing and warping as you can get, and make sure the parts stick well to the bed. Parts that warp will not assemble.
- Clean each part thoroughly and check the critical spots before assembly.
- **Middle plate:** use settings tuned for the best support contact quality. A solid support interface greatly improves it.
- **Bottom case:** the R2 and R4 triggers float above the bed. Use the **smallest support Z distance** and **normal or snug supports**, so the support top surface carries the R2/R4 shafts well.
- **Top case:** use **tree supports**. There are spots above R1/L1 where regular supports cannot be removed.
- **Screws:** the hollow case is designed to go together without screws, but the current middle plate may not give enough clamping force to hold the controller together on its own. Use the screws until this is confirmed with your print settings.

## Tolerances and printer calibration

Every printer is a little different. The global parameters in `Grip.blend` have three presets for `tolerance`, `cap tolerance` and `press tolerance`: `tight`, `default` and `loose`. If the default exports do not fit, change the preset and re-export, or print a different variant from `orca_slicer/`.

## Still missing

- Photos and a video guide for cleaning and assembly. The written [assembly guide](assembly-guide.md) is a draft that has not been checked step by step on a build yet.
- A checked bill of materials. The [draft](bom.md) still has screw lengths, the board revision and the filament amounts to confirm.
- Some parts are not exported yet, among them the GripV middle plate (see [Known gaps](../orca_slicer/README.md#known-gaps)).
- Recommended slicer profiles
- A tolerance test print
