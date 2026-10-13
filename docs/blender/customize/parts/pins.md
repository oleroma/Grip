# Alignment pins

A small square peg that sits half in the case top and half in the case bottom, so the two halves line up when they are screwed together. One pin is generated; print two, one for each side. The holes are cut into both halves on both sides.

**Where:** controls panel › PINS › `GripV pins parameters` or `GripX pins` › `pins params` and `pins postion` (sic).

| Input | What it changes |
|---|---|
| `pin width`, `pin height` | size of the hole. The pin is this size minus the tolerances. |
| `xy tol` | side play: the pin is this much narrower than the hole (half per side) |
| `z tol` | vertical play: the pin is this much shorter than the hole (half at each end) |
| `bevel` | rounding of the pin's edges |
| `X`, `Y`, `Z` | where the pin and its holes are. `Z` should stay at the split height (40) so the pin is shared evenly between the halves. |

## Shell bodies

`hollow` cases do not use these pins: the shells get alignment pins of their own, at the markers in the collection `align cut`. The `lattice` body still cuts these holes (a switch-off in the file that is probably temporary).

## Export

Both "Parts" presets export `pin`.
