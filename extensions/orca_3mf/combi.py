"""What Combi Export writes, asked from Combi itself in this Blender: its presets, and for a preset every file it
exports with the Blender object it comes from. Nothing here changes Combi's data.

Combi is another add-on (its package is bl_ext.<repo>.combi_export when installed as an extension, combi_export
when loaded as a plain add-on). Its functions are used as Combi's own export_manifest uses them; when Combi is not
installed, or it changed so that they are gone, every function here answers as if there were no Combi."""
import os
import sys

LIMIT = 5000  # files per preset, as Combi's own tree preview and manifest


def module():
    """Combi's targets module, or None."""
    for name, mod in list(sys.modules.items()):
        if name == "combi_export.targets" or name.endswith(".combi_export.targets"):
            if all(hasattr(mod, f) for f in ("iter_export_objects", "group_by_signature", "export_file_parts",
                                              "generate_named_combinations", "export_dir", "root_dir",
                                              "blend_dir", "get_flat_overrides", "cached_menu_items")):
                return mod
    return None


def available(scene):
    return module() is not None and hasattr(scene, "batch_stl_presets")


def presets(scene):
    """[(uid, name)] of Combi's presets in the scene (a preset without a uid yet is named by its name)."""
    if not available(scene):
        return []
    return [(p.uid or p.name, p.name) for p in scene.batch_stl_presets]


def find_preset(scene, key):
    """The Combi preset whose uid is key, else the one named key, else None."""
    if not key or not available(scene):
        return None
    found = [p for p in scene.batch_stl_presets if p.uid == key]
    return found[0] if found else next((p for p in scene.batch_stl_presets if p.name == key), None)


def files(scene, preset):
    """[(absolute STL path, Blender object)] of every file the preset writes, each path once, sorted by path; at most
    LIMIT. Empty without Combi."""
    t = module()
    if t is None or preset is None:
        return []
    base = t.blend_dir()
    root = t.root_dir(scene) or base
    found = {}
    with t.cached_menu_items():
        global_ovrs = t.get_flat_overrides(getattr(scene, "batch_stl_global_nodegroups", ()), "GLOBAL")
        batches = t.group_by_signature(t.iter_export_objects(scene, preset, global_ovrs))
        for ovrs, items in batches.values():
            for _combo, tags_by_level, paths_by_level in t.generate_named_combinations(ovrs):
                for c, obj_prop, bl_obj in items:
                    dir_parts, file_name = t.export_file_parts(preset, c, obj_prop, bl_obj, tags_by_level,
                                                               paths_by_level)
                    path = os.path.normpath(os.path.join(t.export_dir(root, dir_parts, base), file_name))
                    found.setdefault(os.path.normcase(path), (path, bl_obj))
                    if len(found) >= LIMIT:
                        return sorted(found.values(), key=lambda f: f[0])
    return sorted(found.values(), key=lambda f: f[0])


def common_folder(paths_):
    """The deepest folder all the paths are in, or ""."""
    folders = [os.path.dirname(p) for p in paths_]
    if not folders:
        return ""
    try:
        return os.path.commonpath(folders)
    except ValueError:  # on different drives
        return ""
