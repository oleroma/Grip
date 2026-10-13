# 5. Add-ons

Two extensions in [`extensions/`](../../../extensions/README.md) work with the file. Both are developed in their own repositories and synced into Grip automatically, so do not edit the copies here.

## `combi_export`: export presets and sweeps

Source: [oleroma/combi_export](https://github.com/oleroma/combi_export). The presets are stored on the `GripV` and `GripX` scenes and mirrored in `blender/GripV_preset.json` and `blender/GripX_preset.json`.

**Model.** A preset lists collections, and each collection lists objects with an export tick, an optional output name, a sub-folder and a file-name tag. Overrides can sit at four levels (global, preset, collection, object). An override names a node input (group › node › input) or a modifier input, and gives a value, a list or a sweep (every menu item, both boolean states, or a number range).

**What an export does:**

1. Objects without overrides are written by the running Blender.
2. For objects with overrides, the add-on saves a temporary copy of the file and starts a headless Blender on it.
3. The worker goes through every combination of override values. For each one it writes the values into the sockets and updates the view layer. Then it takes each object's evaluated mesh in world space and writes a binary STL.
4. **Linked sockets are unlinked for the duration** and relinked afterwards. That is how a preset can force the D-pad stick switch inside `dpad stick parameters`, or pick a GripX stick preset by overriding the *Menu Switch* behind the `stick menu` node.
5. Excluded or disabled collections are skipped without an error. Objects hidden with the eye icon are briefly unhidden.

**Naming:** folder = preset prefix / collection sub-folder / object sub-folder / one folder per override value with its folder template on. File = object name (or output name) + `_tag` per override value with its tag template on. `*` is replaced by the value, and spaces become underscores.

**Design consequence:** because overrides target socket names, renaming a group, node or input breaks the presets that point at it. Update the presets (and their JSON copies) together with any rename.

## `blender_tracking`: `tracking.json`

Source: [oleroma/blender-tracking](https://github.com/oleroma/blender-tracking). Its settings are on the `source` scene. It tracks `GripV controls` and `GripX contols` one level deep (group nodes only), plus the `basemesh` collection. On every save it writes `blender/tracking.json` with:

- `tracked_inputs`: every input value of the preset groups in the two panels;
- `modifiers`: modifier inputs of objects that use those trees (empty here);
- `meshes`: a hash per basemesh of its transform, vertex positions and topology, so basemesh edits show up too;
- `all_node_trees`: the link list of every node group.

*Why:* a `.blend` cannot be diffed. This file makes every value change and every relinking visible in git and in pull requests. Keys are names, so renames show up as removed and added keys.

`GripR1 controls` is not tracked.

## Keeping `variant` in step with the workspace

The global `variant` is one setting, and the scenes do not set it. Two helpers exist:

- **`Auto sync workspaces`** (text block, embedded): once run, it listens for workspace changes and sets `variant` to GripX or GripV to match. It is not registered, so it needs running once per session.
- **`w2g`** (an add-on that is not in the repository): its settings on the scenes map the workspaces `GripV`, `GripX` and `Project` to values of `variant`.

The export presets set `variant` themselves, so exports never depend on either.

## Other add-on data in the file

Settings of a renaming add-on, Node Wrangler and a paint tool are stored on the scenes too. They do not affect geometry.
