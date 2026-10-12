"""Property groups of the data model with their update, get, set and search callbacks, including the computed value
and naming fields of the override table (ARCHITECTURE.md, Data Model & Hierarchy, Expression Fields)."""
import os
import re

import bpy

from .common import (DELETED, MAX_SWEEP_STEPS, edit_callback, in_raw_edits, mark_dirty, nested_edits, push_search_undo,
    raw_edits)
from .nodes import (clean_node_name, default_value_text, get_menu_switch_items, get_socket_default_value,
    get_supported_inputs, get_target_node_names, infer_input_type)
from .naming import (SCOPE_KINDS, VALUE_SLOT, legacy_naming_template, split_path_parts, split_tag_parts, underscore_spaces,
    value_name_parts)
from .fields import (add_value, compose_block_naming, compose_value_field, expr_text, fields_text, _is_open, lex_expr,
    name_permutations, parse_block_naming, parse_number, parse_value_field, _render_typed, same_fields, _slot_run,
    _split_bare, split_field, value_expr, value_fields, _value_readers, _value_runs, value_specs)
from .scope import OTHER_KIND, BranchScope, naming_completions, scope_dead
from .data import get_active_collection, get_active_object, get_active_preset

# Undo: Blender records an undo step for every property edited in the UI, and the operators below declare
# 'UNDO' in bl_options, so property updates only refresh the UI cache. The exception is search fields
# (any StringProperty with search=, including the folder fields with upstream suggestions), which push their own
# step through a labelled edit_callback / search_field_update. A search field without a label gets no undo step.

class HierarchyIterator:
    """Helper to yield all active node groups in the hierarchy context."""
    @staticmethod
    def iterate_lists(scene):
        yield ('GLOBAL', scene.batch_stl_global_nodegroups)
        preset = get_active_preset(scene)
        if not preset: return
        yield ('PRESET', preset.nodegroups)
        col = get_active_collection(preset)
        if not col: return
        yield ('COLLECTION', col.nodegroups)
        obj = get_active_object(col)
        if not obj: return
        yield ('OBJECT', obj.nodegroups)

    @staticmethod
    def iterate(scene):
        for lvl, container in HierarchyIterator.iterate_lists(scene):
            for ng in container: yield (lvl, ng)

def sync_input_type(inp, scene, update_value=True):
    for _lvl, ng in HierarchyIterator.iterate(scene):
        for n in ng.nodes:
            if inp in n.inputs.values():
                ng_ptr = bpy.data.node_groups.get(ng.group_name)
                new_type = infer_input_type(ng_ptr, n.name, inp.name)
                # These writes are consistent data, so the edit callbacks must not run on them: they treat an emptied
                # value as "delete it", which would remove the input (and with it its node and node group).
                with raw_edits():
                    inp.override_type = new_type
                    if update_value:
                        items = get_menu_switch_items(ng_ptr, n.name, inp.name) if new_type == 'MENU' else []
                        text = default_value_text(new_type, get_socket_default_value(ng_ptr, n.name, inp.name), items)
                        field = "value_menu" if new_type in ('BOOLEAN', 'MENU') else "value_string"
                        for v in inp.values:
                            v.use_sweep = False
                            if text is not None: setattr(v, field, text)
                return

@edit_callback("Edit Override Input", "name", "prev_name")
def on_input_name_update(self, context):
    is_duplicate = False
    is_invalid = False
    my_node = None
    my_ng = None
    other_input = None
    if hasattr(context.scene, "batch_stl_presets"):
        for _lvl, ng in HierarchyIterator.iterate(context.scene):
            for n in ng.nodes:
                if self in n.inputs.values():
                    my_node = n
                    my_ng = ng
                    for other in n.inputs:
                        if other != self and other.name == self.name and self.name != "":
                            is_duplicate = True
                            other_input = other
                            break
                    break
            if my_node: break

    if my_node and my_ng and self.name != "":
        ng_ptr = bpy.data.node_groups.get(my_ng.group_name)
        source_inputs = get_supported_inputs(ng_ptr, my_node.name)
        if self.name not in source_inputs:
            is_invalid = True

    if self.name == "" and my_node:
        for i, inp in enumerate(my_node.inputs):
            if inp == self:
                with raw_edits(): my_node.inputs.remove(i)
                if len(my_node.inputs) == 0:
                    my_node.name = ""
                return DELETED

    if is_invalid:
        with raw_edits():
            self.name = self.prev_name
        return

    if is_duplicate:
        with raw_edits():
            self.name = self.prev_name

        my_idx = -1
        other_idx = -1
        if my_node:
            for i, inp in enumerate(my_node.inputs):
                if inp == self: my_idx = i
                elif inp == other_input: other_idx = i

            if my_idx != -1 and other_idx != -1:
                i, j = my_idx, other_idx
                if i > j:
                    i, j = j, i
                my_node.inputs.move(j, i)
                my_node.inputs.move(i+1, j)
        return

    if self.name == "" and self.prev_name != "":
        with raw_edits(): self.name = self.prev_name
        return

    name_changed = (self.prev_name != self.name)
    self.prev_name = self.name
    if name_changed and self.name != "":
        self.values.clear()
        add_value(self.values)

    if hasattr(context.scene, "batch_stl_presets"):
        try: sync_input_type(self, context.scene, update_value=name_changed)
        except Exception: pass

def search_target_node_cb(self, context, edit_text):
    if not context or not getattr(context, "scene", None): return ["<Modifier Interface>"]
    if edit_text == self.name: edit_text = ""
    res = []

    for _lvl, ng in HierarchyIterator.iterate(context.scene):
        if self in ng.nodes.values():
            ng_ptr = bpy.data.node_groups.get(ng.group_name)
            if ng_ptr:
                if get_supported_inputs(ng_ptr, "<Modifier Interface>"):
                    res.append("<Modifier Interface>")

                for node in sorted(ng_ptr.nodes, key=lambda n: n.type == 'GROUP_OUTPUT'):
                    if node.type != 'GROUP_INPUT':
                        if get_supported_inputs(ng_ptr, node.name):
                            val = f"{node.name} [{node.node_tree.name if node.type == 'GROUP' and getattr(node, 'node_tree', None) else node.type}]"
                            if not edit_text or edit_text.lower() in val.lower(): res.append(val)
            else:
                res.append("<Modifier Interface>")
            return res

    res.append("<Modifier Interface>")
    return res

def search_input_name_cb(self, context, edit_text):
    """Sockets of the target node (or modifier interface) that can still be overridden."""
    if not context or not getattr(context, "scene", None): return []
    if edit_text == self.name: edit_text = ""
    for _lvl, ng in HierarchyIterator.iterate(context.scene):
        for n in ng.nodes:
            if self in n.inputs.values():
                names = get_supported_inputs(bpy.data.node_groups.get(ng.group_name), n.name)
                return [s for s in names if edit_text.lower() in s.lower()] if edit_text else names
    return []

def on_value_update(prop_name, label=""):
    @edit_callback(label, prop_name, "prev_" + prop_name)
    def update(self, context):
        is_duplicate = False
        is_invalid = False
        my_input = None
        for _lvl, ng in HierarchyIterator.iterate(context.scene):
            for n in ng.nodes:
                for i in n.inputs:
                    if self in i.values.values():
                        my_input = i
                        my_val = getattr(self, prop_name)

                        if prop_name == "value_menu" and my_val != "":
                            if i.override_type == 'BOOLEAN':
                                items = ['True', 'False']
                            else:
                                ng_ptr = bpy.data.node_groups.get(ng.group_name)
                                items = get_menu_switch_items(ng_ptr, n.name, i.name) if ng_ptr else []
                            # Items that cannot be listed are checked when exporting (a rejected value is logged)
                            if items and my_val not in items:
                                is_invalid = True

                        if prop_name in ("value_string", "sweep_start", "sweep_step"):
                            if my_val != "":
                                try:
                                    if i.override_type in ('FLOAT', 'INT'): parse_number(my_val, i.override_type)
                                except ValueError:
                                    is_invalid = True
                            elif prop_name != "value_string":
                                is_invalid = True

                        if prop_name == "sweep_count":
                            try:
                                if not 1 <= int(my_val) <= MAX_SWEEP_STEPS: is_invalid = True
                            except ValueError:
                                is_invalid = True

                        for other in i.values:
                            if other != self and getattr(other, prop_name) == my_val and not getattr(other, "use_sweep", False) and not getattr(self, "use_sweep", False):
                                is_duplicate = True
                                break
                        break
                if my_input: break
            if my_input: break

        my_val = getattr(self, prop_name)
        if my_input and prop_name in ("value_string", "value_menu") and my_val == "":
            for idx, val_item in enumerate(my_input.values):
                if val_item == self:
                    with raw_edits(): my_input.values.remove(idx)
                    if len(my_input.values) == 0:
                        my_input.name = ""
                    return DELETED

        if is_invalid or is_duplicate:
            with raw_edits(): setattr(self, prop_name, getattr(self, "prev_" + prop_name))
        else:
            setattr(self, "prev_" + prop_name, getattr(self, prop_name))
    return update

def on_name_field_update(prop_name):
    """Update callback of a plain name field (tag, sub-folder, preset root): spaces are not allowed in names, so they
    are written as '_' (underscore_spaces)."""
    def update(self, context):
        val = getattr(self, prop_name)
        fixed = underscore_spaces(val)
        if fixed != val: setattr(self, prop_name, fixed)
        mark_dirty()
    return update

_PATH_STEP = re.compile(r"(\w+)\[(\d+)\]")

def upstream_scope(item):
    """(BranchScope, context) at `item` in the override stack: the names that exist before it and the branches the
    blocks around it are merged into.

    Order matches the exporter: Global, Preset, Collection, Object lists; inside a list node groups and nodes top to
    bottom; inside a block its sub-folder, then its tag, then (for a node) its inputs. Only what comes before `item`
    exists yet."""
    scope, empty = BranchScope(), frozenset()
    scene = item.id_data
    try: steps = _PATH_STEP.findall(item.path_from_id())
    except (ValueError, AttributeError): return scope, empty
    if not steps: return scope, empty

    # Resolve the chain of override lists that lead to the item, plus the item's position in its own list.
    lists, pos = [scene.batch_stl_global_nodegroups], {}
    if steps[0][0] == "batch_stl_presets":
        owner = scene
        for attr, idx in steps:
            if attr == "nodegroups" or attr == "batch_stl_global_nodegroups": break
            owner = getattr(owner, attr)[int(idx)]
            lists.append(owner.nodegroups)
    for attr, idx in steps:
        if attr in ("nodegroups", "batch_stl_global_nodegroups", "nodes", "inputs"): pos[attr if attr != "batch_stl_global_nodegroups" else "nodegroups"] = int(idx)
    own = lists[-1]

    def add_node(ng, ng_ptr, node, ng_ctx, ng_alive, input_limit=None):
        n_ctx, res = scope.enter_block(node, ng_ctx, ng, node, ng_alive)
        alive = ng_alive and not scope_dead(res)
        for i_idx, inp in enumerate(node.inputs):
            if input_limit is not None and i_idx >= input_limit: break
            scope.add_input(ng, ng_ptr, node, inp, n_ctx, alive)
        return n_ctx

    def add_group(ng):
        ng_ptr = bpy.data.node_groups.get(ng.group_name)
        ng_ctx, res = scope.enter_block(ng, empty, ng)
        for node in ng.nodes: add_node(ng, ng_ptr, node, ng_ctx, not scope_dead(res))
        scope.close_group()

    for lst in lists[:-1]:
        for ng in lst: add_group(ng)

    g = pos.get("nodegroups", len(own))
    for ng in list(own)[:g]: add_group(ng)
    if g >= len(own) or not isinstance(item, (BatchSTLNode, BatchSTLValue)): return scope, empty

    # Inside the item's own group: its sub-folder / tag (and the node's, for a value) already exist and set the context.
    ng = own[g]
    ng_ptr = bpy.data.node_groups.get(ng.group_name)
    ng_ctx, res = scope.enter_block(ng, empty, ng)
    ng_alive = not scope_dead(res)
    n_pos = pos.get("nodes", 0)
    for node in list(ng.nodes)[:n_pos]: add_node(ng, ng_ptr, node, ng_ctx, ng_alive)
    if isinstance(item, BatchSTLNode) or n_pos >= len(ng.nodes): return scope, ng_ctx
    return scope, add_node(ng, ng_ptr, ng.nodes[n_pos], ng_ctx, ng_alive, input_limit=pos.get("inputs", 0))

def search_results(typed, offers, tab=()):
    """Search list from [(text, description)]: duplicates dropped, and the text as typed first. Blender highlights the
    only result (or one equal to the text) and Enter applies the highlighted one, so deleting a mark and pressing Enter
    would bring the mark back: Enter keeps the text as typed, arrow down picks a suggestion.

    Tab fills the longest start that every result beginning with the typed text shares (exact, case-sensitive), and
    ends the edit when only one result begins with it. `tab` are the texts Tab should reach: a name completed with the
    separator after it ('\\A\\'), so the next name can be typed right away. When they share more than the typed text,
    the results that would stop Tab short (the text as typed among them) are left out; the callers offer two results
    per completion (one would end the edit)."""
    unique = {}
    for text, desc in offers: unique.setdefault(text, desc)
    reach = [t for t in tab if t.startswith(typed) and t != typed]
    if typed and reach:
        prefix = os.path.commonprefix(reach)
        if len(prefix) > len(typed):
            return [(t, d) for t, d in unique.items() if not t.startswith(typed) or t.startswith(prefix)]
    if typed and typed not in unique: unique = {typed: "Keep as typed", **unique}
    return list(unique.items())

_VALUE_PATH = re.compile(r"^(.*nodegroups\[\d+\])\.nodes\[(\d+)\]\.inputs\[(\d+)\]\.values\[\d+\]$")

def value_owner(val):
    """(node group, node, input) entries a BatchSTLValue belongs to, or None."""
    try:
        m = _VALUE_PATH.match(val.path_from_id())
        if not m: return None
        ng = val.id_data.path_resolve(m.group(1))
        node = ng.nodes[int(m.group(2))]
        return ng, node, node.inputs[int(m.group(3))]
    except (ValueError, AttributeError, IndexError, KeyError, TypeError): return None

def input_items(ng, node, inp):
    """Items a menu or boolean value can take; None for other types, or a menu that lists none."""
    if inp.override_type == 'BOOLEAN': return ['True', 'False']
    if inp.override_type == 'MENU':
        return get_menu_switch_items(bpy.data.node_groups.get(ng.group_name), node.name, inp.name) or None
    return None

# Edits of an expression field: set() parses and writes the stored fields, then update() (called right after it)
# records the undo step or deletes the value. Keyed by as_pointer() of the edited item.
_expr_edits = {}

def get_value_expr(self):
    owner = value_owner(self)
    if owner is None: return value_expr(self, 'STRING')
    ng, node, inp = owner
    return value_expr(self, inp.override_type, input_items(ng, node, inp))

def _taken_check(inp, val):
    """taken(fields) for a value of `inp`: whether another single value of the input already has that value."""
    others = [f for f in (value_fields(o, inp.override_type) for o in inp.values if o != val and not o.use_sweep) if f]
    return lambda fields: not fields["use_sweep"] and any(same_fields(inp.override_type, o, fields) for o in others)

def _upstream_check(item):
    """upstream(kind, name) for a field: whether a folder / token of that name exists above it (see _infer_value). The
    scope is only built when it is asked."""
    scope = []
    def upstream(kind, name):
        if not scope: scope.append(upstream_scope(item)[0])
        return (kind, name) in scope[0]
    return upstream

def set_value_expr(self, text):
    """Parse a value field (see the comment above lex_expr) into the value's fields. Text that does not fit the input
    type, a single value another value of the input already has, or a name that cannot be a file name is rejected: the
    field shows the stored value again. An empty field deletes the value, and '*' (every menu item, True and False)
    replaces the input's other values like Shift + '+' (both in the update, on_value_expr_update)."""
    owner = value_owner(self)
    if owner is None: return
    ng, node, inp = owner
    if not text.strip():
        _expr_edits[self.as_pointer()] = "delete"
        return
    override_type = inp.override_type
    stored, taken = value_fields(self, override_type), _taken_check(inp, self)
    try: fields, templates = parse_value_field(text, override_type, input_items(ng, node, inp), stored, taken, value_specs(self), _upstream_check(self))
    except ValueError: return
    if taken(fields): return
    # Typing over a blank value (a string just added as a permutation shows '\') fills in the value, and '*' makes the
    # input permute: without a section typed, the value keeps its naming
    sweep_all = fields["use_sweep"] and override_type in ('BOOLEAN', 'MENU')
    if (stored is None or sweep_all) and all(t is None for t in templates.values()): templates = value_specs(self)
    fields = dict(fields, use_dir=templates["dir"] is not None, dir_tag=templates["dir"] or "", use_tag=templates["tag"] is not None, tag=templates["tag"] or "")
    changed = {p: v for p, v in fields.items() if getattr(self, p) != v}
    solo = sweep_all and (changed or len(inp.values) > 1)
    if not changed and not solo: return
    with raw_edits():
        for p, v in changed.items(): setattr(self, p, v)
    _expr_edits[self.as_pointer()] = "solo" if solo else "changed"

def on_value_expr_update(self, context):
    edit = _expr_edits.pop(self.as_pointer(), None)
    mark_dirty()
    if edit is None or in_raw_edits(): return
    if edit in ("delete", "solo"):
        owner = value_owner(self)
        if owner is None: return
        inp = owner[2]
        idx = next((i for i, v in enumerate(inp.values) if v == self), None)
        if idx is None: return
        with nested_edits():
            if edit == "delete":
                with raw_edits(): inp.values.remove(idx)
                if len(inp.values) == 0: inp.name = ""  # deletes the input, and an emptied node and node group
            else:
                # '*' already holds every item: the other values go, and the sweep gets a folder per value when plain
                with raw_edits():
                    for j in reversed(range(len(inp.values))):
                        if j != idx: inp.values.remove(j)
                name_permutations(inp.values, 0)
    push_search_undo("Edit Override Value")

def _quote_suggested(kind):
    """How a suggested upstream name is typed in a section (see _render_typed)."""
    return lambda name: _render_typed(name, "", kind == "dir")

def _chain_end(kind, chars, closed, is_value):
    """Index in a section's chars where the folder name / token holding the value starts, or None when the section does
    not hold it (`is_value` finds it). The typed names before it are the chain the search completes."""
    if _is_open(kind, chars, closed): return None
    if kind == "dir":
        for s, e in reversed(_split_bare(chars, "\\/")):
            if _value_runs(chars[s:e], is_value): return s
        return None
    run = _slot_run(chars, is_value, "_/")
    return run[0] if run else None

def search_value_expr(self, context, edit_text):
    """Search list of a value field (see the comment above lex_expr). Free text is still allowed.
    - Menus and booleans list their items (and '*', every item) when the field opens and while the value written before
      the sections is not one of them, keeping the naming.
    - The text can be read another way (see _infer_value): the other reading is offered too ('16\\' when '\\16' merges
      into an upstream 16, '\\"big"' when '\\big' changes a string value).
    - The section typed last completes its chain of typed names (naming_completions) with upstream names that can
      exist in this branch and still fit the other section, each twice: with the value after it ('\\A\\15') and ending
      in the separator ('\\A\\', the value follows too), which Tab fills (see search_results).
    - A section not typed yet is offered: one per value ('\\15'), and while no section is typed also merged into each
      upstream name ('\\B\\15', '_B_15')."""
    owner = value_owner(self)
    if owner is None: return []
    ng, node, inp = owner
    override_type = inp.override_type
    items = input_items(ng, node, inp)
    read, readable = _value_readers(override_type, items)
    stored, stored_templates, taken = value_fields(self, override_type), value_specs(self), _taken_check(inp, self)
    upstream = _upstream_check(self)
    # Suggestions are read back as the field reads them when picked
    def compose(fields, templates): return compose_value_field(fields, templates, override_type, items, (stored, stored_templates), upstream)
    def parse(text, **kw):
        args = dict(stored=stored, taken=taken, stored_templates=stored_templates, upstream=upstream)
        args.update(kw)
        try: return parse_value_field(text, override_type, items, **args)
        except ValueError: return None, None
    def same(a, b):
        return a[0] is not None and b[0] is not None and same_fields(override_type, a[0], b[0]) and a[1] == b[1]
    opened = edit_text == value_expr(self, override_type, items)
    fields, templates = parse(edit_text)
    if fields is None: templates = stored_templates
    chars = lex_expr(edit_text)
    try: value_chars, sections = split_field(chars, readable)
    except ValueError: value_chars, sections = [], []
    offers, tab = [], []

    if items is not None and (opened or (value_chars and not readable(value_chars))):
        query = "" if opened else expr_text(value_chars).lower()
        offers += [(compose({"use_sweep": False, "value_menu": i}, templates), f"Value · {i}") for i in items if query in i.lower()]
        if not query:
            offers.append((compose({"use_sweep": True}, templates), "True and False" if override_type == 'BOOLEAN' else f"Every item ({len(items)} values)"))
    if fields is None: return search_results(edit_text, offers)

    if not opened:
        main = (fields, templates)
        as_value = parse(edit_text, stored=None)  # names read as the value wherever they can be
        if as_value[0] is not None and not same(as_value, main):
            offers.append((compose(*as_value), f"Value {fields_text(as_value[0], override_type)}"))
        as_names = parse(edit_text, stored_templates=None, upstream=None)  # names kept as typed, the value stays
        if as_names[0] is not None and stored is not None and not same(as_names, main):
            offers.append((compose(*as_names), f"Typed names, the value stays {fields_text(stored, override_type)}"))

    scope, ctx = upstream_scope(self)
    vtext = fields_text(fields, override_type)
    def is_value(run):
        try: return same_fields(override_type, read(run), fields)
        except ValueError: return False
    def other_parts(kind):
        template = templates[OTHER_KIND[kind]]
        return value_name_parts("", template, OTHER_KIND[kind])[0] if template is not None else []
    if sections:
        kind, body, start, closed = sections[-1]
        at = _chain_end(kind, body, closed, is_value)
        chain, tail = (body, vtext) if at is None else (body[:at], edit_text[body[at][2]:].rstrip())
        head = edit_text[:chars[start][2] + 1]
        # A section holding only typed names lists their alternatives when the field opens
        current = stored_templates[kind] if stored_templates[kind] is not None and VALUE_SLOT not in stored_templates[kind] else ""
        if kind == "dir": current = current.replace("/", "\\")
        completions = naming_completions(scope, ctx, kind, expr_text(chain), current, other_parts(kind), False, _quote_suggested(kind))
        for spec, desc in completions:
            offers.append((head + spec + tail, desc))
            # The chain alone, while it is typed at the end of the section: the value follows its separator
            if at is None:
                tab.append(head + spec)
                offers.append((head + spec, desc))
        if not completions:
            if not chain: offers.append((head + tail, "Folder per value" if kind == "dir" else "Filename token per value"))
            elif at is None and _is_open(kind, body, closed): offers.append((edit_text.rstrip() + tail, "Then the value"))
    for kind in SCOPE_KINDS:
        if templates[kind] is not None: continue
        offers.append((compose(fields, {**templates, kind: VALUE_SLOT}), "Folder per value" if kind == "dir" else "Filename token per value"))
        if not sections:
            offers += [(compose(fields, {**templates, kind: legacy_naming_template(spec, kind)}), desc)
                       for spec, desc in naming_completions(scope, ctx, kind, "", "", [], False)]
    return search_results(edit_text, offers, tab)

def get_block_naming(self):
    return compose_block_naming(self.sub_path, self.tag)

def set_block_naming(self, text):
    """Parse a node group / node naming field ('\\C\\2\\_B', see parse_block_naming) into its sub-folder and tag. Text
    without a mark is a folder: 'C/2' is '\\C\\2'."""
    try: sub_path, tag = parse_block_naming(text)
    except ValueError: return
    changed = {p: v for p, v in (("sub_path", sub_path), ("tag", tag)) if getattr(self, p) != v}
    if not changed: return
    with raw_edits():
        for p, v in changed.items(): setattr(self, p, v)
    _expr_edits[self.as_pointer()] = "changed"

def block_naming_update(label):
    def update(self, context):
        edit = _expr_edits.pop(self.as_pointer(), None)
        mark_dirty()
        if edit and not in_raw_edits(): push_search_undo(label)
    return update

def search_block_naming(self, context, edit_text):
    """Search list of a node group / node naming field ('\\C\\2\\_B'). The section typed last completes with upstream
    names that can exist in this branch and still fit the other section ('\\C\\' offers '\\C\\1', '\\C\\2', ...); a
    section not typed yet is offered merged into each upstream name. Text typed without a mark is a folder."""
    chars = lex_expr(edit_text)
    try: sections = split_field(chars)[1]
    except ValueError: sections = []
    typed = {kind: expr_text(body) for kind, body, _start, _closed in sections}
    scope, ctx = upstream_scope(self)
    stored = {"dir": self.sub_path, "tag": self.tag}
    def other_parts(kind):
        text = typed.get(OTHER_KIND[kind])
        return split_path_parts(text) if kind == "tag" else split_tag_parts(text)
    offers, tab = [], []
    if sections:
        kind, body, start, _closed = sections[-1]
        head = edit_text[:chars[start][2] + 1] if start is not None else "\\"  # a bare folder gets its '\'
        completions = naming_completions(scope, ctx, kind, expr_text(body), stored[kind], other_parts(kind), True, _quote_suggested(kind))
        # Each name ends in its separator, which Tab fills so the next name can be typed ('\\C\\' means folder C)
        sep, other_mark = ("\\", "_") if kind == "dir" else ("_", "\\")
        for spec, desc in completions:
            tab.append(head + spec + sep)
            offers.append((head + spec + sep, desc))
        # Tab ends the edit when one result begins with the text: the other section's mark goes on after the only name
        reach = [t for t in tab if t.startswith(edit_text) and t != edit_text]
        if len(reach) == 1 and OTHER_KIND[kind] not in typed:
            offers.append((reach[0] + other_mark, "Then a filename token" if kind == "dir" else "Then a folder"))
    try: sub_path, tag = parse_block_naming(edit_text)
    except ValueError: sub_path = tag = None
    for kind in SCOPE_KINDS:
        if kind in typed or sub_path is None: continue
        for spec, desc in naming_completions(scope, ctx, kind, "", "", other_parts(kind), True):
            offers.append((compose_block_naming(spec, tag) if kind == "dir" else compose_block_naming(sub_path, spec), desc))
    return search_results(edit_text, offers, tab)

class BatchSTLLogLine(bpy.types.PropertyGroup): text: bpy.props.StringProperty()

EXPR_DESCRIPTION = (
    "The value and its naming: '\\' starts the folder, '_' the filename token, and the value goes where it is written.\n"
    "15: value only · \\15: folder 15 · _15: token 15 · \\15\\_15: both\n"
    "\\big, _big: your name instead of the value (the value stays, hover the icon to see it) · \\15_mm, \\size_15, _15_mm: the value joined with text\n"
    "\\B\\15, _B_15: B, then the value. Names that exist upstream merge into that branch (\\C\\2\\15)\n"
    "\\15 → \\16 changes the value, unless 16 exists upstream (then it merges). 16\\big: value and names at once\n"
    "Tab completes an upstream name with its separator (\\A → \\A\\), so the next name can be typed\n"
    "Sweeps: \\0:0.5:5 (start:step:count), _{a, b} (strings), \\* (every menu item, True and False; replaces the other values)\n"
    "Quoted text is literal: \"a_b\". Clear the field to delete the value")

BLOCK_NAMING_DESCRIPTION = (
    "Sub-folder and filename tokens of everything in this block: '\\' for folders, '_' for tokens.\n"
    "\\X: folder X · _X: token X · \\C\\2\\_B: folders C/2 and token B\n"
    "Names that exist upstream merge into that branch: \\B applies only to the B branches\n"
    "Tab completes an upstream name with its separator (\\B → \\B\\), so the next name can be typed")

class BatchSTLValue(bpy.types.PropertyGroup):
    # The table edits the value and its naming through `expr` (see lex_expr); the fields below are the stored data.
    expr: bpy.props.StringProperty(name="Value", description=EXPR_DESCRIPTION, get=get_value_expr, set=set_value_expr, search=search_value_expr, update=on_value_expr_update)
    prev_value_string: bpy.props.StringProperty(default="", options={'HIDDEN'})
    value_string: bpy.props.StringProperty(name="Value", default="", update=on_value_update("value_string"))
    prev_value_menu: bpy.props.StringProperty(default="", options={'HIDDEN'})
    value_menu: bpy.props.StringProperty(name="Value", default="", update=on_value_update("value_menu", "Edit Override Value"))
    use_tag: bpy.props.BoolProperty(name="Use Tag", description="Add this value to the filename, named by `tag` (the '_' section)", default=False, update=mark_dirty)
    tag: bpy.props.StringProperty(name="Tag", description="Filename tokens, '*' where the value goes: '*' the value, 'name' replaces it, 'B_*' token B then the value, '*_mm' one token 15_mm (see VALUE_SLOT)", default="", update=mark_dirty)
    use_dir: bpy.props.BoolProperty(name="Use Dir", description="Put this value's files in a sub-folder, named by `dir_tag` (the '\\' section)", default=True, update=mark_dirty)
    dir_tag: bpy.props.StringProperty(name="Directory", description="Folder names separated by '/', '*' where the value goes: '*' the value, 'name' replaces it, 'B/*' folder B then the value, 'size_*' one folder size_15 (see VALUE_SLOT)", default="", update=mark_dirty)
    use_sweep: bpy.props.BoolProperty(name="Sweep", default=False, update=mark_dirty)
    sweep_range: bpy.props.StringProperty(name="Sweep Range", default="", update=mark_dirty)
    prev_sweep_start: bpy.props.StringProperty(default="0", options={'HIDDEN'})
    sweep_start: bpy.props.StringProperty(name="Start", description="Value start", default="0", update=on_value_update("sweep_start"))
    prev_sweep_step: bpy.props.StringProperty(default="1", options={'HIDDEN'})
    sweep_step: bpy.props.StringProperty(name="Step", description="Value step", default="1", update=on_value_update("sweep_step"))
    prev_sweep_count: bpy.props.StringProperty(default="2", options={'HIDDEN'})
    sweep_count: bpy.props.StringProperty(name="Steps", description=f"Number of steps (1 to {MAX_SWEEP_STEPS})", default="2", update=on_value_update("sweep_count"))

class BatchSTLInput(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(name="Input Socket", default="", search=search_input_name_cb, update=on_input_name_update)
    prev_name: bpy.props.StringProperty(default="", options={'HIDDEN'})
    override_type: bpy.props.StringProperty(default='FLOAT', update=mark_dirty)
    values: bpy.props.CollectionProperty(type=BatchSTLValue)

@edit_callback("Edit Override Node", "name", "prev_name")
def on_node_name_update(self, context):
    is_duplicate = False
    is_invalid = False
    my_ng = None
    for _lvl, ng in HierarchyIterator.iterate(context.scene):
        if self in ng.nodes.values():
            my_ng = ng
            is_duplicate = any(other != self and clean_node_name(other.name) == clean_node_name(self.name) for other in ng.nodes) and self.name != ""
            break

    if self.name == "" and my_ng:
        for i, n in enumerate(my_ng.nodes):
            if n == self:
                with raw_edits(): my_ng.nodes.remove(i)
                if len(my_ng.nodes) == 0:
                    my_ng.group_name = ""
                return DELETED

    if self.name != "" and my_ng:
        ng_ptr = bpy.data.node_groups.get(my_ng.group_name)
        targets = get_target_node_names(ng_ptr) if ng_ptr else []
        if self.name not in targets:
            is_invalid = True

    if is_invalid or is_duplicate or (self.name == "" and self.prev_name != ""):
        with raw_edits(): self.name = self.prev_name
        return

    if self.prev_name != self.name and self.name != "" and my_ng:
        self.inputs.clear()

        ng_ptr = bpy.data.node_groups.get(my_ng.group_name)
        source_inputs = get_supported_inputs(ng_ptr, self.name)

        if source_inputs:
            inp = self.inputs.add()
            inp.name = source_inputs[0]
        else:
            add_value(self.inputs.add().values)

    self.prev_name = self.name

class BatchSTLNode(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(name="Target Node", default="", search=search_target_node_cb, update=on_node_name_update, description="Select <Modifier Interface> to target the modifier directly")
    prev_name: bpy.props.StringProperty(default="", options={'HIDDEN'})
    naming: bpy.props.StringProperty(name="Naming", description=BLOCK_NAMING_DESCRIPTION, get=get_block_naming, set=set_block_naming, search=search_block_naming, update=block_naming_update("Edit Override Node Naming"))
    sub_path: bpy.props.StringProperty(name="Sub-folder", default="", description="Sub-folder path added by this node (the '\\' section)", update=mark_dirty)
    tag: bpy.props.StringProperty(name="Tag", default="", description="Filename tokens added by this node (the '_' section)", update=mark_dirty)
    inputs: bpy.props.CollectionProperty(type=BatchSTLInput)

@edit_callback("Edit Override Node Group", "group_name", "prev_group_name")
def on_group_name_update(self, context):
    is_duplicate = False
    my_container = None
    for _lvl, container in HierarchyIterator.iterate_lists(context.scene):
        if self in container.values():
            my_container = container
            is_duplicate = any(other != self and other.group_name == self.group_name for other in container) and self.group_name != ""
            break

    if self.group_name == "" and my_container:
        for i, ng in enumerate(my_container):
            if ng == self:
                with raw_edits(): my_container.remove(i)
                return DELETED

    is_invalid = self.group_name != "" and not bpy.data.node_groups.get(self.group_name)

    if is_invalid or is_duplicate or (self.group_name == "" and self.prev_group_name != ""):
        with raw_edits(): self.group_name = self.prev_group_name
        return

    # A blank group (new, or a pasted duplicate that had its name cleared) keeps the nodes it already has when it is
    # given a group; switching from one group to another starts over with that group's first node.
    prev = self.prev_group_name
    if prev != self.group_name and self.group_name != "" and not (prev == "" and self.nodes):
        self.nodes.clear()
        targets = get_target_node_names(bpy.data.node_groups.get(self.group_name))
        if targets:
            self.nodes.add().name = targets[0]

    self.prev_group_name = self.group_name

def search_group_name_cb(self, context, edit_text):
    if not context or not getattr(context, "scene", None): return []
    if edit_text == getattr(self, "group_name", ""): edit_text = ""
    res = [ng.name for ng in bpy.data.node_groups]
    return [item for item in res if edit_text.lower() in item.lower()] if edit_text else res

class BatchSTLNodeGroup(bpy.types.PropertyGroup):
    group_name: bpy.props.StringProperty(name="Node Group", default="", search=search_group_name_cb, update=on_group_name_update)
    prev_group_name: bpy.props.StringProperty(default="", options={'HIDDEN'})
    naming: bpy.props.StringProperty(name="Naming", description=BLOCK_NAMING_DESCRIPTION, get=get_block_naming, set=set_block_naming, search=search_block_naming, update=block_naming_update("Edit Override Group Naming"))
    sub_path: bpy.props.StringProperty(name="Sub-folder", default="", description="Sub-folder path added by this node group (the '\\' section)", update=mark_dirty)
    tag: bpy.props.StringProperty(name="Tag", default="", description="Filename tokens added by this node group (the '_' section)", update=mark_dirty)
    nodes: bpy.props.CollectionProperty(type=BatchSTLNode)

def get_export_name(self):
    return underscore_spaces(self.name_override or self.name)

def set_export_name(self, value):
    # Empty, or the object's own name (as the file name has it, without spaces), means "follow the object" (renames included)
    value = underscore_spaces(value.strip())
    self.name_override = "" if value == underscore_spaces(self.name) else value
    mark_dirty()

class BatchSTLObject(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty()
    name_override: bpy.props.StringProperty(default="", options={'HIDDEN'})
    # Shows the object name until edited; clearing the field returns to the object name
    export_name: bpy.props.StringProperty(name="File Name", description="Name the exported files start with. Clear the field to use the object name again", get=get_export_name, set=set_export_name, options={'SKIP_SAVE'})
    # session_uid of the object, to follow renames (see sync_collection_objects); not an ID pointer, which adds a user
    obj_uid: bpy.props.IntProperty(default=0, options={'HIDDEN'})
    export: bpy.props.BoolProperty(default=True, update=mark_dirty)
    tag: bpy.props.StringProperty(name="Tag", default="", description="Filename token(s), '/' between tokens. Placed in hierarchy order: Global, Preset, Collection, Object", update=on_name_field_update("tag"))
    sub_path: bpy.props.StringProperty(name="Sub-folder", default="", update=on_name_field_update("sub_path"))
    nodegroups: bpy.props.CollectionProperty(type=BatchSTLNodeGroup)

@edit_callback("Edit Collection", "collection_name", "prev_collection_name")
def on_collection_name_update(self, context):
    self.prev_collection_name = self.collection_name

class BatchSTLCollection(bpy.types.PropertyGroup):
    collection_name: bpy.props.StringProperty(name="Collection", default="", update=on_collection_name_update)
    prev_collection_name: bpy.props.StringProperty(default="", options={'HIDDEN'})
    use_tag: bpy.props.BoolProperty(name="Use Tag", default=True, update=mark_dirty)
    tag: bpy.props.StringProperty(name="Tag", default="", description="Filename token(s), '/' between tokens. Placed in hierarchy order: Global, Preset, Collection, Object", update=on_name_field_update("tag"))
    sub_path: bpy.props.StringProperty(name="Sub-folder", default="", update=on_name_field_update("sub_path"))
    objects: bpy.props.CollectionProperty(type=BatchSTLObject)
    object_index: bpy.props.IntProperty(default=0, update=mark_dirty)
    nodegroups: bpy.props.CollectionProperty(type=BatchSTLNodeGroup)

class BatchSTLJob(bpy.types.PropertyGroup):
    """Runtime state of one preset's export. Lives on the WindowManager so undo never rolls it back; cleared when a
    file loads. Keyed by preset uid and scene session_uid (see get_job)."""
    preset_uid: bpy.props.StringProperty(default="")
    scene_uid: bpy.props.IntProperty(default=0)
    is_exporting: bpy.props.BoolProperty(default=False)
    cancel_export: bpy.props.BoolProperty(default=False)
    export_progress: bpy.props.FloatProperty(name="Progress", default=0.0, min=0.0, max=1.0)
    export_status: bpy.props.StringProperty(default="")
    console_logs: bpy.props.CollectionProperty(type=BatchSTLLogLine)
    console_index: bpy.props.IntProperty(default=0)

class BatchSTLExportPreset(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(name="Preset Name", default="New Preset", update=mark_dirty)
    uid: bpy.props.StringProperty(default="", options={'HIDDEN'})  # stable identity of a running export's preset
    preset_prefix: bpy.props.StringProperty(name="Preset Root Directory", default="", update=on_name_field_update("preset_prefix"))
    collections: bpy.props.CollectionProperty(type=BatchSTLCollection)
    collection_index: bpy.props.IntProperty(name="Collection Index", default=0, update=mark_dirty)
    nodegroups: bpy.props.CollectionProperty(type=BatchSTLNodeGroup)
    last_export_time: bpy.props.FloatProperty(name="Last Export Time", default=0.0)

# Registration order: a property group after the ones it holds
classes = (BatchSTLLogLine, BatchSTLJob, BatchSTLValue, BatchSTLInput, BatchSTLNode, BatchSTLNodeGroup, BatchSTLObject,
           BatchSTLCollection, BatchSTLExportPreset)
