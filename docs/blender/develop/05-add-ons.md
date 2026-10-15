# 5. Add-ons

Three extensions in [`extensions/`](../../../extensions/README.md) work with the file. `combi_export` and `blender_tracking` are developed in their own repositories and synced into Grip automatically, so do not edit the copies here. `grip_controls` lives in the Grip repository and is edited here.

## `combi_export`: export presets and sweeps

Source: [oleroma/combi_export](https://github.com/oleroma/combi_export). The presets are stored on the `GripV` and `GripX` scenes and mirrored in `blender/GripV_preset.json` and `blender/GripX_preset.json`. combi_export rewrites both every time the file is saved (*Save JSON with File*, the tick icon next to the JSON buttons in the Root row, on by default). Each also lists, under `exports`, every file its presets write, which the [release builder](../../../tools/release/README.md) checks the print sets against.

**Model.** A preset lists collections, and each collection lists objects with an export tick, an optional output name, a sub-folder and a file-name tag. Overrides can sit at four levels (global, preset, collection, object). An override names a node input (group › node › input) or a modifier input, and gives a value, a list or a sweep (every menu item, both boolean states, or a number range).

**What an export does:**

1. Objects without overrides are written by the running Blender.
2. For objects with overrides, the add-on saves a temporary copy of the file and starts a headless Blender on it.
3. The worker goes through every combination of override values. For each one it writes the values into the sockets and updates the view layer. Then it takes each object's evaluated mesh in world space and writes a binary STL.
4. **Linked sockets are unlinked for the duration** and relinked afterwards. That is how a preset can force the D-pad stick switch inside `dpad stick parameters`, or pick a GripX stick preset by overriding the *Menu Switch* behind the `stick menu` node.
5. Excluded or disabled collections are skipped without an error. Objects hidden with the eye icon are briefly unhidden.

**Naming:** folder = preset prefix / collection sub-folder / object sub-folder / one folder per override value with its folder template on. File = object name (or output name) + `_tag` per override value with its tag template on. `*` is replaced by the value, and spaces become underscores.

**Design consequence:** because overrides target socket names, renaming a group, node or input breaks the presets that point at it. Update the presets together with any rename; their JSON copies follow on the next save.

## `blender_tracking`: `tracking.json`

Source: [oleroma/blender-tracking](https://github.com/oleroma/blender-tracking). Its settings are on the `source` scene. It tracks `GripV controls` and `GripX controls` one level deep (group nodes only), plus the `basemesh` collection. On every save it writes `blender/tracking.json` with:

- `tracked_inputs`: every input value of the preset groups in the two panels;
- `modifiers`: modifier inputs of objects that use those trees (empty here);
- `meshes`: a hash per basemesh of its transform, vertex positions and topology, so basemesh edits show up too;
- `all_node_trees`: the link list of every node group.

*Why:* a `.blend` cannot be diffed. This file makes every value change and every relinking visible in git and in pull requests. Keys are names, so renames show up as removed and added keys. [`tools/tracking_diff`](../../../tools/tracking_diff/README.md) turns a change of the file into a readable list.

`GripR1 controls` is not tracked.

## `grip_controls`: the Grip tab

Source: [`extensions/grip_controls`](../../../extensions/grip_controls/README.md), in this repository. It adds a **Grip** tab to the 3D Viewport sidebar with the settings people change most (variant, preview quality, the three tolerance menus, the feature switches and the main sizes of triggers, bumpers, sticks, buttons and the battery), and it keeps `variant` in step with the scene (next section).

*Why:* each controls panel holds hundreds of inputs, and a common edit means finding the right preset group, style node and constructor first. The tab is a shortcut, not a copy: every field is the real node input, so undo, `tracking.json` and the export presets see no difference.

**Lookups by name.** The tab finds preset groups, constructors and inputs by name, from tables at the top of `resolve.py`, spelled as in the file (typos and double spaces included). Where a preset group holds several nodes of one constructor, it only counts nodes whose output reaches the group output, then picks the GripX style node through the `gripD` *Switch* or the frame label ("GripX", "GripD"), and the GripX stick preset through the *Menu* behind the *Menu Switch*. When that finds nothing or more than one node, or the input is linked, the row is greyed with the reason instead of guessing.

**Design consequence:** like the export presets, the tab breaks on renames. After renaming a group, node or input, update the tables in `resolve.py` and run the add-on's tests, which check every name it reads against `blender/tracking.json`.

## Keeping `variant` in step with the scene

The global `variant` is one setting, and the scenes do not set it. If it does not match the scene, the GripX scene shows GripX objects built from GripV numbers.

- **The Grip tab's sync** (`grip_controls`, on by default) does this now. It subscribes to scene and workspace switches of a window through the message bus, renews the subscription after every file load, and syncs once after opening. It sets `variant` to the scene the windows show when that is `GripV` or `GripX`, writes only when the value differs, and does nothing when two windows show different Grip scenes. A button in the tab syncs once by hand.
- **`Auto sync workspaces`** (text block, still embedded) is the older helper it replaces: once run, it listens for workspace changes and sets `variant` to match. It is not registered, so it needs running once per session.
- **`w2g`** (an add-on that is not in the repository): its settings on the scenes map the workspaces `GripV`, `GripX` and `Project` to values of `variant`. They are still stored in the file.

The export presets set `variant` themselves, so exports never depend on any of these.

## Other add-on data in the file

Settings of a renaming add-on, Node Wrangler and a paint tool are stored on the scenes too. They do not affect geometry.
