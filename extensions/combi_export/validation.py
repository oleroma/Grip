"""Checks that override entries still match their node trees and hold valid values. An invalid setup is flagged in the
table and blocks the export."""
import bpy

from .nodes import SUPPORTED_OVERRIDE_TYPES, clean_node_name, find_interface_input, get_menu_switch_items
from .fields import number_sweep_values, parse_number, steps_differ, string_sweep_values

def is_override_group_valid(ng):
    if not ng.group_name or not bpy.data.node_groups.get(ng.group_name):
        return False
    return True

def is_override_node_valid(ng_ptr, node):
    if not node.name or node.name == "<Modifier Interface>":
        return True
    if not ng_ptr:
        return False
    return clean_node_name(node.name) in ng_ptr.nodes

def is_override_input_valid(ng_ptr, node, inp):
    if not inp.name or not ng_ptr:
        return False
    is_mod = not node.name or node.name == "<Modifier Interface>"
    if is_mod:
        return find_interface_input(ng_ptr, inp.name) is not None
    target_n = ng_ptr.nodes.get(clean_node_name(node.name))
    if not target_n:
        return False
    return inp.name in target_n.inputs

def is_override_val_valid(inp, val, ng_ptr=None, node=None):
    if val is None or inp.override_type not in SUPPORTED_OVERRIDE_TYPES:
        return False
    if getattr(val, "use_sweep", False):
        if inp.override_type in ('FLOAT', 'INT'):
            # Numbers, 1 to MAX_SWEEP_STEPS steps, and no value twice (a step of 0)
            try: number_sweep_values(val.sweep_start, val.sweep_step, val.sweep_count, inp.override_type)
            except ValueError: return False
            return True
        elif inp.override_type == 'STRING':
            strings = string_sweep_values(val.sweep_range)
            return bool(strings) and steps_differ(strings)
        return True
    if inp.override_type in ('FLOAT', 'INT'):
        # get_input_value() would silently export an empty or malformed number as 0
        try: parse_number(val.value_string, inp.override_type)
        except ValueError: return False
        return True
    if inp.override_type == 'STRING':
        return bool(val.value_string and val.value_string.strip())
    elif inp.override_type == 'MENU':
        if not (val.value_menu and val.value_menu.strip()):
            return False
        if ng_ptr and node:
            valid_items = get_menu_switch_items(ng_ptr, node.name, inp.name)
            if valid_items and val.value_menu not in valid_items:
                return False
        return True
    return True

def validate_overrides(nodegroups):
    for ng in nodegroups:
        if not is_override_group_valid(ng):
            return False
        ng_ptr = bpy.data.node_groups.get(ng.group_name)
        for node in ng.nodes:
            if not is_override_node_valid(ng_ptr, node):
                return False
            for inp in node.inputs:
                if not is_override_input_valid(ng_ptr, node, inp):
                    return False
                if not inp.values:
                    return False
                for val in inp.values:
                    if not is_override_val_valid(inp, val, ng_ptr, node):
                        return False
    return True

def is_preset_setup_valid(scene, preset):
    if not validate_overrides(scene.batch_stl_global_nodegroups):
        return False
    if not validate_overrides(preset.nodegroups):
        return False
    for c in preset.collections:
        if not validate_overrides(c.nodegroups):
            return False
        for obj in c.objects:
            if obj.export:
                if not validate_overrides(obj.nodegroups):
                    return False
    return True
