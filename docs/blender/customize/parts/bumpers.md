# Bumpers (L1, R1)

The shoulder bumpers are levers that sit in an opening at the top edge of the case. Each one has a round **stem** it pivots on and a **press face** at the front that pushes the switch. Its back reaches under the edge of the case top (the *overlap*), which holds it in place. The opening in the case is generated from the same preset, so it always follows the bumper. L1 is a mirror copy of R1.

There are two designs:

- **pivot** (`R1L1 flex` off, used by GripX): the bumper rotates on its stem.
- **flex** (`R1L1 flex` on, used by GripV): the bumper gets an extra arm of about 17 mm towards the centre of the controller. Probably the arm bends instead of the bumper rotating on its stem.

**Where:** controls panel › R1L1 LEVER › `GripV  lever R1L1` (two spaces) or `GripX lever R1L1` › `R1L1 lever parameters`. On GripX there are two nodes, frame "GripX" for xbox and "GripD" for dualsense. Edit the one for the style you use.

## Shape

| Input | What it changes |
|---|---|
| `wdith` (sic) | length of the bumper along the case edge |
| `height` | height of the bumper |
| `top bevel` | rounding of the top edge |
| `overlap` | how far the bumper reaches down under the case edge |
| `overlap slant` | the slope of that underside |
| `R1L1 flex` | flex or pivot design (above) |

## Stem (the pivot)

| Input | What it changes |
|---|---|
| `stem radius` | size of the stem. **On GripV this input is fed by a separate *Value* node next to it; change that node, not the input.** |
| `stem tolerance` | play of the stem in its seat |

## Press face

| Input | What it changes |
|---|---|
| `button height` | how far the press face stands out; the bumper gets deeper front to back |
| `depth` | depth of the press face |
| `insert depth` | how deep the bumper reaches into the case |
| `button inset offset` | how far the press face is set in |
| `button front shift X` | how far the press face extends along the bumper |

## Fit

| Input | What it changes |
|---|---|
| `bumper Z tolerance` | play below the bumper |
| `X tolerance` | play at the ends |
| `overlap tolerance` | play between the overlap and the case edge |
| `button press tol` | trims the press face, which sets the free play before the switch. On GripV it comes from the global `press tolerance`. On GripX it is a plain number on each style node; the global menu does not reach it. |

## Position

| Input | What it changes |
|---|---|
| `X`, `Z` | move both bumpers and their openings sideways or up |
| `Y` | moves only the back of the bumper. The front stays at the case edge, so the bumper gets shorter or longer front to back. |

## Curved bumpers

`curved R1L1` replaces the straight outline with a curve drawn per variant (collections `custom shape  gripV`, `custom shape gripD`, `custom shape gripX` in the `source` scene). `curved button slant`, `curved button depth tolerance` and `curved button bevel` only act when it is on. **The xbox-style curve collection is empty**, so curved bumpers do not work for GripX xbox yet; they work for GripV and GripX dualsense.

## Does nothing

`bevel inner`, `bevel inner sbdiv` and `curved button thickness`.

## Related settings

- `stock bumpers` (global) replaces the generated bumpers with fixed hand-modelled ones.
- The bumpers carry an `R` or `L` mark from their own `marks` switch, which is on ([Marks](marks-and-logos.md)).

## Export

GripV exports L1 and R1 in the "Parts" preset at each `press tolerance` (folders `press_*`). GripX exports them per style in the "Bumpers" preset (folders `pres_*`); those three folders are identical because of the fit issue above.
