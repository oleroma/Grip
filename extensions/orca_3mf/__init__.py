"""Orca Reload: an "Orca" tab in the 3D Viewport sidebar that builds OrcaSlicer projects (.3mf) from projects > plates
> parts set up in Blender: each part an exported STL, stood on the plate by an up axis and a turn, nested with a gap,
and painted with the seam drawn on it as a curve or marked edges.

reload3mf.py reads and reloads projects (no bpy, also runs from the command line), layout.py places and
nests the parts, build3mf.py writes the projects, seams.py turns seam lines into Orca's seam painting (these four
without bpy). props.py holds what the .blend saves, blender_seams.py reads the seam lines, operators.py and ui.py make
the tab. See README.md.
"""
import sys

_MODULES = ("seams", "reload3mf", "layout", "build3mf", "props", "blender_seams", "operators", "ui")

if "bpy" in locals():
    # Reload Scripts runs this file again but keeps the submodules: reload them too, dependencies first
    import importlib
    for _name in _MODULES:
        if f"{__name__}.{_name}" in sys.modules:
            importlib.reload(sys.modules[f"{__name__}.{_name}"])

import bpy

from . import operators, props, ui

_CLASSES = props.classes + operators.classes + ui.classes


def register():
    for cls in _CLASSES:
        bpy.utils.register_class(cls)
    props.register_properties()


def unregister():
    props.unregister_properties()
    for cls in reversed(_CLASSES):
        try:
            bpy.utils.unregister_class(cls)
        except RuntimeError:
            pass
