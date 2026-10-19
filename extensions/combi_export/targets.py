"""What a preset exports and where: the collections and objects Blender evaluates, the object entries of mapped
collections, the overrides that apply to each object, output paths and the collision check."""
import os

import bpy

from .common import COUNT_LIMIT, blend_dir, root_dir
from .nodes import cached_menu_items
from .naming import build_export_dir_parts, clash_key, export_dir, format_export_filename
from .paths import relative_below
from .engine import generate_named_combinations, get_flat_overrides, get_override_signature, resolve_overrides

SUPPORTED_OBJECT_TYPES = {"MESH", "CURVE", "SURFACE", "META", "FONT"}

def is_group_used_by_object(group, obj, override_target):
    if not group: return False
    for mod in obj.modifiers:
        if mod.type == 'NODES' and mod.node_group:
            if override_target == 'MODIFIER':
                if mod.node_group == group: return True
            else:
                def check_tree(tree, seen=None):
                    if not tree: return False
                    if seen is None: seen = set()
                    if tree in seen: return False
                    seen.add(tree)
                    if tree == group: return True
                    for node in tree.nodes:
                        if getattr(node, "node_tree", None):
                            if check_tree(node.node_tree, seen): return True
                    return False
                if check_tree(mod.node_group): return True
    return False

def filter_overrides_for_object(overrides, bl_obj):
    return [o for o in overrides if is_group_used_by_object(o.parent_group_ptr, bl_obj, getattr(o, "override_target", "NODE"))]

def live_collection_names(view_layer):
    """Names of the collections Blender evaluates in `view_layer`: not excluded and not disabled in viewports, and
    neither are their parents. A collection linked in several places is live if one occurrence is. Objects outside
    them are not evaluated (their mesh lacks its modifiers) until the worker switches their collections on, see
    is_direct and headless.isolate_batch."""
    live = set()
    def traverse(layer_collection):
        if layer_collection.exclude or layer_collection.collection.hide_viewport: return
        live.add(layer_collection.collection.name)
        for child in layer_collection.children: traverse(child)
    if view_layer: traverse(view_layer.layer_collection)
    return live

def is_object_live(obj, live):
    """Whether Blender evaluates `obj` (see live_collection_names); hiding with the eye icon still evaluates."""
    return not obj.hide_viewport and any(c.name in live for c in obj.users_collection)

def is_direct(bl_obj, ovrs, live):
    """Whether the open Blender writes `bl_obj` itself (the direct path): no overrides, and evaluated in the view layer
    of the export (`live`). Everything else goes to the worker, which switches its collections on in its copy. The
    worker asks the same of the job's view layer, saved at the click, to skip what was written directly."""
    return not ovrs and is_object_live(bl_obj, live)

def untick_unevaluated(preset, live):
    """Untick what the view layer kept from exporting before the ticks alone decided (data version 4): collections
    that are not evaluated in it (`live`), and the objects of the others that are not. Objects without an entry yet
    get one, unticked when not evaluated, so that the first export after the update writes the same files. A missing
    collection keeps its tick: the export reports it as not found."""
    for c in preset.collections:
        col = bpy.data.collections.get(c.collection_name)
        if col is None: continue
        if col.name not in live:
            c.export = False
            continue
        names = {entry.name for entry in c.objects}
        for entry in c.objects:
            obj = col.all_objects.get(entry.name)
            if obj and not is_object_live(obj, live): entry.export = False
        for obj in col.all_objects:
            if obj.type in SUPPORTED_OBJECT_TYPES and obj.name not in names and not is_object_live(obj, live):
                entry = c.objects.add()
                entry.name, entry.obj_uid, entry.export = obj.name, obj.session_uid, False

def sync_collection_objects(col_prop, col_ptr=None):
    """Match the object entries of a mapped collection to its objects: drop entries of objects that left, add entries
    for new ones (in the collection's order) and follow renames, so a renamed object keeps its settings."""
    if not col_ptr: col_ptr = bpy.data.collections.get(col_prop.collection_name)
    if not col_ptr: return

    # A list (not a set) keeps new objects in the collection's own order.
    actual_objs = [obj for obj in col_ptr.all_objects if obj.type in SUPPORTED_OBJECT_TYPES]
    by_name = {obj.name: obj for obj in actual_objs}
    by_uid = {obj.session_uid: obj for obj in actual_objs}
    entry_names = {entry.name for entry in col_prop.objects}

    # Entries remember their object's session_uid; an ID pointer would add a user to the object, so deleting the
    # object would only unlink it. An entry whose name is gone follows the uid to the renamed object. Otherwise the name
    # wins: uids change when a file is loaded (restamp_object_uids() refreshes them) and can be stale in appended data.
    orphans = []
    for entry in col_prop.objects:
        obj = by_name.get(entry.name)
        if obj is None:
            obj = by_uid.get(entry.obj_uid) if entry.obj_uid else None
            if obj is None or obj.name in entry_names:
                orphans.append(entry)
                continue
            entry.name = obj.name
            entry_names.add(obj.name)
        if entry.obj_uid != obj.session_uid: entry.obj_uid = obj.session_uid

    # A rename the uid cannot follow (made while the add-on was off): one entry lost its object, which no longer exists,
    # and one object has no entry.
    new_objs = [obj for obj in actual_objs if obj.name not in entry_names]
    if len(orphans) == 1 and len(new_objs) == 1:
        entry, obj = orphans[0], new_objs[0]
        if not entry.obj_uid or not any(o.session_uid == entry.obj_uid for o in bpy.data.objects):
            entry.name, entry.obj_uid = obj.name, obj.session_uid
            entry_names.add(obj.name)

    for i in reversed(range(len(col_prop.objects))):
        if col_prop.objects[i].name not in by_name: col_prop.objects.remove(i)

    for obj in actual_objs:
        if obj.name not in entry_names:
            entry = col_prop.objects.add()
            entry.name = obj.name  # `export` defaults to True; setting it would mark the cache dirty again
            entry.obj_uid = obj.session_uid

def restamp_object_uids(scene):
    """Session uids change when a file is loaded: point the object entries at their objects again, by name."""
    for preset in scene.batch_stl_presets:
        for col in preset.collections:
            col_ptr = bpy.data.collections.get(col.collection_name)
            for entry in col.objects:
                obj = col_ptr.all_objects.get(entry.name) if col_ptr else None
                uid = obj.session_uid if obj else 0
                if entry.obj_uid != uid: entry.obj_uid = uid

def export_file_parts(preset, c, obj_prop, bl_obj, tags_by_level=None, paths_by_level=None):
    """(folder names below the root, filename) of one exported file."""
    return (build_export_dir_parts(preset.preset_prefix, c.sub_path, obj_prop.sub_path, paths_by_level),
            format_export_filename(obj_prop.export_name, obj_prop.tag, c.use_tag, c.tag, tags_by_level))

def iter_export_objects(scene, preset, global_ovrs=None):
    """(collection index, collection entry, object entry, object, resolved overrides) of every object the preset
    exports: ticked in a ticked collection that exists. The ticks alone decide, not the view layer: an object Blender
    does not evaluate there is exported by the worker, which switches its collections on (is_direct). Call
    sync_collection_objects() first."""
    if global_ovrs is None: global_ovrs = get_flat_overrides(scene.batch_stl_global_nodegroups, "GLOBAL")
    preset_ovrs = global_ovrs + get_flat_overrides(preset.nodegroups, "PRESET")
    for c_idx, c in enumerate(preset.collections):
        if not c.export: continue
        c_ptr = bpy.data.collections.get(c.collection_name)
        if not c_ptr: continue
        col_ovrs = preset_ovrs + get_flat_overrides(c.nodegroups, "COLLECTION")
        for obj_prop in c.objects:
            if not obj_prop.export: continue
            bl_obj = c_ptr.all_objects.get(obj_prop.name)
            if not bl_obj or bl_obj.type not in SUPPORTED_OBJECT_TYPES: continue
            ovrs = resolve_overrides(col_ovrs + get_flat_overrides(obj_prop.nodegroups, "OBJECT"))
            yield c_idx, c, obj_prop, bl_obj, filter_overrides_for_object(ovrs, bl_obj)

def group_by_signature(export_objects):
    """{override signature: (overrides, [(collection entry, object entry, object)])}: objects with the same overrides
    share their variants, which are generated once (and evaluated in one depsgraph pass in the worker)."""
    batches = {}
    for _c_idx, c, obj_prop, bl_obj, ovrs in export_objects:
        batches.setdefault(get_override_signature(ovrs), (ovrs, []))[1].append((c, obj_prop, bl_obj))
    return batches

def iter_export_files(scene, preset, global_ovrs=None):
    """(folder names below the root, filename) of every file the preset writes, duplicates included."""
    for ovrs, items in group_by_signature(iter_export_objects(scene, preset, global_ovrs)).values():
        for _combo, tags_by_level, paths_by_level in generate_named_combinations(ovrs):
            for c, obj_prop, bl_obj in items:
                yield export_file_parts(preset, c, obj_prop, bl_obj, tags_by_level, paths_by_level)

def find_export_clashes(scene, preset, root):
    """{clash key: path} of the output paths that more than one file of the preset would be written to. No limit:
    every collision overwrites a file."""
    seen, clashes, base = set(), {}, blend_dir()
    for dir_parts, filename in iter_export_files(scene, preset):
        path = os.path.join(export_dir(root, dir_parts, base), filename)
        key = clash_key(path)
        if key in seen: clashes.setdefault(key, path)
        else: seen.add(key)
    return clashes

def export_manifest(scene, limit=COUNT_LIMIT):
    """The files each preset of `scene` writes, for the JSON saved with the file: {"complete", "presets": [{"name",
    "files"}]}. Files are paths below the root folder with `/` between names (absolute when a `..` or absolute
    sub-folder puts them outside it), sorted, each once. After `limit` files in all the rest are left out and
    `complete` is false. Call sync_collection_objects() first."""
    global_ovrs = get_flat_overrides(scene.batch_stl_global_nodegroups, "GLOBAL")
    base = blend_dir()
    root = root_dir(scene) or base
    presets, total, complete = [], 0, True
    with cached_menu_items():
        for preset in scene.batch_stl_presets:
            files = set()
            for dir_parts, filename in iter_export_files(scene, preset, global_ovrs):
                if total == limit:
                    complete = False
                    break
                total += 1
                files.add(relative_below(root, os.path.join(export_dir(root, dir_parts, base), filename)))
            presets.append({"name": preset.name, "files": sorted(files)})
            if not complete: break
    return {"complete": complete, "presets": presets}
