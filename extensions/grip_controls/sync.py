"""Keeps the global variant in step with the scene shown, so the GripX scene is never built from GripV numbers.

Replaces the 'Auto sync workspaces' text block. It listens with the message bus for scene and workspace switches
in a window (never on every depsgraph update and never from a draw call), and only writes when the value differs.
"""
import bpy
from bpy.app.handlers import persistent

from . import resolve

_OWNER = object()  # message bus owner of the subscriptions


def addon_prefs(context):
    """The add-on preferences, or None when the add-on is not enabled through Preferences."""
    addon = context.preferences.addons.get(__package__) if context.preferences else None
    return addon.preferences if addon is not None else None


def sync_enabled(context):
    prefs = addon_prefs(context)
    return bool(prefs and prefs.sync_variant)


def target_variant(scene_names):
    """The variant every Grip scene on screen agrees on, or None (no Grip scene, or GripV and GripX at once)."""
    targets = {resolve.variant_for_scene(name) for name in scene_names} - {None}
    return targets.pop() if len(targets) == 1 else None


def sync_scene(scene):
    """Sets the variant to match one scene. Returns True when it wrote."""
    if scene is None or not resolve.is_grip_file():
        return False
    return resolve.set_variant(resolve.variant_for_scene(scene.name))


def sync_from_windows(context):
    """Sync after a switch: follows the scenes of all windows, since the message bus does not say which window."""
    if not sync_enabled(context) or not resolve.is_grip_file():
        return False
    wm = context.window_manager
    names = [w.scene.name for w in wm.windows if w.scene is not None] if wm is not None else []
    return resolve.set_variant(target_variant(names))


def _on_window_change():
    try:
        sync_from_windows(bpy.context)
    except Exception as e:  # a callback must not raise into Blender's event loop
        print(f"Grip Controls: variant sync failed: {e}")


def _sync_later():
    _on_window_change()
    return None  # run once


def subscribe():
    """(Re)subscribes to scene and workspace switches. Loading a file clears all subscriptions."""
    bpy.msgbus.clear_by_owner(_OWNER)
    for prop in ("scene", "workspace"):
        bpy.msgbus.subscribe_rna(key=(bpy.types.Window, prop), owner=_OWNER, args=(), notify=_on_window_change)


def is_subscribed():
    return _on_load in bpy.app.handlers.load_post


@persistent
def _on_load(*_args):
    subscribe()
    # Sync once the file's windows are up, not while it is loading
    if not bpy.app.timers.is_registered(_sync_later):
        bpy.app.timers.register(_sync_later, first_interval=0.2)


def register():
    subscribe()
    if _on_load not in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.append(_on_load)
    # Enabled with a file already open: sync after Preferences gives bpy.data back
    if not bpy.app.timers.is_registered(_sync_later):
        bpy.app.timers.register(_sync_later, first_interval=0.2)


def unregister():
    bpy.msgbus.clear_by_owner(_OWNER)
    if _on_load in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(_on_load)
    if bpy.app.timers.is_registered(_sync_later):
        bpy.app.timers.unregister(_sync_later)
