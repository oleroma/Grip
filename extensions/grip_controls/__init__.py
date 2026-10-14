"""Grip Controls: a "Grip" tab in the 3D Viewport sidebar with the settings of Grip.blend people change most.

resolve.py finds the node inputs (no drawing), ui.py draws them, sync.py keeps the global variant in step with the
scene shown. See README.md.
"""
import sys

_MODULES = ("resolve", "sync", "ui")

if "bpy" in locals():
    # Reload Scripts runs this file again but keeps the submodules: reload them too, dependencies first
    import importlib
    for _name in _MODULES:
        if f"{__name__}.{_name}" in sys.modules:
            importlib.reload(sys.modules[f"{__name__}.{_name}"])

import bpy

from . import sync, ui


def register():
    for cls in ui.classes:
        bpy.utils.register_class(cls)
    sync.register()


def unregister():
    sync.unregister()
    for cls in reversed(ui.classes):
        try:
            bpy.utils.unregister_class(cls)
        except RuntimeError:
            pass
