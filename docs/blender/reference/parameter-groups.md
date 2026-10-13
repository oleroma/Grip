# Parameter groups (constructors)

The 54 constructor groups: generic groups whose inputs are the part parameters and which pack them into a bundle. Presets (`GripV abxy`, …) place them and type the values; see [2. Parameter system](../02-parameter-system.md). Generated from the file [wiring].

For each group: the inputs with their type, the **interface default** (what a newly added node gets, not the value used by the presets; those are in the preset tables for [GripV](preset-values-GripV.md) and [GripX](preset-values-GripX.md)), the range when one is set, and the bundle key the input is packed under. A key that differs from the input name is in **bold**; a key filled by a node inside the group instead of an input is shown with that node. "Unpacked by" lists the `… outputs` groups that read a key of that name.

## Index

- [`abxy advanced parameters`](#abxy-advanced-parameters): 3 inputs, placed in 2 preset node(s)
- [`advanced button parameters`](#advanced-button-parameters): 5 inputs, placed in 8 preset node(s)
- [`advanced caps parameters`](#advanced-caps-parameters): 10 inputs, placed in 4 preset node(s)
- [`advanced cover parameters`](#advanced-cover-parameters): 18 inputs, placed in 7 preset node(s)
- [`advanced R1L1 parameters`](#advanced-r1l1-parameters): 11 inputs, placed in 1 preset node(s)
- [`advanced R4R2 parameters`](#advanced-r4r2-parameters): 1 inputs, placed in 1 preset node(s)
- [`advanced stick parameters`](#advanced-stick-parameters): 12 inputs, placed in 16 preset node(s)
- [`advanced stick parameters.001`](#advanced-stick-parameters001): 13 inputs, placed in 18 preset node(s)
- [`advanced trigger parameters`](#advanced-trigger-parameters): 11 inputs, placed in 2 preset node(s)
- [`base usb width`](#base-usb-width): 2 inputs, placed in 0 preset node(s)
- [`basic cover parameters`](#basic-cover-parameters): 2 inputs, placed in 6 preset node(s)
- [`basic R1L1 parameters`](#basic-r1l1-parameters): 8 inputs, placed in 1 preset node(s)
- [`basic R4R2 parameters`](#basic-r4r2-parameters): 5 inputs, placed in 1 preset node(s)
- [`basic stick parameters`](#basic-stick-parameters): 14 inputs, placed in 16 preset node(s)
- [`basic stick parameters.001`](#basic-stick-parameters001): 33 inputs, placed in 18 preset node(s)
- [`button parameters`](#button-parameters): 12 inputs, placed in 16 preset node(s)
- [`cable size`](#cable-size): 4 inputs, placed in 0 preset node(s)
- [`capacitive plate advanced parameters`](#capacitive-plate-advanced-parameters): 2 inputs, placed in 2 preset node(s)
- [`capacitive plate parameters`](#capacitive-plate-parameters): 5 inputs, placed in 4 preset node(s)
- [`caps parameters`](#caps-parameters): 19 inputs, placed in 12 preset node(s)
- [`combine`](#combine): 18 inputs, placed in 0 preset node(s)
- [`cubic fill array parameters`](#cubic-fill-array-parameters): 3 inputs, placed in 12 preset node(s)
- [`curve parameters`](#curve-parameters): 5 inputs, placed in 10 preset node(s)
- [`dpad advanced parameters`](#dpad-advanced-parameters): 6 inputs, placed in 2 preset node(s)
- [`dpad stick parameters`](#dpad-stick-parameters): 36 inputs, placed in 3 preset node(s)
- [`fill parameters`](#fill-parameters): 21 inputs, placed in 2 preset node(s)
- [`fill parameters.001`](#fill-parameters001): 29 inputs, placed in 62 preset node(s)
- [`grid texture parameters`](#grid-texture-parameters): 8 inputs, placed in 16 preset node(s)
- [`holllow lattice parameters`](#holllow-lattice-parameters): 5 inputs, placed in 1 preset node(s)
- [`hollow  parameters`](#hollow--parameters): 5 inputs, placed in 3 preset node(s)
- [`home advanced parameters`](#home-advanced-parameters): 5 inputs, placed in 2 preset node(s)
- [`icosahedron texture parameters`](#icosahedron-texture-parameters): 4 inputs, placed in 16 preset node(s)
- [`L1 parameters`](#l1-parameters): 3 inputs, placed in 1 preset node(s)
- [`marks inputs`](#marks-inputs): 15 inputs, placed in 0 preset node(s)
- [`marks parameters`](#marks-parameters): 19 inputs, placed in 14 preset node(s)
- [`middle plate parameters`](#middle-plate-parameters): 16 inputs, placed in 6 preset node(s)
- [`pcb cutout parameters`](#pcb-cutout-parameters): 4 inputs, placed in 4 preset node(s)
- [`pins params`](#pins-params): 5 inputs, placed in 3 preset node(s)
- [`pins postion`](#pins-postion): 3 inputs, placed in 3 preset node(s)
- [`R1 lever paramteters`](#r1-lever-paramteters): 19 inputs, placed in 0 preset node(s)
- [`R1 lever postion`](#r1-lever-postion): 3 inputs, placed in 0 preset node(s)
- [`R1 parameters`](#r1-parameters): 3 inputs, placed in 1 preset node(s)
- [`R1L1 lever parameters`](#r1l1-lever-parameters): 27 inputs, placed in 3 preset node(s)
- [`screw parameters`](#screw-parameters): 14 inputs, placed in 0 preset node(s)
- [`screw parameters.002`](#screw-parameters002): 15 inputs, placed in 0 preset node(s)
- [`screw position`](#screw-position): 2 inputs, placed in 0 preset node(s)
- [`screw positions`](#screw-positions): 12 inputs, placed in 1 preset node(s)
- [`scroll parameters`](#scroll-parameters): 4 inputs, placed in 3 preset node(s)
- [`shield parameters`](#shield-parameters): 6 inputs, placed in 16 preset node(s)
- [`spiral trigger params`](#spiral-trigger-params): 6 inputs, placed in 0 preset node(s)
- [`stick top parameters`](#stick-top-parameters): 7 inputs, placed in 16 preset node(s)
- [`top face parameters`](#top-face-parameters): 6 inputs, placed in 4 preset node(s)
- [`trigger parameters`](#trigger-parameters): 22 inputs, placed in 10 preset node(s)
- [`voronoi parameters`](#voronoi-parameters): 1 inputs, placed in 9 preset node(s)

## abxy advanced parameters

Placed in presets: `GripR1 abxy`, `GripR1 abxy_OLD`. Placed in any group: 2 group(s).

| Input | Type | Default | Range | Bundle key | Unpacked by |
|---|---|---|---|---|---|
| abxy subdivisions | int | 16 |  … 128 | abxy subdivisions | `ABXY button outputs` |
| abxy base radius | float | 6 |  | abxy base radius | `ABXY button outputs` |
| fillet tolerance | float | 0.6 |  | fillet tolerance | `ABXY button outputs`, `base curve outputs` |

## advanced button parameters

Placed in presets: `GripR1 abxy`, `GripR1 abxy_OLD`, `GripR1 dpad`, `GripR1 dpad_OLD`, `GripR1 home`, `GripR1 home_OLD`, `GripR1 select`, `GripR1 select_OLD`. Placed in any group: 8 group(s).

| Input | Type | Default | Range | Bundle key | Unpacked by |
|---|---|---|---|---|---|
| stopper position | float | 9 | 4 … 12 | stopper position | `R1L1 outputs`, `button outputs` |
| stopper offset | float | 1 | 1 … 3 | stopper offset | `button outputs` |
| case bool bevel | float | 1 |  | case bool bevel | `button outputs` |
| case middle bevel | float | 0.4 |  | case middle bevel | `button outputs` |
| stopper height | float | 2 |  | stopper height | `R1L1 outputs`, `button outputs` |

## advanced caps parameters

Placed in presets: `GripR1 abxy`, `GripR1 dpad`, `GripR1 home`, `GripR1 select`. Placed in any group: 5 group(s).

| Input | Type | Default | Range | Bundle key | Unpacked by |
|---|---|---|---|---|---|
| button cap | bool | off |  | button cap | `caps outputs` |
| custom cap | bool | off |  | custom cap | `caps outputs` |
| caps base offset | float | 1.6 |  | **caps offset** | `caps outputs` |
| button cap travel distance | float | 1.6 |  | button cap travel distance | `caps outputs` |
| caps additional size | float | 0 |  | caps additional size | `caps outputs` |
| cap base fillet | float | 2.85 |  | cap base fillet | `caps outputs` |
| cap base fillet subd | int | 16 |  | cap base fillet subd | `caps outputs` |
| caps depth | float | 2 |  | caps depth | `caps outputs` |
| caps hook inset | float | 0.3 |  | caps hook inset | `caps outputs` |
| caps hook height | float | 1.12 |  | caps hook height | `caps outputs` |

## advanced cover parameters

Placed in presets: `GripR1 cover parameters`, `GripR1 cover parameters_OLD`, `GripV cover parameters`, `GripX cover parameters`. Placed in any group: 4 group(s).

| Input | Type | Default | Range | Bundle key | Unpacked by |
|---|---|---|---|---|---|
| lip height | float | 1.6 |  | lip height | `cover outputs` |
| battery length | float | 65 |  | battery length | `cover outputs` |
| battery width | float | 34 |  | battery width | `cover outputs` |
| battery height | float | 5.4 |  | battery height | `cover outputs` |
| flex width | float | 1 |  | flex width | `cover outputs` |
| lip width | float | 1.2 |  | lip width | `cover outputs` |
| lip hook height | float | 2 |  | lip hook height | `cover outputs` |
| shift Y | float | 0 |  | shift Y | `cover outputs` |
| cover base thickness | float | 1 |  | cover base thickness | `cover outputs` |
| cover base overlap | float | 6 |  | cover base overlap | `cover outputs` |
| appendix | bool | off |  | appendix | `cover outputs` |
| appendix height | float | 0.95 |  | appendix height | `cover outputs` |
| appendix length | float | 31.6 |  | appendix length | `cover outputs` |
| appendix gap | float | 2.7 |  | appendix gap | `cover outputs` |
| compression offset | float | 0.1 |  | compression offset | `cover outputs` |
| battery wire cut | float | 6 |  | battery wire cut | `cover outputs` |
| test parameter | float | 0 |  | test parameter | `cover outputs` |
| curved cover | bool | off |  | curved cover | `cover outputs` |

## advanced R1L1 parameters

Placed in presets: `GripR1 R1L1 parameters`. Placed in any group: 3 group(s).

| Input | Type | Default | Range | Bundle key | Unpacked by |
|---|---|---|---|---|---|
| wdith | float | 9 |  | wdith | `R1L1 outputs`, `lever R1L1 outputs` |
| height | float | 8 |  | height | `R1L1 outputs`, `lever R1L1 outputs` |
| side offset | float | -1 |  | side offset | `R1L1 outputs` |
| stopper position | float | 7 |  | stopper position | `R1L1 outputs`, `button outputs` |
| stopper height | float | 2 |  | stopper height | `R1L1 outputs`, `button outputs` |
| stopper thickness | float | 1.4 |  | stopper thickness | `R1L1 outputs` |
| height offset | float | 0 |  | height offset | `R1L1 outputs` |
| top lip | float | 6.2 |  | top lip | `R1L1 outputs` |
| bottom lip | float | -6.2 |  | bottom lip | `R1L1 outputs` |
| first offset | float | 13 |  | **main Y offset** | `R1L1 outputs` |
| flex | bool | on |  | flex | `R1L1 outputs` |

## advanced R4R2 parameters

Placed in presets: `GripR1 R4R2 parameters`. Placed in any group: 1 group(s).

| Input | Type | Default | Range | Bundle key | Unpacked by |
|---|---|---|---|---|---|
| subdivision length | float | 1 |  | subdivision length | `trigger outputs` |

## advanced stick parameters

Placed in presets: `GripR1 stick L parameters`, `GripR1 stick R parameters`, `GripV stick L parameters`, `GripV stick R parameters`, `GripX stick L parameters`, `GripX stick R parameters`. Placed in any group: 6 group(s).

| Input | Type | Default | Range | Bundle key | Unpacked by |
|---|---|---|---|---|---|
| contact angle | float | 45 |  | contact angle | `stick outputs` |
| hole bevel | float | 2 |  | hole bevel | `stick outputs` |
| hole radius | float | 6 | 5 … 9 | hole radius | `stick outputs` |
| stick subdivision | int | 128 |  | stick subdivision | `stick outputs` |
| stick hole subdivision | int | 8 |  | stick hole subdivision | `stick outputs` |
| stick  XY correction | bool | off |  | **stick XY correction** | `stick outputs` |
| X correction | float | 0 |  | X correction | `stick outputs` |
| Y correction | float | 0 |  | Y correction | `stick outputs` |
| shaft X correction | float | 0 |  | shaft X correction | `stick outputs` |
| shaft Y correction | float | 0 |  | shaft Y correction | `stick outputs` |
| case cutout thickness  | float | 2.5 |  | **case cutout thickness** | `stick outputs` |
| swap stick rotation | bool | off |  | swap stick rotation | `stick outputs` |

## advanced stick parameters.001

Placed in presets: `GripR1 stick L parameters`, `GripR1 stick L parameters_OLD`, `GripR1 stick R parameters`. Placed in any group: 4 group(s).

| Input | Type | Default | Range | Bundle key | Unpacked by |
|---|---|---|---|---|---|
| contact angle | float | 45 |  | contact angle | `stick outputs` |
| hole bevel | float | 2 |  | hole bevel | `stick outputs` |
| hole radius | float | 6 | 5 … 9 | hole radius | `stick outputs` |
| stick subdivision | int | 128 |  | stick subdivision | `stick outputs` |
| stick hole subdivision | int | 8 |  | stick hole subdivision | `stick outputs` |
| stick  XY correction | bool | off |  | **stick XY correction** | `stick outputs` |
| X correction | float | 0 |  | X correction | `stick outputs` |
| Y correction | float | 0 |  | Y correction | `stick outputs` |
| shaft X correction | float | 0 |  | shaft X correction | `stick outputs` |
| shaft Y correction | float | 0 |  | shaft Y correction | `stick outputs` |
| case cutout thickness  | float | 2.5 |  | **case cutout thickness** | `stick outputs` |
| swap stick rotation | bool | off |  | swap stick rotation | `stick outputs` |
| swap top rotation | bool | off |  | swap top rotation | `stick outputs` |

## advanced trigger parameters

Placed in presets: `GripR1 R2 parameters`, `GripR1 R4 parameters`. Placed in any group: 3 group(s).

| Input | Type | Default | Range | Bundle key | Unpacked by |
|---|---|---|---|---|---|
| trigger radius | float | 80 |  | trigger radius | `trigger outputs` |
| stopper length | float | 29 |  | stopper length | `trigger outputs` |
| button rotation | float | 23.7 |  | button rotation | `trigger outputs` |
| shift z | float | 37 |  | shift z | `trigger outputs` |
| button radius offset | float | 2 |  | button radius offset | `trigger outputs` |
| height | float | 9 |  | height | `R1L1 outputs`, `lever R1L1 outputs` |
| width | float | 11 |  | width | `trigger outputs` |
| stopper height | float | 2 |  | stopper height | `R1L1 outputs`, `button outputs` |
| subdivision length | float | 1 |  | subdivision length | `trigger outputs` |
| button pressed height | float | 1.65 |  | button pressed height | `trigger outputs` |
| x offset | float | 0 |  | x offset | `trigger outputs` |

## base usb width

Placed in presets: none. Placed in any group: 1 group(s).

| Input | Type | Default | Range | Bundle key | Unpacked by |
|---|---|---|---|---|---|
| width | float | 13.5 |  | width | `trigger outputs` |
| height | float | 7.562 |  | height | `R1L1 outputs`, `lever R1L1 outputs` |

## basic cover parameters

Placed in presets: `GripR1 cover parameters`, `GripR1 cover parameters_OLD`, `GripV cover parameters`, `GripX cover parameters`. Placed in any group: 4 group(s).

| Input | Type | Default | Range | Bundle key | Unpacked by |
|---|---|---|---|---|---|
| y tolerance | float | 0.1 |  | y tolerance | `cover outputs` |
| x tolerance | float | 0.1 |  | x tolerance | `cover outputs` |

## basic R1L1 parameters

Placed in presets: `GripR1 R1L1 parameters`. Placed in any group: 3 group(s).

| Input | Type | Default | Range | Bundle key | Unpacked by |
|---|---|---|---|---|---|
| button height | float | 2.1 |  | button height | `R1L1 outputs`, `button outputs` |
| top bevel | float | 1.2 |  | top bevel | `R1L1 outputs`, `button outputs`, `stick outputs` |
| Z tolerance | float | 0.3 |  | Z tolerance | `R1L1 outputs`, `middle plate outputs` |
| X tolerance | float | 0.8 |  | X tolerance | `R1L1 outputs`, `lever R1L1 outputs` |
| bevel inner | float | 4 |  | bevel inner | `R1L1 outputs`, `lever R1L1 outputs` |
| bevel inner sbdiv | int | 2 |  | bevel inner sbdiv | `R1L1 outputs`, `lever R1L1 outputs` |
| button press tolerance | float | 0.5 |  | button press tolerance | `R1L1 outputs`, `trigger outputs` |
| jump fix shear | float | 0 |  | jump fix shear | `R1L1 outputs` |

## basic R4R2 parameters

Placed in presets: `GripR1 R4R2 parameters`. Placed in any group: 1 group(s).

| Input | Type | Default | Range | Bundle key | Unpacked by |
|---|---|---|---|---|---|
| top bevel | float | 1.2 |  | top bevel | `R1L1 outputs`, `button outputs`, `stick outputs` |
| x tolerance | float | 0.2 |  | x tolerance | `cover outputs` |
| radius tolerance | float | 0.2 |  | radius tolerance | `trigger outputs` |
| bevel | float | 4.2 |  | bevel | `trigger outputs` |
| bevel subd | int | 2 |  | bevel subd | `trigger outputs` |

## basic stick parameters

Placed in presets: `GripR1 stick L parameters`, `GripR1 stick R parameters`, `GripV stick L parameters`, `GripV stick R parameters`, `GripX stick L parameters`, `GripX stick R parameters`. Placed in any group: 6 group(s).

| Input | Type | Default | Range | Bundle key | Unpacked by |
|---|---|---|---|---|---|
| stick top radius | float | 5 |  | stick top radius | `stick outputs` |
| stick heght | float | 5 | 0 … 15 | stick heght | `stick outputs` |
| range degrees | float | 16.1 | 5 … 20 | range degrees | `stick outputs` |
| contact top offset | float | 1 |  | contact top offset | `stick outputs` |
| contact bottom offset | float | 1.4 |  | contact bottom offset | `stick outputs` |
| topmost offset | float | 2 |  | topmost offset | `stick outputs` |
| base size | float | 2.9 |  | base size | `stick outputs` |
| base height | float | 8 |  | base height | `stick outputs` |
| action | bool | off |  | action; via nodes: **action rotation** | `dpad stick outputs`, `stick outputs`, `trigger outputs` |
| action rotation | float | 0 |  | via nodes: action rotation | `stick outputs` |
| top bevel | float | 0.4 |  | top bevel | `R1L1 outputs`, `button outputs`, `stick outputs` |
| middle bevel | float | 1.2 |  | middle bevel | `button outputs`, `stick outputs` |
| shaft tolerance | float | 0.2 |  | shaft tolerance | `stick outputs` |
| shaft Z offset | float | 0 |  | shaft Z offset | `stick outputs` |

Keys not filled from an input: **action rotation** ← Switch.

## basic stick parameters.001

Placed in presets: `GripR1 stick L parameters`, `GripR1 stick L parameters_OLD`, `GripR1 stick R parameters`. Placed in any group: 4 group(s).

| Input | Type | Default | Range | Bundle key | Unpacked by |
|---|---|---|---|---|---|
| stick top radius | float | 5 |  | stick top radius | `stick outputs` |
| stick heght | float | 5 | 0 … 15 | stick heght | `stick outputs` |
| range degrees | float | 16.1 | 5 … 20 | range degrees | `stick outputs` |
| contact top offset | float | 1 |  | contact top offset | `stick outputs` |
| contact bottom offset | float | 1.4 |  | contact bottom offset | `stick outputs` |
| topmost offset | float | 2 |  | topmost offset | `stick outputs` |
| square texture subdivision | int | 2 |  | square texture subdivision |  |
| square texture sharpness | float | 0.3 |  | square texture sharpness | `stick outputs` |
| square texture height | float | 0.5 |  | square texture height | `stick outputs` |
| convex texture height | float | 0.4 | -1 … 2 | **circle texture height** |  |
| convex texture sharpness | float | 0.4 | 0 … 1 | **circle texture sharpness** |  |
| convex texture subdivision | int | 4 |  | **circle texture subdivision** |  |
| convex texture flatness | int | 3 | 1 … 7 | **circle texture flatness** |  |
| convex texture size offset | float | 0 |  | **circle texture size offset** |  |
| sheild | bool | off |  | sheild | `stick outputs` |
| sheild height | float | -1.8 |  | sheild height | `stick outputs` |
| shield cutoff height | float | 10.6 |  | shield cutoff height | `stick outputs` |
| sheild radius | float | 12.4 |  | sheild radius | `stick outputs` |
| FDM shield thickness | float | 0 |  | FDM shield thickness | `stick outputs` |
| FDM Z correction | float | 0 |  | FDM Z correction | `stick outputs` |
| base size | float | 2.9 |  | base size | `stick outputs` |
| action | bool | off |  | action | `dpad stick outputs`, `stick outputs`, `trigger outputs` |
| base height | float | 8 |  | base height | `stick outputs` |
| Menu | menu | concave top |  | via nodes: **top index** |  |
| top bevel | float | 0.4 |  | top bevel | `R1L1 outputs`, `button outputs`, `stick outputs` |
| middle bevel | float | 1.2 |  | middle bevel | `button outputs`, `stick outputs` |
| morph square texture | bool | off |  | morph square texture |  |
| shaft tolerance | float | 0.045 |  | shaft tolerance | `stick outputs` |
| shaft Z offset | float | 0 |  | shaft Z offset | `stick outputs` |
| concave radius | float | 9 |  | concave radius |  |
| concave texture height | float | -0.2 |  | concave texture height |  |
| concave texture subdivisions | int | 3 |  | concave texture subdivisions |  |
| concave texture sharpness | float | 0.4 |  | concave texture sharpness |  |

Keys not filled from an input: **top index** ← Menu Switch.

## button parameters

Placed in presets: `GripR1 abxy`, `GripR1 abxy_OLD`, `GripR1 dpad`, `GripR1 dpad_OLD`, `GripR1 home`, `GripR1 home_OLD`, `GripR1 select`, `GripR1 select_OLD` +8. Placed in any group: 16 group(s).

| Input | Type | Default | Range | Bundle key | Unpacked by |
|---|---|---|---|---|---|
| button tolerance | float | 0.35 | 0.1 … 0.8 | button tolerance | `button outputs` |
| SMD height | float | 4.9 |  | SMD height | `button outputs` |
| button height | float | 3 | 1 … 5 | button height | `R1L1 outputs`, `button outputs` |
| button height offset | float | -0.5 | -5 … 5 | button height offset | `button outputs` |
| top bevel | float | 0.8 |  | top bevel | `R1L1 outputs`, `button outputs`, `stick outputs` |
| case middle bevel | float | 0.4 |  | **middle bevel** | `button outputs`, `stick outputs` |
| bottom bevel | float | 3 |  | bottom bevel | `button outputs` |
| middle bevel | float | 0.4 |  | **case middle bevel** | `button outputs` |
| stopper position | float | 9 |  | stopper position | `R1L1 outputs`, `button outputs` |
| stopper height | float | 2 |  | stopper height | `R1L1 outputs`, `button outputs` |
| stopper offset | float | 1 |  | stopper offset | `button outputs` |
| case bool bevel | float | 1 |  | case bool bevel | `button outputs` |

## cable size

Placed in presets: none. Placed in any group: 1 group(s).

| Input | Type | Default | Range | Bundle key | Unpacked by |
|---|---|---|---|---|---|
| Z tolerance | float | 0 |  | Z tolerance | `R1L1 outputs`, `middle plate outputs` |
| width | float | 13.5 |  | width | `trigger outputs` |
| height | float | 7.562 |  | height | `R1L1 outputs`, `lever R1L1 outputs` |
| apply to clip | bool | off |  | apply to clip |  |

## capacitive plate advanced parameters

Placed in presets: `GripR1 abxy`, `GripR1 abxy_OLD`. Placed in any group: 2 group(s).

| Input | Type | Default | Range | Bundle key | Unpacked by |
|---|---|---|---|---|---|
| capacitive plate | bool | off |  | capacitive plate |  |
| plate button offset | float | 0.8 | 0 … 4 | plate button offset | `cap plate outputs` |

## capacitive plate parameters

Placed in presets: `GripR1 abxy`, `GripR1 abxy_OLD`, `GripV abxy`, `GripX abxy`. Placed in any group: 4 group(s).

| Input | Type | Default | Range | Bundle key | Unpacked by |
|---|---|---|---|---|---|
| capacitive | menu | plate |  | via nodes: capacitive, **knob** | `cap plate outputs` |
| screw hole | bool | off |  | screw hole | `cap plate outputs` |
| capacitive plate tolerance | float | 0.4 |  | capacitive plate tolerance | `cap plate outputs` |
| capacitive plate stem tolerance | float | -0.1 |  | capacitive plate stem tolerance | `cap plate outputs` |
| plate button offset | float | 1 |  | plate button offset | `cap plate outputs` |

Keys not filled from an input: **capacitive** ← Menu Switch; **knob** ← Menu Switch.

## caps parameters

Placed in presets: `GripR1 abxy`, `GripR1 dpad`, `GripR1 home`, `GripR1 select`, `GripV abxy`, `GripV dpad`, `GripV home`, `GripV select` +4. Placed in any group: 13 group(s).

| Input | Type | Default | Range | Bundle key | Unpacked by |
|---|---|---|---|---|---|
| caps fit tolerance | float | -0.2 |  | **caps fit XY tolerance** | `caps outputs` |
| caps fit Z tolerance | float | 0.3 |  | **caps fit Z olerance** | `caps outputs` |
| caps fit Z | float | 1 |  | caps fit Z | `caps outputs` |
| cap case tolerance | float | 0.6 |  | cap case tolerance | `caps outputs` |
| cap bevel | float | 2 |  | cap bevel | `caps outputs` |
| cap bevel subd | int | 16 |  | cap bevel subd | `caps outputs` |
| cap bevel cutoff | bool | on |  | cap bevel cutoff; via nodes: **bevel cutoff** | `caps outputs` |
| bevel cutoff | float | 0.7854 |  | via nodes: bevel cutoff | `caps outputs` |
| caps flex cut | float | 0.6 |  | caps flex cut | `caps outputs` |
| button cap | bool | on |  | button cap | `caps outputs` |
| caps offset | float | 1.48 |  | caps offset | `caps outputs` |
| button cap travel distance | float | 1.92 |  | button cap travel distance | `caps outputs` |
| caps additional size | float | 0 |  | caps additional size | `caps outputs` |
| cap base fillet | float | 2.85 |  | cap base fillet | `caps outputs` |
| cap base fillet subd | int | 16 |  | cap base fillet subd | `caps outputs` |
| custom cap | bool | off |  | custom cap | `caps outputs` |
| caps hook inset | float | 0.3 |  | caps hook inset | `caps outputs` |
| caps hook height | float | 1.12 |  | caps hook height | `caps outputs` |
| caps depth | float | 2.08 |  | caps depth | `caps outputs` |

Keys not filled from an input: **bevel cutoff** ← Switch.

## combine

Placed in presets: none. Placed in any group: 1 group(s).

| Input | Type | Default | Range | Bundle key | Unpacked by |
|---|---|---|---|---|---|
| stick R | bundle |  |  | stick R |  |
| stick L | bundle |  |  | stick L |  |
| R2R4 | bundle |  |  | R2R4 |  |
| R2 | bundle |  |  | R2 |  |
| R4 | bundle |  |  | R4 |  |
| R1L1 | bundle |  |  | R1L1 |  |
| R1 | bundle |  |  | R1 |  |
| L1 | bundle |  |  | L1 |  |
| pcb | bundle |  |  | pcb |  |
| cover | bundle |  |  | cover |  |
| screw | bundle |  |  | screw |  |
| screw positions | bundle |  |  | screw positions |  |
| scrollwheel | bundle |  |  | scrollwheel |  |
| lever R1L1 | bundle |  |  | lever R1L1 |  |
| abxy | bundle |  |  | abxy |  |
| dpad | bundle |  |  | dpad |  |
| select | bundle |  |  | select |  |
| home | bundle |  |  | home |  |

## cubic fill array parameters

Placed in presets: `GripR1 cubic hollow array parameters`, `GripV cubic hollow array parameters`, `GripX cubic hollow array parameters`. Placed in any group: 3 group(s).

| Input | Type | Default | Range | Bundle key | Unpacked by |
|---|---|---|---|---|---|
| translate | vector | (0, 12, 0) |  | translate | `fill outputs.001`, `indent outputs`, `lattice outputs`, `logo outputs`, `marks outputs` |
| rotate | vector | (0, -0.262, -1.047) |  | rotate | `fill outputs.001`, `indent outputs`, `lattice outputs`, `logo outputs`, `marks outputs` |
| interval | float | 10 |  | **scale** | `fill outputs.001`, `indent outputs`, `lattice outputs` |

## curve parameters

Placed in presets: `GripR1 select`, `GripR1 select_OLD`, `GripV abxy`, `GripV dpad`, `GripV home`, `GripV select`, `GripX abxy`, `GripX dpad` +2. Placed in any group: 10 group(s).

| Input | Type | Default | Range | Bundle key | Unpacked by |
|---|---|---|---|---|---|
| width | float | 9.8 |  | **base width** | `base curve outputs` |
| octagonal fillet | bool | on |  | **even fillet** | `base curve outputs` |
| fillet | float | 2 | 0 … 20 | **base fillet** | `base curve outputs` |
| fillet subdiv | int | 16 |  | fillet subdiv | `base curve outputs`, `dpad button outputs` |
| fillet tolerance | float | 0.4 |  | fillet tolerance | `ABXY button outputs`, `base curve outputs` |

## dpad advanced parameters

Placed in presets: `GripR1 dpad`, `GripR1 dpad_OLD`. Placed in any group: 2 group(s).

| Input | Type | Default | Range | Bundle key | Unpacked by |
|---|---|---|---|---|---|
| dpad base button length | float | 10 |  | dpad base button length | `dpad button outputs` |
| dpad base button width | float | 10 |  | dpad base button width | `dpad button outputs` |
| base curve fillet | float | 2 | 1 … 4 | base curve fillet | `dpad button outputs` |
| fillet subdiv | int | 16 |  | fillet subdiv | `base curve outputs`, `dpad button outputs` |
| fillet tolerance | float | 0.4 |  | **additional fillet** | `dpad button outputs` |
| dpad shift | float | 0.7 |  | dpad shift | `dpad button outputs` |

## dpad stick parameters

Placed in presets: `GripR1 dpad stick`, `GripV dpad stick`, `GripX dpad stick`. Placed in any group: 3 group(s).

| Input | Type | Default | Range | Bundle key | Unpacked by |
|---|---|---|---|---|---|
| dpad stick | bool | off |  | dpad stick | `dpad stick outputs` |
| rocker size | float | 13 |  | rocker size | `dpad stick outputs` |
| rocker base thickness | float | 0.6 |  | rocker base thickness | `dpad stick outputs` |
| stiick height | float | 17.9 |  | stiick height | `dpad stick outputs` |
| ball radius | float | 6.9 |  | ball radius | `dpad stick outputs` |
| rocker support size | float | 14.4 |  | rocker support size | `dpad stick outputs` |
| button center offset | float | 9 |  | button center offset | `dpad stick outputs` |
| action | bool | off |  | action | `dpad stick outputs`, `stick outputs`, `trigger outputs` |
| texture height | float | 0.8 |  | texture height | `dpad stick outputs`, `stick outputs` |
| texture sharpness | float | 0.5 |  | texture sharpness | `dpad stick outputs`, `stick outputs` |
| cap height offset | float | 15.8 |  | cap height offset | `dpad stick outputs` |
| cap radius | float | 7 |  | cap radius | `dpad stick outputs` |
| cap subdivisions | int | 2 | 2 …  | cap subdivisions | `dpad stick outputs` |
| cutout | float | 5.8 |  | cutout | `dpad stick outputs` |
| chamber height | float | 14.7 |  | chamber height | `dpad stick outputs` |
| chamber size | float | 14.15 |  | chamber size | `dpad stick outputs` |
| ball support height | float | 5.5 |  | ball support height | `dpad stick outputs` |
| button travel | float | 1.3 |  | button travel | `dpad stick outputs` |
| rocker support height | float | 4.8 |  | rocker support height | `dpad stick outputs` |
| ball support radius | float | 2.2 |  | ball support radius | `dpad stick outputs` |
| ball support compression tolerance | float | -0.4 |  | ball support compression tolerance | `dpad stick outputs` |
| rocker support thickness | float | 5.8 |  | rocker support thickness | `dpad stick outputs` |
| stick bottom offset | float | 1.4 |  | stick bottom offset | `dpad stick outputs` |
| ball stopper height | float | 1.4 |  | ball stopper height | `dpad stick outputs` |
| stick thickness | float | 2.2 |  | stick thickness | `dpad stick outputs` |
| stick tolerance | float | 0.1 |  | stick tolerance | `dpad stick outputs` |
| stick hook depth | float | 1.12 |  | stick hook depth | `dpad stick outputs` |
| stick hook height | float | 2.72 |  | stick hook height | `dpad stick outputs` |
| hook z tolerance | float | 0.16 |  | hook z tolerance | `dpad stick outputs` |
| inner hook tolerance | float | 0.6 |  | inner hook tolerance | `dpad stick outputs` |
| hook extrude | float | 1.6 |  | hook extrude | `dpad stick outputs` |
| flex cut width | float | 0.4 |  | flex cut width | `dpad stick outputs` |
| flex cut depth | float | 1 |  | flex cut depth | `dpad stick outputs` |
| ball stopper position | float | 4 |  | ball stopper position | `dpad stick outputs` |
| cap fit tolerance | float | 0 |  | **stick fit tolerance** | `dpad stick outputs` |
| cap oval offset | float | 0.78 |  | cap oval offset | `dpad stick outputs` |

## fill parameters

Placed in presets: `GripV  lattice parameters`, `GripV cubic hollow parameters`. Placed in any group: 2 group(s).

| Input | Type | Default | Range | Bundle key | Unpacked by |
|---|---|---|---|---|---|
| voxel size | float | 1 |  | voxel size | `fill outputs.001`, `indent outputs`, `lattice outputs` |
| band width | int | 5 |  | band width | `fill outputs.001`, `indent outputs`, `lattice outputs` |
| scale | float | 0.4 |  | scale | `fill outputs.001`, `indent outputs`, `lattice outputs` |
| thickness | float | 1 |  | thickness | `fill outputs.001`, `indent outputs`, `lattice outputs` |
| fill depth | float | 0 |  | fill depth | `fill outputs.001`, `indent outputs`, `lattice outputs` |
| fill depth smooth | float | 0 |  | fill depth smooth | `fill outputs.001`, `indent outputs`, `lattice outputs` |
| boundary smooth | float | 0 |  | boundary smooth | `fill outputs.001`, `indent outputs`, `lattice outputs` |
| boundary offset | float | 0.2 |  | boundary offset | `fill outputs.001`, `indent outputs`, `lattice outputs` |
| limit geometry smooth | float | 0 |  | limit geometry smooth | `fill outputs.001`, `indent outputs`, `lattice outputs` |
| droop height | float | 4 |  | droop height | `fill outputs.001`, `indent outputs`, `lattice outputs` |
| droop depth | float | -3 |  | droop depth | `fill outputs.001`, `indent outputs`, `lattice outputs` |
| droop multiplier | float | 1 |  | droop multiplier | `fill outputs.001`, `indent outputs`, `lattice outputs` |
| rotate | vector | (0, 0, 0) |  | rotate | `fill outputs.001`, `indent outputs`, `lattice outputs`, `logo outputs`, `marks outputs` |
| translate | vector | (0, 0, 0) |  | translate | `fill outputs.001`, `indent outputs`, `lattice outputs`, `logo outputs`, `marks outputs` |
| scale axis | vector | (1, 1, 1) |  | scale axis | `fill outputs.001`, `indent outputs`, `lattice outputs` |
| insert rim depth | float | 1 |  | insert rim depth | `fill outputs.001`, `indent outputs`, `lattice outputs` |
| insert rim height | float | 2 |  | insert rim height | `fill outputs.001`, `indent outputs`, `lattice outputs` |
| insert rim smooth | float | 5 |  | insert rim smooth | `fill outputs.001`, `indent outputs`, `lattice outputs` |
| smooth pattern | float | 6 |  | smooth pattern | `fill outputs.001`, `indent outputs`, `lattice outputs` |
| protect sharp | float | 3 |  | protect sharp | `fill outputs.001`, `indent outputs`, `lattice outputs` |
| smooth sharp | float | 5 |  | smooth sharp | `fill outputs.001`, `indent outputs`, `lattice outputs` |

## fill parameters.001

Placed in presets: `GripR1 FischerKoch CY hollow parameters`, `GripR1 FischerKoch CY indent parameters`, `GripR1 FischerKoch CY skeleton parameters`, `GripR1 FischerKoch S hollow parameters`, `GripR1 FischerKoch S indent parameters`, `GripR1 FischerKoch S skeleton parameters`, `GripR1 cubic hollow parameters`, `GripR1 cubic indent parameters` +54. Placed in any group: 63 group(s).

| Input | Type | Default | Range | Bundle key | Unpacked by |
|---|---|---|---|---|---|
| voxel size | float | 1 |  | voxel size | `fill outputs.001`, `indent outputs`, `lattice outputs` |
| band width | int | 20 |  | band width | `fill outputs.001`, `indent outputs`, `lattice outputs` |
| scale | float | 0.4 |  | scale | `fill outputs.001`, `indent outputs`, `lattice outputs` |
| thickness | float | 1 |  | thickness | `fill outputs.001`, `indent outputs`, `lattice outputs` |
| smooth meshed voxels | int | 0 |  | smooth meshed voxels | `fill outputs.001` |
| fill depth | float | 1.2 |  | fill depth | `fill outputs.001`, `indent outputs`, `lattice outputs` |
| fill depth smooth | float | 3 |  | fill depth smooth | `fill outputs.001`, `indent outputs`, `lattice outputs` |
| boundary smooth | float | 0 |  | boundary smooth | `fill outputs.001`, `indent outputs`, `lattice outputs` |
| boundary offset | float | 0.2 |  | boundary offset | `fill outputs.001`, `indent outputs`, `lattice outputs` |
| limit geometry smooth | float | 6 |  | limit geometry smooth | `fill outputs.001`, `indent outputs`, `lattice outputs` |
| droop height | float | 4 |  | droop height | `fill outputs.001`, `indent outputs`, `lattice outputs` |
| droop depth | float | -3 |  | droop depth | `fill outputs.001`, `indent outputs`, `lattice outputs` |
| droop multiplier | float | 1 |  | droop multiplier | `fill outputs.001`, `indent outputs`, `lattice outputs` |
| rotate | vector | (0, 0, 0) |  | rotate | `fill outputs.001`, `indent outputs`, `lattice outputs`, `logo outputs`, `marks outputs` |
| translate | vector | (0, 0, 0) |  | translate | `fill outputs.001`, `indent outputs`, `lattice outputs`, `logo outputs`, `marks outputs` |
| scale axis | vector | (1, 1, 1) |  | scale axis | `fill outputs.001`, `indent outputs`, `lattice outputs` |
| protect geometry | float | 1 |  | protect geometry | `fill outputs.001`, `shell outputs` |
| smooth protected geometry | float | 3 |  | smooth protected geometry | `fill outputs.001` |
| shell thickness | float | 2.7 |  | shell thickness | `fill outputs.001`, `shell outputs` |
| shell protect geometry | float | 3 |  | shell protect geometry | `fill outputs.001` |
| shell smooth protected | float | 3 |  | shell smooth protected | `fill outputs.001` |
| insert rim depth | float | 1 |  | insert rim depth | `fill outputs.001`, `indent outputs`, `lattice outputs` |
| insert rim height | float | 2 |  | insert rim height | `fill outputs.001`, `indent outputs`, `lattice outputs` |
| protect flat surface | float | 3 |  | protect flat surface | `fill outputs.001` |
| smooth flat surface | float | 3 |  | smooth flat surface | `fill outputs.001` |
| insert rim smooth | float | 5 |  | insert rim smooth | `fill outputs.001`, `indent outputs`, `lattice outputs` |
| smooth pattern | float | 6 |  | smooth pattern | `fill outputs.001`, `indent outputs`, `lattice outputs` |
| protect sharp | float | 3 |  | protect sharp | `fill outputs.001`, `indent outputs`, `lattice outputs` |
| smooth sharp | float | 5 |  | smooth sharp | `fill outputs.001`, `indent outputs`, `lattice outputs` |

## grid texture parameters

Placed in presets: `GripR1 stick L parameters`, `GripR1 stick R parameters`, `GripV stick L parameters`, `GripV stick R parameters`, `GripX stick L parameters`, `GripX stick R parameters`. Placed in any group: 6 group(s).

| Input | Type | Default | Range | Bundle key | Unpacked by |
|---|---|---|---|---|---|
| texture height | float | -0.2 |  | **square texture height** | `stick outputs` |
| texture subdivisions | int | 3 |  | **square texture subdivisions** | `stick outputs` |
| texture sharpness | float | 0.4 |  | **square texture sharpness** | `stick outputs` |
| grid curvature offset | float | 0 |  | grid curvature offset | `stick outputs` |
| scale | float | 1 |  | **scale correction** | `stick outputs` |
| bottom xy correction | float | 0 |  | bottom xy correction | `stick outputs` |
| bottom z correction | float | 0.1 |  | bottom z correction | `stick outputs` |
| z offset | float | 0 |  | z offset | `stick outputs` |

## holllow lattice parameters

Placed in presets: `GripV  lattice parameters`. Placed in any group: 1 group(s).

| Input | Type | Default | Range | Bundle key | Unpacked by |
|---|---|---|---|---|---|
| voxel remesh size | float | 1 |  | voxel remesh size | `shell outputs` |
| band remesh width | int | 20 |  | band remesh width | `shell outputs` |
| smooth sdf | int | 0 |  | smooth sdf | `shell outputs` |
| protect geometry | float | 1 |  | protect geometry | `fill outputs.001`, `shell outputs` |
| shell thickness | float | 2.7 |  | shell thickness | `fill outputs.001`, `shell outputs` |

## hollow  parameters

Placed in presets: `GripV cubic hollow parameters`, `GripV hollow parameters`, `GripX hollow parameters`. Placed in any group: 3 group(s).

| Input | Type | Default | Range | Bundle key | Unpacked by |
|---|---|---|---|---|---|
| voxel remesh size | float | 1 |  | voxel remesh size | `shell outputs` |
| band remesh width | int | 20 |  | band remesh width | `shell outputs` |
| smooth sdf | int | 0 |  | smooth sdf | `shell outputs` |
| protect geometry | float | 1 |  | protect geometry | `fill outputs.001`, `shell outputs` |
| shell thickness | float | 2.7 |  | shell thickness | `fill outputs.001`, `shell outputs` |

## home advanced parameters

Placed in presets: `GripR1 home`, `GripR1 home_OLD`. Placed in any group: 2 group(s).

| Input | Type | Default | Range | Bundle key | Unpacked by |
|---|---|---|---|---|---|
| home number of sides | int | 6 | 3 … 10 | home number of sides |  |
| home base radius | float | 7 |  | home base radius |  |
| base curve fillet | float | 2 | 1 … 4 | base curve fillet | `dpad button outputs` |
| fillet subdiv | int | 16 |  | fillet subdiv | `base curve outputs`, `dpad button outputs` |
| fillet tolerance | float | 0.6 |  | fillet tolerance | `ABXY button outputs`, `base curve outputs` |

## icosahedron texture parameters

Placed in presets: `GripR1 stick L parameters`, `GripR1 stick R parameters`, `GripV stick L parameters`, `GripV stick R parameters`, `GripX stick L parameters`, `GripX stick R parameters`. Placed in any group: 6 group(s).

| Input | Type | Default | Range | Bundle key | Unpacked by |
|---|---|---|---|---|---|
| texture height | float | -0.2 |  | texture height | `dpad stick outputs`, `stick outputs` |
| texture sharpness | float | 0.4 |  | texture sharpness | `dpad stick outputs`, `stick outputs` |
| icosahedron subdivisions | int | 3 |  … 4 | **texture subdivisions** | `stick outputs` |
| icosahedron curvature offset | float | -8.2 |  | icosahedron curvature offset | `stick outputs` |

## L1 parameters

Placed in presets: `GripR1 L1 parameters`. Placed in any group: 1 group(s).

| Input | Type | Default | Range | Bundle key | Unpacked by |
|---|---|---|---|---|---|
| front press tol | float | 0 |  | front press tol |  |
| front offset | float | 0 |  | front offset |  |
| offset | float | 4 |  | offset |  |

## marks inputs

Placed in presets: none. Placed in any group: 1 group(s).

| Input | Type | Default | Range | Bundle key | Unpacked by |
|---|---|---|---|---|---|
| mark depth | float | 0.46 |  | **depth** | `lever R1L1 outputs`, `logo outputs` |
| insertion | bool | off |  | insertion | `logo outputs`, `marks outputs` |
| type | menu | custom |  | type; via nodes: **custom**, **parameter**, **rotate**, **rotate text**, **text** | `fill outputs.001`, `indent outputs`, `lattice outputs`, `logo outputs`, `marks outputs` |
| font size | float | 9.6 |  | font size | `logo outputs`, `marks outputs` |
| text | string | A |  | via nodes: text | `logo outputs`, `marks outputs` |
| translate | vector | (0, 0, 0) |  | translate | `fill outputs.001`, `indent outputs`, `lattice outputs`, `logo outputs`, `marks outputs` |
| rotate text | float | 0 | -1e+04 … 1e+04 | via nodes: **rotate**, rotate text | `fill outputs.001`, `indent outputs`, `lattice outputs`, `logo outputs`, `marks outputs` |
| rotate | float | 0 | -1e+04 … 1e+04 | via nodes: rotate, **rotate text** | `fill outputs.001`, `indent outputs`, `lattice outputs`, `logo outputs`, `marks outputs` |
| axis | menu | X |  | via nodes: axis | `marks outputs` |
| side | menu | min |  | via nodes: **min_max** | `marks outputs` |
| parameter bundle | bundle |  |  | via nodes: **text** | `logo outputs`, `marks outputs` |
| parameters | string |  |  | via nodes: **text** | `logo outputs`, `marks outputs` |
| Decimals | int | 2 | 0 …  | via nodes: **text** | `logo outputs`, `marks outputs` |
| bump | float | 0.16 | -1e+04 … 1e+04 | bump | `logo outputs`, `marks outputs` |
| mirror | bool | off |  | mirror |  |

Keys not filled from an input: **text** ← Switch.008; **font** ← unlinked: Segoe UI Bold; **rotate text** ← Switch.011; **rotate** ← Switch.011; **parameter** ← Menu Switch.001; **axis** ← Menu Switch.005; **min_max** ← Menu Switch.006; **custom** ← Menu Switch.001.

## marks parameters

Placed in presets: `GripV  lever R1L1`, `GripV R2 parameters`, `GripV R4 parameters`, `GripV abxy`, `GripV dpad`, `GripV home`, `GripV select`, `GripX R2 parameters` +6. Placed in any group: 14 group(s).

| Input | Type | Default | Range | Bundle key | Unpacked by |
|---|---|---|---|---|---|
| bump | float | 0.16 | -1e+04 … 1e+04 | bump | `logo outputs`, `marks outputs` |
| mark depth | float | 0.46 |  | mark depth | `marks outputs` |
| insertion | bool | off |  | insertion | `logo outputs`, `marks outputs` |
| type | menu | custom |  | type; via nodes: **Side mark**, **curve**, **custom**, **parameter**, **rotate**, **rotate text**, **text** | `fill outputs.001`, `indent outputs`, `lattice outputs`, `logo outputs`, `marks outputs` |
| L-R side | bool | off |  | via nodes: **Side mark**, **text** | `logo outputs`, `marks outputs` |
| text | string | A |  | via nodes: text | `logo outputs`, `marks outputs` |
| parameters | string |  |  | via nodes: **text** | `logo outputs`, `marks outputs` |
| font size | float | 9.6 |  | font size | `logo outputs`, `marks outputs` |
| translate | vector | (0, 0, 0) |  | translate | `fill outputs.001`, `indent outputs`, `lattice outputs`, `logo outputs`, `marks outputs` |
| rotate text | float | 0 | -1e+04 … 1e+04 | via nodes: **rotate**, rotate text | `fill outputs.001`, `indent outputs`, `lattice outputs`, `logo outputs`, `marks outputs` |
| rotate | float | 0 | -1e+04 … 1e+04 | via nodes: rotate, **rotate text** | `fill outputs.001`, `indent outputs`, `lattice outputs`, `logo outputs`, `marks outputs` |
| axis | menu | X |  | via nodes: **axis v** | `marks outputs` |
| side | menu | min |  | via nodes: **min_max** | `marks outputs` |
| parameter bundle | bundle |  |  | via nodes: **text** | `logo outputs`, `marks outputs` |
| Decimals | int | 2 | 0 …  | via nodes: **text** | `logo outputs`, `marks outputs` |
| Character Spacing | float | 1.1 | 0 …  | Character Spacing | `marks outputs` |
| Word Spacing | float | 0 | 0 …  | Word Spacing | `marks outputs` |
| Line Spacing | float | 0.7 | 0 …  | Line Spacing | `marks outputs` |
| Text Box Width | float | 0.1 | 0 …  | Text Box Width | `marks outputs` |

Keys not filled from an input: **text** ← Switch.009; **font** ← unlinked: Segoe UI Bold; **rotate text** ← Switch.011; **rotate** ← Switch.011; **parameter** ← Menu Switch.001; **axis** ← Menu Switch.005; **min_max** ← Menu Switch.006; **custom** ← Menu Switch.001; **curve** ← Menu Switch.001; **axis v** ← Menu Switch.007; **Side mark** ← Switch.001.

## middle plate parameters

Placed in presets: `GripR1 middle plate parameters`, `GripR1 shell middle plate parameters`, `GripV middle plate parameters`, `GripX hollow fill middle plate parameters`, `GripX shell middle plate parameters`. Placed in any group: 5 group(s).

| Input | Type | Default | Range | Bundle key | Unpacked by |
|---|---|---|---|---|---|
| insert height | float | 1 |  | insert height | `middle plate outputs` |
| inset width | float | 2.4 |  | inset width | `middle plate outputs` |
| plate inset width | float | 0.4 |  | plate inset width | `middle plate outputs` |
| hook inset | float | 0.2 |  | hook inset | `middle plate outputs` |
| hook height | float | 0.2 |  | hook height | `middle plate outputs` |
| xy tolerance | float | 0.1 |  | xy tolerance | `middle plate outputs` |
| hook to top | float | 0.2 |  | hook to top | `middle plate outputs` |
| Z tolerance | float | 0.2 |  | Z tolerance | `R1L1 outputs`, `middle plate outputs` |
| fit Z tolerance | float | 0 |  | fit Z tolerance | `middle plate outputs` |
| inner Z tolerance | float | 0.2 |  | inner Z tolerance | `middle plate outputs` |
| inner xy tolerance | float | 0.4 |  | inner xy tolerance | `middle plate outputs` |
| pcb pocket thickness | float | 1.6 |  | pcb pocket thickness | `middle plate outputs` |
| pcb pocket tolerance | float | 0.3 |  | pcb pocket tolerance | `middle plate outputs` |
| rim slant height | float | 6 |  | rim slant height | `middle plate outputs` |
| rim slant outset | float | 6 |  | rim slant outset | `middle plate outputs` |
| slant height | float | 0.92 |  | slant height | `middle plate outputs` |

## pcb cutout parameters

Placed in presets: `GripR1 pcb cutout paramters`, `GripR1 pcb cutout paramters.001`, `GripV pcb cutout paramters`, `GripX pcb cutout paramters`. Placed in any group: 4 group(s).

| Input | Type | Default | Range | Bundle key | Unpacked by |
|---|---|---|---|---|---|
| PCB tolerance XY | float | 0.75 |  | PCB tolerance XY | `pcb outputs` |
| PCB thickness | float | 0 |  | PCB thickness | `pcb outputs` |
| PCB support edge | float | 1 |  | **PCB offset support** | `pcb outputs` |
| PCB below height | float | 2 |  | PCB below height | `pcb outputs` |

## pins params

Placed in presets: `GripR1 pins`, `GripV pins parameters`, `GripX pins`. Placed in any group: 3 group(s).

| Input | Type | Default | Range | Bundle key | Unpacked by |
|---|---|---|---|---|---|
| pin width | float | 4 |  | pin width |  |
| pin height | float | 8 |  | pin height |  |
| xy tol | float | 0.1 |  | xy tol |  |
| z tol | float | 0.6 |  | z tol |  |
| bevel | float | 1 |  | bevel | `trigger outputs` |

## pins postion

Placed in presets: `GripR1 pins`, `GripV pins parameters`, `GripX pins`. Placed in any group: 3 group(s).

| Input | Type | Default | Range | Bundle key | Unpacked by |
|---|---|---|---|---|---|
| X | float | 72.22 |  | X | `cubic fill outputs`, `lever R1L1 outputs` |
| Y | float | -57.31 |  | Y | `cubic fill outputs`, `lever R1L1 outputs` |
| Z | float | 40 |  | Z | `cubic fill outputs`, `lever R1L1 outputs` |

## R1 lever paramteters

Placed in presets: none. Placed in any group: 1 group(s).

| Input | Type | Default | Range | Bundle key | Unpacked by |
|---|---|---|---|---|---|
| button press tol | float | 0 |  | button press tol | `lever R1L1 outputs` |
| top bevel | float | 2.5 |  | top bevel | `R1L1 outputs`, `button outputs`, `stick outputs` |
| stem tolerance | float | 0.03 |  | stem tolerance | `lever R1L1 outputs` |
| wdith | float | 19.4 |  | wdith | `R1L1 outputs`, `lever R1L1 outputs` |
| height | float | 7.9 |  | height | `R1L1 outputs`, `lever R1L1 outputs` |
| stem radius | float | 3 |  | stem radius | `lever R1L1 outputs` |
| Z tolerance | float | 0.5 |  | Z tolerance | `R1L1 outputs`, `middle plate outputs` |
| X tolerance | float | 0.3 |  | X tolerance | `R1L1 outputs`, `lever R1L1 outputs` |
| bevel inner | float | 3 |  | bevel inner | `R1L1 outputs`, `lever R1L1 outputs` |
| bevel inner sbdiv | int | 2 |  | bevel inner sbdiv | `R1L1 outputs`, `lever R1L1 outputs` |
| overlap | float | -5.4 |  | overlap | `lever R1L1 outputs` |
| overlap tolerance | float | 0.2 |  | overlap tolerance | `lever R1L1 outputs` |
| button height | float | 2.2 |  | button height | `R1L1 outputs`, `button outputs` |
| depth | float | 2.2 |  | depth | `lever R1L1 outputs`, `logo outputs` |
| insert depth | float | 1.8 |  | insert depth | `lever R1L1 outputs` |
| button inset offset | float | 0.6 |  | button inset offset | `lever R1L1 outputs` |
| overlap slant | float | 2.9 |  | overlap slant | `lever R1L1 outputs` |
| button front shift X | float | 18 |  | button front shift X | `lever R1L1 outputs` |
| curved R1L1 | bool | off |  | curved R1L1 | `lever R1L1 outputs` |

## R1 lever postion

Placed in presets: none. Placed in any group: 1 group(s).

| Input | Type | Default | Range | Bundle key | Unpacked by |
|---|---|---|---|---|---|
| X | float | 28 |  | X | `cubic fill outputs`, `lever R1L1 outputs` |
| Y | float | -14 |  | Y | `cubic fill outputs`, `lever R1L1 outputs` |
| Z | float | 40 |  | Z | `cubic fill outputs`, `lever R1L1 outputs` |

## R1 parameters

Placed in presets: `GripR1 R1 parameters`. Placed in any group: 1 group(s).

| Input | Type | Default | Range | Bundle key | Unpacked by |
|---|---|---|---|---|---|
| front press tol | float | 0 |  | front press tol |  |
| front offset | float | 0 |  | front offset |  |
| offset | float | 4 |  | offset |  |

## R1L1 lever parameters

Placed in presets: `GripV  lever R1L1`, `GripX lever R1L1`. Placed in any group: 2 group(s).

| Input | Type | Default | Range | Bundle key | Unpacked by |
|---|---|---|---|---|---|
| button press tol | float | 0 |  | button press tol | `lever R1L1 outputs` |
| top bevel | float | 2.5 |  | **bumper top bevel** | `lever R1L1 outputs` |
| stem tolerance | float | 0.03 |  | stem tolerance | `lever R1L1 outputs` |
| wdith | float | 19.4 |  | wdith | `R1L1 outputs`, `lever R1L1 outputs` |
| height | float | 7.9 |  | height | `R1L1 outputs`, `lever R1L1 outputs` |
| stem radius | float | 3 |  | stem radius | `lever R1L1 outputs` |
| bumper Z tolerance | float | 0.5 |  | bumper Z tolerance | `lever R1L1 outputs` |
| X tolerance | float | 0.3 |  | X tolerance | `R1L1 outputs`, `lever R1L1 outputs` |
| bevel inner | float | 3 |  | bevel inner | `R1L1 outputs`, `lever R1L1 outputs` |
| bevel inner sbdiv | int | 2 |  | bevel inner sbdiv | `R1L1 outputs`, `lever R1L1 outputs` |
| overlap | float | -5.4 |  | overlap | `lever R1L1 outputs` |
| overlap tolerance | float | 0.2 |  | overlap tolerance | `lever R1L1 outputs` |
| button height | float | 2.2 |  | **bumper button height** | `lever R1L1 outputs` |
| depth | float | 2.2 |  | depth | `lever R1L1 outputs`, `logo outputs` |
| insert depth | float | 1.8 |  | insert depth | `lever R1L1 outputs` |
| button inset offset | float | 0.6 |  | button inset offset | `lever R1L1 outputs` |
| overlap slant | float | 2.9 |  | overlap slant | `lever R1L1 outputs` |
| button front shift X | float | 18 |  | button front shift X | `lever R1L1 outputs` |
| curved R1L1 | bool | off |  | curved R1L1 | `lever R1L1 outputs` |
| curved button thickness | float | 6.1 |  | curved button thickness | `lever R1L1 outputs` |
| curved button slant | float | -1 |  | curved button slant | `lever R1L1 outputs` |
| curved button depth tolerance | float | 1 |  | curved button depth tolerance | `lever R1L1 outputs` |
| curved button bevel | float | 1 |  | curved button bevel | `lever R1L1 outputs` |
| X | float | 0 |  | X | `cubic fill outputs`, `lever R1L1 outputs` |
| Y | float | 0 |  | Y | `cubic fill outputs`, `lever R1L1 outputs` |
| Z | float | 0 |  | Z | `cubic fill outputs`, `lever R1L1 outputs` |
| R1L1 flex | bool | off |  | R1L1 flex | `lever R1L1 outputs` |

## screw parameters

Placed in presets: none. Placed in any group: 3 group(s).

| Input | Type | Default | Range | Bundle key | Unpacked by |
|---|---|---|---|---|---|
| screw hole diameter | float | 2.9 |  | screw hole diameter | `screw outputs` |
| screw head hole diameter | float | 5.2 |  | screw head hole diameter | `screw outputs` |
| screw head hole height | float | 4.8 |  | screw head hole height | `screw outputs` |
| screw length | float | 12 |  | screw length | `screw outputs` |
| screwdriver hole diameter | float | 5.2 |  | screwdriver hole diameter | `screw outputs` |
| screwdriver guide slant height | float | 5 |  | screwdriver guide slant height | `screw outputs` |
| nut width | float | 5.1 |  | nut width | `screw outputs` |
| nut slot hideout depth | float | 3.2 |  | nut slot hideout depth | `screw outputs` |
| nut slot depth tolerance offset | float | 0.1 |  | nut slot depth tolerance offset | `screw outputs` |
| nut height | float | 2 |  | nut height | `screw outputs` |
| nut pocket length | float | 8.7 |  | nut pocket length | `screw outputs` |
| screw end slot offset | float | 0.4 |  | screw end slot offset | `screw outputs` |
| reinforcer offset | float | 3 |  | reinforcer offset | `screw outputs` |
| reinforcer top offset | float | 0 |  | reinforcer top offset | `screw outputs` |

## screw parameters.002

Placed in presets: none. Placed in any group: 1 group(s).

| Input | Type | Default | Range | Bundle key | Unpacked by |
|---|---|---|---|---|---|
| screw hole diameter | float | 2.9 |  | screw hole diameter | `screw outputs` |
| screw head hole diameter | float | 5.2 |  | screw head hole diameter | `screw outputs` |
| screw head hole height | float | 4.8 |  | screw head hole height | `screw outputs` |
| screw front length | float | 12 |  | screw front length |  |
| screw rear length | float | 12 |  | screw rear length |  |
| screw side length | float | 16 |  | screw side length |  |
| screwdriver hole diameter | float | 5.2 |  | screwdriver hole diameter | `screw outputs` |
| screwdriver side hole diameter | float | 7.6 |  | screwdriver side hole diameter |  |
| screwdriver guide slant height | float | 5 |  | screwdriver guide slant height | `screw outputs` |
| nut width | float | 5.1 |  | nut width | `screw outputs` |
| nut slot hideout depth | float | 3.2 |  | nut slot hideout depth | `screw outputs` |
| nut slot depth tolerance offset | float | 0.1 |  | nut slot depth tolerance offset | `screw outputs` |
| nut height | float | 2 |  | nut height | `screw outputs` |
| nut pocket length | float | 8.7 |  | nut pocket length | `screw outputs` |
| screw end slot offset | float | 0.4 |  | screw end slot offset | `screw outputs` |

## screw position

Placed in presets: none. Placed in any group: 3 group(s).

| Input | Type | Default | Range | Bundle key | Unpacked by |
|---|---|---|---|---|---|
| position | vector | (0, 0, 0) |  | position | `screw outputs` |
| rotation | float | 0 |  | rotation | `screw outputs` |

## screw positions

Placed in presets: `GripR1 screw positions`. Placed in any group: 2 group(s).

| Input | Type | Default | Range | Bundle key | Unpacked by |
|---|---|---|---|---|---|
| screw front X | float | 51.1 |  | screw front X |  |
| screw front Y | float | -0.7511 |  | screw front Y |  |
| screw front Z | float | 46.6 |  | screw front Z |  |
| screw side X | float | 69.85 |  | screw side X |  |
| screw side Y | float | -52.81 |  | screw side Y |  |
| screw side Z | float | 46.6 |  | screw side Z |  |
| screw back X | float | 28.11 |  | screw back X |  |
| screw back Y | float | -69.7 |  | screw back Y |  |
| screw back Z | float | 46.6 |  | screw back Z |  |
| screw front rotate | float | -53.2 |  | screw front rotate |  |
| screw side rotate | float | 90 |  | screw side rotate |  |
| screw back rotate | float | 0 |  | screw back rotate |  |

## scroll parameters

Placed in presets: `GripR1 scrollwheel`, `GripV scrollwheel`, `GripX scrollwheel`. Placed in any group: 3 group(s).

| Input | Type | Default | Range | Bundle key | Unpacked by |
|---|---|---|---|---|---|
| scroll radius offset | float | -1.15 | -5 … 3 | scroll radius offset |  |
| scroll width offset | float | 0 |  | scroll width offset |  |
| scroll wheel tolerance | float | 0.6 |  | scroll wheel tolerance |  |
| scroll wheel shift X | float | 0 |  | scroll wheel shift X |  |

## shield parameters

Placed in presets: `GripR1 stick L parameters`, `GripR1 stick R parameters`, `GripV stick L parameters`, `GripV stick R parameters`, `GripX stick L parameters`, `GripX stick R parameters`. Placed in any group: 6 group(s).

| Input | Type | Default | Range | Bundle key | Unpacked by |
|---|---|---|---|---|---|
| sheild | bool | off |  | sheild | `stick outputs` |
| sheild height | float | -1.8 |  | sheild height | `stick outputs` |
| shield cutoff height | float | 10.6 |  | shield cutoff height | `stick outputs` |
| sheild radius offset | float | 12.4 |  | **sheild radius** | `stick outputs` |
| FDM shield thickness | float | 0 |  | FDM shield thickness | `stick outputs` |
| FDM Z correction | float | 0 |  | FDM Z correction | `stick outputs` |

## spiral trigger params

Placed in presets: none. Placed in any group: 1 group(s).

| Input | Type | Default | Range | Bundle key | Unpacked by |
|---|---|---|---|---|---|
| height | float | -15.2 |  | height | `R1L1 outputs`, `lever R1L1 outputs` |
| turns | float | 0.17 |  | turns |  |
| profile height | float | 8.8 |  | profile height |  |
| profile width | float | 9.5 |  | profile width |  |
| fillet | float | 1.7 |  | fillet |  |
| trigger length | float | -18.8 |  | trigger length | `trigger outputs` |

## stick top parameters

Placed in presets: `GripR1 stick L parameters`, `GripR1 stick R parameters`, `GripV stick L parameters`, `GripV stick R parameters`, `GripX stick L parameters`, `GripX stick R parameters`. Placed in any group: 6 group(s).

| Input | Type | Default | Range | Bundle key | Unpacked by |
|---|---|---|---|---|---|
| top shape | menu |  |  | via nodes: **top type** | `stick outputs` |
| swap top rotation | bool | off |  | swap top rotation | `stick outputs` |
| extrude texture | bool | off |  | **texture** | `stick outputs` |
| top curvature | menu |  |  | via nodes: **texture type** | `stick outputs` |
| texture type | menu |  |  | via nodes: **flat texture type** | `stick outputs` |
| square top subd | int | 4 |  | square top subd | `stick outputs` |
| square morph | float | 0.1 |  | square morph | `stick outputs` |

Keys not filled from an input: **top type** ← top shape; **texture type** ← top curvature; **flat texture type** ← texture type.

## top face parameters

Placed in presets: `GripV  lattice parameters`, `GripV cubic hollow parameters`, `GripV hollow parameters`, `GripX hollow parameters`. Placed in any group: 4 group(s).

| Input | Type | Default | Range | Bundle key | Unpacked by |
|---|---|---|---|---|---|
| top thickness | float | 2.4 |  | top thickness | `top face outputs` |
| top grid | bool | on |  | top grid | `top face outputs` |
| grid thickness | float | 1.2 |  | grid thickness | `top face outputs` |
| parts offset | float | 1.6 |  | parts offset | `top face outputs` |
| stick offset | float | 3 |  | stick offset | `top face outputs` |
| smooth grid | int | 3 |  | smooth grid | `top face outputs` |

## trigger parameters

Placed in presets: `GripR1 R2 parameters`, `GripR1 R4 parameters`, `GripV R2 parameters`, `GripV R4 parameters`, `GripX R2 parameters`, `GripX R4 parameters`. Placed in any group: 7 group(s).

| Input | Type | Default | Range | Bundle key | Unpacked by |
|---|---|---|---|---|---|
| button press tolerance | float | 0.3 |  | button press tolerance | `R1L1 outputs`, `trigger outputs` |
| tip angle offset | float | -4.9 |  | tip angle offset | `trigger outputs` |
| tip shear | float | 0 |  | tip shear | `trigger outputs` |
| trigger length | float | 47.1 |  | trigger length | `trigger outputs` |
| top bevel | float | 1.2 |  | **trigger top bevel** | `trigger outputs` |
| x tolerance | float | 0.3 |  | **trigger x tolerance** | `trigger outputs` |
| radius tolerance | float | 0.3 |  | radius tolerance | `trigger outputs` |
| bevel | float | 4.2 |  | bevel | `trigger outputs` |
| bevel subd | int | 2 |  | bevel subd | `trigger outputs` |
| bevel cutoff | float | 0.5 |  | **trigger bevel cutoff** | `trigger outputs` |
| action | bool | off |  | action | `dpad stick outputs`, `stick outputs`, `trigger outputs` |
| trigger radius | float | 40.7 |  | trigger radius | `trigger outputs` |
| stopper length | float | 21.7 |  | stopper length | `trigger outputs` |
| button rotation | float | 0 |  | button rotation | `trigger outputs` |
| shift z | float | 0 |  | shift z | `trigger outputs` |
| button radius offset | float | 0 |  | button radius offset | `trigger outputs` |
| height | float | 14.4 |  | **trigger height** | `trigger outputs` |
| width | float | 11.2 |  | width | `trigger outputs` |
| stopper height | float | 1 |  | **trigger stopper height** | `trigger outputs` |
| subdivision length | float | 1 |  | subdivision length | `trigger outputs` |
| button pressed height | float | 1.65 |  | button pressed height | `trigger outputs` |
| x offset | float | 0 |  | x offset | `trigger outputs` |

## voronoi parameters

Placed in presets: `GripR1 voroni indent parameters`, `GripR1 voronoi  hollow parameters`, `GripR1 voronoi skeleton parameters`, `GripV voroni indent parameters`, `GripV voronoi  hollow parameters`, `GripV voronoi skeleton parameters`, `GripX voroni indent parameters`, `GripX voronoi  hollow parameters` +1. Placed in any group: 9 group(s).

| Input | Type | Default | Range | Bundle key | Unpacked by |
|---|---|---|---|---|---|
| voronoi randomness | float | 0.76 |  | voronoi randomness |  |

