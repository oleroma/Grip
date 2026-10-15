"""Editing operators: JSON import / export, list actions with the internal clipboard, override table actions, tree
expansion and the merge info bar."""
import os
import json

import bpy
from bpy_extras.io_utils import ExportHelper, ImportHelper

from .common import inside_operator, mark_dirty, overrides_open_prop, raw_edits, _held_keys, _ui_cache
from .nodes import clean_node_name, get_menu_switch_items, get_supported_inputs, get_target_node_names
from .fields import add_value, name_permutations, same_fields, value_fields
from .engine import MockInput, MockOverride, parse_sweep_values
from .data import (copy_collection_to_dict, copy_ng_to_dict, copy_preset_to_dict, copy_setup_to_dict,
    ensure_preset_uids, get_active_collection, get_active_object, get_active_preset, get_job,
    paste_collection_from_dict, paste_ng_from_dict, paste_preset_from_dict, remove_job, upgrade_nodegroup_dicts)
from .ui_cache import (expand_last_dirs, is_dir_collapsed, iter_tree_dirs, load_toggled_dirs, save_toggled_dirs,
    set_dir_collapsed)

_clipboard = {"preset": None, "collection": None, "nodegroup": None}


class BATCH_STL_OT_export_presets_json(bpy.types.Operator, ExportHelper):
    bl_idname = "batch_stl.export_presets_json"
    bl_label = "Export JSON"
    bl_description = "Export all presets, the global overrides and the root folder to a JSON file"
    filename_ext = ".json"
    filter_glob: bpy.props.StringProperty(default="*.json", options={'HIDDEN'})
    def execute(self, context):
        try:
            with open(self.filepath, 'w', encoding="utf-8") as f:
                json.dump(copy_setup_to_dict(context.scene), f, indent=4)
            self.report({'INFO'}, f"Presets exported to {os.path.basename(self.filepath)}")
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"Failed to export presets: {e}")
            return {'CANCELLED'}

class BATCH_STL_OT_import_presets_json(bpy.types.Operator, ImportHelper):
    bl_idname = "batch_stl.import_presets_json"
    bl_label = "Import JSON"
    bl_description = "Add the presets of a JSON file, and take its global overrides and root folder"
    bl_options = {'REGISTER', 'UNDO'}
    filename_ext = ".json"
    filter_glob: bpy.props.StringProperty(default="*.json", options={'HIDDEN'})
    # The scene has one of each, so taking the file's replaces the scene's. Files from before they were exported have
    # neither and leave the scene's alone.
    use_global_overrides: bpy.props.BoolProperty(name="Global Overrides", default=True, description=(
        "Replace the scene's global overrides with the ones in the file. They apply to every preset, so with them the "
        "imported presets write the same files as where they were exported"))
    use_root_dir: bpy.props.BoolProperty(name="Root Folder", default=True, description="Set the scene's root folder to the one in the file")

    @inside_operator
    def execute(self, context):
        scene = context.scene
        presets, global_ngs = scene.batch_stl_presets, scene.batch_stl_global_nodegroups
        before, old_root, old_global = len(presets), scene.batch_stl_root_dir, None
        try:
            with open(self.filepath, 'r', encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list): data = {"presets": data}  # a file of an earlier version: the presets only
            if not isinstance(data, dict) or not isinstance(data.get("presets"), list):
                self.report({'ERROR'}, "Invalid JSON: expected the presets of a Combi Export file.")
                return {'CANCELLED'}
            for p_data in data["presets"]:
                paste_preset_from_dict(presets.add(), p_data, context.view_layer)
            taken = []
            if self.use_global_overrides and isinstance(data.get("global_nodegroups"), list):
                old_global = [copy_ng_to_dict(ng) for ng in global_ngs]
                upgrade_nodegroup_dicts(data["global_nodegroups"], data.get("data_version", 0))
                global_ngs.clear()
                for ng_data in data["global_nodegroups"]: paste_ng_from_dict(global_ngs, ng_data)
                taken.append("global overrides")
            if self.use_root_dir and isinstance(data.get("root_dir"), str):
                scene.batch_stl_root_dir = data["root_dir"]
                taken.append("root folder")
            ensure_preset_uids(scene)
            self.report({'INFO'}, f"Presets imported from {os.path.basename(self.filepath)}" + (f", with its {' and '.join(taken)}" if taken else ""))
        except Exception as e:
            while len(presets) > before: presets.remove(len(presets) - 1)
            if old_global is not None:
                global_ngs.clear()
                for ng_data in old_global: paste_ng_from_dict(global_ngs, ng_data)
            scene.batch_stl_root_dir = old_root
            self.report({'ERROR'}, f"Failed to import presets: {e}")
            return {'CANCELLED'}
        mark_dirty()
        return {'FINISHED'}

class BATCH_STL_OT_clear_console(bpy.types.Operator):
    bl_idname = "batch_stl.clear_console"
    bl_label = "Clear Console"
    bl_description = "Clear console logs for the current view"
    def execute(self, context):
        job = get_job(get_active_preset(context.scene))
        if job: job.console_logs.clear()
        return {'FINISHED'}

class ListActionHandler:
    """Utility class to handle standardized ADD/REMOVE/UP/DOWN/COPY/PASTE operations for UI lists."""
    @staticmethod
    def perform_action(action, lst, index, shift_pressed, clipboard_key, copy_func, paste_func):
        new_index = index
        if action == 'ADD':
            lst.add()
            new_index = len(lst) - 1
        elif action == 'REMOVE' and lst:
            if 0 <= index < len(lst):
                lst.remove(index)
                new_index = max(0, min(index, len(lst) - 1))
        elif action == 'UP' and 0 < index < len(lst):
            target = 0 if shift_pressed else index - 1
            lst.move(index, target)
            new_index = target
        elif action == 'DOWN' and 0 <= index < len(lst) - 1:
            target = len(lst) - 1 if shift_pressed else index + 1
            lst.move(index, target)
            new_index = target
        elif action == 'COPY' and lst and 0 <= index < len(lst):
            _clipboard[clipboard_key] = copy_func(lst[index])
        elif action == 'PASTE' and _clipboard.get(clipboard_key):
            paste_func(lst.add(), _clipboard[clipboard_key])
            new_index = len(lst) - 1
        return new_index

class BATCH_STL_OT_preset_actions(bpy.types.Operator):
    bl_idname = "batch_stl.preset_actions"
    bl_label = "Preset Actions"
    bl_options = {'UNDO', 'INTERNAL'}  # no REGISTER: hides the "Adjust Last Operation" redo panel
    action: bpy.props.EnumProperty(items=(('ADD', "", ""), ('REMOVE', "", ""), ('UP', "", ""), ('DOWN', "", ""), ('COPY', "", ""), ('PASTE', "", "")))
    shift_pressed: bpy.props.BoolProperty(options={'HIDDEN', 'SKIP_SAVE'}, default=False)

    @classmethod
    def description(cls, context, properties):
        act = properties.action
        if act == 'ADD': return "Add new preset"
        if act == 'REMOVE': return "Remove active preset"
        if act == 'UP': return "Move preset up (Shift: Move to top)"
        if act == 'DOWN': return "Move preset down (Shift: Move to bottom)"
        if act == 'COPY': return "Copy active preset"
        if act == 'PASTE': return "Paste preset from clipboard"
        return "Preset action"

    def invoke(self, context, event):
        self.shift_pressed = event.shift
        return self.execute(context)

    @inside_operator
    def execute(self, context):
        scene = context.scene
        lst = scene.batch_stl_presets
        idx = scene.batch_stl_preset_index
        # Jobs are keyed by preset uid, so reordering is safe while an export runs; removing the exporting preset is not.
        removed = lst[idx] if self.action == 'REMOVE' and 0 <= idx < len(lst) else None
        removed_job = get_job(removed)

        if removed_job and removed_job.is_exporting:
            self.report({'WARNING'}, "Cannot remove a preset while it is exporting.")
        else:
            if removed_job: remove_job(scene.session_uid, removed.uid)  # its log
            scene.batch_stl_preset_index = ListActionHandler.perform_action(
                self.action, lst, idx, self.shift_pressed, "preset", copy_preset_to_dict, paste_preset_from_dict
            )
            ensure_preset_uids(scene)  # added and pasted presets

        mark_dirty()
        return {'FINISHED'}

class BATCH_STL_OT_collection_actions(bpy.types.Operator):
    bl_idname = "batch_stl.collection_actions"
    bl_label = "Collection Actions"
    bl_options = {'UNDO', 'INTERNAL'}
    action: bpy.props.EnumProperty(items=(('ADD', "", ""), ('REMOVE', "", ""), ('UP', "", ""), ('DOWN', "", ""), ('COPY', "", ""), ('PASTE', "", "")))
    shift_pressed: bpy.props.BoolProperty(options={'HIDDEN', 'SKIP_SAVE'}, default=False)

    @classmethod
    def description(cls, context, properties):
        act = properties.action
        if act == 'ADD': return "Add new collection target"
        if act == 'REMOVE': return "Remove active collection"
        if act == 'UP': return "Move collection up (Shift: Move to top)"
        if act == 'DOWN': return "Move collection down (Shift: Move to bottom)"
        if act == 'COPY': return "Copy active collection target"
        if act == 'PASTE': return "Paste collection target from clipboard"
        return "Collection action"

    def invoke(self, context, event):
        self.shift_pressed = event.shift
        return self.execute(context)

    @inside_operator
    def execute(self, context):
        preset = get_active_preset(context.scene)
        if not preset: return {'CANCELLED'}

        preset.collection_index = ListActionHandler.perform_action(
            self.action, preset.collections, preset.collection_index, self.shift_pressed, "collection", copy_collection_to_dict, paste_collection_from_dict
        )

        mark_dirty()
        return {'FINISHED'}

class BATCH_STL_OT_table_action(bpy.types.Operator):
    bl_idname = "batch_stl.table_action"
    bl_label = "Override Action"
    bl_options = {'UNDO', 'INTERNAL'}

    action: bpy.props.StringProperty()
    is_global: bpy.props.BoolProperty(default=False)
    is_preset: bpy.props.BoolProperty(default=False)
    is_collection: bpy.props.BoolProperty()
    c_idx: bpy.props.IntProperty(default=-1)
    o_idx: bpy.props.IntProperty(default=-1)
    ng_idx: bpy.props.IntProperty(default=-1)
    n_idx: bpy.props.IntProperty(default=-1)
    i_idx: bpy.props.IntProperty(default=-1)
    v_idx: bpy.props.IntProperty(default=-1)
    shift_pressed: bpy.props.BoolProperty(options={'HIDDEN', 'SKIP_SAVE'}, default=False)

    @classmethod
    def description(cls, context, properties):
        act = properties.action
        if act == 'ADD_GROUP': return "Add an Override Group to this level"
        if act == 'REMOVE_GROUP': return "Remove this empty Override Group (a group with a name is deleted by clearing its name field)"
        if act == 'CLEAR_GROUPS': return "Clear the overrides: remove every Override Group of this level"
        if act == 'COPY_GROUP': return "Copy this Override Group to clipboard"
        if act == 'PASTE_GROUP': return "Paste an Override Group from clipboard"
        if act == 'MOVE_GROUP_UP': return "Move group up (Shift: Move directly to parent hierarchy level)"
        if act == 'MOVE_GROUP_DOWN': return "Move group down (Shift: Localize and copy group to every nested child)"
        if act == 'ADD_NODE': return "Add a Target Node filter"
        if act == 'MOVE_NODE_UP': return "Move Target Node up"
        if act == 'MOVE_NODE_DOWN': return "Move Target Node down"
        if act == 'ADD_INPUT': return "Add an Input Parameter override (Shift: Auto-populate all available socket inputs)"
        if act == 'VALUE_ACTION': return "Add Permutation (Shift: Toggle Sweep range mode)"
        if act == 'TOGGLE_COLLECTION_USE_TAG': return "Toggle collection-level filename prefix/suffix tag"
        return "Perform structural table action"

    def invoke(self, context, event):
        self.shift_pressed = event.shift
        return self.execute(context)

    def _resolve_context_list(self, context, preset):
        if self.is_global: return context.scene.batch_stl_global_nodegroups
        elif self.is_preset: return preset.nodegroups

        active_col = get_active_collection(preset)
        if not active_col: return None
        if self.is_collection: return active_col.nodegroups

        active_obj = get_active_object(active_col)
        return active_obj.nodegroups if active_obj else None

    def _show_table(self, context):
        """Open the table of this level, collapsed it would hide the group that was just added."""
        setattr(context.window_manager, overrides_open_prop(self.is_collection, self.is_preset, self.is_global), True)

    def _handle_group_action(self, ng_list, context, preset):
        if self.action == 'ADD_GROUP':
            ng_list.add()
            self._show_table(context)
        elif self.action == 'REMOVE_GROUP' and 0 <= self.ng_idx < len(ng_list):
            ng_list.remove(self.ng_idx)
        elif self.action == 'CLEAR_GROUPS':
            ng_list.clear()
        elif self.action == 'COPY_GROUP' and 0 <= self.ng_idx < len(ng_list):
            _clipboard["nodegroup"] = copy_ng_to_dict(ng_list[self.ng_idx])
        elif self.action == 'PASTE_GROUP' and _clipboard.get("nodegroup"):
            paste_ng_from_dict(ng_list, _clipboard["nodegroup"])
            self._show_table(context)
        elif self.action == 'MOVE_GROUP_UP' and 0 <= self.ng_idx < len(ng_list):
            if self.shift_pressed:
                src_ng = ng_list[self.ng_idx]
                dst = None
                if self.is_preset: dst = context.scene.batch_stl_global_nodegroups
                elif self.is_collection: dst = preset.nodegroups
                elif not self.is_global:
                    col = get_active_collection(preset)
                    dst = col.nodegroups if col else None
                if dst is not None:
                    paste_ng_from_dict(dst, copy_ng_to_dict(src_ng))
                    ng_list.remove(self.ng_idx)
            elif self.ng_idx > 0: ng_list.move(self.ng_idx, self.ng_idx - 1)
        elif self.action == 'MOVE_GROUP_DOWN' and 0 <= self.ng_idx < len(ng_list):
            if self.shift_pressed:
                src_ng = ng_list[self.ng_idx]
                copied_data = copy_ng_to_dict(src_ng)
                pushed = False
                if self.is_global:
                    for p in context.scene.batch_stl_presets:
                        paste_ng_from_dict(p.nodegroups, copied_data)
                        pushed = True
                elif self.is_preset:
                    for c in preset.collections:
                        paste_ng_from_dict(c.nodegroups, copied_data)
                        pushed = True
                elif self.is_collection:
                    col = get_active_collection(preset)
                    if col:
                        for o in col.objects:
                            paste_ng_from_dict(o.nodegroups, copied_data)
                            pushed = True
                if pushed:
                    ng_list.remove(self.ng_idx)
            elif self.ng_idx < len(ng_list) - 1:
                ng_list.move(self.ng_idx, self.ng_idx + 1)

    def _handle_node_action(self, ng_list):
        if not (0 <= self.ng_idx < len(ng_list)): return
        nodes = ng_list[self.ng_idx].nodes
        if self.action == 'ADD_NODE':
            ng_ptr = bpy.data.node_groups.get(ng_list[self.ng_idx].group_name)
            # Only targets with sockets left to override: the <Modifier Interface> fallback would add one more entry
            # to a group that has none left
            valid_targets = get_target_node_names(ng_ptr, {clean_node_name(n.name) for n in nodes}, fallback=False)
            if valid_targets:
                nodes.add().name = valid_targets[0]
        elif self.action == 'MOVE_NODE_UP' and 0 < self.n_idx < len(nodes):
            nodes.move(self.n_idx, self.n_idx - 1)
        elif self.action == 'MOVE_NODE_DOWN' and 0 <= self.n_idx < len(nodes) - 1:
            nodes.move(self.n_idx, self.n_idx + 1)

    def _handle_input_action(self, ng_list):
        if not (0 <= self.ng_idx < len(ng_list)): return
        ng = ng_list[self.ng_idx]
        if not (0 <= self.n_idx < len(ng.nodes)): return
        node = ng.nodes[self.n_idx]
        inputs = node.inputs
        if self.action == 'ADD_INPUT':
            ng_ptr = bpy.data.node_groups.get(ng.group_name)
            source_inputs = get_supported_inputs(ng_ptr, node.name)

            existing = {i.name for i in node.inputs}

            if self.shift_pressed and source_inputs:
                for s_name in source_inputs:
                    if s_name and s_name not in existing:
                        inp = node.inputs.add()
                        add_value(inp.values)
                        inp.name = s_name
                return

            if source_inputs:
                for s_name in source_inputs:
                    if s_name and s_name not in existing:
                        inp = inputs.add()
                        add_value(inp.values)
                        inp.name = s_name
                        break
            else:
                add_value(inputs.add().values)

    def _handle_value_action(self, ng_list):
        if not (0 <= self.ng_idx < len(ng_list)): return
        ng = ng_list[self.ng_idx]
        if not (0 <= self.n_idx < len(ng.nodes)): return
        node = ng.nodes[self.n_idx]
        if not (0 <= self.i_idx < len(node.inputs)): return
        inp_obj = node.inputs[self.i_idx]
        vals = inp_obj.values
        if self.action == 'VALUE_ACTION':
            def add_smart_value():
                if inp_obj.override_type == 'BOOLEAN':
                    existing = {v.value_menu for v in vals if not v.use_sweep}
                    if 'True' not in existing:
                        v = add_value(vals)
                        v.value_menu = 'True'
                        return v
                    elif 'False' not in existing:
                        v = add_value(vals)
                        v.value_menu = 'False'
                        return v
                    return None
                elif inp_obj.override_type == 'MENU':
                    ng_ptr = bpy.data.node_groups.get(ng.group_name)
                    items = get_menu_switch_items(ng_ptr, node.name, inp_obj.name) if ng_ptr else []
                    existing = {v.value_menu for v in vals if not v.use_sweep}
                    for item in items:
                        if item not in existing:
                            v = add_value(vals)
                            v.value_menu = item
                            return v
                    return None
                elif inp_obj.override_type in ('FLOAT', 'INT'):
                    existing = []
                    for v in vals:
                        if not v.use_sweep:
                            try:
                                existing.append(float(v.value_string))
                            except ValueError:
                                pass
                    v = add_value(vals)
                    if existing:
                        new_val = max(existing) + 1
                        v.value_string = str(int(new_val) if inp_obj.override_type == 'INT' else round(new_val, 4))
                    return v
                elif inp_obj.override_type == 'STRING':
                    # A blank string is invalid and would duplicate the previous blank one: fill it in first.
                    if any(not v.use_sweep and v.value_string == "" for v in vals): return None
                    return add_value(vals)
                else:
                    return add_value(vals)

            def add_permutation():
                # A second value makes the input permute: see name_permutations
                if add_smart_value() is not None and len(vals) > 1: name_permutations(vals, len(vals) - 1)

            if self.v_idx < 0:
                add_permutation()
            elif 0 <= self.v_idx < len(vals):
                val = vals[self.v_idx]
                if not val.use_sweep:
                    if self.shift_pressed:
                        val.use_sweep = True
                        for j in reversed(range(len(vals))):
                            if j != self.v_idx: vals.remove(j)
                        name_permutations(vals, 0)
                    else:
                        add_permutation()
                else:
                    val.use_sweep = False
                    if self.shift_pressed and inp_obj.override_type in ['FLOAT', 'INT', 'MENU', 'BOOLEAN', 'STRING']:
                        ng_obj = ng_list[self.ng_idx]
                        ng_ptr = bpy.data.node_groups.get(ng_obj.group_name)
                        node_obj = ng_obj.nodes[self.n_idx]
                        target = 'MODIFIER' if not node_obj.name or node_obj.name == "<Modifier Interface>" else 'NODE'
                        temp_inp = MockInput(inp_obj, val, is_temp=True)
                        # An empty value (unknown menu items, empty string range) would delete the value it is written to
                        parsed_vals = [x for x in parse_sweep_values(MockOverride(target, ng_ptr, node_obj.name, [temp_inp]), temp_inp) if x != ""]
                        if parsed_vals:
                            # A step that repeats another value of the input, or an earlier step (a step of 0 in
                            # imported data), is left out: written, it would be rejected as a duplicate and stay blank
                            override_type = inp_obj.override_type
                            prop = "value_menu" if override_type in ('MENU', 'BOOLEAN') else "value_string"
                            taken = [f for f in (value_fields(o, override_type) for o in vals if o != val and not o.use_sweep) if f]
                            new = []
                            for p_val in parsed_vals:
                                fields = {"use_sweep": False, prop: str(p_val)}
                                if not any(same_fields(override_type, f, fields) for f in taken + new): new.append(fields)
                            # Generated values inherit the sweep's naming. Read first: add() and remove() can move the
                            # items in memory, so `val` is looked up again
                            naming = val.use_dir, val.dir_tag, val.use_tag, val.tag
                            if not new: vals.remove(self.v_idx)  # every step is a value already
                            with raw_edits():
                                for p_idx, fields in enumerate(new):
                                    v = vals[self.v_idx] if p_idx == 0 else vals.add()
                                    v.use_sweep = False
                                    v.use_dir, v.dir_tag, v.use_tag, v.tag = naming
                                    setattr(v, prop, fields[prop])

    @inside_operator
    def execute(self, context):
        preset = get_active_preset(context.scene)
        if not preset: return {'CANCELLED'}

        try:
            if self.action == 'TOGGLE_COLLECTION_USE_TAG':
                if 0 <= self.c_idx < len(preset.collections): preset.collections[self.c_idx].use_tag = not preset.collections[self.c_idx].use_tag
            else:
                ng_list = self._resolve_context_list(context, preset)
                if ng_list is None: return {'CANCELLED'}

                if 'GROUP' in self.action: self._handle_group_action(ng_list, context, preset)
                elif 'NODE' in self.action: self._handle_node_action(ng_list)
                elif 'INPUT' in self.action: self._handle_input_action(ng_list)
                elif 'VALUE' in self.action: self._handle_value_action(ng_list)
        except IndexError:
            self.report({'WARNING'}, "UI Sync Error: List mutated unexpectedly. Please try again.")
            return {'CANCELLED'}

        mark_dirty()
        return {'FINISHED'}

class BATCH_STL_OT_toggle_dir_tree(bpy.types.Operator):
    bl_idname = "batch_stl.toggle_dir_tree"
    bl_label = "Toggle Directory Tree"
    bl_options = {'INTERNAL'}
    bl_description = "Toggle directory tree expansion (Shift: also expand/collapse all child directories)"
    dir_path: bpy.props.StringProperty()
    recursive: bpy.props.BoolProperty(options={'HIDDEN', 'SKIP_SAVE'}, default=False)

    def invoke(self, context, event):
        self.recursive = event.shift
        return self.execute(context)

    def execute(self, context):
        wm = context.window_manager
        toggled = load_toggled_dirs(wm)
        subtree = []
        if self.recursive:
            subtree = [(p, is_root) for p, _node, is_root in iter_tree_dirs(_ui_cache["tree"][0])
                       if p == self.dir_path or p.startswith(self.dir_path + "/")]
        clicked = next((is_root for p, is_root in subtree if p == self.dir_path), None)
        if clicked is not None:
            # The clicked folder flips and every folder below it follows its new state.
            collapse = not is_dir_collapsed(toggled, self.dir_path, clicked)
            for p, is_root in subtree: set_dir_collapsed(toggled, p, is_root, collapse)
        elif self.dir_path in toggled: toggled.discard(self.dir_path)
        else: toggled.add(self.dir_path)
        save_toggled_dirs(wm, toggled)
        return {'FINISHED'}

class BATCH_STL_OT_tree_expansion(bpy.types.Operator):
    bl_idname = "batch_stl.tree_expansion"
    bl_label = "Directory Tree Expansion"
    bl_options = {'INTERNAL'}
    mode: bpy.props.EnumProperty(items=(('EXPAND_ALL', "", ""), ('COLLAPSE_ALL', "", ""), ('EXPAND_LAST', "", "")))

    @classmethod
    def description(cls, context, properties):
        if properties.mode == 'EXPAND_ALL': return "Expand all directories"
        if properties.mode == 'COLLAPSE_ALL': return "Collapse all directories"
        return "Collapse all, then expand the last subdirectory of every directory"

    def execute(self, context):
        wm = context.window_manager
        tree = _ui_cache["tree"][0]
        toggled = load_toggled_dirs(wm)
        if self.mode == 'EXPAND_LAST':
            for p, _node, is_root in iter_tree_dirs(tree):
                set_dir_collapsed(toggled, p, is_root, True)
            expand_last_dirs(tree, toggled)
        else:
            collapse = self.mode == 'COLLAPSE_ALL'
            for p, _node, is_root in iter_tree_dirs(tree):
                set_dir_collapsed(toggled, p, is_root, collapse)
        save_toggled_dirs(wm, toggled)
        return {'FINISHED'}

class BATCH_STL_OT_merge_info(bpy.types.Operator):
    """Highlight bar of an override block that merges into an upstream folder; the tooltip explains the merge."""
    bl_idname = "batch_stl.merge_info"
    bl_label = "Merged Branch"
    bl_options = {'INTERNAL'}
    info: bpy.props.StringProperty(options={'HIDDEN', 'SKIP_SAVE'})

    @classmethod
    def description(cls, context, properties):
        return properties.info

    def execute(self, context):
        return {'CANCELLED'}

class BATCH_STL_OT_collection_note(bpy.types.Operator):
    """Icon on a ticked collection that the view layer does not evaluate; the tooltip says it is exported all the same."""
    bl_idname = "batch_stl.collection_note"
    bl_label = "Collection Note"
    bl_options = {'INTERNAL'}
    info: bpy.props.StringProperty(options={'HIDDEN', 'SKIP_SAVE'})

    @classmethod
    def description(cls, context, properties):
        return properties.info

    def execute(self, context):
        return {'CANCELLED'}

class BATCH_STL_OT_read_modifiers(bpy.types.Operator):
    """Records the modifier keys of the window's event state, for a property setter (ctrl_held)."""
    bl_idname = "batch_stl.read_modifiers"
    bl_label = "Read Modifier Keys"
    bl_options = {'INTERNAL'}

    def invoke(self, context, event):
        _held_keys["ctrl"] = event.ctrl
        return {'CANCELLED'}

classes = (BATCH_STL_OT_export_presets_json, BATCH_STL_OT_import_presets_json, BATCH_STL_OT_clear_console,
           BATCH_STL_OT_preset_actions, BATCH_STL_OT_collection_actions, BATCH_STL_OT_table_action,
           BATCH_STL_OT_toggle_dir_tree, BATCH_STL_OT_tree_expansion, BATCH_STL_OT_merge_info, BATCH_STL_OT_collection_note,
           BATCH_STL_OT_read_modifiers)
