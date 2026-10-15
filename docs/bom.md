# Bill of materials (draft)

> **Draft, not checked on a finished build.** This list collects what Grip needs besides the printed parts, so you can order everything before you print. Every row says where it comes from: a Grip file, a page from Input Labs, or "guess". "To confirm" means nobody has checked it yet. If you build one, please correct this page or say what you used in a [fit report](https://github.com/oleroma/Grip/issues/new?template=fit-report.yml).

Grip is a case for the **Alpakka**, the open game controller by [Input Labs](https://inputlabs.io/alpakka/components). The electronics are the Alpakka's: Grip replaces its printed case, buttons, sticks, triggers and bumpers. So most of this list is the Alpakka hardware, and the rest is the screws, nuts and filament Grip itself needs.

The printed parts and how many of each are in the [print list](../orca_slicer/README.md). How it all goes together is in the [assembly guide](assembly-guide.md).

## Electronics

These come from the Alpakka. Input Labs sells them as a set and as a complete DIY kit, and the board can be ordered from its open design files ([components](https://inputlabs.io/alpakka/components), [order the board](https://inputlabs.io/alpakka/manual/diy_pcb), [solder the board](https://inputlabs.io/alpakka/manual/diy_solder)).

| Part | Qty | What it does in Grip | Source |
| --- | --- | --- | --- |
| Alpakka PCB | 1 | The main board. It drops into the slot in the case bottom (on hollow cases, into the middle plate). Which board revision the slot is drawn for: to confirm. | repo description "procedural Alpakka controller case"; [PCB and cable](blender/customize/parts/pcb-and-cable.md); [Alpakka components](https://inputlabs.io/alpakka/components) |
| Marmota core module | 1 | The Alpakka's core module that connects to the main board. Grip's PCB slot includes a cutout named `marmota cutout`, so the case probably leaves room for it. | [Alpakka components](https://inputlabs.io/alpakka/components); [Case pipeline](blender/develop/03-case-pipeline.md#bottom-half-bottom-bools) |
| Front buttons, Alps SKPMAME010 | 13 | The switches under the button shafts: 4 ABXY, 4 D-pad, 4 Select and Home. They are SMD switches on the front of the board, so they are probably soldered by the board maker. Grip's `SMD height` decides how long the shafts are, so it has to match these switches. | [Alpakka specs](https://inputlabs.io/alpakka/manual/specs); [Buttons and caps](blender/customize/parts/buttons-and-caps.md) |
| Shoulder buttons, Alps SKHHLNA010 | 2 | The switches the L1 and R1 bumpers press. | [Alpakka specs](https://inputlabs.io/alpakka/manual/specs); [Bumpers](blender/customize/parts/bumpers.md) |
| Trigger buttons, Alps SKQGAFE010 | 4 | On the back of the board, pressed by the L2 and R2 triggers and the L4 and R4 back paddles. | [Alpakka solder guide](https://inputlabs.io/alpakka/manual/diy_solder); [Triggers](blender/customize/parts/triggers.md) |
| Thumbsticks, Alps RKJXV122400R | 2 | The joystick modules. The printed sticks push onto their shafts; `shaft tolerance` and `base size` set that fit. | [Alpakka specs](https://inputlabs.io/alpakka/manual/specs); [Sticks](blender/customize/parts/sticks.md) |
| Rotary encoder, Alps EC10E1220503 | 1 | Probably what the scroll wheel turns: Grip's wheel has the same three pieces as the Alpakka's (wheel, core, holder). | [Alpakka specs](https://inputlabs.io/alpakka/manual/specs); [Scroll wheel](blender/customize/parts/scroll-wheel.md) |
| Battery connector, JST PH 2-pin (XUNPU WAFER-PH2-0-2PWZ) | 1 | The battery plug on the board. The case has fixed clearances for it (`JST-2P (B)`, `jst2p pass`). | [Alpakka components](https://inputlabs.io/alpakka/components); [File structure](blender/develop/01-file-structure.md) |

## Battery

| Part | Qty | What it does in Grip | Source |
| --- | --- | --- | --- |
| LiPo cell 503562, 1200 mAh, 3.7 V, JST PH 2-pin plug | 1 | Optional on the Alpakka, needed for wireless play. Grip's battery compartment and cover are made for a cell of about 63 × 35 × 5 mm (GripV a little thinner than GripX), which is probably this cell. For another battery, change `battery length`, `battery width` and `battery height`. | [Alpakka specs](https://inputlabs.io/alpakka/manual/specs); [tracking.json](../blender/tracking.json) `advanced cover parameters`; [Battery cover](blender/customize/parts/battery-cover.md) |

## Screws and nuts

Four screws hold the case together, two at the front and two at the back. The [printing guide](print-guide.md#solid-case) names M2.5 DIN 912 socket-head screws with nuts. Grip does not need the Alpakka's trigger bolts: its triggers have no screws.

| Part | Qty | What it does in Grip | Source |
| --- | --- | --- | --- |
| M2.5 DIN 912 socket-head screw, front | 2 | The front pair. Probably 12 mm long (the file's `screw length` is just over 12 on GripV and 12 on GripX; the Alpakka uses 12 mm screws at the top). Length to confirm. | [Screws](blender/customize/parts/screws.md); [tracking.json](../blender/tracking.json) `screw parameters (FRONT)` › `screw length`; [Alpakka assembly](https://inputlabs.io/alpakka/manual/diy_assembly) |
| M2.5 DIN 912 socket-head screw, back | 2 | The back pair, at the grips. Probably 20 mm on GripV and 25 mm on GripX (`screw length` just over 20 and 25). Lengths to confirm. | [tracking.json](../blender/tracking.json) `screw parameters.001 (BACK)`, `screw parameters.002 (BACK)` › `screw length` |
| M2.5 hex nut | 4 | Pressed into the pockets in the case top. The pockets fit a standard M2.5 nut (5 mm across flats, 2 mm thick), probably DIN 934 as on the Alpakka. Standard to confirm. | [Printing guide](print-guide.md#solid-case); [tracking.json](../blender/tracking.json) `nut width`, `nut height`; [Alpakka components](https://inputlabs.io/alpakka/components) |

**Hollow case:** the printing guide recommends the screws for now. The exported hollow shells probably have no screw holes yet, because the "Case hollow" export does not turn on `screws hollow` ([known gaps](../orca_slicer/README.md#known-gaps)). Check your print before you buy screws for it.

## Filament

| Part | Qty | What it is for | Source |
| --- | --- | --- | --- |
| PLA | to confirm | Everything except the capacitive part. The fit settings were tuned with PLA. | [Printing guide](print-guide.md); [Fit and tolerances](blender/customize/03-fit-and-tolerances.md) |
| Conductive PLA | small amount, to confirm | Probably needed for the capacitive knob or plate, if you want the touch function: the Alpakka's touch part must be printed in conductive PLA, and Input Labs only got reliable results with Protopasta's. Whether Grip's part works the same way: to confirm. | [Alpakka case printing](https://inputlabs.io/alpakka/manual/diy_case); [Capacitive plate](blender/customize/parts/capacitive.md) |

## Cable and extras

| Part | Qty | What it is for | Source |
| --- | --- | --- | --- |
| USB-C cable | 1 | The board has a USB-C port. The printed cable holder clamps the cable in the USB opening. It is made for one plug size, set on the node `cable size.001` (labelled "pwnage paracord", probably a braided cable). Plug size to confirm; measure yours and see [PCB and cable](blender/customize/parts/pcb-and-cable.md#cable-holder). | [Alpakka specs](https://inputlabs.io/alpakka/manual/specs); [PCB and cable](blender/customize/parts/pcb-and-cable.md) |
| Alpakka wireless dongle | 1, optional | For wireless play. `orca_slicer/dongle_case/` has a printable case that is probably for it. | [Alpakka components](https://inputlabs.io/alpakka/components); guess for the case |

## Tools

| Tool | What it is for | Source |
| --- | --- | --- |
| 2 mm hex key | the M2.5 DIN 912 screws | [Alpakka assembly](https://inputlabs.io/alpakka/manual/diy_assembly) |
| Flush cutters, a deburring tool or a hobby knife, fine sandpaper | removing supports and cleaning sliding surfaces | guess |
| Soldering iron and solder | only if you solder the board yourself | [Alpakka solder guide](https://inputlabs.io/alpakka/manual/diy_solder) |

## Printed, not bought

Some parts that are hardware on other controllers are printed for Grip. They are in the [print list](../orca_slicer/README.md): the two alignment pins (standard case only; hollow shells line up on the middle plate), the cable holder and the optional nut lock for the front nuts.
