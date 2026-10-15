# Buttons and caps

The face buttons (ABXY), the D-pad, the four small Select buttons and the Home button all work the same way. Each one is made of two printed pieces:

- the **shaft** (`abxy button`, `dpad button`, `select button`, `home button`) sits on a switch on the board. It slides up through a hole in the case top, and a collar (the *stopper*) keeps it from falling out.
- the **cap** clips onto the shaft from above the case and is what your finger touches. Caps can have their own outline and an engraved symbol.

One shaft object exists per family; print one for every button position. The caps are separate objects, one per position (`abxy cap up`, `dpad cap left`, …). The hole in the case is generated from the same numbers as the shaft and cap, so changing the button changes its hole too.

**Where:** controls panel › BUTTONS › `… abxy`, `… dpad`, `… select`, `… home` (with `GripV` or `GripX` in front). The four families have separate presets, so you can make the D-pad different from the face buttons. Inside each preset:

| Constructor | What it holds |
|---|---|
| `curve parameters` | the outline of shaft and cap |
| `caps parameters` | the cap and how it clips on |
| `button parameters` | the shaft |
| `tolerance set` (two of them) | the tight/default/loose values for `tolerance` and `cap tolerance` |
| `marks parameters` | the identification letter ([Marks](marks-and-logos.md)) |
| `capacitive plate parameters` | ABXY only: the [capacitive plate](capacitive.md) |

## Size and outline (`curve parameters`)

| Input | What it changes |
|---|---|
| `width` | the size of the button: shaft, cap and case hole grow together |
| `octagonal fillet` | switches the outline between two corner styles |
| `fillet` | how round the cap's corners are. The shaft ignores it while `horizontal buttons` is on. |
| `fillet subdiv` | smoothness of the cap's corners; it does not change the shaft |
| `fillet tolerance` | extra rounding of the corners of the case hole only, so a square-ish cap does not catch in it |

## The cap (`caps parameters`)

| Input | What it changes |
|---|---|
| `button height` | how far the cap stands up; only the cap gets taller |
| `caps depth` | thickness of the cap |
| `caps additional size` | makes the cap bigger than the outline. The case hole grows with it. |
| `cap case tolerance` | gap between the cap and its hole in the case, per side |
| `cap bevel`, `cap bevel subd` | rounding of the cap's top edge, and its smoothness |
| `cap bevel cutoff`, `bevel cutoff` | cut that rounding off at an angle (in radians) for a flatter, crisper top |
| `cap base fillet`, `cap base fillet subd` | corner rounding of non-round caps |
| `custom cap` | use a hand-drawn outline instead of the generated one. The outline comes from the collection set on each cap object's modifier (`… cap curve …` in the `source` scene). The D-pad uses this for its arrow shape. |
| `button cap` | on: two-piece buttons (shaft + cap). Off: no caps, and the shaft itself becomes the whole button. |

### How the cap clips on

| Input | What it changes |
|---|---|
| `caps fit Z` | how far the shaft reaches into the cap |
| `caps fit tolerance` | side fit of cap on shaft. It comes from the global `cap tolerance` through a `tolerance set`, and a higher value is tighter. |
| `caps fit Z tolerance` | vertical play of the cap on the shaft |
| `caps hook inset`, `caps hook height` | size of the snap hook that holds the cap |
| `caps flex cut` | depth of a slit that makes the clip flexible (probably) |
| `caps offset` | how much wider the cap is than the shaft: it is subtracted from `width` for the shaft and its case hole, while the cap stays the same size. |

## The shaft (`button parameters`)

| Input | What it changes |
|---|---|
| `button tolerance` | how loosely the shaft slides in the case hole: the shaft gets this much narrower (half per side). It comes from the global `tolerance` through a `tolerance set`. |
| `SMD height` | height of the switch on the board that the shaft stands on. Set it for your switches; the shaft gets shorter as it rises. |
| `button cap travel distance` | how far the button can be pressed: the shaft gets taller and the cap thinner |
| `stopper position`, `stopper height`, `stopper offset` | the collar that stops the shaft from coming out of the case: its height on the shaft, its thickness and how far it sticks out |
| `bottom bevel`, `middle bevel` | rounding of the shaft's edges |
| `case middle bevel` | rounding of the edge of the case hole |
| `case bool bevel` | rounding of the case hole for the old shaft design (only with `horizontal buttons` off) |
| `top bevel` | not used while the buttons have caps |
| `button height offset` | does nothing |

## Global settings that affect buttons

- `tolerance` and `cap tolerance` pick the shaft and cap fits ([Fit and tolerances](../03-fit-and-tolerances.md)).
- `horizontal buttons`: keep it on. Off switches to an older shaft design whose geometry jumps between two shapes when unrelated values change.
- `button logo`: the engraved symbols on the ABXY and Home caps. To change a symbol, edit its curves in the `source` scene ([Logos](marks-and-logos.md#logos)).
- `marks`: a letter on each shaft.
- The D-pad stick switch (in `dpad stick`) replaces the D-pad shaft and caps with the [rocker D-pad](dpad-stick.md).

## Moving a button

A button's position is its objects' location: the shaft, its caps, and the matching cutter objects in the `source` scene (`abxy cutout …`, `dpad cutout …`). Move them together.

## Export

The "Buttons" preset exports the ABXY shaft (named `button`) at each `tolerance`, and the caps at each `tolerance` × `cap tolerance`. All button holes are the same for now, so this one shaft is printed for every button. Many cap settings change only the cap, not the shaft or its hole, so the caps differ while the shafts stay the same. If a family's hole changes one day, add its shaft (`select button`, `dpad button` or `home button`) to the preset.
