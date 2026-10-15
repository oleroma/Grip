"""Fixture tests for apply_tooltips.py. They need Blender's Python module bpy:

    python scripts/tests/test_apply_tooltips.py -v

(with a Python that has bpy installed, for example `pip install bpy` in a
virtual environment). Grip.blend is not opened: the node groups are built in
memory, one per group in TOOLTIPS, with a float input for every entry. Some of
the inputs sit in a panel, and some in a panel inside that panel.
"""

import io
import re
import sys
import unittest
from unittest import mock
from contextlib import redirect_stdout
from pathlib import Path

import bpy

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import apply_tooltips  # noqa: E402

TOOLTIPS = apply_tooltips.TOOLTIPS
ENTRIES = sum(len(tooltips) for tooltips in TOOLTIPS.values())

# The typo cleanup, written out here so the test does not check
# apply_tooltips.corrected against itself.
CLEANUP = [
    (r"\bwdith\b", "width"), (r"\bheght\b", "height"), (r"\bstiick\b", "stick"),
    (r"\bsheild\b", "shield"), (r"\bsbdiv\b", "subdiv"), (r"\bparam(te)?ters\b", "parameters"),
    (r"\bpostion\b", "position"), (r"\bcontols\b", "controls"),
]


def cleanup(name):
    for pattern, fix in CLEANUP:
        name = re.sub(pattern, fix, name)
    return " ".join(name.split())


# Old spellings of a few current names, to test the fallback with a table
# whose keys still carry typos (as it did before the cleanup of 2026-10-15).
TYPOS = {"pins position": "pins postion", "hollow parameters": "hollow  parameters", "width": "wdith",
         "shield": "sheild", "shield height": "sheild height", "stick height": "stick heght"}


def typo_table():
    return {TYPOS.get(name, name): {TYPOS.get(key, key): text for key, text in tooltips.items()}
            for name, tooltips in TOOLTIPS.items()}


def clear():
    for group in list(bpy.data.node_groups):
        bpy.data.node_groups.remove(group)


def build(name, inputs, tree_type='GeometryNodeTree'):
    """A node group with a float input per name. Returns the group."""
    group = bpy.data.node_groups.new(name, tree_type)
    outer = group.interface.new_panel("settings")
    inner = group.interface.new_panel("more")
    group.interface.move_to_parent(inner, outer, 0)
    for i, input_name in enumerate(inputs):
        parent = inner if i % 9 == 8 else outer if i % 3 == 2 else None
        socket = group.interface.new_socket(input_name, in_out='INPUT', socket_type='NodeSocketFloat', parent=parent)
        socket.default_value = 0.25 + i
        socket.min_value = -100.0
        socket.max_value = 100.0
    group.interface.new_socket("Bundle", in_out='OUTPUT', socket_type='NodeSocketBundle')
    return group


def build_all(rename=lambda name: name):
    """One group per TOOLTIPS group, names passed through rename."""
    return {name: build(rename(name), [rename(key) for key in tooltips]) for name, tooltips in TOOLTIPS.items()}


def descriptions(group):
    return {item.name: item.description for item in group.interface.items_tree
            if item.item_type == 'SOCKET' and item.in_out == 'INPUT'}


def snapshot(group):
    """Everything about the interface except the descriptions."""
    items = []
    for item in group.interface.items_tree:
        row = [item.item_type, item.name, item.parent.name, item.position]
        if item.item_type == 'SOCKET':
            row += [item.in_out, item.identifier, item.socket_type]
            if item.in_out == 'INPUT':
                row += [round(item.default_value, 6), item.min_value, item.max_value]
        else:
            row.append(item.description)
        items.append(tuple(row))
    return items


class ApplyTooltipsTest(unittest.TestCase):

    def setUp(self):
        clear()

    def run_script(self, dry_run=False):
        out = io.StringIO()
        with redirect_stdout(out):
            report = apply_tooltips.apply_tooltips(dry_run)
            apply_tooltips.print_report(report, dry_run)
        return report, out.getvalue()

    def assert_clean(self, report):
        for key in ("missing_groups", "missing_inputs", "missing_in_copies", "linked", "uncovered", "replaced"):
            self.assertEqual(report[key], [], key)

    def test_dry_run_changes_nothing(self):
        groups = build_all()
        report, text = self.run_script(dry_run=True)
        self.assertEqual(report["changed"], ENTRIES)
        self.assertEqual(report["unchanged"], 0)
        self.assert_clean(report)
        self.assertIn(f"Would set {ENTRIES} tooltips", text)
        self.assertIn("dry run, nothing changed", text)
        for group in groups.values():
            self.assertEqual(set(descriptions(group).values()), {""}, group.name)

    def test_main_honours_dry_run_switch(self):
        groups = build_all()
        old = apply_tooltips.DRY_RUN
        apply_tooltips.DRY_RUN = True
        try:
            with redirect_stdout(io.StringIO()):
                apply_tooltips.main()
        finally:
            apply_tooltips.DRY_RUN = old
        self.assertEqual(set(descriptions(groups["pins params"]).values()), {""})

    def test_apply_sets_every_tooltip(self):
        groups = build_all()
        report, text = self.run_script()
        self.assertEqual(report["changed"], ENTRIES)
        self.assert_clean(report)
        self.assertEqual(report["corrected"], [])
        self.assertIn(f"Set {ENTRIES} tooltips, 0 already up to date.", text)
        for name, tooltips in TOOLTIPS.items():
            self.assertEqual(descriptions(groups[name]), tooltips, name)

    def test_second_run_is_a_no_op(self):
        groups = build_all()
        self.run_script()
        before = {name: descriptions(group) for name, group in groups.items()}
        report, text = self.run_script()
        self.assertEqual(report["changed"], 0)
        self.assertEqual(report["unchanged"], ENTRIES)
        self.assert_clean(report)
        self.assertIn(f"Set 0 tooltips, {ENTRIES} already up to date.", text)
        self.assertEqual({name: descriptions(group) for name, group in groups.items()}, before)

    def test_defaults_and_values_unchanged(self):
        groups = build_all()
        # Group nodes with typed values, as in the presets.
        preset = bpy.data.node_groups.new("GripV test preset", 'GeometryNodeTree')
        nodes = []
        for name in ("trigger parameters", "marks parameters", "pins position", "hollow parameters"):
            node = preset.nodes.new('GeometryNodeGroup')
            node.node_tree = groups[name]
            for i, socket in enumerate(node.inputs):
                socket.default_value = 7.5 - i
            nodes.append(node)
        before = {name: snapshot(group) for name, group in groups.items()}
        values = [[round(socket.default_value, 6) for socket in node.inputs] for node in nodes]
        names = sorted(group.name for group in bpy.data.node_groups)
        self.run_script()
        self.assertEqual({name: snapshot(group) for name, group in groups.items()}, before)
        self.assertEqual([[round(socket.default_value, 6) for socket in node.inputs] for node in nodes], values)
        self.assertEqual(sorted(group.name for group in bpy.data.node_groups), names)

    def test_inputs_in_panels(self):
        groups = build_all()
        self.run_script()
        in_panels = 0
        for name, group in groups.items():
            for item in group.interface.items_tree:
                if item.item_type == 'PANEL':
                    self.assertEqual(item.description, "", f"{name} > panel {item.name}")
                elif item.in_out == 'INPUT' and item.parent.name:
                    self.assertEqual(item.description, TOOLTIPS[name][item.name])
                    in_panels += 1
        nested = sum(1 for group in groups.values() for item in group.interface.items_tree
                     if item.item_type == 'SOCKET' and item.parent.name == "more")
        self.assertGreater(nested, 0)
        self.assertGreater(in_panels, nested)

    def test_numbered_copies(self):
        build("pins params", TOOLTIPS["pins params"])
        copy = build("pins params.001", TOOLTIPS["pins params"])
        build("screw parameters", TOOLTIPS["screw parameters"])
        # An older group that only shares the name, with other inputs.
        legacy = build("screw parameters.002", ["screw hole diameter", "screw front length"])
        report, text = self.run_script()
        self.assertEqual(descriptions(copy), TOOLTIPS["pins params"])
        self.assertEqual(descriptions(legacy)["screw hole diameter"], TOOLTIPS["screw parameters"]["screw hole diameter"])
        self.assertEqual(descriptions(legacy)["screw front length"], "")
        self.assertEqual(report["missing_inputs"], [])
        self.assertEqual(len(report["missing_in_copies"]), len(TOOLTIPS["screw parameters"]) - 1)
        self.assertTrue(all(line.startswith("screw parameters.002 > ") for line in report["missing_in_copies"]))
        self.assertEqual(report["uncovered"], [])
        self.assertIn("Input not found in a numbered copy", text)

    def test_fallback_spellings(self):
        groups = build_all()
        table = typo_table()
        with mock.patch.object(apply_tooltips, "TOOLTIPS", table):
            report, text = self.run_script()
        self.assertEqual(report["changed"], ENTRIES)
        self.assert_clean(report)
        for name, tooltips in TOOLTIPS.items():
            self.assertEqual(descriptions(groups[name]), tooltips, name)
        expected = {f"{name!r} -> {cleanup(name)!r}" for name in table if cleanup(name) != name}
        for name, tooltips in table.items():
            expected |= {f"{cleanup(name)} > {key!r} -> {cleanup(key)!r}" for key in tooltips if cleanup(key) != key}
        self.assertEqual(set(report["corrected"]), expected)
        self.assertIn(f"Matched through a corrected spelling ({len(expected)}):", text)
        self.assertIn("  'pins postion' -> 'pins position'", text)
        self.assertIn("  R1L1 lever parameters > 'wdith' -> 'width'", text)

    def test_exact_name_wins_over_corrected_spelling(self):
        table = typo_table()
        exact = build("hollow  parameters", table["hollow  parameters"])
        other = build("hollow parameters", table["hollow  parameters"])
        shield = build("shield parameters", list(table["shield parameters"]) + ["shield"])
        with mock.patch.object(apply_tooltips, "TOOLTIPS", table):
            report, _ = self.run_script()
        self.assertEqual(descriptions(exact), table["hollow  parameters"])
        self.assertEqual(set(descriptions(other).values()), {""})
        self.assertEqual(descriptions(shield)["sheild"], table["shield parameters"]["sheild"])
        self.assertEqual(descriptions(shield)["shield"], "")
        self.assertEqual(report["corrected"], [])
        self.assertIn("shield parameters > 'shield'", report["uncovered"])

    def test_find_input_leaves_exact_keys_alone(self):
        find = apply_tooltips.find_input
        self.assertEqual(find({"width": ["a"], "wdith": ["b"]}, "wdith", {"wdith", "width"}), (["b"], "wdith"))
        self.assertEqual(find({"width": ["a"]}, "wdith", {"wdith"}), (["a"], "width"))
        self.assertEqual(find({"width": ["a"]}, "wdith", {"wdith", "width"}), ([], None))
        self.assertEqual(find({"stick XY correction": ["a"]}, "stick  XY correction", set()), (["a"], "stick XY correction"))
        self.assertEqual(find({"case cutout thickness": ["a"]}, "case cutout thickness ", set()), (["a"], "case cutout thickness"))

    def test_existing_tooltip_is_replaced_and_reported(self):
        group = build("pins params", TOOLTIPS["pins params"])
        for item in group.interface.items_tree:
            if item.name == "bevel":
                item.description = "old text"
        report, _ = self.run_script()
        self.assertEqual(report["replaced"], ["pins params > 'bevel': 'old text'"])
        self.assertEqual(descriptions(group)["bevel"], TOOLTIPS["pins params"]["bevel"])

    def test_missing_and_uncovered_inputs_reported(self):
        inputs = [key for key in TOOLTIPS["pins params"] if key != "bevel"] + ["pin depth"]
        build("pins params", inputs)
        report, text = self.run_script()
        self.assertEqual(report["missing_inputs"], ["pins params > 'bevel'"])
        self.assertEqual(report["uncovered"], ["pins params > 'pin depth'"])
        self.assertEqual(len(report["missing_groups"]), len(TOOLTIPS) - 1)
        self.assertIn("Input not found (renamed?) (1):", text)

    def test_other_tree_types_are_ignored(self):
        shader = build("pins params", TOOLTIPS["pins params"], tree_type='ShaderNodeTree')
        report, _ = self.run_script()
        self.assertIn("pins params", report["missing_groups"])
        self.assertEqual(set(descriptions(shader).values()), {""})
        self.assertEqual(report["changed"], 0)


if __name__ == "__main__":
    unittest.main()
