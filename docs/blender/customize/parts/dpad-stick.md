# D-pad stick (rocker D-pad)

An alternative to the four D-pad caps. A short stick comes up through the case top with a textured cap on it. Underneath, it sits on a rocker plate that pivots on a ball, so tilting the stick presses one of the four D-pad switches. It is printed as six pieces:

| Object | Piece |
|---|---|
| `dpad stick cap` | the textured cap your thumb touches |
| `stick` | the stick through the case top |
| `rocker` | the plate that presses the switches |
| `rocker ball` | the ball the rocker pivots on |
| `ball support` | the seat for the ball |
| `rocker support` | the support under the rocker |

**Switch it on** with `dpad stick` on the `dpad stick parameters` node (controls panel › DPAD STICK). The D-pad shaft and caps then disappear and the case top gets the D-pad stick opening instead. The export presets produce both versions, so `case_top_dpad_stick_…` files exist next to the normal tops.

**Where:** controls panel › DPAD STICK › `… dpad stick` › `dpad stick parameters`.

## What you can change

| Input | What it changes |
|---|---|
| **cap** | |
| `cap radius` | size of the cap |
| `cap oval offset` | how oval the cap is |
| `texture height`, `texture sharpness` | the grip texture on the cap |
| `cap subdivisions` | smoothness of the cap |
| `cap fit tolerance` | fit of the cap on the stick |
| `stick hook depth`, `stick hook height`, `hook extrude`, `hook z tolerance` | the snap hook that holds the cap on the stick, and its vertical play |
| `flex cut width`, `flex cut depth` | a slot that lets the cap flex onto the hook |
| **stick** | |
| `stick height` | stick length (the cap moves up with it) |
| `stick thickness` | stick thickness |
| `stick tolerance` | clearance between stick and cap |
| **rocker and ball** | |
| `rocker size`, `rocker base thickness` | footprint and thickness of the rocker plate |
| `button center offset` | distance from the centre to the switch contact points. Set it for your board. |
| `button travel` | press travel of the rocker |
| `ball radius` | size of the pivot ball |
| `ball stopper height`, `ball stopper position`, `stick bottom offset` | fine adjustment of where stick, ball and rocker meet |
| `ball support height`, `ball support compression tolerance` | the ball seat, and how much it preloads the ball |
| `rocker support size`, `rocker support height`, `rocker support thickness` | the support under the rocker |
| **case** | |
| `cutout` | size of the stick opening; it changes both the rocker and the case top |
| `chamber size`, `chamber height` | the cavity in the case top that the rocker moves in |
| **preview** | |
| `action` | shows the assembly tilted |

`cap height offset`, `ball support radius` and `inner hook tolerance` do nothing.

## Good to know

- `dpad stick parameters` is one group shared by GripV and GripX; only `hook z tolerance` differs between the two presets. The export presets force the switch on in that shared group, so both variants export it.
- The stick reaches up to the top surface of the case, so it follows the basemesh height.
