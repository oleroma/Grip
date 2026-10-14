# 7. Known issues

Everything found while documenting the file that is wrong, fragile, misleading or unused. Rows marked **Fixed** have been corrected since; the rest is unchanged. The numbers are for reference in issues and pull requests.

## A. Exports

| # | Issue | Effect | Suggested fix |
|---|---|---|---|
| A1 | The GripV view layer excludes the `case middle plate` collection. | "Case hollow" skips the middle plate. | Include the collection, or remove it from the preset until the plate is ready. |
| A2 | **Fixed** in the preset (commit d0bf44d): the GripX "Parts" preset switched the capacitive part through `GripV abxy`. | The GripX `capacitive_knob.stl` in `orca_slicer/` was exported before the fix and is still the plate. | Re-run the GripX "Parts" preset. |
| A3 | In `GripX lever R1L1` the `tolerance set` is not connected, and `button press tol` is typed 0 on both style nodes. | The three GripX bumper `pres_*` folders are identical. | Connect the set to both style nodes with real values, or drop the sweep. |
| A4 | GripX cap tolerance is the same value for tight, default and loose. | Three identical GripX `cap_*` folders. | Three values, or no sweep for GripX. |
| A5 | GripX trigger `tolerance`: default = loose. | Two identical trigger folders. | Give loose its own value. |
| A6 | The *Index Switch* that picks the mark letter is typed, not linked to a tolerance menu. | Every part prints `T` whatever its tolerance. | Drive it from the tolerance index, or use `type` = `parameter`. |
| A7 | **Fixed:** six part files used spaces (`battery cover.stl`, …) while the exporter writes underscores. Both variants now use the exporter's names. | — | — |
| A8 | Not exported by any preset: GripV `StickR`, GripX scroll wheel parts and `nut lock`, `reinforcers`, `case_middle_plate`. (GripV has written the scroll wheel to `parts/scrollwheel/` and `nut lock` to `parts/misc/` since commit d478402.) | Those STLs in the repo are older than the file. | Add them to a preset, or confirm they are not released. |
| A9 | GripV "Case standard" turns on `hollow top` for `case_top`. | The released "standard" tops are shells. | Probably intended; say so in the print guide. |
| A10 | The export root is an absolute Windows path (`D:\Grip\orca_slicer\…`). | Exports on other machines go to a wrong or missing folder. | Use a path relative to the `.blend` if the add-on supports it. |
| A11 | GripV bumper folders are `press_*`, GripX `pres_*`. | Two spellings. | Pick one. |

## B. Fragile geometry

| # | Issue | Effect | Suggested fix |
|---|---|---|---|
| B1 | The triggers are not closed meshes (a few non-manifold edges, more with `bevel subd` = 2). In Blender 5.2.0, GripX xbox R4 `shift z` = 4.62 made the whole case bottom empty; 5.2.2 did not reproduce it. | Slicer warnings; a nearby value can delete a case half. | Make the trigger generator output closed meshes (merge by distance before the boolean). |
| B2 | `horizontal buttons` off is unstable: unrelated edits make the shafts and caps jump between two shapes. | The old button design cannot be trusted. | Only relevant if that design is revived. |
| B3 | `fill type` = manual has no preset and an empty curve collection. | Choosing it destroys the case. | Remove the item or finish it. |
| B4 | The lattice curves are shrinkwrapped to `basemesh GripV` only. | GripX lattice cases do not follow the GripX shape. | Curve sets per basemesh, or project onto the current basemesh in the nodes. |
| B5 | `ribs` passes `ribs gripv top` to both its inputs; `ribs gripx` is unused. | GripX shells get ribs placed for GripV. | Connect `ribs gripx`. |
| B6 | `custom shape gripX` (curved bumper outline for xbox style) is empty. | Curved bumpers fail on GripX xbox. | Add an outline curve. |
| B7 | All fonts load from `C:\Windows\Fonts`. | On macOS and Linux all text marks are silently dropped. | Pack the fonts (File › External Data › Pack Resources). |
| B8 | The `logo` modifiers on `select button` and `home button` report "Font not specified". | No effect, but they show as errors. | Delete them or set a font. |
| B9 | The split height 40 is repeated as a constant in five groups, plus a 40 in `screw`. | Changing it in one place breaks shells, plate or screws. | One global value. |
| B10 | GripV with `hollow` and `screws hollow` on: the case top jumps by about 2,000 mm³ between the saved screw values and any nearby value of `screw end slot offset` or screw height. The difference is a thin layer over most of the top, not at the screws. | The shell wall may shift slightly with unrelated edits; volume checks can mislead. | Probably the SDF voxel grid shifting with the screw bosses; fix the grid's origin or size. |

## C. Misleading values

| # | Issue | What to know |
|---|---|---|
| C1 | GripV bumper `stem radius` shows one value but is fed by a *Value* node with another; `tracking.json` records the unused one. | Edit the *Value* node. |
| C2 | GripX cover: frame "battery" is not connected; the live values are in "old cover". | Edits in "battery" do nothing. |
| C3 | Disconnected alternatives in presets: GripV trigger frame "SNES" (whose `button rotation` = 90 looks like degrees in a radian field), *Value* nodes in frame "za3tarani", a sixth GripX StickL set, the unused `cable size` node, `Value.001` "button pressed height (old)" in GripX R4. | They look like settings but nothing reads them. |
| C4 | Inputs with no effect: hollow `smooth sdf`; most indent and lattice preset inputs; `button height offset`; `capacitive plate stem tolerance`; stick `shaft X/Y correction`; dpad stick `cap height offset`, `ball support radius`, `inner hook tolerance`; bumper `bevel inner`, `bevel inner sbdiv`, `curved button thickness`; cover `test parameter`; middle plate `hook to top`. | Placeholders or unfinished features; remove them or note it in tooltips. |
| C5 | `home button` has `tolerance` and `cap tolerance` modifier inputs that lead nowhere; the `marks` input on every button and cap modifier is unused. | Changing them does nothing. |
| C6 | The `… fill controls` panels hold skeleton and hollow presets per fill type that nothing reads. | Edits there do nothing. |
| C7 | `PCB z tolerance` (on `middle supports`) and `extra thickness` (clip objects) read keys no constructor writes. | The board supports get no Z tolerance. |
| C8 | The scenes do not set `variant`; the sync script is not registered and `w2g` is not in the repository. | After opening, the GripX scene can show GripV numbers. |
| C9 | `subdivision level` is saved as `low ` with a trailing space. | Trips scripts that compare menu names. |
| C10 | `pillars` and the pin holes are applied with `lattice` because the exclusion is `lattice AND False`. | Probably a temporary switch-off; decide which is wanted. |
| C11 | The press and cap tolerance conversion nodes in `global parameters` are named the wrong way round. | Only confusing when reading the group. |

## D. Leftovers and naming

| # | Item |
|---|---|
| D1 | 10 node groups that no modifier reaches: `Combine variants`, `parameters`, `Tool`, `Tool.001`, `vector vis`, `visualize vector at`, `delete half`, `mesh to curve to mesh`, `Smooth by Angle`, `tip`. Another 39 are reached only from objects that live in `source` (clips, `marmota case`, `spiral trigger`, tests). |
| D2 | GripR1 is still fully wired. With `variant` = GripR1 the file evaluates, but L1/R1 and the ABXY, D-pad and Home caps come out empty, and the shafts are plain blocks. |
| D3 | The old selection chain (`part and variant`, `main switch`, `bundle variant switching base`, `GripR1  parameters`) is dead code behind the unconnected `trigger cap`. `R2 tip`, `R4 tip` and the `R4` group's 16 unconnected marks inputs belong to the same era. |
| D4 | `scrollwheel holder` has a Geometry Nodes modifier with no group. |
| D5 | Typos in names people see: `wdith`, `heght`, `stiick`, `sheild`, `sbdiv`, `paramters` / `paramteters`, `contols`, `neighboor`, `suppprts`, `roker`, `postion`, `coer Y tolerance`, `Xbox syle`, `holllow lattice parameters`, `voroni`, `coVer base`. Double spaces in `GripV  lever R1L1`, `GripV  lattice parameters`, `GripR1  parameters`, `hollow  parameters`, `stick  XY correction`, `custom shape  gripV`. |
| D6 | Automatic `.001` names on real alternatives (`fill parameters.001`, `basic stick parameters.001`, `screw parameters.001`, …) say nothing about what they are for. |
| D7 | `test` / `tests` and `Tool.001` are unused. |
| D8 | `GripR1 controls` is not tracked by `tracking.json`. |
| D9 | The battery compartment logic exists twice: `battery bool and cover` and `coVer base`. |
