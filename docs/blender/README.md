# Grip.blend documentation

How `blender/Grip.blend` is built, what every parameter does, and how to change it safely. Everything was read from the file itself and checked by evaluating copies of it headless; nothing in the file was changed.

Each claim carries a tag: **[measured]** (observed by evaluating a copy), **[wiring]** (read from node links and stored values) or **[inferred]** (an interpretation that could not be proved).

## Start here

- **New to the file?** Read [1. File tour](01-file-tour.md), then [2. Parameter system](02-parameter-system.md).
- **Want to change something?** Go to [10. Editing guide](10-editing.md); its table "Where is the value for…?" points at the right preset.
- **Want to know what is broken or odd?** See [9. Issues](09-issues.md).

## The model

| Page | What it covers |
|---|---|
| [1. File tour](01-file-tour.md) | scenes, collections, objects, add-on data, baseline sizes |
| [2. Parameter system](02-parameter-system.md) | global switches, presets, bundles, `selector`, where a value lives |
| [3. Global switches](03-global-switches.md) | the 21 inputs of `global parameters`, measured |
| [4. Variants and styles](04-variants-and-styles.md) | GripV, GripX xbox and dualsense, GripR1 |
| [5. Case](05-case.md) | from basemesh to case halves, every cutter |
| [6. Body types](06-body-types.md) | standard, indent, hollow, lattice, hollow top, middle plate, with cross-sections |
| [7. Tolerances](07-tolerances.md) | the three tolerance menus and every fixed fit value |
| [8. Export and tracking](08-export-and-tracking.md) | `combi_export` presets, the STL files, `tracking.json` |
| [9. Issues](09-issues.md) | everything wrong, fragile, misleading or unused, with fixes |
| [10. Editing guide](10-editing.md) | recipes and pitfalls |
| [11. Method](11-method.md) | how this was produced and its limits |

## Parts

| Page | Objects |
|---|---|
| [Buttons and caps](parts/buttons-and-caps.md) | ABXY, D-pad, Select, Home shafts and caps |
| [Capacitive plate](parts/capacitive.md) | `capacitive` |
| [Thumbsticks](parts/sticks.md) | `StickL`, `StickR` |
| [D-pad stick](parts/dpad-stick.md) | the rocker D-pad alternative (6 pieces) |
| [Triggers](parts/triggers.md) | `L2`, `R2`, `L4`, `R4` |
| [Bumpers](parts/bumpers.md) | `L1`, `R1` |
| [Battery cover](parts/battery-cover.md) | `battery cover` and the battery compartment |
| [Screws](parts/screws.md) | screw holes, nut pockets, `nut lock`, `reinforcers` |
| [Alignment pins](parts/pins.md) | `pin` |
| [Scroll wheel](parts/scroll-wheel.md) | `scrollwheel`, `scrollwheel core`, `scrollwheel holder` |
| [PCB slot, USB and cable holder](parts/pcb-and-cable.md) | PCB cutout, USB opening, `cable holder` |
| [Marks and logos](parts/marks-and-logos.md) | engraved letters and cap logos |

## Reference tables

| Page | Content |
|---|---|
| [Preset values, GripV](reference/preset-values-GripV.md) | every value in every GripV preset, in controls-panel order |
| [Preset values, GripX](reference/preset-values-GripX.md) | the same for GripX, with the xbox and dualsense nodes side by side |
| [Parameter groups](reference/parameter-groups.md) | the 54 constructor groups: inputs, defaults, bundle keys |
| [Node group catalogue](reference/node-group-catalogue.md) | all 511 node groups by role, with users and reachability |
| [Measurements](reference/measurements.md) | size, volume and mesh quality of every object, per scene and body, and every GripX stick preset |

The reference tables are generated from the file; if the file changes, they describe the version at commit `571e768`.
