# Screws, nut lock and reinforcers

Four screws hold the case together: two at the front and two at the back, mirrored left and right. Probably each screw goes in from the bottom, with its head sunk into the case bottom, and threads into a nut held in a pocket in the case top. The holes are sized for M2.5 socket-head screws (DIN 912) and M2.5 nuts. Models of those are in the reference collection `screws DIN912`.

The front pair and the back pair have their own settings, because they sit at different heights and need different screw lengths.

**Where:** controls panel › SCREWS › `… screw parameters`. Inside:

| Node | What it is |
|---|---|
| `screw parameters` / `screw position` | the FRONT screws |
| `screw parameters.001` / `screw position.001` | the BACK screws on GripV, and on GripX dualsense (frame "GripD") |
| `screw parameters.002` / `screw position.002` | the BACK screws on GripX xbox (frame "GripX") |

## Screw

| Input | What it changes |
|---|---|
| `screw hole diameter` | the hole the screw passes through |
| `screw length` | length of the screw. It decides how deep the head sits in the case bottom. |
| `screw head hole diameter`, `screw head hole height` | the recess for the screw head |
| `screwdriver hole diameter` | the access hole below the head. It has no effect when it equals the head diameter. |
| `screwdriver guide slant height` | the cone between that access hole and the head |

## Nut

| Input | What it changes |
|---|---|
| `nut width`, `nut height` | the nut pocket. Leave some play over your nut's size across flats. |
| `nut pocket length` | the slot the nut is slid in through |
| `nut slot hideout depth` | how far inside the slot the nut sits |
| `screw end slot offset` | extra room past the screw's tip |
| `nut slot depth tolerance offset` | only affects the GripX reinforcers |

## Position

| Input | What it changes |
|---|---|
| `position` (on `screw position`) | where the screw is. The mirror copy on the other side follows. |
| `rotation` | turns the nut slot around the screw |

## Nut lock and reinforcers

- **`nut lock`** is a small separate piece made from the FRONT screw settings. It probably wedges the front nut in its slot. Its size follows the nut settings. It is built at the world origin, not in place.
- **`reinforcers`** (GripX only) are sleeves around the screws. `reinforcer offset` sets their wall thickness and `reinforcer top offset` their height. As generated they reach far below the case, so they are probably meant to be combined with something else rather than printed as they are.

Neither is exported by a preset.

## Shell bodies

With `hollow` or `lattice` bodies, turn on the global `screws hollow`. The shell then gets solid bosses around each screw. The same settings now shape the holes through those bosses, and larger nut pockets grow the boss around them. On GripV the shell top changes slightly in wall thickness when `screw end slot offset` or the screw height is changed (see [known issues](../../develop/07-known-issues.md)).
