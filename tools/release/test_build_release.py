"""Tests for build_release.py. Run: python -m unittest discover tools/release

The tests build a small repository in a temporary folder: preset files as
combi_export saves them in blender/, a LICENSE, the guides, a print list in
orca_slicer/README.md and an orca_slicer/ tree made of fake Git LFS pointer
files (or of small real files where the test needs real models)."""

import io
import json
import os
import shutil
import subprocess
import tempfile
import unittest
import zipfile
import hashlib
from contextlib import redirect_stdout, redirect_stderr

import build_release as br

LEVELS = ("tight", "default", "loose")

# What the presets of the scene V export, below orca_slicer/V/
V_FILES = sorted(
    ["case_standard/case_bottom.stl", "case_standard/case_top_knob.stl",
     "case_hollow/case_bottom.stl", "case_hollow/case_middle_plate.stl",
     "parts/sticks/circle/stick_10_deg.stl"]
    + ["parts/buttons/%s/button.stl" % t for t in LEVELS]
    + ["parts/buttons/%s/cap_%s/cross.stl" % (t, c) for t in LEVELS for c in LEVELS]
    + ["parts/triggers/%s/press_%s/R2.stl" % (t, p) for t in LEVELS for p in LEVELS]
    + ["parts/bumpers/press_%s/L1.stl" % p for p in LEVELS])
V_PROJECTS = ["V_case_standard.3mf", "V_parts.3mf"]

# The scene X exports with a root folder relative to Grip.blend
X_FILES = ["parts/pins/pin.stl", "xbox_style/case_bottom.stl"]

# V-standard at the default tolerance, below orca_slicer/V/, and as a plain build lays it out
DEFAULT_FILES = [
    "V_case_standard.3mf",
    "V_parts.3mf",
    "case_standard/case_bottom.stl",
    "case_standard/case_top_knob.stl",
    "parts/bumpers/press_default/L1.stl",
    "parts/buttons/default/button.stl",
    "parts/buttons/default/cap_default/cross.stl",
    "parts/sticks/circle/stick_10_deg.stl",
    "parts/triggers/default/press_default/R2.stl",
]
FLAT_FILES = [
    "V_case_standard.3mf",
    "V_parts.3mf",
    "case_standard/case_bottom.stl",
    "case_standard/case_top_knob.stl",
    "parts/bumpers/L1.stl",
    "parts/buttons/button.stl",
    "parts/buttons/cap/cross.stl",
    "parts/sticks/circle/stick_10_deg.stl",
    "parts/triggers/R2.stl",
]

PRINT_LISTS = """# Printed parts

## Tolerances

Start with default.

## Print list: V standard and V hollow

| Qty | Part | File |
| ---: | --- | --- |
| 4 | Shaft | `parts/buttons/default/button.stl`, see [tolerances](#tolerances) |
| 2 | Pin | the [guide](../docs/print-guide.md#pins) |

## Print list: X

| Qty | Part |
| ---: | --- |
| 2 | Pin |

## Release zips

Built by the script.
"""


def pointer(content):
    """Git LFS pointer text for content."""
    return ("version https://git-lfs.github.com/spec/v1\noid sha256:%s\nsize %d\n"
            % (hashlib.sha256(content).hexdigest(), len(content))).encode()


def preset_file(root_dir, presets, complete=True):
    """A preset file as combi_export saves it: presets is [(name, files)]."""
    return {"data_version": 4, "root_dir": root_dir, "global_nodegroups": [], "presets": [],
            "exports": {"complete": complete, "presets": [{"name": n, "files": f} for n, f in presets]}}


class Fixture(unittest.TestCase):
    """A temporary repository with every file the presets export."""

    real = False

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="grip_release_test_")
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.root = os.path.join(self.tmp, "orca_slicer")
        self.write(os.path.join(self.tmp, "LICENSE"), b"Test License 1.0\n\nText.\n")
        for _, path in br.GUIDES:
            if "://" not in path:
                self.write(os.path.join(self.tmp, *path.split("/")), b"# Guide\n")
        self.write(os.path.join(self.tmp, "orca_slicer", "README.md"), PRINT_LISTS.encode())
        self.write_presets("V", "D:\\Grip\\orca_slicer\\V\\",
                           [("Cases", [f for f in V_FILES if f.startswith("case_")]),
                            ("Parts", [f for f in V_FILES if f.startswith("parts/")])])
        self.write_presets("X", "//../orca_slicer/X/", [("All", X_FILES)])
        for rel in V_FILES + V_PROJECTS:
            self.put("V/" + rel)
        for rel in X_FILES:
            self.put("X/" + rel)

    def write_presets(self, scene, root_dir, presets, complete=True):
        data = preset_file(root_dir, presets, complete)
        self.write(os.path.join(self.tmp, "blender", scene + "_preset.json"), json.dumps(data, indent=4).encode())

    def write(self, path, data):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as f:
            f.write(data)

    def put(self, rel, content=None, real=None):
        """Write a part under orca_slicer/: a pointer, or the real content."""
        content = content if content is not None else ("solid %s\nendsolid\n" % rel).encode()
        real = self.real if real is None else real
        self.write(br.native(self.root, rel), content if real else pointer(content))

    def releases(self):
        scenes, notes = br.load_scenes(self.tmp)
        self.assertEqual([n for n in notes if n[0] == "error"], [])
        return br.releases(scenes, br.scan(self.root))

    def release(self, release_id):
        return br.find_release(self.releases(), release_id)

    def check(self, verbose=False):
        return br.check(self.tmp, verbose)

    def run_main(self, *args):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = br.main(["--repo", self.tmp] + list(args))
        return code, out.getvalue() + err.getvalue()


class PresetTests(Fixture):

    def test_root_folder_names_the_scene_folder(self):
        for root_dir, folder in (("D:\\Grip\\orca_slicer\\GripV\\", "GripV"), ("//../orca_slicer/GripV/", "GripV"),
                                 ("/home/me/Grip/Orca_Slicer/v", "v"), ("D:\\Grip\\orca_slicer\\GripV\\old", "GripV/old"),
                                 ("D:\\Grip\\orca_slicer\\", None), ("D:\\Grip\\other\\V\\", None), ("", None)):
            self.assertEqual(br.scene_folder(root_dir), folder, root_dir)

    def test_scenes_hold_the_exports_of_their_presets(self):
        scenes, notes = br.load_scenes(self.tmp)
        self.assertEqual([s.folder for s in scenes], ["V", "X"])
        self.assertEqual(sorted(scenes[0].files), V_FILES)
        self.assertEqual(scenes[0].files["parts/buttons/default/button.stl"], "Parts")
        self.assertIn(("info", "blender/V_preset.json: 2 presets write %d files to orca_slicer/V/." % len(V_FILES)),
                      notes)
        self.assertIn(("info", "blender/X_preset.json: 1 preset writes 2 files to orca_slicer/X/."), notes)

    def test_problem_files_are_errors(self):
        for kwargs, words in (({"complete": False}, "lists only part of the exported files"),
                              ({"root_dir": "D:\\Grip\\exports\\"}, "is not a folder in orca_slicer/")):
            with self.subTest(words=words):
                args = dict({"root_dir": "D:\\Grip\\orca_slicer\\X\\", "presets": [("All", X_FILES)]}, **kwargs)
                self.write_presets("X", **args)
                _, notes = br.load_scenes(self.tmp)
                self.assertTrue(any(level == "error" and words in text for level, text in notes), notes)
        old = {"data_version": 3, "root_dir": "D:\\Grip\\orca_slicer\\X\\", "presets": []}
        self.write(os.path.join(self.tmp, "blender", "X_preset.json"), json.dumps(old).encode())
        code, text = self.check()
        self.assertEqual(code, br.EXIT_ERROR)
        self.assertIn("ERROR    blender/X_preset.json has no list of the exported files: save Grip.blend", text)
        self.write(os.path.join(self.tmp, "blender", "X_preset.json"), b"{not json")
        code, text = self.check()
        self.assertIn("ERROR    blender/X_preset.json is not valid JSON", text)
        code, out = self.run_main("--list")
        self.assertEqual(code, br.EXIT_ERROR)
        self.assertIn("blender/X_preset.json is not valid JSON", out)

    def test_no_preset_files(self):
        shutil.rmtree(os.path.join(self.tmp, "blender"))
        code, text = self.check()
        self.assertEqual(code, br.EXIT_ERROR)
        self.assertIn("no blender/*_preset.json", text)


class ReleaseTests(Fixture):

    def test_one_release_per_shape_folder(self):
        rels = self.releases()
        self.assertEqual([(r.id, r.title, r.shape) for r in rels],
                         [("V-hollow", "V hollow", "case_hollow"), ("V-standard", "V standard", "case_standard"),
                          ("X-xbox", "X xbox", "xbox_style")])
        hollow = rels[0]
        self.assertIn("case_hollow/case_middle_plate.stl", hollow.files)
        self.assertNotIn("case_standard/case_bottom.stl", hollow.files)
        self.assertIn("parts/buttons/tight/button.stl", hollow.files)
        self.assertEqual(hollow.projects, ["V_parts.3mf"])
        self.assertEqual(rels[1].projects, ["V_case_standard.3mf", "V_parts.3mf"])
        self.assertEqual(rels[2].files, X_FILES)

    def test_shape_labels(self):
        for shape, label in (("case_standard", "standard"), ("xbox_style", "xbox"), ("case_", "case_"),
                             ("_style", "_style"), ("bumpers", "bumpers")):
            self.assertEqual(br.shape_label(shape), label)

    def test_scene_without_a_shape_folder_is_one_release(self):
        self.write_presets("X", "D:\\Grip\\orca_slicer\\X\\", [("All", ["parts/pins/pin.stl", "case.stl"])])
        self.put("X/case.stl")
        release = self.release("X")
        self.assertEqual((release.id, release.title, release.files), ("X", "X", ["case.stl", "parts/pins/pin.stl"]))

    def test_unknown_release(self):
        with self.assertRaises(br.BuildError) as cm:
            self.release("V-round")
        self.assertIn("known: V-hollow, V-standard, X-xbox", str(cm.exception))

    def test_default_layout_leaves_out_the_tolerance_folders(self):
        release = self.release("v-standard")
        paths = br.layout(release, "default", flat=True)
        self.assertEqual(sorted(paths), DEFAULT_FILES)
        self.assertEqual(sorted(paths.values()), FLAT_FILES)
        self.assertEqual(br.layout(release, "default"), {rel: rel for rel in DEFAULT_FILES})

    def test_other_tolerances(self):
        release = self.release("V-standard")
        tight = br.layout(release, "tight", flat=True)
        self.assertEqual(tight["parts/buttons/tight/cap_tight/cross.stl"], "parts/buttons/cap/cross.stl")
        self.assertNotIn("V_parts.3mf", tight)  # projects only go with the default tolerance
        every = br.layout(release, br.ALL)
        self.assertEqual(len([f for f in every if f.endswith("cross.stl")]), 9)
        self.assertNotIn("V_parts.3mf", every)
        self.assertEqual(every["parts/triggers/loose/press_tight/R2.stl"], "parts/triggers/loose/press_tight/R2.stl")

    def test_a_tolerance_word_stays_only_beside_files(self):
        """cap_default/ next to button.stl becomes cap/; press_default/ in a folder of
        tolerance folders only goes."""
        self.write_presets("X", "D:\\Grip\\orca_slicer\\X\\", [("All", [
            "default/a.stl", "parts/x/default/fit_default/b.stl", "parts/y/default/fit_default/c.stl",
            "parts/y/default/d.stl"])])
        paths = br.layout(self.release("X"), "default", flat=True)
        self.assertEqual(paths, {"default/a.stl": "a.stl", "parts/x/default/fit_default/b.stl": "parts/x/b.stl",
                                 "parts/y/default/d.stl": "parts/y/d.stl",
                                 "parts/y/default/fit_default/c.stl": "parts/y/fit/c.stl"})

    def test_levels_of_a_path(self):
        self.assertEqual(br.levels_of("parts/buttons/tight/cap_loose/cross.stl"), ["tight", "loose"])
        self.assertEqual(br.levels_of("parts/defaults/default.stl"), [])


class CheckTests(Fixture):

    def test_complete_tree_passes(self):
        code, text = self.check()
        self.assertEqual(code, br.EXIT_OK, text)
        for line in ("  V-hollow             7 files at `default`, with V_parts.3mf",
                     "  V-standard           7 files at `default`, with V_case_standard.3mf, V_parts.3mf",
                     "  X-xbox               2 files at `default`",
                     "  all %d exported files are in orca_slicer/." % (len(V_FILES) + len(X_FILES)),
                     "Files no preset exports\n  none.",
                     "%d pointer files, 0 real files." % (len(V_FILES) + len(X_FILES) + 2),
                     "Result: 0 errors, 0 warnings."):
            self.assertIn(line, text)

    def test_exported_file_missing_on_disk_fails(self):
        os.remove(br.native(self.root, "V/parts/buttons/loose/cap_tight/cross.stl"))
        code, text = self.check()
        self.assertEqual(code, br.EXIT_ERROR)
        self.assertIn("ERROR    missing V/parts/buttons/loose/cap_tight/cross.stl: preset 'Parts' exports it, "
                      "so export it again", text)

    def test_exported_file_with_another_case_fails(self):
        # A case-blind disk (Windows, macOS) would find the file, a Linux clone would not.
        os.remove(br.native(self.root, "V/parts/buttons/default/button.stl"))
        self.put("V/parts/buttons/default/Button.stl")
        code, text = self.check()
        self.assertEqual(code, br.EXIT_ERROR)
        self.assertIn("case differs: preset 'Parts' exports V/parts/buttons/default/button.stl, "
                      "the file is V/parts/buttons/default/Button.stl", text)

    def test_files_no_preset_exports_warn(self):
        self.put("V/parts/misc/old.stl")
        self.put("V/V_case_round.3mf")
        self.put("dongle/case.3mf")
        code, text = self.check()
        self.assertEqual(code, br.EXIT_OK, text)
        stale = text.split("Files no preset exports")[1].split("File and folder names")[0]
        self.assertIn("warning  V/parts/misc/old.stl: in no release; delete it, or add it to a preset", stale)
        self.assertIn("  V/V_case_round.3mf: an OrcaSlicer project that no release takes", stale)
        self.assertIn("  dongle/case.3mf: outside the export folders", stale)
        self.assertNotIn("V_parts.3mf", stale)
        self.assertIn("Result: 0 errors, 1 warning.", text)
        self.assertNotIn("names X", text)

    def test_missing_license_fails_and_missing_guides_warn(self):
        os.remove(os.path.join(self.tmp, "LICENSE"))
        os.remove(os.path.join(self.tmp, "docs", "print-guide.md"))
        code, text = self.check()
        self.assertEqual(code, br.EXIT_ERROR)
        self.assertIn("ERROR    missing LICENSE", text)
        self.assertIn("warning  missing docs/print-guide.md", text)

    def test_scene_without_a_print_list_warns(self):
        self.write(os.path.join(self.root, "README.md"), b"# Printed parts\n\n## Print list: V\n\nOnly V.\n")
        code, text = self.check()
        self.assertEqual(code, br.EXIT_OK, text)
        self.assertIn("warning  orca_slicer/README.md has no \"## Print list\" section that names X", text)
        self.assertNotIn("that names V", text)

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
        for level in LEVELS:
            self.put("V/parts/buttons/default/cap_%s/cross.stl" % level, b"the same cap")
        self.put("V/parts/triggers/default/press_tight/R2.stl", b"trigger")
        self.put("V/parts/triggers/loose/press_tight/R2.stl", b"trigger")
        self.put("V/parts/old/tight/a.stl", b"stale")  # no preset exports these
        self.put("V/parts/old/loose/a.stl", b"stale")
        code, text = self.check()
        self.assertEqual(code, br.EXIT_OK, text)
        self.assertIn("V/parts/buttons/*/<cap_*>/: cap_tight = cap_default = cap_loose (1 of 3 files)", text)
        self.assertIn("V/parts/triggers/<tolerance>/press_*/: default = loose (1 of 3 files)", text)
        self.assertNotIn("V/parts/old/", text.split("Tolerance variants")[1])

    def test_tolerance_folder_at_the_top(self):
        digests = {"tight/a.stl": "1", "default/a.stl": "1", "loose/a.stl": "2"}
        self.assertEqual(br.identical_siblings(digests), [("<tolerance>/", "tight = default", ["*/a.stl"], 1)])

    def test_listing_identical_files(self):
        self.put("V/parts/buttons/tight/button.stl", b"shaft")
        self.put("V/parts/buttons/default/button.stl", b"shaft")
        _, text = self.check(verbose=True)
        self.assertIn("V/parts/buttons/<tolerance>/: tight = default (1 of 1 files)", text)
        self.assertIn("V/parts/buttons/*/button.stl", text)

    def test_pointer_and_real_file_with_the_same_content_match(self):
        self.put("V/parts/buttons/tight/button.stl", b"shaft", real=True)
        self.put("V/parts/buttons/loose/button.stl", b"shaft", real=False)
        _, text = self.check()
        self.assertIn("V/parts/buttons/<tolerance>/: tight = loose (1 of 1 files)", text)
        self.assertIn("1 real files.", text)

    def test_files_that_would_land_on_one_path_fail(self):
        files = V_FILES + ["parts/buttons/button.stl"]
        self.write_presets("V", "D:\\Grip\\orca_slicer\\V\\", [("All", files)])
        self.put("V/parts/buttons/button.stl")
        code, text = self.check()
        self.assertEqual(code, br.EXIT_ERROR)
        self.assertIn("V/parts/buttons/button.stl and V/parts/buttons/default/button.stl land on the same path "
                      "parts/buttons/button.stl in the V hollow release", text)

    def test_check_from_the_command_line(self):
        code, out = self.run_main("--check")
        self.assertEqual(code, br.EXIT_OK)
        self.assertIn("Result: 0 errors", out)
        os.remove(br.native(self.root, "V/case_hollow/case_bottom.stl"))
        code, out = self.run_main("--check")
        self.assertEqual(code, br.EXIT_ERROR)

    def test_real_repository(self):
        """The repository's own presets and orca_slicer/ pass, once Grip.blend was
        saved with a combi_export that writes the export lists."""
        if not os.path.isdir(os.path.join(br.DEFAULT_REPO, br.ROOT)):
            self.skipTest("no orca_slicer/ next to this tool")
        _, notes = br.load_scenes(br.DEFAULT_REPO)
        if any("has no list of the exported files" in text for _, text in notes):
            self.skipTest("the preset files have no export lists yet")
        code, text = br.check(br.DEFAULT_REPO)
        self.assertEqual(code, br.EXIT_OK, text)


class PrintListTests(Fixture):

    def test_default_print_list(self):
        release = self.release("V-standard")
        paths = br.layout(release, "default", flat=True)
        text = br.print_list(release, "default", paths, br.print_section(self.tmp, release.scene),
                             "commit `abc1234`", flat=True)
        self.assertTrue(text.startswith("# V standard: print list\n\nFit: `default`.\nBuilt from commit `abc1234`.\n"))
        for line in (
                "paths leave out the tolerance folders that `orca_slicer/V/` in the repository has. For example "
                "`parts/bumpers/press_default/` there is `parts/bumpers/` here.",
                "## What to print\n\nFrom the print list in the repository",
                "| 4 | Shaft | `parts/buttons/default/button.stl`, see "
                "[tolerances](https://github.com/oleroma/Grip/blob/main/orca_slicer/README.md#tolerances) |",
                "the [guide](https://github.com/oleroma/Grip/blob/main/docs/print-guide.md#pins)",
                "- `parts/buttons/`: `button.stl`",
                "- `parts/buttons/cap/`: `cross.stl`",
                "- `case_standard/`: `case_bottom.stl`, `case_top_knob.stl`",
                "## OrcaSlicer projects\n\n- `V_case_standard.3mf`\n- `V_parts.3mf`",
                "- [Printing guide](https://github.com/oleroma/Grip/blob/main/docs/print-guide.md)",
                "Licensed under Creative Commons BY-NC-SA 4.0, see `LICENSE`. Credits: Oleroma, Milwud."):
            self.assertIn(line, text)
        self.assertNotIn("Built by the script", text)  # the next section of the README
        self.assertNotIn("V_parts.3mf`, `", text)  # projects are not listed with the files

    def test_full_paths_and_all_tolerances(self):
        release = self.release("V-hollow")
        text = br.print_list(release, br.ALL, br.layout(release, br.ALL), None)
        self.assertIn("Every tolerance variant is included. Start with `default` everywhere.", text)
        self.assertIn("The paths are the same as in `orca_slicer/V/` in the repository", text)
        self.assertIn("- `parts/buttons/tight/cap_loose/`: `cross.stl`", text)
        self.assertIn("See the [print list](https://github.com/oleroma/Grip/blob/main/orca_slicer/README.md)", text)
        self.assertNotIn("## OrcaSlicer projects", text)

    def test_print_list_from_the_command_line(self):
        code, out = self.run_main("--print-list", "V-hollow")
        self.assertEqual(code, br.EXIT_OK, out)
        self.assertIn("`parts/buttons/cap/`: `cross.stl`", out)
        code, out = self.run_main("--print-list", "V-hollow", "--full-paths")
        self.assertIn("`parts/buttons/default/cap_default/`: `cross.stl`", out)
        code, out = self.run_main("--list")
        self.assertEqual(code, br.EXIT_OK)
        self.assertIn("V-standard           orca_slicer/V/case_standard + parts/", out)

    def test_unknown_tolerance(self):
        code, out = self.run_main("--tolerance", "medium", "--print-list", "V-hollow")
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
        os.remove(br.native(self.root, "V/case_hollow/case_middle_plate.stl"))
        code, out = self.build("--shape", "V-hollow")
        self.assertEqual(code, br.EXIT_ERROR)
        self.assertIn("missing V/case_hollow/case_middle_plate.stl", out)

    def test_build_refuses_a_file_spelt_with_another_case(self):
        os.remove(br.native(self.root, "V/case_hollow/case_bottom.stl"))
        self.put("V/case_hollow/Case_bottom.stl")
        code, out = self.build("--shape", "V-hollow")
        self.assertEqual(code, br.EXIT_ERROR)
        self.assertIn("missing V/case_hollow/case_bottom.stl", out)

    def test_default_build(self):
        code, out = self.build()
        self.assertEqual(code, br.EXIT_OK, out)
        self.assertEqual(self.folder_files("V-standard"), sorted(FLAT_FILES + ["LICENSE", "PRINT_LIST.md"]))
        dist = os.path.join(self.tmp, "dist")
        with zipfile.ZipFile(os.path.join(dist, "V-standard.zip")) as z:
            self.assertEqual(sorted(z.namelist()),
                             sorted("V-standard/" + f for f in FLAT_FILES + ["LICENSE", "PRINT_LIST.md"]))
            self.assertEqual(z.read("V-standard/parts/buttons/cap/cross.stl"),
                             b"solid V/parts/buttons/default/cap_default/cross.stl\nendsolid\n")
            listing = z.read("V-standard/PRINT_LIST.md").decode()
        self.assertIn("Fit: `default`.", listing)
        self.assertIn("| 4 | Shaft |", listing)
        self.assertNotIn("V_case_standard.3mf", self.folder_files("V-hollow"))
        self.assertIn("V_parts.3mf", self.folder_files("V-hollow"))
        self.assertEqual(self.folder_files("X-xbox"), ["LICENSE", "PRINT_LIST.md"] + X_FILES)
        with open(os.path.join(dist, "SHA256SUMS.txt")) as f:
            sums = f.read().splitlines()
        self.assertEqual([line.split("  ")[1] for line in sums], ["V-hollow.zip", "V-standard.zip", "X-xbox.zip"])
        self.assertNotIn("warning", out)
        self.write(os.path.join(self.root, "README.md"), b"# Printed parts\n")
        code, out = self.build("--shape", "X-xbox")
        self.assertEqual(code, br.EXIT_OK, out)
        self.assertIn("warning: orca_slicer/README.md has no print list for X", out)
        with zipfile.ZipFile(os.path.join(dist, "X-xbox.zip")) as z:
            self.assertIn("See the [print list](https://github.com/oleroma/Grip/blob/main/orca_slicer/README.md)",
                          z.read("X-xbox/PRINT_LIST.md").decode())

    def test_full_paths_build(self):
        code, out = self.build("--shape", "V-standard", "--full-paths")
        self.assertEqual(code, br.EXIT_OK, out)
        self.assertEqual(self.folder_files("V-standard-default"), sorted(DEFAULT_FILES + ["LICENSE", "PRINT_LIST.md"]))

    def test_files_that_would_land_on_one_path(self):
        self.write_presets("V", "D:\\Grip\\orca_slicer\\V\\", [("All", V_FILES + ["parts/buttons/button.stl"])])
        self.put("V/parts/buttons/button.stl")
        code, out = self.build("--shape", "V-hollow")
        self.assertEqual(code, br.EXIT_ERROR)
        self.assertIn("V-hollow: parts/buttons/button.stl and parts/buttons/default/button.stl land on the "
                      "same path parts/buttons/button.stl", out)
        self.assertFalse(os.path.exists(os.path.join(self.tmp, "dist")))
        code, out = self.build("--shape", "V-hollow", "--full-paths")
        self.assertEqual(code, br.EXIT_OK, out)

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

    def test_files_no_preset_exports_stay_out(self):
        self.put("V/parts/misc/old.stl")
        code, out = self.build("--shape", "V-standard")
        self.assertEqual(code, br.EXIT_OK, out)
        self.assertNotIn("parts/misc/old.stl", self.folder_files("V-standard"))


if __name__ == "__main__":
    unittest.main()
