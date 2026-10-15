# Customize and export

This guide is for changing parts of the controller and printing them. Each page explains what a setting changes in the design and why you would change it. Current values are in `blender/tracking.json`, not here.

## The workflow in four steps

1. **Open the file and pick the controller.** Go to the GripV or GripX scene and make sure the variant matches it (the Grip tab does that for you), and for GripX pick the style. See [Getting started](01-getting-started.md).
2. **Find the part's settings** and change them: the most used ones are in the [Grip tab](01-getting-started.md#the-grip-tab) of the 3D Viewport sidebar, all of them in the controls panel. Each part has its own page below.
3. **Check the fit.** Parts and their openings in the case are generated together, so changing a part usually changes the case too. Look at both. [Fit and tolerances](03-fit-and-tolerances.md) explains which values decide how tight things are.
4. **Export** with the `combi_export` presets. See [Exporting](05-exporting.md).

## Pages

| Page | What it covers |
|---|---|
| [1. Getting started](01-getting-started.md) | setup, scenes, choosing the variant, the Grip tab, the controls panel, keeping Blender fast |
| [2. Global settings](02-global-settings.md) | the switches that apply to the whole controller |
| [3. Fit and tolerances](03-fit-and-tolerances.md) | how parts fit each other and the case, and how to tune that for your printer |
| [4. Case and body types](04-case.md) | the case shape, solid versus shell versus patterned cases, the middle plate |
| [5. Exporting](05-exporting.md) | the export presets, the files they write, known export problems |

### Parts

| Part | Page |
|---|---|
| face buttons (ABXY), D-pad, Select, Home and their caps | [Buttons and caps](parts/buttons-and-caps.md) |
| touch knob or plate between the face buttons | [Capacitive plate](parts/capacitive.md) |
| thumbsticks | [Sticks](parts/sticks.md) |
| rocker D-pad (alternative to the four D-pad caps) | [D-pad stick](parts/dpad-stick.md) |
| L2/R2 triggers and L4/R4 back paddles | [Triggers](parts/triggers.md) |
| L1/R1 bumpers | [Bumpers](parts/bumpers.md) |
| battery compartment and cover | [Battery cover](parts/battery-cover.md) |
| screws, nut lock, GripX reinforcers | [Screws](parts/screws.md) |
| alignment pins between the case halves | [Pins](parts/pins.md) |
| scroll wheel | [Scroll wheel](parts/scroll-wheel.md) |
| PCB slot, USB opening, cable holder | [PCB and cable](parts/pcb-and-cable.md) |
| letters on parts, symbols on caps | [Marks and logos](parts/marks-and-logos.md) |

If you want to know how a part is built inside the nodes, the [contributor guide](../develop/README.md) has a section per part.
