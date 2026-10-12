"""Entry script of the headless export worker. The export operator starts it in a background Blender, on a copy of the
.blend file:

    blender --factory-startup --python-exit-code 1 -b <copy.blend> -P headless_main.py -- --batch-stl-headless <job.json>

Blender runs this file as a plain script, outside the package (so it cannot use relative imports), and --factory-startup
leaves the add-on disabled. The script therefore imports the package from its own folder, registers it and runs the job
(headless.run_headless_export).
"""
import importlib
import importlib.util
import os
import sys


def load_package(name="combi_export"):
    """Import the package this file belongs to as `name`, so its modules import each other as usual."""
    folder = os.path.dirname(os.path.abspath(__file__))
    spec = importlib.util.spec_from_file_location(name, os.path.join(folder, "__init__.py"), submodule_search_locations=[folder])
    package = importlib.util.module_from_spec(spec)
    sys.modules[name] = package
    spec.loader.exec_module(package)
    return package


if __name__ == "__main__":
    import bpy
    package = load_package()
    if not hasattr(bpy.types.Scene, "batch_stl_root_dir"): package.register()
    headless = importlib.import_module(f"{package.__name__}.headless")
    headless.run_headless_export(sys.argv[sys.argv.index("--batch-stl-headless") + 1])
