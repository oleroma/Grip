"""Tests for tracking_diff.py. Run: python -m unittest discover tools/tracking_diff

The fixtures are small tracking files with the layout blender_tracking writes
(format version 3): tracked_inputs per panel, preset group and node, meshes as
hashes and all_node_trees as sorted link lines."""

import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tracking_diff as td  # noqa: E402

V, X = "GripV controls", "GripX contols"


def preset(nodes, inputs=None):
    """A preset group entry: {node key: {input: value}} (+ the group's own inputs)."""
    entry = {"nodes": {key: {"inputs": dict(values)} for key, values in nodes.items()}}
    if inputs:
        entry["inputs"] = dict(inputs)
    return entry


def tracking(gripv=None, gripx=None, meshes=None, trees=None, modifiers=None, version=3):
    return {
        "version": version,
        "tracked_inputs": {V: gripv or {}, X: gripx or {}},
        "modifiers": modifiers or {},
        "meshes": meshes or {},
        "all_node_trees": trees or {},
    }


def global_group(**values):
    """The panel content {"global": preset group} with the shared global settings."""
    base = {"variant": "GripV", "subdivision level": "low ", "screws": True}
    base.update(values)
    return {"global": preset({"global parameters": base})}


def text(old, new, verbose=False):
    return td.render_text(td.compare(old, new, "old", "new"), verbose)


def markdown(old, new, verbose=False):
    return td.render_markdown(td.compare(old, new, "old", "new"), verbose)


class ValueTests(unittest.TestCase):
    def test_changed_number_shows_difference(self):
        old = tracking({"GripV stick L parameters": preset({"advanced stick parameters": {"contact angle": 18.1}})})
        new = tracking({"GripV stick L parameters": preset({"advanced stick parameters": {"contact angle": 16.0}})})
        out = text(old, new)
        self.assertIn("1 value changed.", out)
        self.assertIn("GripV (custom ergonomic shape), panel GripV controls", out)
        self.assertIn("  GripV stick L parameters\n    advanced stick parameters\n"
                      "      contact angle: 18.1 -> 16 (-2.1)", out)

    def test_integer_and_small_float_differences(self):
        old = tracking({"g": preset({"n": {"stick subdivision": 64, "X correction": 0.05}})})
        new = tracking({"g": preset({"n": {"stick subdivision": 128, "X correction": 0.1}})})
        out = text(old, new)
        self.assertIn("stick subdivision: 64 -> 128 (+64)", out)
        self.assertIn("X correction: 0.05 -> 0.1 (+0.05)", out)

    def test_boolean(self):
        old = tracking({"g": preset({"n": {"curved R1L1": False, "flag": 1}})})
        new = tracking({"g": preset({"n": {"curved R1L1": True, "flag": True}})})
        out = text(old, new)
        self.assertIn("curved R1L1: off -> on\n", out)
        self.assertIn("flag: 1 -> on\n", out)      # a bool is not the number 1

    def test_menu_keeps_trailing_space_visible(self):
        old = tracking(global_group(**{"subdivision level": "low "}))
        new = tracking(global_group(**{"subdivision level": "low"}))
        self.assertIn('subdivision level: "low " -> "low"', text(old, new))

    def test_vector_shows_changed_axes(self):
        old = tracking({"g": preset({"marks parameters": {"translate": [22.0, 0.0, 0.0]}})})
        new = tracking({"g": preset({"marks parameters": {"translate": [20.0, 0.0, 1.5]}})})
        self.assertIn("translate: [22, 0, 0] -> [20, 0, 1.5] (X -2, Z +1.5)", text(old, new))

    def test_names_with_hidden_spaces_are_quoted(self):
        old = tracking({"GripV  lever R1L1": preset({"n": {"case cutout thickness ": 2.5}})})
        new = tracking({"GripV  lever R1L1": preset({"n": {"case cutout thickness ": 2.0}})})
        out = text(old, new)
        self.assertIn('  "GripV  lever R1L1"\n', out)
        self.assertIn('"case cutout thickness ": 2.5 -> 2 (-0.5)', out)

    def test_added_and_removed_inputs(self):
        old = tracking({"g": preset({"n": {"keep": 1, "gone": 2.0}})})
        new = tracking({"g": preset({"n": {"keep": 1, "fresh": 0.5}})})
        out = text(old, new)
        self.assertIn("1 input added, 1 input removed.", out)
        self.assertIn("fresh: new input, 0.5", out)
        self.assertIn("gone: removed, was 2", out)

    def test_renamed_input_keeps_its_value(self):
        old = tracking({"g": preset({"basic stick parameters": {"stick heght": 6.2}})})
        new = tracking({"g": preset({"basic stick parameters": {"stick height": 6.2}})})
        out = text(old, new)
        self.assertIn("1 input renamed.", out)
        self.assertIn('stick height: probably renamed from stick heght, value 6.2', out)

    def test_rename_needs_the_same_value(self):
        old = tracking({"g": preset({"n": {"stick heght": 6.2}})})
        new = tracking({"g": preset({"n": {"stick height": 7.0}})})
        out = text(old, new)
        self.assertIn("stick height: new input, 7", out)
        self.assertIn("stick heght: removed, was 6.2", out)

    def test_node_settings(self):
        old = tracking({"g": {"nodes": {"Math": {"properties": {"operation": "ADD"}}}}})
        new = tracking({"g": {"nodes": {"Math": {"properties": {"operation": "MULTIPLY"}}}}})
        self.assertIn('operation (setting): "ADD" -> "MULTIPLY"', text(old, new))

    def test_group_own_inputs(self):
        old = tracking({"GripV screw paramters": preset({}, {"Index": 0})})
        new = tracking({"GripV screw paramters": preset({}, {"Index": 1})})
        self.assertIn("  GripV screw paramters\n    Index: 0 -> 1 (+1)", text(old, new))

    def test_unchanged_file(self):
        data = tracking(global_group(), meshes={"basemesh GripV": "a"}, trees={"t": ["[A] x -> y [B]"]})
        self.assertEqual(text(data, json.loads(json.dumps(data))),
                         "tracking.json: old -> new\nNo changes in tracking.json.\n")


class NodeTests(unittest.TestCase):
    def test_added_and_removed_nodes(self):
        old = tracking({"GripX abxy": preset({"button parameters": {"a": 1}, "curve parameters": {"b": 2, "c": 3}})})
        new = tracking({"GripX abxy": preset({"button parameters": {"a": 1}, "marks parameters": {"text": "A"}})})
        out = text(old, new)
        self.assertIn("1 node added, 1 node removed.", out)
        self.assertIn("    curve parameters: removed node, 2 inputs\n", out)
        self.assertIn("    marks parameters: new node, 1 input\n", out)
        self.assertNotIn('text: "A"', out)
        verbose = text(old, new, verbose=True)
        self.assertIn('      text: "A"', verbose)
        self.assertIn("      b: 2", verbose)

    def test_renamed_node(self):
        values = {"extrude texture": True, "square morph": 0.08, "texture type": "grid"}
        changed = dict(values, **{"square morph": 0.1})
        old = tracking(gripx={"GripX stick R parameters": preset({"stick top parameters.001": values,
                                                                  "stick top parameters": {"other": 1}})})
        new = tracking(gripx={"GripX stick R parameters": preset({"stick top parameters.normal": changed,
                                                                  "stick top parameters": {"other": 1}})})
        out = text(old, new)
        self.assertIn("1 value changed, 1 node renamed.", out)
        self.assertIn("    stick top parameters.normal: probably renamed from stick top parameters.001\n"
                      "      square morph: 0.08 -> 0.1 (+0.02)", out)

    def test_different_nodes_are_not_a_rename(self):
        old = tracking({"g": preset({"advanced stick parameters": {"a": 1, "b": 2}})})
        new = tracking({"g": preset({"advanced stick parameters.001": {"a": 5, "b": 6}})})
        out = text(old, new)
        self.assertIn("advanced stick parameters: removed node", out)
        self.assertIn("advanced stick parameters.001: new node", out)

    def test_added_preset_group(self):
        old = tracking({"a": preset({"n": {"x": 1}})})
        new = tracking({"a": preset({"n": {"x": 1}}), "GripV new part": preset({"p": {"x": 1, "y": 2}})})
        out = text(old, new)
        self.assertIn("1 preset group added.", out)
        self.assertIn("  GripV new part: new preset group, 1 node, 2 values", out)

    def test_shared_group_is_shown_once(self):
        old = tracking(global_group(), global_group())
        new = tracking(global_group(variant="GripX"), global_group(variant="GripX"))
        out = text(old, new)
        self.assertEqual(out.count("variant:"), 1)
        self.assertIn("GripV and GripX, same change in both panels\n  global\n    global parameters\n"
                      '      variant: "GripV" -> "GripX"  (working setting, the export presets set their own)',
                      out)
        self.assertNotIn("panel GripV controls", out)

    def test_different_changes_stay_per_panel(self):
        old = tracking(global_group(), global_group())
        new = tracking(global_group(screws=False), global_group())
        out = text(old, new)
        self.assertIn("GripV (custom ergonomic shape), panel GripV controls\n  global", out)
        self.assertNotIn("GripX", out.split("\n", 1)[1])

    def test_unknown_panel_and_modifiers(self):
        old = {"tracked_inputs": {"GripR1 controls": {"g": preset({"n": {"a": 1}})}},
               "modifiers": {"case": {"GeometryNodes": {"inputs": {"Socket_2": 1.0}}}}}
        new = {"tracked_inputs": {"GripR1 controls": {"g": preset({"n": {"a": 2}})}},
               "modifiers": {"case": {"GeometryNodes": {"inputs": {"Socket_2": 3.0}},
                                      "Smooth": {"inputs": {"Factor": 0.5}}}}}
        out = text(old, new)
        self.assertIn("2 values changed, 1 modifier added.", out)
        self.assertIn("\nGripR1 controls\n  g\n    n\n      a: 1 -> 2 (+1)", out)
        self.assertIn("Modifier inputs\n  case\n    GeometryNodes\n      Socket_2: 1 -> 3 (+2)\n"
                      "    Smooth: new modifier, 1 input", out)
        md = markdown(old, new)
        self.assertIn("#### GripR1 controls\n\n**`g`**", md)
        self.assertIn("| `Smooth` |  |  |  | new modifier, 1 input |", md)


class MeshAndTreeTests(unittest.TestCase):
    def test_mesh_hashes(self):
        old = tracking(meshes={"basemesh GripV": "aaa", "basemesh GripS": "bbb"})
        new = tracking(meshes={"basemesh GripV": "ccc", "basemesh_X_style": "ddd"})
        out = text(old, new)
        self.assertIn("No parameter changes, 3 meshes changed.", out)
        self.assertIn("  basemesh GripS was removed (old GripS shape)", out)
        self.assertIn("  basemesh GripV was edited (GripV shape)", out)
        self.assertIn("  basemesh_X_style was added (GripX xbox shape)", out)

    def test_links_added_and_removed(self):
        old = tracking(trees={"stick": ["[A] Bundle -> Bundle [Join]", "[B] Bundle -> Bundle [Join]",
                                        "[Join] Bundle -> Bundle [Group Output]"],
                              "capacitive": ["[Group Input] capacitive -> Menu [Menu Switch]"]})
        new = tracking(trees={"stick": ["[A] Bundle -> Bundle [Join]", "[Join] Bundle -> Input [Menu Switch]",
                                        "[Menu Switch] Output -> Bundle [Group Output]"],
                              "new group": []})
        out = text(old, new)
        self.assertIn("wiring changed in 3 node groups.", out)
        self.assertIn("  Node groups added: new group (0 links)", out)
        self.assertIn("  Node groups removed: capacitive (1 link)", out)
        self.assertIn("  stick: 2 links added, 2 removed\n      now linked: Menu Switch\n"
                      "      no longer linked: B", out)
        self.assertNotIn("[Menu Switch] Output", out)
        verbose = text(old, new, verbose=True)
        self.assertIn("added [Menu Switch] Output -> Bundle [Group Output]", verbose)
        self.assertIn("removed [B] Bundle -> Bundle [Join]", verbose)

    def test_relabels_and_mutes_are_not_rewiring(self):
        old = tracking(trees={"labels": ["[screw parameters] Bundle -> Bundle [Join Bundle]"],
                              "mute": ["[A] x -> y [B]", "[C] x -> y [B]"]})
        new = tracking(trees={"labels": ["[screw parameters (FRONT)] Bundle -> Bundle [Join Bundle]"],
                              "mute": ["[A] x -> y [B] (muted)", "[C] x -> y [B]"]})
        out = text(old, new)
        self.assertIn("  mute: 1 link muted", out)
        self.assertIn("  Only node labels changed in 1 node group: labels", out)
        verbose = text(old, new, verbose=True)
        self.assertIn("relabeled screw parameters -> screw parameters (FRONT)", verbose)

    def test_relabel_with_rewiring(self):
        old = tracking(trees={"t": ["[Reroute.002 (connect here)] Output -> Input [Reroute]"]})
        new = tracking(trees={"t": ["[Join Bundle] Bundle -> Input [Reroute.002]"]})
        out = text(old, new)
        self.assertIn("  t: 1 link added, 1 removed, 1 node relabeled\n      now linked: Join Bundle\n"
                      "      no longer linked: Reroute", out)

    def test_format_version_change(self):
        out = text(tracking(version=2), tracking(version=3))
        self.assertIn("No parameter changes.\nFormat version 2 -> 3", out)


class MarkdownTests(unittest.TestCase):
    def test_tables_and_wiring(self):
        old = tracking({"GripV abxy": preset({"caps parameters": {"cap bevel": 2.3, "a|b": "x"}})},
                       trees={"t": ["[A] x -> y [B]"]}, meshes={"basemesh_D_style": "1"})
        new = tracking({"GripV abxy": preset({"caps parameters": {"cap bevel": 2.5, "a|b": "y"}})},
                       trees={"t": ["[A] x -> z [B]"]}, meshes={"basemesh_D_style": "2"})
        out = markdown(old, new)
        self.assertTrue(out.startswith("### Parameter changes: `old` → `new`\n\n2 values changed"))
        self.assertIn("#### GripV (custom ergonomic shape)\n\nPanel `GripV controls`.", out)
        self.assertIn("**`GripV abxy`**\n\n| Node | Input | Before | After | Change |", out)
        self.assertIn("| `caps parameters` | `cap bevel` | `2.3` | `2.5` | +0.2 |", out)
        self.assertIn("| `caps parameters` | `a\\|b` | `\"x\"` | `\"y\"` |  |", out)
        self.assertIn("- `basemesh_D_style` was edited (GripX dualsense shape)", out)
        self.assertIn("<details>\n<summary>Node wiring: 1 node group changed</summary>\n\n"
                      "- `t`: 1 link added, 1 removed\n\n</details>", out)

    def test_shared_section_and_hint(self):
        old = tracking(global_group(), global_group())
        new = tracking(global_group(variant="GripX"), global_group(variant="GripX"))
        out = markdown(old, new)
        self.assertIn("#### GripV and GripX\n\nSame change in both panels.", out)
        self.assertIn("| `global parameters` | `variant` | `\"GripV\"` | `\"GripX\"` | "
                      "working setting, the export presets set their own |", out)

    def test_node_rows(self):
        old = tracking({"g": preset({"gone": {"a": 1}}, {"Index": 0})})
        new = tracking({"g": preset({"new": {"b": 2}}, {"Index": 1})})
        out = markdown(old, new, verbose=True)
        self.assertIn("| *(preset group)* | `Index` | `0` | `1` | +1 |", out)
        self.assertIn("| `gone` |  |  |  | removed node, 1 input |", out)
        self.assertIn("| `gone` | `a` | `1` |  |  |", out)
        self.assertIn("| `new` | `b` |  | `2` |  |", out)


GIT = shutil.which("git")


@unittest.skipUnless(GIT, "git is not installed")
class GitTests(unittest.TestCase):
    """A throwaway repository with a few versions of blender/tracking.json."""

    def git(self, *args):
        return subprocess.run(["git", "-c", "user.name=Tester", "-c", "user.email=t@example.com",
                               "-c", "commit.gpgsign=false"] + list(args),
                              cwd=self.repo, check=True, capture_output=True, text=True).stdout.strip()

    def commit(self, data, message):
        if data is not None:
            with open(self.file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, sort_keys=True)
        else:
            with open(os.path.join(self.repo, "notes.txt"), "a") as f:
                f.write(message + "\n")
        self.git("add", "-A")
        self.git("commit", "-q", "-m", message)
        return self.git("rev-parse", "--short", "HEAD")

    def setUp(self):
        self.repo = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.repo, ignore_errors=True)
        self.file = os.path.join(self.repo, "blender", "tracking.json")
        os.makedirs(os.path.dirname(self.file))
        self.git("init", "-q")
        self.v1 = tracking(global_group(), global_group())
        self.v2 = tracking(global_group(variant="GripX"), global_group(variant="GripX"))
        self.v3 = tracking(global_group(variant="GripX"), global_group(variant="GripX"),
                           meshes={"basemesh GripV": "2"})
        self.c1 = self.commit(self.v1, "presets saved")
        self.c2 = self.commit(None, "unrelated change")
        self.c3 = self.commit(self.v2, "sticks upd")
        self.c4 = self.commit(self.v3, "basemesh tweak")
        cwd = os.getcwd()
        os.chdir(self.repo)
        self.addCleanup(os.chdir, cwd)

    def run_main(self, *args):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = td.main(list(args))
        return code, out.getvalue(), err.getvalue()

    def test_default_is_the_last_commit(self):
        code, out, _ = self.run_main()
        self.assertEqual(code, 0)
        self.assertTrue(out.startswith(f"tracking.json: HEAD^ ({self.c3}) -> HEAD ({self.c4})\n"))
        self.assertIn("basemesh GripV was added", out)
        self.assertNotIn("variant", out)

    def test_single_ref_is_that_commits_change(self):
        code, out, _ = self.run_main(self.c3)
        self.assertEqual(code, 0)
        self.assertTrue(out.startswith(f"tracking.json: {self.c2} -> {self.c3}\n1 value changed."))
        self.assertIn('variant: "GripV" -> "GripX"', out)

    def test_ranges(self):
        _, out, _ = self.run_main(f"{self.c1}..{self.c4}")
        self.assertIn("1 value changed, 1 mesh changed.", out)
        _, two, _ = self.run_main(self.c1, self.c4)
        self.assertEqual(out, two)
        _, dots3, _ = self.run_main(f"{self.c1}...HEAD")
        self.assertIn(f"tracking.json: merge base {self.c1} -> HEAD", dots3)

    def test_commit_without_tracking_change_points_to_the_last_one(self):
        _, out, _ = self.run_main(self.c2)
        self.assertIn("No changes in tracking.json.\n\nThe last commit that changed it: "
                      f"{self.c1} presets saved\n", out)

    def test_windows_style_path_option(self):
        _, out, _ = self.run_main("--path", "blender\\tracking.json", self.c3)
        self.assertIn('variant: "GripV" -> "GripX"', out)

    def test_first_version(self):
        _, out, _ = self.run_main(self.c1)
        self.assertIn("First recorded version of tracking.json (GripV: 1 preset group, 3 values;", out)

    def test_working_file_against_head(self):
        with open(self.file, "w", encoding="utf-8") as f:
            json.dump(tracking(global_group(variant="GripX", screws=False), global_group(variant="GripX", screws=False),
                               meshes={"basemesh GripV": "2"}), f)
        _, out, _ = self.run_main(os.path.join("blender", "tracking.json"))
        self.assertIn("screws: on -> off", out)

    def test_two_files(self):
        a, b = os.path.join(self.repo, "a.json"), os.path.join(self.repo, "b.json")
        for path, data in ((a, self.v1), (b, self.v2)):
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f)
        _, out, _ = self.run_main(a, b)
        self.assertTrue(out.startswith(f"tracking.json: {a} -> {b}\n1 value changed."))

    def test_log(self):
        code, out, _ = self.run_main("--log", "0")
        self.assertEqual(code, 0)
        self.assertEqual([line.split()[1] for line in out.splitlines() if line.startswith("commit ")],
                         [self.c4, self.c3, self.c1])
        self.assertIn(f"commit {self.c3}  ", out)
        self.assertIn("    sticks upd\n\n    1 value changed.", out)
        self.assertNotIn("unrelated change", out)
        _, two, _ = self.run_main("--log", "2")
        self.assertNotIn(f"commit {self.c1}", two)
        _, md, _ = self.run_main("--log", "1", "--markdown")
        self.assertTrue(md.startswith(f"### `{self.c4}` basemesh tweak\n\nTester, "))
        self.assertIn(f"compared with `{self.c3}`", md)
        _, ranged, _ = self.run_main("--log", "0", f"{self.c3}..HEAD")
        self.assertIn(f"commit {self.c4}", ranged)
        self.assertNotIn(f"commit {self.c3}", ranged)

    def test_errors(self):
        code, out, err = self.run_main("no-such-ref")
        self.assertEqual((code, out), (1, ""))
        self.assertIn("unknown revision 'no-such-ref'", err)
        pointer = os.path.join(self.repo, "pointer.json")
        with open(pointer, "w") as f:
            f.write("version https://git-lfs.github.com/spec/v1\noid sha256:00\nsize 1\n")
        code, _, err = self.run_main(pointer)
        self.assertEqual(code, 1)
        self.assertIn("is a Git LFS pointer", err)


if __name__ == "__main__":
    unittest.main()
