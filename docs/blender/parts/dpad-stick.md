# D-pad stick (rocker D-pad)

An alternative to the four-cap D-pad: a small stick on a rocker that presses the D-pad switches. Six objects, all using the modifier group `dpad stick` with a `Menu` input that picks the piece, plus the cutter `dpad stick bool` in `source` (`bool` on) [wiring]:

| Object | `Menu` value | Piece |
|---|---|---|
| `rocker` | `roker` (sic) | the rocker plate that presses the switches |
| `rocker ball` | `roker ball` | the ball the rocker pivots on |
| `rocker support` | `rocker support` | the support under the rocker |
| `ball support` | `ball support` | the seat for the ball |
| `stick` | `stick` | the stick rising through the case |
| `dpad stick cap` | `cap` | the textured cap on the stick |

## Switching it on

The switch is the `dpad stick` input of the `dpad stick parameters` node inside `GripV dpad stick` / `GripX dpad stick`; it is off as saved, and then all six pieces are empty [measured]. When it is on [measured, GripV]:

- the six pieces appear (sizes below);
- `dpad button` and the four D-pad caps become empty, because `dpad button` outputs nothing while the dpad stick is on [wiring];
- the case top uses the `dpad stick cutout` collection instead of the D-pad holes: case top −1,302 mm³.

The export presets switch it by overriding the *Combine Bundle* inside the shared group `dpad stick parameters`, which forces it on (or off) for every variant at once; that is how the `case_top_dpad_stick_*` files and the `parts/dpad_stick/` files are produced [wiring].

## Sizes when on

| Piece | GripV size (mm), volume | GripX |
|---|---|---|
| rocker | 28.0 × 28.0 × 2.62, 441 mm³ | identical |
| rocker ball | 13.41 × 13.41 × 4.32, 312 mm³ | identical |
| rocker support | 14.21 × 14.21 × 3.40, 448 mm³ | identical |
| ball support | 13.00 × 13.00 × 4.00, 245 mm³ | identical |
| stick | 7.0 × 3.64 × 18.98, 255 mm³ | 7.0 × 3.64 × 17.94, 243 mm³ |
| dpad stick cap | 15.07 × 15.09 × 7.60, 685 mm³ | 15.07 × 15.09 × 7.60, 692 mm³ |

[measured]. The stick is 1.04 mm shorter on GripX because it reaches up to the basemesh top, which is 1.04 mm lower on GripX (59.04 vs 58.00) [measured; the dependence is inferred from the matching numbers]. The cap differs because `hook z tolerance` is 0.32 on GripV and 0.16 on GripX, the only differing value between the two presets [wiring]. The committed STLs of rocker, rocker ball, rocker support and ball support are byte-identical between `orca_slicer/GripV` and `orca_slicer/GripX` [measured].

## Parameters (`dpad stick parameters`, 36 inputs)

All values are the same in GripV and GripX except `hook z tolerance` [wiring]. Effects measured on GripV with the dpad stick on [measured]:

| Input | Value | Effect of the test step |
|---|---|---|
| dpad stick | off | the switch above |
| rocker size | 14 | rocker footprint: +1.4 → rocker 2.8 wider; rocker ball slightly smaller |
| rocker base thickness | 0.6 | rocker thickness: +0.2 → rocker 0.2 thicker |
| stiick height (sic) | 1 | stick length: +0.2 → stick 0.2 longer, cap moves up 0.2 |
| ball radius | 7.2 | +0.72 → rocker ball 1.5 wider, ball support adapts |
| rocker support size | 14.4 | +1.44 → support 1.0 wider |
| button center offset | 9 | distance of the switch contact points: rocker and ball adapt |
| action | off | on: shows the assembly tilted (pose only) |
| texture height, texture sharpness | 0.6, 0.5 | cap texture (+37 / +28 mm³) |
| cap height offset | 20 | **no effect** |
| cap radius | 7.4 | +0.74 → cap 1.4 wider, +269 mm³ |
| cap subdivisions | 2 | cap mesh density (×2 vertices) and slightly larger cap |
| cutout | 5.8 | size of the opening in the rocker and case: +0.58 → case top +103 mm³, rocker −11 mm³ |
| chamber height, chamber size | 11.04, 15 | the cavity in the case top (case top +25 / −638 mm³) |
| ball support height | 4 | +0.4 → ball support 0.4 taller |
| button travel | 1.3 | press travel: rocker, ball and support adapt by ≈0.2–0.3 |
| rocker support height, rocker support thickness | 4.7, 5.7 | rocker support size |
| ball support radius | 2.2 | **no effect** |
| ball support compression tolerance | 0 | +0.2 → ball support 0.2 taller (preload) |
| stick bottom offset, ball stopper height, ball stopper position | 1.4, 1.4, 4.3 | small changes to stick, cap and ball |
| stick thickness | 2.2 | +0.22 → stick 0.44 wider; cap and rocker adapt |
| stick tolerance | 0.1 | clearance between stick and cap: +0.2 → stick 0.4 narrower |
| stick hook depth, stick hook height, hook extrude | 1.12, 2.72, 1.6 | the snap hook between stick and cap |
| hook z tolerance | 0.32 (GripX 0.16) | vertical play of that hook (cap −8.8 mm³ for +0.2) |
| inner hook tolerance | 0.6 | **no effect** |
| flex cut width, flex cut depth | 0.4, 1 | flex slot in the cap |
| cap fit tolerance (key `stick fit tolerance`) | 0 | cap fit on the stick (+0.2 → cap −3.8 mm³) |
| cap oval offset | 0.7 | cap shape (+8.7 mm³) |

The two preset groups also contain two loose *Value* nodes (5.44 and 14.72) and an unconnected `dpad stick outputs` node [wiring]. The interface defaults of `dpad stick parameters` (for a new node) differ from the preset values: for example `stiick height` 17.9, `ball radius` 6.9, `cap height offset` 15.8, `chamber height` 14.7 [wiring].
