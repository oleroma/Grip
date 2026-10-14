"""Write tooltips into Grip.blend.

A tooltip is the description of a node group input. Blender shows it when you
hover the input on a group node or in the modifier panel.

This script covers the global settings and the parameters that decide fit:
tolerances, buttons and caps, triggers, bumpers, sticks, battery cover, pins,
scroll wheel, PCB slot and capacitive plate. The texts follow the guide in
docs/blender/customize. Lines marked "# guess" describe something the file
does not show directly; check them in Blender.

How to run:
1. Open blender/Grip.blend.
2. Text Editor > Open > scripts/apply_tooltips.py > Run Script.
3. Read the report (Window > Toggle System Console on Windows).
4. Unlink the script from the file (the X next to its name in the Text Editor
   header), so it is not saved inside Grip.blend, then save. If the report
   looks wrong, use File > Revert instead of saving.

The script only sets descriptions of the inputs listed below. It changes no
value, default, link or name, so blender/tracking.json does not change.
Numbered copies of a group (for example "basic stick parameters.001") get the
same tooltips. Names are spelled as in the file, typos included; if an input
is renamed, rename its key here too.
"""

import re

import bpy

# True: only report what would change.
DRY_RUN = False

TOLERANCE_LINK = "Comes from the global {} menu through a tolerance set."

TOOLTIPS = {
    "global parameters": {
        "variant": "Controller shape to build: GripV or GripX (GripR1 is legacy). Match it to the scene you are in. The export presets set it themselves.",
        "style": "GripX only: xbox or dualsense case shape. It also picks that style's trigger, bumper and back screw settings.",
        "body type": "Inside of the case: standard (solid), indent (solid with a surface pattern), hollow (thin shell on a middle plate) or lattice (shell made of strips).",
        "subdivision level": "Smoothness of the case surface. Keep it low while editing; the case exports use very high.",
        "voxel resolution": "Detail of the shell of hollow, lattice and hollow top bodies. Higher is smoother but much slower. The case exports use high.",
        "fill type": "Surface pattern of the indent body. Ignored by the other bodies. Do not use manual: it is unfinished and breaks the case.",
        "hollow top": "GripV with a standard body: makes the top half a light shell while the bottom stays solid.",
        "ribs": "Shell bodies: adds stiffening ribs inside the top half.",
        "pillars": "Adds support pillars inside the case bottom. Turn it on if the PCB sits shifted and the sticks look off centre. Not used by the hollow body.",
        "screws": "Solid bodies: cuts the screw holes and nut pockets. Turn it off only if you hold the case together another way.",
        "screws hollow": "Shell bodies: adds solid bosses around the screws so they have material to bite into.",
        "stock bumpers": "Uses fixed, hand-modelled L1/R1 bumpers and openings instead of the generated, adjustable ones.",
        "top wire cutouts": "Cuts wire channels into the case top.",
        "R4 wire cutouts": "Cuts a wire channel into both case halves for the L4/R4 back paddle wiring.",  # guess
        "cable holder": "On: a wider USB opening that takes the printed cable holder, which clamps the cable. Off: a plain USB opening.",
        "horizontal buttons": "Button shaft design. Keep it on: off is an older design with unstable geometry.",
        "button logo": "Engraves the symbols on the ABXY and Home caps.",
        "marks": "Engraves an identification letter on the button shafts and triggers. The bumpers have their own switch.",
        "tolerance": "Fit of the button shafts in the case and of the triggers in their openings: tight, default or loose. Start with default.",
        "press tolerance": "Press travel of the triggers and GripV bumpers before they reach the switch: tight, default or loose.",
        "cap tolerance": "How firmly the caps clip onto the button shafts: tight, default or loose. GripX uses one value for all three.",
    },
    "tolerance set": {
        "tolerance": "Which of the three values is passed on. Linked to a global tolerance menu, so one menu switches every part.",
        "tight": "Value this part uses when the global menu is set to tight.",
        "default": "Value this part uses when the global menu is set to default.",
        "loose": "Value this part uses when the global menu is set to loose.",
    },
    # Buttons and caps
    "curve parameters": {
        "width": "Size of the button. Shaft, cap and case hole grow together.",
        "octagonal fillet": "Switches the outline between two corner styles.",
        "fillet": "How round the corners of the outline are.",
        "fillet subdiv": "Smoothness of the rounded corners. Ignored while horizontal buttons is on.",
        "fillet tolerance": "Extra rounding of the case hole corners only, so a square cap does not catch in its hole.",
    },
    "caps parameters": {
        "button cap travel distance": "How far the button can be pressed. The shaft gets taller and the cap thinner.",
        "caps depth": "Thickness of the cap.",
        "caps additional size": "Makes the cap bigger than the button outline. The case hole grows with it.",
        "cap case tolerance": "Gap between the cap and its hole in the case, per side: 0.2 makes the cap 0.4 mm smaller.",
        "cap bevel": "Rounding of the top edge of the cap.",
        "cap bevel subd": "Smoothness of the rounding of the cap top edge.",
        "cap bevel cutoff": "Cuts the rounding of the cap top off at an angle (radians) for a flatter, crisper top.",
        "bevel cutoff": "Cuts the rounding of the cap top off at an angle (radians) for a flatter, crisper top.",
        "cap base fillet": "Corner rounding of caps that are not round.",
        "cap base fillet subd": "Smoothness of that corner rounding.",
        "custom cap": "Uses a hand-drawn outline (the collection set on the cap object's modifier) instead of the generated one. The D-pad arrows use it.",
        "button cap": "On: two-piece button, shaft plus cap. Off: no cap, the shaft is the whole button.",
        "caps fit Z": "How far the shaft reaches into the cap.",
        "caps fit tolerance": "Side fit of the cap on the shaft. Higher is tighter. " + TOLERANCE_LINK.format("cap tolerance"),
        "caps fit Z tolerance": "Vertical play of the cap on the shaft.",
        "caps hook inset": "How far the snap hook that holds the cap reaches in.",
        "caps hook height": "Height of the snap hook that holds the cap.",
        "caps flex cut": "Depth of the slit that lets the cap clip flex.",  # guess
        "caps offset": "How much wider the cap is than the shaft. Raising it makes the shaft and its case hole thinner; the cap keeps its size.",
    },
    "button parameters": {
        "button tolerance": "How loosely the shaft slides in its case hole: the shaft gets this much narrower, half per side. " + TOLERANCE_LINK.format("tolerance"),
        "SMD height": "Height of the switch on the board that the shaft stands on. Set it for your switches.",
        "button height": "How far the cap stands up. Only the cap gets taller.",
        "button height offset": "Not used.",
        "stopper position": "Height on the shaft of the collar that keeps the shaft from falling out of the case.",
        "stopper height": "Thickness of the collar that keeps the shaft in the case.",
        "stopper offset": "How far the collar sticks out from the shaft.",
        "bottom bevel": "Rounding of the bottom edge of the shaft.",
        "middle bevel": "Rounding of the middle edge of the shaft.",
        "case middle bevel": "Rounding of the edge of the case hole.",
        "case bool bevel": "Rounding of the case hole for the old shaft design (horizontal buttons off).",
        "top bevel": "Not used while the buttons have caps.",
    },
    "capacitive plate parameters": {
        "capacitive": "Touch part between the face buttons: knob, plate around the buttons, or disabled. The case top gets the matching opening.",
        "screw hole": "Hole through the capacitive part.",
        "capacitive plate tolerance": "Plate mode: gap between the plate and the case.",
        "plate button offset": "Plate mode: how far the plate reaches out around the buttons. Its opening in the case grows with it.",
        "capacitive plate stem tolerance": "Not used.",
    },
    # Triggers (L2/R2) and back paddles (L4/R4)
    "trigger parameters": {
        "trigger radius": "Radius of the arc the trigger slides on. Larger is a flatter path, smaller a tighter curve.",
        "button pressed height": "Height of the trigger above its switch.",
        "action": "Shows the trigger pressed, to check its travel. Preview only.",
        "trigger length": "Length of the trigger, measured along the arc.",
        "width": "Width of the trigger bar, left to right. The case opening follows.",
        "height": "Thickness of the trigger bar.",
        "tip angle offset": "Tilt of the finger end.",
        "tip shear": "Lean of the finger end.",
        "top bevel": "Rounding of the finger end.",
        "bevel": "Rounding of the long edges of the bar.",
        "bevel cutoff": "Where the rounding of the long edges is cut off.",
        "bevel subd": "Smoothness of the edge rounding. Keep it at 1: 2 adds mesh defects.",
        "stopper length": "Length of the stop on the bar that limits how far the trigger slides. The case opening has a slot for it.",  # guess
        "stopper height": "Height of the stop on the bar that limits how far the trigger slides.",  # guess
        "subdivision length": "Mesh density along the arc. Smaller is smoother; the shape does not change.",
        "button radius offset": "Moves the trigger away from its switch, outward from the arc centre. The case opening follows.",
        "x offset": "Moves the trigger sideways. The case opening follows.",
        "button rotation": "Turns the trigger about the vertical axis. The case opening follows.",
        "shift z": "Slides the trigger along its arc. The case opening follows.",
        "x tolerance": "Side-to-side play in the case opening. " + TOLERANCE_LINK.format("tolerance"),
        "radius tolerance": "Play across the arc in the case opening. " + TOLERANCE_LINK.format("tolerance"),
        "button press tolerance": "Trims the end that presses the switch, which sets the free play before the click. " + TOLERANCE_LINK.format("press tolerance"),
    },
    # Bumpers (L1/R1)
    "R1L1 lever parameters": {
        "wdith": "Length of the bumper along the case edge.",
        "height": "Height of the bumper.",
        "top bevel": "Rounding of the top edge of the bumper.",
        "overlap": "How far the back of the bumper reaches under the case edge, which holds it in place.",
        "overlap slant": "Slope of the underside that reaches under the case edge.",
        "R1L1 flex": "On: flex design with an extra arm towards the centre (GripV). Off: the bumper pivots on its stem (GripX).",
        "stem radius": "Size of the stem the bumper pivots on. On GripV a separate Value node drives it; change that node.",
        "stem tolerance": "Play of the stem in its seat.",
        "button height": "How far the press face stands out. The bumper gets deeper front to back.",
        "depth": "Depth of the press face.",
        "insert depth": "How deep the bumper reaches into the case.",
        "button inset offset": "How far the press face is set in.",
        "button front shift X": "How far the press face extends along the bumper.",
        "bumper Z tolerance": "Play below the bumper. It also moves the case edge around the bumper slightly.",
        "X tolerance": "Play at the ends of the bumper.",
        "overlap tolerance": "Play between the overlap and the case edge. It also moves the case edge slightly.",
        "button press tol": "Trims the press face, which sets the free play before the click. GripV: linked to the global press tolerance. GripX: set here, per style.",
        "X": "Moves both bumpers and their openings sideways.",
        "Y": "Moves only the back of the bumper. The front stays at the case edge, so the bumper gets shorter or longer.",
        "Z": "Moves both bumpers and their openings up or down.",
        "curved R1L1": "Uses the curved outline drawn per variant instead of the straight one. Not available for GripX xbox yet (its curve is empty).",
        "curved button slant": "Curved bumpers only: slant of the press face.",  # guess
        "curved button depth tolerance": "Curved bumpers only: depth play of the press face.",  # guess
        "curved button bevel": "Curved bumpers only: rounding of the press face.",  # guess
        "curved button thickness": "Not used.",
        "bevel inner": "Not used.",
        "bevel inner sbdiv": "Not used.",
    },
    # Sticks
    "basic stick parameters": {
        "stick heght": "Height of the stick above the top surface of the case.",
        "stick top radius": "Size of the thumb surface.",
        "base size": "Size of the part that grips the joystick module's shaft.",
        "base height": "Height of the part that grips the joystick module's shaft.",
        "shaft tolerance": "Fit on the joystick module's shaft. Higher is looser.",
        "shaft Z offset": "How deep the module's shaft goes into the stick.",
        "top bevel": "Rounding of the top edge of the stick.",
        "middle bevel": "Rounding of the middle of the stick.",
        "range degrees": "Tilt the stick must reach. The neck is shaped so it touches the case hole exactly at this angle.",
        "contact top offset": "Shape of the rim that touches the case hole at full tilt: top edge.",
        "contact bottom offset": "Shape of the rim that touches the case hole at full tilt: bottom edge.",
        "topmost offset": "Shape of the rim that touches the case hole at full tilt: topmost point.",
        "action": "Shows the stick tilted, to check clearance. Preview only; turn it off before exporting.",
        "action rotation": "Direction of the preview tilt.",  # guess
    },
    "advanced stick parameters": {
        "contact angle": "Angle of the surface where stick and case hole meet at full tilt.",
        "hole radius": "Size of the stick hole in the case top. The neck of the stick follows.",
        "hole bevel": "Rounding of the edge of the stick hole.",
        "case cutout thickness ": "GripX: wall around the stick opening. Does nothing on GripV, which uses fixed cutouts.",
        "stick  XY correction": "On: shifts the stick off the module centre by X correction and Y correction.",
        "X correction": "Sideways shift of the stick when XY correction is on.",
        "Y correction": "Front-to-back shift of the stick when XY correction is on.",
        "swap stick rotation": "Turns the mesh layout of the stick.",
        "stick subdivision": "Smoothness of the stick. 8 gives an eight-sided stick.",
        "stick hole subdivision": "Smoothness of the stick hole.",
        "shaft X correction": "Not used.",
        "shaft Y correction": "Not used.",
    },
    "shield parameters": {
        "sheild": "Skirt at the bottom of the stick that keeps the case hole covered at every tilt.",
        "sheild height": "How far down the skirt reaches.",
        "shield cutoff height": "Where the skirt is cut off.",
        "sheild radius offset": "Radius of the skirt.",
        "FDM shield thickness": "Extra skirt thickness for FDM printing.",
        "FDM Z correction": "Height correction of the skirt for FDM printing.",
    },
    "stick top parameters": {
        "top shape": "Circle or square thumb surface.",
        "top curvature": "Concave, convex or flat thumb surface.",
        "texture type": "Grip pattern: grid or icosahedron. Only the matching texture settings act.",
        "extrude texture": "Raises the texture instead of cutting it in.",
        "swap top rotation": "Turns the outline and texture of the top.",
        "square top subd": "Square tops: smoothness of the corners.",
        "square morph": "Square tops: how much the square bulges.",
    },
    # Battery cover
    "basic cover parameters": {
        "x tolerance": "Gap around the battery cover in its opening, along X.",
        "y tolerance": "Gap around the battery cover in its opening, along Y.",
    },
    "advanced cover parameters": {
        "battery length": "Length of the battery the compartment is made for. Set it for your battery.",
        "battery width": "Width of the battery the compartment is made for. Set it for your battery.",
        "battery height": "Height of the battery the compartment is made for. Set it for your battery.",
        "shift Y": "Moves the battery compartment front to back.",
        "battery wire cut": "Slot in the cover for the battery wire.",
        "appendix": "Adds an extension to the battery compartment, sized by the appendix inputs.",
        "appendix length": "Appendix only: length of the compartment extension.",
        "appendix height": "Appendix only: height of the compartment extension.",
        "appendix gap": "Appendix only: gap of the compartment extension.",
        "cover base thickness": "Thickness of the cover plate.",
        "cover base overlap": "How far the cover reaches over the edge of the opening.",
        "curved cover": "The cover follows the curved underside of the case instead of being flat.",
        "flex width": "Width of the flexible tongues the clip lips sit on.",
        "lip height": "Height of the clip lips.",
        "lip width": "Width of the clip lips.",
        "lip hook height": "Height of the hook that snaps into the case.",
        "compression offset": "Makes the cover thinner, which sets how hard it presses on the battery.",
        "test parameter": "Not used.",
    },
    # Alignment pins
    "pins params": {
        "pin width": "Width of the pin hole. The pin is this size minus xy tol.",
        "pin height": "Height of the pin hole. The pin is this size minus z tol.",
        "xy tol": "Side play: the pin is this much narrower than its hole, half per side.",
        "z tol": "Vertical play: the pin is this much shorter than its hole, half at each end.",
        "bevel": "Rounding of the pin edges.",
    },
    # Scroll wheel
    "scroll parameters": {
        "scroll radius offset": "Wheel diameter. The slot in the case grows with it.",
        "scroll width offset": "Wheel width. The slot in the case grows with it.",
        "scroll wheel tolerance": "Side play of the wheel in its slot: the wheel gets this much narrower, half per side.",
        "scroll wheel shift X": "Moves one face of the wheel and its slot, so the wheel gets wider towards one side.",
    },
    # PCB slot
    "pcb cutout parameters": {
        "PCB thickness": "Depth of the slot for the board itself.",
        "PCB below height": "Depth of the pocket under the board for its components.",
        "PCB support edge": "Width of the ledge the board rests on.",
        "PCB tolerance XY": "Gap around the board. It enlarges the slot, so the case bottom needs a reprint.",
    },
}


def matching_groups(name):
    """The group called name and its numbered copies (name.001, name.002, ...)."""
    pattern = re.compile(re.escape(name) + r"(\.\d{3})?")
    return [
        group for group in bpy.data.node_groups
        if group.bl_idname == 'GeometryNodeTree' and pattern.fullmatch(group.name)
    ]


def group_inputs(group):
    inputs = {}
    for item in group.interface.items_tree:
        if item.item_type == 'SOCKET' and item.in_out == 'INPUT':
            inputs.setdefault(item.name, []).append(item)
    return inputs


def main():
    changed = unchanged = 0
    replaced, missing_groups, missing_inputs, linked, uncovered = [], [], [], [], []

    for group_name, tooltips in TOOLTIPS.items():
        groups = matching_groups(group_name)
        if not groups:
            missing_groups.append(group_name)
            continue
        for group in groups:
            if group.library:
                linked.append(group.name)
                continue
            inputs = group_inputs(group)
            for input_name, text in tooltips.items():
                if input_name not in inputs:
                    missing_inputs.append(f"{group.name} > {input_name!r}")
                    continue
                for item in inputs[input_name]:
                    if item.description == text:
                        unchanged += 1
                        continue
                    if item.description:
                        replaced.append(f"{group.name} > {input_name!r}: {item.description!r}")
                    if not DRY_RUN:
                        item.description = text
                    changed += 1
            uncovered += [f"{group.name} > {name!r}" for name in inputs if name not in tooltips]

    print("\n=== apply_tooltips" + (" (dry run, nothing changed)" if DRY_RUN else "") + " ===")
    print(f"{'Would set' if DRY_RUN else 'Set'} {changed} tooltips, {unchanged} already up to date.")
    for title, lines in (
        ("Replaced an existing tooltip", replaced),
        ("Group not found", missing_groups),
        ("Input not found (renamed?)", missing_inputs),
        ("Linked from a library, skipped", linked),
        ("Inputs of these groups that still have no tooltip", uncovered),
    ):
        if lines:
            print(f"\n{title} ({len(lines)}):")
            for line in lines:
                print("  " + line)


if __name__ == "__main__":
    main()
