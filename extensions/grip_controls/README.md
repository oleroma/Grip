# Grip Controls

A front panel for `blender/Grip.blend`. It adds a **Grip** tab to the 3D Viewport sidebar (press **N**) with the settings people change most: which controller is built, how smooth the preview is, how tight parts fit, the feature switches, and the main sizes and positions of triggers, bumpers, sticks, buttons and the battery compartment.

It does not replace the controls panel (`GripV controls`, `GripX contols`). Everything else is still there. The tab is a shortcut to the values you reach for most, without going into node groups.

Every field in the tab is the real node input, shown in another place. Changing it is exactly the same as changing it in the node editor: undo works, and `blender_tracking` records it in `blender/tracking.json` when you save. Hover the name of a setting to see what it does: the tab shows the tooltips stored in the file (written by `scripts/apply_tooltips.py`).

## Enable it

The add-on sits in the `extensions/` folder of the repository, next to `combi_export` and `blender_tracking`. If you already added that folder as a local repository, it is listed there:

1. Edit › Preferences › Get Extensions.
2. If the folder is not a repository yet: Repositories (the drop-down at the top right) › **+** › Add Local Repository, and choose the `extensions/` folder of your Grip clone.
3. Find **Grip Controls** in the list and enable it.

It needs Blender 5.2 or newer. In any other file than Grip.blend the tab only says that it is meant for Grip.blend.

## The panels

| Panel | What it is for |
|---|---|
| **Controller** | `variant`, `style` (GripX only) and `body type`, plus only the switches that matter for the chosen body (for example `fill type` for `indent`, `screws hollow` for shells). It warns when `variant` does not match the scene you are looking at, and has the variant sync (below). |
| **Preview quality** | `subdivision level` and `voxel resolution`. Keep both low while you edit; the export presets raise them on their own. |
| **Fit** | the three global menus `tolerance`, `press tolerance` and `cap tolerance`. Each part decides what tight, default and loose mean for itself; see [Fit and tolerances](../../docs/blender/customize/03-fit-and-tolerances.md). |
| **Features** | the global switches: `cable holder`, `stock bumpers`, wire cutouts, `horizontal buttons`, `button logo`, `marks`. |
| **Parts** | quick settings of the active variant (and, for GripX, the active style): R2 and R4 trigger length, width and position; bumper size and position; stick height, tilt range and top; the size of the four button families; the battery size. |

Each part box ends with a grey line that names the preset group and node it edits, and the last line of a part section names the frame of the controls panel where the rest of that part's settings are.

A greyed row means the tab will not edit that value:

- **"set by …"**: the input is connected to another node, so a typed value would do nothing. Edit the node it names in the controls panel (tolerances come from `tolerance set` nodes this way).
- **"not in this file", "node not found", "input not found"**: the name the tab looks for is not there, for example after a rename.
- **"several nodes, use the controls panel"** or **"preset not resolved"**: the tab could not tell for sure which node the preset uses, so it does not guess.

## Keep variant in step with the scene

Which controller is built is decided by the global `variant`, not by the scene you look at. If they differ, the GripX scene shows GripX parts built from GripV numbers, which looks broken.

- **Match variant to scene** (Controller panel) sets `variant` to the scene you are in, once.
- **Keep variant in step with the scene** (Controller panel, also in the add-on preferences, on by default) does it for you. It checks whenever you switch scene or workspace, and once after opening the file, and sets `variant` to the scene the window shows when that is `GripV` or `GripX`. It replaces the `Auto sync workspaces` text block, so you no longer need to run that script.

The sync only writes when the value is different. When two windows show GripV and GripX at the same time it does nothing, because it cannot tell which one you mean; use the button then. The export presets set `variant` themselves, so exports never depend on it.

## How it finds the nodes (for contributors)

The tab looks everything up by name, as spelled in the file (typos included: `wdith`, `stick heght`, `contols`). The names live in tables at the top of `resolve.py`:

- `PART_GROUPS`: the preset group of each part for GripV and GripX (`GripV  lever R1L1` has two spaces).
- `SECTIONS`: which constructor inputs each part section shows.
- `GLOBAL_INPUTS`: the inputs of `global` › `global parameters`.

A preset group can hold several nodes made from the same constructor. The tab picks the one that is used:

1. Only nodes whose output reaches the group output count. Unconnected leftovers, like the GripX cover nodes in frame "battery", are skipped. Nodes in frame "SNES" are never shown.
2. If two connected nodes remain (GripX triggers and bumpers, one per style), it takes the node that the `gripD` *Switch* passes on for the current style (False = xbox, True = dualsense). Without such a switch it takes the node in the frame labelled "GripX" (xbox) or "GripD" (dualsense).
3. GripX sticks pick a whole preset with a *Menu Switch*. The tab reads the selected item from the *Menu* node that drives it (`stick menu`, `Menu`), follows that item's input back to its *Join Bundle* and shows the constructors linked into it. It also shows the preset menu itself, so you can switch presets from the tab.

If any step finds nothing, or more than one node, the row is greyed with the reason instead.

The code is split so the lookups can be tested without drawing:

| File | Job |
|---|---|
| `resolve.py` | the name tables and the lookups. Reads only, except `set_variant`. |
| `ui.py` | the panels, the operators and the preferences. Drawing never writes and never raises; an unexpected error becomes a line in the panel. Each setting's name is a flat button (`grip.input_info`) whose tooltip is the description of the group input, because a plain field in a sidebar would only show Blender's generic socket tooltip. |
| `sync.py` | the variant sync: a message bus subscription on window scene and workspace switches, renewed after every file load. |

**After renaming** a group, node or input in Grip.blend, update the tables in `resolve.py` and run the tests. The tests check every name against `blender/tracking.json`, so a rename that is saved in the file but not in the tables fails there.

To **add a field**, add a `FieldSpec` to a block in `SECTIONS` (or a name to one of the global tuples) and run the tests.

## Tests

```
python -I extensions/grip_controls/tests/test_grip_controls.py
```

Use a Python with the `bpy` module of Blender 5.2 or newer. The tests do not open Grip.blend. They build node groups named like the real ones, enable the add-on from the `extensions/` folder the way a user does, and check what the panels find and draw, that drawing writes nothing, the variant sync and the clean-up when the add-on is disabled. Two groups follow the real file through `blender/tracking.json`: one checks that every path the add-on reads exists there, the other rebuilds the preset groups from the recorded nodes and links and runs the add-on's lookups on that real wiring (which trigger, bumper and cover node is used, every GripX stick preset, which inputs are linked).

## License

GPL 3.0 or later, see [LICENSE](LICENSE). The rest of the Grip repository is under CC BY-NC-SA 4.0.
