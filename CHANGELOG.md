# Changelog

Releases will be listed here, newest first, with what changed for people who print, customize or contribute. Until the first release, changes collect under "Unreleased".

## Unreleased

### Printed files

- Exported parts are sorted into tolerance folders (`tight`, `default`, `loose`, `cap_*`, `press_*`), so you can reprint only the part that does not fit.
- File names now match what the exporter writes, with underscores instead of spaces (`battery_cover.stl`, `dpad_stick_cap.stl`, …), on GripV and GripX. GripX triggers moved from `Xbox_style/` to `xbox_style/`.
- GripV exports the scroll wheel (`parts/scrollwheel/`) and the nut lock (`parts/misc/`).
- The GripX "Parts" preset no longer takes the capacitive part from the GripV settings. The GripX `capacitive_knob.stl` still has to be exported again.
- Design tuning: stick variants (including the Elite 2 stick base), triggers, face button, Select and Home caps, back screws, R4 and the GripX dualsense back case.

### Guides

- [Printing guide](docs/print-guide.md) (draft) and a [print list](orca_slicer/README.md) per shape: which files, how many and which tolerance folder.
- [Assembly guide](docs/assembly-guide.md) and [bill of materials](docs/bom.md) (drafts).
- [Documentation for Grip.blend](docs/blender/README.md): a guide to customizing and exporting parts, and a guide to the node system for contributors.
- [Roadmap](ROADMAP.md) and [contributing guide](CONTRIBUTING.md).

### Blender project

- `Grip.blend` needs Blender 5.2 or newer.
- Export presets (`combi_export`) and `blender/tracking.json`, which records every preset value on save (`blender_tracking`). Both extensions are in [`extensions/`](extensions/README.md).
- The **Grip** tab in the 3D Viewport sidebar (`grip_controls`) gathers the most used settings and keeps `variant` in step with the scene.
- `scripts/apply_tooltips.py` writes a tooltip for every input that `tracking.json` tracks: the global settings and every part's settings.
- `scripts/fix_names.py` fixes the typos in node group and input names (`wdith`, `paramters`, …) and updates the export presets that name them. It starts in a dry run that only lists the renames.

### Repository and tools

- Models, the Blender file and large images are stored with Git LFS. Clone the repository; "Download ZIP" gives pointer files.
- The full CC BY-NC-SA 4.0 licence text is in [LICENSE](LICENSE); the extensions are GPL.
- Issue forms for fit reports and problems.
- [orca_reload](tools/orca_reload/README.md) updates the parts in OrcaSlicer projects from the STL files in one run.
- [tracking_diff](tools/tracking_diff/README.md) lists the changes in `tracking.json` in readable form.
- [release](tools/release/README.md) checks `orca_slicer/` and packs one zip per shape for a release.
