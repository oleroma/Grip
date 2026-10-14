"""Finds the node inputs the Grip tab shows. No drawing and no writing here, except set_variant.

Every lookup is by name, as the names are spelled in Grip.blend (typos included), and every function returns
None or a problem text instead of raising, so the panels can show a greyed row when the file differs.
"""
import re
from collections import namedtuple

import bpy

GLOBAL_GROUP = "global"
GLOBAL_NODE = "global parameters"
VARIANTS = ("GripV", "GripX")
CONTROLS_PANELS = {"GripV": "GripV controls", "GripX": "GripX contols"}  # 'contols' sic

# GripX keeps one constructor per style, each in a frame with this label
STYLE_FRAMES = {"xbox": "GripX", "dualsense": "GripD"}
# Frames that hold unconnected alternatives; their nodes are never shown
DEAD_FRAMES = ("SNES",)

# Global settings on 'global' > 'global parameters', grouped as the panels show them
CONTROLLER_INPUTS = ("variant", "style", "body type")
PREVIEW_INPUTS = ("subdivision level", "voxel resolution")
FIT_INPUTS = ("tolerance", "press tolerance", "cap tolerance")
FEATURE_INPUTS = ("cable holder", "stock bumpers", "top wire cutouts", "R4 wire cutouts", "horizontal buttons",
                  "button logo", "marks")
BODY_INPUTS = ("fill type", "hollow top", "ribs", "pillars", "screws", "screws hollow")
GLOBAL_INPUTS = CONTROLLER_INPUTS + BODY_INPUTS + PREVIEW_INPUTS + FIT_INPUTS + FEATURE_INPUTS

# Preset group of each part slot, per variant
PART_GROUPS = {
    "R2": {"GripV": "GripV R2 parameters", "GripX": "GripX R2 parameters"},
    "R4": {"GripV": "GripV R4 parameters", "GripX": "GripX R4 parameters"},
    "R1L1": {"GripV": "GripV  lever R1L1", "GripX": "GripX lever R1L1"},  # two spaces in the GripV name
    "stick L": {"GripV": "GripV stick L parameters", "GripX": "GripX stick L parameters"},
    "stick R": {"GripV": "GripV stick R parameters", "GripX": "GripX stick R parameters"},
    "abxy": {"GripV": "GripV abxy", "GripX": "GripX abxy"},
    "dpad": {"GripV": "GripV dpad", "GripX": "GripX dpad"},
    "select": {"GripV": "GripV select", "GripX": "GripX select"},
    "home": {"GripV": "GripV home", "GripX": "GripX home"},
    "cover": {"GripV": "GripV cover parameters", "GripX": "GripX cover parameters"},
}

FieldSpec = namedtuple("FieldSpec", "slot constructor input label")
Block = namedtuple("Block", "title fields")
Section = namedtuple("Section", "key title frame blocks")


def fields(slot, constructor, inputs):
    """FieldSpecs for several inputs of one constructor, labelled with the input name."""
    return tuple(FieldSpec(slot, constructor, name, name) for name in inputs)


TRIGGER_INPUTS = ("trigger length", "width", "shift z", "x offset", "button radius offset")
STICK_FIELDS = (("basic stick parameters", ("stick heght", "range degrees", "stick top radius")),
                ("stick top parameters", ("top shape", "top curvature", "texture type")))


def stick_fields(slot):
    return sum((fields(slot, constructor, inputs) for constructor, inputs in STICK_FIELDS), ())


SECTIONS = (
    Section("triggers", "Triggers", "R2R4", (
        Block("R2 trigger", fields("R2", "trigger parameters", TRIGGER_INPUTS)),
        Block("R4 back paddle", fields("R4", "trigger parameters", TRIGGER_INPUTS)),
    )),
    Section("bumpers", "Bumpers", "R1L1 LEVER", (
        Block("L1 and R1", fields("R1L1", "R1L1 lever parameters", ("wdith", "height", "X", "Y", "Z"))),
    )),
    Section("sticks", "Sticks", "STICKS", (
        Block("Left stick", stick_fields("stick L")),
        Block("Right stick", stick_fields("stick R")),
    )),
    Section("buttons", "Buttons", "BUTTONS", (
        Block("Size (curve parameters width)", tuple(
            FieldSpec(slot, "curve parameters", "width", slot) for slot in ("abxy", "dpad", "select", "home"))),
    )),
    Section("battery", "Battery", "PCB AND BATTERY", (
        Block("Battery compartment", fields("cover", "advanced cover parameters",
                                            ("battery length", "battery width", "battery height"))),
    )),
)
SECTIONS_BY_KEY = {section.key: section for section in SECTIONS}

# Problem texts shown in greyed rows
NO_GROUP = "not in this file"
NO_NODE = "node not found"
NOT_CONNECTED = "node not connected"
AMBIGUOUS = "several nodes, use the controls panel"
NO_INPUT = "input not found"
NO_PRESET = "preset not resolved, use the controls panel"

# socket: the input to draw, or None. source: name of the node that feeds it when it is linked
Field = namedtuple("Field", "label socket source problem node")
# data, prop: what to draw for the preset menu. item: the selected preset
Selector = namedtuple("Selector", "label data prop item problem")
ResolvedBlock = namedtuple("ResolvedBlock", "title rows where")
Preset = namedtuple("Preset", "data prop item members problem")


# ------------------------------------------------------------------------------------------------ global settings

def global_node():
    """The node 'global parameters' inside the group 'global', or None outside Grip.blend."""
    tree = bpy.data.node_groups.get(GLOBAL_GROUP)
    if tree is None or not hasattr(tree, "nodes"):
        return None
    return tree.nodes.get(GLOBAL_NODE)


def is_grip_file():
    return global_node() is not None


def global_socket(name):
    node = global_node()
    return node.inputs.get(name) if node is not None else None


def global_value(name, default=None):
    socket = global_socket(name)
    return getattr(socket, "default_value", default) if socket is not None else default


def current_variant():
    return global_value("variant")


def current_style():
    """The GripX style, or None for other variants (they ignore it)."""
    return global_value("style") if current_variant() == "GripX" else None


def variant_for_scene(scene_name):
    """The variant a scene shows: the scenes GripV and GripX are named after their variant."""
    return scene_name if scene_name in VARIANTS else None


def set_variant(value):
    """Writes the global variant. Only writes when the value differs; returns True when it wrote."""
    socket = global_socket("variant")
    if socket is None or value is None or socket.is_linked or socket.default_value == value:
        return False
    try:
        socket.default_value = value
    except (TypeError, ValueError):
        return False  # not an item of the menu
    return True


def body_inputs(variant, body_type, hollow_top):
    """The global switches that matter for this body type (see docs/blender/develop/03-case-pipeline.md)."""
    shell_top = variant == "GripV" and body_type == "standard" and bool(hollow_top)
    shell = body_type in ("hollow", "lattice")
    names = []
    if body_type == "indent":
        names.append("fill type")
    if variant == "GripV" and body_type == "standard":
        names.append("hollow top")
    if shell or shell_top:
        names.append("ribs")
    if body_type != "hollow":
        names.append("pillars")
    if body_type in ("standard", "indent"):
        names.append("screws")
    if shell or shell_top:
        names.append("screws hollow")
    return names


def section_notes(key, variant):
    """Short (text, alert) notes for a part section, from the global settings."""
    notes = []
    if key == "bumpers" and global_value("stock bumpers"):
        notes.append(("stock bumpers is on: these values are not used", True))
    if key == "buttons" and global_value("horizontal buttons") is False:
        notes.append(("horizontal buttons is off: the old, unstable design", True))
    if key == "bumpers" and variant == "GripX":
        notes.append(("GripX bumpers ignore press tolerance", False))
    return notes


# ------------------------------------------------------------------------------------------------ node graph

def base_name(name):
    """A name without Blender's numeric suffix: 'trigger parameters.001' -> 'trigger parameters'."""
    return re.sub(r"\.\d+$", "", name)


def is_constructor(node, constructor):
    tree = getattr(node, "node_tree", None)
    return node.bl_idname == "GeometryNodeGroup" and tree is not None and base_name(tree.name) == constructor


def frame_labels(node):
    """Labels (or names) of the frames around a node, innermost first."""
    labels = []
    parent = node.parent
    while parent is not None and len(labels) < 32:
        labels.append((parent.label or parent.name).strip())
        parent = parent.parent
    return labels


def live_node_names(tree):
    """Names of the nodes whose output reaches the group output through links: the nodes that are used."""
    feeds = {}
    for link in tree.links:
        if link.is_muted or not link.is_valid:
            continue
        feeds.setdefault(link.to_node.name, set()).add(link.from_node.name)
    outputs = [n for n in tree.nodes if n.bl_idname == "NodeGroupOutput"]
    active = [n for n in outputs if getattr(n, "is_active_output", False)]
    stack = [n.name for n in (active or outputs)]
    live = set()
    while stack:
        name = stack.pop()
        if name not in live:
            live.add(name)
            stack.extend(feeds.get(name, ()))
    return live


def upstream_node(socket):
    """The node that feeds an input socket, skipping reroutes, or None when nothing real is linked."""
    for _ in range(64):
        if socket is None or not socket.is_linked:
            return None
        links = socket.links
        if not links:
            return None
        node = links[0].from_node
        if node.bl_idname != "NodeReroute":
            return node
        socket = node.inputs[0] if node.inputs else None
    return None


def pick_by_switch(tree, nodes, style):
    """The node a Switch driven by 'gripD' passes on for the style (False = xbox, True = dualsense)."""
    want = "True" if style == "dualsense" else "False"
    names = {n.name for n in nodes}
    for link in tree.links:
        switch = link.to_node
        if (link.from_node.name not in names or switch.bl_idname != "GeometryNodeSwitch"
                or link.to_socket.name != want):
            continue
        control = switch.inputs.get("Switch")
        if control is not None and control.is_linked and control.links[0].from_socket.name == "gripD":
            return link.from_node
    return None


def pick_by_frame(nodes, style):
    """The only node inside the frame of the style ('GripX' for xbox, 'GripD' for dualsense)."""
    want = STYLE_FRAMES.get(style, "").lower()
    found = [n for n in nodes if want and want in (label.lower() for label in frame_labels(n))]
    return found[0] if len(found) == 1 else None


def find_constructor(tree, constructor, style=None, among=None, live=None):
    """Returns (node, problem): the constructor node the preset group really uses.

    Unconnected alternatives and nodes in DEAD_FRAMES are skipped. When several connected nodes remain (GripX
    styles), the style decides: first by the gripD Switch they feed, then by the label of their frame.
    """
    nodes = [n for n in tree.nodes if is_constructor(n, constructor) and (among is None or n.name in among)]
    nodes = [n for n in nodes if not set(frame_labels(n)) & set(DEAD_FRAMES)]
    if not nodes:
        return None, NO_NODE
    live = live_node_names(tree) if live is None else live
    used = [n for n in nodes if n.name in live]
    if len(used) == 1:
        return used[0], None
    if not used:
        return None, NOT_CONNECTED
    if style:
        node = pick_by_switch(tree, used, style) or pick_by_frame(used, style)
        if node is not None:
            return node, None
    return None, AMBIGUOUS


def find_preset(tree, live=None):
    """The named preset a group picks with a Menu Switch (GripX sticks), or None when it has none.

    Follows the Menu Switch to the Menu node that drives it, reads the selected item, and collects the nodes linked
    into what that item's input receives (a Join Bundle). Anything unexpected gives a Preset with a problem.
    """
    live = live_node_names(tree) if live is None else live
    switches = [n for n in tree.nodes if n.bl_idname == "GeometryNodeMenuSwitch" and n.name in live]
    if not switches:
        return None
    if len(switches) > 1:
        return Preset(None, None, None, None, NO_PRESET)
    switch = switches[0]
    menu = switch.inputs[0] if switch.inputs else None
    if menu is None:
        return Preset(None, None, None, None, NO_PRESET)
    if menu.is_linked:
        source = upstream_node(menu)
        if source is None or source.bl_idname != "FunctionNodeInputMenu":
            return Preset(None, None, None, None, NO_PRESET)
        data, prop = source, "value"
    else:
        data, prop = menu, "default_value"
    item = getattr(data, prop, None)
    socket = next((s for s in list(switch.inputs)[1:] if s.name == item and s.enabled), None)
    joined = upstream_node(socket) if socket is not None else None
    if joined is None:
        return Preset(data, prop, item, None, NO_PRESET)
    members = {link.from_node.name for link in tree.links if link.to_node == joined}
    return Preset(data, prop, item, members, None)


def part_group(slot, variant):
    name = PART_GROUPS.get(slot, {}).get(variant)
    return bpy.data.node_groups.get(name) if name else None


def resolve_field(socket_owner, spec, problem=None):
    """A Field for one input of a node: editable, linked, or missing with the reason."""
    if socket_owner is None:
        return Field(spec.label, None, None, problem or NO_NODE, None)
    socket = socket_owner.inputs.get(spec.input)
    if socket is None or not hasattr(socket, "default_value"):
        return Field(spec.label, None, None, NO_INPUT, socket_owner.name)
    if socket.is_linked:
        source = upstream_node(socket)
        return Field(spec.label, socket, source.label or source.name if source else "a link", None, socket_owner.name)
    return Field(spec.label, socket, None, None, socket_owner.name)


def global_field(name, label=None):
    node = global_node()
    return resolve_field(node, FieldSpec(None, GLOBAL_NODE, name, label or name), NO_GROUP)


def resolve_block(block, variant, style=None):
    """Resolves a Block for the variant: preset menu rows (GripX sticks) and one Field per input."""
    rows, groups, nodes = [], [], []
    cache = {}
    for spec in block.fields:
        tree = part_group(spec.slot, variant)
        if tree is None:
            rows.append(Field(spec.label, None, None, NO_GROUP, None))
            continue
        if tree.name not in cache:
            live = live_node_names(tree)
            preset = find_preset(tree, live)
            cache[tree.name] = (live, preset)
            groups.append(tree.name)
            if preset is not None:
                rows.append(Selector("preset", preset.data, preset.prop, preset.item, preset.problem))
        live, preset = cache[tree.name]
        if preset is not None and preset.problem:
            rows.append(Field(spec.label, None, None, NO_PRESET, None))
            continue
        node, problem = find_constructor(tree, spec.constructor, style, preset.members if preset else None, live)
        rows.append(resolve_field(node, spec, problem))
        if node is not None and node.name not in nodes:
            nodes.append(node.name)
    where = " | ".join(groups)
    if len(groups) == 1 and len(nodes) == 1:
        where += f" > {nodes[0]}"
    return ResolvedBlock(block.title, rows, where)


def tracked_paths(variant):
    """Every (group, constructor, input) the tab reads for a variant, to check against blender/tracking.json."""
    paths = [(GLOBAL_GROUP, GLOBAL_NODE, name) for name in GLOBAL_INPUTS]
    for section in SECTIONS:
        for block in section.blocks:
            for spec in block.fields:
                paths.append((PART_GROUPS[spec.slot][variant], spec.constructor, spec.input))
    return paths
