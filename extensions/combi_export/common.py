"""Shared state and edit plumbing: the UI cache and its dirty flag, the limits used across modules, and the undo and
raw-edit machinery every property callback and operator goes through (ARCHITECTURE.md, Undo Stack Protection)."""
import contextlib
import functools

import bpy

MAX_SWEEP_STEPS = 1000
# Counting variants by enumeration (only needed when values apply to some branches only) stops above this, and so does
# the tree preview. The export's collision check has no limit.
COUNT_LIMIT = 5000

# Open state of the override tables, one WindowManager flag per level (the tables of a level share it)
OVERRIDES_OPEN_PROPS = {"global": "batch_stl_ui_global_ovr", "preset": "batch_stl_ui_preset_ovr",
                        "collection": "batch_stl_ui_collection_ovr", "object": "batch_stl_ui_object_ovr"}

def overrides_open_prop(is_collection=False, is_preset=False, is_global=False):
    """Name of the WindowManager flag that holds the open state of the override table of a level."""
    return OVERRIDES_OPEN_PROPS["global" if is_global else "preset" if is_preset else "collection" if is_collection else "object"]

_ui_cache = {
    "is_dirty": True,
    "live": set(),
    "stats": {"global": {"presets": 0, "cols": 0, "objs": 0, "exp": 0}, "presets": {}, "cols": {}},
    "tree": ({}, set()),
    "preset_metrics": {},
    # (scene session uid, view layer name) of the window the cache was built for, see ui_cache.window_target
    "target": None,
    # Bumped whenever data the panels show may have changed: every edit (mark_dirty), node tree updates and menu items
    # found changed. Draw-time caches (the override tables' merge predictions) hold for one revision.
    "revision": 0,
}

def mark_dirty(self=None, context=None):
    _ui_cache["is_dirty"] = True
    _ui_cache["revision"] += 1

def bump_revision():
    """Data the panels show changed without needing a UI cache rebuild (see _ui_cache["revision"])."""
    _ui_cache["revision"] += 1

# Blender gives every UI-edited property an undo step except search fields (prop_search / StringProperty(search=...)):
# those buttons are created without UI_BUT_UNDO, so picking an item from the dropdown leaves no history entry.
# Their update callbacks push the step themselves. Operators record their own step ('UNDO' in bl_options), so
# property writes made while an operator (or an outer update callback) runs must not push a second one.
_undo_suppress_depth = 0

def push_search_undo(label):
    if _undo_suppress_depth: return
    try: bpy.ops.ed.undo_push(message=label)
    except RuntimeError: pass

def search_field_update(label):
    """Update callback for a search field: refresh the UI cache and record an undo step."""
    def update(self, context):
        mark_dirty()
        push_search_undo(label)
    return update

def inside_operator(execute):
    """Decorator for operator execute(): property updates fired by the operator itself do not push undo steps."""
    @functools.wraps(execute)
    def wrapper(self, context):
        global _undo_suppress_depth
        _undo_suppress_depth += 1
        try: return execute(self, context)
        finally: _undo_suppress_depth -= 1
    return wrapper

@contextlib.contextmanager
def nested_edits():
    """Property writes inside record no undo step of their own: the edit around them records one."""
    global _undo_suppress_depth
    _undo_suppress_depth += 1
    try: yield
    finally: _undo_suppress_depth -= 1

# Override name/value callbacks react to edits made by the user: they revert duplicates and refill dependent data
# (group -> node -> input -> value). Code that writes already-consistent data (paste, JSON import) runs inside
# raw_edits(), where the callbacks only accept the written value as the new "previous" one and do nothing else.
_raw_edit_depth = 0

@contextlib.contextmanager
def raw_edits():
    global _raw_edit_depth
    _raw_edit_depth += 1
    try: yield
    finally: _raw_edit_depth -= 1

def in_raw_edits():
    """Whether code inside raw_edits() is writing. Other modules ask here: an imported copy of the counter would
    never change."""
    return _raw_edit_depth > 0

# Returned by an edit callback that removed its own item (field cleared to delete it): `self` is then gone and
# must not be read again.
DELETED = object()

def edit_callback(label, prop, prev_prop):
    """Decorator for the update callback of `prop`: skips the logic during raw_edits(), and records a single undo
    step (when `label` is set) for the outermost callback of a cascade instead of one per nested callback."""
    def decorate(update):
        @functools.wraps(update)
        def wrapper(self, context):
            global _undo_suppress_depth
            if _raw_edit_depth:
                setattr(self, prev_prop, getattr(self, prop))
                mark_dirty()
                return
            old_val = getattr(self, prev_prop)
            _undo_suppress_depth += 1
            try: result = update(self, context)
            finally: _undo_suppress_depth -= 1
            mark_dirty()
            if not label: return
            if result is DELETED:
                push_search_undo(label)
                return
            try: new_val = getattr(self, prop)
            except ReferenceError: return
            if new_val != old_val: push_search_undo(label)
        return wrapper
    return decorate

_held_keys = {"ctrl": False}

def ctrl_held():
    """Whether Ctrl is held at the current click. A property setter gets no event, but an operator invoked from it gets
    the window's event state (batch_stl.read_modifiers). False without a UI (background, or no window)."""
    if bpy.app.background or getattr(bpy.context, "window", None) is None: return False
    _held_keys["ctrl"] = False
    try: bpy.ops.batch_stl.read_modifiers('INVOKE_DEFAULT')
    except RuntimeError: return False
    return _held_keys["ctrl"]

def redraw_sidebars(context=None):
    """Redraw only the 3D viewport sidebars (where this add-on lives), not the whole viewports."""
    wm = getattr(context or bpy.context, "window_manager", None)
    if not wm: return
    for window in wm.windows:
        for area in window.screen.areas:
            if area.type == 'VIEW_3D':
                for region in area.regions:
                    if region.type == 'UI': region.tag_redraw()
