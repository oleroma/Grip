bl_info = {
    "name": "Batch STL Exporter (Multi-Collection, Presets & Versioning)",
    "author": "AI",
    "version": (4, 1),
    "blender": (4, 1, 0),
    "location": "View3D > Sidebar > Export",
    "description": "Export collections to a dynamic root directory with relative sub-paths, switchable via global presets.",
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
    """Recursively gather all valid objects from a LayerCollection if it is enabled."""
    objects = []

    if layer_coll.exclude:
        return objects

    for obj in layer_coll.collection.objects:
        if obj.type in {"MESH", "CURVE", "SURFACE", "META", "FONT"}:
            objects.append(obj)

    for child in layer_coll.children:
        objects.extend(get_enabled_objects_recursive(child))

    return objects

def get_active_preset(scene):
    """Return the currently active BatchSTLExportPreset, or None if none exist."""
    presets = scene.batch_stl_presets
    index = scene.batch_stl_preset_index
    if presets and 0 <= index < len(presets):
        return presets[index]
    return None


# --- PROPERTIES ---

class BatchSTLExportItem(bpy.types.PropertyGroup):
    """Group of properties representing a single collection -> sub-path mapping."""

    # FIX: Use StringProperty instead of PointerProperty to prevent Depsgraph lag
    collection_name: bpy.props.StringProperty(
        name="Collection",
        description="Select the root collection to export",
        default=""
    )

    sub_path: bpy.props.StringProperty(
        name="Sub-folder Path",
        description="Relative path appended to the Root Directory (e.g., 'parts/gears/')",
        default="",
    )


class BatchSTLExportPreset(bpy.types.PropertyGroup):
    """A named, self-contained set of collection -> sub-path mappings."""
    name: bpy.props.StringProperty(
        name="Preset Name",
        default="New Preset",
    )
    mappings: bpy.props.CollectionProperty(type=BatchSTLExportItem)
    mapping_index: bpy.props.IntProperty(
        name="Active Mapping Index",
        default=0,
    )


# --- PRESET OPERATORS ---

class BATCH_STL_OT_add_preset(bpy.types.Operator):
    bl_idname = "batch_stl.add_preset"
    bl_label = "Add Export Preset"
    bl_description = "Add a new, empty export preset"

    def execute(self, context):
        scene = context.scene
        preset = scene.batch_stl_presets.add()
        preset.name = f"Preset {len(scene.batch_stl_presets)}"
        scene.batch_stl_preset_index = len(scene.batch_stl_presets) - 1
        return {'FINISHED'}


class BATCH_STL_OT_remove_preset(bpy.types.Operator):
    bl_idname = "batch_stl.remove_preset"
    bl_label = "Remove Export Preset"
    bl_description = "Remove the active export preset"

    @classmethod
    def poll(cls, context):
        return len(context.scene.batch_stl_presets) > 0

    def execute(self, context):
        scene = context.scene
        scene.batch_stl_presets.remove(scene.batch_stl_preset_index)
        scene.batch_stl_preset_index = min(
            max(0, scene.batch_stl_preset_index - 1),
            len(scene.batch_stl_presets) - 1,
        )
        return {'FINISHED'}


class BATCH_STL_OT_duplicate_preset(bpy.types.Operator):
    bl_idname = "batch_stl.duplicate_preset"
    bl_label = "Duplicate Export Preset"
    bl_description = "Duplicate the active preset, copying all of its collection/sub-path mappings"

    @classmethod
    def poll(cls, context):
        return get_active_preset(context.scene) is not None

    def execute(self, context):
        scene = context.scene
        source = get_active_preset(scene)
        if source is None:
            return {'CANCELLED'}

        new_preset = scene.batch_stl_presets.add()
        new_preset.name = f"{source.name} Copy"

        for src_item in source.mappings:
            new_item = new_preset.mappings.add()
            new_item.collection_name = src_item.collection_name
            new_item.sub_path = src_item.sub_path

        scene.batch_stl_preset_index = len(scene.batch_stl_presets) - 1
        return {'FINISHED'}


# --- MAPPING (COLLECTION / SUB-PATH) OPERATORS ---

class BATCH_STL_OT_add_item(bpy.types.Operator):
    bl_idname = "batch_stl.add_item"
    bl_label = "Add Export Mapping"
    bl_description = "Add a new collection to sub-path mapping to the active preset"

    @classmethod
    def poll(cls, context):
        return get_active_preset(context.scene) is not None

    def execute(self, context):
        preset = get_active_preset(context.scene)
        preset.mappings.add()
        preset.mapping_index = len(preset.mappings) - 1
        return {'FINISHED'}


class BATCH_STL_OT_remove_item(bpy.types.Operator):
    bl_idname = "batch_stl.remove_item"
    bl_label = "Remove Export Mapping"
    bl_description = "Remove the selected collection mapping from the active preset"

    @classmethod
    def poll(cls, context):
        preset = get_active_preset(context.scene)
        return preset is not None and len(preset.mappings) > 0

    def execute(self, context):
        preset = get_active_preset(context.scene)
        preset.mappings.remove(preset.mapping_index)
        preset.mapping_index = min(max(0, preset.mapping_index - 1), len(preset.mappings) - 1)
        return {'FINISHED'}


# --- EXPORT OPERATOR ---

class EXPORT_OT_batch_stl_multi(bpy.types.Operator):
    bl_idname = "export_scene.batch_stl_multi"
    bl_label = "Batch Export STLs"
    bl_description = "Export the active preset's mapped collections to the Root Directory + Sub-path"
    bl_options = {"REGISTER"}

    @classmethod
    def poll(cls, context):
        return get_active_preset(context.scene) is not None

    def execute(self, context):
        scene = context.scene

        if not scene.batch_stl_root_dir:
            self.report({'ERROR'}, "Please select a Root Export Directory first.")
            return {"CANCELLED"}

        preset = get_active_preset(scene)
        if preset is None:
            self.report({'ERROR'}, "No active export preset. Add a preset first.")
            return {"CANCELLED"}

        root_dir = bpy.path.abspath(scene.batch_stl_root_dir)

        if context.active_object and context.mode != "OBJECT":
            bpy.ops.object.mode_set(mode="OBJECT")

        # Save active selection state to restore later
        original_selected = context.selected_objects
        original_active = context.active_object

        total_exported = 0

        for item in preset.mappings:
            if not item.collection_name:
                continue

            if item.collection_name not in bpy.data.collections:
                self.report({'WARNING'}, f"Collection '{item.collection_name}' does not exist.")
                continue

            out_dir = os.path.normpath(os.path.join(root_dir, item.sub_path))
            os.makedirs(out_dir, exist_ok=True)

            root_layer_coll = find_layer_collection(context.view_layer.layer_collection, item.collection_name)

            if not root_layer_coll:
                self.report({'WARNING'}, f"Collection '{item.collection_name}' not found in View Layer.")
                continue

            objects_to_export = get_enabled_objects_recursive(root_layer_coll)
            objects_to_export = list(set(objects_to_export))

            for obj in objects_to_export:
                bpy.ops.object.select_all(action="DESELECT")
                obj.select_set(True)

                filepath = os.path.join(out_dir, f"{bpy.path.clean_name(obj.name)}.stl")

                bpy.ops.wm.stl_export(filepath=filepath, export_selected_objects=True)
                total_exported += 1

        # Restore original selection
        bpy.ops.object.select_all(action="DESELECT")
        for obj in original_selected:
            obj.select_set(True)
        if original_active:
            context.view_layer.objects.active = original_active

        self.report(
            {'INFO'},
            f"Successfully exported {total_exported} STLs using preset '{preset.name}' to {root_dir}",
        )
        return {"FINISHED"}


# --- UI LISTS ---

class BATCH_STL_UL_presets(bpy.types.UIList):
    """Custom UI List to draw the available export presets."""
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            row = layout.row(align=True)
            row.prop(item, "name", text="", emboss=False, icon='PRESET')
            row.label(text=f"{len(item.mappings)} mapping(s)")
        elif self.layout_type == 'GRID':
            layout.alignment = 'CENTER'
            layout.label(text="", icon='PRESET')


class BATCH_STL_UL_items(bpy.types.UIList):
    """Custom UI List to draw the collection/sub-path pairs for the active preset."""
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            if item.collection_name:
                layout.label(text=item.collection_name, icon='OUTLINER_COLLECTION')
                if item.sub_path:
                    layout.label(text=f"/{item.sub_path}", icon='FILE_FOLDER')
            else:
                layout.label(text="Assign a Collection", icon='ERROR')
        elif self.layout_type == 'GRID':
            layout.alignment = 'CENTER'
            layout.label(text="", icon='OUTLINER_COLLECTION')


# --- UI PANEL ---

class VIEW3D_PT_batch_export_stl_multi(bpy.types.Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Export"
    bl_label = "Batch STL Export"

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        # Global Root Directory at the top (shared by every preset)
        layout.prop(scene, "batch_stl_root_dir")
        layout.separator()

        # --- Presets section ---
        layout.label(text="Export Presets:", icon='PRESET')
        row = layout.row()
        row.template_list(
            "BATCH_STL_UL_presets", "",
            scene, "batch_stl_presets",
            scene, "batch_stl_preset_index",
            rows=3,
        )

        col = row.column(align=True)
        col.operator("batch_stl.add_preset", icon='ADD', text="")
        col.operator("batch_stl.remove_preset", icon='REMOVE', text="")
        col.separator()
        col.operator("batch_stl.duplicate_preset", icon='DUPLICATE', text="")

        layout.separator()

        active_preset = get_active_preset(scene)

        if active_preset is None:
            layout.label(text="Add a preset to begin.", icon='INFO')
            return

        # --- Mappings section (belongs to the active preset only) ---
        box = layout.box()
        box.label(text=f"Mappings for '{active_preset.name}':", icon='FILE_FOLDER')

        row = box.row()
        row.template_list(
            "BATCH_STL_UL_items", "",
            active_preset, "mappings",
            active_preset, "mapping_index",
            rows=4,
        )

        col = row.column(align=True)
        col.operator("batch_stl.add_item", icon='ADD', text="")
        col.operator("batch_stl.remove_item", icon='REMOVE', text="")

        if active_preset.mappings and 0 <= active_preset.mapping_index < len(active_preset.mappings):
            active_item = active_preset.mappings[active_preset.mapping_index]

            sub_box = box.box()
            # FIX: Use prop_search to populate a dropdown menu with scene collections, safely!
            sub_box.prop_search(active_item, "collection_name", bpy.data, "collections", text="Collection")
            sub_box.prop(active_item, "sub_path")

        layout.separator()
        layout.operator(
            EXPORT_OT_batch_stl_multi.bl_idname,
            text=f"Export Active Preset ({active_preset.name})",
            icon="EXPORT",
        )


# --- REGISTRATION ---

classes = (
    BatchSTLExportItem,
    BatchSTLExportPreset,
    BATCH_STL_UL_items,
    BATCH_STL_UL_presets,
    BATCH_STL_OT_add_item,
    BATCH_STL_OT_remove_item,
    BATCH_STL_OT_add_preset,
    BATCH_STL_OT_remove_preset,
    BATCH_STL_OT_duplicate_preset,
    EXPORT_OT_batch_stl_multi,
    VIEW3D_PT_batch_export_stl_multi,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.batch_stl_root_dir = bpy.props.StringProperty(
        name="Root Export Directory",
        description="The base directory. Preset sub-paths will be added to this.",
        default="//",
        subtype="DIR_PATH",
    )

    bpy.types.Scene.batch_stl_presets = bpy.props.CollectionProperty(type=BatchSTLExportPreset)
    bpy.types.Scene.batch_stl_preset_index = bpy.props.IntProperty(name="Active Preset Index", default=0)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    del bpy.types.Scene.batch_stl_root_dir
    del bpy.types.Scene.batch_stl_presets
    del bpy.types.Scene.batch_stl_preset_index

if __name__ == "__main__":
    register()
