"""Data the panels show, rebuilt by a ~10 Hz timer when marked dirty: preset metrics, statistics, menu items and the
directory tree preview with its expansion state (ARCHITECTURE.md, UI Cache Engine)."""
import os
import json
import itertools
import traceback

import bpy
from bpy.app.handlers import persistent

from .common import COUNT_LIMIT, blend_dir, bump_revision, root_dir, mark_dirty, redraw_sidebars, _ui_cache
from .nodes import cached_menu_items, get_menu_switch_items
from .naming import clash_key, export_dir
from .paths import parts_below
from .engine import count_override_combinations, generate_named_combinations, get_flat_overrides, get_override_signature
from .targets import SUPPORTED_OBJECT_TYPES, export_file_parts, iter_export_objects, sync_collection_objects
from .data import ensure_preset_uids, get_active_preset, iter_scene_nodegroup_lists, stamp_data_version

def check_ng_for_overrides(nodegroups):
    has_ovr = len(nodegroups) > 0
    has_perm = any(len(i.values) > 1 or any(getattr(v, "use_sweep", False) for v in i.values) for ng in nodegroups for n in ng.nodes for i in n.inputs)
    return has_ovr, has_perm

def _get_preset_status(scene, preset, g_has_ovr=False, g_has_perm=False):
    pho, php = check_ng_for_overrides(preset.nodegroups)
    has_ovr = g_has_ovr or pho
    has_perm = g_has_perm or php

    for c in preset.collections:
        if not c.export: continue
        cho, chp = check_ng_for_overrides(c.nodegroups)
        has_ovr = has_ovr or cho
        has_perm = has_perm or chp
        for obj in c.objects:
            if obj.export:
                oho, ohp = check_ng_for_overrides(obj.nodegroups)
                has_ovr = has_ovr or oho
                has_perm = has_perm or ohp
        if has_ovr and has_perm:
            return True, True
    return has_ovr, has_perm

def window_target(context):
    """What the cache is built for: the window's scene and view layer (None while there is none)."""
    scene, view_layer = getattr(context, "scene", None), getattr(context, "view_layer", None)
    return (scene.session_uid, view_layer.name) if scene and view_layer else None

def rebuild_ui_cache_if_dirty():
    # Switching the window's scene or view layer fires no depsgraph update, so the timer looks for it
    if window_target(bpy.context) != _ui_cache.get("target"): mark_dirty()
    if not _ui_cache.get("is_dirty", False): return 0.1
    _ui_cache["is_dirty"] = False

    try:
        with cached_menu_items(): return _rebuild_ui_cache()
    except Exception:
        _ui_cache["is_dirty"] = True  # retry, otherwise the UI shows stale data until the next unrelated edit
        try:
            if bpy.context.window_manager.batch_stl_verbose_console:
                traceback.print_exc()
        except Exception:
            pass
        return 0.25

def _rebuild_ui_cache():
    context = bpy.context
    if not hasattr(context, "scene") or not context.scene:
        _ui_cache["is_dirty"] = True
        return 0.1

    scene, wm = context.scene, context.window_manager
    _ui_cache["target"] = window_target(context)
    stamp_data_version(scene)
    ensure_preset_uids(scene)
    refresh_menu_items(scene)
    _ui_cache["objects_state"] = mapped_objects_state(scene)

    gho, ghp = check_ng_for_overrides(scene.batch_stl_global_nodegroups)
    preset_metrics = {}
    for p_idx, p in enumerate(scene.batch_stl_presets):
        ho, hp = _get_preset_status(scene, p, gho, ghp)
        preset_metrics[p_idx] = {"has_ovr": ho, "has_perm": hp}
    _ui_cache["preset_metrics"] = preset_metrics

    # "capped": a count stopped at COUNT_LIMIT, so the number is a lower bound
    g_stats = {"presets": len(scene.batch_stl_presets), "cols": 0, "objs": 0, "exp": 0, "capped": False}
    preset_stats, col_stats = {}, {}
    global_ovrs = get_flat_overrides(scene.batch_stl_global_nodegroups, "GLOBAL")
    count_cache = {}  # objects with identical overrides have the same number of variants

    for p_idx, p in enumerate(scene.batch_stl_presets):
        for c in p.collections: sync_collection_objects(c)
        p_stats = preset_stats[p_idx] = {"cols": len(p.collections), "objs": 0, "exp": 0, "capped": False}
        for c_idx in range(len(p.collections)): col_stats[(p_idx, c_idx)] = {"objs": 0, "exp": 0, "capped": False}
        for c_idx, _c, _obj_prop, _bl_obj, ovrs in iter_export_objects(scene, p, global_ovrs):
            n = count_override_combinations(ovrs, count_cache)
            for stats in (col_stats[(p_idx, c_idx)], p_stats, g_stats):
                stats["objs"] += 1
                stats["exp"] += min(n, COUNT_LIMIT)
                stats["capped"] |= n > COUNT_LIMIT
        g_stats["cols"] += p_stats["cols"]

    _ui_cache["stats"] = {"global": g_stats, "presets": preset_stats, "cols": col_stats}

    if wm.batch_stl_info_tab == 'TREE':
        preset = get_active_preset(scene)
        is_global = wm.batch_stl_info_global
        _ui_cache["tree"] = build_tree_dict(context, is_global) if (preset or is_global) else ({}, set())

    redraw_sidebars(context)
    return 0.1

def refresh_menu_items(scene):
    """Look up the items of every overridden menu socket outside of drawing: draw code cannot run the lookup of
    socket_menu_items() and reuses what this finds."""
    for nodegroups in iter_scene_nodegroup_lists(scene):
        for ng in nodegroups:
            ng_ptr = bpy.data.node_groups.get(ng.group_name)
            if not ng_ptr: continue
            for node in ng.nodes:
                for inp in node.inputs:
                    if inp.override_type == 'MENU': get_menu_switch_items(ng_ptr, node.name, inp.name)

def mapped_objects_state(scene):
    """(collection, object name) of every supported object in a mapped collection: renaming one changes the object
    lists and the tree. Hiding one changes nothing: the ticks decide what is exported."""
    state = set()
    for name in {c.collection_name for p in scene.batch_stl_presets for c in p.collections if c.collection_name}:
        col = bpy.data.collections.get(name)
        if col: state.update((name, o.name) for o in col.all_objects if o.type in SUPPORTED_OBJECT_TYPES)
    return frozenset(state)

@persistent
def batch_stl_undo_handler(*args):
    # A running export carries on: its worker exports from its own copy of the file, and its job is found by preset uid.
    mark_dirty()

@persistent
def batch_stl_depsgraph_handler(scene, depsgraph):
    """Runs after every depsgraph update, so it decides from the update's ID types first (cheap) and reads the add-on's
    data only for the updates that can change what the panels show."""
    # Menu items and node groups the merge predictions read can change in the node editor
    if depsgraph.id_type_updated('NODETREE'): bump_revision()
    if _ui_cache.get("is_dirty", False): return

    # Objects linked to / unlinked from collections change the object lists, counts and tree.
    collections_changed = depsgraph.id_type_updated('COLLECTION')

    # Renamed objects. Only a scene update or an object update that re-evaluates nothing (a rename) can change them:
    # every step of a transform drag, and every geometry or material edit, only re-evaluates objects, and selecting,
    # making active or hiding with the eye only updates the scene itself, so they skip the walk over the mapped objects.
    if not collections_changed:
        scene_changed = depsgraph.id_type_updated('SCENE') and not all(isinstance(u.id, bpy.types.Scene) for u in depsgraph.updates)
        if not scene_changed and not (depsgraph.id_type_updated('OBJECT') and any(
                isinstance(u.id, bpy.types.Object) and not (u.is_updated_transform or u.is_updated_geometry or u.is_updated_shading)
                for u in depsgraph.updates)):
            return

    if not any(c.collection_name for p in scene.batch_stl_presets for c in p.collections): return
    if collections_changed or mapped_objects_state(scene) != _ui_cache.get("objects_state"): mark_dirty()

# --- Directory tree preview -------------------------------------------------------------------------------------------
def build_tree_dict(context, is_global=False):
    """Folder tree of the files the active preset (or every preset) writes, and the clash keys of paths written more
    than once. Stops above COUNT_LIMIT files; the export runs its own collision check without a limit."""
    scene = context.scene
    base = blend_dir()
    root = root_dir(scene)
    root_name = root or os.path.normpath("//")
    tree, outside, all_filepaths, duplicates = {}, {}, set(), set()
    file_count = 0
    global_ovrs = get_flat_overrides(scene.batch_stl_global_nodegroups, "GLOBAL")
    active = get_active_preset(scene)
    target_presets = scene.batch_stl_presets if is_global else ([active] if active else [])
    variants_by_sig = {}  # objects with identical overrides share their variants

    for preset in target_presets:
        for _c_idx, c, obj_prop, bl_obj, ovrs in iter_export_objects(scene, preset, global_ovrs):
            sig = get_override_signature(ovrs)
            variants = variants_by_sig.get(sig)
            if variants is None:
                named = itertools.islice(generate_named_combinations(ovrs), COUNT_LIMIT + 1)
                variants = variants_by_sig[sig] = [(tags, paths) for _combo, tags, paths in named]
            for tags_by_level, paths_by_level in variants:
                file_count += 1
                if file_count > COUNT_LIMIT:
                    return {root_name: {"_files": [f"Tree preview limited to {COUNT_LIMIT} files (the export still checks every file for collisions)"]}}, set()
                full_dir_parts, filename = export_file_parts(preset, c, obj_prop, bl_obj, tags_by_level, paths_by_level)
                # A folder a '..' or absolute sub-folder puts outside the root is a tree of its own, by its full path
                folder = export_dir(root or base, full_dir_parts, base)
                below = parts_below(root or base, folder)
                combo_root, top_name = (tree, root_name) if below is not None else (outside.setdefault(folder, {}), folder)
                for part in below or ():
                    combo_root = combo_root.setdefault(part, {})
                combo_root.setdefault('_files', []).append(filename)

                full_path_key = clash_key(os.path.join(top_name, *(below or ()), filename))
                if full_path_key in all_filepaths:
                    duplicates.add(full_path_key)
                else:
                    all_filepaths.add(full_path_key)

    return {root_name: tree, **dict(sorted(outside.items()))}, duplicates

# Expansion state: `WindowManager.batch_stl_collapsed_dirs` stores the directory paths whose state is flipped from the
# default. The root folder starts expanded and everything below it collapsed.
def load_toggled_dirs(wm):
    try: return set(json.loads(wm.batch_stl_collapsed_dirs))
    except Exception: return set()

def save_toggled_dirs(wm, toggled):
    wm.batch_stl_collapsed_dirs = json.dumps(sorted(toggled))

def is_dir_collapsed(toggled, dir_path, is_root):
    return (dir_path in toggled) if is_root else (dir_path not in toggled)

def set_dir_collapsed(toggled, dir_path, is_root, collapsed):
    if collapsed == is_root: toggled.add(dir_path)  # the requested state differs from the default
    else: toggled.discard(dir_path)

def iter_tree_dirs(tree_node, current_path=""):
    """Yield (dir_path, node, is_root) for every directory, keyed exactly like draw_tree_dict."""
    for k, child in tree_node.items():
        if k == '_files' or not isinstance(child, dict): continue
        dir_path = f"{current_path}/{k}"
        yield dir_path, child, current_path == ""
        yield from iter_tree_dirs(child, dir_path)

def expand_last_dirs(tree_node, toggled, current_path=""):
    """Expand the last subdirectory of every directory, recursively."""
    subdirs = [k for k, v in tree_node.items() if k != '_files' and isinstance(v, dict)]
    is_root = current_path == ""
    if subdirs: set_dir_collapsed(toggled, f"{current_path}/{subdirs[-1]}", is_root, False)
    for k in subdirs:
        dir_path = f"{current_path}/{k}"
        expand_last_dirs(tree_node[k], toggled, dir_path)
