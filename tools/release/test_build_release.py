"""Tests for build_release.py. Run: python -m unittest discover tools/release

The tests build a small repository in a temporary folder: a print sets file,
a LICENSE and an orca_slicer/ tree made of fake Git LFS pointer files (or of
small real files where the test needs real models)."""

import copy
import hashlib
import io
import json
import os
import shutil
import subprocess
import tempfile
import unittest
import zipfile
from contextlib import redirect_stdout, redirect_stderr

import build_release as br

SETS = {
    "root": "orca_slicer",
    "repo_url": "https://example.invalid/Grip",
    "license": "LICENSE",
    "license_name": "Test License 1.0",
    "credits": "Tester",
    "guides": [
        {"title": "Guide", "path": "docs/guide.md"},
        {"title": "Report", "url": "https://example.invalid/report"},
    ],
    "tolerance_levels": ["tight", "default", "loose"],
    "default_tolerance": "default",
    "tolerance_placeholders": {"tolerance": "tolerance", "cap": "cap tolerance", "press": "press tolerance"},
    "flat_folders": {"tolerance": "", "cap": "cap", "press": ""},
    "groups": {
        "case": {"title": "Case", "items": [
            {"name": "Bottom", "file": "{case}/case_bottom.stl", "qty": 1},
            {"name": "Top", "qty": 1, "files": ["{case}/case_top_knob.stl", "{case}/case_top_plate.stl"]},
        ]},
        "buttons": {"title": "Buttons", "note": "Caps go with their shaft.", "items": [
            {"name": "Shaft", "file": "parts/buttons/{tolerance}/button.stl", "qty": 4},
            {"name": "Cross cap", "file": "parts/buttons/{tolerance}/cap_{cap}/cross.stl", "qty": 1,
             "unconfirmed": "one per symbol, probably"},
            {"name": "Select shafts", "qty": 4, "missing": "no preset exports them."},
        ]},
        "triggers": {"title": "Triggers", "items": [
            {"name": "R2", "file": "{style}/triggers/{tolerance}/press_{press}/R2.stl", "qty": 1},
        ]},
        "sticks": {"title": "Sticks", "when": "with a stick top", "items": [
            {"name": "Stick", "qty": 2, "file": "parts/sticks/{top}/stick_{range}_deg.stl",
             "choose": {"top": ["circle", "square"], "range": ["10", "12"]}},
        ]},
    },
    "shapes": [
        {"id": "V-standard", "title": "V standard", "folder": "V", "about": "The test shape.",
         "vars": {"case": "case_standard", "style": "parts"},
         "groups": ["case", "buttons", "triggers", "sticks"],
         "projects": ["V_parts.3mf"], "hardware": "Four screws."},
        {"id": "V-hollow", "title": "V hollow", "folder": "V",
         "vars": {"case": "case_hollow", "style": "parts"},
         "groups": ["case", "buttons"]},
    ],
}

DEFAULT_FILES = [
    "case_standard/case_bottom.stl",
    "case_standard/case_top_knob.stl",
    "case_standard/case_top_plate.stl",
    "parts/buttons/default/button.stl",
    "parts/buttons/default/cap_default/cross.stl",
    "parts/triggers/default/press_default/R2.stl",
    "parts/sticks/circle/stick_10_deg.stl",
    "parts/sticks/circle/stick_12_deg.stl",
    "parts/sticks/square/stick_10_deg.stl",
    "parts/sticks/square/stick_12_deg.stl",
    "V_parts.3mf",
]

# DEFAULT_FILES as a plain build lays them out: without tolerance folders.
FLAT_FILES = [
    "case_standard/case_bottom.stl",
    "case_standard/case_top_knob.stl",
    "case_standard/case_top_plate.stl",
    "parts/buttons/button.stl",
    "parts/buttons/cap/cross.stl",
    "parts/triggers/R2.stl",
    "parts/sticks/circle/stick_10_deg.stl",
    "parts/sticks/circle/stick_12_deg.stl",
    "parts/sticks/square/stick_10_deg.stl",
    "parts/sticks/square/stick_12_deg.stl",
    "V_parts.3mf",
]


def pointer(content):
    """Git LFS pointer text for content."""
    return ("version https://git-lfs.github.com/spec/v1\noid sha256:%s\nsize %d\n"
            % (hashlib.sha256(content).hexdigest(), len(content))).encode()


class Fixture(unittest.TestCase):
    """A temporary repository with every file the fixture print sets need."""

    real = False

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="grip_release_test_")
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.sets = copy.deepcopy(SETS)
        self.sets_path = os.path.join(self.tmp, "print_sets.json")
        self.write_sets()
        self.root = os.path.join(self.tmp, "orca_slicer")
        self.write(os.path.join(self.tmp, "LICENSE"), b"Test License 1.0\n\nText.\n")
        self.write(os.path.join(self.tmp, "docs", "guide.md"), b"# Guide\n")
        for shape in self.sets["shapes"]:
            for rel in br.shape_files(self.sets, shape, br.ALL) + shape.get("projects", []):
                self.put(shape["folder"] + "/" + rel)

    def write_sets(self):
        with open(self.sets_path, "w", encoding="utf-8") as f:
            json.dump(self.sets, f)

    def write(self, path, data):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as f:
            f.write(data)

    def put(self, rel, content=None, real=None):
        """Write a part under orca_slicer/: a pointer, or the real content."""
        content = content if content is not None else ("solid %s\nendsolid\n" % rel).encode()
        real = self.real if real is None else real
        self.write(br.native(self.root, rel), content if real else pointer(content))

    def check(self):
        sets = br.load_sets(self.sets_path)
        return br.check(self.tmp, sets)

    def run_main(self, *args):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = br.main(["--repo", self.tmp, "--sets", self.sets_path] + list(args))
        return code, out.getvalue() + err.getvalue()


class PrintSetTests(Fixture):

    def test_default_files_of_a_shape(self):
        shape = br.find_shape(self.sets, "v-standard")
        self.assertEqual(br.shape_files(self.sets, shape, "default"), DEFAULT_FILES)

    def test_all_tolerances_expand_every_placeholder(self):
        shape = br.find_shape(self.sets, "V-standard")
        files = br.shape_files(self.sets, shape, br.ALL)
        self.assertIn("parts/buttons/tight/cap_loose/cross.stl", files)
        self.assertIn("parts/triggers/loose/press_tight/R2.stl", files)
        self.assertEqual(len([f for f in files if f.endswith("cross.stl")]), 9)
        self.assertNotIn("V_parts.3mf", files)  # projects only go with the default tolerance

    def test_flat_layout_leaves_out_the_tolerance_folders(self):
        shape = br.find_shape(self.sets, "V-standard")
        paths = br.layout(self.sets, shape, "default", flat=True)
        self.assertEqual(list(paths), DEFAULT_FILES)
        self.assertEqual(list(paths.values()), FLAT_FILES)
        self.assertEqual(br.layout(self.sets, shape, "tight", flat=True)["parts/buttons/tight/cap_tight/cross.stl"],
                         "parts/buttons/cap/cross.stl")
        self.assertEqual(br.layout(self.sets, shape, "default"), {rel: rel for rel in DEFAULT_FILES})

    def test_flat_template_keeps_other_folders_and_the_file_name(self):
        for template, flat in (
                ("parts/buttons/{tolerance}/cap_{cap}/cross.stl", "parts/buttons/cap/cross.stl"),
                ("{tolerance}/press_{press}/R2.stl", "R2.stl"),
                ("parts/{top}_{tolerance}/a.stl", "parts/{top}_{tolerance}/a.stl"),
                ("parts/a_{press}.stl", "parts/a_{press}.stl")):
            self.assertEqual(br.flat_template(self.sets, template), flat)

    def test_shape_variables_are_filled_in(self):
        shape = br.find_shape(self.sets, "V-hollow")
        group, items = br.resolve(self.sets, shape)[0]
        self.assertEqual(items[1]["files"], ["case_hollow/case_top_knob.stl", "case_hollow/case_top_plate.stl"])
        self.assertEqual(SETS["groups"]["case"]["items"][0]["file"], "{case}/case_bottom.stl")

    def test_invalid_sets_are_rejected_with_every_problem(self):
        bad = copy.deepcopy(SETS)
        bad["shapes"][0]["groups"].append("nope")
        items = bad["groups"]["buttons"]["items"]
        items.append({"name": "Zero", "file": "a.stl", "qty": 0})
        items.append({"name": "Both", "file": "a.stl", "missing": "x", "qty": 1})
        items.append({"name": "Odd", "file": "parts/{colour}/a.stl", "qty": 1})
        items.append({"name": "Spaced", "file": "parts/a b.stl", "qty": 1})
        items.append({"name": "Chosen", "files": ["a.stl"], "choose": {"x": ["1"]}, "qty": 1})
        bad["flat_folders"] = {"colour": "", "cap": "a b"}
        with self.assertRaises(br.SetError) as cm:
            br.validate(bad)
        text = str(cm.exception)
        for words in ("unknown group 'nope'", "'Zero': qty", "'Both': needs exactly one",
                      "unknown placeholder colour", "space in path", "choose only works with file",
                      "flat_folders: 'colour' is not a tolerance placeholder", "flat_folders: 'cap' must be"):
            self.assertIn(words, text)

    def test_invalid_sets_stop_the_command_line(self):
        self.sets["default_tolerance"] = "medium"
        self.write_sets()
        code, out = self.run_main("--check")
        self.assertEqual(code, br.EXIT_ERROR)
        self.assertIn("default_tolerance 'medium'", out)

    def test_real_print_sets(self):
        """The repository's print_sets.json is valid and, when the parts are
        present, --check finds every file and no name problems."""
        sets = br.load_sets(br.DEFAULT_SETS)
        if not os.path.isdir(os.path.join(br.DEFAULT_REPO, sets["root"])):
            self.skipTest("no orca_slicer/ next to this tool")
        code, text = br.check(br.DEFAULT_REPO, sets)
        self.assertEqual(code, br.EXIT_OK, text)


class CheckTests(Fixture):

    def test_complete_pointer_tree_passes(self):
        code, text = self.check()
        self.assertEqual(code, br.EXIT_OK, text)
        self.assertIn("2 shapes need 32 files at all tolerances: all found.", text)
        self.assertIn("32 pointer files, 0 real files.", text)
        self.assertIn("Result: 0 errors, 1 warning.", text)  # the Select shafts
        self.assertIn("4 x Select shafts (Buttons): V standard, V hollow", text)

    def test_missing_file_fails(self):
        os.remove(br.native(self.root, "V/parts/buttons/loose/cap_tight/cross.stl"))
        code, text = self.check()
        self.assertEqual(code, br.EXIT_ERROR)
        self.assertIn("ERROR    missing V/parts/buttons/loose/cap_tight/cross.stl (V standard, V hollow)", text)

    def test_missing_project_and_license_fail(self):
        os.remove(br.native(self.root, "V/V_parts.3mf"))
        os.remove(os.path.join(self.tmp, "LICENSE"))
        code, text = self.check()
        self.assertEqual(code, br.EXIT_ERROR)
        self.assertIn("missing V/V_parts.3mf", text)
        self.assertIn("missing LICENSE", text)

    def test_space_in_a_name_fails(self):
        self.put("V/parts/extra parts/pin.stl")
        code, text = self.check()
        self.assertEqual(code, br.EXIT_ERROR)
        self.assertIn("space in name: V/parts/extra parts", text)

    def test_windows_characters_fail(self):
        self.put("V/parts/a?b.stl")
        code, text = self.check()
        self.assertEqual(code, br.EXIT_ERROR)
        self.assertIn("name not allowed on Windows: V/parts/a?b.stl", text)

    def test_names_that_differ_only_by_case_fail(self):
        self.put("V/Parts/pin.stl")
        if os.path.isfile(br.native(self.root, "V/parts/pin.stl")):
            self.skipTest("this file system ignores case")
        code, text = self.check()
        self.assertEqual(code, br.EXIT_ERROR)
        self.assertIn("names differ only by case: V/Parts, V/parts", text)

    def test_wrong_case_in_the_print_sets_fails(self):
        # A case-blind disk (Windows, macOS) would find the file, a Linux clone would not.
        os.remove(br.native(self.root, "V/parts/buttons/default/button.stl"))
        self.put("V/parts/buttons/default/Button.stl")
        code, text = self.check()
        self.assertEqual(code, br.EXIT_ERROR)
        self.assertIn("case differs: the print sets name V/parts/buttons/default/button.stl, "
                      "the file is V/parts/buttons/default/Button.stl", text)

    def test_names_that_differ_only_by_case_in_git_fail(self):
        # The disk holds one spelling, git's file list both: what a Windows clone sees.
        if not shutil.which("git"):
            self.skipTest("git not found")
        git = ["git", "-C", self.tmp, "-c", "core.autocrlf=false"]
        subprocess.run(git + ["init", "-q"], check=True)
        subprocess.run(git + ["add", "orca_slicer"], check=True)
        blob = subprocess.run(git + ["hash-object", "-w", "LICENSE"], check=True,
                              capture_output=True, text=True).stdout.strip()
        subprocess.run(git + ["update-index", "--add", "--cacheinfo",
                              "100644,%s,orca_slicer/V/Parts/pin.stl" % blob], check=True)
        code, text = self.check()
        self.assertEqual(code, br.EXIT_ERROR)
        self.assertIn("names differ only by case: V/Parts, V/parts", text)

    def test_unusual_characters_only_warn(self):
        self.put("V/parts/sticks/stick_(60%).stl")
        code, text = self.check()
        self.assertEqual(code, br.EXIT_OK, text)
        self.assertIn("unusual characters % ( )", text)

    def test_identical_tolerance_variants_warn(self):
        same = b"the same cap"
        for level in ("tight", "default", "loose"):
            self.put("V/parts/buttons/default/cap_%s/cross.stl" % level, same)
        self.put("V/parts/triggers/default/press_tight/R2.stl", b"trigger")
        self.put("V/parts/triggers/loose/press_tight/R2.stl", b"trigger")
        code, text = self.check()
        self.assertEqual(code, br.EXIT_OK, text)
        self.assertIn("V/parts/buttons/*/<cap tolerance>/: cap_tight = cap_default = cap_loose (1 of 3 files)", text)
        self.assertIn("V/parts/triggers/<tolerance>/press_*/: default = loose (1 of 3 files)", text)

    def test_tolerance_folder_at_the_top(self):
        digests = {"tight/a.stl": "1", "default/a.stl": "1", "loose/a.stl": "2"}
        self.assertEqual(br.identical_siblings(self.sets, digests),
                         [("<tolerance>/", "tight = default", ["*/a.stl"], 1)])

    def test_listing_identical_files(self):
        self.put("V/parts/buttons/tight/button.stl", b"shaft")
        self.put("V/parts/buttons/default/button.stl", b"shaft")
        sets = br.load_sets(self.sets_path)
        _, text = br.check(self.tmp, sets, verbose=True)
        self.assertIn("V/parts/buttons/<tolerance>/: tight = default (1 of 1 files)", text)
        self.assertIn("V/parts/buttons/*/button.stl", text)

    def test_identical_choices_warn(self):
        self.put("V/case_standard/case_top_knob.stl", b"plate")
        self.put("V/case_standard/case_top_plate.stl", b"plate")
        code, text = self.check()
        self.assertEqual(code, br.EXIT_OK, text)
        self.assertIn("V/case_standard/case_top_knob.stl = V/case_standard/case_top_plate.stl (Top; V standard)",
                      text)

    def test_pointer_and_real_file_with_the_same_content_match(self):
        self.put("V/parts/buttons/tight/button.stl", b"shaft", real=True)
        self.put("V/parts/buttons/loose/button.stl", b"shaft", real=False)
        code, text = self.check()
        self.assertIn("V/parts/buttons/<tolerance>/: tight = loose (1 of 1 files)", text)
        self.assertIn("31 pointer files, 1 real files.", text)

    def test_files_no_set_uses_are_listed(self):
        self.put("V/parts/misc/nut_lock.stl")
        self.write(br.native(self.root, "README.md"), b"# Parts\n")
        code, text = self.check()
        self.assertEqual(code, br.EXIT_OK, text)
        unused = text.split("Files no print set uses")[1].split("Git LFS")[0]
        self.assertIn("V/parts/misc/nut_lock.stl", unused)
        self.assertNotIn("README.md", unused)

    def test_check_from_the_command_line(self):
        code, out = self.run_main("--check")
        self.assertEqual(code, br.EXIT_OK)
        self.assertIn("Result: 0 errors", out)
        os.remove(br.native(self.root, "V/case_hollow/case_bottom.stl"))
        code, out = self.run_main("--check")
        self.assertEqual(code, br.EXIT_ERROR)


class PresetTests(Fixture):
    """The JSON files combi_export saves next to the .blend file list what the
    presets export; --check and the build compare the print sets with them."""

    def setUp(self):
        super().setUp()
        self.sets["presets"] = ["blender/V_preset.json"]
        self.write_sets()
        shapes = self.sets["shapes"]
        self.exported = sorted(set(rel for shape in shapes for rel in br.shape_files(self.sets, shape, br.ALL)))
        self.write_presets(self.exported)

    def write_presets(self, files, root_dir="D:\\Grip\\orca_slicer\\V\\", complete=True, exports=True):
        data = {"data_version": 4, "root_dir": root_dir, "global_nodegroups": [], "presets": []}
        if exports:
            data["exports"] = {"complete": complete, "presets": [
                {"name": "Parts", "files": [f for f in files if f.startswith("parts/")]},
                {"name": "Cases", "files": [f for f in files if not f.startswith("parts/")]}]}
        self.write(os.path.join(self.tmp, "blender", "V_preset.json"), json.dumps(data, indent=4).encode())

    def test_root_folder_names_the_shape_folder(self):
        for root_dir, folder in (("D:\\Grip\\orca_slicer\\V\\", "V"), ("//../orca_slicer/V/", "V"),
                                 ("/home/me/Grip/Orca_Slicer/v", "V"), ("D:\\Grip\\orca_slicer\\", None),
                                 ("D:\\Grip\\other\\V\\", None), ("", None)):
            self.assertEqual(br.preset_folder(self.sets, root_dir), folder, root_dir)

    def test_presets_that_export_every_file_pass(self):
        code, text = self.check()
        self.assertEqual(code, br.EXIT_OK, text)
        self.assertIn("blender/V_preset.json: 2 presets export 31 files to orca_slicer/V/.", text)
        self.assertIn("Result: 0 errors, 1 warning.", text)  # the Select shafts, as without presets

    def test_a_file_no_preset_exports_warns(self):
        self.write_presets([f for f in self.exported if f != "parts/buttons/tight/button.stl"])
        code, text = self.check()
        self.assertEqual(code, br.EXIT_OK, text)
        self.assertIn("warning  V/parts/buttons/tight/button.stl: no preset exports it, so it may be older than "
                      "the .blend file (V standard, V hollow)", text)
        self.assertIn("Result: 0 errors, 2 warnings.", text)

    def test_exports_missing_from_disk_and_unused_files_are_listed(self):
        self.write_presets(self.exported + ["parts/buttons/huge/button.stl", "parts/misc/nut_lock.stl"])
        self.put("V/parts/misc/nut_lock.stl")
        self.put("V/parts/misc/old.stl")
        code, text = self.check()
        self.assertEqual(code, br.EXIT_OK, text)
        self.assertIn("1 file the presets export is not in orca_slicer/V/, and no print set needs it (-v lists it).", text)
        unused = text.split("Files no print set uses")[1].split("Git LFS")[0]
        self.assertIn("V/parts/misc/old.stl    (no preset exports it)", unused)
        self.assertIn("V/parts/misc/nut_lock.stl\n", unused)
        code, text = self.run_main("--check", "-v")
        self.assertIn("           V/parts/buttons/huge/button.stl", text)

    def test_files_without_a_list_are_not_compared(self):
        empty = []
        for kwargs, words in (({"exports": False}, "has no list of the exported files"),
                              ({"complete": False}, "lists only part of the exported files"),
                              ({"root_dir": "D:\\Grip\\exports\\"}, "is not a shape folder in orca_slicer/")):
            with self.subTest(words=words):
                self.write_presets(empty, **kwargs)
                code, text = self.check()
                self.assertEqual(code, br.EXIT_OK, text)
                self.assertIn(words, text)
                self.assertNotIn("no preset exports", text)
                self.assertIn("Result: 0 errors, 2 warnings.", text)
        os.remove(os.path.join(self.tmp, "blender", "V_preset.json"))
        code, text = self.check()
        self.assertIn("warning  missing blender/V_preset.json", text)
        self.write(os.path.join(self.tmp, "blender", "V_preset.json"), b"{not json")
        code, text = self.check()
        self.assertEqual(code, br.EXIT_ERROR)
        self.assertIn("ERROR    blender/V_preset.json is not valid JSON", text)

    def test_presets_must_be_a_list_of_paths(self):
        self.sets["presets"] = "blender/V_preset.json"
        with self.assertRaises(br.SetError) as cm:
            br.validate(self.sets)
        self.assertIn("presets must be a list of paths", str(cm.exception))

    def test_build_warns_about_files_no_preset_exports(self):
        self.real = True
        for shape in self.sets["shapes"]:
            for rel in br.shape_files(self.sets, shape, br.ALL) + shape.get("projects", []):
                self.put(shape["folder"] + "/" + rel)
        self.write_presets([f for f in self.exported if f != "parts/buttons/default/button.stl"])
        code, out = self.run_main("--out", os.path.join(self.tmp, "dist"), "--shape", "V-hollow")
        self.assertEqual(code, br.EXIT_OK, out)
        self.assertIn("warning: no preset exports parts/buttons/default/button.stl, so it may be older than the "
                      ".blend file", out)


class PrintListTests(Fixture):

    def test_default_print_list(self):
        shape = br.find_shape(self.sets, "V-standard")
        text = br.print_list(self.sets, shape, "default", "commit `abc1234`")
        self.assertTrue(text.startswith("# V standard: print list\n\nThe test shape.\n"))
        for line in (
                "Fit: `default` for `tolerance`, `cap tolerance` and `press tolerance`.",
                "Built from commit `abc1234`.",
                "> Not complete yet: 1 part is not exported (marked **not exported yet** below).",
                "- 1 x Bottom: `case_standard/case_bottom.stl`",
                "- 1 x Top, one of:\n  - `case_standard/case_top_knob.stl`\n  - `case_standard/case_top_plate.stl`",
                "Caps go with their shaft.",
                "- 4 x Shaft: `parts/buttons/default/button.stl`",
                "- 1 x Cross cap: `parts/buttons/default/cap_default/cross.stl`. Not confirmed: one per symbol",
                "- 4 x Select shafts: **not exported yet.** no preset exports them.",
                "- 1 x R2: `parts/triggers/default/press_default/R2.stl`",
                "## Sticks\n\nOnly with a stick top.\n\n- 2 x Stick: `parts/sticks/<top>/stick_<range>_deg.stl`, "
                "with top one of `circle`, `square`; range one of `10`, `12`.\n",
                "## OrcaSlicer projects\n\n- `V_parts.3mf`",
                "## Not printed\n\nFour screws.",
                "- [Guide](https://example.invalid/Grip/blob/main/docs/guide.md)",
                "- [Report](https://example.invalid/report)",
                "Licensed under Test License 1.0, see `LICENSE`. Credits: Tester.",
                "[tolerances](https://example.invalid/Grip/blob/main/orca_slicer/README.md#tolerances)"):
            self.assertIn(line, text)

    def test_flat_print_list(self):
        shape = br.find_shape(self.sets, "V-standard")
        text = br.print_list(self.sets, shape, "default", None, (), flat=True)
        for line in (
                "Every fit part here is the `default` one, so the paths leave out the tolerance folders that "
                "`orca_slicer/V/` in the repository has. For example `parts/buttons/default/` there is "
                "`parts/buttons/` here. If a part does not fit, reprint only that part from another tolerance "
                "(`tight` or `loose`) in the repository",
                "- 4 x Shaft: `parts/buttons/button.stl`",
                "- 1 x Cross cap: `parts/buttons/cap/cross.stl`.",
                "- 1 x R2: `parts/triggers/R2.stl`",
                "## OrcaSlicer projects\n\n- `V_parts.3mf`"):
            self.assertIn(line, text)
        self.assertNotIn("default/", text.split("## Case")[1])

    def test_all_tolerances_print_list(self):
        shape = br.find_shape(self.sets, "V-standard")
        text = br.print_list(self.sets, shape, br.ALL)
        self.assertIn("Every tolerance variant is included. Start with `default`", text)
        self.assertIn("`parts/buttons/<tolerance>/cap_<cap tolerance>/cross.stl`", text)
        self.assertIn("`parts/triggers/<tolerance>/press_<press tolerance>/R2.stl`", text)
        self.assertNotIn("OrcaSlicer projects", text)

    def test_identical_choices_are_noted(self):
        shape = br.find_shape(self.sets, "V-standard")
        text = br.print_list(self.sets, shape, "default", None,
                             [("Top", ["case_standard/case_top_knob.stl", "case_standard/case_top_plate.stl"])])
        self.assertIn("Top: `case_standard/case_top_knob.stl` and `case_standard/case_top_plate.stl` are the "
                      "same file in this release", text)

    def test_print_list_from_the_command_line(self):
        self.put("V/case_standard/case_top_knob.stl", b"plate")
        self.put("V/case_standard/case_top_plate.stl", b"plate")
        code, out = self.run_main("--print-list", "V-standard", "--tolerance", "tight")
        self.assertEqual(code, br.EXIT_OK)
        self.assertIn("`parts/buttons/button.stl`", out)
        self.assertIn("are the same file in this release", out)  # read from the pointers
        code, out = self.run_main("--print-list", "V-standard", "--tolerance", "tight", "--full-paths")
        self.assertIn("`parts/buttons/tight/button.stl`", out)
        code, out = self.run_main("--print-list", "W")
        self.assertEqual(code, br.EXIT_ERROR)
        self.assertIn("unknown shape 'W'", out)

    def test_unknown_tolerance(self):
        code, out = self.run_main("--tolerance", "medium")
        self.assertEqual(code, br.EXIT_ERROR)
        self.assertIn("unknown tolerance 'medium'", out)


class BuildTests(Fixture):

    real = True

    def build(self, *args):
        return self.run_main("--out", os.path.join(self.tmp, "dist"), *args)

    def folder_files(self, name):
        return br.scan(os.path.join(self.tmp, "dist", name))

    def test_build_refuses_pointer_files(self):
        self.put("V/parts/buttons/default/button.stl", real=False)
        code, out = self.build()
        self.assertEqual(code, br.EXIT_ERROR)
        self.assertIn("1 file is a Git LFS pointer, not the model: V/parts/buttons/default/button.stl", out)
        self.assertIn("git lfs pull", out)
        self.assertFalse(os.path.exists(os.path.join(self.tmp, "dist")))

    def test_build_refuses_missing_files(self):
        os.remove(br.native(self.root, "V/case_hollow/case_top_plate.stl"))
        code, out = self.build("--shape", "V-hollow")
        self.assertEqual(code, br.EXIT_ERROR)
        self.assertIn("missing V/case_hollow/case_top_plate.stl", out)

    def test_build_refuses_a_file_spelt_with_another_case(self):
        os.remove(br.native(self.root, "V/case_hollow/case_top_plate.stl"))
        self.put("V/case_hollow/Case_top_plate.stl")
        code, out = self.build("--shape", "V-hollow")
        self.assertEqual(code, br.EXIT_ERROR)
        self.assertIn("missing V/case_hollow/case_top_plate.stl", out)

    def test_default_build(self):
        code, out = self.build()
        self.assertEqual(code, br.EXIT_OK, out)
        self.assertEqual(self.folder_files("V-standard"), sorted(FLAT_FILES + ["LICENSE", "PRINT_LIST.md"]))
        dist = os.path.join(self.tmp, "dist")
        with zipfile.ZipFile(os.path.join(dist, "V-standard.zip")) as z:
            self.assertEqual(sorted(z.namelist()),
                             sorted("V-standard/" + f for f in FLAT_FILES + ["LICENSE", "PRINT_LIST.md"]))
            self.assertEqual(z.read("V-standard/case_standard/case_bottom.stl"),
                             b"solid V/case_standard/case_bottom.stl\nendsolid\n")
            self.assertEqual(z.read("V-standard/parts/buttons/cap/cross.stl"),
                             b"solid V/parts/buttons/default/cap_default/cross.stl\nendsolid\n")
            listing = z.read("V-standard/PRINT_LIST.md").decode()
        self.assertIn("Fit: `default`", listing)
        self.assertIn("`parts/buttons/cap/cross.stl`", listing)
        self.assertIn("V_parts.3mf", self.folder_files("V-standard"))
        self.assertNotIn("V_parts.3mf", self.folder_files("V-hollow"))
        with open(os.path.join(dist, "SHA256SUMS.txt")) as f:
            sums = f.read().splitlines()
        self.assertEqual([line.split("  ")[1] for line in sums], ["V-hollow.zip", "V-standard.zip"])
        self.assertIn("not exported yet: Select shafts", out)

    def test_full_paths_build(self):
        code, out = self.build("--full-paths")
        self.assertEqual(code, br.EXIT_OK, out)
        self.assertEqual(self.folder_files("V-standard-default"),
                         sorted(DEFAULT_FILES + ["LICENSE", "PRINT_LIST.md"]))
        with open(os.path.join(self.tmp, "dist", "V-standard-default", "PRINT_LIST.md"), encoding="utf-8") as f:
            self.assertIn("`parts/buttons/default/cap_default/cross.stl`", f.read())

    def test_files_that_would_land_on_one_path(self):
        self.sets["groups"]["buttons"]["items"].append(
            {"name": "Old shaft", "file": "parts/buttons/button.stl", "qty": 1})
        self.write_sets()
        self.put("V/parts/buttons/button.stl")
        code, out = self.build("--shape", "V-hollow")
        self.assertEqual(code, br.EXIT_ERROR)
        self.assertIn("V-hollow: parts/buttons/default/button.stl and parts/buttons/button.stl land on the "
                      "same path parts/buttons/button.stl", out)
        self.assertFalse(os.path.exists(os.path.join(self.tmp, "dist")))
        code, out = self.build("--shape", "V-hollow", "--full-paths")
        self.assertEqual(code, br.EXIT_OK, out)
        code, text = self.check()
        self.assertEqual(code, br.EXIT_ERROR)
        self.assertIn("V/parts/buttons/default/button.stl and V/parts/buttons/button.stl land on the same path "
                      "parts/buttons/button.stl in the V hollow release", text)

    def test_output_inside_the_repository_ignores_itself(self):
        code, _ = self.build("--shape", "V-hollow")
        self.assertEqual(code, br.EXIT_OK)
        with open(os.path.join(self.tmp, "dist", ".gitignore")) as f:
            self.assertIn("*", f.read().splitlines())

    def test_build_is_reproducible(self):
        zip_path = os.path.join(self.tmp, "dist", "V-hollow.zip")
        self.build("--shape", "V-hollow")
        with open(zip_path, "rb") as f:
            first = f.read()
        self.build("--shape", "V-hollow")
        with open(zip_path, "rb") as f:
            self.assertEqual(f.read(), first)

    def test_tight_build(self):
        code, out = self.build("--shape", "V-standard", "--tolerance", "tight", "--tag", "v0.1")
        self.assertEqual(code, br.EXIT_OK, out)
        files = self.folder_files("V-standard-v0.1-tight")
        self.assertIn("parts/buttons/cap/cross.stl", files)
        self.assertIn("parts/triggers/R2.stl", files)
        self.assertFalse(any("tight" in f or "default" in f for f in files))
        self.assertNotIn("V_parts.3mf", files)
        with zipfile.ZipFile(os.path.join(self.tmp, "dist", "V-standard-v0.1-tight.zip")) as z:
            self.assertEqual(z.read("V-standard-v0.1-tight/parts/triggers/R2.stl"),
                             b"solid V/parts/triggers/tight/press_tight/R2.stl\nendsolid\n")
        self.assertTrue(os.path.isfile(os.path.join(self.tmp, "dist", "V-standard-v0.1-tight.zip")))

    def test_all_tolerances_build(self):
        code, out = self.build("--shape", "V-standard", "--all-tolerances", "--no-zip")
        self.assertEqual(code, br.EXIT_OK, out)
        files = self.folder_files("V-standard-all-tolerances")
        self.assertEqual(len([f for f in files if f.endswith("cross.stl")]), 9)
        self.assertEqual(len([f for f in files if f.endswith("R2.stl")]), 9)
        self.assertFalse(os.path.exists(os.path.join(self.tmp, "dist", "V-standard-all-tolerances.zip")))

    def test_rebuild_replaces_the_earlier_build(self):
        self.build("--shape", "V-hollow")
        stale = os.path.join(self.tmp, "dist", "V-hollow", "old.stl")
        self.write(stale, b"old")
        code, _ = self.build("--shape", "V-hollow", "--no-zip")
        self.assertEqual(code, br.EXIT_OK)
        self.assertFalse(os.path.exists(stale))
        self.assertFalse(os.path.exists(os.path.join(self.tmp, "dist", "V-hollow.zip")))

    def test_build_leaves_other_folders_alone(self):
        foreign = os.path.join(self.tmp, "dist", "V-hollow", "mine.txt")
        self.write(foreign, b"keep me")
        code, out = self.build("--shape", "V-hollow")
        self.assertEqual(code, br.EXIT_ERROR)
        self.assertIn("was not made by this script", out)
        self.assertTrue(os.path.isfile(foreign))

    def test_identical_choices_are_reported_in_the_build(self):
        self.put("V/case_hollow/case_top_knob.stl", b"plate")
        self.put("V/case_hollow/case_top_plate.stl", b"plate")
        code, out = self.build("--shape", "V-hollow")
        self.assertEqual(code, br.EXIT_OK, out)
        self.assertIn("warning: Top: case_hollow/case_top_knob.stl = case_hollow/case_top_plate.stl", out)
        with open(os.path.join(self.tmp, "dist", "V-hollow", "PRINT_LIST.md"), encoding="utf-8") as f:
            self.assertIn("are the same file in this release", f.read())


if __name__ == "__main__":
    unittest.main()
