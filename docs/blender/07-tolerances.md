# 7. Tolerances and fit presets

Fits between printed parts are set in two ways: three **global tolerance menus** that choose between tight/default/loose values stored per part, and many **fixed tolerances** typed directly into the presets. All values are millimetres unless noted [wiring].

## 7.1 The three global menus

| Global menu | Bundle key | Index | Used by |
|---|---|---|---|
| `tolerance` | `button tol` | tight 0, default 1, loose 2 | button shafts (all four families); triggers (X and radius fit) |
| `press tolerance` | `button press tol` | same | triggers (press travel fit); GripV bumpers |
| `cap tolerance` | `cap tol` | same | caps (fit on the shaft) |

Inside `global parameters` the nodes that convert the menus are named confusingly (`cap tolerance` reads the *press tolerance* menu, `button press` reads the *cap tolerance* menu), but the bundle keys they write are the right ones [wiring].

Each preset turns the index into a number with a `tolerance set` node (tight / default / loose values). The complete list [wiring]:

| Preset | Feeds | Menu | GripV tight / default / loose | GripX tight / default / loose |
|---|---|---|---|---|
| abxy, dpad, select, home | `button parameters` › button tolerance | `tolerance` | 0.12 / 0.16 / 0.24 | 0.16 / 0.20 / 0.30 |
| abxy, dpad, select, home | `caps parameters` › caps fit tolerance | `cap tolerance` | 0.10 / 0 / −0.10 | −0.16 / −0.16 / −0.16 |
| R2 | trigger › x tolerance and radius tolerance | `tolerance` | 0.16 / 0.24 / 0.32 | 0.20 / 0.22 / 0.22 |
| R4 | trigger › x tolerance and radius tolerance | `tolerance` | 0.16 / 0.24 / 0.32 | 0.18 / 0.20 / 0.20 |
| R2 | trigger › button press tolerance | `press tolerance` | 0.50 / 0.60 / 0.75 | 0.56 / 0.61 / 0.65 |
| R4 | trigger › button press tolerance | `press tolerance` | 0.45 / 0.55 / 0.75 | 0.60 / 0.65 / 0.70 |
| lever R1L1 (bumpers) | `R1L1 lever parameters` › button press tol | `press tolerance` | −0.10 / 0 / 0.10 | **not connected**: the node holds 0 and the tolerance set (0 / 0 / 0) is unused |

In GripX the two trigger presets each hold two `trigger parameters` nodes (xbox and dualsense); both read the same tolerance sets [wiring].

### What the numbers do [measured]

| Tolerance | Measured meaning |
|---|---|
| button tolerance | the shaft cross-section is `width − tolerance`: +0.2 made it 0.2 narrower in X and Y; so the clearance per side is half the value |
| caps fit tolerance | positive = tighter: GripV tight (+0.1) added ≈3 mm³ to each cap, loose (−0.1) removed ≈3 mm³ |
| cap case tolerance (fixed) | gap per side between cap and case hole: +0.2 made each cap 0.4 smaller in X and Y |
| trigger x / radius tolerance | GripV tight vs default (−0.08): L2/R2 grew ≈0.075 mm in X and Y and +35 mm³, L4/R4 +0.086 mm and +62 mm³ |
| trigger press tolerance | GripV tight vs default: L2/R2 +11 mm³ and 0.05 mm taller, L4/R4 +14 mm³ |
| bumper press tol (GripV) | tight (−0.1) made L1/R1 0.1 mm longer in Y (+5.6 mm³); loose the opposite |

### Consequences visible in the exports [measured by comparing STL files]

- GripX `cap_tight`, `cap_default`, `cap_loose` folders contain identical caps.
- GripX trigger `default` and `loose` folders contain identical triggers (equal values above).
- GripX bumper `pres_tight`, `pres_default`, `pres_loose` contain identical bumpers.
- Marks on the parts do not tell the tolerance apart: the letter is always `T` (see [Marks](parts/marks-and-logos.md)).

## 7.2 Fixed tolerances in the presets

Values that do not follow any menu (GripV / GripX) [wiring]. Where a GripX group has two nodes (xbox / dualsense), the dualsense value is given after a slash.

| Part | Input | GripV | GripX |
|---|---|---|---|
| all caps | cap case tolerance | 0.6 | 0.5 |
| all caps | caps fit Z tolerance | 0 | 0 |
| all buttons | curve › fillet tolerance (case hole rounding) | 1 | 0.4 |
| capacitive | capacitive plate tolerance | 0.4 | 0.4 |
| capacitive | capacitive plate stem tolerance (unused) | −0.1 | −0.1 |
| sticks | shaft tolerance | 0.2 | 0.2 (all presets) |
| dpad stick | stick tolerance | 0.1 | 0.1 |
| dpad stick | hook z tolerance | 0.32 | 0.16 |
| dpad stick | inner hook tolerance (no measured effect) | 0.6 | 0.6 |
| dpad stick | cap fit tolerance | 0 | 0 |
| dpad stick | ball support compression tolerance | 0 | 0 |
| bumpers | stem tolerance | −0.025 | 0.1 / 0.1 |
| bumpers | bumper Z tolerance | 0.52 | 0.3 / 0.3 |
| bumpers | X tolerance | 1 | 1 / 1 |
| bumpers | overlap tolerance | 0.48 | 0.3 / 0.3 |
| battery cover | x tolerance / y tolerance | 0.2 / 0.15 | 0.15 / 0.15 |
| scroll wheel | scroll wheel tolerance | 0.6 | 0.7 |
| PCB cutout | PCB tolerance XY | 0.2 | 0.3 |
| screws | nut slot depth tolerance offset | 0.1 | 0.1 |
| middle plate (shell bodies) | xy / Z / fit Z / inner Z / inner xy / pcb pocket tolerance | 0 / 0.32 / 0.1 / 0.32 / 0.4 / 0.32 | −0.1 / 0.16 / −0.2 / 0.16 / 0.4 / 0.32 |

Fixed fit offsets hidden in node trees rather than presets: `button and caps` adds 0.23 to the cap hook inset of the cutter [wiring]; `lever R1L1 outputs` returns an SDF clearance of 2 mm around the bumpers for shell bodies, `dpad stick outputs` 1 mm [wiring]; `trigger cap` uses 0.4 / 0.2 pad and tip offsets, but that group is not connected [wiring].

## 7.3 Where the printer settings live

Tolerances in the model assume a particular printer and profile. The OrcaSlicer projects in `orca_slicer/` use a Bambu Lab A1, 0.4 mm nozzle, 0.16 mm layers, X-Y hole and contour compensation 0, elephant-foot compensation 0.075 [measured, read from the 3MF files]. Nothing in the `.blend` records which printer the tolerances were tuned for [wiring].
