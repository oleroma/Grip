"""Drawing: UI lists, panels, the override table with its merge bars and value icons, and the directory tree."""
import os

import bpy

from .common import _ui_cache, overrides_open_prop
from .nodes import SUPPORTED_OVERRIDE_TYPES, cached_menu_items, clean_node_name, has_free_target
from .naming import SCOPE_KINDS, clash_key, value_field_anchors, value_name_parts
from .fields import value_specs
from .engine import get_sorted_values
from .scope import _block_where, scope_dead, _value_steps
from .data import get_active_collection, get_active_object, get_active_preset, get_job, is_any_exporting
from .validation import is_override_group_valid, is_override_input_valid, is_override_node_valid, is_override_val_valid
from .ui_cache import is_dir_collapsed, load_toggled_dirs
from .props import upstream_scope
from .operators import _clipboard
from .standby import get_preferences

ICONS = {
    'PRESET': 'PRESET', 'COLLECTION': 'OUTLINER_COLLECTION', 'OBJECT': 'OBJECT_DATA',
    'SWEEP': 'CON_ROTLIMIT', 'GLOBAL': 'WORLD', 'DIR': 'FILE_FOLDER', 'TAG': 'TAG',
    'ADD': 'ADD', 'DEL': 'TRASH', 'CLEAR': 'X', 'UP': 'TRIA_UP', 'DOWN': 'TRIA_DOWN',
    'COPY': 'COPYDOWN', 'PASTE': 'PASTEDOWN', 'CANCEL': 'CANCEL', 'EXPORT': 'EXPORT',
    'IMPORT': 'IMPORT', 'INFO': 'INFO', 'CONSOLE': 'CONSOLE', 'CHECK_ON': 'CHECKBOX_HLT',
    'CHECK_OFF': 'CHECKBOX_DEHLT', 'OVR': 'DECORATE_OVERRIDE', 'NODE': 'NODETREE',
    'TIME': 'TIME', 'MODIFIER': 'MODIFIER', 'TREE': 'OUTLINER_OB_EMPTY', 'ERROR': 'ERROR',
    'RIGHT': 'TRIA_RIGHT', 'BLANK': 'BLANK1', 'FILE': 'FILE_3D',
    'EXPAND_ALL': 'FULLSCREEN_ENTER', 'COLLAPSE_ALL': 'FULLSCREEN_EXIT', 'EXPAND_LAST': 'TRIA_DOWN_BAR',
    'MERGE': 'AUTOMERGE_ON', 'PLAIN': 'DOT', 'STANDBY': 'FF', 'SAVE_JSON': 'FILE_TICK'
}

def draw_tree_dict(layout, tree_node, current_path="", toggled_list=None, duplicates=None, actual_path=""):
    if toggled_list is None: toggled_list = load_toggled_dirs(bpy.context.window_manager)
    if duplicates is None: duplicates = set()

    dirs = [k for k in tree_node.keys() if k != '_files']
    for k in dirs:
        dir_path = f"{current_path}/{k}"
        next_actual = os.path.normpath(os.path.join(actual_path, k)) if actual_path else os.path.normpath(k)
        is_root = current_path == ""
        is_collapsed = False if is_root else is_dir_collapsed(toggled_list, dir_path, is_root)

        split = layout.split(factor=0.005)
        split.column()
        box = split.column().box()
        row = box.row(align=True)
        if is_root:
            row.label(text="", icon=ICONS['DOWN'])
        else:
            row.operator_context = 'INVOKE_DEFAULT'
            row.operator("batch_stl.toggle_dir_tree", text="", icon=ICONS['RIGHT'] if is_collapsed else ICONS['DOWN'], emboss=False).dir_path = dir_path
            row.operator_context = 'EXEC_DEFAULT'
        row.scale_y = 0.8
        row.label(text=str(k), icon=ICONS['DIR'])
        if not is_collapsed and isinstance(tree_node[k], dict):
            draw_tree_dict(box, tree_node[k], dir_path, toggled_list, duplicates, next_actual)

    for f in tree_node.get('_files', []):
        split = layout.split(factor=0.12)
        split.column()
        col = split.column()

        row = col.row()
        row.scale_y = 0.8
        check_path = os.path.normpath(os.path.join(actual_path, f)) if actual_path else os.path.normpath(f)
        if clash_key(check_path) in duplicates: row.alert = True
        row.label(text=str(f), icon=ICONS['OBJECT'])

def merge_tooltip(hits, dead, scope):
    """`hits` / `dead` are lists of (kind, name) keys."""
    lines = [f"{name}  ({scope.desc((kind, name))})" for kind, name in hits]
    if dead:
        lines += [f"{name}  ({scope.desc((kind, name))}) cannot exist here" for kind, name in dead]
        lines.append("No branch contains all of these names together, so this block and everything inside it never applies")
    elif any(scope.is_branch(k) for k in hits):
        lines.append("This block and everything inside it only applies to the branches that contain these names")
    else:
        lines.append("This block and everything inside it is placed inside these existing folders / name tokens")
    return "\n".join(lines)

def format_step(value): return f"{value:.10g}" if isinstance(value, float) else str(value)

def value_info(ng_ptr, node, inp, val, res, scope):
    """(icon, merges, dead, tooltip) of the button before a value's expression field: what the expression gives, and
    the upstream names its folder / tag merge into (`res` is {kind: (hits, dead)}, see BranchScope.resolve_value)."""
    _tmp, steps = _value_steps(ng_ptr, node, inp, val)
    steps = steps or [""]
    shown = ", ".join(format_step(v) for v in steps[:6]) + (", …" if len(steps) > 6 else "")
    lines = [f"Value: {shown}" if len(steps) == 1 else f"{len(steps)} values: {shown}"]
    specs = value_specs(val)
    for kind, label, joiner in (("dir", "Folder", " / "), ("tag", "Filename token", "_")):
        if specs[kind] is None: continue
        first, last = (joiner.join(sum(value_name_parts(step, specs[kind], kind), [])) for step in (steps[0], steps[-1]))
        lines.append(f"{label}: {first}" + (f" … {last}" if last != first else ""))
    if all(spec is None for spec in specs.values()): lines.append("No folder and no filename token")
    hits = [(k, n) for k in SCOPE_KINDS for n in res[k][0]]
    dead = [(k, n) for k in SCOPE_KINDS for n in res[k][1]]
    if hits or dead:
        lines.append("")
        lines += [f"Merges into {name}  ({scope.desc((kind, name))})" for kind, name in hits]
        lines += [f"{name}  ({scope.desc((kind, name))}) cannot exist here" for kind, name in dead]
        if dead: lines.append("No branch contains all of these names together, so this value never applies")
        elif any(scope.is_branch(k) for k in hits): lines.append("This value only applies to the branches that contain these names")
        else: lines.append("Its folders / name tokens go inside these existing ones")
    if dead: icon = ICONS['ERROR']
    elif hits: icon = ICONS['MERGE']
    elif specs["dir"] is not None: icon = ICONS['DIR']
    elif specs["tag"] is not None: icon = ICONS['TAG']
    else: icon = ICONS['PLAIN']
    return icon, bool(hits), bool(dead), "\n".join(lines)

def naming_icon(block, res):
    """Icon of a node group / node naming field: merge when a name merges into an upstream one."""
    if any(res[kind][0] or res[kind][1] for kind in SCOPE_KINDS): return ICONS['MERGE']
    return ICONS['TAG'] if block.tag and not block.sub_path else ICONS['DIR']

def merge_state(res, scope):
    """(dead, text, tooltip) of a block whose sub-folder or tag merges into upstream names, else None. Dead when the
    chosen names can never exist together (the block never applies). The tooltip is taken now: names added further
    down the stack must not change it."""
    hits = [(k, n) for k in SCOPE_KINDS for n in res[k][0]]
    dead = [(k, n) for k in SCOPE_KINDS for n in res[k][1]]
    if not hits and not dead: return None
    segments = []
    d_names, t_names = res["dir"][0] + res["dir"][1], res["tag"][0] + res["tag"][1]
    if d_names: segments.append(" / ".join(d_names))
    if t_names: segments.append("name " + " + ".join(t_names))
    text = ("Never applies: " if dead else "Merges into ") + " · ".join(segments)
    return bool(dead), text, merge_tooltip(hits, dead, scope)

def predict_table(nodegroups):
    """Merge predictions of a non-empty override table, built in export order like the exporter walks it (see
    BranchScope): {(ng_idx,) and (ng_idx, n_idx): (naming icon, merge state or None), (ng_idx, n_idx, i_idx, v_idx):
    value_info()}."""
    out = {}
    scope = upstream_scope(nodegroups[0])[0]
    for ng_idx, ng in enumerate(nodegroups):
        ng_ptr = bpy.data.node_groups.get(ng.group_name)
        ng_ctx, ng_res = scope.enter_block(ng, frozenset(), ng)
        ng_alive = not scope_dead(ng_res)
        out[ng_idx,] = naming_icon(ng, ng_res), merge_state(ng_res, scope)
        for n_idx, node in enumerate(ng.nodes):
            n_ctx, n_res = scope.enter_block(node, ng_ctx, ng, node, ng_alive)
            n_alive = ng_alive and not scope_dead(n_res)
            out[ng_idx, n_idx] = naming_icon(node, n_res), merge_state(n_res, scope)
            for i_idx, inp in enumerate(node.inputs):
                if inp.override_type in SUPPORTED_OVERRIDE_TYPES:
                    for v_idx, val in enumerate(inp.values):
                        v_res = scope.resolve_value(value_field_anchors(val), n_ctx)[1]
                        out[ng_idx, n_idx, i_idx, v_idx] = value_info(ng_ptr, node, inp, val, v_res, scope)
                scope.add_input(ng, ng_ptr, node, inp, n_ctx, n_alive)
    return out

# Building a table's predictions is most of its draw time (about 180 of 225 ms for 200 values with merges), and the
# sidebar redraws on every hover and every step of a transform drag. They only change with the data, so they are kept
# per table for one _ui_cache["revision"] (bumped by edits, undo, loads, node tree updates and changed menu items).
_predictions = {}

def table_predictions(nodegroups):
    """predict_table() of a non-empty override table, kept until the data changes. The key holds the table's shape too:
    rows added without an edit callback (by a script) must not be drawn from predictions that lack them."""
    if _predictions.get("revision") != _ui_cache["revision"]:
        _predictions.clear()
        _predictions["revision"] = _ui_cache["revision"]
    shape = tuple(tuple(tuple(len(inp.values) for inp in node.inputs) for node in ng.nodes) for ng in nodegroups)
    key = (nodegroups[0].id_data.session_uid, nodegroups[0].path_from_id(), shape)
    if key not in _predictions: _predictions[key] = predict_table(nodegroups)
    return _predictions[key]


# Gap between a preset row's export button and the item's fields, in UI units (a unit is a button's width)
PRESET_BUTTON_GAP = 1.0

class BATCH_STL_UL_presets(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        job = get_job(item)
        is_exporting = bool(job and job.is_exporting)
        row = layout.row(align=True)
        # The export / cancel button leads the row, set apart from the item's fields by a gap
        if is_exporting:
            row.operator("batch_stl.cancel_export", text="", icon=ICONS['CANCEL']).preset_uid = item.uid
        else:
            row.operator("export_scene.batch_stl_multi", text="", icon=ICONS['EXPORT']).preset_index = index
        row.separator(factor=PRESET_BUTTON_GAP)
        prop_row = row.row(align=True)
        prop_row.enabled = not is_any_exporting()
        prop_row.prop(item, "name", text="", emboss=False)

        metrics = _ui_cache.get("preset_metrics", {}).get(index, {"has_ovr": False, "has_perm": False})
        icon_row = prop_row.row(align=True)
        icon_row.alignment = 'RIGHT'
        icon_row.label(text="", icon=ICONS['SWEEP'] if metrics["has_perm"] else ICONS['BLANK'])
        icon_row.label(text="", icon=ICONS['NODE'] if metrics["has_ovr"] else ICONS['BLANK'])
        prop_row.prop(item, "preset_prefix", text="", emboss=False, icon=ICONS['DIR'])

        if is_exporting:
            row.prop(job, "export_progress", text=job.export_status, slider=True)

def collection_note(scene, item):
    """Tooltip of the note icon on a ticked collection that is not in the scene (it is exported all the same), or
    None."""
    col = bpy.data.collections.get(item.collection_name) if item.export else None
    if col is None or col in scene.collection.children_recursive: return None
    return "Not in this scene: exported all the same, the export links it into its own copy of the file"

class BATCH_STL_UL_collections(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        row = layout.row(align=True)
        row.prop(item, "export_tick", text="", icon=ICONS['CHECK_ON'] if item.export else ICONS['CHECK_OFF'], emboss=False)
        row.prop_search(item, "collection_name", bpy.data, "collections", text="", icon=ICONS['COLLECTION'])
        note = collection_note(context.scene, item)
        if note: row.operator("batch_stl.collection_note", text="", icon=ICONS['INFO'], emboss=False).info = note
        row.separator(factor=0.5)
        sub_row = row.row(align=True)
        op = sub_row.operator("batch_stl.table_action", text="", icon=ICONS['TAG'], depress=item.use_tag)
        op.action = 'TOGGLE_COLLECTION_USE_TAG'; op.c_idx = index
        sub_row.separator(factor=0.5)
        sub_row.row(align=True).prop(item, "tag", text="", emboss=False)
        row.prop(item, "sub_path", text="", emboss=False, icon=ICONS['DIR'])

class BATCH_STL_UL_objects(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        split = layout.split(factor=0.45)
        row = split.row(align=True)
        row.prop(item, "export_tick", text="", icon=ICONS['CHECK_ON'] if item.export else ICONS['CHECK_OFF'], emboss=False)
        row.prop(item, "export_name", text="", emboss=False)

        tools = split.row(align=True)
        tools.label(text="", icon=ICONS['TAG'])
        tools.prop(item, "tag", text="", emboss=False)
        tools.separator(factor=0.5)
        tools.label(text="", icon=ICONS['DIR'])
        tools.prop(item, "sub_path", text="", emboss=False)

class BATCH_STL_UL_console_logs(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        layout.label(text=item.text)

def draw_list_controls(layout, operator_id, use_clipboard=False):
    """The action buttons of a UI list, as a column on its right: put it in the row that holds the template_list. Its
    height sets the list's rows (LIST_ROWS)."""
    col = layout.column(align=True)
    col.enabled = not is_any_exporting()
    col.operator_context = 'INVOKE_DEFAULT'
    col.operator(operator_id, icon=ICONS['ADD'], text="").action = 'ADD'
    col.operator(operator_id, icon=ICONS['DEL'], text="").action = 'REMOVE'
    col.separator()
    col.operator(operator_id, icon=ICONS['UP'], text="").action = 'UP'
    col.operator(operator_id, icon=ICONS['DOWN'], text="").action = 'DOWN'
    if use_clipboard:
        col.separator()
        col.operator(operator_id, icon=ICONS['COPY'], text="").action = 'COPY'
        col.operator(operator_id, icon=ICONS['PASTE'], text="").action = 'PASTE'

# Rows of a list with draw_list_controls: tall enough for its six buttons (and never more: the list scrolls)
LIST_ROWS = 6

# Width of the "Root:" label before the root folder field, in UI units (a unit is a button's width)
ROOT_LABEL_UNITS = 2.5

def format_count(stats, key="exp"):
    """A stats count; '5000+' when counting stopped at COUNT_LIMIT for some object."""
    return f"{stats[key]}+" if stats.get("capped") else stats[key]

def draw_stats_table(parent_layout, stats_list, lead=None):
    """A box with the counts of a level, centered in what the row has left. `lead(row)` draws buttons at its start."""
    row = parent_layout.box().row()
    if lead: lead(row)
    stats = row.row(align=True)
    stats.alignment = 'CENTER'
    for i, (val, icon) in enumerate(stats_list):
        if i > 0: stats.separator(factor=2.0)
        stats.label(text=str(val), icon=icon)

def draw_table_op(parent, action, icon, level, depress=False, ng_idx=-1, n_idx=-1, i_idx=-1, v_idx=-1):
    """A batch_stl.table_action button for the override table of `level`: (is_collection, is_preset, is_global)."""
    parent.operator_context = 'INVOKE_DEFAULT'
    op = parent.operator("batch_stl.table_action", text="", icon=icon, depress=depress)
    op.action = action
    op.is_collection, op.is_preset, op.is_global = level
    op.ng_idx, op.n_idx, op.i_idx, op.v_idx = ng_idx, n_idx, i_idx, v_idx
    return op

def draw_override_buttons(layout, nodegroups, is_collection=False, is_preset=False, is_global=False):
    """The buttons of a level's override table, at the start of the panel's first row (nothing for a level that does
    not exist). An empty table draws nothing (see draw_overrides_table), so these hold the way to add its first group,
    and a paste button while the clipboard holds a group. Once the table has groups it draws its own add / paste
    buttons, and this button clears the table instead."""
    if nodegroups is None: return
    level = (is_collection, is_preset, is_global)
    if len(nodegroups): buttons = [('CLEAR_GROUPS', ICONS['CLEAR'])]
    else: buttons = [('ADD_GROUP', ICONS['OVR'])] + ([('PASTE_GROUP', ICONS['PASTE'])] if _clipboard.get("nodegroup") else [])
    row = layout.row(align=True)
    row.enabled = not is_any_exporting()
    row.ui_units_x = len(buttons)  # a button is one unit wide: the row stays as wide as its buttons
    for action, icon in buttons: draw_table_op(row, action, icon, level)

def draw_overrides_table(*args, **kwargs):
    with cached_menu_items(): _draw_overrides_table(*args, **kwargs)

def _draw_overrides_table(layout, wm, nodegroups, is_collection, title_text, is_preset=False, is_global=False, is_locked=False):
    # An empty table is not drawn: the button that adds its first group is at the start of the panel's first row
    # (draw_override_buttons)
    if len(nodegroups) == 0: return

    level = (is_collection, is_preset, is_global)
    is_open_prop = overrides_open_prop(*level)
    def draw_op(parent, action, icon, depress=False, ng_idx=-1, n_idx=-1, i_idx=-1, v_idx=-1):
        return draw_table_op(parent, action, icon, level, depress, ng_idx, n_idx, i_idx, v_idx)

    def draw_input_name(parent, inp, ng, node):
        row = parent.row(align=True)
        row.alert = not is_override_input_valid(bpy.data.node_groups.get(ng.group_name), node, inp)
        row.prop(inp, "name", text="")

    box = layout.box()

    header_row = box.row()
    header_row.enabled = not is_locked
    is_open = getattr(wm, is_open_prop)
    icon_open = ICONS['DOWN'] if is_open else ICONS['RIGHT']
    header_row.prop(wm, is_open_prop, text="", icon=icon_open, emboss=False)

    icon_header = ICONS['GLOBAL'] if is_global else (ICONS['PRESET'] if is_preset else (ICONS['COLLECTION'] if is_collection else ICONS['OBJECT']))
    header_row.label(text="", icon=ICONS['OVR'])
    header_row.label(text=title_text, icon=icon_header)

    op_row = header_row.row(align=True)
    op_row.enabled = not is_locked
    draw_op(op_row, 'ADD_GROUP', ICONS['ADD'])
    draw_op(op_row, 'PASTE_GROUP', ICONS['PASTE'])

    # Collapsed, a table with inputs switches to the clear view: only the inputs and their values, without the node
    # group / node rows around them. Without inputs it collapses completely.
    clear = not is_open
    if clear and not any(node.inputs for ng in nodegroups for node in ng.nodes):
        return

    content_col = box.column()
    content_col.enabled = not is_locked

    def draw_merge_bar(parent, state):
        """Bar on top of a merging block: marks the block and its children. Blue for a merge, red when it is dead."""
        if not state: return
        dead, text, tooltip = state
        row = parent.row(align=True)
        row.alert = dead
        row.operator("batch_stl.merge_info", text=text, icon=ICONS['ERROR'] if dead else ICONS['MERGE'], depress=not dead).info = tooltip

    def draw_merge_icon(parent, merges):
        """Clear view: the merge bars of an input's hidden node group / node as one icon at the start of its row.
        `merges` is [(block name, merge_state)]; without merges the slot stays blank, so the names line up."""
        if merges:
            dead = any(state[0] for _where, state in merges)
            row = parent.row(align=True)
            row.alert = dead
            op = row.operator("batch_stl.merge_info", text="", icon=ICONS['ERROR'] if dead else ICONS['MERGE'], depress=not dead)
            op.info = "\n\n".join(f"{where}: {text}\n{tooltip}" for where, (_dead, text, tooltip) in merges)
        else:
            parent.label(text="", icon=ICONS['BLANK'])
        parent.separator(factor=0.5)

    def draw_input(parent, ng_idx, ng, ng_ptr, n_idx, node, i_idx, inp, merges=None):
        """Rows of one input (its first value on the input's row, the others below). `merges` is given in the clear
        view only (see draw_merge_icon)."""
        input_layout = parent.column()
        # Wrap in array to ensure rendering block triggers at least once even if 'values' logic is empty
        values = inp.values if inp.values else [None]

        for visual_v, (v_idx, val) in enumerate(get_sorted_values(ng_ptr, node, inp, values)):
            i_first = (visual_v == 0)
            i_row = input_layout.row(align=True)
            # The merge icon slot sits before the columns (blank on the other value rows), so it takes no width from them
            if merges is not None: draw_merge_icon(i_row.row(align=True), merges if i_first else [])

            # Two columns: the input, then one field per value with the value, its folder ('\') and its filename
            # token ('_'), see lex_expr
            s_main = i_row.split(factor=0.35, align=False)
            c_inp = s_main.row(align=True)

            if i_first:
                action_icon = ICONS['SWEEP'] if val and getattr(val, "use_sweep", False) else ICONS['ADD']
                draw_op(c_inp, 'VALUE_ACTION', action_icon, depress=(action_icon == ICONS['SWEEP']),
                        ng_idx=ng_idx, n_idx=n_idx, i_idx=i_idx, v_idx=v_idx if val else -1)
                draw_input_name(c_inp, inp, ng, node)
            else:
                c_inp.alignment = 'RIGHT'

            c_val = s_main.row(align=True)
            # Handing unpopulated values safely
            if val is None:
                continue
            if inp.override_type not in SUPPORTED_OVERRIDE_TYPES:
                c_val.label(text="Unsupported socket type", icon=ICONS['ERROR'])
                continue

            # The button before the field explains the expression (hover it) and shows its merges: blue when its
            # folder / token merges into an upstream one, red when it cannot exist in this block's branch (the value
            # never applies). The field is red for that too, and for a value that does not fit the input.
            icon, v_merges, v_dead, info = predictions[ng_idx, n_idx, i_idx, v_idx]
            c_info = c_val.row(align=True)
            c_info.alert = v_dead
            c_info.operator("batch_stl.merge_info", text="", icon=icon, depress=v_merges, emboss=v_merges or v_dead).info = info
            c_field = c_val.row(align=True)
            c_field.alert = v_dead or not is_override_val_valid(inp, val, ng_ptr, node)
            c_field.prop(val, "expr", text="")

    # Merge bars, naming icons and value icons, predicted in export order (kept until the data changes). The clear view
    # shows the same predictions without the node group / node rows.
    predictions = table_predictions(nodegroups)
    clear_layout = content_col.box().column() if clear else None

    for ng_idx, ng in enumerate(nodegroups):
        ng_ptr = bpy.data.node_groups.get(ng.group_name)
        ng_icon, ng_merge = predictions[ng_idx,]

        if not clear:
            ng_layout = content_col.box().column()
            draw_merge_bar(ng_layout, ng_merge)
            ng_row = ng_layout.row(align=True)

            if ng.group_name:
                # Greyed out once every target of the group has an entry
                add_row = ng_row.row(align=True)
                add_row.enabled = has_free_target(ng_ptr, {clean_node_name(n.name) for n in ng.nodes})
                draw_op(add_row, 'ADD_NODE', ICONS['ADD'], ng_idx=ng_idx)
            ng_sub = ng_row.row(align=True)
            ng_sub.alert = not is_override_group_valid(ng)
            ng_sub.prop(ng, "group_name", text="")
            # An empty field has no clear button of its own, and emptying it is how a group is deleted
            if not ng.group_name: draw_op(ng_sub, 'REMOVE_GROUP', ICONS['CLEAR'], ng_idx=ng_idx)
            ng_row.prop(ng, "naming", text="", icon=ng_icon)
            draw_op(ng_row, 'MOVE_GROUP_UP', ICONS['UP'], ng_idx=ng_idx)
            draw_op(ng_row, 'MOVE_GROUP_DOWN', ICONS['DOWN'], ng_idx=ng_idx)
            draw_op(ng_row, 'COPY_GROUP', ICONS['COPY'], ng_idx=ng_idx)

            if not ng.nodes:
                continue

            n_split = ng_layout.split(factor=0.03)
            n_split.column()
            nodes_col = n_split.column()
            nodes_box = nodes_col.box() if len(ng.nodes) > 1 else nodes_col
            nodes_layout = nodes_box.column()

        for n_idx, node in enumerate(ng.nodes):
            n_icon, n_merge = predictions[ng_idx, n_idx]

            if clear:
                inputs_layout = clear_layout
                merges = [(where, state) for where, state in ((_block_where(ng), ng_merge), (_block_where(ng, node), n_merge)) if state]
            else:
                node_layout = nodes_layout.box().column()
                draw_merge_bar(node_layout, n_merge)

                n_row = node_layout.row(align=True)
                draw_op(n_row, 'ADD_INPUT', ICONS['ADD'], ng_idx=ng_idx, n_idx=n_idx)
                n_sub = n_row.row(align=True)
                n_sub.alert = not is_override_node_valid(ng_ptr, node)
                n_sub.prop(node, "name", text="", icon=ICONS['NODE'])
                n_row.prop(node, "naming", text="", icon=n_icon)

                if len(ng.nodes) > 1:
                    draw_op(n_row, 'MOVE_NODE_UP', ICONS['UP'], ng_idx=ng_idx, n_idx=n_idx)
                    draw_op(n_row, 'MOVE_NODE_DOWN', ICONS['DOWN'], ng_idx=ng_idx, n_idx=n_idx)

                i_split = node_layout.split(factor=0.03)
                i_split.column()
                inputs_layout = i_split.column().box().column()
                merges = None

            for i_idx, inp in enumerate(node.inputs):
                draw_input(inputs_layout, ng_idx, ng, ng_ptr, n_idx, node, i_idx, inp, merges)


class VIEW3D_PT_batch_export_stl_main(bpy.types.Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Combi Export"
    bl_label = "Combi Export"

    def draw_header(self, context):
        self.layout.label(text="", icon=ICONS['EXPORT'])

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        any_exporting = is_any_exporting()

        # The root folder, with the global overrides' buttons before it and the JSON import / export buttons and the
        # Save JSON with File toggle next to it.
        # The label is a row of fixed width whose text sits at its right end, against the field (a field's own label is
        # drawn inside it, from the left).
        dir_row = layout.row()
        dir_row.enabled = not any_exporting
        draw_override_buttons(dir_row, scene.batch_stl_global_nodegroups, is_global=True)
        label_row = dir_row.row()
        label_row.ui_units_x = ROOT_LABEL_UNITS
        label_row.alignment = 'RIGHT'
        label_row.label(text="Root:")
        dir_row.prop(scene, "batch_stl_root_dir", text="")
        json_row = dir_row.row(align=True)
        json_row.operator("batch_stl.import_presets_json", text="", icon=ICONS['IMPORT'])
        json_row.operator("batch_stl.export_presets_json", text="", icon=ICONS['EXPORT'])
        json_row.prop(scene, "batch_stl_save_json", text="", icon=ICONS['SAVE_JSON'])

        layout.separator()

        # Global Overrides
        g_col = layout.column()
        g_col.enabled = not any_exporting
        draw_overrides_table(g_col, context.window_manager, scene.batch_stl_global_nodegroups, False, "Global Overrides", is_global=True, is_locked=any_exporting)


class VIEW3D_PT_batch_export_stl_info(bpy.types.Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Combi Export"
    bl_label = "Info"
    bl_options = {'DEFAULT_CLOSED'}

    def draw_header(self, context):
        self.layout.label(text="", icon=ICONS['INFO'])

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        any_exporting = is_any_exporting()

        tab_row = layout.row()
        wm = context.window_manager
        tab_row.prop(wm, "batch_stl_info_tab", expand=True)

        if wm.batch_stl_info_tab == 'LOG':
            active_job = get_job(get_active_preset(scene))
            log_row = layout.row()

            if active_job:
                col = log_row.column(align=True)
                col.template_list("BATCH_STL_UL_console_logs", "", active_job, "console_logs", active_job, "console_index", rows=6)
            else:
                col = log_row.column()
                col.label(text="No export log for this preset yet.", icon=ICONS['INFO'])

            log_tools = log_row.column(align=True)
            log_tools.prop(wm, "batch_stl_verbose_console", text="", toggle=True, icon=ICONS['CONSOLE'])

            if active_job:
                log_tools.separator()
                clear_col = log_tools.column(align=True)
                clear_col.enabled = not any_exporting
                clear_col.operator("batch_stl.clear_console", text="", icon=ICONS['DEL'])

        elif wm.batch_stl_info_tab == 'TREE':
            tree_dict, duplicates = _ui_cache.get("tree", ({}, set()))
            if duplicates:
                warn_box = layout.box()
                warn_row = warn_box.row()
                warn_row.label(text=f"WARNING: {len(duplicates)} naming collisions detected! Files will be overwritten.", icon=ICONS['ERROR'])

            # Tree on the left, a vertical strip of icon buttons on the right (same layout as UIList side buttons).
            tree_row = layout.row()
            col = tree_row.column(align=True)
            draw_tree_dict(col, tree_dict, duplicates=duplicates)
            expand_tools = tree_row.column(align=True)
            expand_tools.prop(wm, "batch_stl_info_global", text="", toggle=True, icon=ICONS['GLOBAL'])
            expand_tools.separator()
            expand_tools.operator("batch_stl.tree_expansion", text="", icon=ICONS['EXPAND_ALL']).mode = 'EXPAND_ALL'
            expand_tools.operator("batch_stl.tree_expansion", text="", icon=ICONS['COLLAPSE_ALL']).mode = 'COLLAPSE_ALL'
            expand_tools.operator("batch_stl.tree_expansion", text="", icon=ICONS['EXPAND_LAST']).mode = 'EXPAND_LAST'

        layout.separator()

        tip_box = layout.box()
        tip_header = tip_box.row()
        icon_tip = ICONS['DOWN'] if wm.batch_stl_ui_tips else ICONS['RIGHT']
        tip_header.prop(wm, "batch_stl_ui_tips", text="", icon=icon_tip, emboss=False)
        tip_header.label(text="EXTENSION GUIDE", icon=ICONS['INFO'])

        if wm.batch_stl_ui_tips:
            box_col = tip_box.column()

            box_col.label(text="Hierarchical Overrides (Priority):", icon=ICONS['OVR'])
            split = box_col.split(factor=0.05)
            split.column()
            child_col = split.column()
            child_col.label(text="  • Global > Preset > Collection > Object", icon=ICONS['BLANK'])
            child_col.label(text="  • Override button (start of the counts row, or the Root row): adds the first group, then X clears them", icon=ICONS['OVR'])
            child_col.label(text="  • Modifiers: Leave Node empty or set to <Modifier Interface>", icon=ICONS['BLANK'])
            child_col.label(text="  • Group Output: Can be targeted to override what the group outputs", icon=ICONS['NODE'])
            box_col.separator()

            box_col.label(text="Shortcuts & Ergonomics:", icon=ICONS['INFO'])
            split = box_col.split(factor=0.05)
            split.column()
            child_col = split.column()
            child_col.label(text="  • Shift + Add Input (+): Auto-populates all exposed inputs", icon=ICONS['ADD'])
            child_col.label(text="  • Shift + Up/Down: Move group to parent tier / copy to all child tiers", icon=ICONS['UP'])
            child_col.label(text="  • Copy/Paste/Import/Export: Transfer configurations seamlessly", icon=ICONS['COPY'])
            child_col.label(text="  • Instant Deletion: Empty a field & submit, or click its X, to delete it", icon=ICONS['DEL'])
            child_col.label(text="  • Validation: Invalid inputs are rejected and reset safely", icon=ICONS['CHECK_ON'])
            box_col.separator()

            box_col.label(text="Parametric Sweeping:", icon=ICONS['SWEEP'])
            split = box_col.split(factor=0.05)
            split.column()
            child_col = split.column()
            child_col.label(text="  • Float/Int Ranges: Define Start, Step, and Count", icon=ICONS['BLANK'])
            child_col.label(text="  • Menus/Bools: Auto-iterates True/False and Enum options", icon=ICONS['BLANK'])
            child_col.label(text="  • Shift + Sweep (+): Populates all menu/bool values automatically", icon=ICONS['SWEEP'])
            box_col.separator()

            box_col.label(text="Value Field (\\folder _filename, the value where it goes):", icon=ICONS['FILE'])
            split = box_col.split(factor=0.05)
            split.column()
            child_col = split.column()
            child_col.label(text="  • 15 = value only · \\15 = folder 15 · _15 = filename token 15 · \\15\\_15 = both", icon=ICONS['BLANK'])
            child_col.label(text="  • New inputs start as value only; + or a sweep adds \\ so permutations don't collide", icon=ICONS['ADD'])
            child_col.label(text="  • \\big / _big: your name instead of the value (not shown; it merges into an upstream big)", icon=ICONS['DIR'])
            child_col.label(text="  • \\15 → \\16 changes the value, unless 16 exists upstream · 16\\big sets both", icon=ICONS['BLANK'])
            child_col.label(text="  • Tab completes an upstream name with its separator: \\A → \\A\\, then type the next", icon=ICONS['MERGE'])
            child_col.label(text="  • \\15_mm, \\size_15, _15_mm: the value joined with text", icon=ICONS['DIR'])
            child_col.label(text="  • \\B\\15 / _B_15: B, then the value (B/15, Box_B_15)", icon=ICONS['TAG'])
            child_col.label(text="  • Sweeps: \\0:0.5:5 = start:step:count · _{a, b} = strings · \\* = all items (replaces other values)", icon=ICONS['SWEEP'])
            child_col.label(text="  • Quoted text is literal: \"a_b\" · Clear the field to delete the value", icon=ICONS['BLANK'])
            child_col.label(text="  • Group / Node naming: \\C\\2\\_B = folders C/2 and token B", icon=ICONS['NODE'])
            child_col.label(text="  • Hover the icon before a value to see its folder, token and merges", icon=ICONS['INFO'])
            child_col.label(text="  • Filename: Object, then tags in stack order (Global > ... > Object)", icon=ICONS['BLANK'])
            child_col.label(text="  • Collection/Object tags: plain tokens, '/' between tokens", icon=ICONS['BLANK'])
            box_col.separator()

            box_col.label(text="Branch Merging:", icon=ICONS['MERGE'])
            split = box_col.split(factor=0.05)
            split.column()
            child_col = split.column()
            child_col.label(text="  • Name an upstream folder or filename token to merge into that branch only", icon=ICONS['BLANK'])
            child_col.label(text="  • Values merge only by a typed name; a name derived from the value is new", icon=ICONS['BLANK'])
            child_col.label(text="  • Tag merges append new tokens at the end of the filename", icon=ICONS['TAG'])
            child_col.label(text="  • \\B = only B permutations, \\C\\2 = only C2, \\2 = every 2 branch", icon=ICONS['BLANK'])
            child_col.label(text="  • After \\ or _, the field lists upstream names that fit the current branch", icon=ICONS['DIR'])
            child_col.label(text="  • Blue bar: block and children merge (hover for sources)", icon=ICONS['MERGE'])
            child_col.label(text="  • Red bar: names never exist together, block never applies", icon=ICONS['ERROR'])
            child_col.label(text="  • Collapsed table: inputs only, a merging group / node shows at the row start", icon=ICONS['RIGHT'])
            box_col.separator()

            box_col.label(text="Tree View & Output Console:", icon=ICONS['TREE'])
            split = box_col.split(factor=0.05)
            split.column()
            child_col = split.column()
            child_col.label(text="  • Global View: Show all presets or isolate current", icon=ICONS['GLOBAL'])
            child_col.label(text="  • Expand/Collapse All: Toggle full directory visibility", icon=ICONS['EXPAND_ALL'])
            child_col.label(text="  • Expand Last: Collapses tree and expands only the last sub-folders", icon=ICONS['EXPAND_LAST'])
            child_col.label(text="  • Verbose Console / Clear Log: Manage background worker output", icon=ICONS['CONSOLE'])


class VIEW3D_PT_batch_export_stl_presets(bpy.types.Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Combi Export"
    bl_label = "Presets"

    @classmethod
    def poll(cls, context):
        return True

    def draw_header(self, context):
        self.layout.label(text="", icon=ICONS['PRESET'])

    def draw_header_preset(self, context):
        active_preset = get_active_preset(context.scene)
        row = self.layout.row(align=True)
        if active_preset and active_preset.last_export_time > 0:
            time_row = row.row(align=True)
            time_row.enabled = not is_any_exporting()
            time_row.label(text=f"{active_preset.last_export_time:.2f}s", icon=ICONS['TIME'])
        prefs = get_preferences()
        if prefs: row.prop(prefs, "keep_worker_ready", text="", icon=ICONS['STANDBY'])
        row.separator()

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        any_exporting = is_any_exporting()
        active_preset = get_active_preset(scene)
        stats = _ui_cache.get("stats", {})

        content_col = layout.column(align=True)
        list_row = content_col.box().row()
        list_row.template_list("BATCH_STL_UL_presets", "", scene, "batch_stl_presets", scene, "batch_stl_preset_index", rows=LIST_ROWS, maxrows=LIST_ROWS)
        draw_list_controls(list_row, "batch_stl.preset_actions", use_clipboard=True)

        locked_col = content_col.column(align=True)
        locked_col.enabled = not any_exporting

        g_stats = stats.get("global", {"presets": 0, "cols": 0, "objs": 0, "exp": 0})
        draw_stats_table(locked_col, [
            (g_stats['presets'], ICONS['PRESET']),
            (g_stats['cols'], ICONS['COLLECTION']),
            (g_stats['objs'], ICONS['OBJECT']),
            (format_count(g_stats), ICONS['SWEEP'])
        ], lead=lambda row: draw_override_buttons(row, active_preset and active_preset.nodegroups, is_preset=True))

        if active_preset:
            draw_overrides_table(locked_col, context.window_manager, active_preset.nodegroups, False, f"Overrides for [ {active_preset.name} ]", is_preset=True, is_locked=any_exporting)


class VIEW3D_PT_batch_export_stl_collections(bpy.types.Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Combi Export"
    bl_label = "Collections"

    @classmethod
    def poll(cls, context):
        return get_active_preset(context.scene) is not None

    def draw_header(self, context):
        self.layout.label(text="", icon=ICONS['COLLECTION'])

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        any_exporting = is_any_exporting()
        active_preset = get_active_preset(scene)
        stats = _ui_cache.get("stats", {})

        layout.enabled = not any_exporting
        active_col = get_active_collection(active_preset)

        content_col = layout.column(align=True)
        list_row = content_col.box().row()
        list_row.template_list("BATCH_STL_UL_collections", "", active_preset, "collections", active_preset, "collection_index", rows=LIST_ROWS, maxrows=LIST_ROWS)
        draw_list_controls(list_row, "batch_stl.collection_actions", use_clipboard=True)

        p_stats = stats.get("presets", {}).get(scene.batch_stl_preset_index, {"cols": 0, "objs": 0, "exp": 0})
        draw_stats_table(content_col, [
            (p_stats['cols'], ICONS['COLLECTION']),
            (p_stats['objs'], ICONS['OBJECT']),
            (format_count(p_stats), ICONS['SWEEP'])
        ], lead=lambda row: draw_override_buttons(row, active_col and active_col.nodegroups, is_collection=True))

        if active_col:
            draw_overrides_table(content_col, context.window_manager, active_col.nodegroups, True, f"Overrides [ {active_col.collection_name or 'Shared'} ]", is_locked=any_exporting)


class VIEW3D_PT_batch_export_stl_objects(bpy.types.Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Combi Export"
    bl_label = "Objects"

    @classmethod
    def poll(cls, context):
        active_preset = get_active_preset(context.scene)
        if not active_preset: return False
        return get_active_collection(active_preset) is not None

    def draw_header(self, context):
        self.layout.label(text="", icon=ICONS['OBJECT'])

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        any_exporting = is_any_exporting()
        active_preset = get_active_preset(scene)
        stats = _ui_cache.get("stats", {})

        layout.enabled = not any_exporting
        active_col = get_active_collection(active_preset)
        active_obj = get_active_object(active_col)

        content_col = layout.column(align=True)
        list_box = content_col.box()
        list_box.template_list("BATCH_STL_UL_objects", "", active_col, "objects", active_col, "object_index", rows=5)

        c_idx = active_preset.collection_index
        col_key = (scene.batch_stl_preset_index, c_idx)
        c_stats = stats.get("cols", {}).get(col_key, {"objs": 0, "exp": 0})
        draw_stats_table(content_col, [
            (c_stats['objs'], ICONS['OBJECT']),
            (format_count(c_stats), ICONS['SWEEP'])
        ], lead=lambda row: draw_override_buttons(row, active_obj and active_obj.nodegroups))

        if active_obj:
            draw_overrides_table(content_col, context.window_manager, active_obj.nodegroups, False, f"Overrides [ {active_obj.name} ]", is_locked=any_exporting)

# Panels show in registration order
classes = (BATCH_STL_UL_presets, BATCH_STL_UL_collections, BATCH_STL_UL_objects, BATCH_STL_UL_console_logs,
           VIEW3D_PT_batch_export_stl_main, VIEW3D_PT_batch_export_stl_info, VIEW3D_PT_batch_export_stl_presets,
           VIEW3D_PT_batch_export_stl_collections, VIEW3D_PT_batch_export_stl_objects)
