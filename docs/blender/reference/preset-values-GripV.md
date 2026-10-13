# Preset values: GripV

Every value typed into the GripV preset groups, as saved in `blender/Grip.blend`. Generated from the file; angles are in radians as Blender stores them. "Live" means the node is wired to the preset's output; values on nodes marked **not connected** have no effect. What each input does is described on the part pages.

The presets are listed in the order of the frames in the `GripV controls` panel.


## `GripV abxy` (frame BUTTONS)


- **tolerance set** `tolerance set`: tight 0.12 / default 0.16 / loose 0.24, picked by the global `tolerance` menu, feeds `button parameters` › button tolerance

- **tolerance set** `tolerance set.001`: tight 0.1 / default 0 / loose -0.1, picked by the global `cap tolerance` menu, feeds `caps parameters` › caps fit tolerance

**button parameters**

| Input | Value |
|---|---|
| button tolerance | ← tolerance set `tolerance`: 0.12 / 0.16 / 0.24 |
| SMD height | 4.4 |
| button height | 2.56 |
| button height offset | -0.5 |
| top bevel | 0.8 |
| case middle bevel | 0.2 |
| bottom bevel | 1 |
| middle bevel | 0.2 |
| stopper position | 11 |
| stopper height | 1.6 |
| stopper offset | 0.6 |
| case bool bevel | 1 |

**capacitive plate parameters**

| Input | Value |
|---|---|
| capacitive | knob |
| screw hole | on |
| capacitive plate tolerance | 0.4 |
| capacitive plate stem tolerance | -0.1 |
| plate button offset | 1 |

**caps parameters**

| Input | Value |
|---|---|
| caps fit tolerance | ← tolerance set `cap tolerance`: 0.1 / 0 / -0.1 |
| caps fit Z tolerance | 0 |
| caps fit Z | 2.08 |
| cap case tolerance | 0.6 |
| cap bevel | 1.6 |
| cap bevel subd | 16 |
| cap bevel cutoff | on |
| bevel cutoff | 0.9599 |
| caps flex cut | 1 |
| button cap | on |
| caps offset | 2.08 |
| button cap travel distance | 1.92 |
| caps additional size | 0.3 |
| cap base fillet | 2.85 |
| cap base fillet subd | 16 |
| custom cap | off |
| caps hook inset | 0.3 |
| caps hook height | 1.12 |
| caps depth | 2.08 |

**curve parameters**

| Input | Value |
|---|---|
| width | 12 |
| octagonal fillet | on |
| fillet | 1.6 |
| fillet subdiv | 16 |
| fillet tolerance | 1 |

**marks parameters**

| Input | Value |
|---|---|
| bump | 0.16 |
| mark depth | 0.16 |
| insertion | off |
| type | custom |
| L-R side | off |
| text | ← GeometryNodeIndexSwitch `Index Switch` |
| parameters | button tolerance |
| font size | 5 |
| translate | (-0.2, 5.6, 0) |
| rotate text | 0 |
| rotate | 1.5708 |
| axis | Y |
| side | min |
| Decimals | 2 |
| Character Spacing | 1.1 |
| Word Spacing | 0 |
| Line Spacing | 0.7 |
| Text Box Width | 0.1 |

- Index Switch `Index Switch` (marks text): Index=0, 0=T, 1=D, 2=L

## `GripV dpad` (frame BUTTONS)


- **tolerance set** `tolerance set`: tight 0.12 / default 0.16 / loose 0.24, picked by the global `tolerance` menu, feeds `button parameters` › button tolerance

- **tolerance set** `tolerance set.001`: tight 0.1 / default 0 / loose -0.1, picked by the global `cap tolerance` menu, feeds `caps parameters` › caps fit tolerance

**button parameters**

| Input | Value |
|---|---|
| button tolerance | ← tolerance set `tolerance`: 0.12 / 0.16 / 0.24 |
| SMD height | 4.4 |
| button height | 2.56 |
| button height offset | -0.5 |
| top bevel | 0.8 |
| case middle bevel | 0.2 |
| bottom bevel | 1 |
| middle bevel | 0.2 |
| stopper position | 11 |
| stopper height | 1.6 |
| stopper offset | 0.6 |
| case bool bevel | 1 |

**curve parameters**

| Input | Value |
|---|---|
| width | 12 |
| octagonal fillet | on |
| fillet | 1.6 |
| fillet subdiv | 16 |
| fillet tolerance | 1 |

**caps parameters**

| Input | Value |
|---|---|
| caps fit tolerance | ← tolerance set `cap tolerance`: 0.1 / 0 / -0.1 |
| caps fit Z tolerance | 0 |
| caps fit Z | 2.08 |
| cap case tolerance | 0.6 |
| cap bevel | 1.6 |
| cap bevel subd | 16 |
| cap bevel cutoff | on |
| bevel cutoff | 0.9599 |
| caps flex cut | 0 |
| button cap | on |
| caps offset | 2.08 |
| button cap travel distance | 1.92 |
| caps additional size | 0 |
| cap base fillet | 3.5 |
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

## `GripV home` (frame BUTTONS)


- **tolerance set** `tolerance set`: tight 0.12 / default 0.16 / loose 0.24, picked by the global `tolerance` menu, feeds `button parameters` › button tolerance

- **tolerance set** `tolerance set.001`: tight 0.1 / default 0 / loose -0.1, picked by the global `cap tolerance` menu, feeds `caps parameters` › caps fit tolerance

**button parameters**

| Input | Value |
|---|---|
| button tolerance | ← tolerance set `tolerance`: 0.12 / 0.16 / 0.24 |
| SMD height | 4.4 |
| button height | 2.56 |
| button height offset | -0.5 |
| top bevel | 0.8 |
| case middle bevel | 0.2 |
| bottom bevel | 1 |
| middle bevel | 0.4 |
| stopper position | 11 |
| stopper height | 1.6 |
| stopper offset | 0.6 |
| case bool bevel | 1 |

**curve parameters**

| Input | Value |
|---|---|
| width | 12 |
| octagonal fillet | on |
| fillet | 1.6 |
| fillet subdiv | 16 |
| fillet tolerance | 1 |

**caps parameters**

| Input | Value |
|---|---|
| caps fit tolerance | ← tolerance set `cap tolerance`: 0.1 / 0 / -0.1 |
| caps fit Z tolerance | 0 |
| caps fit Z | 2.08 |
| cap case tolerance | 0.6 |
| cap bevel | 1.6 |
| cap bevel subd | 16 |
| cap bevel cutoff | on |
| bevel cutoff | 0.9599 |
| caps flex cut | 1.4 |
| button cap | on |
| caps offset | 2.08 |
| button cap travel distance | 1.92 |
| caps additional size | 1 |
| cap base fillet | 3.6 |
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

## `GripV select` (frame BUTTONS)


- **tolerance set** `tolerance set`: tight 0.12 / default 0.16 / loose 0.24, picked by the global `tolerance` menu, feeds `button parameters` › button tolerance

- **tolerance set** `tolerance set.001`: tight 0.1 / default 0 / loose -0.1, picked by the global `cap tolerance` menu, feeds `caps parameters` › caps fit tolerance

**button parameters**

| Input | Value |
|---|---|
| button tolerance | ← tolerance set `tolerance`: 0.12 / 0.16 / 0.24 |
| SMD height | 4.4 |
| button height | 2.56 |
| button height offset | -0.5 |
| top bevel | 0.8 |
| case middle bevel | 0.2 |
| bottom bevel | 1 |
| middle bevel | 0.2 |
| stopper position | 11 |
| stopper height | 1.6 |
| stopper offset | 0.6 |
| case bool bevel | 1 |

**curve parameters**

| Input | Value |
|---|---|
| width | 8.96 |
| octagonal fillet | on |
| fillet | 1.6 |
| fillet subdiv | 8 |
| fillet tolerance | 1 |

**caps parameters**

| Input | Value |
|---|---|
| caps fit tolerance | ← tolerance set `cap tolerance`: 0.1 / 0 / -0.1 |
| caps fit Z tolerance | 0 |
| caps fit Z | 2.08 |
| cap case tolerance | 0.6 |
| cap bevel | 1.6 |
| cap bevel subd | 16 |
| cap bevel cutoff | on |
| bevel cutoff | 0.9599 |
| caps flex cut | 0.6 |
| button cap | on |
| caps offset | 0.56 |
| button cap travel distance | 1.92 |
| caps additional size | 1.2 |
| cap base fillet | 3 |
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

## `GripV dpad stick` (frame DPAD STICK)


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
| hook z tolerance | 0.32 |
| inner hook tolerance | 0.6 |
| hook extrude | 1.6 |
| flex cut width | 0.4 |
| flex cut depth | 1 |
| ball stopper position | 4.3 |
| cap fit tolerance | 0 |
| cap oval offset | 0.7 |

- Value node `Value` = 5.44 (not connected)

- Value node `Value.001` = 14.72 (not connected)

## `GripV cover parameters` (frame PCB AND BATTERY)


**basic cover parameters** (frame "battery")

| Input | Value |
|---|---|
| y tolerance | 0.15 |
| x tolerance | 0.2 |

**advanced cover parameters** (frame "battery")

| Input | Value |
|---|---|
| lip height | 2.6 |
| battery length | 63.3 |
| battery width | 35.4 |
| battery height | 4.8 |
| flex width | 1 |
| lip width | 0.7 |
| lip hook height | 2 |
| shift Y | -48 |
| cover base thickness | 1 |
| cover base overlap | 0.5 |
| appendix | off |
| appendix height | 0.95 |
| appendix length | 31.6 |
| appendix gap | 2.7 |
| compression offset | 0 |
| battery wire cut | 0 |
| test parameter | 0 |
| curved cover | on |

## `GripV pcb cutout paramters` (frame PCB AND BATTERY)


**pcb cutout parameters**

| Input | Value |
|---|---|
| PCB tolerance XY | 0.2 |
| PCB thickness | 2.08 |
| PCB support edge | 1.4 |
| PCB below height | 1.76 |

## `GripV pins parameters` (frame PINS)


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
| X | 69 |
| Y | -43.0119 |
| Z | 40 |

## `GripV  lever R1L1` (frame R1L1 LEVER)


- **tolerance set** `tolerance set`: tight -0.1 / default 0 / loose 0.1, picked by the global `press tolerance` menu, feeds `R1L1 lever parameters` › button press tol

**R1L1 lever parameters** (frame "lever R1L1")

| Input | Value |
|---|---|
| button press tol | ← tolerance set `press tolerance`: -0.1 / 0 / 0.1 |
| top bevel | 2.5 |
| stem tolerance | -0.025 |
| wdith | 20 |
| height | 8.16 |
| stem radius | ← Value node 2 |
| bumper Z tolerance | 0.52 |
| X tolerance | 1 |
| bevel inner | 3 |
| bevel inner sbdiv | 2 |
| overlap | -5.16 |
| overlap tolerance | 0.48 |
| button height | 0 |
| depth | 2 |
| insert depth | 5 |
| button inset offset | 1 |
| overlap slant | 2.9 |
| button front shift X | 18 |
| curved R1L1 | off |
| curved button thickness | 6.1 |
| curved button slant | -1 |
| curved button depth tolerance | 1 |
| curved button bevel | 1 |
| X | 28 |
| Y | -14 |
| Z | 40 |
| R1L1 flex | on |

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
| translate | (22, 0, 0) |
| rotate text | 0 |
| rotate | 0 |
| axis | Z |
| side | min |
| Decimals | 2 |
| Character Spacing | 1.1 |
| Word Spacing | 0 |
| Line Spacing | 0.7 |
| Text Box Width | 0.1 |

- Value node `Value` in frame "lever R1L1" = 2

- Index Switch `Index Switch` (marks text): Index=0, 0=T, 1=D, 2=L

## `GripV R2 parameters` (frame R2R4)


- **tolerance set** `tolerance set`: tight 0.5 / default 0.6 / loose 0.75, picked by the global `press tolerance` menu, feeds `trigger parameters.001` › button press tolerance

- **tolerance set** `tolerance set.001`: tight 0.16 / default 0.24 / loose 0.32, picked by the global `tolerance` menu, feeds `trigger parameters.001` › x tolerance, `trigger parameters.001` › radius tolerance

**trigger parameters** (2 nodes)

| Input | SNES (not connected) | more inward |
|---|---|---|
| button press tolerance | 0.4 | ← tolerance set `press tolerance`: 0.5 / 0.6 / 0.75 |
| tip angle offset | 1.5708 | -0.3491 |
| tip shear | 0 | -0.3491 |
| trigger length | 17 | 28 |
| top bevel | 0.4 | 1 |
| x tolerance | 0.3 | ← tolerance set `tolerance`: 0.16 / 0.24 / 0.32 |
| radius tolerance | 0.3 | ← tolerance set `tolerance`: 0.16 / 0.24 / 0.32 |
| bevel | 4.2 | 2.6 |
| bevel subd | 2 | 1 |
| bevel cutoff | 0.5 | 0.5 |
| action | off | off |
| trigger radius | 30 | 30 |
| stopper length | 10 | 15 |
| button rotation | 90 | 1.0472 |
| shift z | 5 | 5 |
| button radius offset | 5 | 5 |
| height | 9 | 11 |
| width | 11 | 12.96 |
| stopper height | 2 | 2 |
| subdivision length | 0.5 | 0.5 |
| button pressed height | 1.29 | 1.29 |
| x offset | 0 | 0 |

**marks parameters**

| Input | Value |
|---|---|
| bump | 0.16 |
| mark depth | 0.16 |
| insertion | off |
| type | custom |
| L-R side | on |
| text | ← GeometryNodeIndexSwitch `Index Switch` |
| parameters | trigger x tolerance, button press tolerance |
| font size | 5 |
| translate | (-4, -3, 0) |
| rotate text | 0 |
| rotate | 3.5779 |
| axis | X |
| side | max |
| Decimals | 2 |
| Character Spacing | 1.1 |
| Word Spacing | 0 |
| Line Spacing | 0.7 |
| Text Box Width | 0.1 |

- Index Switch `Index Switch` (marks text): Index=0, 0=T, 1=D, 2=L

- Value node `Value.001` "butt rot" in frame "za3tarani" = 40 (not connected)

- Value node `Value.002` "trig len" in frame "za3tarani" = 30 (not connected)

## `GripV R4 parameters` (frame R2R4)


- **tolerance set** `tolerance set`: tight 0.45 / default 0.55 / loose 0.75, picked by the global `press tolerance` menu, feeds `trigger parameters.001` › button press tolerance

- **tolerance set** `tolerance set.001`: tight 0.16 / default 0.24 / loose 0.32, picked by the global `tolerance` menu, feeds `trigger parameters.001` › x tolerance, `trigger parameters.001` › radius tolerance

**trigger parameters** (2 nodes)

| Input | SNES (not connected) | default |
|---|---|---|
| button press tolerance | 0.5 | ← tolerance set `press tolerance`: 0.45 / 0.55 / 0.75 |
| tip angle offset | 1.5708 | -0.5236 |
| tip shear | 0 | 0.1745 |
| trigger length | 16 | 40 |
| top bevel | 0.4 | 1 |
| x tolerance | 0.3 | ← tolerance set `tolerance`: 0.16 / 0.24 / 0.32 |
| radius tolerance | 0.3 | ← tolerance set `tolerance`: 0.16 / 0.24 / 0.32 |
| bevel | 4.2 | 2.6 |
| bevel subd | 2 | 1 |
| bevel cutoff | 0.5 | 0.5 |
| action | off | off |
| trigger radius | 80 | 80 |
| stopper length | 10 | 20 |
| button rotation | 90 | 0.6545 |
| shift z | 25 | 25 |
| button radius offset | 2 | 2 |
| height | 11 | 11 |
| width | 11 | 12.96 |
| stopper height | 2 | 2 |
| subdivision length | 0.5 | 0.5 |
| button pressed height | 1.65 | 1.29 |
| x offset | 0 | 0 |

**marks parameters**

| Input | Value |
|---|---|
| bump | 0.16 |
| mark depth | 0.16 |
| insertion | off |
| type | custom |
| L-R side | on |
| text | ← GeometryNodeIndexSwitch `Index Switch` |
| parameters | trigger x tolerance, button press tolerance |
| font size | 5 |
| translate | (-8, -4, 0) |
| rotate text | 0 |
| rotate | -0.4363 |
| axis | X |
| side | min |
| Decimals | 2 |
| Character Spacing | 1.1 |
| Word Spacing | 0 |
| Line Spacing | 0.7 |
| Text Box Width | 0.1 |

- Index Switch `Index Switch` (marks text): Index=0, 0=T, 1=D, 2=L

- Value node `Value.003` "butt rot" in frame "za3tarani" = 25 (not connected)

- Value node `Value` "trig lenght" in frame "za3tarani" = 43 (not connected)

## `GripV screw paramters` (frame SCREWS)


**screw parameters** (2 nodes)

| Input | front | back |
|---|---|---|
| screw hole diameter | 2.9 | 2.9 |
| screw head hole diameter | 5.2 | 5.2 |
| screw head hole height | 4.8 | 4.8 |
| screw length | 12.4 | 20.4 |
| screwdriver hole diameter | 5.2 | 8 |
| screwdriver guide slant height | 5 | 5 |
| nut width | 5.1 | 5.1 |
| nut slot hideout depth | 1.8 | 3.2 |
| nut slot depth tolerance offset | 0.1 | 0.1 |
| nut height | 2 | 2 |
| nut pocket length | 7 | 7 |
| screw end slot offset | 0.4 | 0.4 |
| reinforcer offset | 3 | 3 |
| reinforcer top offset | 0 | 0 |

**screw position** (2 nodes)

| Input | front | back |
|---|---|---|
| position | (26, -8.2, 46.6) | (69.8525, -62.8109, 46.6) |
| rotation | 3.1416 | 1.5708 |

## `GripV scrollwheel` (frame SCROLLWHEEL)


**scroll parameters** (label "scroll")

| Input | Value |
|---|---|
| scroll radius offset | -1.15 |
| scroll width offset | 0 |
| scroll wheel tolerance | 0.6 |
| scroll wheel shift X | -3.2 |

## `GripV stick L parameters` (frame STICKS)


**basic stick parameters** (frame "SQUARE HOLES LOW RANGE")

| Input | Value |
|---|---|
| stick top radius | 7 |
| stick heght | 7 |
| range degrees | 18 |
| contact top offset | 0.4 |
| contact bottom offset | 1.2 |
| topmost offset | 1.3 |
| base size | 4.2 |
| base height | 8.8 |
| action | off |
| action rotation | 3.1416 |
| top bevel | 0.6 |
| middle bevel | 1.2 |
| shaft tolerance | 0.2 |
| shaft Z offset | -0.5 |

**advanced stick parameters** (frame "SQUARE HOLES LOW RANGE")

| Input | Value |
|---|---|
| contact angle | 23 |
| hole bevel | 1 |
| hole radius | 9 |
| stick subdivision | 128 |
| stick hole subdivision | 128 |
| stick  XY correction | off |
| X correction | 0.05 |
| Y correction | 1 |
| shaft X correction | 0 |
| shaft Y correction | 0 |
| case cutout thickness  | 2.5 |
| swap stick rotation | on |

**icosahedron texture parameters** (frame "SQUARE HOLES LOW RANGE")

| Input | Value |
|---|---|
| texture height | 0.5 |
| texture sharpness | 0.4 |
| icosahedron subdivisions | 3 |
| icosahedron curvature offset | -10.2 |

**stick top parameters** (frame "SQUARE HOLES LOW RANGE")

| Input | Value |
|---|---|
| top shape | square |
| swap top rotation | on |
| extrude texture | on |
| top curvature | concave |
| texture type | grid |
| square top subd | 4 |
| square morph | 0.08 |

**grid texture parameters** (frame "SQUARE HOLES LOW RANGE")

| Input | Value |
|---|---|
| texture height | 0.4 |
| texture subdivisions | 5 |
| texture sharpness | 0.4 |
| grid curvature offset | 0 |
| scale | 1 |
| bottom xy correction | 0 |
| bottom z correction | 1 |
| z offset | -0.1 |

**shield parameters** (frame "SQUARE HOLES LOW RANGE")

| Input | Value |
|---|---|
| sheild | on |
| sheild height | 12.4 |
| shield cutoff height | 6.8 |
| sheild radius offset | 0 |
| FDM shield thickness | 0.2 |
| FDM Z correction | 1.8 |

## `GripV stick R parameters` (frame STICKS)


**basic stick parameters** (frame "SQUARE HOLES LOW RANGE")

| Input | Value |
|---|---|
| stick top radius | 7 |
| stick heght | 7 |
| range degrees | 18 |
| contact top offset | 0.4 |
| contact bottom offset | 1.2 |
| topmost offset | 1.3 |
| base size | 4.2 |
| base height | 8.8 |
| action | off |
| action rotation | 2.3562 |
| top bevel | 0.6 |
| middle bevel | 1.2 |
| shaft tolerance | 0.2 |
| shaft Z offset | -0.5 |

**advanced stick parameters** (frame "SQUARE HOLES LOW RANGE")

| Input | Value |
|---|---|
| contact angle | 23 |
| hole bevel | 1 |
| hole radius | 9 |
| stick subdivision | 128 |
| stick hole subdivision | 128 |
| stick  XY correction | off |
| X correction | 0.05 |
| Y correction | 1 |
| shaft X correction | 0 |
| shaft Y correction | 0 |
| case cutout thickness  | 2.5 |
| swap stick rotation | off |

**icosahedron texture parameters** (frame "SQUARE HOLES LOW RANGE")

| Input | Value |
|---|---|
| texture height | 0.5 |
| texture sharpness | 0.4 |
| icosahedron subdivisions | 3 |
| icosahedron curvature offset | -10.2 |

**stick top parameters** (frame "SQUARE HOLES LOW RANGE")

| Input | Value |
|---|---|
| top shape | circle |
| swap top rotation | on |
| extrude texture | on |
| top curvature | convex |
| texture type | icosahedron |
| square top subd | 4 |
| square morph | 0.08 |

**grid texture parameters** (frame "SQUARE HOLES LOW RANGE")

| Input | Value |
|---|---|
| texture height | 0.4 |
| texture subdivisions | 5 |
| texture sharpness | 0.4 |
| grid curvature offset | 10 |
| scale | 1 |
| bottom xy correction | 0 |
| bottom z correction | 0.1 |
| z offset | 0 |

**shield parameters** (frame "SQUARE HOLES LOW RANGE")

| Input | Value |
|---|---|
| sheild | on |
| sheild height | 12.4 |
| shield cutoff height | 6.8 |
| sheild radius offset | 0 |
| FDM shield thickness | 0.2 |
| FDM Z correction | 1.8 |

- Value node `Value` in frame "SQUARE HOLES LOW RANGE" = 7 (not connected)

## `GripV hollow parameters` (frame shell)


**hollow  parameters**

| Input | Value |
|---|---|
| voxel remesh size | ← group `global outputs` |
| band remesh width | 3 |
| smooth sdf | 3 |
| protect geometry | 0.84 |
| shell thickness | 1.2 |

**top face parameters**

| Input | Value |
|---|---|
| top thickness | ← GeometryNodeSwitch `Switch` |
| top grid | ← FunctionNodeInputBool `top grid` |
| grid thickness | 1.2 |
| parts offset | 1.6 |
| stick offset | 3 |
| smooth grid | 3 |

- Value node `Value` = 2.4

- Value node `Value.001` = 0.96

## `GripV middle plate parameters` (frame shell)


**middle plate parameters**

| Input | Value |
|---|---|
| insert height | 1.92 |
| inset width | 3 |
| plate inset width | 2.6 |
| hook inset | 0.6 |
| hook height | 0.64 |
| xy tolerance | 0 |
| hook to top | 0.32 |
| Z tolerance | 0.32 |
| fit Z tolerance | 0.1 |
| inner Z tolerance | 0.32 |
| inner xy tolerance | 0.4 |
| pcb pocket thickness | 1.28 |
| pcb pocket tolerance | 0.32 |
| rim slant height | 7 |
| rim slant outset | 6 |
| slant height | 0.92 |

## `GripV fill controls` (frame pattern)

The pattern presets of the case bodies. The variant parameter group reads the INDENT presets (one per `fill type`), the HOLLOW CUBIC ARRAY preset and the lattice preset; the presets in the SKELETON and HOLLOW frames are shown in the panel but nothing reads them.


### `GripV  lattice parameters`

**holllow lattice parameters**

| Input | Value |
|---|---|
| voxel remesh size | 0.6 |
| band remesh width | 2 |
| smooth sdf | 0 |
| protect geometry | 0.81 |
| shell thickness | 2.7 |

**fill parameters**

| Input | Value |
|---|---|
| voxel size | 0.6 |
| band width | 5 |
| scale | 3 |
| thickness | 1.6 |
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
| insert rim depth | -0.4 |
| insert rim height | 2.4 |
| insert rim smooth | 4 |
| smooth pattern | 3 |
| protect sharp | 3 |
| smooth sharp | 5 |

**top face parameters**

| Input | Value |
|---|---|
| top thickness | 2.4 |
| top grid | on |
| grid thickness | 1.2 |
| parts offset | 1.6 |
| stick offset | 3 |
| smooth grid | 3 |


### `GripV FischerKoch CY hollow parameters` (frame HOLLOW) — not read by anything

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


### `GripV FischerKoch S hollow parameters` (frame HOLLOW) — not read by anything

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


### `GripV cubic hollow parameters` (frame HOLLOW) — not read by anything

**hollow  parameters**

| Input | Value |
|---|---|
| voxel remesh size | 1 |
| band remesh width | 2 |
| smooth sdf | 0 |
| protect geometry | 0.81 |
| shell thickness | 2.7 |

**fill parameters**

| Input | Value |
|---|---|
| voxel size | 1 |
| band width | 5 |
| scale | 0.4 |
| thickness | 1 |
| fill depth | 0 |
| fill depth smooth | 0 |
| boundary smooth | 0 |
| boundary offset | 0.2 |
| limit geometry smooth | 0 |
| droop height | 4 |
| droop depth | -3 |
| droop multiplier | 1 |
| rotate | (0, 0, 0) |
| translate | (0, 0, 0) |
| scale axis | (1, 1, 1) |
| insert rim depth | 1 |
| insert rim height | 2 |
| insert rim smooth | 5 |
| smooth pattern | 6 |
| protect sharp | 3 |
| smooth sharp | 5 |

**top face parameters**

| Input | Value |
|---|---|
| top thickness | 2.4 |
| top grid | on |
| grid thickness | 1.2 |
| parts offset | 1.6 |
| stick offset | 3 |
| smooth grid | 3 |


### `GripV diamond hollow parameters` (frame HOLLOW) — not read by anything

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


### `GripV gyroid hollow parameters` (frame HOLLOW) — not read by anything

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


### `GripV primitive hollow parameters` (frame HOLLOW) — not read by anything

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


### `GripV voronoi  hollow parameters` (frame HOLLOW) — not read by anything

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


### `GripV cubic hollow array parameters` (frame HOLLOW CUBIC ARRAY)

**cubic fill array parameters**

| Input | Value |
|---|---|
| translate | (4, 0, 0) |
| rotate | (0, 0, 0.4538) |
| interval | 6 |

**cubic fill array parameters**

| Input | Value |
|---|---|
| translate | (0, -10, 0) |
| rotate | (0.2618, 0, 0.7854) |
| interval | 7 |

**cubic fill array parameters**

| Input | Value |
|---|---|
| translate | (3, 0, 0) |
| rotate | (1.2217, 0, -0.5236) |
| interval | 7 |


### `GripV FischerKoch CY indent parameters` (frame INDENT)

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


### `GripV FischerKoch S indent parameters` (frame INDENT)

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


### `GripV cubic indent parameters` (frame INDENT)

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


### `GripV diamond indent parameters` (frame INDENT)

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


### `GripV gyroid indent parameters` (frame INDENT)

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


### `GripV primitive indent parameters` (frame INDENT)

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


### `GripV voroni indent parameters` (frame INDENT)

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


### `GripV FischerKoch CY skeleton parameters` (frame SKELETON) — not read by anything

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


### `GripV FischerKoch S skeleton parameters` (frame SKELETON) — not read by anything

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


### `GripV cubic skeleton parameters` (frame SKELETON) — not read by anything

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


### `GripV diamond skeleton parameters` (frame SKELETON) — not read by anything

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


### `GripV gyroid skeleton parameters` (frame SKELETON) — not read by anything

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


### `GripV primitive skeleton parameters` (frame SKELETON) — not read by anything

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


### `GripV voronoi skeleton parameters` (frame SKELETON) — not read by anything

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

