# Extensions

Blender extensions used by Grip. All of them need Blender 5.2 or newer.

| Folder | What it does | Source |
|---|---|---|
| `combi_export/` | exports the STL files with the export presets | https://github.com/oleroma/combi_export |
| `blender_tracking/` | writes `blender/tracking.json` on every save | https://github.com/oleroma/blender-tracking |
| `grip_controls/` | the **Grip** tab in the 3D Viewport sidebar: the most used settings of Grip.blend in one place, and the variant sync. See its [README](grip_controls/README.md). | this repository |
| `orca_reload/` | the **Orca** tab: builds the Orca projects (plates, parts, nesting) from the exported STLs and paints the seams drawn as curves or edges. See its [README](orca_reload/README.md). Prototype. | this repository |

**`combi_export/` and `blender_tracking/` are synced, do not edit them here.** Each of those folders is overwritten automatically by a GitHub Action in its source repo whenever that repo's main branch changes. Change them in their own repositories.

**`grip_controls/` and `orca_reload/` live in Grip itself.** Edit them here, in pull requests to this repository. Their tests run with a Python that has the `bpy` module: `python -I extensions/grip_controls/tests/test_grip_controls.py`, and the ones in `orca_reload/tests/`.

## Use in Blender

Edit › Preferences › Get Extensions › Repositories (the drop-down at the top right) › **+** › Add Local Repository, then point it at this folder. All three extensions appear in the list; enable the ones you want. A `git pull` updates them, because Blender reads them straight from this folder (restart Blender afterwards).

## License

The add-ons here are GPL, not CC BY-NC-SA like the rest of Grip. Each folder carries its own `LICENSE` file: the synced ones copy it from their source repo with the same action, and `grip_controls/` and `orca_reload/` carry GPL 3.0 or later. The rest of the repository is under CC BY-NC-SA 4.0, see [LICENSE](../LICENSE).
