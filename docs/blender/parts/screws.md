# Screws, nut lock and reinforcers

The case halves are held together by four screws: two at the front and two at the back, mirrored left and right [wiring]. Each screw goes in from the case bottom (head and screwdriver access are cut into the bottom half) and threads into a nut held in a pocket in the case top [inferred from which half each input changes, below].

Everything about the screws comes from one group, `screws`, used in several places with different flags [wiring]:

| Used by | Flags | Produces |
|---|---|---|
| object `screw bools` (collection `screw comp` in `source`), subtracted from the case top | none | screw holes and nut pockets |
| `bottom bools` (case bottom) | none | screw holes, head and screwdriver holes |
| `button shafts sdf` (shell bodies) | `sdf` | solid bosses around each screw, grown by the hollow preset's `protect geometry` (+0.6 top, +0.2 bottom) |
| `plate bools` (middle plate) | | the screw holes through the plate (output `plate`) |
| object `nut lock` (both scenes) | `nut lock` | a small insert for the FRONT nut slot, built at the origin, not mirrored |
| object `reinforcers` (GripX scene only) | `reinforcer` | sleeves around the screws (frame "REINFORCER" in the group `screw`) |

The global `screws` switches the holes for `standard` and `indent` bodies; `screws hollow` switches the bosses for `hollow` and `lattice` bodies ([3](../03-global-switches.md#screws)) [wiring].

## How the screws are placed

`screws` places two `selector` nodes on the `screw` slot: `part index` 0 gives the **FRONT** screw definition, `part index` 1 the **BACK** one. Each is unpacked by `screw outputs` and built by the group `screw` (151 nodes). The two are joined and mirrored across X = 0 by `MirrorX` [wiring]. `screw` reads the current basemesh (`basemesh variant`) and contains the constant 40 twice, so the screw geometry is related to the split height and the basemesh top [wiring; how exactly is not traced].

In the preset groups (`GripV screw paramters`, `GripX screw paramters`, sic), each definition is a `screw parameters` node (sizes) plus a `screw position` node (`position` vector and `rotation` about Z, radians). In GripX the BACK definition exists twice, picked by `style`: `screw parameters.002` / `screw position.002` in frame "GripX" for xbox and `screw parameters.001` / `screw position.001` in frame "GripD" for dualsense. GripV's BACK nodes are `screw parameters.001` / `screw position.001` [wiring].

| Definition | GripV | GripX xbox | GripX dualsense |
|---|---|---|---|
| FRONT position | (26, −8.2, 46.6), rotation π | (21.3, −10.94, 46.6), π | same as xbox |
| BACK position | (69.85, −62.81, 46.6), π/2 | (64.94, −80.54, 43.76), π/2 | (59, −75, 43.76), π/2 |

## Sizes

| Input | GripV FRONT | GripV BACK | GripX FRONT | GripX BACK xbox | GripX BACK dualsense |
|---|---|---|---|---|---|
| screw hole diameter | 2.9 | 2.9 | 2.9 | 2.9 | 2.9 |
| screw head hole diameter | 5.2 | 5.2 | 5.2 | 5.2 | 5.2 |
| screw head hole height | 4.8 | 4.8 | 4.8 | 4.8 | 4.8 |
| screw length | 12.4 | 20.4 | 12 | 25 | 25 |
| screwdriver hole diameter | 5.2 | 8 | 5.2 | 8 | 8 |
| screwdriver guide slant height | 5 | 5 | 5 | 5 | 5 |
| nut width | 5.1 | 5.1 | 5.1 | 5.1 | 5.1 |
| nut height | 2 | 2 | 2 | 2 | 2 |
| nut pocket length | 7 | 7 | 8.7 | 8.7 | 8.7 |
| nut slot hideout depth | 1.8 | 3.2 | 1.5 | 1.51 | 1.51 |
| nut slot depth tolerance offset | 0.1 | 0.1 | 0.1 | 0.1 | 0.1 |
| screw end slot offset | 0.4 | 0.4 | 0.4 | 0.4 | 0 |
| reinforcer offset | 3 | 3 | 3 | 3 | 3 |
| reinforcer top offset | 0 | 0 | −0.5 | 0 | −0.1 |

[wiring]. The reference collection `screws DIN912` holds models of `screw M2.5-12 DIN912`, `screw M2.5-16 DIN912` and `nut M2.5 DIN912` (4.9 mm across flats, 1.7 mm high) [wiring], so the holes are sized for M2.5 socket-head screws and nuts: `nut width` 5.1 and `nut height` 2 leave about 0.2 and 0.3 mm of play [inferred from those models]. The FRONT `screw length` 12.4 probably matches the M2.5-12 screw [inferred]; nothing in the file pairs the longer BACK lengths (20.4, 25) with a screw model [wiring].

## What each input does

One change at a time (+10 % or +0.2) with the saved settings; case changes in mm³ [measured]. "Top" and "bottom" are the case halves.

| Input | Effect (GripV unless noted) |
|---|---|
| `screw hole diameter` | wider shaft hole through both halves: FRONT top −9 / bottom −16; BACK bottom −38; GripX BACK bottom −59 |
| `screw head hole diameter` | wider head recess in the bottom half: FRONT −29, BACK −68 |
| `screw head hole height` | BACK +28 on the bottom; no effect on the FRONT screws |
| `screw length` | the head recess starts lower, more material in the bottom: FRONT +36, BACK +177 (GripX BACK +213) |
| `screwdriver hole diameter` | access hole for the screwdriver below the head: no effect where it equals the head diameter (FRONT, 5.2); BACK 8 → 8.8 removed 296 (GripX 99) |
| `screwdriver guide slant height` | the cone between screwdriver hole and head: BACK +15; no effect on FRONT |
| `nut width` | wider nut pocket in the top: −86 (FRONT), −88 (BACK); the nut lock gets 0.51 wider; GripX reinforcers +1,439 to +1,461 |
| `nut height` | taller nut pocket: top −9 to −10 |
| `nut pocket length` | longer slot to slide the nut in: top −50; nut lock 0.7 longer; GripX reinforcers +102 to +135 |
| `nut slot hideout depth` | how far the nut sits inside the slot: top −2 to −3; moves the nut lock 0.1 |
| `screw end slot offset` | space past the screw end: top −17 (GripX −20); nut lock 0.2 taller |
| `nut slot depth tolerance offset` | **no effect** on the case; GripX reinforcers +35 |
| `reinforcer offset` | GripX only: reinforcer sleeves thicker, +907 to +920; no effect on GripV (no reinforcer object) |
| `reinforcer top offset` | GripX only: reinforcers +55, 0.2 taller; no effect on GripV |
| `position` | moves the screw (and its mirror); changing Z by +0.2 moved the nut pockets up (top −17 to −20) and the nut lock grew by 0.2 |
| `rotation` | turns the nut slot about the screw axis (a few vertices change) |

With `style` = xbox, edits to the "GripD" BACK node change nothing; with dualsense the "GripD" node acts and gives the same effects as the xbox node within a few mm³ (`screw length` +2.5: bottom +210; `screwdriver hole diameter` +0.8: −90; `nut width` +0.51: top −55, reinforcers +1,431) [measured]. The FRONT node is shared by both styles [wiring].

### With shell bodies

With `body type` = `hollow` and `screws hollow` on, the case is a thin shell and the screws sit in solid bosses. The same inputs then mostly grow or shrink the boss instead of cutting a hole, so several effects change sign [measured, GripV and GripX xbox, case top / bottom in mm³]:

| Input | GripV FRONT | GripV BACK | GripX BACK xbox |
|---|---|---|---|
| `nut width` +10 % | top +114 | top +219 | top +6 |
| `nut pocket length` +10 % | top +190 | top +144 | top +0.2 |
| `nut slot hideout depth` +0.2 to +0.32 | top +18 | top +41 | top +0.5 |
| `screw hole diameter` +10 % | top −5.5, middle plate −6 | top −9, bottom +20, plate −3.5 | top −1.4, bottom +33 |
| `screw length` +10 % | bottom −6.5 | bottom −73 | bottom −76 |
| `screw head hole diameter` +10 % | bottom −2 | bottom +34 | bottom +30 |
| `nut height` +0.2 | top −8 | top −9 | none |

**The saved GripV values sit on a jump.** In this setting the GripV case top weighs 34,702 mm³ as saved, but 1,700 to 2,000 mm³ less with any nearby value of the FRONT or BACK `screw end slot offset` (0.3, 0.45, 0.5, 0.55, 0.6 against the saved 0.4) or with either screw raised by 0.2 [measured]. The missing material is a thin layer spread over most of the case top (X 16 to 79, Y −69 to −6 on the right half), not something at the screws, so the whole shell wall changes slightly [measured]. That points to the voxel grid of the SDF shell shifting with the screw bosses rather than to the screw geometry itself [inferred]. GripX did not show it (−19 for the same edit). See [Issues](../09-issues.md) B10.

## Nut lock and reinforcers

- **`nut lock`** is built from the FRONT definition only, at the world origin (X 3.5 to 10.4, Z −6.6 to 0), so it is printed as a separate part: 6.86 × 4.96 × 6.60 mm, 224 mm³ (GripV); 8.56 × 4.96 × 6.60 mm, 280 mm³ (GripX) [measured]. Its size follows `nut width`, `nut pocket length`, `screw end slot offset` and `nut slot hideout depth` [measured]. I read it as a wedge that keeps the front nut from sliding out of its slot [inferred].
- **`reinforcers`** (GripX scene only) is a single object of 137.98 × 78.33 × 103.84 mm, 23,651 mm³, reaching from Z −56.2 to 47.6, far below the case bottom (which starts at Z 3.7) [measured]. It looks like a set of sleeves meant to be combined with something else rather than printed as is [inferred].

Neither is exported by a preset ([Issues](../09-issues.md) A8).
