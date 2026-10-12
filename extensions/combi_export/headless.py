"""What runs in the headless worker process: the job manifest, applying and reverting overrides on the scene, and the
export loop (run_headless_export). The worker starts with WORKER_SCRIPT (headless_main.py)."""
import os
import json
import time
import sys

import bpy

from .nodes import (cached_menu_items, clean_node_name, get_modifier_input, get_modifier_socket_identifier,
    set_modifier_input)
from .engine import MockOverride, count_and_keep_combinations, generate_named_combinations, get_input_value
from .targets import export_file_parts, group_by_signature, iter_export_objects, live_collection_names
from .stl import collect_instance_arrays, export_object_stl

# Variants the worker keeps from counting for the export (about 2 KB each); past this many they are generated again
KEEP_VARIANTS = 20000

def reconstruct_overrides_for_combo(combo):
    grouped = {}
    for ovr, inp in combo:
        target_key = (ovr.override_target, ovr.parent_group_ptr, ovr.node_name, getattr(ovr, "level", "NONE"))
        grouped.setdefault(target_key, []).append(inp)
    return [MockOverride(tgt, ptr, name, inputs, lvl) for (tgt, ptr, name, lvl), inputs in grouped.items()]

def capture_baseline_states(overrides, target_objects):
    global_states, mod_states = [], []
    processed_node_sockets, processed_mod_sockets = set(), set()

    for ovr in overrides:
        if ovr.override_target == 'NODE' and ovr.parent_group_ptr and ovr.node_name:
            parent_tree = ovr.parent_group_ptr
            target_node = parent_tree.nodes.get(clean_node_name(ovr.node_name))
            if not target_node: continue
            for inp in ovr.inputs:
                socket = target_node.inputs.get(inp.input_name)
                if not socket: continue
                key = (parent_tree.name, target_node.name, inp.input_name)
                if key not in processed_node_sockets:
                    link_from = socket.links[0].from_socket if socket.is_linked else None
                    default_v = socket.default_value.copy() if hasattr(socket.default_value, "copy") else socket.default_value
                    global_states.append(('SOCKET', socket, default_v, link_from, parent_tree))
                    processed_node_sockets.add(key)

        elif ovr.override_target == 'MODIFIER' and ovr.parent_group_ptr:
            for inp in ovr.inputs:
                ident = get_modifier_socket_identifier(ovr.parent_group_ptr, inp.input_name)
                if not ident: continue
                for obj in target_objects:
                    for mod in obj.modifiers:
                        if mod.type == 'NODES' and mod.node_group == ovr.parent_group_ptr:
                            key = (obj.name, mod.name, ident)
                            orig_val = get_modifier_input(mod, ident)
                            if key not in processed_mod_sockets and orig_val is not None:
                                mod_states.append((mod, ident, orig_val))
                                processed_mod_sockets.add(key)
    return global_states, mod_states

_reported_failures = set()

def report_apply_failure(target, input_name, value, error):
    """Log a value Blender rejects (e.g. a menu item that no longer exists) once instead of exporting silently."""
    msg = f"WARNING: could not set {target} > {input_name} to {value!r} ({error}); the file keeps its current value"
    if msg not in _reported_failures:
        _reported_failures.add(msg)
        print(msg, flush=True)

def apply_overrides(overrides, target_objects):
    trees_to_update, objects_to_update = set(), set()
    for override in overrides:
        if override.override_target == 'NODE' and override.parent_group_ptr and override.node_name:
            parent_tree = override.parent_group_ptr
            target_node = parent_tree.nodes.get(clean_node_name(override.node_name))
            if not target_node: continue
            for inp in override.inputs:
                socket = target_node.inputs.get(inp.input_name)
                if not socket: continue
                if socket.is_linked: parent_tree.links.remove(socket.links[0])
                val = get_input_value(inp)
                if val is not None:
                    try:
                        if socket.default_value != val:
                            socket.default_value = val
                            trees_to_update.add(parent_tree)
                    except (TypeError, ValueError) as e: report_apply_failure(f"{parent_tree.name} > {target_node.name}", inp.input_name, val, e)

        elif override.override_target == 'MODIFIER' and override.parent_group_ptr:
            for inp in override.inputs:
                ident = get_modifier_socket_identifier(override.parent_group_ptr, inp.input_name)
                val = get_input_value(inp)
                if not ident or val is None: continue
                for obj in target_objects:
                    for mod in obj.modifiers:
                        if mod.type == 'NODES' and mod.node_group == override.parent_group_ptr and get_modifier_input(mod, ident) != val:
                            try: set_modifier_input(mod, ident, val)
                            except (TypeError, ValueError) as e:
                                report_apply_failure(f"{obj.name} > {mod.name}", inp.input_name, val, e)
                                continue
                            objects_to_update.add(obj)
    for tree in trees_to_update: tree.update_tag()
    # Setting modifier inputs from Python does not reliably re-evaluate the object, so tag it explicitly.
    for obj in objects_to_update: obj.update_tag()

def override_targets(overrides):
    """Keys of the sockets an override list writes, matching the baseline states revert_overrides() restores."""
    keys = set()
    for ovr in overrides:
        if not ovr.parent_group_ptr: continue
        for inp in ovr.inputs:
            if ovr.override_target == 'NODE':
                keys.add(('NODE', ovr.parent_group_ptr.name, clean_node_name(ovr.node_name), inp.input_name))
            else:
                keys.add(('MODIFIER', ovr.parent_group_ptr.name, get_modifier_socket_identifier(ovr.parent_group_ptr, inp.input_name)))
    return keys

def revert_overrides(global_states, mod_states, target_objects, skip=frozenset()):
    """Restore the baseline values and links; sockets whose override_targets() key is in `skip` are left alone."""
    objects_to_update = set()
    for mod, ident, orig_val in mod_states:
        try:
            if skip and ('MODIFIER', mod.node_group.name, ident) in skip: continue
            if get_modifier_input(mod, ident) != orig_val:
                set_modifier_input(mod, ident, orig_val)
                objects_to_update.add(mod.id_data)
        except Exception: pass
    for obj in objects_to_update:
        try: obj.update_tag()
        except Exception: pass

    trees_to_update = set()
    for state in global_states:
        if state[0] == 'SOCKET':
            _, socket, original_val, link_from, parent_tree = state
            try:
                if skip and ('NODE', parent_tree.name, socket.node.name, socket.name) in skip: continue
                is_diff = (socket.default_value != original_val)
                if hasattr(is_diff, "__iter__"): is_diff = any(is_diff)
                if is_diff:
                    socket.default_value = original_val
                    trees_to_update.add(parent_tree)
                if link_from and not any(l.from_socket == link_from for l in socket.links):
                    parent_tree.links.new(link_from, socket)
                    trees_to_update.add(parent_tree)
            except Exception: pass

    for tree in trees_to_update:
        try: tree.update_tag()
        except Exception: pass

# The script the worker process starts with: it loads this package and calls run_headless_export
WORKER_SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "headless_main.py")

def write_job_file(path, scene, view_layer, preset, root_dir, skip_direct):
    """The job manifest run_headless_export reads: the preset (by uid) of `scene` to export, evaluated in `view_layer`
    (one of the scene's), to `root_dir`. skip_direct: the objects without overrides were already written."""
    with open(path, 'w', encoding="utf-8") as f:
        json.dump({"scene": scene.name, "view_layer": view_layer.name, "preset_uid": preset.uid, "root_dir": root_dir,
                   "start_time": time.time(), "skip_direct": skip_direct}, f)

def run_headless_export(job_file_path):
    try:
        with open(job_file_path, 'r', encoding="utf-8") as f: job_data = json.load(f)
        scene_name, view_layer_name, preset_uid = job_data["scene"], job_data["view_layer"], job_data["preset_uid"]
        root_dir, start_time_unix, skip_direct = job_data["root_dir"], job_data["start_time"], job_data["skip_direct"]
    except Exception as e:
        print(f"ERROR: Failed to load job manifest: {e}", flush=True)
        sys.exit(1)

    # The scene and view layer the export was started from. A background load opens the scene of the saved file's
    # first window, which may be another one (e.g. a second window showing another scene).
    scene = bpy.data.scenes.get(scene_name)
    view_layer = scene.view_layers.get(view_layer_name) if scene else None
    if view_layer is None:
        print(f"ERROR: View layer '{view_layer_name}' of scene '{scene_name}' not found", flush=True)
        sys.exit(1)
    preset = next((p for p in scene.batch_stl_presets if p.uid == preset_uid), None) if preset_uid else None
    if preset is None:
        print("ERROR: Preset not found", flush=True)
        sys.exit(1)
    # Show them in the window too, so that the context (e.g. scripted drivers) matches. The scene first: switching
    # scenes resets the window's view layer.
    window = bpy.context.window
    if window:
        window.scene = scene
        window.view_layer = view_layer

    print("\n  [Phase 0] Evaluating Targets and Building Depsgraph Culling Maps...", flush=True)
    t_phase0_start = time.perf_counter()

    # Objects whose effective overrides are identical share one batch (one set of variants, one depsgraph pass).
    # Objects without overrides were already written by the main process (skip_direct).
    targets = iter_export_objects(scene, preset, live_collection_names(view_layer))
    batches = group_by_signature(t for t in targets if t[4] or not skip_direct)

    layer_collection_map, layer_collection_parents = {}, {}
    def map_layer_collections(lc, parent=None):
        if lc.collection:
            layer_collection_map[lc.collection.name] = lc
            layer_collection_parents[lc.collection.name] = parent
        for child in lc.children: map_layer_collections(child, lc)
    map_layer_collections(view_layer.layer_collection)

    print(f"    ├─ Mapped {len(layer_collection_map)} collections for depsgraph culling in {time.perf_counter() - t_phase0_start:.4f}s", flush=True)

    if not batches:
        print("  └─ No active objects to export.\nBATCH_STL_DONE", flush=True)
        sys.exit(0)

    # The progress total needs every batch's count first. Variants that only enumerating counts are kept from that pass
    # (up to KEEP_VARIANTS in all) for the export below.
    batch_variants, keep = {}, KEEP_VARIANTS
    with cached_menu_items():
        for sig, (ovrs, _items) in batches.items():
            batch_variants[sig] = count_and_keep_combinations(ovrs, keep)
            keep -= len(batch_variants[sig][1] or ())
    total_ops = sum(len(items) * batch_variants[sig][0] for sig, (_ovrs, items) in batches.items())
    print(f"BATCH_STL_TOTAL:{total_ops}", flush=True)

    current_op_step, batch_counter, first_export_started = 0, 1, False

    for signature, (all_overrides, batch_items) in batches.items():
        num_combinations, variants = batch_variants.pop(signature)
        if variants is None: variants = generate_named_combinations(all_overrides)
        batch_objects = {item[2] for item in batch_items}

        isolated_collections = []
        if len(all_overrides) > 0:
            batch_col_names = {col.name for item in batch_items for col in item[2].users_collection}
            visible_hierarchy = set()
            for c_name in batch_col_names:
                curr = c_name
                while curr in layer_collection_map:
                    visible_hierarchy.add(curr)
                    parent_lc = layer_collection_parents.get(curr)
                    curr = parent_lc.collection.name if (parent_lc and parent_lc.collection) else None
            for name, lc in layer_collection_map.items():
                if name not in visible_hierarchy and not lc.exclude:
                    lc.exclude = True
                    isolated_collections.append(name)

        baseline_global_states, baseline_mod_states = capture_baseline_states(all_overrides, batch_objects)

        try:
            for combo_idx, (combo, tags_by_level, paths_by_level) in enumerate(variants):
                t_perm_start = time.perf_counter()
                if not first_export_started:
                    print(f"=== Headless init took {time.time() - start_time_unix:.2f} s to start first export ===", flush=True)
                    first_export_started = True

                # A parameter left out of this variant (no value applies to its branch) must be back at its baseline,
                # not keep what the previous variant set.
                combo_overrides = reconstruct_overrides_for_combo(combo)
                revert_overrides(baseline_global_states, baseline_mod_states, batch_objects, skip=override_targets(combo_overrides))
                apply_overrides(combo_overrides, batch_objects)
                view_layer.update()
                depsgraph = view_layer.depsgraph
                instance_arrays = collect_instance_arrays(depsgraph, batch_objects)

                for c, obj_prop, bl_obj in batch_items:
                    full_dir_parts, filename = export_file_parts(preset, c, obj_prop, bl_obj, tags_by_level, paths_by_level)
                    out_dir = os.path.normpath(os.path.join(root_dir, *full_dir_parts)) if full_dir_parts else root_dir
                    filepath = os.path.join(out_dir, filename)

                    result_text = export_object_stl(filepath, bl_obj, depsgraph, instance_arrays.get(bl_obj.name_full, ()))

                    print(f"{preset.name} | {c.collection_name} | {bl_obj.name} | Permutation {combo_idx + 1}/{num_combinations} | Batch {batch_counter}/{len(batches)}\n  └─ {result_text} | {time.perf_counter() - t_perm_start:.2f} s", flush=True)
                    current_op_step += 1
                    print(f"BATCH_STL_PROGRESS:{current_op_step}", flush=True)

        finally:
            revert_overrides(baseline_global_states, baseline_mod_states, batch_objects)
            for name in isolated_collections:
                if name in layer_collection_map: layer_collection_map[name].exclude = False
            view_layer.update()

        batch_counter += 1

    print("BATCH_STL_DONE", flush=True)
    sys.exit(0)
