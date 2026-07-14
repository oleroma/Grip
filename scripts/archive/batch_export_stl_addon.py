bl_info = {
    "name": "Batch STL Exporter",
    "author": "AI",
    "version": (1, 2),
    "blender": (4, 1, 0),
    "location": "View3D > Sidebar > Export",
    "description": "Batch export objects from enabled collections to separate STL files.",
    "category": "Import-Export",
}

import os

import bpy


class BatchSTLExportProperties(bpy.types.PropertyGroup):
    export_dir: bpy.props.StringProperty(
        name="Folder",
        description="Choose a directory to export the STL files",
        default="//",
        subtype="DIR_PATH",
    )


class EXPORT_OT_batch_stl(bpy.types.Operator):
    bl_idname = "export_scene.batch_stl"
    bl_label = "Batch Export STLs"
    bl_description = "Export all objects in enabled collections as separate STL files"
    bl_options = {"REGISTER"}

    def execute(self, context):
        out_dir = bpy.path.abspath(context.scene.batch_stl_props.export_dir)
        os.makedirs(out_dir, exist_ok=True)

        if context.active_object and context.mode != "OBJECT":
            bpy.ops.object.mode_set(mode="OBJECT")

        bpy.ops.object.select_all(action="DESELECT")

        objects_to_export = [
            obj
            for obj in context.view_layer.objects
            if obj.type in {"MESH", "CURVE", "SURFACE", "META", "FONT"}
        ]

        for obj in objects_to_export:
            obj.select_set(True)

            filepath = os.path.join(out_dir, f"{bpy.path.clean_name(obj.name)}.stl")
            bpy.ops.wm.stl_export(filepath=filepath, export_selected_objects=True)

            obj.select_set(False)

        return {"FINISHED"}


class VIEW3D_PT_batch_export_stl(bpy.types.Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Export"
    bl_label = "Batch STL Export"

    def draw(self, context):
        layout = self.layout
        layout.prop(context.scene.batch_stl_props, "export_dir")
        layout.operator(
            EXPORT_OT_batch_stl.bl_idname, text="Export STLs", icon="EXPORT"
        )


classes = (
    BatchSTLExportProperties,
    EXPORT_OT_batch_stl,
    VIEW3D_PT_batch_export_stl,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.batch_stl_props = bpy.props.PointerProperty(
        type=BatchSTLExportProperties
    )


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.batch_stl_props


if __name__ == "__main__":
    register()
