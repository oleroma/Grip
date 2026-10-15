# Release builder

Packs the printed parts into one zip per shape for a release, and checks that everything a release needs is in `orca_slicer/`.

There is no configuration file. A release is made from three things that are in the repository anyway:

- the preset files `combi_export` saves next to `Grip.blend` on every save, `blender/GripV_preset.json` and `blender/GripX_preset.json`. Under `exports` they list every file the presets write (see [The preset files](#the-preset-files));
- the folder names in `orca_slicer/`;
- the print lists in [`orca_slicer/README.md`](../../orca_slicer/README.md), which go into the `PRINT_LIST.md` of each zip.

The few fixed texts (repository link, license name, credits, guide links) are at the top of `build_release.py`.

## Where the releases come from

| What | Rule | In Grip |
| --- | --- | --- |
| Scene | one preset file; its `root_dir` names the scene's folder in `orca_slicer/`, whatever drive or folders come before it. A folder spelt with another case takes the spelling on disk. | `D:\Grip\orca_slicer\GripV\` is `GripV` |
| Shape | each top folder of the scene folder other than `parts/` and tolerance folders. The release id is the scene and the folder name without `case_` or `_style`; two folders that would get the same id keep their full names. | `GripV-standard` (`case_standard/`), `GripV-hollow`, `GripX-xbox` (`xbox_style/`), `GripX-dualsense` |
| Files | the files the presets export in the shape's folder, in `parts/` and directly in the scene folder | |
| OrcaSlicer projects | `<scene>_<shape folder>.3mf` and `<scene>_parts.3mf` in the scene folder, if they are there | `GripV_case_standard.3mf`, `GripV_parts.3mf` |
| Tolerance folders | `tight/`, `default/`, `loose/`, or a word and a tolerance (`cap_default/`, `press_loose/`). A build with one tolerance takes the files whose tolerance folders all name it, so every part with tolerance variants needs one at that tolerance. | |
| Print list | the first `## Print list` section of `orca_slicer/README.md` whose heading names the shape (`GripV hollow`), else the first that names the scene (`GripV`), up to the next `##` heading | `## Print list: GripV standard and GripV hollow` |

So a file is in a release only when a preset exports it. To add a part to a release, add it to a preset and export it. To add a shape, export it to a new top folder of the scene folder. To change how many of a part to print, edit the print list.

The `exports` lists need a `combi_export` with the *Save JSON with File* tick. Preset files saved by an older one have no such list, and then `--check` and every build stop with an error until `Grip.blend` is saved with the new add-on.

## Use

You need Python 3.8 or newer, with no extra packages. Blender's own Python works too (see [orca_reload](../orca_reload/README.md#use) for its path on Windows).

```
python tools/release/build_release.py --check
python tools/release/build_release.py
python tools/release/build_release.py --full-paths
python tools/release/build_release.py --all-tolerances
python tools/release/build_release.py --shape GripX-xbox --tolerance loose --tag v0.1
python tools/release/build_release.py --print-list GripV-hollow
```

1. `--check` checks the presets, the files and their names. It works on Git LFS pointer files too, so it runs on any clone, also one without the models.
2. With no options it builds every shape with the `default` tolerance files into `dist/` in the repository, without the tolerance folders: `parts/bumpers/press_default/` becomes `parts/bumpers/`, and `parts/buttons/default/cap_default/` becomes `parts/buttons/cap/`.
3. `--full-paths` keeps the folders as they are in `orca_slicer/`. `--all-tolerances` puts every tolerance variant into the zips, always with the full paths. `--tolerance tight` or `loose` builds with that tolerance instead of `default`.
4. `--print-list` shows the `PRINT_LIST.md` of one shape without building anything.

A build looks like this:

```
dist/
  .gitignore                    ignores the whole folder, so builds never show up in git
  GripV-standard/
    PRINT_LIST.md
    LICENSE
    GripV_case_standard.3mf
    GripV_parts.3mf
    case_standard/case_bottom.stl ...
    parts/buttons/button.stl
    parts/buttons/cap/cross.stl ...
    parts/bumpers/L1.stl ...
  GripV-standard.zip
  GripV-hollow/ ...
  SHA256SUMS.txt
```

| Option | What it does |
| --- | --- |
| `--check` | Check the presets, files and names only (see below). |
| `--shape ID` | Build only this shape. Can be repeated. `--list` shows the ids. |
| `--tolerance LEVEL` | Use the `tight`, `default` or `loose` files for every fit part. Default: `default`. |
| `--all-tolerances` | Include every tolerance variant. The paths are always the full ones. |
| `--full-paths` | Keep the tolerance folders of `orca_slicer/` in the paths (`parts/buttons/default/cap_default/`) and the tolerance in the folder and zip names (`GripV-standard-default.zip`). |
| `--tag TEXT` | Add a tag to the folder and zip names, for example `GripV-standard-v0.1.zip`. |
| `--out DIR` | Write somewhere else than `dist/`. |
| `--no-zip` | Build the folders only. |
| `--print-list ID` | Print one shape's `PRINT_LIST.md` and stop. Takes `--tolerance`, `--all-tolerances` and `--full-paths`. |
| `--list` | List the shapes and stop. |
| `-v` | With `--check`: list every file of each identical tolerance variant. |
| `--repo DIR` | Use another repository folder. |
| `--allow-pointers` | Build even from Git LFS pointer files. Only for trying the script: the zips then hold no models. |

The exit code is 0 when all is well and 1 when a preset file is not usable, a file is missing, a name is wrong or a build failed.

## What `--check` reports

| Section | What it looks for | Result |
| --- | --- | --- |
| Presets | every `blender/*_preset.json`: how many files its presets write, and to which folder | an **error** when there is none, or one is not valid JSON, has a `root_dir` outside `orca_slicer/`, or has no complete `exports` list (saved by an older `combi_export`, or cut off at 5000 files) |
| Releases | the shapes, how many files each has at `default`, and its projects; parts that have tolerance variants but none at some tolerance; `LICENSE`, the guides the print lists link to, a print list for each scene, and the paths in it | two files that would land on the same path in a build without tolerance folders, two releases with the same id, a part with no `default` variant and a missing `LICENSE` are **errors**. A part with no `tight` or `loose` variant, a missing guide or print list, and a path in a print list that no preset exports (so no zip has it) are warnings. |
| Exported files | every file the presets export is in `orca_slicer/` | a missing file is an **error**, and so is one whose name differs only by case (Windows and macOS find it, a Linux clone does not) |
| Files no preset exports | `.stl` and `.3mf` files in the scene folders that no preset exports and no release takes, and part files outside the scene folders | an `.stl` is a warning (it is in no release: delete it or add it to a preset, which it says first when the print list asks for it); a project or a file outside is information. A scene whose preset file could not be read is reported once, not file by file. |
| File and folder names | spaces, characters Windows does not allow, and names that differ only by case (they collide on Windows and macOS) in all of `orca_slicer/`. It reads git's file list as well as the disk, because on Windows and macOS the disk only holds one of two such names. | **errors**. Other unusual characters, such as `%` or `( )`, are warnings: they work on disk but are awkward in links and shells. |
| Tolerance variants that are the same file | exported files in sibling tolerance folders (`tight`/`default`/`loose`, `cap_*`, `press_*`) with the same content | warning, summarised per folder pattern, for example `GripX/parts/buttons/*/<cap_*>/: cap_tight = cap_default = cap_loose` |
| Git LFS | how many files are pointers and how many are real | information |

Two files count as the same when their sha256 matches. For a pointer file that is the `oid` it records, which is the sha256 of the real file, so pointers and real files can be compared with each other.

## How a build works

- It stops before writing anything if a file is missing or is still a Git LFS pointer (run `git lfs pull` first), or if a part has no variant at the chosen tolerance.
- Files keep their path below the scene folder (`orca_slicer/GripV/` for GripV), but without the tolerance folders, because a build holds one tolerance: a folder named only by a tolerance (`default/`) is left out. A folder with a word before the tolerance (`cap_default/`, `press_default/`) keeps the word (`cap/`) when the folder it is in holds files of its own, so the caps stay apart from the `button.stl` shaft next to them, and is left out otherwise (`parts/bumpers/press_default/` becomes `parts/bumpers/`). The `default` tolerance is not added to the folder and zip names either; `tight` and `loose` are (`GripV-standard-tight.zip`).
- With `--full-paths` or `--all-tolerances` the paths are the same as in `orca_slicer/`, so the tolerance of each part shows in its path.
- If two files would land on the same path without the tolerance folders, the build stops before writing anything, and `--check` reports it as an error.
- The OrcaSlicer projects of a shape go only into `default` builds, because they were laid out with those files (probably).
- `PRINT_LIST.md` holds the fit, which repository folders became which zip folders, the print list from `orca_slicer/README.md`, the files in the zip by folder, the projects, links to the guides, the license and the credits. The print list loses the table rows that only name the other shapes of the scene (the middle plate in GripV standard), its paths in backticks become the paths in the zip, and its links point at GitHub. A path it names that the zip does not have is listed under "Not in this zip", and the build warns about it. Without a print list for the scene it links to `orca_slicer/README.md` instead.
- "Built from commit" in `PRINT_LIST.md` also says when `orca_slicer/` or `blender/` had uncommitted changes, since the preset files decide what is in the zips.
- Each zip has one top folder with the release name. Files are stored in a fixed order with a fixed date, so the same files always give the same zip. `SHA256SUMS.txt` lists the checksum of every zip in the output folder.
- A new build replaces the folder and zip of an earlier build with the same name. A folder that has no `PRINT_LIST.md` was not made by this script and is never removed.

## The preset files

When `Grip.blend` is saved, `combi_export` writes the presets of each scene to `<scene>_preset.json` next to it (its *Save JSON with File* tick, on by default). Besides the presets, the file lists under `exports` every file each preset writes, below the preset's root folder, named as the add-on names them:

```json
"root_dir": "D:\\Grip\\orca_slicer\\GripV\\",
"exports": {"complete": true, "presets": [{"name": "Buttons", "files": ["parts/buttons/default/button.stl", "..."]}]}
```

The builder only reads the end of `root_dir` after `orca_slicer`, so the absolute paths of one computer work on any clone. OrcaSlicer projects are not exports; they are found by their names.

### When you export a new part

1. Export it into `orca_slicer/` with the `combi_export` presets, save `Grip.blend` and commit the preset files with it.
2. Run `--check`. The part should be counted under its release and not appear under "Files no preset exports".
3. Add it to the print list in `orca_slicer/README.md`.

## Tests

```
python -m unittest discover tools/release
```

The tests build a small repository with preset files and fake Git LFS pointer files in a temporary folder. One test also runs `--check` on the real repository once its preset files list their exports.
