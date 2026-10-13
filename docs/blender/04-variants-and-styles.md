# 4. Variants and styles

The file models one controller family in several shapes. A **variant** is a complete set of part presets plus a basemesh; GripX additionally has two **styles**.

## 4.1 What exists

| Variant | Basemesh object(s) | Scene | Status |
|---|---|---|---|
| **GripV** | `basemesh GripV` | `GripV` | release target |
| **GripX**, style **xbox** | `basemesh_X_style` | `GripX` | release target |
| **GripX**, style **dualsense** | `basemesh_D_style` | `GripX` | release target |
| GripR1 | `basemesh GripR1` | only in `source` | older variant; still fully wired into the selectors [wiring] |
| GripS | `basemesh GripS` | only in `source` | no node tree reads it [wiring] |
| GripX without battery | `basemesh_gripx_no battery` (with modifier `battery compartment`) | `source` › archive | archived [wiring] |

All basemeshes are half models (one side of X = 0) that the `MirrorX` modifier group mirrors and welds at the seam; a second modifier group subdivides them by the global `subdivision level` (`subdivision surface` for GripV, `subd` for GripX) [wiring]. The `crease_edge` attribute (and `crease_vert` for GripV) keeps edges sharp through subdivision [wiring].

## 4.2 How the variant is chosen

The global `variant` menu (GripX, GripV, GripR1) is turned into a `variant index` (GripR1 = 0, GripV = 1, GripX = 2) and three booleans [wiring]. Everything that differs per variant switches on that index:

- `selector` picks the variant's parameter bundle for every part (see [2. Parameter system](02-parameter-system.md));
- `basemesh variant` picks the basemesh collection for the case;
- `part variant switching` picks per-variant geometry inside a few groups (stick cutouts, bumper cutouts, inner supports, bumper shapes).

The value is one setting for the whole file. The `GripV` and `GripX` **scenes do not set it**: the scenes only decide which objects are around and which basemesh collection is linked. Opening the GripX scene while `variant` is still GripV evaluates GripX's objects with GripV presets and the GripV basemesh [wiring]. Two mechanisms try to keep them in step:

- the export presets set `variant` to the scene name as a global override, so exports are always consistent [wiring];
- in the UI, the `Auto sync workspaces` text (when run) or the external `w2g` add-on (when installed) set `variant` when you switch workspace [wiring]. The embedded script is not registered, so after opening the file nothing syncs unless one of them is active [wiring].

## 4.3 GripV versus GripX

Main shape differences as saved (bounding boxes in mm) [measured]:

| | GripV | GripX xbox | GripX dualsense |
|---|---|---|---|
| Basemesh | 165.8 × 86.5 × 74.3, Z from −15.3 | 175.5 × 99.5 × 54.3, Z from 3.7 | 160.5 × 102.8 × 54.5, Z from 3.5 |
| Case top | 162.4 × 77.6 × 19.0 | 168.2 × 88.6 × 18.0 | 154.0 × 84.3 × 18.0 |
| Case bottom | 165.8 × 86.5 × 55.3 | 175.5 × 99.2 × 36.3 | 160.5 × 102.5 × 36.5 |
| L1 / R1 | 46.5 × 11.5 × 12.3 | 29.9 × 13.1 × 14.0 | 30.9 × 13.1 × 13.6 |
| L2 / R2 | 23.0 × 18.4 × 21.9 | 9.0 × 26.5 × 18.2 | 11.1 × 26.8 × 18.1 |
| L4 / R4 | 24.0 × 27.3 × 33.6 | 18.0 × 12.3 × 16.4 | 17.1 × 12.8 × 23.2 |

Objects that exist in only one variant scene: `case_middle_plate` (GripV) and `reinforcers` (GripX) [wiring]. Options that only one variant honours [measured on copies]:

| Option | GripV | GripX |
|---|---|---|
| `hollow top` | cuts the case top into a shell (130,394 → 34,161 mm³) | no effect |
| `style` | no effect | switches basemesh, bumpers, triggers, screw positions |
| `cap tolerance` | changes cap fit (about ±3 mm³ per cap) | no effect: all three values are −0.16 |
| `press tolerance` | bumpers and triggers | triggers only |

## 4.4 Styles (GripX only)

`style` (xbox, dualsense) only matters while the variant is GripX. For any other variant `global parameters` forces it to `dualsense` internally, and no GripV or GripR1 consumer reads it [wiring]; switching style in the GripV scene changed nothing [measured].

With variant GripX, the internal flag `gripD` (true for dualsense) switches [wiring]:

| Where | What changes |
|---|---|
| `basemesh variant` | `basemesh xbox style` ↔ `basemesh dualsense style` collection, so the whole case |
| `GripX lever R1L1` | two `R1L1 lever parameters` nodes in frames "GripX" and "GripD": top bevel 2.5 → 2.7, overlap −4 → −3.6, button front shift X 17 → 18 |
| `GripX R2 parameters`, `GripX R4 parameters` | two `trigger parameters` nodes (frames "GripX" / "GripD") with different lengths, widths, angles |
| `GripX screw paramters` | different screw positions per style |
| `inner supports` | the middle-plate support markers (`Xbox syle middle plate supports` vs `dualsense style middle plate supports`) for hollow bodies |
| `lever R1L1 base` | the custom bumper outline collection (`custom shape gripX`, which is empty, vs `custom shape gripD`) |

Measured effect of switching xbox → dualsense with everything else as saved: case top −17,022 mm³ and 14.3 mm narrower, case bottom −6,130 mm³ and 14.9 mm narrower, L1/R1 −54 mm³, L2/R2 +426 mm³, L4/R4 +641 mm³ and 6.8 mm taller, reinforcers repositioned [measured]. Buttons, caps, sticks, capacitive, battery cover, cable holder and pin do not change [measured].

## 4.5 GripR1

GripR1 is still complete in the parameter tree: `GripR1 parameters` fills all 22 slots, including `R1` and `L1`, which only it uses (bumpers built by the `R1`/`L1` modifier groups on objects `R1 GripR1` and `L1 GripR1` in `source`) [wiring]. Its stick presets carry many disconnected alternatives (49 of 58 nodes in `GripR1 stick R parameters` are unused) [wiring]. It is not part of the release and the controls panel `GripR1 controls` is not tracked by `tracking.json` [wiring]. See [9. Issues](09-issues.md) for whether it still evaluates.
