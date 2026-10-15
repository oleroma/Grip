# Work on the node system

This guide is for contributors: people who want to fix something in `Grip.blend`, add a parameter or a part, or clean the file up. It explains how the file is organised and how the node trees work, and for each piece of structure, what it achieves in the design. For what individual parameters do, see the [customize guide](../customize/README.md); this guide links there instead of repeating it.

## The ideas the file is built on

Five design decisions explain most of the structure. Knowing them makes the node trees much easier to read.

1. **One generator per part, used twice.** Every part's node group can output the printable part *or* the shape of its opening in the case. The part object uses the generator with the part flag on. A hidden cutter object in the `source` scene uses the same group with the flag off, and the case subtracts it. Because both read the same numbers, a part and its opening can never drift apart. → [File structure](01-file-structure.md), [Part generators](04-part-generators.md)

2. **Numbers live apart from geometry.** No geometry group holds dimensions. They live in small *preset groups*, one per part and variant (`GripV abxy`, `GripX R2 parameters`, …), and travel to the geometry inside Blender bundles. A group called `selector` picks the right bundle for the current variant. The geometry groups are therefore the same for GripV and GripX, and a variant is just a set of presets plus a basemesh. → [Parameter system](02-parameter-system.md)

3. **The case is the basemesh minus everything else.** The outer shape is a hand-modelled half mesh. The case is that mesh split at Z = 40, built according to the body type, minus every part's cutter. Shell bodies first grow solid material around every opening, so the cuts always go through solid walls. → [Case pipeline](03-case-pipeline.md)

4. **Everything can be swept at export.** The export add-on can override any node input for one export, so tolerances, styles and options become folders of STL files without duplicating anything in the file. → [Add-ons](05-add-ons.md)

5. **Values are tracked as text.** The tracking add-on writes every preset value to `blender/tracking.json` on save, so changes to numbers show up in git. → [Add-ons](05-add-ons.md)

## Pages

| Page | What it covers |
|---|---|
| [1. File structure](01-file-structure.md) | scenes, collections, which object uses which generator, the `source` scene |
| [2. Parameter system](02-parameter-system.md) | global settings, presets, constructors, bundles, `selector`, styles, tolerance sets |
| [3. Case pipeline](03-case-pipeline.md) | basemesh to case halves, every cutter, how each body type is built |
| [4. Part generators](04-part-generators.md) | how each part's node group is built, step by step, and why |
| [5. Add-ons](05-add-ons.md) | `combi_export`, `blender_tracking`, the workspace sync |
| [6. Extending the file](06-extending.md) | adding a parameter, a preset, a part or a variant; checking a change; pitfalls |
| [7. Known issues](07-known-issues.md) | what is broken, fragile, unused or misnamed, with suggested fixes |

## Reading the node trees

- Group nodes are named after their group (the `rename.py` text block does that), so a node's name tells you which group it is.
- Frames inside preset groups are meaningful. In GripX they separate the xbox ("GripX") and dualsense ("GripD") settings; elsewhere they hold old alternatives.
- Node group and input names were cleaned of typos on 2026-10-15. Collections, labels, menu items and bundle items still carry a few (`Xbox syle`, `roker`, `caps fit Z olerance`). Search for them as spelled.
