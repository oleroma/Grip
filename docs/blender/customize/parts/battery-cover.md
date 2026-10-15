# Battery cover

The battery sits in a compartment in the underside of the case bottom. A printed cover closes it and clips in with flexible lips. A fixed finger notch helps to open it. The compartment and the cover are generated from the same preset, so changing the battery size resizes both. On shell bodies the compartment is also cut into the middle plate.

**Where:** controls panel › PCB AND BATTERY › `… cover parameters`. Inside are `basic cover parameters` (the fit) and `advanced cover parameters` (everything else). **On GripX, edit the nodes in frame "old cover"**; the frame "battery" next to it is not connected.

## Battery and compartment

| Input | What it changes |
|---|---|
| `battery length`, `battery width`, `battery height` | the battery the compartment is made for. Set them for your battery. |
| `shift Y` | where the compartment sits, front to back |
| `battery wire cut` | a slot in the cover for the battery wire |
| `appendix` + `appendix length`, `appendix height`, `appendix gap` | an optional extension of the compartment. The three sizes only act when `appendix` is on. |

## Cover

| Input | What it changes |
|---|---|
| `cover base thickness` | thickness of the cover plate |
| `cover base overlap` | how far the cover reaches over the edge of the opening |
| `curved cover` | the cover follows the curved underside of the case instead of being flat |

## Clip lips

| Input | What it changes |
|---|---|
| `flex width` | width of the flexible tongues the lips sit on |
| `lip height`, `lip width` | size of the lips |
| `lip hook height` | the hook that snaps into the case |

## Fit

| Input | What it changes |
|---|---|
| `x tolerance`, `y tolerance` | gap around the cover in the opening |
| `compression offset` | makes the cover thinner, probably so it presses the battery in place |

`test parameter` does nothing.

## Export

Both "Parts" presets export the cover as `battery_cover.stl`.
