# PCB slot, USB opening and cable holder

Three things in the case bottom are about the electronics: the slot the main board sits in, the USB opening, and the optional cable holder part that clamps a USB cable inside the case [inferred from the names and shapes].

## PCB slot

The slot is cut from the case bottom by the collection `pcb cutout` in `source` [wiring]:

| Object | What it is |
|---|---|
| `pcb cutout` | an 8-vertex outline of half the board, turned into a solid by the modifier group `GripX pcb` (used by both variants despite its name) → `pcb` |
| `marmota cutout` | fixed mesh with a `MirrorX` modifier, an extra clearance (`marmota` is also the name of a collection under `references`, next to the board model) |
| `corner relief` | fixed mesh with its own modifier group `corner relief` |

`pcb` takes the outline, grows it by `tolerance XY`, mirrors it, and builds a slot `thickness` deep for the board plus a deeper pocket of `below height` under it whose outline is inset by `support edge`, which leaves a ledge of that width for the board to rest on [inferred from the input names and the measured directions below: thickness, below height and tolerance remove material, support edge adds it]. The collection `supports` (object `middle supports`, modifier `pcb Z tolerance`) is subtracted from this cutter, so those support blocks stay in the case [wiring]. `pcb Z tolerance` is meant to raise them by a key `PCB z tolerance`, which no preset provides, so the offset is always 0 ([Issues](../09-issues.md) C7) [wiring].

Values come from the `pcb` slot (`GripV pcb cutout paramters` / `GripX pcb cutout paramters` › `pcb cutout parameters`). The key `PCB support edge` travels as `PCB offset support` inside the bundle [wiring].

| Input | GripV | GripX | Effect of +10 % or +0.2 on the case bottom [measured] |
|---|---|---|---|
| `PCB thickness` | 2.08 | 2 | deeper slot: −577 mm³ (GripV), −573 (GripX) |
| `PCB below height` | 1.76 | 1.92 | deeper pocket: −479, −522 |
| `PCB tolerance XY` | 0.2 | 0.3 | larger outline: −209, −205 |
| `PCB support edge` | 1.4 | 1 | wider ledge: +92, +96 |

With the hollow body the same inputs mainly shape the middle plate's board pocket (GripV: thickness +0.21 → plate +41 mm³ and bottom −37; tolerance XY +0.2 → plate −20) [measured]. GripX has no middle plate, so with its hollow body the effects on the case bottom are only a few percent of the standard ones: `PCB thickness` −32 (standard −573), `PCB below height` −30 (−522), `PCB tolerance XY` −5 (−205), `PCB support edge` +1.7 (+96) [measured].

## USB opening

`common bools` subtracts a fixed mesh from both halves: `USB BOOL cable holder` when the global `cable holder` is on (as saved), `USB BOOL` when it is off [wiring]. Both are hand-made 18-vertex meshes with a `MirrorX` modifier, so the opening does **not** follow any parameter [wiring]. Turning `cable holder` off added 319 mm³ to the GripV case bottom (213 on GripX), i.e. the opening without the holder is smaller [measured]. In shell bodies the opening is surrounded by a 2 mm boss ([6.5](../06-body-types.md#65-hollow-the-sdf-shell)).

## Cable holder

`cable holder` is a small printed part (origin X 0, Y −2.52, Z 34.91) that sits in the USB opening [wiring; its role is inferred]. Modifier stack: `MirrorX`, then `cable hole` [wiring]:

1. The object's own half mesh, mirrored.
2. Minus a box the size of the USB cable plug: the group `cable holder usb bool` reads `cable holder parameters`.
3. Plus the teeth: object `cable holder teeth` (in `source`, also mirrored).
4. Minus the basemesh of the current variant, so the part follows the outer shell.

`cable holder parameters` is **not** a variant preset: it is one group with no inputs, used by every variant, holding two `cable size` nodes [wiring]:

| Node | Label | width | height | Used |
|---|---|---|---|---|
| `cable size.001` | "pwnage paracord" | 12.27 | 6.52 | **yes** |
| `cable size` | — | 13.5 | 7.562 | no |

`cable hole` also contains a `base usb width` node with 13.5 × 7.562 [wiring]. Measured on GripV: `cable size.001` width +0.2 → holder −9 mm³, height +0.2 → −17 mm³; the unused node changed nothing; the case did not change in any of these [measured]. To fit a different cable, change `cable size.001`.

| | GripV | GripX |
|---|---|---|
| size (mm) | 22.70 × 16.44 × 11.00 | 22.70 × 16.44 × 11.00 |
| volume (mm³) | 1,425 | 1,939 |

The volume differs only because each variant's basemesh trims it differently; the subdivision level changes it by 2–20 mm³ for the same reason [measured]. Both "Parts" presets export it, as `cable holder.stl` on disk ([Issues](../09-issues.md) A7).

## Other fixed cutters in the case bottom

`battery wire space` (standard and indent bodies only) and `jst2p pass` are fixed meshes with `MirrorX`; they do not follow any parameter [wiring]. See [5.2](../05-case.md#52-what-is-cut-out-and-from-where).
