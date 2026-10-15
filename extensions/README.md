# Extensions

Blender extensions used by Grip. All three need Blender 5.2 or newer.

| Folder | What it does | Source |
|---|---|---|
| `combi_export/` | exports the STL files with the export presets | https://github.com/oleroma/combi_export |
| `blender_tracking/` | writes `blender/tracking.json` on every save | https://github.com/oleroma/blender-tracking |
| `grip_controls/` | the **Grip** tab in the 3D Viewport sidebar: the most used settings of Grip.blend in one place, and the variant sync. See its [README](grip_controls/README.md). | this repository |

**`combi_export/` and `blender_tracking/` are synced, do not edit them here.** Each of those folders is overwritten automatically by a GitHub Action in its source repo whenever that repo's main branch changes. Change them in their own repositories.

**`grip_controls/` lives in Grip itself.** Edit it here, in pull requests to this repository. Its tests run with a Python that has the `bpy` module: `python -I extensions/grip_controls/tests/test_grip_controls.py`.

## Use in Blender

Edit › Preferences › Get Extensions › Repositories (the drop-down at the top right) › **+** › Add Local Repository, then point it at this folder. All three extensions appear in the list; enable the ones you want. A `git pull` updates them, because Blender reads them straight from this folder (restart Blender afterwards).

## License

The add-ons here are GPL, not CC BY-NC-SA like the rest of Grip. Each folder carries its own `LICENSE` file: the synced ones copy it from their source repo with the same action, and `grip_controls/` carries GPL 3.0 or later. The rest of the repository is under CC BY-NC-SA 4.0, see [LICENSE](../LICENSE).
