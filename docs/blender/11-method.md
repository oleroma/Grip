# 11. How this documentation was produced

Everything here comes from the `.blend` itself, the two export preset JSON files, `blender/tracking.json` and the add-on source in `extensions/`. The work was done in two passes: the first on 2026-10-12 with Blender on Windows (pages 1 to 8, the first part pages), the second on 2026-10-13 in a cloud container (see [Second pass](#second-pass-2026-10-13) below), which re-checked the first and added the remaining part pages, the issues list, the editing guide and the reference tables. No earlier documentation was used as a source.

## Ground rules

- `blender/Grip.blend` was never opened for writing. All work used byte-identical copies (MD5 `f253e09119cbf0184f7bbcc10589298c`) in a scratch folder, opened with `blender.exe -b --factory-startup` (Blender 5.2.0 LTS, so no add-ons and no auto-run scripts), and nothing was saved.
- Claims are tagged **[measured]** (observed by evaluating a copy), **[wiring]** (read from node links and stored values) or **[inferred]** (interpretation).

## Static extraction

A Python script inside Blender dumped every scene, view layer, collection, object (transform, visibility, modifiers and all their input values), and every node group (interface sockets with type, default, min, max, subtype, description; every node with its settings and unlinked input values; every link) to JSON. All further static analysis ran on that dump:

- **Call graph** of group nodes, from the 64 groups used by modifiers down; groups reachable from objects in the `GripV`/`GripX` scenes are called *release* groups (437).
- **Liveness**: a node is live if a path of links leads from it to its group's output. 594 nodes in 158 groups are not live.
- **Bundle analysis**: for every *Combine Bundle*, the keys it writes and which group inputs feed them (finding renamed keys); for every *Separate Bundle*, a data-flow trace back to the producing *Combine Bundle* through group boundaries, switches and bundle joins, following constant menu choices (such as `selector`'s `part`). This found every key read without a producer and gave the "read by" columns in [reference/parameter-groups.md](reference/parameter-groups.md).
- **Parameter slots**: every unlinked number, boolean, menu, string or vector input on a live node inside the GripV and GripX preset trees: 896 for GripV, 1,330 for GripX.
- **Cross-checks**: the stored export presets against the two preset JSON files; the 1,881 values in `tracking.json` against the file (all equal).

## Measurements

A harness evaluated a scene's view layer and read each object's evaluated mesh in world space: vertex, edge and face counts, bounding box, signed volume from the triangles, surface area, and the number of non-manifold edges. Evaluating a whole scene with the saved settings takes about half a second; hollow and lattice bodies take 7 to 12 seconds on their own and several times that when many jobs run at once.

1. **Baseline**: both scenes as saved, with `variant` set to match the scene ([reference/measurements.md](reference/measurements.md)).
2. **Global switches**: every value of every global menu and the opposite of every global boolean, one at a time, in both scenes ([3. Global switches](03-global-switches.md)).
3. **Parameter sensitivity**: every parameter slot changed once by a small step (numbers by +10 % or at least +0.2, angles by +0.1 rad, integers by +1, booleans flipped, menus set to each other item, strings and vectors altered), evaluated, compared with the baseline of its context, and reverted. Contexts: the saved settings, plus contexts that switch on the feature a slot belongs to (horizontal buttons off, marks on, stock bumpers, dpad stick on, capacitive plate and knob, body type hollow, lattice and indent with each fill type), and for GripX both styles. About 4,300 evaluations in total. Each run ends with a re-evaluation of the untouched baseline as a determinism check.
4. **Targeted combinations**: body types with other switches, tolerances with marks, stick presets, edge cases.
5. **Export dry run**: the add-on's own path and combination code, imported in Blender, listing every file each preset would write without exporting, compared with `orca_slicer/`, and MD5 hashes of all 383 committed STL files to find identical outputs.

## Known limits

- A "no change" result means that, in the tested context and with the tested step, no exported object changed. A parameter can still matter in a context that was not tested (for example a GripR1-only path or a combination of switches).
- The effect of a step says what a parameter does near its current value, not over its whole range.
- Volumes and sizes describe the mesh, not printability. Non-manifold edge counts are reported, but nothing was sliced.
- One bug in my own harness (vector values were not restored after a test) contaminated 15 test batches; they were rerun after the fix, and only batches whose final determinism check matched were used.
- The vertex counts of text marks and logos depend on the fonts installed on this machine.

## Second pass (2026-10-13)

The second pass ran in a Linux cloud container without a Blender installation, using the `bpy` 5.2.2 module from PyPI (the Blender 5.2.2 LTS build packaged as a Python module), headless, on `blender/Grip.blend` from the repository at commit `571e768`. As before, the file was only read and nothing was saved.

**Static dump.** A new dump of the file gave the same inventory as the first pass: 511 node groups, 298 objects, 190 collections, 64 groups used directly by modifiers, and the same 10 unreachable groups [measured]. The reference pages were generated from it:

- [reference/preset-values-GripV.md](reference/preset-values-GripV.md) and [reference/preset-values-GripX.md](reference/preset-values-GripX.md): every value of every live constructor node in the preset groups, in controls-panel order, with alternatives labelled by the menu item or frame they belong to and unconnected nodes marked;
- [reference/parameter-groups.md](reference/parameter-groups.md): the 54 constructor groups with interface defaults and bundle keys (renamed keys traced through the nodes between input and *Combine Bundle*);
- [reference/node-group-catalogue.md](reference/node-group-catalogue.md): all 511 groups by role. Its "release" count (462) is larger than the 437 of the first pass because it also follows *Object Info* and *Collection Info* references to cutter objects and counts every branch of every switch.

**Re-measurement of the first pass.** The baseline of both scenes matched the first pass to the last digit for every object compared (case halves, triggers, bumpers, buttons, caps, sticks, capacitive, battery cover, cable holder, pin), and so did the checked changes (`button height` +0.256, R4 `trigger length` 40 → 44, `hollow top`, `screws` off, `style` = dualsense) [measured]. Two differences:

- **Fonts.** The Windows fonts the file points at do not exist on Linux, so text marks produced no geometry: L1 and R1 came out identical (364 vertices) instead of 376 and 779. Measurements of mark inputs therefore come from the first pass only, and the vertex counts in [reference/measurements.md](reference/measurements.md) exclude marks.
- **Empty case bottom.** The GripX R4 `shift z` = 4.62 case that emptied the case bottom in the first pass did not reproduce with 5.2.2, at subdivision low or very high ([Issues](09-issues.md) B1).

**Sensitivity of the remaining parts.** Every parameter slot of the bumper, battery cover, screw, pin, scroll wheel and PCB presets was changed once with the same step rules as in the first pass, in the contexts: GripV and GripX xbox as saved, GripX dualsense (bumpers and screws), hollow bodies with the middle plate included (bumpers, cover, PCB, pins), and hollow bodies with `screws hollow` on (screws). That was 569 evaluations, run in four parallel processes. The 20 planned for the unconnected GripX "battery" cover frame in the hollow context were skipped, since that frame had no effect in the standard context. Each context ended by re-evaluating its baseline, and every one of these determinism checks gave identical results. A short list of targeted tests covered what the slot sweep cannot reach: the GripV bumper `stem radius` *Value* node, the curved-bumper inputs with `curved R1L1` on, curved bumpers on both GripX styles, `R1L1 flex` on GripX, the cable size nodes, `press tolerance` on both variants, every GripX stick preset, and `variant` = GripR1. One result needed a follow-up: the 2,000 mm³ jump of the GripV shell top with the screw end slot ([Issues](09-issues.md) B10) was checked with four more values of `screw end slot offset`, and the changed region was located by testing a 0.5 mm grid of points inside both meshes.

**Timing.** In this container (4 cores) a standard-body scene evaluated in about 2 s; hollow bodies took 40 to 60 s per evaluation with four processes running at once.
