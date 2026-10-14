"""Tests for the Grip Controls extension. Run with a Python that has the bpy module (Blender 5.2 or newer):

    python -I extensions/grip_controls/tests/test_grip_controls.py

Grip.blend is not opened. The tests build node groups named like the ones in Grip.blend, enable the add-on from
the extensions folder the way a user does (a local repository), and check what the panels find and draw. A last set
checks every path the add-on reads against blender/tracking.json, so the names are known to exist in the real file.
"""
import atexit
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from types import SimpleNamespace

HERE = os.path.dirname(os.path.abspath(__file__))
EXT_DIR = os.path.dirname(HERE)
EXTENSIONS = os.path.dirname(EXT_DIR)
REPO = os.path.dirname(EXTENSIONS)
TRACKING = os.path.join(REPO, "blender", "tracking.json")

# Keep Blender's user folders out of the real ones, and no __pycache__ in the repository
_USER = tempfile.mkdtemp(prefix="grip_controls_test_")
atexit.register(shutil.rmtree, _USER, ignore_errors=True)
os.environ["BLENDER_USER_RESOURCES"] = _USER
sys.dont_write_bytecode = True

import bpy  # noqa: E402
import addon_utils  # noqa: E402  (comes with bpy)

REPO_MODULE = "grip_test"
ADDON = f"bl_ext.{REPO_MODULE}.grip_controls"
PANELS = {"GripV": "GripV controls", "GripX": "GripX contols"}


# ---------------------------------------------------------------- add-on

def enable_addon():
    """Adds the extensions folder as a local repository and enables the add-on from it."""
    bpy.context.preferences.use_preferences_save = False
    repos = bpy.context.preferences.extensions.repos
    if not any(r.module == REPO_MODULE for r in repos):
        repos.new(name=REPO_MODULE, module=REPO_MODULE, custom_directory=EXTENSIONS, source='USER')
    module = addon_utils.enable(ADDON, default_set=True, handle_error=None)
    if module is None:
        raise RuntimeError(f"could not enable {ADDON}")
    return module


def disable_addon():
    addon_utils.disable(ADDON, default_set=True)


def submodule(name):
    return sys.modules[f"{ADDON}.{name}"]


# ---------------------------------------------------------------- fixture: node groups named like Grip.blend

MENUS = {
    "variant": ("GripR1", "GripV", "GripX"),
    "style": ("xbox", "dualsense"),
    "body type": ("standard", "indent", "hollow", "lattice"),
    "subdivision level": ("low ", "medium", "high", "very high"),
    "voxel resolution": ("low", "medium", "high"),
    "tolerance": ("tight", "default", "loose"),
    "press tolerance": ("tight", "default", "loose"),
    "cap tolerance": ("tight", "default", "loose"),
    "fill type": ("Gyroid", "Diamond", "cubic"),
    "top shape": ("circle", "square"),
    "top curvature": ("concave", "convex", "flat"),
    "texture type": ("grid", "icosahedron"),
}
GLOBAL_BOOLS = ("hollow top", "ribs", "pillars", "screws", "screws hollow", "cable holder", "stock bumpers",
                "top wire cutouts", "R4 wire cutouts", "horizontal buttons", "button logo", "marks")
GLOBAL_START = {"variant": "GripV", "style": "xbox", "body type": "standard", "subdivision level": "low ",
                "voxel resolution": "low", "tolerance": "default", "press tolerance": "default",
                "cap tolerance": "default", "fill type": "Gyroid", "horizontal buttons": True, "screws": True}


def constructor(name, floats=(), menus=(), bools=(), outputs=(("Bundle", "NodeSocketBundle"),)):
    """A constructor group: inputs only matter by name and type. Menus get their items from a Menu Switch."""
    tree = bpy.data.node_groups.new(name, "GeometryNodeTree")
    for socket in floats:
        tree.interface.new_socket(socket, in_out='INPUT', socket_type='NodeSocketFloat')
    for socket in menus:
        tree.interface.new_socket(socket, in_out='INPUT', socket_type='NodeSocketMenu')
    for socket in bools:
        tree.interface.new_socket(socket, in_out='INPUT', socket_type='NodeSocketBool')
    for socket, socket_type in outputs:
        tree.interface.new_socket(socket, in_out='OUTPUT', socket_type=socket_type)
    group_in = tree.nodes.new("NodeGroupInput")
    tree.nodes.new("NodeGroupOutput")
    for socket in menus:
        switch = tree.nodes.new("GeometryNodeMenuSwitch")
        switch.data_type = 'INT'
        items = switch.enum_definition.enum_items
        items.clear()
        for item in MENUS[socket]:
            items.new(item)
        tree.links.new(group_in.outputs[socket], switch.inputs["Menu"])
    return tree


def add_group(tree, group, name=None, frame=None, values=None):
    node = tree.nodes.new("GeometryNodeGroup")
    node.node_tree = bpy.data.node_groups[group]
    node.name = name or group
    if frame is not None:
        node.parent = frame
    for socket, value in (values or {}).items():
        node.inputs[socket].default_value = value
    return node


def add_frame(tree, label):
    frame = tree.nodes.new("NodeFrame")
    frame.label = label
    return frame


def preset_group(name):
    """A preset group with a Join Bundle wired to its output. Returns (tree, join)."""
    tree = bpy.data.node_groups.new(name, "GeometryNodeTree")
    tree.interface.new_socket("Bundle", in_out='OUTPUT', socket_type='NodeSocketBundle')
    out = tree.nodes.new("NodeGroupOutput")
    join = tree.nodes.new("NodeJoinBundle")
    tree.links.new(join.outputs[0], out.inputs[0])
    return tree, join


def link_bundle(tree, node, target):
    tree.links.new(node.outputs["Bundle"], target)


def gripd_switch(tree, join, false_node, true_node):
    """The GripX style switch: gripD from 'global outputs' picks False (xbox) or True (dualsense)."""
    switch = tree.nodes.new("GeometryNodeSwitch")
    switch.input_type = 'BUNDLE'
    outputs = add_group(tree, "global outputs")
    tree.links.new(outputs.outputs["gripD"], switch.inputs["Switch"])
    link_bundle(tree, false_node, switch.inputs["False"])
    link_bundle(tree, true_node, switch.inputs["True"])
    tree.links.new(switch.outputs[0], join.inputs[0])
    return switch


TRIGGER = ("trigger length", "width", "shift z", "x offset", "button radius offset", "x tolerance")
LEVER = ("wdith", "height", "X", "Y", "Z", "stem radius")


def build_fixture():
    """Groups and nodes named like Grip.blend, with values that tell the candidate nodes apart."""
    constructor("global parameters", menus=tuple(n for n in MENUS if n in GLOBAL_START), bools=GLOBAL_BOOLS)
    constructor("global outputs", outputs=(("gripD", "NodeSocketBool"), ("button tol", "NodeSocketFloat")))
    constructor("trigger parameters", floats=TRIGGER)
    constructor("tolerance set", floats=("tight", "default", "loose"), outputs=(("Value", "NodeSocketFloat"),))
    constructor("R1L1 lever parameters", floats=LEVER)
    constructor("basic stick parameters", floats=("stick heght", "range degrees", "stick top radius"))
    constructor("stick top parameters", menus=("top shape", "top curvature", "texture type"))
    constructor("curve parameters", floats=("width",))
    constructor("advanced cover parameters", floats=("battery length", "battery width", "battery height"))

    tree, _join = preset_group("global")
    node = add_group(tree, "global parameters")
    tree.links.new(node.outputs[0], tree.nodes["Group Output"].inputs[0])
    for name, value in GLOBAL_START.items():
        node.inputs[name].default_value = value

    # GripV triggers: the live node, and an unconnected alternative in frame SNES
    tree, join = preset_group("GripV R2 parameters")
    add_group(tree, "trigger parameters", frame=add_frame(tree, "SNES"), values={"trigger length": 17.0})
    live = add_group(tree, "trigger parameters", "trigger parameters.001", values={"trigger length": 28.0})
    link_bundle(tree, live, join.inputs[0])
    tol = add_group(tree, "tolerance set")
    tree.links.new(tol.outputs["Value"], live.inputs["x tolerance"])

    # GripV R4: one live node, 'shift z' fed by a Value node (a linked quick input)
    tree, join = preset_group("GripV R4 parameters")
    live = add_group(tree, "trigger parameters", values={"trigger length": 16.0})
    link_bundle(tree, live, join.inputs[0])
    value = tree.nodes.new("ShaderNodeValue")
    value.label = "paddle shift"
    tree.links.new(value.outputs[0], live.inputs["shift z"])

    # GripX triggers: one node per style in frames GripX and GripD; R2 behind the gripD switch, R4 frames only
    tree, join = preset_group("GripX R2 parameters")
    xbox = add_group(tree, "trigger parameters", frame=add_frame(tree, "GripX"), values={"trigger length": 30.5})
    dual = add_group(tree, "trigger parameters", "trigger parameters.001", frame=add_frame(tree, "GripD"),
                     values={"trigger length": 30.15})
    gripd_switch(tree, join, xbox, dual)
    tree, join = preset_group("GripX R4 parameters")
    xbox = add_group(tree, "trigger parameters", frame=add_frame(tree, "GripX"), values={"trigger length": 21.2})
    dual = add_group(tree, "trigger parameters", "trigger parameters.001", frame=add_frame(tree, "GripD"),
                     values={"trigger length": 24.1})
    link_bundle(tree, xbox, join.inputs[0])
    link_bundle(tree, dual, join.inputs[0])

    # Bumpers: GripV stem radius comes from a Value node; GripX has one node per style
    tree, join = preset_group("GripV  lever R1L1")
    lever = add_group(tree, "R1L1 lever parameters", values={"wdith": 20.0})
    link_bundle(tree, lever, join.inputs[0])
    value = tree.nodes.new("ShaderNodeValue")
    tree.links.new(value.outputs[0], lever.inputs["stem radius"])
    tree, join = preset_group("GripX lever R1L1")
    xbox = add_group(tree, "R1L1 lever parameters", frame=add_frame(tree, "GripX"), values={"wdith": 21.0})
    dual = add_group(tree, "R1L1 lever parameters", "R1L1 lever parameters.001", frame=add_frame(tree, "GripD"),
                     values={"wdith": 22.0})
    gripd_switch(tree, join, xbox, dual)

    # Sticks: GripV has one set per stick
    for side in ("L", "R"):
        tree, join = preset_group(f"GripV stick {side} parameters")
        for group in ("basic stick parameters", "stick top parameters"):
            link_bundle(tree, add_group(tree, group), join.inputs[0])

    # GripX sticks: complete sets behind a Menu Switch. L: driven by the Menu node 'stick menu', with a sixth
    # unconnected set. R: the Menu Switch's own menu value.
    for side, items, menu_node in (("L", ("Xbox cap", "Octagonal 18d range"), "stick menu"),
                                   ("R", ("normal", "small round"), None)):
        tree, _join = preset_group(f"GripX stick {side} parameters")
        out = tree.nodes["Group Output"]
        tree.links.remove(out.inputs[0].links[0])
        switch = tree.nodes.new("GeometryNodeMenuSwitch")
        switch.data_type = 'BUNDLE'
        switch.enum_definition.enum_items.clear()
        for item in items:
            switch.enum_definition.enum_items.new(item)
        tree.links.new(switch.outputs[0], out.inputs[0])
        for index, item in enumerate(items, start=1):
            join = tree.nodes.new("NodeJoinBundle")
            join.name = f"Join Bundle.{index:03d}"
            reroute = tree.nodes.new("NodeReroute")
            tree.links.new(join.outputs[0], reroute.inputs[0])
            tree.links.new(reroute.outputs[0], switch.inputs[item])
            for group in ("basic stick parameters", "stick top parameters"):
                node = add_group(tree, group, f"{group}.{index:03d}")
                link_bundle(tree, node, join.inputs[0])
            tree.nodes[f"basic stick parameters.{index:03d}"].inputs["stick heght"].default_value = 10.0 + index
        if menu_node:
            menu = tree.nodes.new("FunctionNodeInputMenu")
            menu.name = menu_node
            tree.links.new(menu.outputs[0], switch.inputs["Menu"])
            menu.value = items[0]
            spare = tree.nodes.new("NodeJoinBundle")
            for group in ("basic stick parameters", "stick top parameters"):
                link_bundle(tree, add_group(tree, group), spare.inputs[0])
        else:
            switch.inputs["Menu"].default_value = items[0]

    for variant in ("GripV", "GripX"):
        for family in ("abxy", "dpad", "select", "home"):
            tree, join = preset_group(f"{variant} {family}")
            link_bundle(tree, add_group(tree, "curve parameters", values={"width": 12.0}), join.inputs[0])

    # Battery: GripX keeps an unconnected cover set in frame "battery"; the live one is .001
    tree, join = preset_group("GripV cover parameters")
    link_bundle(tree, add_group(tree, "advanced cover parameters"), join.inputs[0])
    tree, join = preset_group("GripX cover parameters")
    dead_join = tree.nodes.new("NodeJoinBundle")
    link_bundle(tree, add_group(tree, "advanced cover parameters", frame=add_frame(tree, "battery"),
                                values={"battery length": 50.0}), dead_join.inputs[0])
    link_bundle(tree, add_group(tree, "advanced cover parameters", "advanced cover parameters.001",
                                frame=add_frame(tree, "old cover"), values={"battery length": 60.0}), join.inputs[0])

    for name in ("GripV", "GripX", "source"):
        if name not in bpy.data.scenes:
            bpy.data.scenes.new(name)


def clear_fixture():
    for tree in list(bpy.data.node_groups):
        bpy.data.node_groups.remove(tree)


def snapshot():
    """Every input value of every node, to prove that drawing writes nothing."""
    values = {}
    for tree in bpy.data.node_groups:
        for node in tree.nodes:
            for socket in node.inputs:
                if hasattr(socket, "default_value"):
                    value = socket.default_value
                    values[(tree.name, node.name, socket.identifier)] = (
                        tuple(value) if hasattr(value, "__len__") and not isinstance(value, str) else value)
            if node.bl_idname == "FunctionNodeInputMenu":
                values[(tree.name, node.name, "value")] = node.value
    return values


# ---------------------------------------------------------------- a layout that records what the panels draw

class FakeLayout:
    """Stands in for bpy.types.UILayout. prop() reads the property, so a wrong name fails the test."""

    def __init__(self, log, enabled=True):
        self.log = log
        self.parent_enabled = enabled
        self.enabled = True
        self.alert = False
        self.active = True
        self.use_property_split = False
        self.use_property_decorate = True
        self.scale_y = 1.0

    def _child(self):
        return FakeLayout(self.log, self.parent_enabled and self.enabled)

    def row(self, align=False, heading=""):
        return self._child()

    column = box = row

    def split(self, factor=0.0, align=False):
        return self._child()

    def separator(self, factor=1.0):
        pass

    def label(self, text="", icon='NONE'):
        self.log.append(("label", text, self.parent_enabled and self.enabled))

    def prop(self, data, prop, text=None, **_kwargs):
        if not hasattr(data, prop):
            raise AttributeError(f"{data!r} has no property {prop!r}")
        getattr(data, prop)
        self.log.append(("prop", text, self.parent_enabled and self.enabled, data, prop))

    def operator(self, idname, text="", icon='NONE'):
        category, name = idname.split(".")
        if not hasattr(getattr(bpy.ops, category), name):
            raise AttributeError(f"no operator {idname}")
        self.log.append(("operator", idname, self.parent_enabled and self.enabled))
        return SimpleNamespace()


def draw_panel(cls, context):
    """Runs a panel's poll and draw like Blender. Returns the recorded calls, or None when poll hides it."""
    if hasattr(cls, "poll") and not cls.poll(context):
        return None
    log = []
    cls.draw(SimpleNamespace(layout=FakeLayout(log), section=getattr(cls, "section", None)), context)
    return log


def fake_context(scene_name="GripV", window_scenes=None):
    scene = bpy.data.scenes.get(scene_name) or bpy.context.scene
    windows = [SimpleNamespace(scene=bpy.data.scenes[n]) for n in (window_scenes or [])]
    return SimpleNamespace(scene=scene, preferences=bpy.context.preferences,
                           window_manager=SimpleNamespace(windows=windows))


def labels(log):
    return [entry[1] for entry in log]


def props(log):
    """The first prop drawn under each label."""
    found = {}
    for entry in log:
        if entry[0] == "prop":
            found.setdefault(entry[1], entry)
    return found


# ---------------------------------------------------------------- tests

class GripControlsTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        clear_fixture()
        enable_addon()
        cls.resolve = submodule("resolve")
        cls.sync = submodule("sync")
        cls.ui = submodule("ui")

    @classmethod
    def tearDownClass(cls):
        disable_addon()
        clear_fixture()

    def setUp(self):
        clear_fixture()
        build_fixture()
        self.prefs = bpy.context.preferences.addons[ADDON].preferences
        self.prefs.sync_variant = False  # tests turn it on where they need it
        self.set_global("variant", "GripV")
        self.set_global("style", "xbox")

    def set_global(self, name, value):
        bpy.data.node_groups["global"].nodes["global parameters"].inputs[name].default_value = value

    def find(self, group, constructor, style=None):
        return self.resolve.find_constructor(bpy.data.node_groups[group], constructor, style)

    # registration -------------------------------------------------------

    def test_registered(self):
        for cls in self.ui.classes:
            self.assertTrue(cls.is_registered, cls.__name__)
        self.assertTrue(hasattr(bpy.ops.grip, "match_variant"))
        self.assertTrue(self.sync.is_subscribed())
        self.assertEqual({c.bl_category for c in self.ui.classes if hasattr(c, "bl_category")}, {"Grip"})

    def test_manifest_valid(self):
        tool = os.path.join(bpy.utils.system_resource('SCRIPTS'), "addons_core", "bl_pkg", "cli", "blender_ext.py")
        if not os.path.exists(tool):
            self.skipTest("Blender's extension tool not found")
        result = subprocess.run([sys.executable, "-I", tool, "validate", EXT_DIR], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertFalse(hasattr(sys.modules[ADDON], "bl_info"))

    # global settings ----------------------------------------------------

    def test_global_resolution(self):
        r = self.resolve
        self.assertTrue(r.is_grip_file())
        self.assertEqual(r.current_variant(), "GripV")
        self.assertIsNone(r.current_style())  # GripV ignores style
        self.set_global("variant", "GripX")
        self.set_global("style", "dualsense")
        self.assertEqual(r.current_style(), "dualsense")
        for name in r.GLOBAL_INPUTS:
            field = r.global_field(name)
            self.assertIsNotNone(field.socket, name)
            self.assertIsNone(field.source, name)

    def test_body_inputs(self):
        body = self.resolve.body_inputs
        self.assertEqual(body("GripV", "standard", False), ["hollow top", "pillars", "screws"])
        self.assertEqual(body("GripV", "standard", True), ["hollow top", "ribs", "pillars", "screws", "screws hollow"])
        self.assertEqual(body("GripX", "standard", True), ["pillars", "screws"])
        self.assertEqual(body("GripX", "indent", False), ["fill type", "pillars", "screws"])
        self.assertEqual(body("GripV", "hollow", False), ["ribs", "screws hollow"])
        self.assertEqual(body("GripX", "lattice", False), ["ribs", "pillars", "screws hollow"])

    # part presets -------------------------------------------------------

    def test_gripv_trigger_skips_snes(self):
        node, problem = self.find("GripV R2 parameters", "trigger parameters")
        self.assertIsNone(problem)
        self.assertEqual(node.name, "trigger parameters.001")
        self.assertEqual(node.inputs["trigger length"].default_value, 28.0)

    def test_snes_never_shown_even_if_connected(self):
        tree = bpy.data.node_groups["GripV R2 parameters"]
        snes = tree.nodes["trigger parameters"]
        link_bundle(tree, snes, tree.nodes["Join Bundle"].inputs[0])
        node, problem = self.find("GripV R2 parameters", "trigger parameters")
        self.assertEqual(node.name, "trigger parameters.001")

    def test_gripx_style_by_switch(self):
        node, _ = self.find("GripX R2 parameters", "trigger parameters", "xbox")
        self.assertAlmostEqual(node.inputs["trigger length"].default_value, 30.5, places=4)
        node, _ = self.find("GripX R2 parameters", "trigger parameters", "dualsense")
        self.assertAlmostEqual(node.inputs["trigger length"].default_value, 30.15, places=4)
        node, _ = self.find("GripX lever R1L1", "R1L1 lever parameters", "dualsense")
        self.assertEqual(node.name, "R1L1 lever parameters.001")

    def test_gripx_style_by_frame(self):
        node, _ = self.find("GripX R4 parameters", "trigger parameters", "xbox")
        self.assertAlmostEqual(node.inputs["trigger length"].default_value, 21.2, places=4)
        node, _ = self.find("GripX R4 parameters", "trigger parameters", "dualsense")
        self.assertAlmostEqual(node.inputs["trigger length"].default_value, 24.1, places=4)
        node, problem = self.find("GripX R4 parameters", "trigger parameters", None)
        self.assertIsNone(node)
        self.assertEqual(problem, self.resolve.AMBIGUOUS)

    def test_switch_wins_over_frame(self):
        """When the frame labels and the gripD switch disagree, the switch is what the geometry uses."""
        tree = bpy.data.node_groups["GripX R2 parameters"]
        tree.nodes["trigger parameters"].parent.label = "GripD"
        tree.nodes["trigger parameters.001"].parent.label = "GripX"
        node, _ = self.find("GripX R2 parameters", "trigger parameters", "xbox")
        self.assertEqual(node.name, "trigger parameters")

    def test_unconnected_cover_skipped(self):
        node, _ = self.find("GripX cover parameters", "advanced cover parameters")
        self.assertEqual(node.name, "advanced cover parameters.001")

    def test_missing_and_unconnected(self):
        r = self.resolve
        node, problem = self.find("GripV R2 parameters", "curve parameters")
        self.assertEqual((node, problem), (None, r.NO_NODE))
        tree = bpy.data.node_groups["GripV R4 parameters"]
        tree.links.remove(tree.nodes["trigger parameters"].outputs["Bundle"].links[0])
        node, problem = self.find("GripV R4 parameters", "trigger parameters")
        self.assertEqual((node, problem), (None, r.NOT_CONNECTED))

    def test_linked_inputs(self):
        r = self.resolve
        lever = bpy.data.node_groups["GripV  lever R1L1"].nodes["R1L1 lever parameters"]
        field = r.resolve_field(lever, r.FieldSpec("R1L1", "R1L1 lever parameters", "stem radius", "stem radius"))
        self.assertEqual(field.source, "Value")
        trigger = bpy.data.node_groups["GripV R2 parameters"].nodes["trigger parameters.001"]
        field = r.resolve_field(trigger, r.FieldSpec("R2", "trigger parameters", "x tolerance", "x tolerance"))
        self.assertEqual(field.source, "tolerance set")
        block = r.resolve_block(r.SECTIONS_BY_KEY["triggers"].blocks[1], "GripV")
        shift = next(row for row in block.rows if row.label == "shift z")
        self.assertEqual(shift.source, "paddle shift")
        log = draw_panel(self.ui.VIEW3D_PT_grip_triggers, fake_context())
        editable = [e for e in log if e[0] == "prop" and e[1] == "shift z"]
        self.assertEqual(len(editable), 1)  # R2 only: R4 shows a greyed line instead
        self.assertIn(("label", "shift z: set by paddle shift", False), log)

    def test_gripx_stick_preset_from_menu_node(self):
        r = self.resolve
        tree = bpy.data.node_groups["GripX stick L parameters"]
        preset = r.find_preset(tree)
        self.assertEqual((preset.item, preset.problem), ("Xbox cap", None))
        self.assertEqual(preset.members, {"basic stick parameters.001", "stick top parameters.001"})
        tree.nodes["stick menu"].value = "Octagonal 18d range"
        block = r.resolve_block(r.SECTIONS_BY_KEY["sticks"].blocks[0], "GripX", "xbox")
        selector = block.rows[0]
        self.assertIsInstance(selector, r.Selector)
        self.assertEqual((selector.data.name, selector.prop, selector.item), ("stick menu", "value",
                                                                             "Octagonal 18d range"))
        height = next(row for row in block.rows if row.label == "stick heght")
        self.assertEqual(height.node, "basic stick parameters.002")
        self.assertEqual(height.socket.default_value, 12.0)

    def test_gripx_stick_preset_from_switch_value(self):
        r = self.resolve
        tree = bpy.data.node_groups["GripX stick R parameters"]
        tree.nodes["Menu Switch"].inputs["Menu"].default_value = "small round"
        preset = r.find_preset(tree)
        self.assertEqual(preset.prop, "default_value")
        self.assertEqual(preset.members, {"basic stick parameters.002", "stick top parameters.002"})

    def test_stick_preset_unresolved(self):
        """A preset menu fed by something other than a Menu node is not guessed."""
        r = self.resolve
        tree = bpy.data.node_groups["GripX stick L parameters"]
        menu = tree.nodes["stick menu"]
        reroute = tree.nodes.new("NodeReroute")
        group_in = tree.nodes.new("NodeGroupInput")
        tree.interface.new_socket("menu", in_out='INPUT', socket_type='NodeSocketMenu')
        tree.links.new(group_in.outputs["menu"], reroute.inputs[0])
        tree.links.new(reroute.outputs[0], tree.nodes["Menu Switch"].inputs["Menu"])
        tree.nodes.remove(menu)
        block = r.resolve_block(r.SECTIONS_BY_KEY["sticks"].blocks[0], "GripX", "xbox")
        self.assertTrue(all(row.problem == r.NO_PRESET for row in block.rows))
        self.set_global("variant", "GripX")
        log = draw_panel(self.ui.VIEW3D_PT_grip_sticks, fake_context())
        self.assertIn(("label", f"preset: {r.NO_PRESET}", False), log)

    def test_every_block_resolves(self):
        r = self.resolve
        for variant in r.VARIANTS:
            for style in ((None,) if variant == "GripV" else ("xbox", "dualsense")):
                for section in r.SECTIONS:
                    for block in section.blocks:
                        for row in r.resolve_block(block, variant, style).rows:
                            linked_on_purpose = variant == "GripV" and row.label == "shift z"
                            if isinstance(row, r.Field) and not linked_on_purpose:
                                self.assertIsNone(row.problem, (variant, style, block.title, row))
                                self.assertIsNone(row.source, (variant, style, block.title, row))

    # files that are not Grip.blend ---------------------------------------

    def test_missing_file(self):
        clear_fixture()
        r, ui = self.resolve, self.ui
        self.assertFalse(r.is_grip_file())
        self.assertIsNone(r.current_variant())
        self.assertFalse(r.set_variant("GripX"))
        log = draw_panel(ui.VIEW3D_PT_grip_controller, fake_context())
        self.assertIn("This tab is meant for Grip.blend.", labels(log))
        for cls in ui.classes:
            if issubclass(cls, bpy.types.Panel) and cls is not ui.VIEW3D_PT_grip_controller:
                self.assertIsNone(draw_panel(cls, fake_context()), cls.__name__)
        self.assertFalse(ui.GRIP_OT_match_variant.poll(fake_context("GripX")))
        block = r.resolve_block(r.SECTIONS_BY_KEY["triggers"].blocks[0], "GripV")
        self.assertTrue(all(row.problem == r.NO_GROUP for row in block.rows))

    def test_partly_missing_file(self):
        """A renamed node or input gives greyed rows, the rest still draws."""
        r = self.resolve
        bpy.data.node_groups.remove(bpy.data.node_groups["GripV home"])
        bpy.data.node_groups["GripV select"].nodes["curve parameters"].node_tree = constructor("outline", ("width",))
        bpy.data.node_groups["global parameters"].interface.items_tree["marks"].name = "letters"
        log = draw_panel(self.ui.VIEW3D_PT_grip_buttons, fake_context())
        self.assertIn(("label", f"home: {r.NO_GROUP}", False), log)
        self.assertIn(("label", f"select: {r.NO_NODE}", False), log)
        self.assertIn("abxy", props(log))
        log = draw_panel(self.ui.VIEW3D_PT_grip_features, fake_context())
        self.assertIn(("label", f"marks: {r.NO_INPUT}", False), log)

    # drawing ------------------------------------------------------------

    def test_draw_all_panels_writes_nothing(self):
        ui = self.ui
        panels = [c for c in ui.classes if issubclass(c, bpy.types.Panel)]
        for variant, style, scene in (("GripV", "xbox", "GripV"), ("GripX", "xbox", "GripX"),
                                      ("GripX", "dualsense", "GripV"), ("GripR1", "xbox", "source")):
            self.set_global("variant", variant)
            self.set_global("style", style)
            for body in MENUS["body type"]:
                self.set_global("body type", body)
                before = snapshot()
                for cls in panels:
                    log = draw_panel(cls, fake_context(scene))
                    for entry in log or ():
                        self.assertFalse(str(entry[1]).startswith("Could not draw"), (cls.__name__, entry))
                self.assertEqual(snapshot(), before, (variant, style, body))

    def test_controller_panel(self):
        ui = self.ui
        log = draw_panel(ui.VIEW3D_PT_grip_controller, fake_context("GripV"))
        drawn = props(log)
        self.assertEqual(set(drawn) & {"variant", "style", "body type", "hollow top", "screws"},
                         {"variant", "style", "body type", "hollow top", "screws"})
        self.assertFalse(drawn["style"][2])  # style greyed for GripV
        self.assertTrue(any(e[0] == "prop" and e[4] == "sync_variant" for e in log))
        self.assertIn(("operator", "grip.match_variant", True), log)
        log = draw_panel(ui.VIEW3D_PT_grip_controller, fake_context("GripX"))
        self.assertIn("variant is not GripX, the scene shown", labels(log))
        self.set_global("variant", "GripX")
        self.assertTrue(props(draw_panel(ui.VIEW3D_PT_grip_controller, fake_context("GripX")))["style"][2])

    def test_section_panels_draw_sockets(self):
        """The fields are the node sockets themselves, so an edit is a node edit."""
        ui = self.ui
        self.set_global("variant", "GripX")
        self.set_global("style", "dualsense")
        log = draw_panel(ui.VIEW3D_PT_grip_triggers, fake_context("GripX"))
        trigger = bpy.data.node_groups["GripX R2 parameters"].nodes["trigger parameters.001"]
        entry = props(log)["trigger length"]
        self.assertEqual(entry[3], trigger.inputs["trigger length"])
        self.assertEqual(entry[4], "default_value")
        self.assertIn("GripX R2 parameters > trigger parameters.001", labels(log))
        self.assertIn("More: GripX contols > R2R4", labels(log))
        log = draw_panel(ui.VIEW3D_PT_grip_sticks, fake_context("GripX"))
        self.assertEqual(props(log)["preset"][3].name, "stick menu")
        log = draw_panel(ui.VIEW3D_PT_grip_bumpers, fake_context("GripX"))
        self.assertIn("GripX bumpers ignore press tolerance", labels(log))
        self.set_global("stock bumpers", True)
        log = draw_panel(ui.VIEW3D_PT_grip_bumpers, fake_context("GripX"))
        self.assertIn("stock bumpers is on: these values are not used", labels(log))

    def test_editing_through_the_socket(self):
        """Writing the drawn socket changes the node the preset uses, not the alternative."""
        r = self.resolve
        block = r.resolve_block(r.SECTIONS_BY_KEY["triggers"].blocks[0], "GripV")
        length = next(row for row in block.rows if row.label == "trigger length")
        length.socket.default_value = 30.0
        tree = bpy.data.node_groups["GripV R2 parameters"]
        self.assertEqual(tree.nodes["trigger parameters.001"].inputs["trigger length"].default_value, 30.0)
        self.assertEqual(tree.nodes["trigger parameters"].inputs["trigger length"].default_value, 17.0)

    # variant sync ---------------------------------------------------------

    def test_target_variant(self):
        target = self.sync.target_variant
        self.assertEqual(target(["GripX"]), "GripX")
        self.assertEqual(target(["GripV", "source"]), "GripV")
        self.assertIsNone(target(["GripV", "GripX"]))  # two windows disagree: do not guess
        self.assertIsNone(target(["source", "Scene"]))
        self.assertIsNone(target([]))

    def test_sync_writes_only_when_different(self):
        s, r = self.sync, self.resolve
        self.assertTrue(s.sync_scene(bpy.data.scenes["GripX"]))
        self.assertEqual(r.current_variant(), "GripX")
        self.assertFalse(s.sync_scene(bpy.data.scenes["GripX"]))
        self.assertFalse(s.sync_scene(bpy.data.scenes["source"]))
        self.assertEqual(r.current_variant(), "GripX")

    def test_sync_from_windows_follows_toggle(self):
        s, r = self.sync, self.resolve
        self.assertFalse(s.sync_from_windows(fake_context(window_scenes=["GripX"])))  # toggle off
        self.assertEqual(r.current_variant(), "GripV")
        self.prefs.sync_variant = True  # turning it on syncs to bpy.context.scene, which is not a Grip scene
        self.assertEqual(r.current_variant(), "GripV")
        self.assertTrue(s.sync_from_windows(fake_context(window_scenes=["GripX", "source"])))
        self.assertEqual(r.current_variant(), "GripX")
        self.assertFalse(s.sync_from_windows(fake_context(window_scenes=["GripX"])))
        self.assertFalse(s.sync_from_windows(fake_context(window_scenes=["GripV", "GripX"])))
        self.assertEqual(r.current_variant(), "GripX")

    def test_message_bus_callback(self):
        """The callback the message bus calls reads the real context and never raises."""
        s, r = self.sync, self.resolve
        self.prefs.sync_variant = True
        window = bpy.context.window_manager.windows[0] if bpy.context.window_manager.windows else None
        if window is None:
            self.skipTest("no window in this build")
        old = window.scene
        try:
            window.scene = bpy.data.scenes["GripX"]
            s._on_window_change()
            self.assertEqual(r.current_variant(), "GripX")
        finally:
            window.scene = old
        clear_fixture()
        s._on_window_change()  # no Grip groups: nothing to do, no error

    def test_operator(self):
        r = self.resolve
        with bpy.context.temp_override(scene=bpy.data.scenes["GripX"]):
            self.assertTrue(bpy.ops.grip.match_variant.poll())
            self.assertEqual(bpy.ops.grip.match_variant(), {'FINISHED'})
            self.assertFalse(bpy.ops.grip.match_variant.poll())  # already matching
        self.assertEqual(r.current_variant(), "GripX")
        with bpy.context.temp_override(scene=bpy.data.scenes["source"]):
            self.assertFalse(bpy.ops.grip.match_variant.poll())


class UnregisterTest(unittest.TestCase):

    def test_disable_cleans_up(self):
        enable_addon()
        sync = submodule("sync")
        disable_addon()
        self.assertFalse(hasattr(bpy.types, "VIEW3D_PT_grip_controller"))
        self.assertFalse(sync.is_subscribed())
        self.assertFalse(bpy.app.timers.is_registered(sync._sync_later))


# ---------------------------------------------------------------- the real file, through blender/tracking.json

LINK = re.compile(r"^\[(.+?)\] (.+?) -> (.+) \[(.+)\]$")


def node_name(key):
    """tracking.json keys a node as 'name (label)' when it has a label."""
    return re.sub(r" \([^()]*\)$", "", key) if " (" in key else key


def parse_links(lines):
    links = []
    for line in lines:
        match = LINK.match(line)
        if match:
            links.append(tuple(match.groups()))
    return links


def tracked_live(links):
    """Node keys whose output reaches 'Group Output', from the link list."""
    feeds = {}
    for from_node, _out, _in, to_node in links:
        feeds.setdefault(to_node, set()).add(from_node)
    live, stack = set(), ["Group Output"]
    while stack:
        key = stack.pop()
        if key not in live:
            live.add(key)
            stack.extend(feeds.get(key, ()))
    return live


class TrackingPathsTest(unittest.TestCase):
    """Every (group, node, input) the tab reads exists in Grip.blend, as recorded in blender/tracking.json."""

    @classmethod
    def setUpClass(cls):
        if not os.path.exists(TRACKING):
            raise unittest.SkipTest("blender/tracking.json not found")
        with open(TRACKING, encoding="utf-8") as f:
            cls.tracking = json.load(f)
        enable_addon()
        cls.resolve = submodule("resolve")

    @classmethod
    def tearDownClass(cls):
        disable_addon()

    def candidates(self, variant, group, constructor):
        """Tracked nodes of the group made from the constructor: {node key: inputs}."""
        nodes = self.tracking["tracked_inputs"][PANELS[variant]][group]["nodes"]
        base = self.resolve.base_name
        return {key: entry.get("inputs", {}) for key, entry in nodes.items()
                if base(node_name(key)) == constructor or node_name(key).startswith(constructor + ".")}

    def test_paths_exist(self):
        for variant in self.resolve.VARIANTS:
            groups = self.tracking["tracked_inputs"][PANELS[variant]]
            for group, constructor, name in self.resolve.tracked_paths(variant):
                with self.subTest(variant=variant, group=group, node=constructor, input=name):
                    self.assertIn(group, groups)
                    found = self.candidates(variant, group, constructor)
                    self.assertTrue(found, "no such node")
                    self.assertTrue(all(name in inputs for inputs in found.values()), "input missing on a node")

    def test_used_node_exists(self):
        """At least one node with the input is connected to the group output, so it is not a leftover."""
        trees = self.tracking["all_node_trees"]
        for variant in self.resolve.VARIANTS:
            for group, constructor, name in self.resolve.tracked_paths(variant):
                with self.subTest(variant=variant, group=group, node=constructor):
                    live = tracked_live(parse_links(trees[group]))
                    found = self.candidates(variant, group, constructor)
                    self.assertTrue(any(key in live for key in found), "only unconnected nodes")

    def test_gripv_triggers_one_live_node(self):
        trees = self.tracking["all_node_trees"]
        for group in ("GripV R2 parameters", "GripV R4 parameters"):
            live = tracked_live(parse_links(trees[group]))
            found = [key for key in self.candidates("GripV", group, "trigger parameters") if key in live]
            self.assertEqual(len(found), 1, group)

    def test_gripx_styles_behind_gripd_switch(self):
        """GripX triggers and bumpers: two connected nodes, one on each side of a Switch driven by gripD."""
        trees = self.tracking["all_node_trees"]
        for group, constructor in (("GripX R2 parameters", "trigger parameters"),
                                   ("GripX R4 parameters", "trigger parameters"),
                                   ("GripX lever R1L1", "R1L1 lever parameters")):
            links = parse_links(trees[group])
            found = self.candidates("GripX", group, constructor)
            sides = {to_socket for from_node, _o, to_socket, to_node in links
                     if from_node in found and to_node == "Switch"}
            self.assertEqual(sides, {"False", "True"}, group)
            self.assertIn(("global outputs", "gripD", "Switch", "Switch"),
                          {(node_name(f), o, i, t) for f, o, i, t in links}, group)

    def test_gripx_stick_presets_resolvable(self):
        """Each item of the GripX stick menus leads (through reroutes) to a Join Bundle with both constructors."""
        trees = self.tracking["all_node_trees"]
        for group in ("GripX stick L parameters", "GripX stick R parameters"):
            links = parse_links(trees[group])
            into = {}
            for from_node, _o, to_socket, to_node in links:
                into.setdefault(to_node, []).append((to_socket, from_node))
            menu_sources = [f for s, f in into.get("Menu Switch", []) if s == "Menu"]
            self.assertEqual(len(menu_sources), 1, group)
            items = [(s, f) for s, f in into["Menu Switch"] if s != "Menu"]
            self.assertGreaterEqual(len(items), 2, group)
            for item, source in items:
                while source.startswith("Reroute"):
                    source = into[source][0][1]
                members = {node_name(f) for _s, f in into.get(source, [])}
                with self.subTest(group=group, item=item):
                    self.assertTrue(source.startswith("Join Bundle"), source)
                    for constructor in ("basic stick parameters", "stick top parameters"):
                        self.assertEqual(len([m for m in members if self.resolve.base_name(m) == constructor
                                              or m.startswith(constructor + ".")]), 1, constructor)


if __name__ == "__main__":
    unittest.main(argv=[sys.argv[0]], verbosity=2)
