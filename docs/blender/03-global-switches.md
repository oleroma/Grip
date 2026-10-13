# 3. Global switches (`global parameters`)

The 21 inputs of the `global parameters` node inside the node group `global`. They apply to every part and both scenes. Below: type, the value saved in the file, the choices, what each one does, and what changed when it was switched on a copy [measured] (volumes in mm³, sizes in mm). "No effect" means no exported object changed in that test.

Interface defaults of the group (what a fresh node would get) are mostly empty menus or off; the saved values on the node are what counts [wiring].

## Summary

| Input | Type | Saved | Choices / range | Affects |
|---|---|---|---|---|
| subdivision level | menu | `low ` (trailing space) | low = 1, medium = 2, high = 3, very high = 4 | basemesh smoothness → case, cable holder |
| variant | menu | `GripV` | GripX, GripV, GripR1 | everything |
| style | menu | `xbox` | xbox, dualsense | GripX only: basemesh, bumpers, triggers, screws |
| stock bumpers | bool | off | | bumpers and their case cutouts |
| top wire cutouts | bool | off | | case top |
| R4 wire cutouts | bool | off | | case bottom and top |
| body type | menu | `standard` | standard, indent, hollow, lattice | case construction |
| hollow top | bool | off | | GripV + standard only: shell case top |
| voxel resolution | menu | `low` | low 0.96, medium 0.64, high 0.32 (voxel size, mm) | hollow / hollow top shells |
| ribs | bool | on | | shell case top |
| fill type | menu | `Gyroid` | Gyroid, FischerKoch S, FischerKoch CY, Voronoi, Diamond, Primitive, cubic, manual | indent body only |
| pillars | bool | off | | case bottom (not with hollow) |
| cable holder | bool | on | | USB opening shape |
| horizontal buttons | bool | on | | button shafts, caps, case holes |
| button logo | bool | on | | logos on ABXY and Home caps |
| marks | bool | off | | marks on button shafts and triggers |
| tolerance | menu | `default` | tight, default, loose | button shafts, triggers |
| press tolerance | menu | `default` | tight, default, loose | triggers, GripV bumpers |
| cap tolerance | menu | `default` | tight, default, loose | GripV caps |
| screws | bool | on | | screw holes for standard and indent bodies |
| screws hollow | bool | off | | screw bosses for hollow and lattice bodies |

## Details

### subdivision level
Sets the *Subdivision Surface* level on the basemesh objects (groups `subdivision surface` for GripV, `subd` for GripX), so it controls how smooth the case is [wiring]. Saved `low ` (level 1); every case-export preset sets `very high` (level 4) [wiring].

| Level | GripV basemesh verts | case_top verts | case_bottom verts | case volume change (top / bottom) |
|---|---|---|---|---|
| low (1) | 2,406 | 7,105 | 4,371 | — |
| medium (2) | 9,618 | 8,527 | 9,897 | +489 / +711 |
| high (3) | 38,466 | 13,983 | 31,236 | +610 / +888 |
| very high (4) | 153,858 | 35,001 | 115,757 | +640 / +932 |

GripX behaves the same (case_bottom 3,146 → 73,431 verts at very high) [measured]. Side effects: the cable holder loses 2–20 mm³ (it is trimmed by the basemesh), and at high/very high the sticks change by a few vertices (their height is measured from the basemesh top) [measured]. Whole-scene evaluation time rose from 0.5 s to 1.9 s (GripV) [measured].

### variant
GripX = index 2, GripV = 1, GripR1 = 0. Picks the preset bundle of every part and the basemesh [wiring]. See [4. Variants and styles](04-variants-and-styles.md). Not set by the scenes: the export presets and the workspace sync set it.

### style
Only read when the variant is GripX; for other variants it is forced to `dualsense` internally and nothing reads it [wiring]. GripV: no effect [measured]. GripX xbox → dualsense: case top −17,022 and 14.3 narrower, case bottom −6,130, L1/R1 −54, L2/R2 +426, L4/R4 +641 and 6.8 taller, reinforcers repositioned; buttons, caps, sticks and small parts unchanged [measured].

### stock bumpers
Replaces the generated L1/R1 with the fixed meshes `L1 stock` / `R1 stock` (296 vertices each) and switches the case cutouts to `R1L1 stock cutouts` [wiring]. GripV: L1/R1 1,870 → 1,990 and 14.2 shorter in X, case top −1,471, case bottom +799. GripX: L1/R1 2,416 → 1,990, case top −927, case bottom +506 [measured].

### top wire cutouts
Subtracts the fixed mesh `top wire cutouts` from the case top. GripV −1,293, GripX −1,101 [measured].

### R4 wire cutouts
Subtracts the collection `R4 wire cutouts` from the case bottom (and the matching part from the top and, for shells, the middle plate). GripV top −137 / bottom −111; GripX −132 / −126 [measured].

### body type
`standard` keeps the solid case halves; `indent` intersects them with a pattern volume; `hollow` replaces them with an SDF shell; `lattice` is a shell plus a lattice made from hand-drawn curves. It also decides which of `screws` / `screws hollow` is used, and forces `fill type` to `cubic` unless the body is `indent` [wiring]. Full description and numbers in [6. Body types](06-body-types.md). Volumes at the saved settings [measured]:

| Body | GripV top | GripV bottom | GripX top | GripX bottom | eval time |
|---|---|---|---|---|---|
| standard | 130,394 | 180,761 | 125,979 | 153,843 | 0.5 s |
| indent (Gyroid) | 129,161 | 173,280 | 123,883 | 147,347 | 3.5–4 s |
| hollow | 30,478 | 36,150 | 29,976 | 30,245 | 7 s |
| lattice | 30,442 | 36,075 | 28,010 | 17,666 | 10–12 s |

### hollow top
Only honoured when the variant is GripV **and** the body is `standard`; then the case top is built by `shell structure` like a hollow body while the bottom stays solid [wiring]. GripV: case top 130,394 → 34,161, 7,105 → 44,023 vertices, eval 2.3 s. GripX: no effect [measured]. The GripV "Case standard" export preset turns it on for `case_top` [wiring].

### voxel resolution
Voxel size of the SDF shell: low 0.96, medium 0.64, high 0.32 mm. Feeds `voxel remesh size` of the GripV and GripX hollow presets [wiring]. No effect on `standard` or `indent` bodies (the indent preset has its own voxel size) [measured]. With `hollow` [measured]:

| | GripV top verts / volume | GripV bottom | time |
|---|---|---|---|
| low | 49,826 / 30,478 | 54,711 / 36,150 | 21 s |
| medium | 94,765 / 31,682 | 100,191 / 36,126 | 46 s |
| high | 332,313 / 32,284 | 346,022 / 35,870 | 83 s |

(times with other jobs running; relative only). The case-export presets use `high` [wiring].

### ribs
Adds rib planes (`ribs gripv top`, `ribs gripx`, …) to the shell of the **top** half [wiring]. No effect on solid bodies [measured]. With `hollow`, off removed 1,708 mm³ (GripV) / 1,232 mm³ (GripX) from the top and left the bottom unchanged [measured].

### fill type
Picks the indent preset and pattern; only honoured when the body is `indent` (otherwise forced to `cubic`) [wiring]. No effect on a standard body [measured]. `manual` is broken: it has no preset behind it and its curve collection `manual indent` is empty; with body `indent` it made the GripV case top **empty** and turned the bottom into a 122.6 × 47.8 × 64.3 mm fragment [measured]. See [6. Body types](06-body-types.md).

### pillars
Adds the fixed meshes `side pillars` and `middle pillars` to the case bottom, unless the body is `hollow` [wiring]. GripV +285, GripX +298 [measured]; no effect with `hollow`, but with `lattice` they are added (+715 / +709) because the lattice exclusion is disabled with an `AND False` [measured, wiring].

### cable holder
Chooses the USB opening: on = `USB BOOL cable holder` (room for the cable holder part), off = `USB BOOL` [wiring]. Off: GripV case bottom +319, GripX +213 [measured].

### horizontal buttons
Switches the button family between two shaft designs (see [Buttons](parts/buttons-and-caps.md)). Off: ABXY shaft 634 → 1,105, D-pad shaft 634 → 1,498, caps and case holes change, GripV case top −5,557 [measured].

### button logo
Engraved logos on the ABXY caps and the Home cap. Off: those caps lose their engraving (+1.7 to +3.3 mm³ each) [measured].

### marks
Engraves marks on the four button shafts and the four triggers (bumpers have their own switch) [wiring]. On: +16 vertices on each shaft, +20 to +330 on the triggers [measured]. See [Marks](parts/marks-and-logos.md) for the fixed `T` letter.

### tolerance, press tolerance, cap tolerance
See [7. Tolerances](07-tolerances.md).

### screws
For `standard` and `indent` bodies: cuts screw holes and nut pockets into both halves (`screw bools`) [wiring]. Off: GripV top +1,427 / bottom +2,115; GripX +1,309 / +1,360 [measured]. No effect with `hollow` or `lattice` [measured].

### screws hollow
The screw switch used instead of `screws` for `hollow` and `lattice` bodies [wiring]. No effect on solid bodies [measured]. With `hollow`, on **added** material (screw bosses in the shell): GripV top +4,226 / bottom +1,281, GripX +2,700 / +888 [measured].
