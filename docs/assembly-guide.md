# Assembly guide (draft)

> **Draft, not checked step by step on a build.** The order and the checks below come from how the parts are designed in `Grip.blend`, the [printing guide](print-guide.md) and the development notes. Steps or details marked *unverified* are inferred and still need someone to try them. Photos and a video guide are still to come. If you assemble one, please send a [fit report](https://github.com/oleroma/Grip/issues/new?template=fit-report.yml) and tell us what was wrong here.

This guide is for the solid (standard) case of GripV and GripX. Notes for the hollow GripV case are [at the end](#hollow-version).

## Before you start

- **Printed parts:** everything on the [print list](../orca_slicer/README.md) for your shape, from the `default` tolerance folders.
- **Hardware:** the Alpakka board with its switches and joystick modules, a battery, four M2.5 DIN 912 screws and four M2.5 nuts, a 2 mm hex key. See the [bill of materials](bom.md).

### When a part is tight or loose

Most fits come in three versions, `tight`, `default` and `loose`, in separate folders. If a part does not fit, reprint **only that part** from the neighbouring folder; the case stays, because these settings change the part and not its opening. The table in [Tolerances](../orca_slicer/README.md#start-with-default-reprint-only-what-does-not-fit) says which folder to use for each problem.

Some fits have no folders (caps in the case, sticks on the joystick, the battery cover, the pins, the board in its slot). For those, change the value in `Grip.blend` and export the part again: [Fit and tolerances](blender/customize/03-fit-and-tolerances.md) lists which value decides which fit.

On GripX some neighbouring folders hold the same file for now (the `cap_*` folders, the trigger folders `default/` and `loose/`, the bumper `pres_*` folders), so reprinting from them changes nothing.

## 1. Clean the prints

- Remove all supports and brims. The PCB slot ledge, the trigger openings in the case bottom and the button holes in the case top need to be clean and smooth.
- The PCB slot supports should come off in one piece if you printed them with a solid interface ([printing guide](print-guide.md#pcb-slot)). Check that the ledge around the slot is flat and complete.
- On the case top, look for leftover support above R1 and L1 (the printing guide recommends tree supports there).
- Remove stringing, and any elephant's foot on parts that slide (button shafts, triggers, bumpers).

**Check:** nothing sticks out into a hole or opening. Do not sand a part to make it fit before you have tried the next tolerance folder.

## 2. Test-fit the button shafts in the case top

Each button is a shaft and a cap. With the case top upside down, slide each shaft into its hole from the inside. The collar (stopper) on the shaft keeps it from going through.

- Every button uses the same shaft, `buttons/default/button.stl`: all button holes are the same for now.

**Check:** each shaft slides in and out freely without catching, and does not wobble.

| If | Then |
| --- | --- |
| a shaft sticks | print it from `buttons/loose/` (and its caps from `loose/` too) |
| a shaft wobbles | print it from `buttons/tight/` (and its caps from `tight/` too) |

## 3. Clip on the caps

Press each cap onto its shaft from the outside of the case, holding the shaft from the inside. Once the caps are on, they probably keep the shafts in the case (*unverified*).

- Face buttons: `triangle` top, `circle` right, `cross` bottom, `square` left.
- D-pad: four `dpad.stl` caps, each turned to its side. Select: four `select.stl`. Home: one `home.stl`.
- If your top takes the rocker D-pad (`case_top_dpad_stick_…`), it replaces the D-pad shafts and caps. The order for its six pieces is not written up yet (*unverified*); see [D-pad stick](blender/customize/parts/dpad-stick.md) for what each piece does.
- The capacitive knob or plate goes in the middle of the face buttons. The plate surrounds the face buttons, so it probably has to go on before their caps (*unverified*).

**Check:** each cap snaps on and stays on when you pull lightly, the button presses down and comes back, and the cap does not rub on the edge of its hole.

| If | Then |
| --- | --- |
| a cap falls off | print it from `cap_tight/`, in the same folder as its shaft |
| a cap does not go on, or cracks | print it from `cap_loose/` |
| a cap rubs on the case | no folder for this: raise `cap case tolerance` ([Buttons and caps](blender/customize/parts/buttons-and-caps.md)) |

Caps belong to their shaft: a cap from `buttons/loose/` is made for the shaft from `buttons/loose/`.

## 4. Put the sticks on the joystick modules

Push each stick straight onto its joystick module's shaft until it is fully seated. Support the board under the module while you press, so the force does not go into the solder joints (*unverified* advice).

- GripV: both stick holes are the same, so any two sticks work.
- GripX: the left and right holes differ; use one stick from `StickL/` and one from `StickR/`.

**Check:** the stick sits firmly without wobble. Once the case is closed (step 10), it should tilt evenly in every direction until its neck meets the edge of the hole, and the skirt should keep the hole covered.

If a stick is loose or will not go on, there is no folder for it: change `shaft tolerance` ([Sticks](blender/customize/parts/sticks.md)). A GripV stick is shaped to meet the case at the tilt in its file name (`stick_14_deg.stl` stops at 14°); if it stops too early or too late for you, print another range.

## 5. Fit the triggers into the case bottom

L2, R2, L4 and R4 have no hinge and no screw. Each one is a curved bar that slides along an arc in a matching curved opening in the case bottom. Slide each one into its opening (probably from the inside, before the board goes in, *unverified*). L and R are mirror parts; check that each is on its own side.

**Check:** the trigger slides along its whole path without rubbing or catching, and does not rattle side to side.

| If | Then |
| --- | --- |
| a trigger rubs or sticks | print it from `triggers/loose/` |
| a trigger rattles | print it from `triggers/tight/` |

Press travel is checked in step 7, once the board is in.

## 6. Place the bumpers

L1 and R1 sit in the openings at the top edge of the case. Each has a round stem: the GripX bumpers pivot on it, while the GripV bumpers have an extra arm towards the centre that probably flexes instead ([Bumpers](blender/customize/parts/bumpers.md)). The back of each bumper reaches under the edge of the case top, which holds it once the case is closed. Set them in place in the case bottom (*unverified* order).

- GripV: `bumpers/press_default/`. GripX: `<style>/bumpers/pres_default/`.

**Check:** the bumper moves freely on its stem and does not catch on the case edge. Press travel is checked in step 7 and again after closing.

## 7. Put the board into its slot

Lower the board into the slot in the case bottom. It rests on a ledge around its edge. If you use the cable holder, the USB cable and the holder go into the USB opening now (probably, *unverified*).

The scroll wheel is three pieces: wheel, core and holder. Put them together and fit them over the encoder on the board, probably at this point (*unverified*). The wheel should spin freely without wobbling; its side play has no folders (`scroll wheel tolerance`, [Scroll wheel](blender/customize/parts/scroll-wheel.md)). GripX has no exported scroll wheel yet.

**Check:**

- The board sits flat on the ledge all round, without forcing. If it does not go in, the slot is too small for your printer: raise `PCB tolerance XY` and print the case bottom again ([PCB and cable](blender/customize/parts/pcb-and-cable.md)). Do not press the board in hard.
- If the board sits slightly shifted front to back (the sticks look off-centre in their holes), the printing guide suggests turning on `pillars` in the global settings and printing the case again.
- Each trigger clicks its switch with a little free travel before the click, and does not click on its own. The bumpers are only held once the case is closed, so check them in step 10.

| If | Then |
| --- | --- |
| a trigger or bumper has a lot of free play before it clicks | print it from `press_tight/` (probably) |
| a trigger or bumper clicks by itself or has no travel | print it from `press_loose/` (probably) |

On GripX the bumper `pres_*` folders hold the same file for now; change `button press tol` on the GripX bumper nodes instead ([Bumpers](blender/customize/parts/bumpers.md)).

## 8. Battery and cover

The battery goes into the compartment in the underside of the case bottom and plugs into the board's battery connector. The compartment opens from the outside, so this step can probably also wait until the case is closed (*unverified*).

Press the cover in until its lips snap into the case.

**Check:** the cover sits flush, holds without rattling, does not press the battery hard and does not pinch the wire. The cover fit has no folders: change `x tolerance`, `y tolerance` or `compression offset` ([Battery cover](blender/customize/parts/battery-cover.md)).

## 9. Alignment pins

Push the two printed pins into their holes in the case bottom, one on each side. Each pin sits half in the bottom and half in the top, so the halves line up.

**Check:** the pins go in by hand and stand straight. The pin fit has no folders: change `xy tol` or `z tol` ([Pins](blender/customize/parts/pins.md)).

## 10. Close and screw

1. **Nuts first.** Press an M2.5 nut into each of the four nut pockets (probably all in the case top, *unverified*). Take your time: the pockets are reinforced, but PLA can still twist or bend while a nut is pressed in ([printing guide](print-guide.md#solid-case)). The optional nut lock probably wedges a front nut in its slot (*unverified*).
2. Check that every button, trigger and bumper is still in place.
3. Lower the case top onto the bottom so the pins go into their holes. Do not force it: if it does not close, something is out of place.
4. Put the screws in from the bottom (probably, *unverified*): the shorter pair at the front, the longer pair at the back. Tighten until the halves meet, and stop there; PLA threads and pockets do not take much force.

**Check:** the seam is closed all round. Every button presses and returns, both sticks reach full tilt, the triggers and bumpers click and return, and the scroll wheel turns. If something got stiffer when you tightened the screws, loosen them a little. For a bumper with too much free play, or one that clicks by itself, use the press table in [step 7](#7-put-the-board-into-its-slot).

## Hollow version

The hollow GripV case has three parts: the top shell, the bottom shell and a middle plate that holds the board ([printing guide](print-guide.md#hollow-version)). What is different:

- The board sits in a pocket of the **middle plate**, and the plate clips into the shells. The middle plate is not exported yet ([known gaps](../orca_slicer/README.md#known-gaps)).
- The shells line up on pins of the middle plate, so the two printed alignment pins are not used.
- **Screws are still recommended.** The case is designed to go together without screws, but the current middle plate may not clamp hard enough on its own. Note that the exported hollow shells probably have no screw holes yet; check yours before you buy screws.
- Parts that warped will not assemble. Clean each part thoroughly and check the critical spots before you start.

## Tell us how it went

Every fit report helps tune the `default` tolerances: [open a fit report](https://github.com/oleroma/Grip/issues/new?template=fit-report.yml). Name the folders you printed, for example `buttons/default/cap_tight`.
