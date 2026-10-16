# Contributing to Grip

Grip is in beta. The most useful help right now is printing parts and telling us how they fit.

## Report how a print fit

Use the [fit report form](https://github.com/oleroma/Grip/issues/new?template=fit-report.yml). Name the tolerance folders you printed (for example `buttons/default/cap_tight`), your printer and filament, and how each part fit. Photos help a lot. Fit reports are how the `default` tolerances get tuned.

For anything else that is wrong (a broken export, a part that does not assemble, a mistake in the docs) use the [problem form](https://github.com/oleroma/Grip/issues/new?template=problem.yml).

## Change Grip.blend

`blender/Grip.blend` is a binary file in Git LFS, so two changes to it cannot be merged. Open an issue first if you plan a larger change, so work does not overlap.

1. **Set up.** Clone with Git LFS ([readme](readme.md#lfs-and-file-download)) and use Blender 5.2 or newer. Add the [`extensions/`](extensions/README.md) folder as a local extension repository and enable `combi_export` and `blender_tracking` (and `grip_controls` if you want the Grip tab).
2. **Keep `blender_tracking` on.** On every save it rewrites `blender/tracking.json` with every preset value. That file is the only readable record of what changed in the `.blend`, so commit it together with the `.blend`.
3. **Make the change.** The [contributor guide](docs/blender/develop/README.md) explains how the file is built and what to check after a change.
4. **Review the `tracking.json` diff.** `python tools/tracking_diff/tracking_diff.py blender/tracking.json` lists what changed since your last commit ([Tracking diff](tools/tracking_diff/README.md)). Only the values you meant to change should be in it.
5. **Export** the affected parts with the `combi_export` presets, as described in [Exporting](docs/blender/customize/05-exporting.md). On every save `combi_export` rewrites `blender/GripV_preset.json` and `blender/GripX_preset.json`, with the files each preset exports, so commit them with the `.blend`. The release zips are made from those lists. `python tools/release/build_release.py --check` then shows any exported file that is missing from `orca_slicer/`, and any file there that no preset exports any more.
6. **Describe the change in the commit message:** what you changed, why, and which parts have to be reprinted. "upd" does not tell testers anything.

## Extensions

`extensions/combi_export` and `extensions/blender_tracking` are copied in automatically from their own repositories ([combi_export](https://github.com/oleroma/combi_export), [blender-tracking](https://github.com/oleroma/blender-tracking)). **Never edit them here by hand**: the next sync overwrites the change. Send changes to those repositories instead. `extensions/grip_controls` lives in Grip and is edited here; its [README](extensions/grip_controls/README.md) says how to test it.

## Scripts and tools

- `scripts/` holds Python scripts that run inside Blender on `Grip.blend` (Text Editor › Open › Run Script), for example `rename.py`, which names group nodes after their group, and `apply_tooltips.py`, which writes the tooltips.
- `tools/` holds stand-alone Python tools that work on the repository files without Blender: [tracking_diff](tools/tracking_diff/README.md) and [release](tools/release/README.md). They use the standard library only, so Blender's own Python can run them. Each has a README and tests: `python -m unittest discover tools/<tool>`.

## Licence

Grip is licensed under [CC BY-NC-SA 4.0](LICENSE). By sending a contribution (a pull request, a file or a design change) you agree that it is published under the same licence. The extensions in `extensions/` are GPL and carry their own licence files.
