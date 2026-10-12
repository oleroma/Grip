"""
Combi Export: batch STL export of mapped collections with Geometry Nodes overrides and combinatorial variants.
Data Hierarchy: Global > Preset > Collection > Object > NodeGroup > Node > Input > Value

One module per subsystem, see the module layout in ARCHITECTURE.md. This file registers the add-on: classes, scene and
window manager properties, app handlers and the UI cache timer.
"""
import sys

# Modules in dependency order: each one imports only modules listed before it
_MODULES = ("common", "nodes", "naming", "fields", "engine", "scope", "targets", "stl", "data", "validation", "headless",
            "ui_cache", "props", "operators", "export_operator", "ui")

if "bpy" in locals():
    # Reload Scripts runs this file again but keeps the modules it imported: reload them too, dependencies first, so
    # the classes registered below come from the edited code.
    import importlib
    for _name in _MODULES:
        if f"{__name__}.{_name}" in sys.modules: importlib.reload(sys.modules[f"{__name__}.{_name}"])

import bpy
from bpy.app.handlers import persistent

from . import export_operator, operators, props, ui
from .common import OVERRIDES_OPEN_PROPS, mark_dirty
from .data import batch_stl_import_handler, batch_stl_save_handler, prepare_scenes
from .export_operator import remove_stale_temp_dirs
from .props import BatchSTLExportPreset, BatchSTLJob, BatchSTLNodeGroup
from .ui import ICONS
from .ui_cache import batch_stl_depsgraph_handler, batch_stl_undo_handler, rebuild_ui_cache_if_dirty

@persistent
def reset_batch_stl_state(*args):
    try:
        for wm in bpy.data.window_managers: wm.batch_stl_jobs.clear()  # no export survives a file load
    except Exception: pass
    if hasattr(bpy.data, "scenes"): prepare_scenes()
    else: bpy.app.timers.register(prepare_scenes, first_interval=0.0)  # enabled from Preferences: bpy.data is still restricted
    mark_dirty()
    if "--batch-stl-headless" not in sys.argv and not bpy.app.timers.is_registered(rebuild_ui_cache_if_dirty):
        bpy.app.timers.register(rebuild_ui_cache_if_dirty)

classes = props.classes + operators.classes + export_operator.classes + ui.classes

# Open state of the override tables (Global, Preset, Collection, Object)
UI_OPEN_PROPS = tuple(OVERRIDES_OPEN_PROPS.values())
WM_PROPS = ("batch_stl_jobs", "batch_stl_verbose_console", "batch_stl_ui_tips", "batch_stl_collapsed_dirs", "batch_stl_info_tab",
            "batch_stl_info_global") + UI_OPEN_PROPS
SCENE_PROPS = ("batch_stl_data_version", "batch_stl_root_dir", "batch_stl_presets", "batch_stl_preset_index", "batch_stl_global_nodegroups")

def register():
    for cls in classes: bpy.utils.register_class(cls)

    if "--batch-stl-headless" not in sys.argv: remove_stale_temp_dirs()

    # Runtime and UI state lives on the WindowManager: not part of the scene's data, so undo never touches it
    WM = bpy.types.WindowManager
    WM.batch_stl_jobs = bpy.props.CollectionProperty(type=BatchSTLJob)
    WM.batch_stl_verbose_console = bpy.props.BoolProperty(name="Verbose Console Output", default=False)
    for prop in UI_OPEN_PROPS:
        setattr(WM, prop, bpy.props.BoolProperty(name="Show Node Groups & Nodes", default=True, description=(
            "Show the node group and node rows. Collapsed, only the inputs and their values are listed, "
            "and an input whose node group or node merges into an upstream branch shows the merge icon at its row start")))
    WM.batch_stl_ui_tips = bpy.props.BoolProperty(default=False)
    WM.batch_stl_collapsed_dirs = bpy.props.StringProperty(default="[]")
    WM.batch_stl_info_tab = bpy.props.EnumProperty(items=[('LOG', "Console Log", "", ICONS['CONSOLE'], 0), ('TREE', "Tree View", "", ICONS['TREE'], 1)], name="Info Tab", default='LOG', update=lambda s, c: mark_dirty())
    WM.batch_stl_info_global = bpy.props.BoolProperty(name="Global Mode", default=False, update=lambda s, c: mark_dirty())

    Scene = bpy.types.Scene
    Scene.batch_stl_root_dir = bpy.props.StringProperty(name="Root", default="//", subtype="DIR_PATH", options={'PATH_SUPPORTS_BLEND_RELATIVE'}, update=mark_dirty)
    Scene.batch_stl_presets = bpy.props.CollectionProperty(type=BatchSTLExportPreset)
    Scene.batch_stl_global_nodegroups = bpy.props.CollectionProperty(type=BatchSTLNodeGroup)
    Scene.batch_stl_preset_index = bpy.props.IntProperty(name="Active Preset", default=0, update=mark_dirty)
    Scene.batch_stl_data_version = bpy.props.IntProperty(default=0, options={'HIDDEN'})

    reset_batch_stl_state(None)
    if reset_batch_stl_state not in bpy.app.handlers.load_post: bpy.app.handlers.load_post.append(reset_batch_stl_state)
    if batch_stl_import_handler not in bpy.app.handlers.blend_import_post: bpy.app.handlers.blend_import_post.append(batch_stl_import_handler)
    if batch_stl_save_handler not in bpy.app.handlers.save_pre: bpy.app.handlers.save_pre.append(batch_stl_save_handler)

    if "--batch-stl-headless" not in sys.argv:
        if batch_stl_depsgraph_handler not in bpy.app.handlers.depsgraph_update_post: bpy.app.handlers.depsgraph_update_post.append(batch_stl_depsgraph_handler)
        if batch_stl_undo_handler not in bpy.app.handlers.undo_post: bpy.app.handlers.undo_post.append(batch_stl_undo_handler)
        if batch_stl_undo_handler not in bpy.app.handlers.redo_post: bpy.app.handlers.redo_post.append(batch_stl_undo_handler)
        if not bpy.app.timers.is_registered(rebuild_ui_cache_if_dirty): bpy.app.timers.register(rebuild_ui_cache_if_dirty)

def unregister():
    if reset_batch_stl_state in bpy.app.handlers.load_post: bpy.app.handlers.load_post.remove(reset_batch_stl_state)
    if batch_stl_import_handler in bpy.app.handlers.blend_import_post: bpy.app.handlers.blend_import_post.remove(batch_stl_import_handler)
    if batch_stl_save_handler in bpy.app.handlers.save_pre: bpy.app.handlers.save_pre.remove(batch_stl_save_handler)
    if batch_stl_depsgraph_handler in bpy.app.handlers.depsgraph_update_post: bpy.app.handlers.depsgraph_update_post.remove(batch_stl_depsgraph_handler)
    if batch_stl_undo_handler in bpy.app.handlers.undo_post: bpy.app.handlers.undo_post.remove(batch_stl_undo_handler)
    if batch_stl_undo_handler in bpy.app.handlers.redo_post: bpy.app.handlers.redo_post.remove(batch_stl_undo_handler)
    if bpy.app.timers.is_registered(rebuild_ui_cache_if_dirty): bpy.app.timers.unregister(rebuild_ui_cache_if_dirty)

    for cls in reversed(classes):
        try: bpy.utils.unregister_class(cls)
        except RuntimeError: pass

    for p in WM_PROPS:
        if hasattr(bpy.types.WindowManager, p): delattr(bpy.types.WindowManager, p)
    for p in SCENE_PROPS:
        if hasattr(bpy.types.Scene, p): delattr(bpy.types.Scene, p)
