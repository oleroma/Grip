"""Combination engine: the override stack flattened into MockOverrides and resolved (most specific level wins), its
parameter pools, and the branch walker that generates every variant with its folders and filename tokens
(ARCHITECTURE.md, Scoping & Inheritance, Branching & Merging)."""
import math

import bpy

from .common import COUNT_LIMIT, MAX_SWEEP_STEPS
from .nodes import clean_node_name, get_menu_switch_items
from .naming import SCOPE_KINDS, segment_tags, split_path_parts, split_tag_parts, value_field_anchors, value_parts
from .fields import parse_number, string_sweep_values, sweep_numbers

def get_input_value(inp):
    if inp.override_type == 'BOOLEAN': return inp.value_menu.lower() == 'true'
    elif inp.override_type == 'INT':
        try: return int(inp.value_string)
        except ValueError: return 0
    elif inp.override_type == 'FLOAT':
        try: return float(inp.value_string)
        except ValueError: return 0.0
    elif inp.override_type == 'STRING': return inp.value_string
    elif inp.override_type == 'MENU': return inp.value_menu
    return None

# More specific levels win: an Object override replaces the Collection/Preset/Global value of the same socket.
LEVEL_RANK = {"NONE": -1, "GLOBAL": 0, "PRESET": 1, "COLLECTION": 2, "OBJECT": 3}

def override_param_key(ovr, input_name):
    """Identity of one overridden socket, independent of the hierarchy level that defines it."""
    pg_name = ovr.parent_group_ptr.name if ovr.parent_group_ptr else ""
    node = clean_node_name(ovr.node_name) if ovr.override_target == 'NODE' else ""
    return (ovr.override_target, pg_name, node, input_name)

def resolve_overrides(overrides):
    """Drop inherited values of a socket whenever a more specific level also defines that socket."""
    best_rank = {}
    for ovr in overrides:
        rank = LEVEL_RANK.get(ovr.level, -1)
        for inp in ovr.inputs:
            key = override_param_key(ovr, inp.input_name)
            best_rank[key] = max(best_rank.get(key, rank), rank)

    resolved = []
    for ovr in overrides:
        rank = LEVEL_RANK.get(ovr.level, -1)
        kept = [inp for inp in ovr.inputs if best_rank[override_param_key(ovr, inp.input_name)] == rank]
        naming = tuple(getattr(ovr, k, "") for k in ("ng_sub_path", "node_sub_path", "ng_tag", "node_tag"))
        # A block whose values are all replaced keeps its sub-folder and tag, like a block without inputs: they name
        # what the stack puts below them, wherever its values come from (a Global '\G' over Size keeps G/ when an
        # object sets its own Size)
        if kept or not ovr.inputs or any(naming): resolved.append(MockOverride(ovr.override_target, ovr.parent_group_ptr, ovr.node_name, kept, ovr.level, *naming, getattr(ovr, "group_uid", None)))
    return resolved

def get_override_signature(overrides):
    """Hashable fingerprint of everything that decides which variants an object gets and how they are named."""
    sig = []
    for ovr in overrides:
        inputs_sig = tuple(
            (inp.input_name, inp.override_type, get_input_value(inp), inp.use_sweep, inp.sweep_range,
             inp.sweep_start, inp.sweep_step, inp.sweep_count,
             inp.use_tag, inp.tag, inp.use_dir, inp.dir_tag)
            for inp in ovr.inputs
        )
        block_sig = tuple(getattr(ovr, k, "") for k in ("ng_sub_path", "node_sub_path", "ng_tag", "node_tag"))
        sig.append((ovr.level, override_param_key(ovr, ""), block_sig, inputs_sig))
    return tuple(sig)

class MockInput:
    def __init__(self, base_inp, override_val, is_temp=False):
        self.input_name = getattr(base_inp, 'input_name', getattr(base_inp, 'name', ''))
        self.name = self.input_name
        self.override_type = base_inp.override_type
        source = override_val if is_temp else base_inp
        self.use_tag = getattr(source, "use_tag", False)
        self.tag = getattr(source, "tag", "")
        self.use_dir = getattr(source, "use_dir", False)
        self.dir_tag = getattr(source, "dir_tag", "")
        self.use_sweep = getattr(source, "use_sweep", False)
        self.sweep_range = getattr(source, "sweep_range", "")
        self.sweep_start = getattr(source, "sweep_start", "0")
        self.sweep_step = getattr(source, "sweep_step", "1")
        self.sweep_count = getattr(source, "sweep_count", "2")
        self._val = override_val
        self._is_temp = is_temp

    @property
    def value_string(self): return self._val.value_string if self._is_temp else str(self._val)
    @property
    def value_menu(self): return self._val.value_menu if self._is_temp else str(self._val)

class MockOverride:
    def __init__(self, target, ptr, node_name, inputs, level="NONE", ng_sub_path="", node_sub_path="", ng_tag="", node_tag="", group_uid=None):
        self.override_target = target
        self.parent_group_ptr = ptr
        self.node_name = node_name
        self.inputs = inputs
        self.level = level
        self.ng_sub_path = ng_sub_path
        self.node_sub_path = node_sub_path
        self.ng_tag = ng_tag
        self.node_tag = node_tag
        self.group_uid = group_uid  # the override-table node group this node belongs to (see _known_branch_dirs)

def get_sorted_values(ng_ptr, node_obj, inp, values):
    menu_order = {}
    if inp and getattr(inp, "override_type", "") == 'MENU':
        items = get_menu_switch_items(ng_ptr, getattr(node_obj, "name", ""), getattr(inp, "name", "")) if ng_ptr else []
        menu_order = {val: idx for idx, val in enumerate(items)}

    def value_sort_key(x):
        idx, val = x
        if val is None:
            return (float('-inf'), idx)
        if getattr(val, "use_sweep", False):
            if inp.override_type in ('FLOAT', 'INT'):
                try: return (float(val.sweep_start), idx)
                except ValueError: return (float('-inf'), idx)
            return ("", idx) if getattr(inp, "override_type", "") == 'STRING' else (0, idx)
        else:
            if inp.override_type in ('FLOAT', 'INT'):
                try:
                    return (float(val.value_string), idx)
                except ValueError:
                    return (float('-inf'), idx)
            if inp.override_type == 'STRING': return (val.value_string, idx)
            if inp.override_type in ('MENU', 'BOOLEAN'): return (menu_order.get(val.value_menu, float('inf')), idx)
            return (0, idx)

    indexed_values = list(enumerate(values))
    indexed_values.sort(key=value_sort_key)
    return indexed_values

def get_flat_overrides(nodegroups, level="NONE"):
    overrides = []
    if not nodegroups: return overrides
    for ng in nodegroups:
        ng_ptr = bpy.data.node_groups.get(ng.group_name)
        if not ng_ptr: continue
        for node in ng.nodes:
            target = 'MODIFIER' if not node.name or node.name == "<Modifier Interface>" else 'NODE'

            temp_inputs = []
            for inp in node.inputs:
                for _, val in get_sorted_values(ng_ptr, node, inp, inp.values):
                    temp_inputs.append(MockInput(inp, val, is_temp=True))

            block_fields = (getattr(ng, "sub_path", ""), getattr(node, "sub_path", ""), getattr(ng, "tag", ""), getattr(node, "tag", ""))
            if temp_inputs or any(block_fields):
                overrides.append(MockOverride(target, ng_ptr, node.name, temp_inputs, level, *block_fields, ng.as_pointer()))
    return overrides

def parse_sweep_values(ovr, inp):
    if inp.override_type == 'BOOLEAN':
        return [True, False]
    elif inp.override_type == 'STRING':
        return string_sweep_values(inp.sweep_range) or [""]
    elif inp.override_type in ['INT', 'FLOAT']:
        # Validation flags every fallback below (see number_sweep_values); they only keep imported data drawable
        is_float = (inp.override_type == 'FLOAT')
        try: start = parse_number(getattr(inp, "sweep_start", "0"), inp.override_type)
        except ValueError: start = 0.0 if is_float else 0
        try: step = parse_number(getattr(inp, "sweep_step", "1"), inp.override_type)
        except ValueError: step = 1.0 if is_float else 1
        try: count = int(getattr(inp, "sweep_count", "2"))
        except ValueError: count = 2
        return sweep_numbers(start, step, min(max(count, 1), MAX_SWEEP_STEPS), inp.override_type)
    elif inp.override_type == 'MENU':
        items = get_menu_switch_items(ovr.parent_group_ptr, ovr.node_name, inp.input_name)
        return items if items else [""]
    return []

def _build_override_pools(overrides):
    grouped_inputs = {}
    for ovr in overrides:
        for inp in ovr.inputs:
            grouped_inputs.setdefault(override_param_key(ovr, inp.input_name), []).append((ovr, inp))

    pools = []
    for pairs in grouped_inputs.values():
        value_groups = {}
        for ovr, inp in pairs:
            vals_to_process = parse_sweep_values(ovr, inp) if getattr(inp, "use_sweep", False) else [get_input_value(inp)]
            for val in vals_to_process:
                value_groups.setdefault(val, []).append((ovr, MockInput(inp, val)))
        if value_groups: pools.append(list(value_groups.values()))
    return pools

def count_override_combinations(overrides, cache=None, limit=COUNT_LIMIT):
    """Number of variants. When no value can fall outside a branch, every combination of values is a variant and the
    count is the product of the parameter pool sizes. Otherwise the variants are enumerated, which stops above `limit`
    (the result is then limit + 1; None counts them all). With `cache` (a dict), objects with the same overrides are
    counted once."""
    sig = None
    if cache is not None:
        sig = get_override_signature(overrides)
        if sig in cache: return cache[sig]
    known_before = _known_branch_dirs(overrides)
    if _has_branch_anchors(overrides, known_before):
        count = 0
        for _ in generate_named_combinations(overrides, known_before):
            count += 1
            if limit is not None and count > limit: break
    else:
        count = math.prod(len(pool) for pool in _build_override_pools(overrides))
    if cache is not None: cache[sig] = count
    return count

def count_and_keep_combinations(overrides, keep):
    """(number of variants, the variants or None), for a caller that needs the number before it goes through them (the
    worker's progress total). With branch anchors only enumerating counts them, so up to `keep` variants are kept from
    that pass instead of being generated twice (None when there are more). Without anchors the count is a product and
    nothing is kept: generating costs little more than reading a list would."""
    known_before = _known_branch_dirs(overrides)
    if not _has_branch_anchors(overrides, known_before):
        return math.prod(len(pool) for pool in _build_override_pools(overrides)), None
    count, kept = 0, []
    for variant in generate_named_combinations(overrides, known_before):
        count += 1
        if kept is not None:
            if count > keep: kept = None
            else: kept.append(variant)
    return count, kept

def _has_branch_anchors(overrides, known_before):
    """Whether a block or an explicitly named value names a branch name created above it. Only then can a value be
    inactive in some branches (see walk_override_branch)."""
    for ovr in overrides:
        known = known_before.get(id(ovr), frozenset())
        for is_group, block_dirs, block_tags in _block_name_parts(ovr):
            b_known = known_before.get(("group", id(ovr)), known) if is_group else known
            block_tags = segment_tags(block_tags, lambda n: ("tag", n) in b_known)
            if any(("dir", n) in b_known for n in block_dirs) or any(("tag", n) in b_known for n in block_tags): return True
        for inp in ovr.inputs:
            known_inp = known_before.get((id(ovr), inp.input_name), known)
            for kind, anchors in value_field_anchors(inp).items():
                if kind == "tag": anchors = segment_tags(anchors, lambda n: ("tag", n) in known_inp)
                if any((kind, n) in known_inp for n in anchors): return True
    return False

# The walker runs once or more per variant, so what it derives from an override or a pool value (which never change
# during a generation) is cached on the MockOverride / MockInput.
def _cached(obj, attr, compute):
    value = obj.__dict__.get(attr)
    if value is None: value = obj.__dict__[attr] = compute()
    return value

def _block_name_parts(ovr):
    """[(is_group, folder names, filename tokens)] of an override's blocks that name any: its node group's sub-folder
    and tag, then its node's. Each block is placed on its own (like the UI's BranchScope.enter_block), so a node
    folder / tag can merge into its group's."""
    return _cached(ovr, "_block_parts", lambda: [parts for parts in (
        (True, split_path_parts(ovr.ng_sub_path), split_tag_parts(ovr.ng_tag)),
        (False, split_path_parts(ovr.node_sub_path), split_tag_parts(ovr.node_tag))) if parts[1] or parts[2]])

def _input_names(ovr):
    return _cached(ovr, "_input_names", lambda: list(dict.fromkeys(i.input_name for i in ovr.inputs)))

def _param_key(ovr, input_name):
    keys = _cached(ovr, "_param_keys", dict)
    key = keys.get(input_name)
    if key is None: key = keys[input_name] = override_param_key(ovr, input_name)
    return key

def _value_name_parts(inp):
    """{kind: (anchors, names)} one pool value contributes (see value_name_parts)."""
    return _cached(inp, "_name_parts", lambda: value_parts(inp, get_input_value(inp)))

def value_branch_names(ovr, inp, kind, known=frozenset()):
    """Folder names (kind "dir") or filename tokens (kind "tag") one override value can generate (every sweep step
    included), anchors first, in order. Tag chains are split against the names `known` before the value."""
    vals = parse_sweep_values(ovr, inp) if getattr(inp, "use_sweep", False) else [get_input_value(inp)]
    names = []
    for val in vals:
        anchors, new = value_parts(inp, val)[kind]
        if kind == "tag": anchors = segment_tags(anchors, lambda n: (kind, n) in known)
        names.extend(n for n in anchors + new if n not in names)
    return names

def _known_branch_dirs(overrides):
    """Branch names that values *earlier* in the stack can generate, as ("dir", folder) / ("tag", token) keys.

    Keyed by id(ovr) for the override's own sub-paths and tags and by (id(ovr), input_name) for its values.
    A sub-path, tag or value naming one of these is an anchor into an existing branch, not a new folder / token.
    ("group", id(ovr)) holds what was known before the override's node group: the group's sub-folder and tag are
    placed once, before its first node (walk_override_branch), and mean the same for all of its nodes (a value of the
    first node merging into the group's folder must not turn that folder into a branch name for the next node)."""
    known_before = {}
    known = set()
    group, group_known = None, frozenset()
    for ovr in overrides:
        uid = getattr(ovr, "group_uid", None)
        if uid is None or uid != group: group, group_known = uid, frozenset(known)
        known_before[("group", id(ovr))] = group_known
        known_before[id(ovr)] = frozenset(known)
        for input_name in dict.fromkeys(getattr(i, "input_name", "") for i in ovr.inputs):
            known_inp = known_before[(id(ovr), input_name)] = frozenset(known)
            for inp in ovr.inputs:
                if getattr(inp, "input_name", "") == input_name:
                    known.update((kind, n) for kind in SCOPE_KINDS for n in value_branch_names(ovr, inp, kind, known_inp))
    return known_before

def _place_dir_parts(parts, branch, known, kind="dir"):
    """Resolve requested folder names (kind "dir") or filename tokens (kind "tag") against the ones this
    permutation branch already has.

    - A name already in the branch (any ancestor / any earlier token, not only the last one) merges into it;
      several anchors ("C/2") must appear in that order.
    - A token is a chain split at '_' (segment_tag): 'B_2' merges into B, then into 2; tokens already in the branch
      (else known upstream) keep their '_'.
    - A branch name (generated by an earlier value) missing from this branch means the override belongs to another
      branch: returns None (inactive here).
    - Any other name is new: a folder below the branch's deepest folder, or a token at the end of the filename.
    Returns the list of new names to append."""
    if kind == "tag":
        # Read the chain the way this branch spells it; only a name it cannot place falls back to the known names
        # (which then decide whether the override belongs to another branch).
        local = segment_tags(parts, lambda n: n in branch)
        parts = local if all(n in branch for n in local) else segment_tags(parts, lambda n: n in branch or (kind, n) in known)
    new_parts = []
    search_from = 0
    for p in parts:
        try:
            search_from = branch.index(p, search_from) + 1
            continue
        except ValueError:
            pass
        if (kind, p) in known: return None
        new_parts.append(p)
    return new_parts

def _place_block(ovr, is_group, dir_branch, tag_branch, known):
    """(new folders, new tokens) of an override's node group block (`is_group`) or node block, or None when it belongs
    to another branch. A block without a sub-folder or tag adds nothing."""
    block = next(((dirs, tags) for g, dirs, tags in _block_name_parts(ovr) if g == is_group), None)
    if block is None: return [], []
    b_dirs = _place_dir_parts(block[0], dir_branch, known, "dir")
    b_tags = _place_dir_parts(block[1], tag_branch, known, "tag")
    if b_dirs is None or b_tags is None: return None
    return b_dirs, b_tags

def walk_override_branch(overrides, combo, known_before=None):
    """Walk overrides top-to-bottom for one (possibly partial) combo, tracking the branch's folders and filename
    tokens.

    Returns (active_input_ids, tags_by_level, paths_by_level). Both combination generation and export naming use this
    walker, so they always agree on which overrides apply to which branch."""
    if known_before is None: known_before = _known_branch_dirs(overrides)
    chosen = {}
    for ovr, inp in combo:
        chosen.setdefault(id(ovr), {})[getattr(inp, "input_name", "")] = inp

    dir_branch, tag_branch = [], []
    paths_by_level = {"GLOBAL": [], "PRESET": [], "COLLECTION": [], "OBJECT": [], "NONE": []}
    tags_by_level = {"GLOBAL": [], "PRESET": [], "COLLECTION": [], "OBJECT": [], "NONE": []}
    active = set()
    processed_params = set()
    group, group_new = None, None

    for ovr in overrides:
        level = getattr(ovr, "level", "NONE")
        known = known_before.get(id(ovr), frozenset())

        uid = getattr(ovr, "group_uid", None)
        if uid is None or uid != group:
            # A node group's sub-folder and tag are placed once, before its first node, so they mean the same for
            # every node (like the UI's BranchScope.enter_block). Placed again after a node added them, a chain 'Y/2'
            # (Y new, 2 upstream) would find Y behind 2 and drop the later nodes. They go in with the first node that
            # applies, so a branch where none of its nodes applies never gets them (BranchScope.close_group mirrors it).
            group = uid
            group_new = _place_block(ovr, True, dir_branch, tag_branch, known_before.get(("group", id(ovr)), known))
        if group_new is None: continue
        new_dirs, new_tags = list(group_new[0]), list(group_new[1])
        placed = _place_block(ovr, False, dir_branch + new_dirs, tag_branch + new_tags, known)
        if placed is None: continue
        new_dirs += placed[0]; new_tags += placed[1]
        group_new = [], []
        dir_branch.extend(new_dirs); paths_by_level[level].extend(new_dirs)
        tag_branch.extend(new_tags); tags_by_level[level].extend(new_tags)

        ovr_chosen = chosen.get(id(ovr))
        if not ovr_chosen: continue
        for input_name in _input_names(ovr):
            inp = ovr_chosen.get(input_name)
            if inp is None: continue
            known_inp = known_before.get((id(ovr), input_name), known)
            parts = _value_name_parts(inp)
            # Only the anchors typed in a field are placed; names derived from the value are always new
            new_dirs = _place_dir_parts(parts["dir"][0], dir_branch, known_inp, "dir")
            new_tags = _place_dir_parts(parts["tag"][0], tag_branch, known_inp, "tag")
            if new_dirs is None or new_tags is None: continue
            new_dirs, new_tags = new_dirs + parts["dir"][1], new_tags + parts["tag"][1]
            active.add(id(inp))

            param_key = _param_key(ovr, input_name)
            if param_key in processed_params: continue
            processed_params.add(param_key)
            dir_branch.extend(new_dirs); paths_by_level[level].extend(new_dirs)
            tag_branch.extend(new_tags); tags_by_level[level].extend(new_tags)

    return active, tags_by_level, paths_by_level

def generate_named_combinations(overrides, known_before=None):
    """Yield (combo, tags_by_level, paths_by_level) for every variant. The naming comes from the same walk that decides
    which values are active, so it costs nothing extra."""
    if known_before is None: known_before = _known_branch_dirs(overrides)
    pools = _build_override_pools(overrides)
    if not pools:
        _, tags_by_level, paths_by_level = walk_override_branch(overrides, [], known_before)
        yield [], tags_by_level, paths_by_level
        return
    # Without anchors every value applies to every branch: no pruning walks, and every combination is unique.
    anchors = _has_branch_anchors(overrides, known_before)
    seen = set()

    def recurse(pool_idx, combo):
        if pool_idx == len(pools):
            active, tags_by_level, paths_by_level = walk_override_branch(overrides, combo, known_before)
            if not anchors:
                yield combo, tags_by_level, paths_by_level
                return
            final = [(o, i) for o, i in combo if id(i) in active]
            key = tuple((id(o), getattr(i, "input_name", ""), repr(get_input_value(i))) for o, i in final)
            if key not in seen:
                seen.add(key)
                yield final, tags_by_level, paths_by_level
            return

        any_active = False
        for variation in pools[pool_idx]:
            trial = combo + variation
            if not anchors or any(id(i) in walk_override_branch(overrides, trial, known_before)[0] for _, i in variation):
                any_active = True
                yield from recurse(pool_idx + 1, trial)
        if not any_active:
            # No value of this parameter belongs to the current branch: leave it at its default.
            yield from recurse(pool_idx + 1, combo)

    yield from recurse(0, [])
