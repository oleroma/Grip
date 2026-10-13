# Node group catalogue

All 511 node groups in `Grip.blend`, grouped by role. Generated from the file [wiring].

- **Status** `release`: reachable from the objects of the `GripV` or `GripX` scene, following their modifiers, every group node inside (in every branch of every switch, connected or not) and every object or collection referenced by *Object Info* / *Collection Info* nodes and modifier inputs, such as the cutters in `source`. This is a static upper bound: a group can be `release` and still be dead code, like the old selection chain that hangs off the unconnected `trigger cap` (see [9. Issues](../09-issues.md) D3). `source only`: reachable only from objects that live just in the `source` scene. `unreachable`: no modifier reaches it.
- **Modifier on**: objects whose modifier uses the group directly. **Placed in**: groups that contain a node of this group.

Counts: 462 release, 39 source only, 10 unreachable; 64 groups are used directly by a modifier (24 of them on objects of the two release scenes).

| Role | Groups |
|---|---|
| selection plumbing | 12 |
| variant parameters | 4 |
| controls panel | 7 |
| preset | 127 |
| variant-specific | 4 |
| constructor (packs a bundle) | 54 |
| outputs (unpacks a bundle) | 24 |
| modifier group | 62 |
| geometry / helper | 217 |

## Selection plumbing (12)

Turns the global switches and the variant presets into the bundle each part reads. See [2. Parameter system](../02-parameter-system.md).

| Group | Nodes | Status | Modifier on | Placed in |
|---|---|---|---|---|
| `basemesh variant` | 12 | release |  | `align pins`, `basemesh SDF variant`, `basemesh to sdf`, `basemesh top face position` +17 |
| `bundle variant switching base` | 4 | release |  | `part and variant` |
| `Combine variants` | 3 | **unreachable** |  | `parameters` |
| `global` | 2 | release |  | `GripV controls`, `GripX contols`, `controls`, `global outputs` |
| `global outputs` | 14 | release |  | `GripR1 parameters`, `GripV  lever R1L1`, `GripV R2 parameters`, `GripV R4 parameters` +62 |
| `global parameters` | 31 | release |  | `global` |
| `main switch` | 4 | release |  | `part and variant` |
| `part and variant` | 7 | release |  | `R4R2 parameters` |
| `part variant switching` | 4 | release |  | `R1L1 cutouts`, `back clip variant`, `basemesh variant`, `cap variant shift` +8 |
| `parts bundle` | 3 | release |  | `GripR1 parameters`, `GripV parameters`, `GripX parameters` |
| `selector` | 10 | release |  | `GripX pcb`, `L1`, `R1`, `R1 base geometry` +58 |
| `tolerance set` | 3 | release |  | `GripV  lever R1L1`, `GripV R2 parameters`, `GripV R4 parameters`, `GripV abxy` +10 |

## Variant parameters (4)

One per variant; fills the 22 slots of `parts bundle`.

| Group | Nodes | Status | Modifier on | Placed in |
|---|---|---|---|---|
| `GripR1  parameters` | 27 | release |  | `part and variant` |
| `GripR1 parameters` | 44 | release |  | `selector` |
| `GripV parameters` | 44 | release |  | `part and variant`, `selector` |
| `GripX parameters` | 42 | release |  | `part and variant`, `selector` |

## Controls panel (7)

Groups with no inputs or outputs that hold every preset of a variant, arranged for editing.

| Group | Nodes | Status | Modifier on | Placed in |
|---|---|---|---|---|
| `controls` | 5 | release | `case_front.002` |  |
| `GripR1 controls` | 29 | release |  | `controls` |
| `GripR1 fill controls` | 28 | release |  | `GripR1 controls` |
| `GripV controls` | 31 | release |  | `controls` |
| `GripV fill controls` | 27 | release |  | `GripV controls` |
| `GripX contols` | 30 | release |  | `controls` |
| `GripX fill controls` | 28 | release |  | `GripX contols` |

## Preset (127)

No inputs, one bundle output: the values typed inside are the model dimensions.

| Group | Nodes | Status | Modifier on | Placed in |
|---|---|---|---|---|
| `GripR1 abxy` | 13 | release |  | `GripR1 controls`, `GripR1 parameters` |
| `GripR1 abxy_OLD` | 7 | release |  | `GripR1  parameters` |
| `GripR1 cover parameters` | 5 | release |  | `GripR1 controls`, `GripR1 parameters` |
| `GripR1 cover parameters_OLD` | 9 | release |  | `GripR1  parameters` |
| `GripR1 cubic hollow array parameters` | 8 | release |  | `GripR1 fill controls`, `GripR1 parameters` |
| `GripR1 cubic hollow parameters` | 2 | release |  | `GripR1 fill controls`, `GripR1 parameters` |
| `GripR1 cubic indent parameters` | 2 | release |  | `GripR1 fill controls`, `GripR1 parameters` |
| `GripR1 cubic skeleton parameters` | 2 | release |  | `GripR1 fill controls` |
| `GripR1 diamond hollow parameters` | 2 | release |  | `GripR1 fill controls` |
| `GripR1 diamond indent parameters` | 2 | release |  | `GripR1 fill controls`, `GripR1 parameters` |
| `GripR1 diamond skeleton parameters` | 2 | release |  | `GripR1 fill controls` |
| `GripR1 dpad` | 11 | release |  | `GripR1 controls`, `GripR1 parameters` |
| `GripR1 dpad stick` | 4 | release |  | `GripR1 controls`, `GripR1 parameters` |
| `GripR1 dpad_OLD` | 5 | release |  | `GripR1  parameters` |
| `GripR1 FischerKoch CY hollow parameters` | 2 | release |  | `GripR1 fill controls` |
| `GripR1 FischerKoch CY indent parameters` | 2 | release |  | `GripR1 fill controls`, `GripR1 parameters` |
| `GripR1 FischerKoch CY skeleton parameters` | 2 | release |  | `GripR1 fill controls` |
| `GripR1 FischerKoch S hollow parameters` | 2 | release |  | `GripR1 fill controls` |
| `GripR1 FischerKoch S indent parameters` | 2 | release |  | `GripR1 fill controls`, `GripR1 parameters` |
| `GripR1 FischerKoch S skeleton parameters` | 2 | release |  | `GripR1 fill controls` |
| `GripR1 gyroid hollow parameters` | 2 | release |  | `GripR1 fill controls` |
| `GripR1 gyroid indent parameters` | 2 | release |  | `GripR1 fill controls`, `GripR1 parameters` |
| `GripR1 gyroid skeleton parameters` | 2 | release |  | `GripR1 fill controls` |
| `GripR1 home` | 7 | release |  | `GripR1 controls`, `GripR1 parameters` |
| `GripR1 home_OLD` | 5 | release |  | `GripR1  parameters` |
| `GripR1 L1 parameters` | 2 | release |  | `GripR1  parameters`, `GripR1 controls`, `GripR1 parameters` |
| `GripR1 middle plate parameters` | 2 | release |  | `GripR1 fill controls`, `GripR1 parameters` |
| `GripR1 pcb cutout paramters` | 2 | release |  | `GripR1 controls`, `GripR1 parameters` |
| `GripR1 pcb cutout paramters.001` | 2 | release |  | `GripR1  parameters` |
| `GripR1 pins` | 4 | release |  | `GripR1 controls`, `GripR1 parameters` |
| `GripR1 primitive hollow parameters` | 2 | release |  | `GripR1 fill controls` |
| `GripR1 primitive indent parameters` | 2 | release |  | `GripR1 fill controls`, `GripR1 parameters` |
| `GripR1 primitive skeleton parameters` | 2 | release |  | `GripR1 fill controls` |
| `GripR1 R1 parameters` | 2 | release |  | `GripR1  parameters`, `GripR1 controls`, `GripR1 parameters` |
| `GripR1 R1L1 parameters` | 5 | release |  | `GripR1  parameters`, `GripR1 controls`, `GripR1 parameters` |
| `GripR1 R2 parameters` | 4 | release |  | `GripR1  parameters`, `GripR1 controls`, `GripR1 parameters` |
| `GripR1 R4 parameters` | 4 | release |  | `GripR1  parameters`, `GripR1 controls`, `GripR1 parameters` |
| `GripR1 R4R2 parameters` | 4 | release |  | `GripR1  parameters` |
| `GripR1 screw positions` | 3 | release |  | `GripR1  parameters`, `GripR1 controls` |
| `GripR1 scrollwheel` | 2 | release |  | `GripR1  parameters`, `GripR1 controls`, `GripR1 parameters` |
| `GripR1 select` | 8 | release |  | `GripR1 controls`, `GripR1 parameters` |
| `GripR1 select_OLD` | 5 | release |  | `GripR1  parameters` |
| `GripR1 shell middle plate parameters` | 2 | release |  | `GripR1 parameters` |
| `GripR1 stick L parameters` | 56 | release |  | `GripR1 controls`, `GripR1 parameters` |
| `GripR1 stick L parameters_OLD` | 7 | release |  | `GripR1  parameters` |
| `GripR1 stick R parameters` | 74 | release |  | `GripR1 controls`, `GripR1 parameters` |
| `GripR1 voroni indent parameters` | 4 | release |  | `GripR1 fill controls`, `GripR1 parameters` |
| `GripR1 voronoi  hollow parameters` | 4 | release |  | `GripR1 fill controls` |
| `GripR1 voronoi skeleton parameters` | 5 | release |  | `GripR1 fill controls` |
| `GripV  lattice parameters` | 5 | release |  | `GripV fill controls`, `GripV parameters` |
| `GripV  lever R1L1` | 12 | release |  | `GripV controls`, `GripV parameters` |
| `GripV abxy` | 18 | release |  | `GripV controls`, `GripV parameters` |
| `GripV cover parameters` | 6 | release |  | `GripV controls`, `GripV parameters` |
| `GripV cubic hollow array parameters` | 8 | release |  | `GripV fill controls`, `GripV parameters` |
| `GripV cubic hollow parameters` | 5 | release |  | `GripV fill controls` |
| `GripV cubic indent parameters` | 2 | release |  | `GripV fill controls`, `GripV parameters` |
| `GripV cubic skeleton parameters` | 2 | release |  | `GripV fill controls` |
| `GripV diamond hollow parameters` | 2 | release |  | `GripV fill controls` |
| `GripV diamond indent parameters` | 2 | release |  | `GripV fill controls`, `GripV parameters` |
| `GripV diamond skeleton parameters` | 2 | release |  | `GripV fill controls` |
| `GripV dpad` | 11 | release |  | `GripV controls`, `GripV parameters` |
| `GripV dpad stick` | 5 | release |  | `GripV controls`, `GripV parameters` |
| `GripV FischerKoch CY hollow parameters` | 2 | release |  | `GripV fill controls` |
| `GripV FischerKoch CY indent parameters` | 2 | release |  | `GripV fill controls`, `GripV parameters` |
| `GripV FischerKoch CY skeleton parameters` | 2 | release |  | `GripV fill controls` |
| `GripV FischerKoch S hollow parameters` | 2 | release |  | `GripV fill controls` |
| `GripV FischerKoch S indent parameters` | 2 | release |  | `GripV fill controls`, `GripV parameters` |
| `GripV FischerKoch S skeleton parameters` | 2 | release |  | `GripV fill controls` |
| `GripV gyroid hollow parameters` | 2 | release |  | `GripV fill controls` |
| `GripV gyroid indent parameters` | 2 | release |  | `GripV fill controls`, `GripV parameters` |
| `GripV gyroid skeleton parameters` | 2 | release |  | `GripV fill controls` |
| `GripV hollow parameters` | 9 | release |  | `GripV controls`, `GripV parameters` |
| `GripV home` | 12 | release |  | `GripV controls`, `GripV parameters` |
| `GripV middle plate parameters` | 2 | release |  | `GripV controls`, `GripV parameters` |
| `GripV pcb cutout paramters` | 2 | release |  | `GripV controls`, `GripV parameters` |
| `GripV pins parameters` | 4 | release |  | `GripV controls`, `GripV parameters` |
| `GripV primitive hollow parameters` | 2 | release |  | `GripV fill controls` |
| `GripV primitive indent parameters` | 2 | release |  | `GripV fill controls`, `GripV parameters` |
| `GripV primitive skeleton parameters` | 2 | release |  | `GripV fill controls` |
| `GripV R2 parameters` | 16 | release |  | `GripV controls`, `GripV parameters` |
| `GripV R4 parameters` | 15 | release |  | `GripV controls`, `GripV parameters` |
| `GripV scrollwheel` | 2 | release |  | `GripV controls`, `GripV parameters` |
| `GripV select` | 11 | release |  | `GripV controls`, `GripV parameters` |
| `GripV stick L parameters` | 12 | release |  | `GripV controls`, `GripV parameters` |
| `GripV stick R parameters` | 16 | release |  | `GripV controls`, `GripV parameters` |
| `GripV voroni indent parameters` | 4 | release |  | `GripV fill controls`, `GripV parameters` |
| `GripV voronoi  hollow parameters` | 4 | release |  | `GripV fill controls` |
| `GripV voronoi skeleton parameters` | 5 | release |  | `GripV fill controls` |
| `GripX abxy` | 14 | release |  | `GripX contols`, `GripX parameters` |
| `GripX cover parameters` | 9 | release |  | `GripX contols`, `GripX parameters` |
| `GripX cubic hollow array parameters` | 17 | release |  | `GripX fill controls`, `GripX parameters` |
| `GripX cubic hollow parameters` | 2 | release |  | `GripX fill controls`, `GripX parameters` |
| `GripX cubic indent parameters` | 2 | release |  | `GripX fill controls`, `GripX parameters` |
| `GripX cubic skeleton parameters` | 2 | release |  | `GripX fill controls` |
| `GripX diamond hollow parameters` | 2 | release |  | `GripX fill controls` |
| `GripX diamond indent parameters` | 2 | release |  | `GripX fill controls`, `GripX parameters` |
| `GripX diamond skeleton parameters` | 2 | release |  | `GripX fill controls` |
| `GripX dpad` | 12 | release |  | `GripX contols`, `GripX parameters` |
| `GripX dpad stick` | 2 | release |  | `GripX contols`, `GripX parameters` |
| `GripX FischerKoch CY hollow parameters` | 2 | release |  | `GripX fill controls` |
| `GripX FischerKoch CY indent parameters` | 2 | release |  | `GripX fill controls`, `GripX parameters` |
| `GripX FischerKoch CY skeleton parameters` | 2 | release |  | `GripX fill controls` |
| `GripX FischerKoch S hollow parameters` | 2 | release |  | `GripX fill controls` |
| `GripX FischerKoch S indent parameters` | 2 | release |  | `GripX fill controls`, `GripX parameters` |
| `GripX FischerKoch S skeleton parameters` | 2 | release |  | `GripX fill controls` |
| `GripX gyroid hollow parameters` | 2 | release |  | `GripX fill controls` |
| `GripX gyroid indent parameters` | 2 | release |  | `GripX fill controls`, `GripX parameters` |
| `GripX gyroid skeleton parameters` | 2 | release |  | `GripX fill controls` |
| `GripX hollow fill middle plate parameters` | 2 | release |  | `GripX fill controls` |
| `GripX hollow parameters` | 5 | release |  | `GripX contols`, `GripX parameters` |
| `GripX home` | 12 | release |  | `GripX contols`, `GripX parameters` |
| `GripX lever R1L1` | 14 | release |  | `GripX contols`, `GripX parameters` |
| `GripX pcb cutout paramters` | 2 | release |  | `GripX contols`, `GripX parameters` |
| `GripX pins` | 4 | release |  | `GripX contols`, `GripX parameters` |
| `GripX primitive hollow parameters` | 2 | release |  | `GripX fill controls` |
| `GripX primitive indent parameters` | 2 | release |  | `GripX fill controls`, `GripX parameters` |
| `GripX primitive skeleton parameters` | 2 | release |  | `GripX fill controls` |
| `GripX R2 parameters` | 15 | release |  | `GripX contols`, `GripX parameters` |
| `GripX R4 parameters` | 15 | release |  | `GripX contols`, `GripX parameters` |
| `GripX scrollwheel` | 2 | release |  | `GripX contols`, `GripX parameters` |
| `GripX select` | 12 | release |  | `GripX contols`, `GripX parameters` |
| `GripX shell middle plate parameters` | 3 | release |  | `GripX contols`, `GripX parameters` |
| `GripX stick L parameters` | 58 | release |  | `GripX contols`, `GripX parameters` |
| `GripX stick R parameters` | 39 | release |  | `GripX contols`, `GripX parameters` |
| `GripX voroni indent parameters` | 4 | release |  | `GripX fill controls`, `GripX parameters` |
| `GripX voronoi  hollow parameters` | 4 | release |  | `GripX fill controls` |
| `GripX voronoi skeleton parameters` | 5 | release |  | `GripX fill controls` |

## Variant-specific (4)

Named after a variant but not a plain preset (with inputs, or several outputs).

| Group | Nodes | Status | Modifier on | Placed in |
|---|---|---|---|---|
| `GripR1 screw paramters` | 13 | release |  | `GripR1  parameters`, `GripR1 controls`, `GripR1 parameters` |
| `GripV screw paramters` | 12 | release |  | `GripV controls`, `GripV parameters` |
| `GripX pcb` | 5 | release | `pcb cutout` |  |
| `GripX screw paramters` | 16 | release |  | `GripX contols`, `GripX parameters` |

## Constructor (packs a bundle) (54)

Generic groups placed inside presets; their inputs are the parameters, packed into a bundle. Inputs and keys: [parameter-groups.md](parameter-groups.md).

| Group | Nodes | Status | Modifier on | Placed in |
|---|---|---|---|---|
| `abxy advanced parameters` | 3 | release |  | `GripR1 abxy`, `GripR1 abxy_OLD` |
| `advanced button parameters` | 3 | release |  | `GripR1 abxy`, `GripR1 abxy_OLD`, `GripR1 dpad`, `GripR1 dpad_OLD` +4 |
| `advanced caps parameters` | 3 | release |  | `GripR1 abxy`, `GripR1 dpad`, `GripR1 home`, `GripR1 select` +1 |
| `advanced cover parameters` | 3 | release |  | `GripR1 cover parameters`, `GripR1 cover parameters_OLD`, `GripV cover parameters`, `GripX cover parameters` |
| `advanced R1L1 parameters` | 3 | release |  | `GripR1 R1L1 parameters`, `R1L1 parameters`, `gripx R1L1 parameters` |
| `advanced R4R2 parameters` | 3 | release |  | `GripR1 R4R2 parameters` |
| `advanced stick parameters` | 3 | release |  | `GripR1 stick L parameters`, `GripR1 stick R parameters`, `GripV stick L parameters`, `GripV stick R parameters` +2 |
| `advanced stick parameters.001` | 3 | release |  | `GripR1 stick L parameters`, `GripR1 stick L parameters_OLD`, `GripR1 stick R parameters`, `parameters` |
| `advanced trigger parameters` | 3 | release |  | `GripR1 R2 parameters`, `GripR1 R4 parameters`, `trigger outputs` |
| `base usb width` | 3 | release |  | `cable hole` |
| `basic cover parameters` | 3 | release |  | `GripR1 cover parameters`, `GripR1 cover parameters_OLD`, `GripV cover parameters`, `GripX cover parameters` |
| `basic R1L1 parameters` | 3 | release |  | `GripR1 R1L1 parameters`, `R1L1 parameters`, `gripx R1L1 parameters` |
| `basic R4R2 parameters` | 3 | release |  | `GripR1 R4R2 parameters` |
| `basic stick parameters` | 4 | release |  | `GripR1 stick L parameters`, `GripR1 stick R parameters`, `GripV stick L parameters`, `GripV stick R parameters` +2 |
| `basic stick parameters.001` | 4 | release |  | `GripR1 stick L parameters`, `GripR1 stick L parameters_OLD`, `GripR1 stick R parameters`, `parameters` |
| `button parameters` | 3 | release |  | `GripR1 abxy`, `GripR1 abxy_OLD`, `GripR1 dpad`, `GripR1 dpad_OLD` +12 |
| `cable size` | 3 | release |  | `cable holder parameters` |
| `capacitive plate advanced parameters` | 3 | release |  | `GripR1 abxy`, `GripR1 abxy_OLD` |
| `capacitive plate parameters` | 4 | release |  | `GripR1 abxy`, `GripR1 abxy_OLD`, `GripV abxy`, `GripX abxy` |
| `caps parameters` | 4 | release |  | `GripR1 abxy`, `GripR1 dpad`, `GripR1 home`, `GripR1 select` +9 |
| `combine` | 3 | release |  | `GripR1  parameters` |
| `cubic fill array parameters` | 3 | release |  | `GripR1 cubic hollow array parameters`, `GripV cubic hollow array parameters`, `GripX cubic hollow array parameters` |
| `curve parameters` | 3 | release |  | `GripR1 select`, `GripR1 select_OLD`, `GripV abxy`, `GripV dpad` +6 |
| `dpad advanced parameters` | 3 | release |  | `GripR1 dpad`, `GripR1 dpad_OLD` |
| `dpad stick parameters` | 4 | release |  | `GripR1 dpad stick`, `GripV dpad stick`, `GripX dpad stick` |
| `fill parameters` | 3 | release |  | `GripV  lattice parameters`, `GripV cubic hollow parameters` |
| `fill parameters.001` | 3 | release |  | `GripR1 FischerKoch CY hollow parameters`, `GripR1 FischerKoch CY indent parameters`, `GripR1 FischerKoch CY skeleton parameters`, `GripR1 FischerKoch S hollow parameters` +59 |
| `grid texture parameters` | 3 | release |  | `GripR1 stick L parameters`, `GripR1 stick R parameters`, `GripV stick L parameters`, `GripV stick R parameters` +2 |
| `holllow lattice parameters` | 3 | release |  | `GripV  lattice parameters` |
| `hollow  parameters` | 3 | release |  | `GripV cubic hollow parameters`, `GripV hollow parameters`, `GripX hollow parameters` |
| `home advanced parameters` | 3 | release |  | `GripR1 home`, `GripR1 home_OLD` |
| `icosahedron texture parameters` | 3 | release |  | `GripR1 stick L parameters`, `GripR1 stick R parameters`, `GripV stick L parameters`, `GripV stick R parameters` +2 |
| `L1 parameters` | 3 | release |  | `GripR1 L1 parameters` |
| `marks inputs` | 19 | release |  | `R4` |
| `marks parameters` | 25 | release |  | `GripV  lever R1L1`, `GripV R2 parameters`, `GripV R4 parameters`, `GripV abxy` +10 |
| `middle plate parameters` | 3 | release |  | `GripR1 middle plate parameters`, `GripR1 shell middle plate parameters`, `GripV middle plate parameters`, `GripX hollow fill middle plate parameters` +1 |
| `pcb cutout parameters` | 4 | release |  | `GripR1 pcb cutout paramters`, `GripR1 pcb cutout paramters.001`, `GripV pcb cutout paramters`, `GripX pcb cutout paramters` |
| `pins params` | 3 | release |  | `GripR1 pins`, `GripV pins parameters`, `GripX pins` |
| `pins postion` | 3 | release |  | `GripR1 pins`, `GripV pins parameters`, `GripX pins` |
| `R1 lever paramteters` | 3 | release |  | `deault lever R1L1` |
| `R1 lever postion` | 3 | release |  | `deault lever R1L1` |
| `R1 parameters` | 3 | release |  | `GripR1 R1 parameters` |
| `R1L1 lever parameters` | 3 | release |  | `GripV  lever R1L1`, `GripX lever R1L1` |
| `screw parameters` | 3 | release |  | `GripR1 screw paramters`, `GripV screw paramters`, `GripX screw paramters` |
| `screw parameters.002` | 3 | release |  | `GripR1 screw paramters` |
| `screw position` | 3 | release |  | `GripR1 screw paramters`, `GripV screw paramters`, `GripX screw paramters` |
| `screw positions` | 3 | release |  | `GripR1 screw paramters`, `GripR1 screw positions` |
| `scroll parameters` | 3 | release |  | `GripR1 scrollwheel`, `GripV scrollwheel`, `GripX scrollwheel` |
| `shield parameters` | 3 | release |  | `GripR1 stick L parameters`, `GripR1 stick R parameters`, `GripV stick L parameters`, `GripV stick R parameters` +2 |
| `spiral trigger params` | 3 | source only |  | `spiral trigger` |
| `stick top parameters` | 6 | release |  | `GripR1 stick L parameters`, `GripR1 stick R parameters`, `GripV stick L parameters`, `GripV stick R parameters` +2 |
| `top face parameters` | 3 | release |  | `GripV  lattice parameters`, `GripV cubic hollow parameters`, `GripV hollow parameters`, `GripX hollow parameters` |
| `trigger parameters` | 3 | release |  | `GripR1 R2 parameters`, `GripR1 R4 parameters`, `GripV R2 parameters`, `GripV R4 parameters` +3 |
| `voronoi parameters` | 3 | release |  | `GripR1 voroni indent parameters`, `GripR1 voronoi  hollow parameters`, `GripR1 voronoi skeleton parameters`, `GripV voroni indent parameters` +5 |

## Outputs (unpacks a bundle) (24)

Unpack a part bundle into named sockets for the geometry groups.

| Group | Nodes | Status | Modifier on | Placed in |
|---|---|---|---|---|
| `ABXY button outputs` | 3 | release |  | `GripR1 abxy` |
| `base curve outputs` | 5 | release |  | `GripR1 select`, `GripV abxy`, `abxy`, `dpad` +3 |
| `button outputs` | 7 | release |  | `GripR1 dpad`, `GripV abxy`, `abxy`, `button.001` +3 |
| `cap plate outputs` | 3 | release |  | `GripR1 abxy`, `GripV abxy`, `abxy`, `button shafts sdf` +4 |
| `caps outputs` | 7 | release |  | `GripR1 dpad`, `GripV abxy`, `abxy`, `button.001` +6 |
| `cover outputs` | 4 | release |  | `GripV cover parameters`, `battery appendix`, `battery bool and cover`, `coVer base` +2 |
| `cubic fill outputs` | 3 | release |  | `cubic` |
| `dpad button outputs` | 5 | release |  | `dpad` |
| `dpad stick outputs` | 3 | release |  | `GripR1 dpad stick`, `GripV dpad stick`, `action`, `ball` +10 |
| `fill outputs.001` | 3 | release |  | `voronoi` |
| `indent outputs` | 3 | release |  | `fill limit`, `indent`, `pattern field` |
| `lattice outputs` | 3 | release |  | `cubic`, `insert rim`, `mesh to grid topology` |
| `lever R1L1 outputs` | 3 | release |  | `GripV  lever R1L1`, `GripX lever R1L1`, `button shafts sdf`, `lever R1L1 base` +3 |
| `logo outputs` | 3 | release |  | `logo` |
| `marks outputs` | 3 | release |  | `GripV  lever R1L1`, `GripX R4 parameters`, `GripX abxy`, `GripX dpad` +3 |
| `middle plate outputs` | 3 | release |  | `align pins`, `inner rim`, `middle plate`, `middle plate outputs.001` +3 |
| `middle plate outputs.001` | 3 | release |  | `align pin`, `extrude insert`, `hollow.001`, `inner supports` +1 |
| `pcb outputs` | 3 | release |  | `GripX pcb`, `corner relief`, `pcb cutout parameters` |
| `R1L1 outputs` | 4 | source only |  | `L1`, `flex switch` |
| `screw outputs` | 3 | release |  | `GripR1 screw paramters`, `GripV screw paramters`, `screws` |
| `shell outputs` | 3 | release |  | `button shafts sdf`, `hollow`, `part to grid` |
| `stick outputs` | 3 | release |  | `GripR1 stick L parameters`, `GripR1 stick R parameters`, `GripV stick L parameters`, `GripV stick R parameters` +12 |
| `top face outputs` | 3 | release |  | `top face` |
| `trigger outputs` | 7 | release |  | `GripV R2 parameters`, `trigger base`, `trigger cap` |

## Modifier group (62)

Used directly by an object modifier and not in a category above.

| Group | Nodes | Status | Modifier on | Placed in |
|---|---|---|---|---|
| `abxy button` | 4 | release | `abxy button`, `abxy cap down`, `abxy cap left`, `abxy cap right` +5 |  |
| `add thickness clip` | 11 | source only | `BACK CLIP`, `BACK CLIP CUTOUT`, `FRONT CLIP CUTOUT`, `USB CLIP` |  |
| `back clip variant` | 6 | source only | `BACK CLIP`, `BACK CLIP CUTOUT` |  |
| `battery compartment` | 6 | source only | `basemesh_gripx_no battery` |  |
| `bool` | 35 | release | `phone holder mount` | `dpad stick` |
| `bools.001` | 22 | source only | `magsafe nest`, `magsafe ring` |  |
| `cable hole` | 41 | release | `cable holder` |  |
| `cam` | 17 | source only | `cam` |  |
| `cap variant shift` | 7 | source only | `USB CLIP` |  |
| `capacitive plate` | 8 | release | `capacitive`, `capacitive plate cutout` |  |
| `case` | 6 | release | `case_bottom`, `case_top` |  |
| `circle` | 7 | release | `circle` |  |
| `clip` | 29 | source only | `BACK CLIP`, `USB CLIP` |  |
| `clip cutoff` | 22 | source only | `BACK CLIP`, `USB CLIP` |  |
| `corner relief` | 23 | release | `corner relief` |  |
| `cover` | 5 | release | `battery bool`, `battery cover` |  |
| `cutout adjustment to hole radius L` | 29 | release | `StickL cutout` |  |
| `cutout adjustment to hole radius R` | 29 | release | `Stick R cutout` |  |
| `dpad button` | 7 | release | `dpad button`, `dpad cap down`, `dpad cap left`, `dpad cap right` +5 |  |
| `dpad stick` | 118 | release | `ball support`, `dpad stick bool`, `dpad stick cap`, `rocker` +3 | `button shafts sdf` |
| `extra` | 6 | release | `StickL`, `StickR` |  |
| `fillet dpad` | 5 | release | `dpad cap curve down`, `dpad cap curve left`, `dpad cap curve right`, `dpad cap curve up` |  |
| `gripx middle plate R2 rim` | 10 | release | `hollow cutout` |  |
| `home button` | 4 | release | `home button`, `home cap`, `home cutout` |  |
| `L1` | 17 | source only | `L1 GripR1` |  |
| `lever R1L1` | 16 | release | `L1`, `R1` |  |
| `lever R1L1 bool` | 17 | release | `R1L1 bool` |  |
| `logo` | 33 | release | `abxy button`, `abxy cap down`, `abxy cap left`, `abxy cap right` +5 |  |
| `marmota case` | 6 | source only | `marmota case` |  |
| `marmota case cap` | 8 | source only | `marmota case cap` |  |
| `merge clean up` | 3 | source only | `R2 tip` |  |
| `middle plate` | 17 | release | `case_middle_plate` |  |
| `mir` | 9 | release | `L1 stock` |  |
| `MirrorX` | 16 | release | `BACK CLIP CUTOUT`, `FRONT CLIP CUTOUT`, `Plane`, `Plane.001` +41 | `button shafts sdf`, `clip cutoff`, `inner supports`, `lattice` +7 |
| `MirrorY` | 20 | source only | `clip mount`, `clip mount bool`, `fix`, `flex` +5 |  |
| `MirrorZ` | 20 | source only | `insert`, `marmota case`, `marmota case cap` |  |
| `nest` | 36 | source only | `nest bool` |  |
| `pcb Z tolerance` | 7 | release | `middle supports` |  |
| `pins` | 5 | release | `pin`, `pin bool` |  |
| `preserve` | 7 | source only | `GripR1 preserve contours` |  |
| `R1` | 14 | source only | `R1 GripR1` |  |
| `R1L1 bool` | 8 | release | `R1L1 bool.001` |  |
| `R4` | 12 | release | `R4 bool`, `R4 tip` |  |
| `screws` | 19 | release | `nut lock`, `reinforcers`, `screw bools` | `bottom bools`, `button shafts sdf`, `plate bools` |
| `scroll bool` | 19 | release | `Wheel cutout (B)` |  |
| `scrollwheel` | 26 | release | `scrollwheel` |  |
| `scrollwheel stem` | 13 | release | `scrollwheel core` |  |
| `select button` | 4 | release | `select button`, `select cap down left`, `select cap down right`, `select cap top left` +5 |  |
| `spiral geometry` | 16 | source only | `spiral trigger`, `spiral trigger bool` |  |
| `square` | 9 | release | `square` |  |
| `stand` | 16 | source only | `stand` |  |
| `stick module` | 4 | release | `StickL`, `StickL hole`, `StickR` |  |
| `stick R` | 4 | release | `Stick R hole` |  |
| `subd` | 5 | release | `basemesh GripX olex`, `basemesh_D_style`, `basemesh_X_style`, `case_front.002` +1 |  |
| `subdivision surface` | 8 | release | `basemesh GripR1`, `basemesh GripS`, `basemesh GripV`, `basemesh GripV.002` +1 |  |
| `sw` | 6 | source only | `fix`, `flex` |  |
| `test` | 24 | source only | `tests` |  |
| `top case supports` | 32 | source only | `top case suppprts` |  |
| `top module` | 5 | release | `StickL`, `StickR` |  |
| `triangle` | 10 | release | `BézierCircle` |  |
| `trigger` | 10 | release | `L2`, `L4`, `R2`, `R2 bool` +2 |  |
| `usb clip variant` | 7 | source only | `FRONT CLIP CUTOUT` |  |

## Geometry / helper (217)

Geometry builders and utilities.

| Group | Nodes | Status | Modifier on | Placed in |
|---|---|---|---|---|
| `-cos*cos*cos` | 8 | release |  | `FischerKoch CY` |
| `-sin*sin*sin` | 8 | release |  | `FischerKoch CY` |
| `.axis_alignment_switch_1` | 20 | release |  | `Array_1` |
| `.curve_UV` | 10 | release |  | `Curve to Tube` |
| `.curve_UV_factor_propagate` | 13 | release |  | `Curve to Tube` |
| `.half_spheres` | 27 | release |  | `Curve to Tube` |
| `.UV_sphere_corrected` | 20 | release |  | `.half_spheres` |
| `abxy` | 36 | release |  | `abxy button` |
| `action` | 13 | release |  | `dpad stick` |
| `align pin` | 70 | release |  | `align pins`, `middle plate` |
| `align pins` | 13 | release |  | `shell structure` |
| `Array_1` | 356 | release |  | `rocker` |
| `ball` | 19 | release |  | `dpad stick` |
| `ball support` | 38 | release |  | `dpad stick` |
| `base shape` | 23 | release |  | `button and caps` |
| `basemesh SDF variant` | 5 | source only |  | `top case supports` |
| `basemesh to sdf` | 4 | release |  | `indent`, `pattern field` |
| `basemesh top face position` | 5 | release |  | `button base`, `cap`, `capacitive plate geometry`, `caps` +12 |
| `battery appendix` | 24 | release |  | `battery bool` |
| `battery bool` | 33 | release |  | `battery bool and cover`, `coVer base` |
| `battery bool and cover` | 53 | release |  | `cover`, `plate bools` |
| `battery face` | 23 | release |  | `hollow.001`, `shell structure` |
| `bevel-extrude` | 42 | release |  | `button and caps` |
| `bool tweaks` | 20 | release |  | `button` |
| `bottom bools` | 48 | release |  | `bools.001`, `case base` |
| `button` | 29 | release |  | `button and caps`, `button.001` |
| `button and caps` | 106 | release |  | `abxy`, `dpad`, `home`, `select` |
| `button base` | 38 | release |  | `button` |
| `button logo base` | 24 | release |  | `logo` |
| `button shafts sdf` | 86 | release |  | `hollow.001`, `shell structure` |
| `button.001` | 5 | release |  | `dpad` |
| `buttons cutouts` | 12 | release |  | `top bools` |
| `cable holder parameters` | 3 | release |  | `cable holder usb bool`, `cable hole` |
| `cable holder usb bool` | 9 | release |  | `cable hole` |
| `cancel out transform` | 6 | release |  | `R1`, `R1L1 bool`, `R1L1 xgrip position`, `bools.001` +4 |
| `cap` | 26 | release |  | `dpad stick` |
| `cap plate cutouts` | 9 | release |  | `top bools` |
| `capacitive plate geometry` | 21 | release |  | `plate base` |
| `caps` | 100 | release |  | `button and caps` |
| `capture all` | 3 | release |  | `battery bool`, `solidify`, `texture` |
| `case base` | 24 | release |  | `case` |
| `circlularize` | 14 | release |  | `convex top` |
| `coer Y tolerance` | 9 | release |  | `battery bool and cover`, `coVer base` |
| `common bools` | 12 | release |  | `bools.001`, `case base` |
| `common R1L1` | 3 | source only |  | `R1` |
| `convex top` | 69 | release |  | `texture` |
| `cos(2*n)*sin*cos` | 8 | release |  | `FischerKoch S` |
| `coVer base` | 51 | release |  | `bottom bools` |
| `cover base plate` | 37 | release |  | `battery bool and cover`, `coVer base` |
| `cover lips` | 113 | release |  | `battery bool and cover`, `coVer base` |
| `cubic` | 23 | release |  | `pattern field` |
| `cubic hollow parameters` | 2 | release |  | `global outputs` |
| `curve offset xy` | 8 | release |  | `plate` |
| `Curve to Tube` | 617 | release |  | `top bools` |
| `curved base plate` | 61 | release |  | `cover base plate` |
| `cut at height` | 28 | source only |  | `top case supports` |
| `cut basemesh` | 27 | release |  | `bools.001`, `case base`, `cut basemesh and offset curve`, `half basemesh variants` +2 |
| `cut basemesh and offset curve` | 18 | release |  | `top bools` |
| `cutoff` | 37 | release |  | `button and caps` |
| `cylinder` | 7 | release |  | `dpad stick` |
| `deault lever R1L1` | 5 | release |  | `GripR1  parameters` |
| `delete half` | 9 | **unreachable** |  |  |
| `delete half icosahedron` | 16 | release |  | `texture` |
| `direction flow` | 7 | release |  | `offset edge even` |
| `dpad` | 64 | release |  | `dpad button` |
| `dpad base` | 69 | release |  | `dpad` |
| `euclidean distance ` | 5 | release |  | `cubic` |
| `extra operations` | 8 | release |  | `extra` |
| `extrude and offset` | 43 | release |  | `bool`, `bool tweaks`, `caps`, `dpad stick` +4 |
| `extrude insert` | 48 | release |  | `plate` |
| `extrude texture` | 5 | release |  | `texture` |
| `extrude texture.001` | 10 | release |  | `top` |
| `fill cap` | 8 | release |  | `pcb` |
| `fill limit` | 9 | release |  | `indent` |
| `final cut` | 20 | release |  | `trigger base` |
| `FischerKoch CY` | 12 | release |  | `pattern field` |
| `FischerKoch S` | 8 | release |  | `pattern field` |
| `flat` | 6 | release |  | `texture` |
| `flex switch` | 9 | source only |  | `L1`, `R1` |
| `flex tol` | 6 | release |  | `lever R1L1 base` |
| `flipX` | 14 | release |  | `R1 base geometry`, `lever R1L1`, `lever R1L1 bool` |
| `gripx R1L1 parameters` | 4 | source only |  | `top case supports` |
| `gyroid` | 8 | release |  | `pattern field` |
| `half basemesh variants` | 4 | release |  | `indent.001`, `shell structure` |
| `hollow` | 9 | release |  | `hollow.001`, `shell structure` |
| `hollow.001` | 30 | source only |  | `bools.001` |
| `home` | 16 | release |  | `home button` |
| `indent` | 18 | release |  | `case base` |
| `indent.001` | 6 | source only |  | `bools.001` |
| `inner rim` | 30 | release |  | `hollow.001`, `shell structure` |
| `inner supports` | 56 | release |  | `inner rim` |
| `insert rim` | 9 | release |  | `lattice` |
| `invert` | 3 | release |  | `abxy`, `bevel-extrude`, `bool tweaks`, `button and caps` +22 |
| `Is Edge Boundary` | 4 | release |  | `flat`, `lever R1L1 base`, `texture`, `top` |
| `Is Edge Boundary.001` | 4 | release |  | `offset face reddit` |
| `lattice` | 25 | release |  | `hollow.001`, `shell structure` |
| `lever R1L1 base` | 349 | release |  | `button shafts sdf`, `lever R1L1`, `lever R1L1 bool`, `plate bools` +1 |
| `marks` | 76 | release |  | `button and caps`, `lever R1L1`, `trigger base` |
| `mesh to curve to mesh` | 4 | **unreachable** |  |  |
| `mesh to grid topology` | 20 | release |  | `indent`, `lattice` |
| `mirror at Z` | 8 | release |  | `texture` |
| `morphed square` | 15 | release |  | `stick` |
| `move to stick top` | 5 | release |  | `texture` |
| `nail cut` | 6 | release |  | `battery bool and cover`, `coVer base` |
| `neighboor direction` | 14 | release |  | `extrude and offset`, `offset edge gemini`, `offset selected`, `offset selected axis` +1 |
| `neighboor direction.001` | 14 | release |  | `offset edge even` |
| `neighboor vert vector` | 16 | release |  | `offset edge even` |
| `nut pocket` | 43 | release |  | `screw` |
| `offset basemesh and slice` | 22 | release |  | `align pins`, `inner rim`, `middle plate`, `plate` |
| `offset curve` | 31 | release |  | `button and caps`, `cut basemesh and offset curve`, `lever R1L1 base`, `plate` |
| `offset edge even` | 42 | release |  | `pcb` |
| `offset edge gemini` | 36 | release |  | `thumbstick shaft` |
| `offset even reddit old` | 25 | release |  | `pcb`, `test` |
| `offset face reddit` | 40 | release |  | `top face` |
| `offset position` | 4 | release |  | `abxy`, `bool tweaks`, `caps`, `dpad base` +2 |
| `offset selected` | 40 | release |  | `lever R1L1 base` |
| `offset selected axis` | 44 | release |  | `trigger base geo` |
| `only x` | 4 | release |  | `cover lips` |
| `only y` | 4 | release |  | `coer Y tolerance` |
| `parameters` | 14 | **unreachable** |  | `Tool` |
| `part to grid` | 4 | release |  | `battery face`, `button shafts sdf`, `hollow`, `hollow.001` +4 |
| `pattern field` | 40 | release |  | `indent` |
| `pcb` | 36 | release |  | `GripX pcb` |
| `pcb grab support` | 64 | release |  | `plate bools` |
| `pcb pocket` | 12 | release |  | `middle plate`, `shell structure` |
| `pin base` | 66 | release |  | `pins` |
| `pins cutouts` | 4 | release |  | `common bools` |
| `place on curve` | 12 | release |  | `align pins`, `middle plate` |
| `plate` | 48 | release |  | `hollow.001`, `middle plate`, `shell structure` |
| `plate base` | 99 | release |  | `capacitive plate` |
| `plate bools` | 61 | release |  | `middle plate` |
| `plate from curve` | 19 | release |  | `inner rim` |
| `Position offset` | 4 | release |  | `plate bools` |
| `primitive` | 8 | release |  | `pattern field` |
| `protect mesh` | 6 | release |  | `protect parts` |
| `protect parts` | 23 | release |  | `indent`, `lattice` |
| `R1 base geometry` | 123 | release |  | `L1`, `R1`, `R1L1 bool` |
| `R1 stem` | 10 | release |  | `lever R1L1 base` |
| `R1L1 cutouts` | 13 | release |  | `top bools` |
| `R1L1 parameters` | 3 | source only |  | `tol ofs` |
| `R1L1 xgrip position` | 5 | release |  | `lever R1L1 base` |
| `R4 wire cutout` | 7 | release |  | `top bools` |
| `R4R2 parameters` | 3 | release |  | `topoff` |
| `Randomize Transforms_1` | 38 | release |  | `Array_1` |
| `ribs` | 14 | release |  | `hollow.001`, `shell structure` |
| `rocker` | 18 | release |  | `dpad stick` |
| `rocker support` | 18 | release |  | `dpad stick` |
| `scale XY` | 7 | release |  | `square morph` |
| `schwarz diamond` | 27 | release |  | `pattern field` |
| `screw` | 151 | release |  | `screws` |
| `screw cutouts` | 6 | release |  | `top bools` |
| `sdf inflate` | 3 | release |  | `protect mesh` |
| `sdf shrink` | 3 | release |  | `indent` |
| `sdf union` | 3 | release |  | `fill limit`, `indent`, `protect mesh` |
| `select` | 15 | release |  | `select button` |
| `select all` | 3 | release |  | `top` |
| `select at` | 9 | release |  | `align pin`, `ball support`, `battery bool`, `button and caps` +16 |
| `selection` | 11 | release |  | `convex top` |
| `separate cover basic` | 3 | release |  | `battery bool`, `battery bool and cover`, `coVer base` |
| `shade flat` | 3 | source only |  | `spiral geometry` |
| `shear` | 9 | source only |  | `L1`, `R1` |
| `shell structure` | 53 | release |  | `case base` |
| `shield` | 34 | release |  | `stick` |
| `sin(2n)*(sin+cos)` | 8 | release |  | `FischerKoch CY` |
| `sin*cos` | 5 | release |  | `gyroid` |
| `smd cutouts` | 4 | release |  | `top bools` |
| `Smooth by Angle` | 14 | **unreachable** |  |  |
| `Smooth Geometry` | 5 | release |  | `lattice`, `offset basemesh and slice` |
| `solidify` | 22 | release |  | `texture` |
| `spiral base` | 90 | source only |  | `spiral geometry` |
| `spiral trigger` | 2 | source only |  | `spiral base` |
| `split parameters` | 1 | release |  | `trigger cap` |
| `square morph` | 33 | release |  | `morphed square` |
| `stem` | 63 | release |  | `plate base` |
| `stem base` | 52 | release |  | `dpad stick` |
| `stick` | 54 | release |  | `stick R`, `stick module` |
| `stick action` | 12 | release |  | `extra operations` |
| `stick base` | 96 | release |  | `stick` |
| `stick hole` | 31 | release |  | `stick` |
| `Stick hole subdivision` | 2 | release |  | `GripR1 stick L parameters`, `GripR1 stick R parameters`, `GripX stick L parameters` |
| `Stick L hole subdivision` | 2 | release |  | `GripR1 stick L parameters` |
| `stick top Z` | 5 | release |  | `move to stick top`, `texture` |
| `stick_math` | 15 | release |  | `stick base` |
| `sticks cutouts` | 27 | release |  | `top bools` |
| `sticks xy correction` | 1 | release |  | `GripX stick L parameters` |
| `stopper offset` | 43 | release |  | `button base` |
| `swap rotation` | 7 | release |  | `texture` |
| `swich tolerance` | 5 | release |  | `trigger cap` |
| `Switch` | 3 | source only |  | `clip`, `sw` |
| `tal` | 7 | release |  | `trigger base`, `trigger cap` |
| `tangent math` | 8 | release |  | `stick base` |
| `texture` | 169 | release |  | `top module` |
| `thumbstick shaft` | 25 | release |  | `stick` |
| `tip` | 15 | **unreachable** |  | `vector vis` |
| `to circle` | 7 | release |  | `texture` |
| `tol ofs` | 6 | source only |  | `L1`, `R1` |
| `tolerance switch` | 4 | release |  | `trigger base geo` |
| `Tool` | 3 | **unreachable** |  |  |
| `Tool.001` | 3 | **unreachable** |  |  |
| `top` | 92 | release |  | `texture` |
| `top bools` | 28 | release |  | `bools.001`, `case base` |
| `top face` | 80 | release |  | `hollow`, `hollow.001`, `shell structure` |
| `top wire cutouts` | 6 | release |  | `top bools` |
| `topoff` | 19 | release |  | `trigger cap` |
| `trigger align` | 29 | release |  | `trigger base` |
| `trigger base` | 91 | release |  | `R4`, `trigger` |
| `trigger base geo` | 49 | release |  | `trigger base` |
| `trigger cap` | 74 | release |  | `trigger base` |
| `trigger cut` | 57 | release |  | `trigger base` |
| `vector vis` | 29 | **unreachable** |  | `visualize vector at` |
| `visualize vector at` | 21 | **unreachable** |  |  |
| `voronoi` | 6 | release |  | `pattern field` |
| `wheel cutouts` | 4 | release |  | `top bools` |
| `x` | 2 | release |  | `pin base` |
| `XY corr` | 6 | release |  | `extra operations` |
| `XY correction` | 4 | release |  | `stick` |
| `xy tol z comp` | 4 | release |  | `extrude insert` |

