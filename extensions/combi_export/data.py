"""The add-on's scene data beyond the property groups: active item lookups, export jobs and their logs, JSON and
clipboard copies, and versioning of stored data (DATA_VERSION, migrations, append and save handlers)."""
import uuid
import traceback

import bpy
from bpy.app.handlers import persistent

from .common import raw_edits
from .naming import legacy_naming_template
from .targets import live_collection_names, restamp_object_uids, untick_unevaluated

# --- Active items and export jobs -------------------------------------------------------------------------------------

def get_active_preset(scene):
    presets = scene.batch_stl_presets
    idx = scene.batch_stl_preset_index
    return presets[idx] if presets and 0 <= idx < len(presets) else None

def get_active_collection(preset):
    return preset.collections[preset.collection_index] if preset and preset.collections and 0 <= preset.collection_index < len(preset.collections) else None

def get_active_object(collection):
    return collection.objects[collection.object_index] if collection and collection.objects and 0 <= collection.object_index < len(collection.objects) else None

# Export jobs are keyed by the preset's uid and its scene's session_uid: unlike indices, pointers and names, both
# survive undo, reordering, renaming and switching scenes while an export runs.
def ensure_preset_uids(scene):
    """Give every preset of `scene` a unique uid (new presets, older files, duplicated scenes or presets)."""
    seen = set()
    for preset in scene.batch_stl_presets:
        if not preset.uid or preset.uid in seen: preset.uid = uuid.uuid4().hex
        seen.add(preset.uid)

def find_preset(scene_uid, preset_uid):
    for scene in bpy.data.scenes:
        if scene.session_uid == scene_uid:
            return next((p for p in scene.batch_stl_presets if p.uid == preset_uid), None)
    return None

def find_job(scene_uid, preset_uid):
    if not preset_uid: return None
    for job in bpy.context.window_manager.batch_stl_jobs:
        if job.preset_uid == preset_uid and job.scene_uid == scene_uid: return job
    return None

def get_job(preset, create=False):
    """Runtime export state of a preset. Creating requires an operator context, not a draw call."""
    if preset is None or not preset.uid: return None
    scene_uid = preset.id_data.session_uid
    job = find_job(scene_uid, preset.uid)
    if job or not create: return job
    job = bpy.context.window_manager.batch_stl_jobs.add()
    job.preset_uid, job.scene_uid = preset.uid, scene_uid
    return job

def remove_job(scene_uid, preset_uid):
    jobs = bpy.context.window_manager.batch_stl_jobs
    for i, job in enumerate(jobs):
        if job.preset_uid == preset_uid and job.scene_uid == scene_uid:
            jobs.remove(i)
            return

def is_any_exporting():
    return any(job.is_exporting for job in bpy.context.window_manager.batch_stl_jobs)

def log_to_console(job, text):
    if job:
        # UI labels cannot show line breaks: one log entry per line, like the worker output.
        for line in text.split("\n"):
            job.console_logs.add().text = line
        while len(job.console_logs) > 300: job.console_logs.remove(0)
        job.console_index = len(job.console_logs) - 1

# --- JSON and clipboard copies ----------------------------------------------------------------------------------------
def copy_val_to_dict(v):
    return {
        "value_string": getattr(v, "value_string", ""), "value_menu": getattr(v, "value_menu", ""),
        "use_tag": getattr(v, "use_tag", False), "tag": getattr(v, "tag", ""),
        "use_dir": getattr(v, "use_dir", False), "dir_tag": getattr(v, "dir_tag", ""), "use_sweep": getattr(v, "use_sweep", False),
        "sweep_range": getattr(v, "sweep_range", ""),
        "sweep_start": getattr(v, "sweep_start", "0"),
        "sweep_step": getattr(v, "sweep_step", "1"),
        "sweep_count": getattr(v, "sweep_count", "2")
    }

def copy_input_to_dict(i):
    return {"name": i.name, "override_type": i.override_type, "values": [copy_val_to_dict(v) for v in i.values]}

def copy_node_to_dict(n):
    return {"name": n.name, "sub_path": getattr(n, "sub_path", ""), "tag": getattr(n, "tag", ""), "inputs": [copy_input_to_dict(i) for i in n.inputs]}

def copy_ng_to_dict(ng):
    return {"group": ng.group_name, "sub_path": getattr(ng, "sub_path", ""), "tag": getattr(ng, "tag", ""), "nodes": [copy_node_to_dict(n) for n in ng.nodes]}

def copy_obj_to_dict(o):
    return {"name": o.name, "name_override": o.name_override, "export": o.export, "tag": getattr(o, "tag", ""), "sub_path": getattr(o, "sub_path", ""), "nodegroups": [copy_ng_to_dict(ng) for ng in o.nodegroups]}

def copy_collection_to_dict(c):
    return {"collection_name": c.collection_name, "export": c.export, "use_tag": c.use_tag, "tag": c.tag, "sub_path": c.sub_path, "objects": [copy_obj_to_dict(o) for o in c.objects], "nodegroups": [copy_ng_to_dict(ng) for ng in c.nodegroups]}

def copy_preset_to_dict(src):
    return {"name": src.name, "data_version": DATA_VERSION, "preset_prefix": src.preset_prefix, "collections": [copy_collection_to_dict(c) for c in src.collections], "nodegroups": [copy_ng_to_dict(ng) for ng in src.nodegroups]}

def copy_setup_to_dict(scene):
    """What a JSON file holds: every preset, plus what applies to all of them, the root folder and the global
    overrides. Files written before these were added hold only the list of presets."""
    return {"data_version": DATA_VERSION, "root_dir": scene.batch_stl_root_dir,
            "global_nodegroups": [copy_ng_to_dict(ng) for ng in scene.batch_stl_global_nodegroups],
            "presets": [copy_preset_to_dict(p) for p in scene.batch_stl_presets]}

def upgrade_nodegroup_dicts(nodegroups, data_version):
    """Bring node groups from a JSON file (copy_ng_to_dict) saved with an older DATA_VERSION up to date, in place:
    value naming fields before version 3 hold the old folder / tag syntax (legacy_naming_template)."""
    if data_version >= 3: return
    for ng in nodegroups or []:
        for n in ng.get("nodes", []):
            for i in n.get("inputs", []):
                for v in i.get("values", []):
                    # Presets saved before the split used one tag for both the filename and the folder
                    if "dir_tag" not in v: v["dir_tag"] = v.get("tag", "")
                    v["dir_tag"] = legacy_naming_template(v["dir_tag"] or "", "dir")
                    v["tag"] = legacy_naming_template(v.get("tag", "") or "", "tag")

def upgrade_preset_dict(data):
    """Bring a preset from a JSON file (copy_preset_to_dict) saved by an older version up to DATA_VERSION, in place."""
    version = data.get("data_version", 0)
    if version >= DATA_VERSION: return data
    upgrade_nodegroup_dicts(data.get("nodegroups"), version)
    for c in data.get("collections", []):
        upgrade_nodegroup_dicts(c.get("nodegroups"), version)
        for o in c.get("objects", []): upgrade_nodegroup_dicts(o.get("nodegroups"), version)
    data["data_version"] = DATA_VERSION
    return data

# v1.0.0 kept numbers and booleans in typed fields, with typed sweep fields; they are all text now.
LEGACY_VALUE_KEYS = ("value_bool", "value_int", "value_float", "sweep_start_float", "sweep_step_float", "sweep_count_float",
                     "sweep_start_int", "sweep_step_int", "sweep_count_int")

def legacy_number_text(value, kind):
    return str(int(value)) if kind == "int" else f"{float(value):.7g}"

def migrate_legacy_value(v, legacy, override_type, fill_defaults=False):
    """Move a value's v1.0.0 typed fields (read with `legacy(key)`, None when absent) into the text fields of its input
    type. With `fill_defaults` a missing typed value gets its old default: .blend files do not store unedited fields."""
    kind = "int" if override_type == 'INT' else "float"
    if override_type in ('INT', 'FLOAT') and not v.value_string:
        old = legacy(f"value_{kind}")
        if old is None and fill_defaults: old = 0
        if old is not None: v.value_string = legacy_number_text(old, kind)
    elif override_type == 'BOOLEAN' and not v.value_menu:
        old = legacy("value_bool")
        if old is None and fill_defaults: old = True
        if old is not None: v.value_menu = str(bool(old))
    for field in ("start", "step", "count"):
        old = legacy(f"sweep_{field}_{kind}")
        if old is not None: setattr(v, f"sweep_{field}", legacy_number_text(old, "int" if field == "count" else kind))

def paste_val_from_dict(new_v, data, override_type='FLOAT'):
    for k, v in data.items():
        if hasattr(new_v, k): setattr(new_v, k, v)
    # Presets saved before the split used one tag for both the filename and the folder
    if "dir_tag" not in data: new_v.dir_tag = data.get("tag", "")
    migrate_legacy_value(new_v, data.get, override_type)

def paste_input_from_dict(new_i, data):
    new_i.name = data["name"]
    new_i.override_type = data.get("override_type", 'FLOAT')
    for v_data in data.get("values", []): paste_val_from_dict(new_i.values.add(), v_data, new_i.override_type)

def paste_node_from_dict(new_n, data):
    new_n.name = data.get("name", "")
    new_n.sub_path = data.get("sub_path", "")
    new_n.tag = data.get("tag", "")
    for i_data in data.get("inputs", []): paste_input_from_dict(new_n.inputs.add(), i_data)

def paste_ng_from_dict(ng_list, data):
    """Append a node group to `ng_list`. If the list already has that group, the new entry keeps its nodes but
    gets a blank group name (to be re-pointed at another group) instead of creating a duplicate."""
    group = data.get("group", "")
    if any(ng.group_name == group for ng in ng_list): group = ""
    with raw_edits():
        new_ng = ng_list.add()
        new_ng.group_name = group
        new_ng.sub_path = data.get("sub_path", "")
        new_ng.tag = data.get("tag", "")
        for n_data in data.get("nodes", []): paste_node_from_dict(new_ng.nodes.add(), n_data)

def paste_obj_from_dict(new_o, data):
    new_o.name = data.get("name", "")
    new_o.name_override = data.get("name_override", "")
    new_o.export = data.get("export", True)
    new_o.tag = data.get("tag", "")
    new_o.sub_path = data.get("sub_path", "")
    for ng_data in data.get("nodegroups", []): paste_ng_from_dict(new_o.nodegroups, ng_data)

def paste_collection_from_dict(new_c, data):
    new_c.collection_name = data.get("collection_name", "")
    new_c.export = data.get("export", True)
    new_c.use_tag = data.get("use_tag", True)
    new_c.tag = data.get("tag", "")
    new_c.sub_path = data.get("sub_path", "")
    for o_data in data.get("objects", []): paste_obj_from_dict(new_c.objects.add(), o_data)
    for ng_data in data.get("nodegroups", []): paste_ng_from_dict(new_c.nodegroups, ng_data)

def paste_preset_from_dict(new_p, data, view_layer=None):
    """Fill `new_p` from a dict of copy_preset_to_dict. A preset saved before version 4 has no collection ticks: the
    view layer decided what it exported, so with `view_layer` (the one of an import) what it does not evaluate comes in
    unticked (untick_unevaluated), as a file of that version is migrated."""
    version = data.get("data_version", 0)
    data = upgrade_preset_dict(data)
    new_p.name = data.get("name", "Imported Preset")
    new_p.preset_prefix = data.get("preset_prefix", "")
    for c_data in data.get("collections", []): paste_collection_from_dict(new_p.collections.add(), c_data)
    for ng_data in data.get("nodegroups", []): paste_ng_from_dict(new_p.nodegroups, ng_data)
    if version < 4 and view_layer is not None: untick_unevaluated(new_p, live_collection_names(view_layer))


# --- Data versioning --------------------------------------------------------------------------------------------------

VALUE_PROPS = ('value_string', 'value_menu')

def sync_prev_values(scene):
    """The `prev_*` properties (what a rejected edit reverts to) are not stored in files saved before they existed:
    make them match the stored data."""
    def sync_groups(nodegroups):
        for ng in nodegroups:
            ng.prev_group_name = ng.group_name
            for n in ng.nodes:
                n.prev_name = n.name
                for inp in n.inputs:
                    inp.prev_name = inp.name
                    for v in inp.values:
                        for prop in VALUE_PROPS: setattr(v, "prev_" + prop, getattr(v, prop))

    sync_groups(scene.batch_stl_global_nodegroups)
    for preset in scene.batch_stl_presets:
        sync_groups(preset.nodegroups)
        for col in preset.collections:
            col.prev_collection_name = col.collection_name
            sync_groups(col.nodegroups)
            for obj in col.objects: sync_groups(obj.nodegroups)

# Version of the stored override data. A scene without a stored version predates versioning and is migrated on load.
# 1: the value folder name (dir_tag) is split from the filename tag (tag).
# 2: v1.0.0 typed values and sweeps become text; object entries drop `obj_ptr` (an ID pointer, which kept deleted
#    objects alive) for `obj_uid`; the UI state moves from the Scene to the WindowManager.
# 3: value naming fields (dir_tag, tag) hold templates with the value's place (VALUE_SLOT, legacy_naming_template).
# 4: collection entries have an export tick, and the ticks alone decide what is exported, not the view layer: what the
#    view layer did not evaluate comes in unticked (untick_unevaluated).
DATA_VERSION = 4

# Scene properties of the UI state before it moved to the WindowManager (version 2)
OLD_SCENE_UI_PROPS = ("batch_stl_ui_global_ovr_main", "batch_stl_ui_preset_ovr", "batch_stl_ui_global_ovr", "batch_stl_ui_local_ovr",
                      "batch_stl_ui_global_ovr_nested", "batch_stl_ui_local_ovr_nested", "batch_stl_ui_tips", "batch_stl_collapsed_dirs",
                      "batch_stl_info_tab", "batch_stl_info_global", "batch_stl_verbose_console")

def iter_scene_nodegroup_lists(scene):
    yield scene.batch_stl_global_nodegroups
    for preset in scene.batch_stl_presets:
        yield preset.nodegroups
        for col in preset.collections:
            yield col.nodegroups
            for obj in col.objects: yield obj.nodegroups

def iter_scene_inputs(scene):
    for nodegroups in iter_scene_nodegroup_lists(scene):
        for ng in nodegroups:
            for n in ng.nodes: yield from n.inputs

def del_stored_prop(owner, key):
    """Remove a stored value of a property this version no longer registers."""
    if key in owner.keys(): del owner[key]

def migrate_scene_data(scene):
    """Bring override data saved by older versions up to DATA_VERSION."""
    version = scene.batch_stl_data_version if scene.is_property_set("batch_stl_data_version") else 0
    if version >= DATA_VERSION: return
    with raw_edits():
        for inp in iter_scene_inputs(scene):
            for v in inp.values:
                # Before the split one tag named both the folder and the filename token
                if version < 1 and not v.dir_tag and v.tag: v.dir_tag = v.tag
                if version < 2:
                    # Only unversioned scenes can be v1.0.0 data, whose unedited typed fields were not stored
                    migrate_legacy_value(v, v.get, inp.override_type, fill_defaults=version < 1)
                    for key in LEGACY_VALUE_KEYS: del_stored_prop(v, key)
                if version < 3:
                    v.dir_tag = legacy_naming_template(v.dir_tag, "dir")
                    v.tag = legacy_naming_template(v.tag, "tag")
        if version < 2:
            for preset in scene.batch_stl_presets:
                for col in preset.collections:
                    for entry in col.objects: del_stored_prop(entry, "obj_ptr")
            for key in OLD_SCENE_UI_PROPS: del_stored_prop(scene, key)
        if version < 4:
            live = live_collection_names(migration_view_layer(scene))
            for preset in scene.batch_stl_presets: untick_unevaluated(preset, live)
        scene.batch_stl_data_version = DATA_VERSION

def migration_view_layer(scene):
    """The view layer a scene's exports were filtered by: the one a window shows it with (the first such window), else
    its first view layer."""
    for wm in bpy.data.window_managers:
        for window in wm.windows:
            if window.scene == scene: return window.view_layer
    return scene.view_layers[0] if scene.view_layers else None

def stamp_data_version(scene):
    """Scenes created in this session hold current data: record that, so a later load does not migrate them."""
    if not scene.is_property_set("batch_stl_data_version"): scene.batch_stl_data_version = DATA_VERSION

def prepare_scene(scene):
    """Bring the data of one scene up to date (after it was loaded or appended, or when the add-on is enabled)."""
    try:
        migrate_scene_data(scene)
        sync_prev_values(scene)
        restamp_object_uids(scene)
        ensure_preset_uids(scene)
    except Exception: traceback.print_exc()

def prepare_scenes():
    """Bring the data of every scene in the file up to date (after a load, or when the add-on is enabled)."""
    for scene in bpy.data.scenes: prepare_scene(scene)

@persistent
def batch_stl_import_handler(import_context, *args):
    """Scenes appended or linked from another file (Append, Link, `bpy.data.libraries.load`, dependencies included)
    hold that file's data, maybe of an older version: prepare them right away, so that an unstamped scene is always one
    created in this session (see batch_stl_save_handler). Linked scenes are migrated in memory like on load, which also
    keeps one made local later from being stamped unmigrated."""
    for item in getattr(import_context, "import_items", ()):
        if item.id_type == 'SCENE' and item.id: prepare_scene(item.id)

@persistent
def batch_stl_save_handler(*args):
    """Stamp the scenes created in this session before they are written, so the next load does not migrate their
    current data again. The UI timer only stamps the scene in view, and timers never run in background Blender: a
    scene filled by a script, or never viewed, would lose its naming on reload. Linked scenes are not written."""
    for scene in bpy.data.scenes:
        if not scene.library: stamp_data_version(scene)
