# Preset values: GripX

Every value typed into the GripX preset groups, as saved in `blender/Grip.blend`. Generated from the file; angles are in radians as Blender stores them. "Live" means the node is wired to the preset's output; values on nodes marked **not connected** have no effect. What each input does is described on the part pages.

The presets are listed in the order of the frames in the `GripX contols` panel.


## `GripX abxy` (frame BUTTONS)


- **tolerance set** `tolerance set`: tight 0.16 / default 0.2 / loose 0.3, picked by the global `tolerance` menu, feeds `button parameters` › button tolerance

- **tolerance set** `tolerance set.001`: tight -0.16 / default -0.16 / loose -0.16, picked by the global `cap tolerance` menu, feeds `caps parameters` › caps fit tolerance

**button parameters**

| Input | Value |
|---|---|
| button tolerance | ← tolerance set `tolerance`: 0.16 / 0.2 / 0.3 |
| SMD height | 4.6 |
| button height | 2.88 |
| button height offset | -0.5 |
| top bevel | 0.8 |
| case middle bevel | 0.4 |
| bottom bevel | 1 |
| middle bevel | 0.4 |
| stopper position | 9 |
| stopper height | 2 |
| stopper offset | 1 |
| case bool bevel | 1 |

**capacitive plate parameters**

| Input | Value |
|---|---|
| capacitive | plate |
| screw hole | off |
| capacitive plate tolerance | 0.4 |
| capacitive plate stem tolerance | -0.1 |
| plate button offset | 1 |

**curve parameters**

| Input | Value |
|---|---|
| width | 12 |
| octagonal fillet | on |
| fillet | 2.2 |
| fillet subdiv | 16 |
| fillet tolerance | 0.4 |

**caps parameters**

| Input | Value |
|---|---|
| caps fit tolerance | ← tolerance set `cap tolerance`: -0.16 / -0.16 / -0.16 |
| caps fit Z tolerance | 0 |
| caps fit Z | 2.08 |
| cap case tolerance | 0.5 |
| cap bevel | 2.3 |
| cap bevel subd | 16 |
| cap bevel cutoff | on |
| bevel cutoff | 1.309 |
| caps flex cut | 0.8 |
| button cap | on |
| caps offset | 1.48 |
| button cap travel distance | 1.92 |
| caps additional size | 0 |
| cap base fillet | 2.85 |
| cap base fillet subd | 16 |
| custom cap | off |
| caps hook inset | 0.3 |
| caps hook height | 1.12 |
| caps depth | 2.08 |

**marks parameters**

| Input | Value |
|---|---|
| bump | 0.16 |
| mark depth | 0.16 |
| insertion | off |
| type | custom |
| L-R side | off |
| text | ← GeometryNodeIndexSwitch `Index Switch` |
| parameters | button press tolerance |
| font size | 5 |
| translate | (0, 5, 0) |
| rotate text | 0 |
| rotate | 0 |
| axis | Y |
| side | min |
| Decimals | 2 |
| Character Spacing | 1.1 |
| Word Spacing | 0 |
| Line Spacing | 0.7 |
| Text Box Width | 0.1 |

- Index Switch `Index Switch` (marks text): Index=0, 0=T, 1=D, 2=L

## `GripX dpad` (frame BUTTONS)


- **tolerance set** `tolerance set`: tight 0.16 / default 0.2 / loose 0.3, picked by the global `tolerance` menu, feeds `button parameters` › button tolerance

- **tolerance set** `tolerance set.001`: tight -0.16 / default -0.16 / loose -0.16, picked by the global `cap tolerance` menu, feeds `caps parameters` › caps fit tolerance

**button parameters**

| Input | Value |
|---|---|
| button tolerance | ← tolerance set `tolerance`: 0.16 / 0.2 / 0.3 |
| SMD height | 4.6 |
| button height | 2.88 |
| button height offset | -0.5 |
| top bevel | 0.8 |
| case middle bevel | 0.4 |
| bottom bevel | 1 |
| middle bevel | 0.4 |
| stopper position | 9 |
| stopper height | 2 |
| stopper offset | 1 |
| case bool bevel | 1 |

**curve parameters**

| Input | Value |
|---|---|
| width | 12 |
| octagonal fillet | on |
| fillet | 1.8 |
| fillet subdiv | 16 |
| fillet tolerance | 0.4 |

**caps parameters**

| Input | Value |
|---|---|
| caps fit tolerance | ← tolerance set `cap tolerance`: -0.16 / -0.16 / -0.16 |
| caps fit Z tolerance | 0 |
| caps fit Z | 2.08 |
| cap case tolerance | 0.5 |
| cap bevel | 1.6 |
| cap bevel subd | 16 |
| cap bevel cutoff | on |
| bevel cutoff | 1.0472 |
| caps flex cut | 0 |
| button cap | on |
| caps offset | 1.48 |
| button cap travel distance | 1.92 |
| caps additional size | 0 |
| cap base fillet | 2.85 |
| cap base fillet subd | 16 |
| custom cap | on |
| caps hook inset | 0.3 |
| caps hook height | 1.12 |
| caps depth | 2.08 |

**marks parameters**

| Input | Value |
|---|---|
| bump | 0.16 |
| mark depth | 0.16 |
| insertion | off |
| type | custom |
| L-R side | off |
| text | ← GeometryNodeIndexSwitch `Index Switch` |
| parameters | button press tolerance |
| font size | 5 |
| translate | (0, 5, 0) |
| rotate text | 0 |
| rotate | 0 |
| axis | Y |
| side | min |
| Decimals | 2 |
| Character Spacing | 1.1 |
| Word Spacing | 0 |
| Line Spacing | 0.7 |
| Text Box Width | 0.1 |

- Index Switch `Index Switch` (marks text): Index=0, 0=T, 1=D, 2=L

## `GripX home` (frame BUTTONS)


- **tolerance set** `tolerance set`: tight 0.16 / default 0.2 / loose 0.3, picked by the global `tolerance` menu, feeds `button parameters` › button tolerance

- **tolerance set** `tolerance set.001`: tight -0.16 / default -0.16 / loose -0.16, picked by the global `cap tolerance` menu, feeds `caps parameters` › caps fit tolerance

**button parameters**

| Input | Value |
|---|---|
| button tolerance | ← tolerance set `tolerance`: 0.16 / 0.2 / 0.3 |
| SMD height | 4.6 |
| button height | 2.88 |
| button height offset | -0.5 |
| top bevel | 0.8 |
| case middle bevel | 0.4 |
| bottom bevel | 1 |
| middle bevel | 0.4 |
| stopper position | 9 |
| stopper height | 2 |
| stopper offset | 1 |
| case bool bevel | 1 |

**curve parameters**

| Input | Value |
|---|---|
| width | 12 |
| octagonal fillet | on |
| fillet | 2.5 |
| fillet subdiv | 16 |
| fillet tolerance | 0.4 |

**caps parameters**

| Input | Value |
|---|---|
| caps fit tolerance | ← tolerance set `cap tolerance`: -0.16 / -0.16 / -0.16 |
| caps fit Z tolerance | 0 |
| caps fit Z | 2.08 |
| cap case tolerance | 0.5 |
| cap bevel | 1.6 |
| cap bevel subd | 16 |
| cap bevel cutoff | on |
| bevel cutoff | 0.9599 |
| caps flex cut | 0.6 |
| button cap | on |
| caps offset | 1.48 |
| button cap travel distance | 1.92 |
| caps additional size | 0.1 |
| cap base fillet | 2.85 |
| cap base fillet subd | 16 |
| custom cap | off |
| caps hook inset | 0.3 |
| caps hook height | 1.12 |
| caps depth | 2.08 |

**marks parameters**

| Input | Value |
|---|---|
| bump | 0.16 |
| mark depth | 0.16 |
| insertion | off |
| type | custom |
| L-R side | off |
| text | ← GeometryNodeIndexSwitch `Index Switch` |
| parameters | button press tolerance |
| font size | 5 |
| translate | (0, 5, 0) |
| rotate text | 0 |
| rotate | 0 |
| axis | Y |
| side | min |
| Decimals | 2 |
| Character Spacing | 1.1 |
| Word Spacing | 0 |
| Line Spacing | 0.7 |
| Text Box Width | 0.1 |

- Index Switch `Index Switch` (marks text): Index=0, 0=T, 1=D, 2=L

## `GripX select` (frame BUTTONS)


- **tolerance set** `tolerance set`: tight 0.16 / default 0.2 / loose 0.3, picked by the global `tolerance` menu, feeds `button parameters` › button tolerance

- **tolerance set** `tolerance set.001`: tight -0.16 / default -0.16 / loose -0.16, picked by the global `cap tolerance` menu, feeds `caps parameters` › caps fit tolerance

**button parameters**

| Input | Value |
|---|---|
| button tolerance | ← tolerance set `tolerance`: 0.16 / 0.2 / 0.3 |
| SMD height | 4.6 |
| button height | 2.88 |
| button height offset | -0.5 |
| top bevel | 0.8 |
| case middle bevel | 0.4 |
| bottom bevel | 1 |
| middle bevel | 0.4 |
| stopper position | 9 |
| stopper height | 2 |
| stopper offset | 1 |
| case bool bevel | 1 |

**curve parameters**

| Input | Value |
|---|---|
| width | 9.8 |
| octagonal fillet | on |
| fillet | 1.5 |
| fillet subdiv | 8 |
| fillet tolerance | 0.4 |

**caps parameters**

| Input | Value |
|---|---|
| caps fit tolerance | ← tolerance set `cap tolerance`: -0.16 / -0.16 / -0.16 |
| caps fit Z tolerance | 0 |
| caps fit Z | 2.08 |
| cap case tolerance | 0.5 |
| cap bevel | 1.6 |
| cap bevel subd | 16 |
| cap bevel cutoff | on |
| bevel cutoff | 1.0472 |
| caps flex cut | 0.4 |
| button cap | on |
| caps offset | 0.38 |
| button cap travel distance | 1.92 |
| caps additional size | 0.3 |
| cap base fillet | 2.85 |
| cap base fillet subd | 16 |
| custom cap | off |
| caps hook inset | 0.3 |
| caps hook height | 1.12 |
| caps depth | 2.08 |

**marks parameters**

| Input | Value |
|---|---|
| bump | 0.16 |
| mark depth | 0.16 |
| insertion | off |
| type | custom |
| L-R side | off |
| text | ← GeometryNodeIndexSwitch `Index Switch` |
| parameters | button press tolerance |
| font size | 5 |
| translate | (0, 5, 0) |
| rotate text | 0 |
| rotate | 0 |
| axis | Y |
| side | min |
| Decimals | 2 |
| Character Spacing | 1.1 |
| Word Spacing | 0 |
| Line Spacing | 0.7 |
| Text Box Width | 0.1 |

- Index Switch `Index Switch` (marks text): Index=0, 0=T, 1=D, 2=L

## `GripX dpad stick` (frame DPAD STICK)


**dpad stick parameters**

| Input | Value |
|---|---|
| dpad stick | off |
| rocker size | 14 |
| rocker base thickness | 0.6 |
| stiick height | 1 |
| ball radius | 7.2 |
| rocker support size | 14.4 |
| button center offset | 9 |
| action | off |
| texture height | 0.6 |
| texture sharpness | 0.5 |
| cap height offset | 20 |
| cap radius | 7.4 |
| cap subdivisions | 2 |
| cutout | 5.8 |
| chamber height | 11.04 |
| chamber size | 15 |
| ball support height | 4 |
| button travel | 1.3 |
| rocker support height | 4.7 |
| ball support radius | 2.2 |
| ball support compression tolerance | 0 |
| rocker support thickness | 5.7 |
| stick bottom offset | 1.4 |
| ball stopper height | 1.4 |
| stick thickness | 2.2 |
| stick tolerance | 0.1 |
| stick hook depth | 1.12 |
| stick hook height | 2.72 |
| hook z tolerance | 0.16 |
| inner hook tolerance | 0.6 |
| hook extrude | 1.6 |
| flex cut width | 0.4 |
| flex cut depth | 1 |
| ball stopper position | 4.3 |
| cap fit tolerance | 0 |
| cap oval offset | 0.7 |

## `GripX cover parameters` (frame PCB AND BATTERY)


**basic cover parameters** (2 nodes)

| Input | battery (not connected) | old cover |
|---|---|---|
| y tolerance | 0.15 | 0.15 |
| x tolerance | 0.15 | 0.15 |

**advanced cover parameters** (2 nodes)

| Input | battery (not connected) | old cover |
|---|---|---|
| lip height | 3.2 | 3.2 |
| battery length | 63.5 | 62.85 |
| battery width | 35.4 | 35.4 |
| battery height | 5.2 | 5.2 |
| flex width | 1 | 1.05 |
| lip width | 0.5 | 0.35 |
| lip hook height | 2 | 1.9 |
| shift Y | -48 | -48 |
| cover base thickness | 1 | 1.5 |
| cover base overlap | 0.5 | 0.75 |
| appendix | off | off |
| appendix height | 0.95 | 0.95 |
| appendix length | 31.6 | 31.6 |
| appendix gap | 2.7 | 2.7 |
| compression offset | 0.1 | 0.1 |
| battery wire cut | 6 | 6 |
| test parameter | 0 | 0 |
| curved cover | off | off |

## `GripX pcb cutout paramters` (frame PCB AND BATTERY)


**pcb cutout parameters**

| Input | Value |
|---|---|
| PCB tolerance XY | 0.3 |
| PCB thickness | 2 |
| PCB support edge | 1 |
| PCB below height | 1.92 |

## `GripX pins` (frame PINS)


**pins params**

| Input | Value |
|---|---|
| pin width | 4 |
| pin height | 8.1 |
| xy tol | 0.1 |
| z tol | 0.6 |
| bevel | 1 |

**pins postion**

| Input | Value |
|---|---|
| X | 70.418 |
| Y | -55.5119 |
| Z | 40 |

## `GripX lever R1L1` (frame R1L1 LEVER)


- **tolerance set** `tolerance set`: tight 0 / default 0 / loose 0, picked by the global `press tolerance` menu — **not connected**

**R1L1 lever parameters** (2 nodes)

| Input | GripX | GripD |
|---|---|---|
| button press tol | 0 | 0 |
| top bevel | 2.5 | 2.7 |
| stem tolerance | 0.1 | 0.1 |
| wdith | 21 | 21 |
| height | 10.6 | 10.6 |
| stem radius | 3 | 3 |
| bumper Z tolerance | 0.3 | 0.3 |
| X tolerance | 1 | 1 |
| bevel inner | 4 | 4 |
| bevel inner sbdiv | 2 | 2 |
| overlap | -4 | -3.6 |
| overlap tolerance | 0.3 | 0.3 |
| button height | 2.4 | 2.4 |
| depth | 1.8 | 1.8 |
| insert depth | 2.5 | 2.5 |
| button inset offset | 1 | 1 |
| overlap slant | 3 | 3 |
| button front shift X | 17 | 18 |
| curved R1L1 | off | off |
| curved button thickness | 6.1 | 6.1 |
| curved button slant | -1 | -1 |
| curved button depth tolerance | 1 | 1 |
| curved button bevel | 1 | 1 |
| X | 28 | 28 |
| Y | -14 | -14 |
| Z | 40 | 40 |
| R1L1 flex | off | off |

**marks parameters**

| Input | Value |
|---|---|
| bump | 0.16 |
| mark depth | 0.16 |
| insertion | off |
| type | custom |
| L-R side | on |
| text | ← GeometryNodeIndexSwitch `Index Switch` |
| parameters | "" |
| font size | 5 |
| translate | (9, 1, 0) |
| rotate text | 0 |
| rotate | 0 |
| axis | Z |
| side | min |
| Decimals | 2 |
| Character Spacing | 1.1 |
| Word Spacing | 0 |
| Line Spacing | 0.7 |
| Text Box Width | 0.1 |

- Index Switch `Index Switch` (marks text): Index=0, 0=T, 1=D, 2=L

## `GripX R2 parameters` (frame R2R4)


- **tolerance set** `tolerance set`: tight 0.56 / default 0.61 / loose 0.65, picked by the global `press tolerance` menu, feeds `trigger parameters` › button press tolerance, `trigger parameters.001` › button press tolerance

- **tolerance set** `tolerance set.001`: tight 0.2 / default 0.22 / loose 0.22, picked by the global `tolerance` menu, feeds `trigger parameters` › x tolerance, `trigger parameters` › radius tolerance, `trigger parameters.001` › x tolerance, `trigger parameters.001` › radius tolerance

**trigger parameters** (2 nodes)

| Input | GripX | GripD |
|---|---|---|
| button press tolerance | ← tolerance set `press tolerance`: 0.56 / 0.61 / 0.65 | ← tolerance set `press tolerance`: 0.56 / 0.61 / 0.65 |
| tip angle offset | -0.1745 | -0.2007 |
| tip shear | 0 | -0.1047 |
| trigger length | 30.5 | 30.15 |
| top bevel | 1 | 1 |
| x tolerance | ← tolerance set `tolerance`: 0.2 / 0.22 / 0.22 | ← tolerance set `tolerance`: 0.2 / 0.22 / 0.22 |
| radius tolerance | ← tolerance set `tolerance`: 0.2 / 0.22 / 0.22 | ← tolerance set `tolerance`: 0.2 / 0.22 / 0.22 |
| bevel | 2 | 2 |
| bevel subd | 1 | 1 |
| bevel cutoff | 0.5 | 0.5 |
| action | off | off |
| trigger radius | 40.7 | 40.7 |
| stopper length | 21.7 | 21.7 |
| button rotation | 0 | -0.0244 |
| shift z | 20.6 | 20.6 |
| button radius offset | 1 | 1 |
| height | 14.4 | 14.4 |
| width | 9.2 | 10.8 |
| stopper height | 1 | 1 |
| subdivision length | 1 | 1 |
| button pressed height | 1.29 | 1.29 |
| x offset | 0 | 0 |

**marks parameters**

| Input | Value |
|---|---|
| bump | 0.16 |
| mark depth | 0.16 |
| insertion | off |
| type | custom |
| L-R side | off |
| text | ← GeometryNodeIndexSwitch `Index Switch` |
| parameters | button press tolerance |
| font size | 5 |
| translate | (0, 0, 0) |
| rotate text | 0 |
| rotate | 0 |
| axis | X |
| side | max |
| Decimals | 2 |
| Character Spacing | 1.1 |
| Word Spacing | 0 |
| Line Spacing | 0.7 |
| Text Box Width | 0.1 |

- Value node `Value.001` "button pressed height (old)" = 1.65 (not connected)

- Index Switch `Index Switch` (marks text): Index=0, 0=T, 1=D, 2=L

## `GripX R4 parameters` (frame R2R4)


- **tolerance set** `tolerance set`: tight 0.6 / default 0.65 / loose 0.7, picked by the global `press tolerance` menu, feeds `trigger parameters` › button press tolerance, `trigger parameters.001` › button press tolerance

- **tolerance set** `tolerance set.001`: tight 0.18 / default 0.2 / loose 0.2, picked by the global `tolerance` menu, feeds `trigger parameters` › x tolerance, `trigger parameters` › radius tolerance, `trigger parameters.001` › x tolerance, `trigger parameters.001` › radius tolerance

**trigger parameters** (2 nodes)

| Input | GripX | GripD |
|---|---|---|
| button press tolerance | ← tolerance set `press tolerance`: 0.6 / 0.65 / 0.7 | ← tolerance set `press tolerance`: 0.6 / 0.65 / 0.7 |
| tip angle offset | -0.5847 | -0.5079 |
| tip shear | 0.0642 | -0.208 |
| trigger length | 21.2 | 24.1 |
| top bevel | 0.7 | 0.7 |
| x tolerance | ← tolerance set `tolerance`: 0.18 / 0.2 / 0.2 | ← tolerance set `tolerance`: 0.18 / 0.2 / 0.2 |
| radius tolerance | ← tolerance set `tolerance`: 0.18 / 0.2 / 0.2 | ← tolerance set `tolerance`: 0.18 / 0.2 / 0.2 |
| bevel | 2 | 2 |
| bevel subd | 1 | 1 |
| bevel cutoff | 0.5 | 0.5 |
| action | off | off |
| trigger radius | 24.6 | 37.4 |
| stopper length | 15.001 | 15.001 |
| button rotation | 1.4661 | 1.7279 |
| shift z | 4.2 | 2.5 |
| button radius offset | 2 | 2 |
| height | 12 | 12 |
| width | 11 | 10.9 |
| stopper height | 2 | 2 |
| subdivision length | 1 | 1 |
| button pressed height | 1.29 | 1.29 |
| x offset | 0 | 0 |

**marks parameters**

| Input | Value |
|---|---|
| bump | 0.16 |
| mark depth | 0.16 |
| insertion | off |
| type | custom |
| L-R side | off |
| text | ← GeometryNodeIndexSwitch `Index Switch` |
| parameters | trigger x tolerance, radius tolerance, button press tolerance |
| font size | 5 |
| translate | (0, -1, 4) |
| rotate text | 0 |
| rotate | 0.4363 |
| axis | X |
| side | max |
| Decimals | 2 |
| Character Spacing | 1.1 |
| Word Spacing | 0 |
| Line Spacing | 0.6 |
| Text Box Width | 0.1 |

- Index Switch `Index Switch` (marks text): Index=0, 0=T, 1=D, 2=L

## `GripX screw paramters` (frame SCREWS)


**screw parameters** (3 nodes)

| Input | FRONT | GripD | GripX |
|---|---|---|---|
| screw hole diameter | 2.9 | 2.9 | 2.9 |
| screw head hole diameter | 5.2 | 5.2 | 5.2 |
| screw head hole height | 4.8 | 4.8 | 4.8 |
| screw length | 12 | 25 | 25 |
| screwdriver hole diameter | 5.2 | 8 | 8 |
| screwdriver guide slant height | 5 | 5 | 5 |
| nut width | 5.1 | 5.1 | 5.1 |
| nut slot hideout depth | 1.5 | 1.51 | 1.51 |
| nut slot depth tolerance offset | 0.1 | 0.1 | 0.1 |
| nut height | 2 | 2 | 2 |
| nut pocket length | 8.7 | 8.7 | 8.7 |
| screw end slot offset | 0.4 | 0 | 0.4 |
| reinforcer offset | 3 | 3 | 3 |
| reinforcer top offset | -0.5 | -0.1 | 0 |

**screw position** (3 nodes)

| Input | FRONT | GripD | GripX |
|---|---|---|---|
| position | (21.3032, -10.94, 46.6) | (59, -75, 43.76) | (64.94, -80.54, 43.76) |
| rotation | 3.1416 | 1.5708 | 1.5708 |

## `GripX scrollwheel` (frame SCROLLWHEEL)


**scroll parameters** (label "scroll")

| Input | Value |
|---|---|
| scroll radius offset | -1.15 |
| scroll width offset | 0 |
| scroll wheel tolerance | 0.7 |
| scroll wheel shift X | -3.6 |

## `GripX hollow parameters` (frame SHELL )


**hollow  parameters**

| Input | Value |
|---|---|
| voxel remesh size | ← group `global outputs` |
| band remesh width | 3 |
| smooth sdf | 3 |
| protect geometry | 0.81 |
| shell thickness | 1.2 |

**top face parameters**

| Input | Value |
|---|---|
| top thickness | 2.4 |
| top grid | on |
| grid thickness | 1.2 |
| parts offset | 1.6 |
| stick offset | 3 |
| smooth grid | 3 |

## `GripX shell middle plate parameters` (frame SHELL )


**middle plate parameters** (2 nodes)

| Input | middle plate parameters (not connected) | middle plate parameters.001 |
|---|---|---|
| insert height | 1.6 | 1.76 |
| inset width | 2.4 | 3 |
| plate inset width | 2.4 | 2.6 |
| hook inset | 0.4 | 0.4 |
| hook height | 0.5 | 0.5 |
| xy tolerance | 0.1 | -0.1 |
| hook to top | 0.48 | 0.64 |
| Z tolerance | 0.16 | 0.16 |
| fit Z tolerance | 0 | -0.2 |
| inner Z tolerance | 0.16 | 0.16 |
| inner xy tolerance | 0.4 | 0.4 |
| pcb pocket thickness | 1.28 | 1.28 |
| pcb pocket tolerance | 0.32 | 0.32 |
| rim slant height | 6 | 3 |
| rim slant outset | 6 | 16 |
| slant height | 0.92 | 0.92 |

## `GripX stick L parameters` (frame STICKS)


**basic stick parameters** (6 nodes)

| Input | basic stick parameters (not connected) | menu "Octagonal 18d range" (frame "Convex/concave") | menu "Xbox cap" | menu "Xbox cap easy print tall" | menu "Xbox Elite2 stick base" | menu "Xbox cap easy print short (60%)" |
|---|---|---|---|---|---|---|
| stick top radius | 7.1 | 6.8 | 8.3 | 8.3 | 2.98 | 8.3 |
| stick heght | 6.2 | 6.7 | 9.2 | 10.2 | 4 | 8.9 |
| range degrees | 20 | 18 | 16 | 17 | 15.3 | 11 |
| contact top offset | 1.3 | 1.5 | 3.1 | 1.9 | -3.5 | 1.9 |
| contact bottom offset | 1.5 | 2.6 | 2.6 | 2.6 | 5 | 2.6 |
| topmost offset | 0.4 | 0.5 | 4.4 | 4.2 | 4.9 | 3.9 |
| base size | 4.2 | 4.2 | 4.2 | 4.2 | 4.2 | 4.2 |
| base height | 8.8 | 9.3 | 9.3 | 9.3 | 9.3 | 9.3 |
| action | off | off | off | off | off | off |
| action rotation | 0.3927 | -0.4119 | 1.672 | -0.4119 | -0.4119 | -0.4119 |
| top bevel | 0.4 | 0.2 | 0.4 | 0.4 | 0.3 | 0.4 |
| middle bevel | 1.2 | 1.2 | 0 | 2 | 1.2 | 1 |
| shaft tolerance | 0.2 | 0.2 | 0.2 | 0.2 | 0.2 | 0.2 |
| shaft Z offset | 0 | -0.5 | -0.5 | -0.5 | -0.5 | -0.5 |

**advanced stick parameters** (6 nodes)

| Input | advanced stick parameters (not connected) | menu "Octagonal 18d range" (frame "Convex/concave") | menu "Xbox cap" | menu "Xbox cap easy print tall" | menu "Xbox Elite2 stick base" | menu "Xbox cap easy print short (60%)" |
|---|---|---|---|---|---|---|
| contact angle | 18.1 | 18 | 16 | 17 | 20 | 11 |
| hole bevel | 1 | 0 | 0 | 0 | 0 | 0 |
| hole radius | 8.3 | 8.3 | 8.3 | 8.3 | 8.3 | 8.3 |
| stick subdivision | 128 | 128 | 128 | 128 | 128 | 128 |
| stick hole subdivision | ← group `Stick hole subdivision` | 8 | 8 | 8 | 8 | 8 |
| stick  XY correction | ← group `sticks xy correction` | off | off | off | off | off |
| X correction | 0.05 | 0.05 | 0.05 | 0.05 | 0.05 | 0.05 |
| Y correction | 1 | 0.8 | 0.8 | 0.7 | 0.8 | 0.8 |
| shaft X correction | 0 | 0 | 0 | 0 | 0 | 0 |
| shaft Y correction | 0 | 0 | 0 | 0 | 0 | 0 |
| case cutout thickness  | 2.5 | 2 | 2 | 2 | 2 | 2 |
| swap stick rotation | off | off | off | off | off | off |

**icosahedron texture parameters** (6 nodes)

| Input | icosahedron texture parameters (not connected) | menu "Octagonal 18d range" (frame "Convex/concave") | menu "Xbox cap" | menu "Xbox cap easy print tall" | menu "Xbox Elite2 stick base" | menu "Xbox cap easy print short (60%)" |
|---|---|---|---|---|---|---|
| texture height | 0.2 | 0.5 | 0.4 | 0.4 | 0.4 | 0.4 |
| texture sharpness | 0.4 | 0.4 | 0.4 | 0.4 | 0.4 | 0.4 |
| icosahedron subdivisions | 3 | 3 | 3 | 3 | 3 | 3 |
| icosahedron curvature offset | -11.3 | -9.5 | -10.2 | -10.2 | -10.2 | -10.2 |

**shield parameters** (6 nodes)

| Input | shield parameters (not connected) | menu "Octagonal 18d range" (frame "Convex/concave") | menu "Xbox cap" | menu "Xbox cap easy print tall" | menu "Xbox Elite2 stick base" | menu "Xbox cap easy print short (60%)" |
|---|---|---|---|---|---|---|
| sheild | off | on | on | on | on | on |
| sheild height | 12.65 | 13.195 | 13.195 | 13.195 | 13.195 | 13.195 |
| shield cutoff height | 5.25 | 5.75 | 5.75 | 5.75 | 5.75 | 5.75 |
| sheild radius offset | 0.85 | 1.34 | 1.34 | 1.34 | 1.34 | 1.34 |
| FDM shield thickness | 0.1 | 0.2 | 0.2 | 0.2 | 0.2 | 0.2 |
| FDM Z correction | 2.25 | 2.3 | 2.3 | 2.3 | 2.3 | 2.3 |

**stick top parameters** (6 nodes)

| Input | stick top parameters (not connected) | menu "Octagonal 18d range" (frame "Convex/concave") | menu "Xbox cap" | menu "Xbox cap easy print tall" | menu "Xbox Elite2 stick base" | menu "Xbox cap easy print short (60%)" |
|---|---|---|---|---|---|---|
| top shape | circle | circle | circle | circle | circle | circle |
| swap top rotation | off | off | off | off | off | off |
| extrude texture | on | on | off | off | off | off |
| top curvature | concave | convex | flat | flat | flat | flat |
| texture type | icosahedron | icosahedron | icosahedron | icosahedron | icosahedron | icosahedron |
| square top subd | 4 | 4 | 4 | 4 | 4 | 4 |
| square morph | 0.08 | 0.25 | 0.25 | 0.25 | 0.25 | 0.25 |

**Stick hole subdivision** — **not connected**

| Input | Value |
|---|---|

**grid texture parameters** (6 nodes)

| Input | grid texture parameters (not connected) | menu "Octagonal 18d range" (frame "Convex/concave") | menu "Xbox cap" | menu "Xbox cap easy print tall" | menu "Xbox Elite2 stick base" | menu "Xbox cap easy print short (60%)" |
|---|---|---|---|---|---|---|
| texture height | 0.4 | 0.6 | 0.5 | 0.5 | 0.5 | 0.5 |
| texture subdivisions | 4 | 5 | 5 | 5 | 5 | 5 |
| texture sharpness | 0.4 | 0.5 | 0.4 | 0.4 | 0.4 | 0.4 |
| grid curvature offset | 10.6 | 9 | 10.6 | 10.6 | 10.6 | 10.6 |
| scale | 1 | 1 | 1 | 1 | 1 | 1 |
| bottom xy correction | 0 | 0 | 0 | 0 | 0 | 0 |
| bottom z correction | 0.1 | 0.1 | 0.1 | 0.1 | 0.1 | 0.1 |
| z offset | 0 | 0 | 0 | 0 | 0 | 0 |

**sticks xy correction** — **not connected**

| Input | Value |
|---|---|

- Menu Switch `Menu Switch` picks one of: "Xbox cap easy print tall", "Xbox cap", "Octagonal 18d range", "Xbox Elite2 stick base", "Xbox cap easy print short (60%)"

## `GripX stick R parameters` (frame STICKS)


**basic stick parameters** (4 nodes)

| Input | menu "normal" (frame "Convex/concave/flat") | menu "small round" (frame "Small round") | menu "small square" (frame "Small square") | menu "8 dir" (frame "8 dir ") |
|---|---|---|---|---|
| stick top radius | 5.75 | 4.5 | 4.5 | 4.5 |
| stick heght | 5.6 | 4.4 | 4.8 | 4.4 |
| range degrees | 18 | 18 | 18 | 14 |
| contact top offset | 1.1 | 1.1 | 1.1 | 1.1 |
| contact bottom offset | 2.48 | 2.48 | 2.48 | 2.48 |
| topmost offset | 0.6 | 0.6 | 0.6 | 0.6 |
| base size | 4.2 | 4.2 | 4.2 | 4.2 |
| base height | 9.3 | 9.3 | 9.3 | 9.3 |
| action | off | off | off | off |
| action rotation | -1.5708 | -1.5708 | -1.5708 | -1.5708 |
| top bevel | 0.4 | 0.4 | 0.4 | 0.4 |
| middle bevel | 1 | 1 | 1 | 1 |
| shaft tolerance | 0.2 | 0.2 | 0.2 | 0.2 |
| shaft Z offset | -0.5 | -0.5 | -0.5 | -0.5 |

**advanced stick parameters** (4 nodes)

| Input | menu "normal" (frame "Convex/concave/flat") | menu "small round" (frame "Small round") | menu "small square" (frame "Small square") | menu "8 dir" (frame "8 dir ") |
|---|---|---|---|---|
| contact angle | 18 | 18 | 18 | 14 |
| hole bevel | 2 | 2 | 2 | 2 |
| hole radius | 8 | 8 | 8 | 8 |
| stick subdivision | 128 | 128 | 256 | 8 |
| stick hole subdivision | 8 | 8 | 8 | 8 |
| stick  XY correction | off | on | on | on |
| X correction | 0.2 | 0.2 | 0.2 | 0.2 |
| Y correction | -0.1 | -0.1 | -0.1 | -0.1 |
| shaft X correction | 0 | 0 | 0 | 0 |
| shaft Y correction | 0 | 0 | 0 | 0 |
| case cutout thickness  | 2 | 2 | 2 | 2 |
| swap stick rotation | off | off | off | off |

**icosahedron texture parameters** (4 nodes)

| Input | menu "normal" (frame "Convex/concave/flat") | menu "small round" (frame "Small round") | menu "small square" (frame "Small square") | menu "8 dir" (frame "8 dir ") |
|---|---|---|---|---|
| texture height | 0.5 | 0.5 | 0.5 | 0.5 |
| texture sharpness | 0.4 | 0.4 | 0.4 | 0.4 |
| icosahedron subdivisions | 3 | 3 | 3 | 3 |
| icosahedron curvature offset | -9.6 | -6.7 | -7.4 | -7.4 |

**stick top parameters** (4 nodes)

| Input | menu "small round" (frame "Small round") | menu "small square" (frame "Small square") | menu "8 dir" (frame "8 dir ") | menu "normal" (frame "Convex/concave/flat") |
|---|---|---|---|---|
| top shape | circle | square | square | circle |
| swap top rotation | off | on | on | off |
| extrude texture | on | on | on | on |
| top curvature | convex | convex | flat | convex |
| texture type | icosahedron | grid | grid | icosahedron |
| square top subd | 4 | 4 | 4 | 4 |
| square morph | 0.08 | 0.08 | 0.08 | 0.08 |

**grid texture parameters** (4 nodes)

| Input | menu "normal" (frame "Convex/concave/flat") | menu "small round" (frame "Small round") | menu "small square" (frame "Small square") | menu "8 dir" (frame "8 dir ") |
|---|---|---|---|---|
| texture height | 0.5 | 0.4 | 0.7 | 0.7 |
| texture subdivisions | 5 | 4 | 4 | 4 |
| texture sharpness | 0.5 | 0.4 | 0.5 | 0.5 |
| grid curvature offset | 9 | 10 | -25 | -25 |
| scale | 1 | 1 | 0.95 | 0.95 |
| bottom xy correction | 0 | 0 | 0 | 0 |
| bottom z correction | 0.1 | 0.1 | 0.1 | 0.1 |
| z offset | 0 | 0 | 0 | 0 |

**shield parameters** (4 nodes)

| Input | menu "normal" (frame "Convex/concave/flat") | menu "small round" (frame "Small round") | menu "small square" (frame "Small square") | menu "8 dir" (frame "8 dir ") |
|---|---|---|---|---|
| sheild | on | on | on | on |
| sheild height | 13.195 | 13.195 | 13.195 | 13.195 |
| shield cutoff height | 7.5 | 7.5 | 7.5 | 8.4 |
| sheild radius offset | 1.34 | 1.34 | 1.34 | 1.34 |
| FDM shield thickness | 0.2 | 0.2 | 0.2 | 0.2 |
| FDM Z correction | 2.3 | 2.3 | 2.3 | 2.3 |

- Menu Switch `Menu Switch` picks one of: "normal", "small round", "small square", "8 dir"

## `GripX fill controls` (frame pattern)

The pattern presets of the case bodies. The variant parameter group reads the INDENT presets (one per `fill type`), the HOLLOW CUBIC ARRAY preset and the lattice preset; the presets in the SKELETON and HOLLOW frames are shown in the panel but nothing reads them.


### `GripX FischerKoch CY hollow parameters` (frame HOLLOW) — not read by anything

**fill parameters.001**

| Input | Value |
|---|---|
| voxel size | 0.8 |
| band width | 25 |
| scale | 0.4 |
| thickness | 0.6 |
| smooth meshed voxels | 7 |
| fill depth | 0 |
| fill depth smooth | 0 |
| boundary smooth | 0 |
| boundary offset | 5 |
| limit geometry smooth | 2 |
| droop height | 0 |
| droop depth | 0 |
| droop multiplier | 1 |
| rotate | (0, 0, 0) |
| translate | (-0.4, 0.8, 0) |
| scale axis | (1, 1, 1) |
| protect geometry | 1 |
| smooth protected geometry | 3 |
| shell thickness | 2.7 |
| shell protect geometry | 3 |
| shell smooth protected | 3 |
| insert rim depth | 1 |
| insert rim height | 2 |
| protect flat surface | 3 |
| smooth flat surface | 3 |
| insert rim smooth | 5 |
| smooth pattern | 6 |
| protect sharp | 3 |
| smooth sharp | 5 |


### `GripX FischerKoch S hollow parameters` (frame HOLLOW) — not read by anything

**fill parameters.001**

| Input | Value |
|---|---|
| voxel size | 0.8 |
| band width | 25 |
| scale | 0.2 |
| thickness | 0.6 |
| smooth meshed voxels | 10 |
| fill depth | 0 |
| fill depth smooth | 0 |
| boundary smooth | 0 |
| boundary offset | 0 |
| limit geometry smooth | 2 |
| droop height | 0 |
| droop depth | 0 |
| droop multiplier | 1 |
| rotate | (0, 0, 0) |
| translate | (-0.4, 0.8, 0) |
| scale axis | (1, 1, 1) |
| protect geometry | 1 |
| smooth protected geometry | 3 |
| shell thickness | 2.7 |
| shell protect geometry | 3 |
| shell smooth protected | 3 |
| insert rim depth | 1 |
| insert rim height | 2 |
| protect flat surface | 3 |
| smooth flat surface | 3 |
| insert rim smooth | 5 |
| smooth pattern | 6 |
| protect sharp | 3 |
| smooth sharp | 5 |


### `GripX cubic hollow parameters` (frame HOLLOW)

**fill parameters.001**

| Input | Value |
|---|---|
| voxel size | 0.5 |
| band width | 2 |
| scale | 3 |
| thickness | 0.4 |
| smooth meshed voxels | 0 |
| fill depth | 20 |
| fill depth smooth | 0 |
| boundary smooth | 10 |
| boundary offset | 10 |
| limit geometry smooth | 5 |
| droop height | 0 |
| droop depth | 0 |
| droop multiplier | 1 |
| rotate | (0, 0, 0) |
| translate | (0, 0, 0) |
| scale axis | (1, 1, 1) |
| protect geometry | 1 |
| smooth protected geometry | 3 |
| shell thickness | 2.7 |
| shell protect geometry | 3 |
| shell smooth protected | 3 |
| insert rim depth | -0.4 |
| insert rim height | 3.5 |
| protect flat surface | 3 |
| smooth flat surface | 0 |
| insert rim smooth | 4 |
| smooth pattern | 3 |
| protect sharp | 3 |
| smooth sharp | 5 |


### `GripX diamond hollow parameters` (frame HOLLOW) — not read by anything

**fill parameters.001**

| Input | Value |
|---|---|
| voxel size | 0.8 |
| band width | 25 |
| scale | 0.3 |
| thickness | 0.7 |
| smooth meshed voxels | 10 |
| fill depth | 0 |
| fill depth smooth | 0 |
| boundary smooth | 0 |
| boundary offset | 5 |
| limit geometry smooth | 2 |
| droop height | 0 |
| droop depth | 0 |
| droop multiplier | 1 |
| rotate | (0.7854, 0.7854, 0.7854) |
| translate | (-0.4, 0.8, 0) |
| scale axis | (1, 1, 1) |
| protect geometry | 1 |
| smooth protected geometry | 3 |
| shell thickness | 2.7 |
| shell protect geometry | 3 |
| shell smooth protected | 3 |
| insert rim depth | 1 |
| insert rim height | 2 |
| protect flat surface | 3 |
| smooth flat surface | 3 |
| insert rim smooth | 5 |
| smooth pattern | 6 |
| protect sharp | 3 |
| smooth sharp | 5 |


### `GripX gyroid hollow parameters` (frame HOLLOW) — not read by anything

**fill parameters.001**

| Input | Value |
|---|---|
| voxel size | 1 |
| band width | 20 |
| scale | 0.5 |
| thickness | 0.8 |
| smooth meshed voxels | 10 |
| fill depth | 20 |
| fill depth smooth | 0 |
| boundary smooth | 0 |
| boundary offset | 5 |
| limit geometry smooth | 2 |
| droop height | 0 |
| droop depth | 0 |
| droop multiplier | 1 |
| rotate | (0, 0, 0) |
| translate | (-0.4, 0.8, 0) |
| scale axis | (1, 1, 1) |
| protect geometry | 1 |
| smooth protected geometry | 3 |
| shell thickness | 2.7 |
| shell protect geometry | 3 |
| shell smooth protected | 3 |
| insert rim depth | 1 |
| insert rim height | 2 |
| protect flat surface | 3 |
| smooth flat surface | 3 |
| insert rim smooth | 5 |
| smooth pattern | 6 |
| protect sharp | 3 |
| smooth sharp | 5 |


### `GripX primitive hollow parameters` (frame HOLLOW) — not read by anything

**fill parameters.001**

| Input | Value |
|---|---|
| voxel size | 1 |
| band width | 20 |
| scale | 0.3 |
| thickness | 1 |
| smooth meshed voxels | 10 |
| fill depth | 20 |
| fill depth smooth | 0 |
| boundary smooth | 0 |
| boundary offset | 5 |
| limit geometry smooth | 2 |
| droop height | 0 |
| droop depth | 0 |
| droop multiplier | 1 |
| rotate | (0.7854, 0.7854, 0.7854) |
| translate | (0, 0.8, 0) |
| scale axis | (1, 1, 1) |
| protect geometry | 1 |
| smooth protected geometry | 3 |
| shell thickness | 2.7 |
| shell protect geometry | 3 |
| shell smooth protected | 3 |
| insert rim depth | 1 |
| insert rim height | 2 |
| protect flat surface | 3 |
| smooth flat surface | 3 |
| insert rim smooth | 5 |
| smooth pattern | 6 |
| protect sharp | 3 |
| smooth sharp | 5 |


### `GripX voronoi  hollow parameters` (frame HOLLOW) — not read by anything

**fill parameters.001**

| Input | Value |
|---|---|
| voxel size | 0.8 |
| band width | 30 |
| scale | 0.7 |
| thickness | 0.06 |
| smooth meshed voxels | 10 |
| fill depth | 20 |
| fill depth smooth | 3.6 |
| boundary smooth | 0 |
| boundary offset | 4 |
| limit geometry smooth | 6.5 |
| droop height | 0 |
| droop depth | 0 |
| droop multiplier | 1 |
| rotate | (0.7854, 0, 0.7854) |
| translate | (0, 10, -5) |
| scale axis | (1, 1, 0.5) |
| protect geometry | 1 |
| smooth protected geometry | 3 |
| shell thickness | 2.7 |
| shell protect geometry | 3 |
| shell smooth protected | 3 |
| insert rim depth | 1 |
| insert rim height | 2 |
| protect flat surface | 3 |
| smooth flat surface | 3 |
| insert rim smooth | 5 |
| smooth pattern | 6 |
| protect sharp | 3 |
| smooth sharp | 5 |

**voronoi parameters**

| Input | Value |
|---|---|
| voronoi randomness | 0.5 |


### `GripX cubic hollow array parameters` (frame HOLOW CUBIC ARRAY)

**cubic fill array parameters**

| Input | Value |
|---|---|
| translate | (0, 12, 0) |
| rotate | (0, -0.262, -1.047) |
| interval | 10 |

**cubic fill array parameters**

| Input | Value |
|---|---|
| translate | (0, 4, 0) |
| rotate | (0.2618, 0, 0) |
| interval | 10 |

**cubic fill array parameters**

| Input | Value |
|---|---|
| translate | (0, 8.5, 0) |
| rotate | (1.6581, 0, -0.6109) |
| interval | 7 |

**cubic fill array parameters**

| Input | Value |
|---|---|
| translate | (0, 0, 0) |
| rotate | (0, 0, -0.6981) |
| interval | 8 |

**cubic fill array parameters**

| Input | Value |
|---|---|
| translate | (0, -6, 0) |
| rotate | (0, 0, -0.2618) |
| interval | 8 |

**cubic fill array parameters**

| Input | Value |
|---|---|
| translate | (0, 0, 2) |
| rotate | (-1.0472, 0, 0) |
| interval | 6 |


### `GripX FischerKoch CY indent parameters` (frame INDENT)

**fill parameters.001**

| Input | Value |
|---|---|
| voxel size | 1 |
| band width | 25 |
| scale | 0.18 |
| thickness | 0.5 |
| smooth meshed voxels | 10 |
| fill depth | 3 |
| fill depth smooth | 5 |
| boundary smooth | 3 |
| boundary offset | 2 |
| limit geometry smooth | 6 |
| droop height | 0 |
| droop depth | 0 |
| droop multiplier | 1 |
| rotate | (3.1416, 0, 0) |
| translate | (0, 0, 0) |
| scale axis | (1, 1, 1) |
| protect geometry | 1 |
| smooth protected geometry | 3 |
| shell thickness | 2.7 |
| shell protect geometry | 3 |
| shell smooth protected | 3 |
| insert rim depth | 1 |
| insert rim height | 2 |
| protect flat surface | 3 |
| smooth flat surface | 3 |
| insert rim smooth | 5 |
| smooth pattern | 6 |
| protect sharp | 3 |
| smooth sharp | 5 |


### `GripX FischerKoch S indent parameters` (frame INDENT)

**fill parameters.001**

| Input | Value |
|---|---|
| voxel size | 1 |
| band width | 20 |
| scale | 0.14 |
| thickness | 0.4 |
| smooth meshed voxels | 10 |
| fill depth | 3 |
| fill depth smooth | 3 |
| boundary smooth | 3.4 |
| boundary offset | 2 |
| limit geometry smooth | 6 |
| droop height | 0 |
| droop depth | 0 |
| droop multiplier | 1 |
| rotate | (3.1416, 0, 0) |
| translate | (0, 0, 0) |
| scale axis | (1, 1, 1) |
| protect geometry | 1 |
| smooth protected geometry | 3 |
| shell thickness | 2.7 |
| shell protect geometry | 3 |
| shell smooth protected | 3 |
| insert rim depth | 1 |
| insert rim height | 2 |
| protect flat surface | 3 |
| smooth flat surface | 3 |
| insert rim smooth | 5 |
| smooth pattern | 6 |
| protect sharp | 3 |
| smooth sharp | 5 |


### `GripX cubic indent parameters` (frame INDENT)

**fill parameters.001**

| Input | Value |
|---|---|
| voxel size | 1 |
| band width | 20 |
| scale | 0.4 |
| thickness | 1.5 |
| smooth meshed voxels | 10 |
| fill depth | 2 |
| fill depth smooth | 3 |
| boundary smooth | 3 |
| boundary offset | 2 |
| limit geometry smooth | 6 |
| droop height | 0 |
| droop depth | 0 |
| droop multiplier | 1 |
| rotate | (0, 0, 0) |
| translate | (0, 0, 0) |
| scale axis | (1, 1, 1) |
| protect geometry | 1 |
| smooth protected geometry | 3 |
| shell thickness | 2.7 |
| shell protect geometry | 3 |
| shell smooth protected | 3 |
| insert rim depth | 1 |
| insert rim height | 2 |
| protect flat surface | 3 |
| smooth flat surface | 3 |
| insert rim smooth | 5 |
| smooth pattern | 6 |
| protect sharp | 3 |
| smooth sharp | 5 |


### `GripX diamond indent parameters` (frame INDENT)

**fill parameters.001**

| Input | Value |
|---|---|
| voxel size | 1 |
| band width | 20 |
| scale | 0.2 |
| thickness | 0.5 |
| smooth meshed voxels | 10 |
| fill depth | 2 |
| fill depth smooth | 3 |
| boundary smooth | 3.4 |
| boundary offset | 2 |
| limit geometry smooth | 6 |
| droop height | 0 |
| droop depth | 0 |
| droop multiplier | 1 |
| rotate | (3.1416, 0, 0) |
| translate | (0, 0, 0) |
| scale axis | (1, 1, 1) |
| protect geometry | 1 |
| smooth protected geometry | 3 |
| shell thickness | 2.7 |
| shell protect geometry | 3 |
| shell smooth protected | 3 |
| insert rim depth | 1 |
| insert rim height | 2 |
| protect flat surface | 3 |
| smooth flat surface | 3 |
| insert rim smooth | 5 |
| smooth pattern | 6 |
| protect sharp | 3 |
| smooth sharp | 5 |


### `GripX gyroid indent parameters` (frame INDENT)

**fill parameters.001**

| Input | Value |
|---|---|
| voxel size | 1 |
| band width | 20 |
| scale | 0.3 |
| thickness | 0.7 |
| smooth meshed voxels | 10 |
| fill depth | 2.2 |
| fill depth smooth | 2 |
| boundary smooth | 3 |
| boundary offset | 2 |
| limit geometry smooth | 3 |
| droop height | 0 |
| droop depth | 0 |
| droop multiplier | 1 |
| rotate | (3.1416, 0, 0) |
| translate | (0, 0, 0) |
| scale axis | (1, 1, 1) |
| protect geometry | 1 |
| smooth protected geometry | 3 |
| shell thickness | 2.7 |
| shell protect geometry | 3 |
| shell smooth protected | 3 |
| insert rim depth | 1 |
| insert rim height | 2 |
| protect flat surface | 3 |
| smooth flat surface | 3 |
| insert rim smooth | 5 |
| smooth pattern | 6 |
| protect sharp | 3 |
| smooth sharp | 5 |


### `GripX primitive indent parameters` (frame INDENT)

**fill parameters.001**

| Input | Value |
|---|---|
| voxel size | 0.8 |
| band width | 20 |
| scale | 0.35 |
| thickness | 0.5 |
| smooth meshed voxels | 10 |
| fill depth | 2 |
| fill depth smooth | 3 |
| boundary smooth | 3 |
| boundary offset | 2 |
| limit geometry smooth | 6 |
| droop height | 0 |
| droop depth | 0 |
| droop multiplier | 1 |
| rotate | (3.1416, 0, 0) |
| translate | (0, 0, 0) |
| scale axis | (1, 1, 1) |
| protect geometry | 1 |
| smooth protected geometry | 3 |
| shell thickness | 2.7 |
| shell protect geometry | 3 |
| shell smooth protected | 3 |
| insert rim depth | 1 |
| insert rim height | 2 |
| protect flat surface | 3 |
| smooth flat surface | 3 |
| insert rim smooth | 5 |
| smooth pattern | 6 |
| protect sharp | 3 |
| smooth sharp | 5 |


### `GripX voroni indent parameters` (frame INDENT)

**fill parameters.001**

| Input | Value |
|---|---|
| voxel size | 1 |
| band width | 20 |
| scale | 0.6 |
| thickness | 0.001 |
| smooth meshed voxels | 10 |
| fill depth | 3 |
| fill depth smooth | 3 |
| boundary smooth | 3 |
| boundary offset | 2 |
| limit geometry smooth | 3 |
| droop height | 0 |
| droop depth | 0 |
| droop multiplier | 1 |
| rotate | (0, 0, 0) |
| translate | (0, 0, 0) |
| scale axis | (1, 1, 1) |
| protect geometry | 1 |
| smooth protected geometry | 3 |
| shell thickness | 2.7 |
| shell protect geometry | 3 |
| shell smooth protected | 3 |
| insert rim depth | 1 |
| insert rim height | 2 |
| protect flat surface | 3 |
| smooth flat surface | 3 |
| insert rim smooth | 5 |
| smooth pattern | 6 |
| protect sharp | 3 |
| smooth sharp | 5 |

**voronoi parameters**

| Input | Value |
|---|---|
| voronoi randomness | 1 |


### `GripX hollow fill middle plate parameters` (frame MIDDLE PLATE) — not read by anything

**middle plate parameters**

| Input | Value |
|---|---|
| insert height | 1.8 |
| inset width | 3.4 |
| plate inset width | 2.3 |
| hook inset | 0.4 |
| hook height | 0.5 |
| xy tolerance | 0.1 |
| hook to top | 0.5 |
| Z tolerance | 0.3 |
| fit Z tolerance | 0 |
| inner Z tolerance | 0.3 |
| inner xy tolerance | 0.4 |
| pcb pocket thickness | 1.6 |
| pcb pocket tolerance | 0.3 |
| rim slant height | 6 |
| rim slant outset | 6 |
| slant height | 0.92 |


### `GripX FischerKoch CY skeleton parameters` (frame SKELETON) — not read by anything

**fill parameters.001**

| Input | Value |
|---|---|
| voxel size | 1 |
| band width | 25 |
| scale | 0.18 |
| thickness | 0.5 |
| smooth meshed voxels | 7 |
| fill depth | 10 |
| fill depth smooth | 0 |
| boundary smooth | 3 |
| boundary offset | 2 |
| limit geometry smooth | 2 |
| droop height | 0 |
| droop depth | -3 |
| droop multiplier | 1 |
| rotate | (0, 0, 0) |
| translate | (-0.4, 0.8, 0) |
| scale axis | (1, 1, 1) |
| protect geometry | 1 |
| smooth protected geometry | 3 |
| shell thickness | 2.7 |
| shell protect geometry | 3 |
| shell smooth protected | 3 |
| insert rim depth | 1 |
| insert rim height | 2 |
| protect flat surface | 3 |
| smooth flat surface | 3 |
| insert rim smooth | 5 |
| smooth pattern | 6 |
| protect sharp | 3 |
| smooth sharp | 5 |


### `GripX FischerKoch S skeleton parameters` (frame SKELETON) — not read by anything

**fill parameters.001**

| Input | Value |
|---|---|
| voxel size | 1 |
| band width | 25 |
| scale | 0.14 |
| thickness | 0.4 |
| smooth meshed voxels | 10 |
| fill depth | 10 |
| fill depth smooth | 0 |
| boundary smooth | 3 |
| boundary offset | 2 |
| limit geometry smooth | 2 |
| droop height | 4 |
| droop depth | -3 |
| droop multiplier | 1 |
| rotate | (0, 0, 0) |
| translate | (-0.4, 0.8, 0) |
| scale axis | (1, 1, 1) |
| protect geometry | 1 |
| smooth protected geometry | 3 |
| shell thickness | 2.7 |
| shell protect geometry | 3 |
| shell smooth protected | 3 |
| insert rim depth | 1 |
| insert rim height | 2 |
| protect flat surface | 3 |
| smooth flat surface | 3 |
| insert rim smooth | 5 |
| smooth pattern | 6 |
| protect sharp | 3 |
| smooth sharp | 5 |


### `GripX cubic skeleton parameters` (frame SKELETON) — not read by anything

**fill parameters.001**

| Input | Value |
|---|---|
| voxel size | 0.8 |
| band width | 25 |
| scale | 0.2 |
| thickness | 1.4 |
| smooth meshed voxels | 10 |
| fill depth | 10 |
| fill depth smooth | 0 |
| boundary smooth | 2 |
| boundary offset | 1 |
| limit geometry smooth | 2 |
| droop height | 4 |
| droop depth | -3 |
| droop multiplier | 1 |
| rotate | (0, 0, 0) |
| translate | (-0.4, 0.8, 0) |
| scale axis | (1, 1, 1) |
| protect geometry | 1 |
| smooth protected geometry | 3 |
| shell thickness | 2.7 |
| shell protect geometry | 3 |
| shell smooth protected | 3 |
| insert rim depth | 1 |
| insert rim height | 2 |
| protect flat surface | 3 |
| smooth flat surface | 3 |
| insert rim smooth | 5 |
| smooth pattern | 6 |
| protect sharp | 3 |
| smooth sharp | 5 |


### `GripX diamond skeleton parameters` (frame SKELETON) — not read by anything

**fill parameters.001**

| Input | Value |
|---|---|
| voxel size | 1 |
| band width | 25 |
| scale | 0.2 |
| thickness | 0.5 |
| smooth meshed voxels | 10 |
| fill depth | 10 |
| fill depth smooth | 0 |
| boundary smooth | 3.4 |
| boundary offset | 2 |
| limit geometry smooth | 2 |
| droop height | 4 |
| droop depth | -3 |
| droop multiplier | 1 |
| rotate | (0.7854, 0, 0.7854) |
| translate | (0, 0.8, 0) |
| scale axis | (1, 1, 1) |
| protect geometry | 1 |
| smooth protected geometry | 3 |
| shell thickness | 2.7 |
| shell protect geometry | 3 |
| shell smooth protected | 3 |
| insert rim depth | 1 |
| insert rim height | 2 |
| protect flat surface | 3 |
| smooth flat surface | 3 |
| insert rim smooth | 5 |
| smooth pattern | 6 |
| protect sharp | 3 |
| smooth sharp | 5 |


### `GripX gyroid skeleton parameters` (frame SKELETON) — not read by anything

**fill parameters.001**

| Input | Value |
|---|---|
| voxel size | 1 |
| band width | 20 |
| scale | 0.3 |
| thickness | 0.7 |
| smooth meshed voxels | 10 |
| fill depth | 20 |
| fill depth smooth | 0 |
| boundary smooth | 3 |
| boundary offset | 2 |
| limit geometry smooth | 2 |
| droop height | 4 |
| droop depth | -3 |
| droop multiplier | 1 |
| rotate | (0, 0, 0) |
| translate | (-0.4, 0.8, 0) |
| scale axis | (1, 1, 1) |
| protect geometry | 1 |
| smooth protected geometry | 3 |
| shell thickness | 2.7 |
| shell protect geometry | 3 |
| shell smooth protected | 3 |
| insert rim depth | 1 |
| insert rim height | 2 |
| protect flat surface | 3 |
| smooth flat surface | 3 |
| insert rim smooth | 5 |
| smooth pattern | 6 |
| protect sharp | 3 |
| smooth sharp | 5 |


### `GripX primitive skeleton parameters` (frame SKELETON) — not read by anything

**fill parameters.001**

| Input | Value |
|---|---|
| voxel size | 0.8 |
| band width | 20 |
| scale | 0.35 |
| thickness | 0.5 |
| smooth meshed voxels | 10 |
| fill depth | 10 |
| fill depth smooth | 0 |
| boundary smooth | 3 |
| boundary offset | 2 |
| limit geometry smooth | 2 |
| droop height | 4 |
| droop depth | -3 |
| droop multiplier | 1 |
| rotate | (0, 0, 0) |
| translate | (-0.4, 0.8, 0) |
| scale axis | (1, 1, 1) |
| protect geometry | 1 |
| smooth protected geometry | 3 |
| shell thickness | 2.7 |
| shell protect geometry | 3 |
| shell smooth protected | 3 |
| insert rim depth | 1 |
| insert rim height | 2 |
| protect flat surface | 3 |
| smooth flat surface | 3 |
| insert rim smooth | 5 |
| smooth pattern | 6 |
| protect sharp | 3 |
| smooth sharp | 5 |


### `GripX voronoi skeleton parameters` (frame SKELETON) — not read by anything

**fill parameters.001**

| Input | Value |
|---|---|
| voxel size | 1 |
| band width | 25 |
| scale | 0.6 |
| thickness | 0.001 |
| smooth meshed voxels | 10 |
| fill depth | 20 |
| fill depth smooth | 0 |
| boundary smooth | 3 |
| boundary offset | 2 |
| limit geometry smooth | 6.5 |
| droop height | 4 |
| droop depth | -3 |
| droop multiplier | 1 |
| rotate | (0, 0, 0) |
| translate | (0, 0, 0) |
| scale axis | (1, 1, 1) |
| protect geometry | 1 |
| smooth protected geometry | 3 |
| shell thickness | 2.7 |
| shell protect geometry | 3 |
| shell smooth protected | 3 |
| insert rim depth | 1 |
| insert rim height | 2 |
| protect flat surface | 3 |
| smooth flat surface | 3 |
| insert rim smooth | 5 |
| smooth pattern | 6 |
| protect sharp | 3 |
| smooth sharp | 5 |

**voronoi parameters**

| Input | Value |
|---|---|
| voronoi randomness | 1 |

