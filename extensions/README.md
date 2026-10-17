# Extensions

Blender extensions used by Grip. All of them need Blender 5.2 or newer.

| Folder | What it does | Source |
|---|---|---|
| `combi_export/` | exports the STL files with the export presets | https://github.com/oleroma/combi_export |
| `blender_tracking/` | writes `blender/tracking.json` on every save | https://github.com/oleroma/blender-tracking |
| `grip_controls/` | the **Grip** tab in the 3D Viewport sidebar: the most used settings of Grip.blend in one place, and the variant sync | https://github.com/oleroma/grip_controls |
| `orca_3mf/` | the **Orca** tab: builds OrcaSlicer projects from plates and parts, with nesting and seams | https://github.com/oleroma/orca_3mf |

**All of these folders are synced, do not edit them here.** Each folder is overwritten automatically by a GitHub Action in its source repo whenever that repo's main (or master) branch changes. Change them in their own repositories, where their README and tests also live.

## Use in Blender

Edit › Preferences › Get Extensions › Repositories (the drop-down at the top right) › **+** › Add Local Repository, then point it at this folder. All the extensions appear in the list; enable the ones you want. A `git pull` updates them, because Blender reads them straight from this folder (restart Blender afterwards).

## License

The add-ons here are GPL, not CC BY-NC-SA like the rest of Grip. `combi_export/` and `blender_tracking/` carry their `LICENSE` file, copied from their source repo by the same action. `grip_controls/` and `orca_3mf/` are GPL 3.0, with the `LICENSE` file in their source repo. The rest of the repository is under CC BY-NC-SA 4.0, see [LICENSE](../LICENSE).
