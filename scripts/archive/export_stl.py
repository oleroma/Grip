import os

import bpy


def batch_export_stl():
    if bpy.context.active_object and bpy.context.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")

    blend_dir = os.path.dirname(bpy.data.filepath) if bpy.data.filepath else os.getcwd()
    out_dir = os.path.normpath(
        os.path.join(blend_dir, "..", "orca_bambu_A1_default", "stl")
    )
    os.makedirs(out_dir, exist_ok=True)

    bpy.ops.object.select_all(action="DESELECT")

    objects_to_export = [
        obj
        for obj in bpy.context.view_layer.objects
        if obj.type in {"MESH", "CURVE", "SURFACE", "META", "FONT"}
    ]

    for obj in objects_to_export:
        obj.select_set(True)

        filepath = os.path.join(out_dir, f"{bpy.path.clean_name(obj.name)}.stl")
        bpy.ops.wm.stl_export(filepath=filepath, export_selected_objects=True)

        obj.select_set(False)


if __name__ == "__main__":
    batch_export_stl()
