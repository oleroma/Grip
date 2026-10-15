# Printed parts

<!-- The print lists below match tools/release/print_sets.json. Change both together. -->

This folder holds every printable part of Grip, exported from `blender/Grip.blend` as `.stl` files, plus a few OrcaSlicer projects (`.3mf`). This page tells you which files to print for each shape, how many of each, and which tolerance folder to start with.

> **Files that look empty?** The models are stored with Git LFS. An `.stl` of about 130 bytes that starts with `version https://git-lfs` is a pointer, not the model. Clone the repository with Git LFS as the [main readme](../readme.md#lfs-and-file-download) explains.

- [Pick a shape](#pick-a-shape)
- [What is in each folder](#what-is-in-each-folder)
- [Tolerances](#tolerances)
- [Print list: GripV standard and GripV hollow](#print-list-gripv-standard-and-gripv-hollow)
- [Print list: GripX xbox and GripX dualsense](#print-list-gripx-xbox-and-gripx-dualsense)
- [Known gaps](#known-gaps)
- [Release zips](#release-zips)

## Pick a shape

| Shape | What it is | Case files | All other parts |
| --- | --- | --- | --- |
| **GripV standard** | the custom ergonomic "pistol-like" shape: a solid case bottom with a thin shell top, held together with screws | `GripV/case_standard/` | `GripV/parts/` |
| **GripV hollow** | the same shape as thin shells that clip onto a middle plate carrying the board; lighter, and also suited to resin and powder printing | `GripV/case_hollow/` | `GripV/parts/` |
| **GripX xbox** | the classic Xbox-style shape, solid, held together with screws | `GripX/xbox_style/` | `GripX/parts/`, plus triggers and bumpers in `GripX/xbox_style/` |
| **GripX dualsense** | the classic DualSense-style shape, solid, held together with screws | `GripX/dualsense_style/` | `GripX/parts/`, plus triggers and bumpers in `GripX/dualsense_style/` |

Every part is made for its variant, so do not mix files from `GripV/` and `GripX/`. The two GripX styles share everything in `GripX/parts/`.

## What is in each folder

### Case tops

Each case folder has one `case_bottom.stl` and four tops. Print the bottom and **one** top. The top's name says which D-pad and which capacitive part it takes, and you print the matching parts with it:

| Case top | D-pad | Capacitive part |
| --- | --- | --- |
| `case_top_cap_knob.stl` | four D-pad caps | the knob |
| `case_top_cap_plate.stl` | four D-pad caps | the plate |
| `case_top_dpad_stick_cap_knob.stl` | the rocker D-pad (D-pad stick) | the knob |
| `case_top_dpad_stick_cap_plate.stl` | the rocker D-pad (D-pad stick) | the plate |

The capacitive part sits in the middle of the face buttons, probably as a touch surface for a sensor on the board. The knob is a small round part between the face buttons; the plate is a plate around them.

### GripV/

| Folder or file | What is in it |
| --- | --- |
| `case_standard/`, `case_hollow/` | the case bottom and the four tops of each version |
| `parts/buttons/<tolerance>/` | `button.stl`, the button shaft, and in `cap_<cap tolerance>/` the caps: one per face button symbol (`triangle`, `circle`, `cross`, `square`), `dpad`, `select` and `home` |
| `parts/triggers/<tolerance>/press_<press tolerance>/` | the triggers L2 and R2 and the back paddles L4 and R4 |
| `parts/bumpers/press_<press tolerance>/` | the bumpers L1 and R1 |
| `parts/sticks/<top>/<curvature>/<texture>/` | thumbsticks: a `circle` or `square` top, `concave`, `convex` or `flat`, with a `grid` or `icosahedron` grip texture, each as `stick_<range>_deg.stl` for a tilt range of 10 to 20 degrees |
| `parts/capacitive/` | the capacitive part as a knob or a plate |
| `parts/dpad_stick/` | the six pieces of the rocker D-pad |
| `parts/scrollwheel/` | the scroll wheel: wheel, core and holder |
| `parts/battery_cover/`, `parts/cable_holder/`, `parts/pins/` | small parts |
| `parts/misc/` | `nut_lock.stl` (optional) and `pin.stl`, a copy of `parts/pins/pin.stl` |
| `GripV_case_standard.3mf`, `GripV_case_hollow.3mf`, `GripV_parts.3mf` | OrcaSlicer projects with the parts laid out on plates |
| `GripV_case_za3tarani.3mf` | probably a case made for one tester; not part of a print list |

### GripX/

| Folder | What is in it |
| --- | --- |
| `xbox_style/`, `dualsense_style/` | the case bottom and four tops of each style, with that style's `triggers/<tolerance>/press_<press tolerance>/` and `bumpers/pres_<press tolerance>/` |
| `parts/buttons/<tolerance>/` | the button shaft and caps, laid out as on GripV |
| `parts/sticks/StickL/` | left sticks, one file per design: `Xbox_cap`, `Xbox_cap_easy_print_tall`, `Xbox_cap_easy_print_short_(60%)`, `Octagonal_18d_range` and `Xbox_Elite2_stick_base` |
| `parts/sticks/StickR/` | right sticks: `normal/` (concave, convex or flat), `small_round`, `small_square` and `8_dir` |
| `parts/capacitive/`, `parts/dpad_stick/`, `parts/battery_cover/`, `parts/cable_holder/`, `parts/pins/` | as on GripV |

GripX has no OrcaSlicer projects yet.

### dongle_case/

`GripV_shell_dongle_case.3mf` is probably a small case for a USB dongle. It is not part of a controller.

## Tolerances

Parts that slide, click or clip into each other come in three fits, `tight`, `default` and `loose`, because every printer makes holes and pins a little differently. The parts were tuned on a Bambu Lab A1 with a 0.4 mm nozzle and 0.16 mm layers, so `default` is the best start on a similar printer.

The folder names say which of the three tolerance settings in `Grip.blend` made a file:

| Folder | Setting | Parts | What a looser fit changes |
| --- | --- | --- | --- |
| `tight/`, `default/`, `loose/` | `tolerance` | button shafts (`buttons/<tolerance>/`) and triggers (`triggers/<tolerance>/`) | more room between the shaft and its hole in the case, and between the trigger and its opening |
| `cap_tight/`, `cap_default/`, `cap_loose/` | `cap tolerance` | caps | the cap clips on more easily and holds less firmly |
| `press_tight/`, `press_default/`, `press_loose/` | `press tolerance` | triggers (GripV and GripX) and the GripV bumpers | the end that presses the switch is trimmed more, which probably gives more free play before the click |
| `pres_tight/`, `pres_default/`, `pres_loose/` | `press tolerance` | the GripX bumpers | the same setting under another spelling. For now these three folders hold the same file. |

A path combines them. `buttons/default/cap_tight/cross.stl` is a cross cap with a firm clip, made for the `default` shaft. `triggers/loose/press_default/R2.stl` is an R2 that slides loosely, with the default press travel.

### Start with default, reprint only what does not fit

1. Print every part from its `default` folders: `buttons/default/button.stl`, the caps in `buttons/default/cap_default/`, the triggers in `triggers/default/press_default/` and the bumpers in `bumpers/press_default/` (GripX: `bumpers/pres_default/`).
2. Test the fit. If one part does not fit, reprint only that part from the neighbouring folder. The case stays: these settings change the part, not its opening in the case.

| If | Print |
| --- | --- |
| a button shaft sticks in its hole | the shaft from `loose/`, and its caps from `loose/` too |
| a button shaft wobbles | the shaft from `tight/`, and its caps from `tight/` too |
| a cap falls off | the cap from `cap_tight/`, in the same `<tolerance>` folder as its shaft |
| a cap does not go on, or cracks | the cap from `cap_loose/`, in the same `<tolerance>` folder as its shaft |
| a trigger rubs or sticks in its opening | the trigger from `triggers/loose/` |
| a trigger rattles | the trigger from `triggers/tight/` |
| a trigger or bumper has a lot of free play before it clicks | the part from `press_tight/` (probably) |
| a trigger or bumper clicks on its own or has no travel | the part from `press_loose/` (probably) |

**Caps belong to their shaft.** A cap in `buttons/<tolerance>/` is made for the shaft in the same folder. When you change the shaft, reprint its caps from the new folder.

On GripX some neighbouring folders hold the same file for now, so reprinting them changes nothing: the three `cap_*` folders, the trigger folders `default/` and `loose/`, and the three bumper `pres_*` folders. To get a different fit there, change the part in `Grip.blend` and export it ([Fit and tolerances](../docs/blender/customize/03-fit-and-tolerances.md)).

## Print list: GripV standard and GripV hollow

Paths are under `GripV/`, shown for the `default` tolerance. "Only with" means the part depends on the case top you picked. Quantities marked *probably* are not confirmed.

| Qty | Part | File | Notes |
| ---: | --- | --- | --- |
| 1 | Case bottom | `case_standard/case_bottom.stl` or `case_hollow/case_bottom.stl` | |
| 1 | Case top | one of the four tops in the same folder | see [Case tops](#case-tops) |
| 1 | Middle plate | **not exported yet** | hollow only |
| 4 | Shaft for A, B, X and Y | `parts/buttons/default/button.stl` | |
| 4 | Shaft for the D-pad | `parts/buttons/default/button.stl` | only with a D-pad caps top. *Probably* right: same `curve parameters` and `button parameters` as ABXY, but two cap settings that may also shape the clip on the shaft differ |
| 1 | Shaft for Home | **not exported yet** | Home has its own shaft (`middle bevel` differs, and so does `caps flex cut`, which may also shape the clip on the shaft). The ABXY `button.stl` has the same outline and probably works until then (not tested). |
| 4 | Shaft for Select | **not exported yet** | the Select buttons are narrower than ABXY |
| 1 each | Caps for the face buttons | `parts/buttons/default/cap_default/` `triangle.stl` (top), `circle.stl` (right), `cross.stl` (bottom), `square.stl` (left) | |
| 4 | D-pad cap | `parts/buttons/default/cap_default/dpad.stl` | only with a D-pad caps top; one outline turned four ways |
| 4 | Select cap | `parts/buttons/default/cap_default/select.stl` | *probably* 4 of the same: the file has four Select caps that share one preset |
| 1 | Home cap | `parts/buttons/default/cap_default/home.stl` | |
| 1 | Capacitive knob or plate | `parts/capacitive/capacitive_knob.stl` or `capacitive_plate.stl` | the one your case top names |
| 1 each | Triggers L2, R2 and back paddles L4, R4 | `parts/triggers/default/press_default/` | |
| 1 each | Bumpers L1, R1 | `parts/bumpers/press_default/` | |
| 2 | Stick | `parts/sticks/<top>/<curvature>/<texture>/stick_<range>_deg.stl` | one per side. Both holes are the same, so you can print one design twice or two different ones. The range is the tilt the stick's neck is shaped for. |
| 1 each | Rocker D-pad: cap, stick, rocker, rocker ball, ball support, rocker support | `parts/dpad_stick/` | only with a `dpad_stick` top |
| 1 each | Scroll wheel: wheel, core, holder | `parts/scrollwheel/` | exported by hand, so they can be older than the Blender file |
| 1 | Battery cover | `parts/battery_cover/battery_cover.stl` | |
| 1 | Cable holder | `parts/cable_holder/cable_holder.stl` | *probably* needed, see [Known gaps](#known-gaps) |
| 2 | Alignment pin | `parts/pins/pin.stl` | standard only, one per side. The hollow shells line up on pins of the middle plate. |
| 2 | Nut lock (optional) | `parts/misc/nut_lock.stl` | a small wedge made from the front screw settings, probably to hold a front nut in its slot, so *probably* one per front screw |

**Not printed:** four M2.5 DIN 912 socket-head screws with nuts (the [printing guide](../docs/print-guide.md) recommends them for the hollow version too, for now) and the electronics: board, joystick modules, battery and cable.

The OrcaSlicer projects `GripV_case_standard.3mf`, `GripV_case_hollow.3mf` and `GripV_parts.3mf` hold these parts laid out on plates, probably with the `default` files. If a part was exported again after a project was saved, the `.stl` is the newer one.

## Print list: GripX xbox and GripX dualsense

Paths are under `GripX/`, shown for the `default` tolerance. `<style>` is `xbox_style` or `dualsense_style`.

| Qty | Part | File | Notes |
| ---: | --- | --- | --- |
| 1 | Case bottom | `<style>/case_bottom.stl` | |
| 1 | Case top | one of the four tops in `<style>/` | use a `cap_plate` top for now: `parts/capacitive/capacitive_knob.stl` is still the plate |
| 4 | Shaft for A, B, X and Y | `parts/buttons/default/button.stl` | |
| 4 | Shaft for the D-pad | **not exported yet** | only with a D-pad caps top. The GripX D-pad has its own corner rounding (`fillet`), so it needs its own shaft. A `dpad_stick` top does not need them. |
| 1 | Shaft for Home | **not exported yet** | its own `fillet` |
| 4 | Shaft for Select | **not exported yet** | the Select buttons are narrower than ABXY |
| 1 each | Caps for the face buttons | `parts/buttons/default/cap_default/` `triangle.stl` (top), `circle.stl` (right), `cross.stl` (bottom), `square.stl` (left) | |
| 4 | D-pad cap | `parts/buttons/default/cap_default/dpad.stl` | only with a D-pad caps top; one outline turned four ways |
| 4 | Select cap | `parts/buttons/default/cap_default/select.stl` | *probably* 4 of the same |
| 1 | Home cap | `parts/buttons/default/cap_default/home.stl` | |
| 1 | Capacitive plate | `parts/capacitive/capacitive_plate.stl` | `capacitive_knob.stl` is currently the same file as the plate |
| 1 each | Triggers L2, R2 and back paddles L4, R4 | `<style>/triggers/default/press_default/` | |
| 1 each | Bumpers L1, R1 | `<style>/bumpers/pres_default/` | |
| 1 | Left stick | one file from `parts/sticks/StickL/` | the left and right holes differ in size, so take one stick from each folder |
| 1 | Right stick | one file from `parts/sticks/StickR/` or `parts/sticks/StickR/normal/` | |
| 1 each | Rocker D-pad: cap, stick, rocker, rocker ball, ball support, rocker support | `parts/dpad_stick/` | only with a `dpad_stick` top |
| 1 each | Scroll wheel: wheel, core, holder | **not exported yet** | the GripX case probably has the slot |
| 1 | Battery cover | `parts/battery_cover/battery_cover.stl` | |
| 1 | Cable holder | `parts/cable_holder/cable_holder.stl` | *probably* needed, see [Known gaps](#known-gaps) |
| 2 | Alignment pin | `parts/pins/pin.stl` | one per side |

**Not printed:** four M2.5 DIN 912 socket-head screws with nuts, and the electronics: board, joystick modules, battery and cable.

## Known gaps

The release is still a beta. These parts are missing or not confirmed yet:

- **Button shafts.** Only the ABXY shaft (`button.stl`) is exported. The Select shafts (every shape), the Home shaft (every shape) and the GripX D-pad shafts are made from presets that differ from ABXY, so they need their own export: `select button`, `home button` and `dpad button` ([Buttons and caps](../docs/blender/customize/parts/buttons-and-caps.md#export)).
- **GripV middle plate.** The "Case hollow" export skips it, because the GripV view layer excludes its collection ([Exporting](../docs/blender/customize/05-exporting.md#known-problems)).
- **GripV hollow screws.** The printing guide recommends screws for the hollow case for now. The "Case hollow" export does not turn on `screws hollow` (the screw bosses of shell bodies) and the saved file has it off, so the exported shells probably have no screw bosses. Check yours before you buy screws.
- **GripX capacitive knob.** `GripX/parts/capacitive/capacitive_knob.stl` was exported before the preset was fixed and is really the plate.
- **GripX scroll wheel.** The GripX case probably has the scroll wheel slot (the slot is not switched per variant), but only GripV's wheel is exported, and the GripX wheel has its own `scroll wheel shift X` and `scroll wheel tolerance`.
- **GripX tolerance folders.** The `cap_*` folders, the trigger folders `default/` and `loose/`, and the bumper `pres_*` folders hold the same files.
- **Cable holder.** It only fits a case exported with the global `cable holder` setting on. The export presets do not set it and the saved file has it on, so the exported cases probably have the opening for it.

To see the file problems at a glance, run `python tools/release/build_release.py --check` from the repository folder.

## Release zips

For a release, each shape is packed into its own zip with only its files, a `PRINT_LIST.md` with the list above and the license. The paths inside are the same as here. See [tools/release](../tools/release/README.md) for how they are built.
