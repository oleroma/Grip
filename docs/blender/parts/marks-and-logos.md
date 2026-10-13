# Marks and logos

Two separate systems put relief or engraving on parts: **marks** (small identification letters on buttons, triggers and bumpers) and **logos** (the symbols on the ABXY and Home caps).

## Marks

The group `marks` takes the part geometry, a bundle (the part's preset) and two flags, `marks` and `mirror`, and engraves or embosses text or curves on one face of the part [wiring]. Where it is switched on:

| Parts | Switched by | As saved |
|---|---|---|
| button shafts (all four families), triggers L2/R2/L4/R4 | global `marks` | off |
| bumpers L1/R1 | the `marks` input on their `lever R1L1` modifier | **on** |

What is written comes from the part's `marks parameters` node [wiring]:

| `type` | Text |
|---|---|
| `custom` with `L-R side` off | the string from a small *Index Switch* next to the node: `T`, `D` or `L` |
| `custom` with `L-R side` on | `R`, or `L` when the part is mirrored (left side) |
| `parameter` | the values of the bundle keys listed in `parameters` (comma separated), with `Decimals` digits |
| `curve` | the curves in collection `case mark custom` (the Grip logo) |

All presets use `custom` [wiring]:

| Preset | `L-R side` | Result |
|---|---|---|
| GripV / GripX abxy, dpad, select, home | off | `T` |
| GripV R2, R4 | on | `R` / `L` |
| GripX R2, R4 | off | `T` |
| GripV / GripX lever R1L1 | on | `R` / `L` |

The *Index Switch* that picks `T`/`D`/`L` has its index typed as 0 and **is not connected to any tolerance menu**, so every part prints `T` whatever tolerance it was exported with [wiring]. Consistent with that, with marks on the ABXY shaft carries the same mark (+16 vertices) at tight, default and loose `tolerance`, and R1 has the same 779 vertices at every press tolerance; setting that *Index Switch* to 1 instead turns the mark into a `D` (+164 vertices compared with the `T`), and `type` = `parameter` prints the number instead (+1,450 vertices on the ABXY shaft) [measured]. The `parameters` field already names the right values (`button tolerance`, `trigger x tolerance, button press tolerance`, …) [wiring], so `parameter` mode is the ready-made way to label exported tolerance variants.

Other inputs: `bump` and `mark depth` (relief height and engraving depth, 0.16 each in all presets), `insertion` (off), `font size` (5), `translate` / `rotate` / `axis` / `side` (where on the part the mark goes: the face at the min or max of the given axis), and the text layout inputs `Character Spacing`, `Word Spacing`, `Line Spacing`, `Text Box Width` [wiring]. The font is fixed to Segoe UI Bold inside `marks parameters` [wiring]; on a machine without that Windows font the marks are not generated at all and Blender only prints a console warning [measured on Linux, see [Issues](../09-issues.md) B7]. Measured: global `marks` on adds about 16 vertices and removes about 0.2 mm³ on each button shaft and 20–330 vertices on the triggers [measured].

L1 and R1 differ in vertex count as saved (GripV 376 vs 779) because one carries an `L` and the other an `R`: with their `marks` input off both become identical (364 vertices, 1,870.70 mm³), so the `L` adds 12 vertices and the `R` 415 [measured].

## Logos

The ABXY caps and the Home cap have a second Geometry Nodes modifier using the group `logo`; the button shafts carry one too [wiring].

| Object | `logo` modifier | Type | Source |
|---|---|---|---|
| `abxy cap up / down / left / right` | on | `custom` | collections `abxy logo up` … (curves) |
| `home cap` | on | `custom` | collection `home logo` |
| `abxy button`, `dpad button` | **disabled in the viewport** (so not exported) | text `A` | — |
| `select button`, `home button` | on, but error **"Font not specified"**; disabling these modifiers changes nothing [measured] | text `A`, no font | — |

`logo` is gated by the global `button logo` (on as saved): off returns the cap unchanged [wiring]. Turning it off made the four ABXY caps identical (2,358 vertices, 183.1 mm³) and the Home cap +3.3 mm³, so the logos are engraved [measured]. The D-pad and Select caps have no logo. Inputs: `depth` (0.16 on caps), `bump` (0.16), `insertion`, `type` (text / custom), `Collection`, `text`, `font size`, `font`, `rotate text`, `translate text`, `rotate`, `translate`, and a hidden `cap` flag (on for caps) [wiring].

The fonts referenced by the text-type logos are Windows system fonts (`Segoe UI Bold`, `Arial Bold`, `Amiri Bold`, …) [wiring]; on a machine without them the text logos would fail, but no exported part uses a text logo [inferred from the table above].
