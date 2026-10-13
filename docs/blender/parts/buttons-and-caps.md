# Buttons and caps (ABXY, D-pad, Select, Home)

Four button families share one generator. Each family has one **button** object (the shaft that sits on the PCB switch), its **caps** (the finger surfaces that clip onto the shaft) and, in the `source` scene, its **cutter** objects (the holes in the case top). All three are made by the same modifier group with different flags, so a hole always matches its button [wiring].

| Family | Button object | Cap objects | Cutters (`source`) | Modifier group |
|---|---|---|---|---|
| ABXY | `abxy button` | `abxy cap up / down / left / right` | `abxy cutout …` | `abxy button` → `abxy` |
| D-pad | `dpad button` | `dpad cap up / down / left / right` | `dpad cutout …` | `dpad button` → `dpad` |
| Select (4 small buttons) | `select button` | `select cap top left / top right / down left / down right` | `select cutout …` | `select button` → `select` |
| Home | `home button` | `home cap` | `home cutout` | `home button` → `home` |

Modifier inputs per object: `button` (on for buttons and caps, off for cutters), `cap` (on for caps), `Collection` (the cap's outline curves, used only when `custom cap` is on) and `marks`, which has no effect: Blender reports it unused on every button and cap modifier, and the ABXY and Home groups pass a constant off instead [wiring]. Engraved marks on buttons are driven by the global `marks` switch. `home button` also has two menu inputs, `tolerance` and `cap tolerance`, that lead nowhere [wiring].

All objects of a family read the same preset slot (`abxy`, `dpad`, `select`, `home`) through `selector`, so all four ABXY caps share one set of numbers; only their position, rotation and outline collection differ [wiring]. The core generator is `button and caps`, which builds the shaft (`button`), the outline (`base shape`), the cap (`caps`), the case hole (`cutoff`) and the marks (`marks`) [wiring].

## Switches that change the whole family

| Global switch | Effect on buttons and caps [measured, GripV unless noted] |
|---|---|
| `tolerance` | button cross-section shrinks by the tolerance value: tight/default/loose = 0.12/0.16/0.24 (GripV), 0.16/0.20/0.30 (GripX); the caps' inner fit follows (≈ ±1–2.5 mm³ per cap) |
| `cap tolerance` | GripV: cap fit tight/default/loose = +0.1/0/−0.1 → about +3/0/−3 mm³ per cap and a small change on the shaft; GripX: no effect (all −0.16) |
| `horizontal buttons` (on as saved) | off switches to a different shaft design: ABXY button 634 → 1,105 mm³, D-pad button 634 → 1,498 mm³, caps and case holes change, case top −5,557 mm³ |
| `button logo` (on) | off removes the engraved logos from the ABXY caps and the Home cap (+1.7 to +3.3 mm³ each) |
| `marks` (off) | on engraves a mark on all four button shafts (+16 vertices, −0.2 mm³ each); the letter is fixed, see [Marks](marks-and-logos.md) |
| `dpad stick` (preset value, off) | on empties the D-pad button and caps (the dpad stick replaces them) and cuts the dpad stick opening instead |

`horizontal buttons` is used in 16 places: it forces the shaft's top bevel to 1 segment and the outline fillet to 1 segment, turns off the custom base curve for ABXY and D-pad, and switches the bottom bevel profile [wiring]. I could not find a description of what "horizontal" refers to; the geometry difference suggests a shaft designed to be printed lying down [inferred].

## Parameters

Values below are GripV / GripX (all four families listed in [the value table](#values-by-family)). Effects were measured on a copy by changing one value at a time with the saved settings (horizontal buttons on) [measured]; "size" is the bounding-box change.

### `button parameters` (the shaft)

| Input | What it does |
|---|---|
| button tolerance | linked to the `tolerance` menu through a *tolerance set*; subtracted from the shaft width: +0.2 made the shaft exactly 0.2 mm narrower in X and Y (so 0.1 per side) |
| SMD height | height of the PCB switch under the shaft: +0.44 raised the shaft's bottom by 0.44 (shaft 0.44 shorter) |
| button height | height of the cap: +0.256 made every cap of the family 0.256 taller; shaft and case unchanged |
| button height offset | no effect in any tested context |
| top bevel | no effect while `button cap` is on (the bevel is then fixed at 0.4) [wiring] |
| case middle bevel | bevel of the case hole: +0.2 removed 1.25 mm³ from the case top, nothing else |
| bottom bevel | bevel at the shaft's foot: +0.2 → shaft −4.6 mm³ |
| middle bevel | bevel on the shaft: +0.2 → shaft −0.3 mm³ |
| stopper position | height of the retaining stopper: +1.1 → shaft +10.5 mm³, case top −38.7 mm³ |
| stopper height | thickness of the stopper: +0.2 → shaft +1.2, case top −3.5 mm³ |
| stopper offset | how far the stopper sticks out: +0.2 → shaft 0.4 narrower on one axis, caps +10.9, case top +172 mm³ |
| case bool bevel | no effect with horizontal buttons on; with them off, bevel of the case hole (+0.2 → case top −58 to −108 mm³) |

Note: inside the bundle `case middle bevel` and `middle bevel` are packed under each other's names and swapped back downstream; the labels on the node are correct [measured].

### `caps parameters` (the cap and how it clips on)

| Input | What it does |
|---|---|
| caps fit tolerance | linked to `cap tolerance` through a *tolerance set*; XY fit between cap and shaft |
| caps fit Z tolerance | vertical play between cap and shaft: +0.2 → each cap −8 mm³ |
| caps fit Z | how far the shaft enters the cap: +0.208 → shaft 0.208 taller, caps −8.3 mm³ |
| cap case tolerance | gap between cap and case hole, per side: +0.2 → caps 0.4 smaller in X and Y |
| cap bevel, cap bevel subd | size and segments of the cap's top edge bevel (+0.2 → −3.5 mm³; +1 segment → +128 vertices) |
| cap bevel cutoff, bevel cutoff | on: the bevel is cut off at the given angle (radians; 0.96 ≈ 55°); off → −4.9 mm³ per cap |
| caps flex cut | depth of a slit in the cap (+0.2 → −0.4 mm³) [inferred: a flex slot for the clip] |
| button cap | on: two-piece buttons (shaft + cap). Off: no caps, the shaft becomes the whole button (ABXY shaft +1,070 mm³, 4.16 mm wider) and the case holes change (case top −4,111 mm³) |
| caps offset | how far the cap overhangs the shaft: +0.208 → shaft 0.416 narrower, caps +12.4, case top +310 mm³ |
| button cap travel distance | press travel: +0.2 → shaft 0.2 taller, caps 0.2 thinner |
| caps additional size | extra cap size beyond the outline: +0.2 → caps 0.4 wider, case top −136 mm³ |
| cap base fillet, cap base fillet subd | corner rounding of non-round caps (no effect on round ABXY caps; D-pad +0.35 → −3.4 mm³ per cap) |
| custom cap | on: the cap outline comes from the object's `Collection` input (hand-drawn curves in `source` › `… cap curve …`) instead of the generated outline; changes cap shape strongly (ABXY caps +128 mm³) |
| caps hook inset, caps hook height | the snap hook between cap and shaft (≤ 1 mm³ changes on both) |
| caps depth | cap thickness: +0.208 → caps 0.208 taller (downwards), shaft 0.208 shorter |

### `curve parameters` (the outline)

| Input | What it does |
|---|---|
| width | base width of shaft and cap: +1.2 → shaft and caps exactly 1.2 wider, case top −1,407 mm³ (ABXY) |
| octagonal fillet | outline variant; off → shaft +61 mm³, case top −66 mm³ |
| fillet | corner fillet of the outline (+0.2 → caps +2 mm³) |
| fillet subdiv | no effect while `horizontal buttons` is on (forced to 1); with it off, changes the shaft mesh |
| fillet tolerance | extra rounding of the case hole only (+0.2 → case top −31 mm³) |

### `capacitive plate parameters` (ABXY slot only)

See [Capacitive plate](capacitive.md).

### `marks parameters`

See [Marks](marks-and-logos.md).

## Values by family

| Constructor › input | V abxy | V dpad | V select | V home | X abxy | X dpad | X select | X home |
|---|---|---|---|---|---|---|---|---|
| button › SMD height | 4.4 | 4.4 | 4.4 | 4.4 | 4.6 | 4.6 | 4.6 | 4.6 |
| button › button height | 2.56 | 2.56 | 2.56 | 2.56 | 2.88 | 2.88 | 2.88 | 2.88 |
| button › button height offset | −0.5 | −0.5 | −0.5 | −0.5 | −0.5 | −0.5 | −0.5 | −0.5 |
| button › top bevel | 0.8 | 0.8 | 0.8 | 0.8 | 0.8 | 0.8 | 0.8 | 0.8 |
| button › case middle bevel | 0.2 | 0.2 | 0.2 | 0.2 | 0.4 | 0.4 | 0.4 | 0.4 |
| button › bottom bevel | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| button › middle bevel | 0.2 | 0.2 | 0.2 | 0.4 | 0.4 | 0.4 | 0.4 | 0.4 |
| button › stopper position | 11 | 11 | 11 | 11 | 9 | 9 | 9 | 9 |
| button › stopper height | 1.6 | 1.6 | 1.6 | 1.6 | 2 | 2 | 2 | 2 |
| button › stopper offset | 0.6 | 0.6 | 0.6 | 0.6 | 1 | 1 | 1 | 1 |
| button › case bool bevel | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| caps › caps fit Z tolerance | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| caps › caps fit Z | 2.08 | 2.08 | 2.08 | 2.08 | 2.08 | 2.08 | 2.08 | 2.08 |
| caps › cap case tolerance | 0.6 | 0.6 | 0.6 | 0.6 | 0.5 | 0.5 | 0.5 | 0.5 |
| caps › cap bevel | 1.6 | 1.6 | 1.6 | 1.6 | 2.3 | 1.6 | 1.6 | 1.6 |
| caps › cap bevel subd | 16 | 16 | 16 | 16 | 16 | 16 | 16 | 16 |
| caps › cap bevel cutoff | on | on | on | on | on | on | on | on |
| caps › bevel cutoff (rad) | 0.960 | 0.960 | 0.960 | 0.960 | 1.309 | 1.047 | 1.047 | 0.960 |
| caps › caps flex cut | 1 | 0 | 0.6 | 1.4 | 0.8 | 0 | 0.4 | 0.6 |
| caps › button cap | on | on | on | on | on | on | on | on |
| caps › caps offset | 2.08 | 2.08 | 0.56 | 2.08 | 1.48 | 1.48 | 0.38 | 1.48 |
| caps › button cap travel distance | 1.92 | 1.92 | 1.92 | 1.92 | 1.92 | 1.92 | 1.92 | 1.92 |
| caps › caps additional size | 0.3 | 0 | 1.2 | 1 | 0 | 0 | 0.3 | 0.1 |
| caps › cap base fillet | 2.85 | 3.5 | 3 | 3.6 | 2.85 | 2.85 | 2.85 | 2.85 |
| caps › cap base fillet subd | 16 | 16 | 16 | 16 | 16 | 16 | 16 | 16 |
| caps › custom cap | off | **on** | off | off | off | **on** | off | off |
| caps › caps hook inset | 0.3 | 0.3 | 0.3 | 0.3 | 0.3 | 0.3 | 0.3 | 0.3 |
| caps › caps hook height | 1.12 | 1.12 | 1.12 | 1.12 | 1.12 | 1.12 | 1.12 | 1.12 |
| caps › caps depth | 2.08 | 2.08 | 2.08 | 2.08 | 2.08 | 2.08 | 2.08 | 2.08 |
| curve › width | 12 | 12 | 8.96 | 12 | 12 | 12 | 9.8 | 12 |
| curve › octagonal fillet | on | on | on | on | on | on | on | on |
| curve › fillet | 1.6 | 1.6 | 1.6 | 1.6 | 2.2 | 1.8 | 1.5 | 2.5 |
| curve › fillet subdiv | 16 | 16 | 8 | 16 | 16 | 16 | 8 | 16 |
| curve › fillet tolerance | 1 | 1 | 1 | 1 | 0.4 | 0.4 | 0.4 | 0.4 |
| tolerance (tight / default / loose) | 0.12 / 0.16 / 0.24 | same | same | same | 0.16 / 0.20 / 0.30 | same | same | same |
| cap tolerance (tight / default / loose) | 0.1 / 0 / −0.1 | same | same | same | −0.16 ×3 | same | same | same |

All of these are read straight from the preset groups [wiring]. The interface defaults of the constructor groups (what a new node would get) differ from these and are listed in [reference/parameter-groups.md](../reference/parameter-groups.md).

## Unstable geometry with `horizontal buttons` off

With `horizontal buttons` off, the ABXY and D-pad results jump between two states: several unrelated parameter changes (for example `fillet subdiv` 16 → 17, `stopper position` 11 → 12.1, cap tolerance *default* 0 → 0.2) all made the ABXY shaft exactly 2.08 mm shorter and every ABXY cap 85 mm³ larger, on top of their own small effect, while changes of ±0.001 mm did not trigger the jump [measured]. The same pattern appears on the D-pad (shaft −0.22 mm, caps +83 mm³) [measured]. That looks like a boolean that fails or flips for some inputs [inferred]. With `horizontal buttons` on (as saved and as exported) no such jump was seen in any of the 250 button tests [measured]. If the non-horizontal design is revived, check these parts before trusting a parameter change.
