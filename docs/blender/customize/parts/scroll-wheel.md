# Scroll wheel

A small wheel between the right stick and the face buttons. It is made of three pieces in the collection `scrollwheel`: the wheel (`scrollwheel`), its core (`scrollwheel core`) and a holder (`scrollwheel holder`).

Unlike the other parts, the wheel is **modelled by hand**. The nodes only adjust a few tagged parts of those meshes. So the axle, rib pattern and holder shape are changed by editing the meshes, and four values are parameters.

**Where:** controls panel › SCROLLWHEEL › `… scrollwheel` › `scroll parameters`.

| Input | What it changes |
|---|---|
| `scroll radius offset` | wheel diameter (the slot in the case grows with it) |
| `scroll width offset` | wheel width (the slot grows with it) |
| `scroll wheel tolerance` | side play of the wheel in its slot: the wheel gets this much narrower, half per side |
| `scroll wheel shift X` | moves one face of the wheel and of its slot, so the wheel gets wider towards one side |

## Export

GripV exports the three pieces to `parts/scrollwheel/`. GripX does not export them yet; add the `scrollwheel` collection to its "Parts" preset if you need them.
