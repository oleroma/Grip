# Sticks

`StickL` and `StickR` are the thumbstick caps. Each one pushes onto the shaft of a joystick module. Its shape is designed around how far the stick tilts: the neck, the hole in the case top and the skirt (*shield*) that covers the hole are all sized so the stick can reach its full tilt without hitting the case, and the hole stays covered.

**Where:** controls panel › STICKS › `… stick L parameters` and `… stick R parameters`.

- **GripV** has one preset per stick.
- **GripX** keeps several named presets per stick and picks one with a menu inside the group. The left stick uses the *Menu* node `stick menu` (frame "STICK VARIANT"), with options such as "Xbox cap", "Xbox cap easy print tall/short", "Octagonal 18d range" and "Xbox Elite2 stick base". The right stick has "normal", "small round", "small square" and "8 dir". Edit the constructors in the frame of the preset you use.

Each preset is made of six constructors.

## Size and fit on the module (`basic stick parameters`)

| Input | What it changes |
|---|---|
| `stick heght` | height of the stick above the case |
| `stick top radius` | size of the thumb surface |
| `base size`, `base height` | the part that grips the joystick module's shaft |
| `shaft tolerance` | fit on the module's shaft: higher is looser |
| `shaft Z offset` | how deep the shaft goes into the stick |
| `top bevel`, `middle bevel` | rounding of the top edge and of the middle of the stick |

## Tilt range and the case hole

| Input | Constructor | What it changes |
|---|---|---|
| `range degrees` | basic | the tilt the stick must reach. The neck is shaped so the stick touches the case hole exactly at this angle. |
| `contact angle` | advanced | angle of the surface where stick and case hole meet at full tilt |
| `contact top offset`, `contact bottom offset`, `topmost offset` | basic | shape of the rim that touches the case hole at full tilt |
| `hole radius` | advanced | size of the hole in the case top (the stick's neck follows) |
| `hole bevel` | advanced | rounding of the hole's edge |
| `case cutout thickness` | advanced | GripX: wall around the stick opening. GripV uses fixed cutouts, so it does nothing there. |

## The top (`stick top parameters` and the texture sets)

| Input | What it changes |
|---|---|
| `top shape` | circle or square thumb surface |
| `top curvature` | concave, convex or flat |
| `texture type` | grid or icosahedron grip pattern. Only the matching texture set below acts. |
| `extrude texture` | raises the texture instead of cutting it in |
| `swap top rotation` | turns the top's outline and texture |
| `square top subd`, `square morph` | square tops: corner smoothness and how much the square bulges |
| `icosahedron texture parameters` | `texture height`, `texture sharpness`, subdivisions and curvature offset of the icosahedron pattern |
| `grid texture parameters` | height, subdivisions, sharpness, scale and offsets of the grid pattern |

## The skirt (`shield parameters`)

The skirt is the flared bottom of the stick that keeps the case hole covered at every angle.

| Input | What it changes |
|---|---|
| `sheild` | the skirt on or off |
| `sheild height` | how far down the skirt reaches |
| `shield cutoff height` | where the skirt is cut off |
| `sheild radius offset` | skirt radius |
| `FDM shield thickness`, `FDM Z correction` | extra thickness and a height correction for FDM printing |

## Position and preview (`advanced stick parameters`)

| Input | What it changes |
|---|---|
| `stick  XY correction` + `X correction`, `Y correction` | when on, shifts the stick off the module centre by X and Y |
| `swap stick rotation` | turns the stick's mesh layout |
| `stick subdivision`, `stick hole subdivision` | smoothness of stick and hole. The "8 dir" preset uses 8, which gives an eight-sided stick, probably for eight-direction input. |
| `action`, `action rotation` (basic) | shows the stick tilted, to check clearance. It is a preview only; turn it off before exporting. |
| `shaft X correction`, `shaft Y correction` | do nothing |

## Good to know

- The stick height is measured from the top surface of the case, so it follows the basemesh.
- A stick's position is its object's location. Move the stick and its cutter (`StickL hole` or `Stick R hole` in `source`) together. On GripV the stick cutouts are fixed meshes that do not move with it.

## Export

GripV exports only the left stick, in every combination of top shape, curvature, texture and range (10° to 20°). That sweep includes the right stick's top options. GripX exports both sticks in their named presets.
