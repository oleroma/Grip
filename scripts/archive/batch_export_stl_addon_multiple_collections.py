bl_info = {
    "name": "Batch STL Exporter (Multi-Collection)",
    "author": "AI",
    "version": (2, 0),
    "blender": (4, 1, 0),
    "location": "View3D > Sidebar > Export",
    "description": "Export specific collections and their enabled children to designated folders.",
    "category": "Import-Export",
}

import os
import bpy


# --- HELPER FUNCTIONS ---

def find_layer_collection(layer_collection, collection_name):
    """Recursively search for a LayerCollection by its collection name."""
    if layer_collection.collection.name == collection_name:
        return layer_collection

    for child in layer_collection.children:
        result = find_layer_collection(child, collection_name)
        if result:
            return result

    return None

def get_enabled_objects_recursive(layer_coll):
    """Recursively gather all valid objects from a LayerCollection if it is enabled (unchecked)."""
    objects = []

    # If the collection is excluded (check mark is off in the outliner), skip it entirely
    if layer_coll.exclude:
        return objects

    # Grab valid objects in the current collection
    for obj in layer_coll.collection.objects:
        if obj.type in {"MESH", "CURVE", "SURFACE", "META", "FONT"}:
            objects.append(obj)

    # Recursively check children
    for child in layer_coll.children:
        objects.extend(get_enabled_objects_recursive(child))

    return objects


# --- PROPERTIES ---

class BatchSTLExportItem(bpy.types.PropertyGroup):
    """Group of properties representing a single export mapping."""
    collection: bpy.props.PointerProperty(
        name="Collection",
        type=bpy.types.Collection,
        description="Select the root collection to export"
    )
    export_dir: bpy.props.StringProperty(
        name="Folder",
        description="Choose a directory to export the STLs for this collection",
        default="//",
        subtype="DIR_PATH",
    )


# --- OPERATORS ---

class BATCH_STL_OT_add_item(bpy.types.Operator):
    bl_idname = "batch_stl.add_item"
    bl_label = "Add Export Mapping"
    bl_description = "Add a new collection to folder mapping"

    def execute(self, context):
        context.scene.batch_stl_items.add()
        context.scene.batch_stl_index = len(context.scene.batch_stl_items) - 1
        return {'FINISHED'}


class BATCH_STL_OT_remove_item(bpy.types.Operator):
    bl_idname = "batch_stl.remove_item"
    bl_label = "Remove Export Mapping"
    bl_description = "Remove the selected collection mapping"

    def execute(self, context):
        scene = context.scene
        if scene.batch_stl_items:
            scene.batch_stl_items.remove(scene.batch_stl_index)
            scene.batch_stl_index = min(max(0, scene.batch_stl_index - 1), len(scene.batch_stl_items) - 1)
        return {'FINISHED'}


class EXPORT_OT_batch_stl_multi(bpy.types.Operator):
    bl_idname = "export_scene.batch_stl_multi"
    bl_label = "Batch Export Mapped STLs"
    bl_description = "Export all mapped collections to their respective folders"
    bl_options = {"REGISTER"}

    def execute(self, context):
        if context.active_object and context.mode != "OBJECT":
            bpy.ops.object.mode_set(mode="OBJECT")

        total_exported = 0

        for item in context.scene.batch_stl_items:
            # Skip incomplete entries
            if not item.collection or not item.export_dir:
                continue

            out_dir = bpy.path.abspath(item.export_dir)
            os.makedirs(out_dir, exist_ok=True)

            # Find the layer collection for the assigned target collection
            root_layer_coll = find_layer_collection(context.view_layer.layer_collection, item.collection.name)

            if not root_layer_coll:
                self.report({'WARNING'}, f"Collection '{item.collection.name}' not found in View Layer.")
                continue

            # Gather all objects recursively
            objects_to_export = get_enabled_objects_recursive(root_layer_coll)

            # Deduplicate objects (in case an object is linked to multiple nested collections)
            objects_to_export = list(set(objects_to_export))

            # Export process
            for obj in objects_to_export:
                bpy.ops.object.select_all(action="DESELECT")
                obj.select_set(True)

                filepath = os.path.join(out_dir, f"{bpy.path.clean_name(obj.name)}.stl")

                # Using the newer experimental C++ STL exporter
                bpy.ops.wm.stl_export(filepath=filepath, export_selected_objects=True)
                total_exported += 1

        # Clean up selection state
        bpy.ops.object.select_all(action="DESELECT")

        self.report({'INFO'}, f"Successfully exported {total_exported} STLs.")
        return {"FINISHED"}


# --- UI PANEL ---

class BATCH_STL_UL_items(bpy.types.UIList):
    """Custom UI List to draw the collection/folder pairs."""
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            if item.collection:
                layout.label(text=item.collection.name, icon='OUTLINER_COLLECTION')
            else:
                layout.label(text="Assign a Collection", icon='ERROR')
        elif self.layout_type == 'GRID':
            layout.alignment = 'CENTER'
            layout.label(text="", icon='OUTLINER_COLLECTION')


class VIEW3D_PT_batch_export_stl_multi(bpy.types.Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Export"
    bl_label = "Batch STL Export"

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        # The dynamic list UI
        row = layout.row()
        row.template_list("BATCH_STL_UL_items", "", scene, "batch_stl_items", scene, "batch_stl_index", rows=3)

        # Add / Remove Buttons
        col = row.column(align=True)
        col.operator("batch_stl.add_item", icon='ADD', text="")
        col.operator("batch_stl.remove_item", icon='REMOVE', text="")

        # Details for the currently selected item in the list
        if scene.batch_stl_items and scene.batch_stl_index >= 0 and scene.batch_stl_index < len(scene.batch_stl_items):
            active_item = scene.batch_stl_items[scene.batch_stl_index]

            box = layout.box()
            box.prop(active_item, "collection")
            box.prop(active_item, "export_dir")

        layout.separator()
        layout.operator(EXPORT_OT_batch_stl_multi.bl_idname, text="Export All Mapped STLs", icon="EXPORT")


# --- REGISTRATION ---

classes = (
    BatchSTLExportItem,
    BATCH_STL_UL_items,
    BATCH_STL_OT_add_item,
    BATCH_STL_OT_remove_item,
    EXPORT_OT_batch_stl_multi,
    VIEW3D_PT_batch_export_stl_multi,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.batch_stl_items = bpy.props.CollectionProperty(type=BatchSTLExportItem)
    bpy.types.Scene.batch_stl_index = bpy.props.IntProperty(name="Active Item Index", default=0)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    del bpy.types.Scene.batch_stl_items
    del bpy.types.Scene.batch_stl_index

if __name__ == "__main__":
    register()
