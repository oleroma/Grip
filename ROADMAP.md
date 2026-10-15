# Roadmap

This is a living plan. Items move as testing goes on.

## Now: customizable base shapes (first release)

Release the parametric controller with its base case shapes, so everyone can tune the parts to their own preferences:

- GripV, the custom ergonomic "pistol-like" shape (solid and hollow)
- GripX, the classic Xbox and DualSense styles (solid first, hollow in progress)
- Exported `.stl` and OrcaSlicer `.3mf` files for each shape, with a [print list](orca_slicer/README.md) per shape
- The Blender project with adjustable triggers, bumpers, sticks, buttons, caps, tolerances and battery cover

Needed before the release:

- [ ] Documentation: printing guide ([first draft](docs/print-guide.md)) and [print list](orca_slicer/README.md), cleaning and assembly guide ([draft](docs/assembly-guide.md)), bill of materials ([draft](docs/bom.md)), video guide
- [ ] Tooltips for the global parameters and the parameters that matter for fit (tolerances, triggers, bumpers, sticks)
- [ ] Simplified controls for frequently used parameters in the Blender UI (a first version is the [Grip tab](extensions/grip_controls/README.md))
- [ ] Clean-up of the Blender file: unused and `_OLD` node groups, duplicated groups, naming typos
- [ ] `.3mf` files for every released version (what exists so far is in the [print list](orca_slicer/README.md))

## Next: ergonomics for your hand

Today you tune triggers, bumpers and sticks by hand. Next step is a small "My hand" layer in the Blender project: a handful of inputs (hand length and width, thumb reach, finger span, trigger-finger length, left or right handed) that drive the existing trigger, bumper and stick parameters, plus ready-made small, medium and large presets.

## Later

- A parametric or shape-key-driven case body: scale along each axis, grip thickness, pistol angle
- Control placement inputs for ABXY, D-pad and sticks
- More base shapes: the SNES-style portable shape and the experimental compliant-bumper shape
- Printed tolerance test strip, so you can choose `tight`, `default` or `loose` with one print
- Slicer profiles for the printed variants
