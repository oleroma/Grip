# Tracking diff

Shows what changed in `blender/tracking.json` as a list people can read.

Every time `Grip.blend` is saved, the `blender_tracking` add-on rewrites `blender/tracking.json` with every preset value, so its git history records every design change. But the file is about 1 MB of JSON, and a commit message like "sticks upd" does not say which values moved. This tool reads two versions of the file and lists the differences by controller, preset group and node:

```
tracking.json: 906bf49 -> 99576f6
4 values changed.

GripV (custom ergonomic shape), panel GripV controls
  GripV stick L parameters
    grid texture parameters
      grid curvature offset: 10 -> 0 (-10)
    stick top parameters
      top curvature: "convex" -> "concave"

GripV and GripX, same change in both panels
  global
    global parameters
      style: "dualsense" -> "xbox"
      variant: "GripX" -> "GripV"  (working setting, the export presets set their own)
```

It reads the JSON only. It never opens `Grip.blend`, so it works on a clone without the Git LFS files.

## Use

You need Python 3.8 or newer, with no extra packages, and git for anything that names a commit. If Python is not installed on Windows, Blender's own Python works:
`"C:\Program Files\Blender Foundation\Blender 5.2\5.2\python\bin\python.exe"`.

The commands below run from the repository folder:

| Command | Shows |
| --- | --- |
| `python tools/tracking_diff/tracking_diff.py` | what the last commit changed (`HEAD~1` against `HEAD`); if it did not touch `tracking.json`, the report names the commit that last did |
| `python tools/tracking_diff/tracking_diff.py blender/tracking.json` | what you changed since your last commit (`HEAD` against the file on disk) |
| `python tools/tracking_diff/tracking_diff.py 99576f6` | what commit `99576f6` changed |
| `python tools/tracking_diff/tracking_diff.py d552c6d..d478402` | everything from one commit to another, as one list |
| `python tools/tracking_diff/tracking_diff.py main...my-branch` | what a branch changed since it left `main`, like a pull request |
| `python tools/tracking_diff/tracking_diff.py old.json new.json` | two files, for example two exports |
| `python tools/tracking_diff/tracking_diff.py --log 10` | one report per commit, for the last 10 commits that changed `tracking.json` |

| Option | What it does |
| --- | --- |
| `--markdown` | Writes Markdown with one table per preset group, for pull request descriptions and GitHub job summaries. |
| `--verbose` | Also lists every value of added and removed nodes, every added and removed link, and every relabeled node. |
| `--log N` | One report per commit, newest first, for the last `N` commits that changed the file (`0` lists them all). A range limits the commits: `--log 0 d552c6d..HEAD`. |
| `--path PATH` | Where the tracking file is inside the repository (default `blender/tracking.json`). |

The exit code is 0 whenever the comparison worked, whether or not anything changed, and 1 when it could not run (an unknown commit, a file that is not tracking data).

## Reading the report

The report starts with one line that counts the changes. Then come the sections in this order: GripV, GripX, changes shared by both, modifier inputs, meshes and node wiring. Sections without changes are left out.

**Values.** A changed input reads `name: old -> new`. Numbers also show the difference in brackets. The add-on rounds values to 4 decimals, so a change smaller than that never shows up. Checkboxes read `on` and `off`. Menu and text values are in quotes, so a trailing space stays visible (the `subdivision level` item is `"low "`, with a space). Vectors list the axes that moved: `translate: [22, 0, 0] -> [20, 0, 1.5] (X -2, Z +1.5)`. Names with a trailing or a double space are quoted for the same reason (`"GripV  lever R1L1"`).

**New and removed inputs and nodes.** These read `fresh: new input, 0.5`, `gone: removed, was 2` and `curve parameters: removed node, 6 inputs`. Add `--verbose` to see the values of a whole added or removed node.

**"probably renamed".** Keys in `tracking.json` are names, so a rename normally looks like one thing removed and another added. The tool pairs them up again when the old and the new name are alike and the values match: for inputs, the same value; for nodes, preset groups and the controls panels, the same inputs (inputs renamed along with them count) with at least half of the values equal; for node groups under node wiring, the same number of links. Treat it as a hint and check in Blender. A renamed node also lists the values that changed with the rename. This is what makes the diff of a name cleanup such as `scripts/fix_names.py` readable: it should list only renames. Link lines name nodes and sockets, so a renamed group node or input still shows under node wiring as links added and removed in the node groups that use it.

**"same change in both panels".** Both controls panels contain the group `global`, which is one node group, so a global setting changes in both at once. The tool shows such a change once instead of twice.

**`variant`.** The global `variant` only says which controller was shown when the file was saved. The export presets set it themselves, so a change of `variant` does not change any exported file.

**Meshes.** `meshes` holds a fingerprint of each basemesh: its placement in the scene (location, rotation, scale), its vertex positions and its topology. `basemesh GripV was edited` means the object was moved or its mesh changed. It does not say how. The note in brackets says which shape it is (`basemesh_X_style` is the GripX xbox shape, `basemesh_D_style` the dualsense shape).

**Node wiring.** `all_node_trees` lists the links of every node group in the file. The tool reports per node group how many links were added and removed, and which nodes are newly linked or no longer linked. It does not print the links themselves unless you add `--verbose`. A link that only changed because a node got a label counts as a relabel, not as rewiring, and groups where only labels changed share one line at the end.

**Format version.** When the `version` number of the file changed, the add-on changed how it writes the file. Some differences may then come from the add-on and not from the design.

## What it cannot see

The report is only as complete as `tracking.json`. The add-on is set to track the two controls panels one level deep, group nodes only, plus the basemesh collection. So it does not see:

- values of nodes that are not groups, such as the *Menu* node `stick menu` that picks a GripX stick preset (its link shows up under node wiring, its value does not);
- values inside a constructor group, which every preset shares;
- the `GripR1 controls` panel, object settings and the export presets (those have their own JSON files).

## In pull requests and on `main`

The workflow `.github/workflows/parameter-changes.yml` runs this tool for every pull request and every push to `main` that changes `blender/tracking.json`, and writes the Markdown report to the run's summary page (*Actions* tab, open the run, *Summary*). A pull request is compared from where it left its base branch. A push gets one section per commit that changed the file. The workflow is informational only: it never fails because values changed, and it does not comment on the pull request. It runs the tests below only when the tool itself changed.

To put the same list in a pull request description, run it on your branch and paste the output:

```
python tools/tracking_diff/tracking_diff.py --markdown main...HEAD
```

## Release notes

`--log` with a range gives one entry per commit, with its date, author and message, followed by what it changed. Start the range at the commit of the last release:

```
python tools/tracking_diff/tracking_diff.py --log 0 --markdown LAST_RELEASE_COMMIT..HEAD > changes.md
```

```
commit 99576f6  2026-10-12  olex
    sticks upd

    4 values changed.

    GripV (custom ergonomic shape), panel GripV controls
      GripV stick L parameters
        grid texture parameters
          grid curvature offset: 10 -> 0 (-10)
...
```

## Tests

```
python -m unittest discover tools/tracking_diff
```

The tests build small tracking files in memory and a throwaway git repository. They do not read the real `tracking.json`.
