# 1. File structure

## Scenes

| Scene | Role |
|---|---|
| `GripV` | what is exported for GripV: its basemesh, the case halves, the middle plate and all parts |
| `GripX` | the same for GripX, with both style basemeshes (`basemesh_X_style`, `basemesh_D_style`) and `reinforcers` instead of the middle plate |
| `source` | every object in the file, including about 230 that appear nowhere else: cutters, hand-modelled pieces, placement empties, logo curves, reference models, old variants (`basemesh GripR1`, `basemesh GripS`), tests and an archive |

The scenes share collections rather than copying them. `parts` is one collection linked into several scenes, so a part is the same object in GripV and GripX; only the variant setting makes it different. Each scene has a workspace of the same name, and the GripV and GripX workspaces have node editors open on their controls panels.

Units are millimetres (unit scale 0.001), so exported STL coordinates are millimetres.

## Collections in the GripV and GripX scenes

```
basemesh GripV / basemesh GripX     ← excluded from the view layer; the case reads it through Collection Info
case middle plate                   ← GripV; excluded from the view layer (see Known issues)
case            case top, case bottom
parts
├ caps          home cap, abxy caps, select caps, dpad caps
├ buttons       one shaft per family: abxy, dpad, select, home
├ triggers      L2, R2, L4, R4
├ bumpers       L1, R1
├ capacitive, dpad stick (6 pieces), sticks, scrollwheel (3 pieces), battery cover, cable holder, pins, nut lock
reinforcers                         ← GripX
references      ← excluded: reference controllers, PCB and SMD models, M2.5 screws, the hidden object that holds the controls panel
```

Excluded collections are still evaluated when a node tree reads them, which is how the basemesh reaches the case. The exporter skips excluded collections, though.

## Which object uses which generator

Each printable object carries one Geometry Nodes modifier with its generator group. The modifier inputs say which variant of the generator's output the object wants. The same groups appear on the cutter objects in `source` with the flags flipped.

| Object(s) | Generator | Per-object inputs | Cutter in `source` |
|---|---|---|---|
| `case_top`, `case_bottom` | `case` | `case part` = top / bottom | — |
| `case_middle_plate` | `middle plate` | — | — |
| `abxy button`, `abxy cap …` | `abxy button` (+ `logo` on the caps) | `button`, `cap`, `Collection` (cap outline curves) | `abxy cutout …` (`button` off) |
| `dpad …`, `select …`, `home …` | `dpad button`, `select button`, `home button` | same pattern | `… cutout …` |
| `L2`, `R2`, `L4`, `R4` | `trigger` | `part` = R2/R4, `SMD button` = the board switch object, `left` = mirror | `R2 bool` (`trigger`), `R4 bool` (old group `R4`) |
| `L1`, `R1` | `lever R1L1` + a Bevel | `marks`, `left` | `R1L1 bool` (`lever R1L1 bool`) |
| `capacitive` | `capacitive plate` | `plate` = on | `capacitive plate cutout` |
| 6 D-pad stick pieces | `dpad stick` | `Menu` = which piece | `dpad stick bool` (`bool` on) |
| `StickL`, `StickR` | `stick module` → 2 Bevels → `top module` → `extra` | `Menu` = stick L / stick R | `StickL hole`, `Stick R hole` (`hole` on) |
| `scrollwheel`, `scrollwheel core` | `scrollwheel`, `scrollwheel stem` | — | `Wheel cutout (B)` (`scroll bool`) |
| `battery cover` | `cover` | `bool` = off | none: `bottom bools` builds the compartment with the group `coVer base`. The object `battery bool` (`bool` on) only feeds the shell's battery face. |
| `cable holder` | `MirrorX` → `cable hole` | — | — |
| `pin` | `pins` + 4 Bevels | `bool` = off | `pin bool` (`bool` on) |
| `nut lock`, `reinforcers` | `screws` | `nut lock` / `reinforcer` flag | `screw bools` (`screws`, no flag) |
| basemeshes | `MirrorX` → `subdivision surface` (GripV) or `subd` (GripX) | — | — |

Fixed cutters, meshes that follow no parameter, also live in `source`: the GripV stick cutouts, the USB openings, wire channels, clearances for board components (`LED`, `SMD`, `JST-2P (B)`), `battery wire space`, `jst2p pass`, the stock bumper cutouts and the pillars. They are listed per case half in [Case pipeline](03-case-pipeline.md#what-is-cut-from-each-half).

**Cutters must stay where they are.** Generated cutters are placed by their object transforms, like the parts, so moving a part means moving its cutter too.

## Hand-modelled inputs the generators read

Not everything is generated. Some of the nodes read hand-made objects and collections in `source` through *Object Info* and *Collection Info*:

| Data | Read by | Purpose |
|---|---|---|
| `basemesh …` objects | `basemesh variant` | outer shape of the case |
| `… cap curve …` collections | `button and caps` (with `custom cap`) | custom cap outlines, such as the D-pad arrows |
| `abxy logo …`, `home logo` | `logo` | cap symbols |
| `R1 lever profile`, `R1 flex profile`, `R1 … bool profile` | `lever R1L1 base` | 2D bumper profiles |
| `custom shape …` collections | `lever R1L1 base` | curved bumper outlines (the GripX xbox one is empty) |
| `R2_pcb_button`, `R4_pcb_button` | `trigger` | where each trigger's switch is |
| `scrollwheel` meshes | `scrollwheel`, `scrollwheel stem` | the wheel itself; the nodes only move tagged vertices |
| `pcb cutout` | `GripX pcb` → `pcb` | half outline of the board |
| `creases and curves` | `lattice` | the curves the lattice strips follow |
| `ribs gripv top`, `ribs gripx` | `ribs` | rib planes for shell tops |
| `align cut` empties | `align pins` | where shell bodies put their alignment pins |
| `… middle plate supports` | `inner supports` | support blocks for the middle plate, per variant and style |
| `top face` (`array.002`) | `top face` | the perforation pattern of shell tops |
| `gripx fill limit` | `fill limit` | where the indent pattern stops |

## Text blocks and add-on settings

- `Auto sync workspaces` (embedded script): once run, it sets the global `variant` when you switch workspace. It is not registered, so it only works after it has been run in the session.
- `rename.py` (external, `scripts/rename.py`): renames every group node after its node group.
- `apply_tooltips.py` (external, `scripts/apply_tooltips.py`): writes the tooltips (input descriptions) of `global parameters` and of every constructor that `tracking.json` records. The texts are a table in the script; run it again after editing the table. Names that are not found are tried with their typos corrected, so the table survives the name cleanup. `scripts/check_tooltips.py` checks the table against `tracking.json` without Blender.
- The scenes store settings of `combi_export` (export presets on GripV and GripX), `blender_tracking` (on `source`) and an external `w2g` add-on (workspace → variant mapping) that is not in the repository. See [Add-ons](05-add-ons.md).

## Fonts and materials

Fonts are loaded from Windows system paths and are not packed (see [Known issues](07-known-issues.md)). Materials (`case`, `button`, `stick`, `trigger`, …) only matter for rendering.
