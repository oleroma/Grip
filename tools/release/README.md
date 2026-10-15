# Release builder

Packs the printed parts into one zip per shape for a release, and checks that everything a release needs is in `orca_slicer/`.

Each released shape (GripV standard, GripV hollow, GripX xbox, GripX dualsense) has a **print set** in `print_sets.json`: the files to print and how many of each. That one file drives everything here: the zips, the `PRINT_LIST.md` inside each zip, and `--check`. `--check` and the build also compare it with what the `combi_export` presets export, from the JSON files combi_export saves next to `Grip.blend` (see [The presets](#the-combi_export-presets)). The print lists in [`orca_slicer/README.md`](../../orca_slicer/README.md) are written by hand from the same sets, so change both together.

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

1. `--check` checks the files and their names. It works on Git LFS pointer files too, so it runs on any clone, also one without the models.
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
| `--check` | Check files and names only (see below). |
| `--shape ID` | Build only this shape. Can be repeated. `--list` shows the ids. |
| `--tolerance LEVEL` | Use the `tight`, `default` or `loose` files for every fit part. Default: `default`. |
| `--all-tolerances` | Include every tolerance variant. The paths are always the full ones. |
| `--full-paths` | Keep the tolerance folders of `orca_slicer/` in the paths (`parts/buttons/default/cap_default/`) and the tolerance in the folder and zip names (`GripV-standard-default.zip`). This is what a plain build made before. |
| `--tag TEXT` | Add a tag to the folder and zip names, for example `GripV-standard-v0.1.zip`. |
| `--out DIR` | Write somewhere else than `dist/`. |
| `--no-zip` | Build the folders only. |
| `--print-list ID` | Print one shape's `PRINT_LIST.md` and stop. Takes `--tolerance`, `--all-tolerances` and `--full-paths`. |
| `--list` | List the shapes and stop. |
| `-v` | With `--check`: list every file of each identical tolerance variant. |
| `--repo DIR`, `--sets FILE` | Use another repository folder or print sets file. |
| `--allow-pointers` | Build even from Git LFS pointer files. Only for trying the script: the zips then hold no models. |

The exit code is 0 when all is well and 1 when a file is missing, a name is wrong, a build failed or the print sets file is not valid.

## What `--check` reports

| Section | What it looks for | Result |
| --- | --- | --- |
| Print sets | every file a print set names, at every tolerance, and the OrcaSlicer projects; also `LICENSE` and the guides the print lists link to | a missing part, project or license is an **error**, and so is a file whose name differs from the print set only by case (Windows and macOS find it, a Linux clone does not), and two files that would land on the same path in a build without tolerance folders; a missing guide is a warning |
| File and folder names | spaces, characters Windows does not allow, and names that differ only by case (they collide on Windows and macOS) in all of `orca_slicer/`. It reads git's file list as well as the disk, because on Windows and macOS the disk only holds one of two such names. | **errors**. Other unusual characters, such as `%` or `( )`, are warnings: they work on disk but are awkward in links and shells. |
| Tolerance variants that are the same file | files in sibling tolerance folders (`tight`/`default`/`loose`, `cap_*`, `press_*`, `pres_*`) with the same content | warning, summarised per folder pattern, for example `GripX/parts/buttons/*/<cap tolerance>/: cap_tight = cap_default = cap_loose` |
| Choices that are the same file | the alternatives of one item (case tops, knob or plate, sticks) that are identical, so one was probably exported with the wrong setting | warning |
| Not exported yet | the parts the print sets mark as `missing` | warning |
| combi_export presets | the `.stl` files the print sets name that no preset exports any more (they may be older than `Grip.blend`), and the exported files that are not in `orca_slicer/` and no print set needs (`-v` lists them) | a file no preset exports is a warning, and so is a preset JSON that is missing or has no complete list of its exports; a JSON that is not valid is an **error** |
| Files no print set uses | `.stl` and `.3mf` files under `orca_slicer/` that no print set names, marked `(no preset exports it)` when the presets do not write them either | information |
| Git LFS | how many files are pointers and how many are real | information |

Two files count as the same when their sha256 matches. For a pointer file that is the `oid` it records, which is the sha256 of the real file, so pointers and real files can be compared with each other.

## How a build works

- It stops before writing anything if a file is missing or is still a Git LFS pointer. Run `git lfs pull` first.
- Files keep their path below the shape's folder (`orca_slicer/GripV/` for GripV), but without the tolerance folders, because a build holds one tolerance: a folder named only by a tolerance (`default/`, `press_default/`) is left out, and `cap_default/` becomes `cap/` so the caps stay apart from the shafts. `flat_folders` in the print sets says which name each kind of tolerance folder gets. The `default` tolerance is not added to the folder and zip names either; `tight` and `loose` are (`GripV-standard-tight.zip`).
- With `--full-paths` or `--all-tolerances` the paths are the same as in `orca_slicer/`, so the tolerance of each part shows in its path.
- If two files would land on the same path without the tolerance folders, the build stops before writing anything, and `--check` reports it as an error.
- If the presets no longer export a file of the release, the build still packs it and prints a warning, because the file may be older than `Grip.blend`.
- A file used by several items (the GripV `button.stl` serves ABXY and the D-pad) is copied once.
- The OrcaSlicer projects of a shape go only into `default` builds, because they were laid out with those files (probably).
- `PRINT_LIST.md` is written from the print set: every item with its quantity and file, the parts not exported yet, the quantities not confirmed, links to the guides on GitHub, the license and the credits. If two alternatives in the build are the same file, it says so at the top.
- Each zip has one top folder with the release name. Files are stored in a fixed order with a fixed date, so the same files always give the same zip. `SHA256SUMS.txt` lists the checksum of every zip in the output folder.
- A new build replaces the folder and zip of an earlier build with the same name. A folder that has no `PRINT_LIST.md` was not made by this script and is never removed.

## The print sets file

`print_sets.json` has three parts: settings, `groups` of items, and `shapes` that list which groups they use. Groups are shared, so a cap that every shape prints is written once.

| Key | What it is for |
| --- | --- |
| `root` | the folder with the exported parts (`orca_slicer`) |
| `repo_url`, `branch` | where the guide links in `PRINT_LIST.md` point |
| `license`, `license_name`, `credits`, `notice` | copied or quoted into every release |
| `guides` | links for the end of each print list: a `path` in the repository or a full `url` |
| `tolerance_levels`, `default_tolerance` | the tolerance levels and the one a plain build uses |
| `tolerance_placeholders` | the placeholders in paths that stand for a tolerance level (`{tolerance}`, `{cap}`, `{press}`), with the setting name a print list shows for them |
| `presets` | the JSON files `combi_export` saves next to `Grip.blend` (`blender/GripV_preset.json`, `blender/GripX_preset.json`), see [The presets](#the-combi_export-presets) |
| `flat_folders` | for each tolerance placeholder, the folder name a build without `--full-paths` gives the folders named by it: `"cap": "cap"` turns `cap_default/` into `cap/`, and `""` leaves the folder out. A placeholder not listed is left out too. |

**A shape** has an `id` (used in folder names and on the command line), a `title`, the `folder` under `root` its paths start from, the `groups` it prints, and optionally `about`, `vars`, `projects`, `notes` and `hardware`. `vars` fills in placeholders that differ per shape, such as `{case}` (`case_standard`, `case_hollow`, `xbox_style`, `dualsense_style`).

**A group** has a `title` (the heading in the print list), `items`, and optionally a `note` and a `when` condition for all its items.

**An item** is one line of the print list:

| Key | What it is for |
| --- | --- |
| `name` | what the part is |
| `qty` | how many to print |
| `file` | the file, relative to the shape's folder |
| `files` | instead of `file`: alternatives, of which you print one (`qty` times) |
| `choose` | with `file`: placeholders for options, each with its values. The item offers every combination, like the GripV sticks. |
| `missing` | instead of a file: a part that is needed but not exported yet, and why |
| `when` | when the part is needed, for example `with a dpad_stick case top` |
| `note` | anything else the printer should know |
| `unconfirmed` | why the quantity or the fit is not confirmed. Shown as "Not confirmed" in the list. |
| `optional` | `true` for parts you can leave out |

Placeholders are written `{name}` and are filled from the shape's `vars`, from the tolerance level, and from `choose`. So this item

```json
{"name": "Cross cap", "file": "parts/buttons/{tolerance}/cap_{cap}/cross.stl", "qty": 1}
```

is `parts/buttons/default/cap_default/cross.stl` in a `default` build and nine files in an `--all-tolerances` build. Paths may not contain spaces; the script checks the file when it loads it and names every problem it finds.

### When you export a new part

1. Export it into `orca_slicer/` with the `combi_export` presets, save `Grip.blend` and commit the preset JSON files with it.
2. Add an item for it to a group, or a new group to the shapes that need it. If the part was listed as `missing`, replace `missing` with `file`.
3. Run `--check`. The part should no longer appear under "Files no print set uses", "Not exported yet" or "combi_export presets".
4. Update the print list in `orca_slicer/README.md`.

### The combi_export presets

When `Grip.blend` is saved, `combi_export` writes the presets of each scene to `<scene>_preset.json` next to it (its *Save JSON with File* tick, on by default). Besides the presets, the file lists under `exports` every file each preset writes, below the preset's root folder, named as the add-on names them:

```json
"root_dir": "D:\\Grip\\orca_slicer\\GripV\\",
"exports": {"complete": true, "presets": [{"name": "Buttons", "files": ["parts/buttons/default/button.stl", "..."]}]}
```

The builder matches a file to a shape folder by the end of its `root_dir` (`orca_slicer/GripV`, whatever the drive or folder above it), so the absolute paths of one computer work on any clone. It then compares the `.stl` files the print sets name with the list, and in a build it warns about any file of the release that no preset exports. A file without `exports`, or with `"complete": false` (combi_export stops listing after 5000 files), is not compared. OrcaSlicer projects are not exports and are never compared.

## Tests

```
python -m unittest discover tools/release
```

The tests build a small repository with fake Git LFS pointer files in a temporary folder. One test also runs `--check` on the real `orca_slicer/` when it is present.
