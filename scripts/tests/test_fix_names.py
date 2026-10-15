"""Tests for scripts/fix_names.py on a small fixture file built in memory.

Run with a Python that has the bpy module (Blender as a module), from anywhere:
    python scripts/tests/test_fix_names.py
combi_export and blender_tracking are registered from extensions/, as when they are enabled in Blender.
"""
import contextlib
import importlib.util
import io
import json
import os
import sys
import tempfile
import unittest

import bpy

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TEMP = tempfile.TemporaryDirectory()
tempfile.tempdir = TEMP.name    # combi_export cleans its old temp folders on register: keep it in ours

sys.path.insert(0, os.path.join(REPO, "extensions"))
import blender_tracking as bt   # noqa: E402
import combi_export             # noqa: E402
from combi_export.common import raw_edits           # noqa: E402
from combi_export.data import copy_setup_to_dict, stamp_data_version     # noqa: E402
from combi_export.validation import is_preset_setup_valid    # noqa: E402

spec = importlib.util.spec_from_file_location("fix_names", os.path.join(REPO, "scripts", "fix_names.py"))
fix_names = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fix_names)


# --- Fixture -----------------------------------------------------------------------------------------------------

def new_group(name, inputs=(), outputs=("Geometry",), panel=None):
    """A Geometry Nodes group with float inputs [(name, default)] and a Group Input -> Group Output link."""
    group = bpy.data.node_groups.new(name, "GeometryNodeTree")
    group.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    parent = group.interface.new_panel(panel) if panel else None
    for socket_name, default in inputs:
        item = group.interface.new_socket(socket_name, in_out="INPUT", socket_type="NodeSocketFloat")
        item.default_value = default
        if parent:
            group.interface.move_to_parent(item, parent, len(parent.interface_items))
    for socket_name in outputs:
        group.interface.new_socket(socket_name, in_out="OUTPUT", socket_type="NodeSocketGeometry")
    gin, gout = group.nodes.new("NodeGroupInput"), group.nodes.new("NodeGroupOutput")
    group.links.new(gin.outputs[0], gout.inputs[0])
    return group

def add_group_node(tree, group, name=None):
    node = tree.nodes.new("GeometryNodeGroup")
    node.node_tree = group
    node.name = name or group.name
    return node

def add_override(ng_list, group, node, inputs):
    """A combi_export override block: group > node > [(input, value)]."""
    with raw_edits():
        ng = ng_list.add()
        ng.group_name = group
        n = ng.nodes.add()
        n.name = node
        for name, value in inputs:
            inp = n.inputs.add()
            inp.name = name
            inp.override_type = 'FLOAT'
            inp.values.add().value_string = value

def build_fixture():
    bpy.ops.wm.read_homefile(use_empty=True, use_factory_startup=True)
    scene = bpy.context.scene
    scene.name = "GripV"

    lever = new_group("R1 lever paramteters", [("wdith", 1.0), ("bevel inner sbdiv", 2.0),
                                               ("case cutout thickness ", 0.4), ("stick  XY correction", 0.1)],
                      panel="paramters")
    bundle = lever.nodes.new("NodeCombineBundle")
    bundle.bundle_items.new("FLOAT", "wdith")
    new_group("basic stick parameters", [("sheild radius", 1.0), ("shield radius", 2.0), ("stick heght", 3.0)])
    r1l1 = new_group("GripV  lever R1L1", [("stiick height", 3.0)])
    r1 = new_group("GripR1  parameters", [("wdith", 5.0)])
    new_group("GripR1 parameters")
    neighbour = new_group("neighboor direction")
    pins = new_group("pins postion", [("x", 1.0)])
    hollow = new_group("holllow lattice parameters")
    position = new_group("R1 lever postion")
    cover = new_group("coVer base")
    glob = new_group("global", [("tolerance", 0.1)])
    menu = glob.nodes.new("GeometryNodeMenuSwitch")
    menu.enum_items[0].name = "low "

    panel = new_group("GripX contols", [("sheild", 0.5)])
    add_group_node(panel, r1l1)
    lever_node = add_group_node(panel, lever)
    lever_node.inputs["bevel inner sbdiv"].default_value = 5.0
    value = panel.nodes.new("ShaderNodeValue")
    value.outputs[0].default_value = 7.0
    panel.links.new(value.outputs[0], lever_node.inputs["wdith"])
    add_group_node(panel, neighbour)
    add_group_node(panel, neighbour)            # becomes 'neighboor direction.001'
    add_group_node(panel, r1)
    add_group_node(panel, hollow)
    add_group_node(panel, position)
    add_group_node(panel, cover)
    add_group_node(panel, glob)
    panel.nodes.new("NodeFrame").label = "Xbox syle"
    panel.driver_add('nodes["GripV  lever R1L1"].inputs[1].default_value')

    pins_tree = new_group("pins tree")
    pins_tree.nodes.new("ShaderNodeValue").name = "pins position"
    add_group_node(pins_tree, pins)             # stays 'pins postion': the new name is taken in this tree

    case = bpy.data.objects.new("case", bpy.data.meshes.new("case"))
    scene.collection.objects.link(case)
    mod = case.modifiers.new("GeometryNodes", "NODES")
    mod.node_group = lever
    getattr(mod.properties.inputs, lever.interface.items_tree["wdith"].identifier).value = 9.0
    holder = bpy.data.objects.new("panel holder", bpy.data.meshes.new("panel holder"))
    scene.collection.objects.link(holder)
    holder.modifiers.new("GeometryNodes", "NODES").node_group = panel
    shape = bpy.data.objects.new("custom shape  gripV", None)
    scene.collection.objects.link(shape)
    scene.collection.children.link(bpy.data.collections.new("middle suppprts"))
    drv = shape.driver_add("location", 0).driver
    drv.expression = 'len("R1 lever postion")'

    scene["note"] = "holllow lattice parameters"
    bpy.data.texts.new("Auto sync workspaces").from_string(
        "variant = 'GripV'\nnode = bpy.data.node_groups['global']\n# global parameters\npanel = 'GripX contols'\n")

    # combi_export: a preset with overrides at preset and object level, global overrides, a second scene
    preset = scene.batch_stl_presets.add()
    preset.name = "Parts"
    add_override(preset.nodegroups, "GripX contols", "GripV  lever R1L1 [GripV  lever R1L1]", [("stiick height", "4")])
    with raw_edits():   # a second node in the same block
        n = preset.nodegroups[0].nodes.add()
        n.name = "R1 lever paramteters [R1 lever paramteters]"
        inp = n.inputs.add()
        inp.name, inp.override_type = "wdith", 'FLOAT'
        inp.values.add().value_string = "3"
    col = preset.collections.add()
    col.collection_name = "parts"
    obj = col.objects.add()
    obj.name = "case"
    add_override(obj.nodegroups, "R1 lever paramteters", "<Modifier Interface>",
                 [("wdith", "2"), ("case cutout thickness ", "0.5")])
    add_override(scene.batch_stl_global_nodegroups, "GripR1  parameters", "<Modifier Interface>", [("wdith", "6")])
    gripx = bpy.data.scenes.new("GripX")
    add_override(gripx.batch_stl_global_nodegroups, "pins postion", "<Modifier Interface>", [("x", "2")])
    p2 = gripx.batch_stl_presets.add()
    p2.name = "Case"

    for s in bpy.data.scenes:
        stamp_data_version(s)   # as saved: re-registering the add-on does not migrate the scenes
    # blender_tracking: the panel, one level deep, group nodes only (as in Grip.blend)
    tracked = scene.geonodes_json_exporter_groups.add()
    tracked.group_ptr, tracked.depth, tracked.groups_only = panel, 1, True


# --- Snapshots ---------------------------------------------------------------------------------------------------

def snapshot():
    """Everything the script may touch, keyed by names (so any rename shows)."""
    def socket_value(s):
        v = getattr(s, "default_value", None)
        return tuple(v) if hasattr(v, "__len__") and not isinstance(v, str) else v
    groups = {}
    for g in bpy.data.node_groups:
        groups[g.name] = {
            "interface": [(i.item_type, i.name, getattr(i, "identifier", None), socket_value(i))
                          for i in g.interface.items_tree],
            "nodes": {n.name: (n.bl_idname, n.label, n.node_tree.name if getattr(n, "node_tree", None) else None,
                               [(s.identifier, s.name, socket_value(s)) for s in n.inputs]) for n in g.nodes},
            "links": sorted((l.from_node.name, l.from_socket.identifier, l.to_node.name, l.to_socket.identifier)
                            for l in g.links),
            "drivers": [fc.data_path for fc in g.animation_data.drivers] if g.animation_data else [],
        }
    objects = {o.name: [(m.name, m.node_group.name if m.node_group else None,
                         {k: socket_value(getattr(m.properties.inputs, k))
                          for k in m.properties.inputs.bl_rna.properties.keys() if k.startswith("Socket")})
                        for m in o.modifiers if m.type == 'NODES'] for o in bpy.data.objects}
    return {
        "groups": groups,
        "objects": objects,
        "collections": sorted(c.name for c in bpy.data.collections),
        "texts": {t.name: t.as_string() for t in bpy.data.texts},
        "combi": {s.name: json.dumps(copy_setup_to_dict(s), sort_keys=True) for s in bpy.data.scenes},
        "tracked": {s.name: [i.group_ptr.name for i in s.geonodes_json_exporter_groups] for s in bpy.data.scenes},
        "props": {s.name: dict(s.items()) for s in bpy.data.scenes},
    }

def identity_links():
    """Links by node and socket pointers, which a rename does not change."""
    return {g.as_pointer(): sorted((l.from_node.as_pointer(), l.from_socket.as_pointer(), l.to_node.as_pointer(),
                                    l.to_socket.as_pointer()) for l in g.links) for g in bpy.data.node_groups}

def tracking_identities():
    """{identity: (key path)} for the tracked inputs and modifier inputs blender_tracking writes, where identity is
    made of pointers and socket identifiers, which a rename does not change."""
    keys = {}

    def walk(tree, depth, max_depth, ids, path):
        for node in tree.nodes:
            if node.type != 'GROUP':
                continue
            node_ids, node_path = ids + (node.as_pointer(),), path + (bt.node_key(node),)
            for label, socket in bt.iter_input_sockets(node):
                keys[("input",) + node_ids + (socket.identifier,)] = ("input",) + node_path + (label,)
            if node.node_tree and depth < max_depth:
                walk(node.node_tree, depth + 1, max_depth, node_ids, node_path)

    tracked = bt.collect_tracked_groups()
    for tree, config in tracked.items():
        walk(tree, 0, config["depth"], (tree.as_pointer(),), (bt.id_key(tree),))
    for obj, mod in bt.iter_tracked_modifiers(tracked):
        for label, item, _mod_input in bt.iter_modifier_inputs(mod):
            keys[("modifier", obj.as_pointer(), mod.name, item.identifier)] = ("modifier", obj.name, mod.name, label)
    return keys

def flat_tracking(data):
    """{key path: value} of a tracking file's tracked inputs and modifier inputs, like tracking_identities."""
    flat = {}
    for tree, nodes in data["tracked_inputs"].items():
        for (node_path, label), value in bt.flatten_entries(nodes).items():
            if not label.endswith(" (property)"):
                flat[("input", tree) + node_path + (label,)] = value
    for obj, mods in data["modifiers"].items():
        for mod, entry in mods.items():
            for label, value in entry["inputs"].items():
                flat[("modifier", obj, mod, label)] = value
    return flat

def export_tracking(name):
    path = os.path.join(TEMP.name, name)
    bt.export_nodes_to_json(path)
    with open(path, encoding="utf-8") as f:
        return json.load(f)


# --- Tests -------------------------------------------------------------------------------------------------------

class FixNamesTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        combi_export.register()
        bt.register()

    @classmethod
    def tearDownClass(cls):
        bt.unregister()
        combi_export.unregister()

    def setUp(self):
        build_fixture()

    def run_script(self, dry_run):
        with contextlib.redirect_stdout(io.StringIO()):
            return fix_names.main(dry_run=dry_run)

    def test_words_and_spaces(self):
        self.assertEqual(fix_names.fixed_name("GripR1 pcb cutout paramters.001"), "GripR1 pcb cutout parameters.001")
        self.assertEqual(fix_names.fixed_name("euclidean distance .002"), "euclidean distance.002")
        self.assertEqual(fix_names.fixed_name("coVer base"), "cover base")
        self.assertEqual(fix_names.fixed_name("Sheild"), "Shield")
        self.assertEqual(fix_names.fixed_name("case cutout thickness ", numbered=False), "case cutout thickness")
        # whole words only, and correct names stay
        for name in ("coerce", "subdivision level", "shield radius", "cover parameters", "position", "R1L1"):
            self.assertEqual(fix_names.fixed_name(name), name)
        self.assertEqual(fix_names.following_name("neighboor direction.002", "neighboor direction.001",
                                                  "neighbour direction.001"), "neighbour direction.002")
        self.assertEqual(fix_names.following_name("stick top parameters.normal", "stick top parameters",
                                                  "stick top params"), "stick top params.normal")
        self.assertIsNone(fix_names.following_name("my lever", "GripV  lever R1L1", "GripV lever R1L1"))

    def test_dry_run_changes_nothing(self):
        before = snapshot()
        result = self.run_script(dry_run=True)
        self.assertEqual(snapshot(), before)
        self.assertIn("DRY RUN", result["report"])
        self.assertGreater(sum(r.active for r in result["renames"]), 10)
        self.assertGreater(len(result["refs"]), 5)

    def test_apply(self):
        before = snapshot()
        links_before = identity_links()
        lever = bpy.data.node_groups["R1 lever paramteters"]
        idents = {i.identifier: i.default_value for i in fix_names.interface_sockets(lever, 'INPUT')
                  if i.socket_type == "NodeSocketFloat"}
        panel = bpy.data.node_groups["GripX contols"]
        valid_before = [is_preset_setup_valid(s, p) for s in bpy.data.scenes for p in s.batch_stl_presets]

        result = self.run_script(dry_run=False)
        groups = bpy.data.node_groups

        # node groups: renamed, or skipped with a reason
        for name in ("R1 lever parameters", "GripV lever R1L1", "neighbour direction", "pins position",
                     "GripX controls", "cover base", "basic stick parameters", "global"):
            self.assertIn(name, groups)
        for name in ("R1 lever paramteters", "GripV  lever R1L1", "neighboor direction", "pins postion",
                     "GripX contols", "coVer base"):
            self.assertNotIn(name, groups)
        skipped = {(r.kind, r.old): r.reason for r in result["renames"] if not r.done}
        self.assertIn("already exists", skipped["group", "GripR1  parameters"])         # collision
        self.assertIn("is not renamed", skipped["node", "GripR1  parameters"])          # its nodes follow
        self.assertIn('scenes["GripV"]["note"]', skipped["group", "holllow lattice parameters"])
        self.assertIn("driver expression", skipped["group", "R1 lever postion"])
        self.assertIn("already exists", skipped["input", "sheild radius"])              # input collision
        self.assertIn("already exists", skipped["node", "pins postion"])                # node collision
        self.assertEqual(len(skipped), 8)
        self.assertIn("GripR1  parameters", groups)
        self.assertIn("holllow lattice parameters", groups)

        # inputs: new names, same identifiers and defaults, modifier value and links kept
        self.assertEqual([i.name for i in fix_names.interface_sockets(lever, 'INPUT')],
                         ["Geometry", "width", "bevel inner subdiv", "case cutout thickness", "stick XY correction"])
        self.assertEqual({i.identifier: i.default_value for i in fix_names.interface_sockets(lever, 'INPUT')
                          if i.socket_type == "NodeSocketFloat"}, idents)
        stick = groups["basic stick parameters"]
        self.assertEqual([i.name for i in fix_names.interface_sockets(stick, 'INPUT')],
                         ["Geometry", "sheild radius", "shield radius", "stick height"])
        mod = bpy.data.objects["case"].modifiers["GeometryNodes"]
        self.assertEqual(mod.node_group, lever)
        self.assertEqual(getattr(mod.properties.inputs, lever.interface.items_tree["width"].identifier).value, 9.0)
        self.assertEqual(identity_links(), links_before)
        lever_node = panel.nodes["R1 lever parameters"]
        self.assertEqual(lever_node.inputs["bevel inner subdiv"].default_value, 5.0)
        self.assertEqual(lever_node.inputs["width"].links[0].from_node.outputs[0].default_value, 7.0)

        # group nodes follow their group
        self.assertEqual(sorted(n.name for n in panel.nodes if n.type == 'GROUP'),
                         ["GripR1  parameters", "GripV lever R1L1", "R1 lever parameters", "R1 lever postion",
                          "cover base", "global", "holllow lattice parameters", "neighbour direction",
                          "neighbour direction.001"])
        self.assertEqual(groups["pins tree"].nodes["pins postion"].node_tree, groups["pins position"])
        self.assertEqual(panel.animation_data.drivers[0].data_path,
                         'nodes["GripV lever R1L1"].inputs[1].default_value')

        # combi_export references, in both scenes
        scene, gripx = bpy.data.scenes["GripV"], bpy.data.scenes["GripX"]
        ng = scene.batch_stl_presets["Parts"].nodegroups[0]
        self.assertEqual((ng.group_name, ng.prev_group_name), ("GripX controls", "GripX controls"))
        self.assertEqual([(n.name, n.prev_name, [(i.name, i.prev_name, i.values[0].value_string) for i in n.inputs])
                          for n in ng.nodes],
                         [("GripV lever R1L1 [GripV lever R1L1]", "GripV lever R1L1 [GripV lever R1L1]",
                           [("stick height", "stick height", "4")]),
                          ("R1 lever parameters [R1 lever parameters]", "R1 lever parameters [R1 lever parameters]",
                           [("width", "width", "3")])])
        obj_ng = scene.batch_stl_presets["Parts"].collections[0].objects[0].nodegroups[0]
        self.assertEqual(obj_ng.group_name, "R1 lever parameters")
        self.assertEqual([(i.name, i.values[0].value_string) for i in obj_ng.nodes[0].inputs],
                         [("width", "2"), ("case cutout thickness", "0.5")])
        glob_ng = scene.batch_stl_global_nodegroups[0]
        self.assertEqual((glob_ng.group_name, glob_ng.nodes[0].inputs[0].name), ("GripR1  parameters", "width"))
        self.assertEqual(gripx.batch_stl_global_nodegroups[0].group_name, "pins position")
        self.assertEqual(len([ref for ref in result["refs"] if ref.done]), 10)
        self.assertEqual([is_preset_setup_valid(s, p) for s in bpy.data.scenes for p in s.batch_stl_presets],
                         valid_before)
        self.assertTrue(all(valid_before))

        # blender_tracking follows by pointer; text blocks, report-only names and the custom property stay
        self.assertEqual(scene.geonodes_json_exporter_groups[0].group_ptr, panel)
        after = snapshot()
        self.assertEqual(after["texts"], before["texts"])
        self.assertEqual(after["props"], before["props"])
        self.assertEqual(after["collections"], before["collections"])
        self.assertIn("custom shape  gripV", bpy.data.objects)
        self.assertEqual([t.name for t, _hits in result["texts"]], ["Auto sync workspaces"])
        only = result["report_only"]
        for key in (("menu item", "low "), ("object", "custom shape  gripV"), ("collection", "middle suppprts"),
                    ("label", "Xbox syle"), ("socket", "wdith"), ("panel", "paramters")):
            self.assertIn(key, only)
        self.assertEqual(groups["global"].nodes["Menu Switch"].enum_items[0].name, "low ")

        # nothing left for a second pass
        self.assertEqual([r for r in result["second"]["renames"] if r.active], [])
        self.assertEqual(result["second"]["refs"], [])
        self.assertIn("Second pass: 0 names left to rename, 0 references left to update.", result["report"])
        self.assertEqual(result["warnings"], [])

    def test_second_run_is_a_no_op(self):
        self.run_script(dry_run=False)
        before = snapshot()
        result = self.run_script(dry_run=False)
        self.assertEqual(snapshot(), before)
        self.assertFalse(any(r.done for r in result["renames"]))
        self.assertEqual(result["refs"], [])

    def test_tracking_only_renames_keys(self):
        old_keys = tracking_identities()
        old = export_tracking("before.json")
        self.run_script(dry_run=False)
        new_keys = tracking_identities()
        new = export_tracking("after.json")
        self.assertEqual(set(old_keys), set(new_keys))
        old_flat, new_flat = flat_tracking(old), flat_tracking(new)
        self.assertEqual(len(old_flat), len(old_keys))
        self.assertEqual(len(new_flat), len(new_keys))
        for identity, old_key in old_keys.items():
            self.assertEqual(new_flat[new_keys[identity]], old_flat[old_key])
        renamed = sum(old_keys[i] != new_keys[i] for i in old_keys)
        self.assertGreater(renamed, 3)
        self.assertIn("GripX controls", new["tracked_inputs"])
        self.assertEqual(len(new["all_node_trees"]), len(old["all_node_trees"]))
        self.assertEqual(sorted(len(v) for v in new["all_node_trees"].values()),
                         sorted(len(v) for v in old["all_node_trees"].values()))
        self.assertEqual(new["meshes"], old["meshes"])

    def test_other_stored_names(self):
        bpy.types.Scene.other_addon_name = bpy.props.StringProperty()
        try:
            bpy.data.scenes["GripV"].other_addon_name = "neighboor direction"
            holder = bpy.data.objects["panel holder"]
            hand_written = holder.driver_add("location", 1).driver.variables.new()
            hand_written.targets[0].id_type = 'NODETREE'
            hand_written.targets[0].id = bpy.data.node_groups["basic stick parameters"]
            hand_written.targets[0].data_path = 'nodes["Group Input"].outputs["stick heght"].default_value'
            node_path = holder.driver_add("location", 2).driver.variables.new()
            node_path.targets[0].id_type = 'NODETREE'
            node_path.targets[0].id = bpy.data.node_groups["GripX contols"]
            node_path.targets[0].data_path = 'nodes["coVer base"].name'
            broken = holder.driver_add("location", 0).driver.variables.new()     # Blender only fixes paths that work
            broken.targets[0].id_type = 'NODETREE'
            broken.targets[0].id = bpy.data.node_groups["GripX contols"]
            broken.targets[0].data_path = 'nodes["R1 lever paramteters"].no_such_property'
            # a node of the same name in another tree, with a driver of its own
            pins_tree = bpy.data.node_groups["pins tree"]
            add_group_node(pins_tree, bpy.data.node_groups["R1 lever paramteters"])
            pins_tree.driver_add('nodes["R1 lever paramteters"].inputs[1].default_value')
            result = self.run_script(dry_run=False)
        finally:
            del bpy.types.Scene.other_addon_name
        reasons = {(r.kind, r.old): r.reason for r in result["renames"] if not r.done}
        self.assertIn('bpy.data.scenes["GripV"].other_addon_name', reasons["group", "neighboor direction"])
        self.assertIn("driver variable", reasons["input", "stick heght"])
        self.assertIn("neighboor direction", bpy.data.node_groups)
        self.assertEqual(bpy.data.node_groups["basic stick parameters"].interface.items_tree[-1].name, "stick heght")
        # node paths: Blender rewrote them, each on its own tree
        self.assertEqual(node_path.targets[0].data_path, 'nodes["cover base"].name')
        self.assertEqual(pins_tree.animation_data.drivers[0].data_path,
                         'nodes["R1 lever parameters"].inputs[1].default_value')
        self.assertIn("R1 lever parameters", bpy.data.node_groups["GripX controls"].nodes)
        lever_node = next(r for r in result["renames"] if r.kind == "node" and r.old == "R1 lever paramteters"
                          and r.owner.name == "GripX controls")
        self.assertIn("Blender leaves 1 broken driver or animation path unchanged", lever_node.also)
        self.assertEqual(len(result["warnings"]), 1)
        self.assertIn('still names node \'R1 lever paramteters\'', result["warnings"][0])

    def test_keep_and_report_text(self):
        fix_names.KEEP, fix_names.REPORT_TEXT = ("GripX contols",), "fix_names report"
        try:
            before = snapshot()
            result = self.run_script(dry_run=True)
            after = snapshot()
            report = after["texts"].pop("fix_names report")
            self.assertEqual(after, before)     # the report text is the only change of a dry run
            self.assertEqual(report, result["report"])
            result = self.run_script(dry_run=False)
        finally:
            fix_names.KEEP, fix_names.REPORT_TEXT = (), ""
        self.assertIn("GripX contols", bpy.data.node_groups)
        self.assertEqual(bpy.data.scenes["GripV"].batch_stl_presets[0].nodegroups[0].group_name, "GripX contols")
        self.assertEqual(bpy.data.node_groups["GripX contols"].interface.items_tree["shield"].item_type, 'SOCKET')
        self.assertIn("listed in KEEP", {r.old: r.reason for r in result["renames"]}["GripX contols"])
        # 'Auto sync workspaces' only names the kept group, and the report is not listed although it names others
        self.assertEqual(result["texts"], [])

    def test_disabled_combi_export_blocks_its_names(self):
        combi_export.unregister()
        try:
            result = fix_names.plan()
        finally:
            combi_export.register()
        blocked = [(r.kind, r.old) for r in result["renames"] if "enable combi_export" in r.reason]
        for key in (("group", "GripX contols"), ("group", "R1 lever paramteters"), ("group", "pins postion"),
                    ("input", "stiick height"), ("input", "case cutout thickness "), ("node", "GripV  lever R1L1")):
            self.assertIn(key, blocked)
        self.assertEqual(blocked.count(("input", "wdith")), 2)     # in two groups, both used by overrides
        active = {(r.kind, r.old) for r in result["renames"] if r.active}
        self.assertIn(("group", "neighboor direction"), active)    # not used by a preset
        self.assertIn(("input", "bevel inner sbdiv"), active)
        self.assertIn(("group", "coVer base"), active)
        self.assertEqual(result["refs"], [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
