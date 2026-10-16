"""Orca Reload: an "Orca" tab in the 3D Viewport sidebar that reloads the STL parts of OrcaSlicer projects (.3mf)
and paints seams onto them from curves or marked edges, so the seams survive every reload.

reload3mf.py updates the projects (no bpy, also run by tools/orca_reload/orca_reload.py), seams.py turns seam lines
into Orca's seam painting (no bpy), blender_seams.py reads the seam lines from the scene, ui.py draws the tab.
See README.md.
"""
import sys

_MODULES = ("seams", "reload3mf", "blender_seams", "ui")

if "bpy" in locals():
    # Reload Scripts runs this file again but keeps the submodules: reload them too, dependencies first
    import importlib
    for _name in _MODULES:
        if f"{__name__}.{_name}" in sys.modules:
            importlib.reload(sys.modules[f"{__name__}.{_name}"])

import bpy

from . import ui


def register():
    for cls in ui.classes:
        bpy.utils.register_class(cls)
    ui.register_properties()


def unregister():
    ui.unregister_properties()
    for cls in reversed(ui.classes):
        try:
            bpy.utils.unregister_class(cls)
        except RuntimeError:
            pass
