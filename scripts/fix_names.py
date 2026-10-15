r"""Fix typos and stray spaces in the names of Grip.blend, keeping export presets and tracking working.

Run it inside Blender on Grip.blend (Scripting workspace > Text Editor > Open this file > Run Script). With
DRY_RUN = True (the default) it changes nothing: it prints a table of what it would rename, where each name is used
and what else it would update. With DRY_RUN = False it applies the same table. The report goes to the system console
(Window > Toggle System Console on Windows); set REPORT_TEXT to also get it in a text block.

What it renames:
- node group names: the words in WORD_FIXES, double spaces and spaces at the ends (a .001 suffix stays);
- input names of node groups (what the modifier panel and group nodes show): the same fixes;
- group nodes named after a renamed group, so they keep following their group (as scripts/rename.py names them).
A rename whose new name is already taken (another group, another input of the same group, another node in the same
tree) is skipped and reported.

What it only reports: menu items (the 'low ' item of subdivision level), objects, collections, modifiers, panels,
output sockets, node labels, other node names, sockets of other nodes (bundle items), and text blocks that mention an
old name. Renaming those by hand needs more care (menu values and bundle keys are stored by name).

What keeps working:
- Links, modifier values and defaults: a renamed input keeps its identifier, which is what they use.
- combi_export presets in every scene: overrides store their node group, node and input by name, so every reference
  to a renamed name is rewritten in the same run. The add-on must be enabled for that; with it disabled the names its
  presets use are skipped.
- blender_tracking: tracked groups are stored as pointers and follow the rename. tracking.json keys change on the
  next save.
- Drivers and animation: Blender rewrites the paths to a renamed node itself (those that work; the report warns
  about any it left).
A name that is also stored where the script cannot update it safely (a linked scene, a driver expression, another
add-on's setting, ...) is not renamed; the report says where it was found.

How to use it:
1. Save a copy of Grip.blend in the same folder (File > Save Copy) and open it, with combi_export and
   blender_tracking enabled. Saved next to Grip.blend, the copy writes the same blender/tracking.json.
2. Run with DRY_RUN = True. Read the renames, the skipped names and the references it would update. Names that
   other code still spells (scripts, tools, add-ons) can be held back with KEEP.
3. Export the presets you want to check into a scratch folder (set the add-on's root folder there).
4. Set DRY_RUN = False and run again. The report ends with a second pass, which should find nothing left to rename.
5. Export the same presets into a second scratch folder and compare the two. The add-on writes a fixed STL header,
   so the files should be byte-identical. In Blender's Python Console:
       import filecmp; filecmp.dircmp(r"C:\before", r"C:\after").report_full_closure()
   lists the differing files; there should be none.
6. Remove this script's text block if you opened it in the Text Editor, then save. blender_tracking rewrites
   tracking.json: its diff should only rename keys and change the link lines that show a renamed name, with no value
   changes (tools/tracking_diff pairs renamed keys as "probably renamed").
7. When it all matches, replace Grip.blend with the copy (or run the script on Grip.blend itself), re-export the
   preset JSON copies (blender/GripV_preset.json, blender/GripX_preset.json), and update the docs and code that
   spell the old names.
"""
import re
import sys
from collections import defaultdict

import bpy

DRY_RUN = True      # True: only report. False: rename.
REPORT_TEXT = ""    # name of a text block to also write the report to, e.g. "fix_names report" ("" = console only);
                    # writing it is the one change a dry run then makes

# Misspelled words and their fix. A word only matches whole (no letter right before or after it), and its
# capitalised form is fixed too. Used for node group and input names, and to find the names that are only reported.
WORD_FIXES = {
    "wdith": "width",
    "heght": "height",
    "stiick": "stick",
    "sheild": "shield",
    "sbdiv": "subdiv",
    "paramters": "parameters",
    "paramteters": "parameters",
    "contols": "controls",
    "neighboor": "neighbour",
    "suppprts": "supports",
    "postion": "position",
    "roker": "rocker",
    "voroni": "voronoi",
    "holllow": "hollow",
    "syle": "style",
    "coer": "cover",
    "coVer": "cover",   # 'coVer base'
}

# Old names to leave as they are for now, e.g. ("GripX contols",) while code that spells it is not updated yet.
# Group nodes named after a kept group keep their name too.
KEEP = ()

# Custom property paths, as the report prints them, that may hold an old name without blocking its rename
IGNORED_PROPERTIES = ()

MODIFIER_INTERFACE = "<Modifier Interface>"     # combi_export's node name for an override of a modifier input
NUMBER_SUFFIX = re.compile(r"\.\d{3,}$")        # the .001 Blender adds to repeated names
MAX_NODE_NAME = 63                              # bytes; Blender cuts longer node names
NODE_PATH = re.compile(r'nodes\["[^"]*"\]')     # a node in a driver or animation path

# Add-on data this script reads and updates itself, so the scan for other stored names leaves it out
HANDLED_PROPERTIES = {"batch_stl_presets", "batch_stl_global_nodegroups", "batch_stl_jobs",
                      "geonodes_json_exporter_groups", "geonodes_json_exporter_collections"}
# Datablocks whose custom properties and add-on settings are searched for old names
PROPERTY_OWNERS = ("scenes", "objects", "collections", "node_groups", "materials", "window_managers", "workspaces")
# Datablocks whose drivers and actions are searched (embedded node trees are added)
ANIMATED = ("objects", "scenes", "materials", "worlds", "meshes", "curves", "lights", "cameras", "shape_keys",
            "textures", "collections")


# --- Names -------------------------------------------------------------------------------------------------------

def _word_fixes():
    fixes = dict(WORD_FIXES)
    for wrong, right in WORD_FIXES.items():
        fixes.setdefault(wrong[0].upper() + wrong[1:], right[0].upper() + right[1:])
    words = sorted(fixes, key=len, reverse=True)
    return fixes, re.compile(r"(?<![A-Za-z])(" + "|".join(map(re.escape, words)) + r")(?![A-Za-z])")

FIXES, WORD_RE = _word_fixes()

def fix_text(text):
    """The text with WORD_FIXES applied, runs of spaces collapsed and no spaces at the ends."""
    text = WORD_RE.sub(lambda m: FIXES[m.group(1)], text)
    return re.sub(r" {2,}", " ", text).strip(" ")

def split_number(name):
    """('name', '.001') for a name with a Blender number suffix, ('name', '') otherwise."""
    m = NUMBER_SUFFIX.search(name)
    return (name[:m.start()], m.group()) if m else (name, "")

def fixed_name(name, numbered=True):
    """The corrected name. With `numbered` a .001 suffix stays and the fix applies to the part before it."""
    base, suffix = split_number(name) if numbered else (name, "")
    return (fix_text(base) or base) + suffix

def following_name(node_name, old_group, new_group):
    """The new name of a group node named after its group ('X', 'X.001', 'X.normal'), or None if it has its own."""
    if node_name == old_group:
        return new_group
    if node_name.startswith(old_group + "."):
        return new_group + node_name[len(old_group):]
    base, suffix = split_number(node_name)
    if base == split_number(old_group)[0]:
        return split_number(new_group)[0] + suffix
    return None

def q(name):
    """A name in quotes, so spaces at the ends stay visible."""
    return f"'{name}'"


# --- Reading the file --------------------------------------------------------------------------------------------

def is_local(data):
    return data.library is None and getattr(data, "override_library", None) is None

def node_trees():
    """Every node tree: node groups and the trees embedded in materials, worlds, lights, ..."""
    trees = list(bpy.data.node_groups)
    for attr in ("materials", "worlds", "lights", "textures", "linestyles", "scenes"):
        for data in getattr(bpy.data, attr, ()):
            tree = getattr(data, "node_tree", None)
            if tree:
                trees.append(tree)
    return trees

def interface_sockets(group, in_out):
    return [i for i in group.interface.items_tree if i.item_type == 'SOCKET' and i.in_out == in_out]

def stored_props(data):
    """Where the add-on properties (bpy.props) of a datablock are stored, readable with the add-on disabled too."""
    get = getattr(data, "bl_system_properties_get", None)
    return get() if get else data       # before Blender 5.0 they were plain ID properties

def addon_root(data, key):
    """(value, enabled) of an add-on property of a datablock: through the add-on when it is enabled, else read from
    its stored data, which this script never writes."""
    if hasattr(data, key):
        return getattr(data, key), True
    props = stored_props(data)
    return (props.get(key, ()) if props is not None else ()), False

def field(entry, key, default=""):
    """A property of an add-on entry: an add-on struct or stored ID properties."""
    if hasattr(entry, "bl_rna"):
        return getattr(entry, key, default)
    return entry.get(key, default)

def clean_node_name(name):
    """The node name in a combi_export node field ('node [group]' -> 'node'), as the add-on reads it."""
    return name.split(" [")[0].strip() if name else ""

def raw_edits_of(entry):
    """combi_export's raw_edits() for an entry of the enabled add-on, or None. Inside it the add-on's callbacks only
    take the written name as the new 'previous' value, as for its own paste and JSON import."""
    package = type(entry).__module__.rpartition(".")[0]
    common = sys.modules.get(package + ".common")
    return getattr(common, "raw_edits", None)

def action_fcurves(anim):
    """F-curves of the action assigned to animation data (of its slot, for a layered action)."""
    action, slot = anim.action, getattr(anim, "action_slot", None)
    if hasattr(action, "layers"):
        for layer in action.layers if slot else ():
            for strip in layer.strips:
                bag = strip.channelbag(slot) if hasattr(strip, "channelbag") else None
                if bag:
                    yield from bag.fcurves
    else:
        yield from getattr(action, "fcurves", ())

def animated_datablocks():
    seen = set()
    for data in [d for attr in ANIMATED for d in getattr(bpy.data, attr, ())] + node_trees():
        if data.as_pointer() not in seen:
            seen.add(data.as_pointer())
            yield data

def anim_texts():
    """Yields (datablock, text, kind, target) for every path and expression of drivers and assigned actions. target
    is the datablock a path is resolved on."""
    for data in animated_datablocks():
        anim = getattr(data, "animation_data", None)
        if not anim:
            continue
        for fc in anim.drivers:
            yield data, fc.data_path, "driver path", data
            yield data, fc.driver.expression, "driver expression", None
            for var in fc.driver.variables:
                for target in var.targets:
                    if target.data_path:
                        yield data, target.data_path, "driver variable", target.id
        if anim.action:
            for fc in action_fcurves(anim):
                yield data, fc.data_path, "animation path", data

def walk_strings(path, value):
    if isinstance(value, str):
        yield path, value
    elif isinstance(value, bpy.types.ID):
        return      # a pointer to another datablock, searched on its own
    elif hasattr(value, "keys"):
        for key in value.keys():
            yield from walk_strings(f'{path}["{key}"]', value[key])
    elif isinstance(value, (list, tuple)):
        for i, item in enumerate(value):
            yield from walk_strings(f"{path}[{i}]", item)

def stored_texts():
    """Yields (path, text) for the text values of custom properties and add-on settings of the main datablocks."""
    for attr in PROPERTY_OWNERS:
        for data in getattr(bpy.data, attr, ()):
            base = f'bpy.data.{attr}["{data.name}"]'
            sources = [(data, '{}["{}"]')]                  # custom properties
            props = stored_props(data)
            if props is not None and props is not data:
                sources.append((props, "{}.{}"))            # add-on settings
            for group, path in sources:
                for key in group.keys():
                    if key not in HANDLED_PROPERTIES:
                        yield from walk_strings(path.format(base, key), group[key])

def users_text(group, nodes_by_group, mods_by_group):
    """Where a node group is used: its group nodes and modifiers."""
    nodes = nodes_by_group.get(group.as_pointer(), [])
    mods = mods_by_group.get(group.as_pointer(), [])
    parts = []
    if nodes:
        trees = sorted({tree.name for tree, _node in nodes})
        shown = ", ".join(q(t) for t in trees[:3]) + (", ..." if len(trees) > 3 else "")
        parts.append(f"{len(nodes)} group node{'s' * (len(nodes) != 1)} in {shown}")
    if mods:
        objects = sorted({obj.name for obj, _mod in mods})
        shown = ", ".join(q(o) for o in objects[:3]) + (", ..." if len(objects) > 3 else "")
        parts.append(f"modifier on {shown}")
    return "; ".join(parts) or "not used"


# --- Planning ----------------------------------------------------------------------------------------------------

class Rename:
    """One planned rename of a node group, an interface input or a group node (`data`)."""

    def __init__(self, kind, data, old, new, owner=None, parent=None):
        self.kind, self.data, self.old, self.new = kind, data, old, new
        self.owner = owner      # the group of an input, the tree of a node
        self.parent = parent    # the group rename a node follows
        self.skip = None        # why it is not renamed
        self.failed = None      # why applying it failed
        self.done = False
        self.where = ""
        self.also = []

    @property
    def active(self):
        return self.skip is None and self.failed is None and (self.parent is None or self.parent.active)

    @property
    def reason(self):
        if self.skip or self.failed:
            return self.skip or self.failed
        if self.parent and not self.parent.active:
            return f"its group {q(self.parent.old)} is not renamed"
        return ""

    def block(self, reason):
        if self.skip is None:
            self.skip = reason


class Ref:
    """A name stored by combi_export that follows renames: entry.key becomes value() when written."""

    def __init__(self, scene, place, entry, key, old, value, renames):
        self.scene, self.place, self.entry, self.key, self.old = scene, place, entry, key, old
        self.value = value
        self.renames = renames
        self.done = False


def plan_groups(renames):
    names = {g.name for g in bpy.data.node_groups}
    found = []
    for group in bpy.data.node_groups:
        new = fixed_name(group.name)
        if new != group.name:
            r = Rename("group", group, group.name, new)
            if not is_local(group):
                r.block("linked from a library")
            found.append(r)
    block_collisions(found, names, "node group")
    renames += found

def plan_inputs(renames):
    for group in bpy.data.node_groups:
        sockets = interface_sockets(group, 'INPUT')
        found = []
        for item in sockets:
            new = fixed_name(item.name, numbered=False)
            if new != item.name:
                r = Rename("input", item, item.name, new, owner=group)
                if not is_local(group):
                    r.block("its group is linked from a library")
                found.append(r)
        block_collisions(found, {s.name for s in sockets}, f"input of {q(group.name)}")
        renames += found

def plan_nodes(renames):
    groups = {r.data.as_pointer(): r for r in renames if r.kind == "group"}
    for tree in node_trees():
        found = []
        for node in tree.nodes:
            parent = groups.get(node.node_tree.as_pointer()) if node.type == 'GROUP' and node.node_tree else None
            new = following_name(node.name, parent.old, parent.new) if parent else None
            if new is None or new == node.name:
                continue
            r = Rename("node", node, node.name, new, owner=tree, parent=parent)
            if not is_local(tree):
                r.block("in a linked tree")
            elif len(new.encode("utf-8")) > MAX_NODE_NAME:
                r.block(f"longer than the {MAX_NODE_NAME} bytes Blender allows for node names")
            found.append(r)
        block_collisions(found, {n.name for n in tree.nodes}, f"node in {q(tree.name)}")
        renames += found

def block_collisions(found, taken, scope):
    """Skip renames whose new name exists in the scope, or that two different old names would share."""
    olds = defaultdict(set)
    for r in found:
        olds[r.new].add(r.old)
    for r in found:
        if r.new in taken:
            r.block(f"{q(r.new)} already exists ({scope})")
        elif len(olds[r.new]) > 1:
            others = ", ".join(q(o) for o in sorted(olds[r.new] - {r.old}))
            r.block(f"{others} would get the same name ({scope})")

def combi_override_lists(scene):
    """Yields (place, list of node group entries) for every combi_export override list of the scene, and whether
    the add-on is enabled (only then can the entries be written)."""
    global_list, enabled = addon_root(scene, "batch_stl_global_nodegroups")
    presets, _enabled = addon_root(scene, "batch_stl_presets")
    lists = [("global overrides", global_list)]
    for preset in presets:
        place = f"preset {q(field(preset, 'name'))}"
        lists.append((place, field(preset, "nodegroups", ())))
        for col in field(preset, "collections", ()):
            col_place = f"{place} > collection {q(field(col, 'collection_name'))}"
            lists.append((col_place, field(col, "nodegroups", ())))
            for obj in field(col, "objects", ()):
                lists.append((f"{col_place} > object {q(field(obj, 'name'))}", field(obj, "nodegroups", ())))
    return lists, enabled

def find_combi_refs(renames):
    """References of combi_export overrides to renamed names, in every scene. Renames whose references cannot be
    written safely are blocked."""
    active = [r for r in renames if r.active]
    groups = {r.old: r for r in active if r.kind == "group"}
    nodes = {(r.owner.as_pointer(), r.old): r for r in active if r.kind == "node"}
    inputs = {(r.owner.as_pointer(), r.old): r for r in active if r.kind == "input"}
    refs = []

    def new_or_old(r, old):
        return r.new if r and r.active else old

    for scene in bpy.data.scenes:
        lists, enabled = combi_override_lists(scene)
        for place, entries in lists:
            entries = list(entries)
            group_names = [field(ng, "group_name") for ng in entries]
            for ng in entries:
                gname = field(ng, "group_name")
                group = bpy.data.node_groups.get(gname) if gname else None
                found = []
                gr = groups.get(gname)
                if gr and group == gr.data:
                    found.append(Ref(scene, place, ng, "group_name", gname,
                                     lambda gr=gr, old=gname: new_or_old(gr, old), [gr]))
                    if gr.new in group_names:
                        gr.block(f"export overrides in scene {q(scene.name)}, {place}, already list {q(gr.new)}")
                node_entries = list(field(ng, "nodes", ()))
                node_names = [clean_node_name(field(n, "name")) for n in node_entries]
                for n in node_entries:
                    nname = field(n, "name")
                    clean = clean_node_name(nname)
                    target_group = None
                    if clean in ("", MODIFIER_INTERFACE):
                        target_group = group
                    elif group:
                        node = group.nodes.get(clean)
                        nr = nodes.get((group.as_pointer(), clean))
                        br = None
                        bracket = nname[len(nname.split(" [")[0]) + 2:-1] if " [" in nname and nname.endswith("]") else None
                        if node and node.type == 'GROUP' and node.node_tree:
                            target_group = node.node_tree
                            br = groups.get(bracket) if bracket is not None else None
                            br = br if br and br.data == node.node_tree else None
                        if nr or br:
                            def node_text(nr=nr, br=br, clean=clean, bracket=bracket):
                                text = new_or_old(nr, clean)
                                return text if bracket is None else f"{text} [{new_or_old(br, bracket)}]"
                            found.append(Ref(scene, f"{place} > {q(gname)}", n, "name", nname, node_text,
                                             [r for r in (nr, br) if r]))
                            if nr and nr.new in node_names:
                                nr.block(f"export overrides in scene {q(scene.name)}, {place}, already list node "
                                         f"{q(nr.new)} of {q(gname)}")
                    if target_group is None:
                        continue
                    input_entries = list(field(n, "inputs", ()))
                    input_names = [field(i, "name") for i in input_entries]
                    for i in input_entries:
                        iname = field(i, "name")
                        ir = inputs.get((target_group.as_pointer(), iname))
                        if ir:
                            found.append(Ref(scene, f"{place} > {q(gname)} > {q(clean or MODIFIER_INTERFACE)}", i,
                                             "name", iname, lambda ir=ir, old=iname: new_or_old(ir, old), [ir]))
                            if ir.new in input_names:
                                ir.block(f"export overrides in scene {q(scene.name)}, {place}, already list input "
                                         f"{q(ir.new)} of {q(clean or MODIFIER_INTERFACE)}")
                for ref in found:
                    if scene.library:
                        reason = f"used by export overrides of the linked scene {q(scene.name)}"
                    elif not enabled:
                        reason = f"used by export overrides in scene {q(scene.name)}; enable combi_export to update them"
                    elif raw_edits_of(ref.entry) is None:
                        reason = "this combi_export version cannot be updated safely (no raw_edits)"
                    else:
                        reason = None
                    for r in ref.renames:
                        if reason:
                            r.block(reason)
                refs += found
    return refs

def find_unsafe(renames):
    """Block renames whose old name is stored where this script cannot update it: driver expressions, hand-written
    paths, custom properties and settings of other add-ons. Returns {node rename: [paths Blender rewrites, paths
    it leaves]}: Blender rewrites the paths to a renamed node that work, and leaves broken ones."""
    active = [r for r in renames if r.active]
    notes = defaultdict(lambda: [0, 0])
    for data, text, kind, target in anim_texts():
        is_path = kind != "driver expression"
        bare = NODE_PATH.sub("", text) if is_path else text    # node paths are checked against node renames
        for r in active:
            if r.kind == "node" and is_path and f'nodes["{r.old}"]' in text:
                if isinstance(target, bpy.types.NodeTree):
                    if target == r.owner:   # on another tree it names that tree's node
                        try:
                            target.path_resolve(text)
                            notes[r][0] += 1
                        except ValueError:
                            notes[r][1] += 1
                    continue
                r.block(f"named in a {kind} on {q(data.name)} that goes through another datablock: {text}")
            elif f'"{r.old}"' in bare or f"'{r.old}'" in bare:
                r.block(f"named in a {kind} on {q(data.name)}: {text}")
    by_old = defaultdict(list)
    for r in active:
        by_old[r.old].append(r)
    for path, text in stored_texts():
        if path not in IGNORED_PROPERTIES:
            for r in by_old.get(text, ()):
                r.block(f"stored in {path} (add the path to IGNORED_PROPERTIES if it may stay)")
    return notes

def find_report_only(planned):
    """Names with typos or stray spaces that this script does not change: {(kind, name): (fixed, [places])}."""
    found = defaultdict(lambda: [None, []])

    def check(kind, name, place, numbered=False):
        fixed = fixed_name(name, numbered)
        if fixed != name:
            entry = found[(kind, name)]
            entry[0] = fixed
            entry[1].append(place)

    for obj in bpy.data.objects:
        check("object", obj.name, "objects", True)
        for mod in obj.modifiers:
            check("modifier", mod.name, f"on {q(obj.name)}", True)
    for col in bpy.data.collections:
        check("collection", col.name, "collections", True)
    for group in bpy.data.node_groups:
        for item in group.interface.items_tree:
            if item.item_type == 'PANEL':
                check("panel", item.name, q(group.name))
            elif item.in_out == 'OUTPUT':
                check("output", item.name, q(group.name))
    for tree in node_trees():
        for node in tree.nodes:
            place = f"{q(tree.name)} > {q(node.name)}"
            if node.label:
                check("label", node.label, place)
            if node.as_pointer() not in planned:
                check("node", node.name, q(tree.name), True)
            if node.type == 'MENU_SWITCH':
                for item in node.enum_items:
                    check("menu item", item.name, place)
            elif node.type not in ('GROUP', 'GROUP_INPUT', 'GROUP_OUTPUT'):
                for socket in list(node.inputs) + list(node.outputs):
                    check("socket", socket.name, f"{place} ({node.bl_label})")
    return found

def find_texts(renames):
    """Text blocks that mention an old name: [(text, [(old name, first line)])]."""
    olds = sorted({r.old for r in renames if r.active})
    found = []
    for text in bpy.data.texts:
        body = text.as_string()
        if text.name == REPORT_TEXT or "WORD_FIXES = {" in body:
            continue    # this script, opened in the Text Editor, and its report
        lines = body.split("\n")
        hits = []
        for old in olds:
            line = next((i + 1 for i, line in enumerate(lines) if old in line), None)
            if line:
                hits.append((old, line))
        if hits:
            found.append((text, hits))
    return found

def describe(renames, refs, notes):
    """Fill in where each name is used and what else changes with it."""
    nodes_by_group, mods_by_group = defaultdict(list), defaultdict(list)
    for tree in node_trees():
        for node in tree.nodes:
            if node.type == 'GROUP' and node.node_tree:
                nodes_by_group[node.node_tree.as_pointer()].append((tree, node))
    for obj in bpy.data.objects:
        for mod in obj.modifiers:
            if mod.type == 'NODES' and mod.node_group:
                mods_by_group[mod.node_group.as_pointer()].append((obj, mod))
    tracked = defaultdict(list)
    for scene in bpy.data.scenes:
        items, _enabled = addon_root(scene, "geonodes_json_exporter_groups")
        for item in items:
            tree = field(item, "group_ptr", None)
            if tree:
                tracked[tree.as_pointer()].append(scene.name)
    ref_count = defaultdict(int)
    for ref in refs:
        for r in ref.renames:
            ref_count[r] += 1
    for r in renames:
        r.also = []
        if r.kind == "group":
            r.where = users_text(r.data, nodes_by_group, mods_by_group)
            following = sum(1 for o in renames if o.parent is r and o.active)
            if following:
                r.also.append(f"{following} group node{'s follow' if following != 1 else ' follows'}")
            for scene in tracked.get(r.data.as_pointer(), []):
                r.also.append(f"tracked in scene {q(scene)} by pointer, tracking.json key changes on save")
        elif r.kind == "input":
            r.where = f"input of {q(r.owner.name)}; " + users_text(r.owner, nodes_by_group, mods_by_group)
            r.also.append(f"keeps identifier {r.data.identifier} (links, modifier values)")
        else:
            r.where = f"node in {q(r.owner.name)}"
            fixed, broken = notes.get(r, (0, 0))
            if fixed:
                r.also.append(f"Blender rewrites {fixed} driver or animation path{'s' * (fixed != 1)}")
            if broken:
                r.also.append(f"Blender leaves {broken} broken driver or animation path{'s' * (broken != 1)} unchanged")
        if ref_count.get(r):
            r.also.append(f"{ref_count[r]} combi_export reference{'s' * (ref_count[r] != 1)}")

def plan():
    """Everything the script would do, without changing anything."""
    renames = []
    plan_groups(renames)
    plan_inputs(renames)
    plan_nodes(renames)
    for r in renames:
        if r.old in KEEP:
            r.block("listed in KEEP")
    # Blocking one rename can block others (its nodes, a shared reference), so repeat until nothing changes
    while True:
        before = sum(r.active for r in renames)
        refs = find_combi_refs(renames)
        notes = find_unsafe(renames)
        if sum(r.active for r in renames) == before:
            break
    refs = [ref for ref in refs if ref.value() != ref.old]
    describe(renames, refs, notes)
    planned = {r.data.as_pointer() for r in renames if r.kind == "node"}
    return {
        "renames": renames,
        "refs": refs,
        "notes": notes,
        "report_only": find_report_only(planned),
        "texts": find_texts(renames),
    }


# --- Applying ----------------------------------------------------------------------------------------------------

def apply(result):
    """Rename what the plan allows, then rewrite the combi_export references."""
    for r in result["renames"]:
        if not r.active:
            continue
        r.data.name = r.new
        if r.data.name != r.new:
            got = r.data.name
            r.data.name = r.old
            r.failed = f"Blender named it {q(got)}; put back"
        else:
            r.done = True
    for ref in result["refs"]:
        value = ref.value()
        if value != ref.old:
            with raw_edits_of(ref.entry)():
                setattr(ref.entry, ref.key, value)
            ref.done = getattr(ref.entry, ref.key) == value
    # Blender rewrites node paths in drivers and actions itself; check that it did
    warnings = []
    done_nodes = [r for r in result["renames"] if r.kind == "node" and r.done]
    if done_nodes:
        for data, text, kind, target in anim_texts():
            for r in done_nodes:
                if target == r.owner and f'nodes["{r.old}"]' in text:
                    warnings.append(f"{kind} on {q(data.name)} still names node {q(r.old)}: {text}")
    result["warnings"] = warnings


# --- Report ------------------------------------------------------------------------------------------------------

def report(result, applied, second=None):
    renames, refs = result["renames"], result["refs"]
    out = []
    add = out.append
    add("=" * 100)
    add("fix_names: " + ("APPLIED" if applied else "DRY RUN, nothing changed (set DRY_RUN = False to apply)"))
    add(f"file: {bpy.data.filepath or '(not saved)'}, Blender {bpy.app.version_string}")
    add("=" * 100)
    active = [r for r in renames if (r.done if applied else r.active)]
    skipped = [r for r in renames if r not in active]
    width = min(max([len(q(r.old)) for r in renames] + [10]), 45)
    add("")
    add(f"RENAMES ({len(active)})")
    add(f"{'kind':<6} {'old name':<{width}}    {'new name':<{width}}  where it is used")
    order = {"group": 0, "input": 1, "node": 2}
    for r in sorted(active, key=lambda r: (order[r.kind], r.owner.name if r.owner else "", r.old)):
        add(f"{r.kind:<6} {q(r.old):<{width}} -> {q(r.new):<{width}}  {r.where}")
        if r.also:
            add(f"{'':<6} {'':<{width}}    also: {'; '.join(r.also)}")
    if skipped:
        add("")
        add(f"SKIPPED ({len(skipped)})")
        for r in sorted(skipped, key=lambda r: (order[r.kind], r.old)):
            owner = f" ({q(r.owner.name)})" if r.owner else ""
            add(f"{r.kind:<6} {q(r.old)} -> {q(r.new)}{owner}: {r.reason}")
    shown = [ref for ref in refs if ref.done or not applied]
    add("")
    add(f"COMBI_EXPORT REFERENCES {'UPDATED' if applied else 'TO UPDATE'} ({len(shown)})")
    for ref in shown:
        add(f"scene {q(ref.scene.name)}, {ref.place}: {ref.key} {q(ref.old)} -> {q(ref.value())}")
    if result.get("warnings"):
        add("")
        add(f"WARNINGS ({len(result['warnings'])})")
        out.extend(result["warnings"])
    only = result["report_only"]
    if only:
        add("")
        add(f"REPORT ONLY, NOT CHANGED ({len(only)})")
        for (kind, name), (fixed, places) in sorted(only.items()):
            where = ", ".join(places[:3]) + (f", ... ({len(places)} places)" if len(places) > 3 else "")
            add(f"{kind:<10} {q(name)} (would be {q(fixed)}): {where}")
    if result["texts"]:
        add("")
        add(f"TEXT BLOCKS THAT MENTION AN OLD NAME, NOT EDITED ({len(result['texts'])})")
        for text, hits in result["texts"]:
            add(f"{q(text.name)}: " + ", ".join(f"{q(old)} (line {line})" for old, line in hits))
    add("")
    counts = {kind: sum(1 for r in active if r.kind == kind) for kind in order}
    add(f"Summary: {counts['group']} node groups, {counts['input']} inputs, {counts['node']} group nodes "
        f"{'renamed' if applied else 'to rename'}; {len(skipped)} skipped; {len(shown)} combi_export references; "
        f"{len(only)} names only reported.")
    if applied:
        add("tracking.json changes on the next save: renamed keys and the link lines that show renamed names.")
    if second is not None:
        left = [r for r in second["renames"] if r.active]
        add(f"Second pass: {len(left)} names left to rename, {len(second['refs'])} references left to update.")
    return "\n".join(out)

def write_report_text(text):
    block = bpy.data.texts.get(REPORT_TEXT) or bpy.data.texts.new(REPORT_TEXT)
    block.from_string(text)

def main(dry_run=None):
    """Plan, report, and apply unless dry_run. Returns the plan, with 'second' (the plan after applying)."""
    dry_run = DRY_RUN if dry_run is None else dry_run
    result = plan()
    second = None
    if not dry_run:
        apply(result)
        describe(result["renames"], result["refs"], result["notes"])    # with the new names
        second = plan()
        result["report_only"] = second["report_only"]
    result["second"] = second
    result["report"] = report(result, not dry_run, second)
    print(result["report"])
    if REPORT_TEXT:
        write_report_text(result["report"])
    return result

if __name__ == "__main__":
    main()
