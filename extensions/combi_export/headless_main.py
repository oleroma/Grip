"""Entry script of the headless export worker. The export operator starts it in a background Blender, on a copy of the
.blend file:

    blender --factory-startup --python-exit-code 1 -b <copy.blend> -P headless_main.py -- --batch-stl-headless <job.json>

Blender runs this file as a plain script, outside the package (so it cannot use relative imports), and --factory-startup
leaves the add-on disabled. The script therefore imports the package the way Blender imports extensions (load_package),
registers it and runs the job (headless.run_headless_export).

The standby worker (standby.py) starts with no file and `--standby` in place of the job file:

    blender --factory-startup --python-exit-code 1 -b -P headless_main.py -- --batch-stl-headless --standby

It prints BATCH_STL_READY once the package is registered, then reads one line from its input: a JSON list
[<copy.blend>, <job.json>]. It opens the copy and runs the job like a worker started on it. An empty input (Blender that
started it is gone) ends it.
"""
import importlib
import os
import sys

import bpy

# Module name of the extension repository the worker adds for the package's folder when no repository holds it
WORKER_REPO = "combi_export_worker"


def load_package():
    """Import the package this file belongs to as Blender imports an extension: bl_ext.<repository>.<folder>, through
    the extension repository whose directory holds its folder. With --factory-startup Blender knows its default
    repositories only (an install from the Extensions platform or from disk); for any other folder (a local repository,
    or the repository checkout in the tests) the worker adds one. --factory-startup never saves the preferences, so the
    added repository lives as long as the worker."""
    folder = os.path.dirname(os.path.abspath(__file__))
    parent = os.path.dirname(folder)
    repos = bpy.context.preferences.extensions.repos
    repo = next((r for r in repos if r.enabled and os.path.normcase(os.path.abspath(r.directory)) == os.path.normcase(parent)), None)
    if repo is None: repo = repos.new(name="Combi Export Worker", module=WORKER_REPO, custom_directory=parent)
    return importlib.import_module(f"bl_ext.{repo.module}.{os.path.basename(folder)}")


if __name__ == "__main__":
    package = load_package()
    if not hasattr(bpy.types.Scene, "batch_stl_root_dir"): package.register()
    headless = importlib.import_module(f"{package.__name__}.headless")
    job_path = sys.argv[sys.argv.index("--batch-stl-headless") + 1]
    if job_path == "--standby":
        import json
        print(importlib.import_module(f"{package.__name__}.standby").READY_LINE, flush=True)
        line = sys.stdin.readline()
        if not line.strip(): sys.exit(0)
        blend_path, job_path = json.loads(line)
        bpy.ops.wm.open_mainfile(filepath=blend_path)
    headless.run_headless_export(job_path)
