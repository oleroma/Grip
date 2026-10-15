# 6. Extending the file

Recipes for common changes, and the traps that make a change silently do nothing.

## Before you start

- **Match `variant` to the scene** you work in ([Getting started](../customize/01-getting-started.md#choose-the-controller)). Otherwise the GripX scene shows GripV numbers.
- **Keep evaluation fast:** `subdivision level` low, `voxel resolution` low, `body type` standard unless you work on shells.
- **Expect your change in `tracking.json`.** Review its diff before committing.

## Add a value a part can read

1. Add an input to the constructor (for example `trigger parameters`) and connect it to its *Combine Bundle*. The item name on the *Combine Bundle* is the key.
2. Add the same key to the *Separate Bundle* in the matching `… outputs` group (`trigger outputs`) and expose it as an output.
3. Use the output in the geometry group.
4. **Type the value in every preset that uses the constructor**: both variants, and both style nodes in GripX where they exist. A new input starts at its interface default.
5. Give it a tooltip: add a line for the input to `scripts/apply_tooltips.py`, check the table with `python scripts/check_tooltips.py` (it compares it with `tracking.json` after your save) and run the script in Blender.

Keys are matched by name, and a missing key quietly comes out as zero. So check the spelling on both sides, or the new value will do nothing without any error.

## Add a named alternative of a part (the GripX stick pattern)

GripX keeps several complete stick definitions in one preset group behind a *Menu Switch*:

1. Copy one frame of constructors (the six constructors and their *Join Bundle*).
2. Add a *Menu Switch* item and connect the new *Join Bundle*.
3. Pick it with the `stick menu` node, or add it to the export preset, which overrides the *Menu Switch*.

The same pattern works for any part, and it is the clean way to keep alternatives. Unconnected nodes in a frame look like settings but do nothing.

## Add a style-specific value

Put two constructor nodes in frames "GripX" and "GripD" and switch between them on `gripD` from `global outputs`, as the trigger and bumper presets do.

## Add a new part

1. Write the generator group: `selector` (with a new slot) → an `… outputs` group → geometry. Give it a flag for the cutter version (`bool` or `button`) so the case opening comes from the same numbers.
2. Add a slot:
   - add an input to `parts bundle` and an item to its *Combine Bundle*;
   - add the item to the *Separate Bundle* in `selector` and to its *Menu Switch*;
   - add the preset group to every variant parameter group and connect it.
3. Write a constructor group and one preset group per variant.
4. Add the part object (flag on) to `parts`, and the cutter object (flag off) to `source`. Add the cutter to `top bools` or `bottom bools`, and for shell bodies to `button shafts sdf` if the opening needs a boss.
5. Put the preset in the controls panels so it is tracked, and add the part to an export preset.

## Add a new variant

What has to change, based on how the current variants are wired:

- a basemesh (half model, with `MirrorX` and subdivision modifiers) in a collection that `basemesh variant` can pick;
- a variant parameter group (`GripN parameters`) with presets for all 22 slots, added to the *Index Switch* in `selector`;
- a new item in the global `variant` menu and its index in `global parameters`;
- every per-variant switch: the `part variant switching` groups (stick cutouts, bumper cutouts, curved bumper outlines, middle plate supports) and the variant switch inside `ribs`;
- a scene and workspace, a controls panel added to `controls` and to the tracking settings, and export presets.

## Change the split height

Z = 40 is a constant in `cut basemesh`, `plate`, `offset basemesh and slice`, `insert rim` and `pattern field`, and a constant 40 also appears in `screw`. Pin heights (`Z` in the pin presets) and the GripV stick cutout meshes also assume it. Change them all together, or better, make it one global value first.

## Check a change

- Look at the part **and** at `case_top` / `case_bottom`. Most part inputs also move a cutter.
- For shells, switch to `hollow` or `lattice` only after the solid version looks right.
- From the command line, `bpy` (the Blender Python module, `pip install bpy`) can open the file headless. It can evaluate a scene and read each object's mesh, so you can compare vertex count, bounding box, volume and non-manifold edges before and after a change. Unhide eye-hidden objects first, or their evaluated mesh is empty.
- Watch for non-manifold meshes after trigger edits. The case is cut with the Manifold boolean solver, which expects closed meshes, and in one Blender build a trigger value made a case half disappear.

To check the numbers, save and run `python tools/tracking_diff/tracking_diff.py blender/tracking.json`. It lists every value that changed since your last commit, by controller, preset group and node, and names edited basemeshes and rewired node groups. That shows whether only the values you meant to change moved, and whether a rename came through as a rename and not as a lost value. Pull requests that change `tracking.json` get the same list on the summary page of the *Parameter changes* workflow run. See [Tracking diff](../../../tools/tracking_diff/README.md).

## Pitfalls

- **Linked inputs ignore typed values.** Edit the node at the other end. The GripV bumper `stem radius` is the classic case.
- **Shared groups.** Values typed on a constructor node belong to that preset. Anything *inside* a constructor group, such as the *Menu Switch* in `capacitive plate parameters` or the *Combine Bundle* in `dpad stick parameters`, is shared by every preset that uses it. `cable holder parameters` has no inputs, so its value is shared by all variants.
- **Renames.** Links and modifier values use socket identifiers and survive a rename. `tracking.json` keys, export-preset overrides and bundle keys use names and do not. Rename the bundle key on both sides, and update the export presets and their JSON copies.
- **`horizontal buttons` off** gives unstable buttons. Do not develop against it.
- **`fill type` = manual** destroys the case.
- **Fonts** are Windows system fonts. Pack them before relying on text on other systems.

## Cleanup conventions

The node group and input names were cleaned of typos with `scripts/fix_names.py`. The file still carries typos in collections, labels, menu items and bundle items (`Xbox syle`, `roker`, `caps fit Z olerance`, …), automatic `.001` names on real alternatives, and leftovers of GripR1 and older designs. The list is in [Known issues](07-known-issues.md#d-leftovers-and-naming). When fixing a name, rename it in the `.blend`, the export presets and `tracking.json` in one change, so the diff shows a rename and not a lost value.
