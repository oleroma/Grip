# 1. Getting started

## What you need

- **Blender 5.2 or newer.** The file was saved in 5.2 and uses Geometry Nodes features that older versions do not have.
- **The extensions in [`extensions/`](../../../extensions/README.md)**: `combi_export` writes the STL files, `blender_tracking` records every parameter in `blender/tracking.json` when you save, and `grip_controls` adds the Grip tab ([below](#the-grip-tab)). Add the folder as a local extension repository (Preferences › Get Extensions › Repositories › Add Local Repository) and enable all three.
- **Git LFS**, because `Grip.blend` and the exported files are stored with it.
- **On macOS or Linux:** the text marks use the Windows font Segoe UI Bold. Without it the letters on parts are silently left out. Everything else works. See [Marks and logos](parts/marks-and-logos.md).

## The scenes

The file has three scenes, each with a workspace of the same name. You only need the first two:

| Scene | What it is for |
|---|---|
| `GripV` | everything that is printed for the GripV controller |
| `GripX` | the same for GripX. It holds both style basemeshes and the GripX-only `reinforcers` part. |
| `source` | the workshop: cutter shapes, hand-modelled pieces, placement markers, reference models and old experiments. You do not need it to customise or export. |

The scenes share their parts. There is one `abxy button` object, not one per scene, so a change made while looking at the GripV scene is a change to the same part in GripX.

## Choose the controller

Which controller is generated is decided by the global setting **`variant`**, not by the scene you are looking at. If `variant` does not match the scene, the GripX scene shows GripX objects built from GripV numbers, which looks broken. The export presets set `variant` themselves, so exports are always right.

With the Grip tab (below) you do not need to think about it: **Keep variant in step with the scene** is on by default and sets `variant` whenever you switch to the GripV or GripX scene. For GripX, pick `style` (`xbox` or `dualsense`) in the same panel.

Without the add-on, make them match by hand after opening the file:

1. Open the controls panel (below) and go into the `global` node.
2. Set `variant` to `GripV` in the GripV scene or `GripX` in the GripX scene.
3. For GripX, set `style` to `xbox` or `dualsense`.

The old way to automate this is the `Auto sync workspaces` script, run once per session (Text Editor › select it › Run Script). The Grip tab replaces it.

## The Grip tab

The `grip_controls` extension adds a **Grip** tab to the sidebar of the 3D Viewport (press **N** in the viewport). It is a front panel for the settings people change most, so you rarely need to go into node groups:

| Panel | What you set there |
|---|---|
| Controller | `variant`, `style`, `body type` and the switches that matter for that body. A button sets `variant` to the scene you are in. |
| Preview quality | `subdivision level` and `voxel resolution`: keep them low while you edit (see [below](#keep-blender-fast-while-editing)). |
| Fit | the three tolerance menus ([Fit and tolerances](03-fit-and-tolerances.md)) |
| Features | the global switches such as `cable holder`, `stock bumpers` and `marks` |
| Parts | for the active variant and style: trigger and back paddle length, width and position, bumper size and position, stick height, tilt range and top, the size of each button family, the battery size |

The fields are the node inputs themselves, so a change there is the same as a change in the node editor: undo works and saving records it in `tracking.json`. For GripX the tab edits the node of the current style, and for GripX sticks the preset picked in the stick menu, which it also shows. Each part box names the preset group and node it edits.

A greyed row is a value the tab will not edit, with the reason. "set by …" means the input is connected to another node; edit that node in the controls panel. Everything that is not in the tab is still in the controls panel, and each part section ends with the frame to look in. More in the add-on's [README](../../../extensions/grip_controls/README.md).

## The controls panel

Every setting you need is in one place: the node group **`GripV controls`** (for GripV) or **`GripX contols`** (for GripX, sic). It contains the `global` node and one node per part, sorted into frames:

| Frame | Preset groups inside |
|---|---|
| BUTTONS | `abxy`, `dpad`, `select`, `home` (each also holds the cap, outline and mark settings) |
| STICKS | `stick L parameters`, `stick R parameters` |
| R2R4 | `R2 parameters`, `R4 parameters` (triggers and back paddles) |
| R1L1 LEVER | `lever R1L1` (bumpers) |
| SCREWS | `screw paramters` |
| PINS | `pins parameters` (GripX: `pins`) |
| PCB AND BATTERY | `pcb cutout paramters`, `cover parameters` |
| SCROLLWHEEL | `scrollwheel` |
| DPAD STICK | `dpad stick` |
| pattern (GripX: FILL) | the patterns for the `indent` body type |
| shell (GripX: SHELL) | `hollow parameters` and the middle plate settings for shell bodies |

The GripV and GripX workspaces already have node editors that show this panel. If an editor shows something else, pin it (pin icon in its header) and then pick the panel from its node-group menu. Pinning first matters: in an unpinned editor that menu replaces the selected object's modifier.

To edit a part, select its preset node (for example `GripV abxy`) and press **Tab** to go inside. Then change the numbers on the constructor nodes there (`button parameters`, `caps parameters`, …). **Tab** again goes back out. A preset group is shared data, so editing it inside the panel edits the real part.

### When an edit does nothing

Three things make a value silently do nothing:

| Check | What to do |
|---|---|
| Is the input **connected to a link**? A linked input ignores the number typed on it. | Edit the node at the other end of the link. Tolerances come from `tolerance set` nodes this way. The GripV bumper `stem radius` comes from a separate *Value* node. |
| Is the node **connected at all**? Some presets keep old alternatives next to the live node. | Follow the node's output to the *Join Bundle*. Known unconnected ones: the GripV trigger nodes in frame "SNES", the GripX cover nodes in frame "battery", the `tolerance set` in `GripX lever R1L1`. |
| Is it the node the **current style or menu** uses? | GripX keeps one node per style for triggers, bumpers and the back screws (frames "GripX" = xbox, "GripD" = dualsense). GripX sticks keep several named presets behind a menu. |

## Keep Blender fast while editing

Leave these global settings low while you work (Grip tab › Preview quality). The export presets raise them on their own:

- `subdivision level` = low: the smoothness of the case.
- `voxel resolution` = low: the detail of shell bodies.
- `body type` = standard, unless you are working on shells. A hollow or lattice case takes seconds to tens of seconds to update after every change, and a standard case well under a second.

## Saving

When `blender_tracking` is enabled, saving writes `blender/tracking.json`. Every preset value is in it, so `git diff` on that file shows exactly what you changed. Check it before you commit.

## Next

- [Global settings](02-global-settings.md): what the switches in `global` do.
- [Fit and tolerances](03-fit-and-tolerances.md): making parts tighter or looser.
- The part pages, from the [guide index](README.md#parts).
