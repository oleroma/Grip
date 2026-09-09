import os
import bpy
import struct

# --- FAST EXPORT FUNCTION ---

def write_fast_binary_stl(filepath, mesh, matrix_world):
    mesh.calc_loop_triangles()
    tris = mesh.loop_triangles

    if len(tris) == 0:
        return

    verts = [matrix_world @ v.co for v in mesh.vertices]
    mat_norm = matrix_world.to_3x3().inverted_safe().transposed()

    with open(filepath, 'wb') as f:
        f.write(b'Batch STL Fast Export' + b'\x00' * 59)
        f.write(struct.pack('<I', len(tris)))

        for tri in tris:
            n = (mat_norm @ tri.normal).normalized()
            f.write(struct.pack('<3f', n.x, n.y, n.z))

            for loop_idx in tri.vertices:
                v = verts[loop_idx]
                f.write(struct.pack('<3f', v.x, v.y, v.z))

            f.write(b'\x00\x00')

# --- HELPER FUNCTIONS ---

def find_layer_collection(layer_collection, collection_name):
    if layer_collection.collection.name == collection_name:
        return layer_collection
    for child in layer_collection.children:
        result = find_layer_collection(child, collection_name)
        if result:
            return result
    return None

def get_enabled_objects_recursive(layer_coll):
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
    presets = scene.batch_stl_presets
    index = scene.batch_stl_preset_index
    if presets and 0 <= index < len(presets):
        return presets[index]
    return None

# --- PROPERTIES ---

class BatchSTLExportItem(bpy.types.PropertyGroup):
    collection_name: bpy.props.StringProperty(
        name="Collection",
        default=""
    )
    sub_path: bpy.props.StringProperty(
        name="Sub-folder Path",
        default="",
    )

class BatchSTLNodeOverride(bpy.types.PropertyGroup):
    parent_group: bpy.props.StringProperty(
        name="Parent Node Group",
        description="The Node Group that contains the node you want to modify",
        default=""
    )
    node_name: bpy.props.StringProperty(
        name="Node Name",
        description="Exact name of the node instance (e.g., 'Group', 'Group.001', or custom name)",
        default=""
    )
    input_name: bpy.props.StringProperty(
        name="Input Name",
        description="Exact name of the input socket on the node instance",
        default=""
    )
    override_type: bpy.props.EnumProperty(
        name="Type",
        items=(
            ('BOOLEAN', "Boolean (Flag)", ""),
            ('INT', "Integer", ""),
            ('STRING', "String (Menu Entry)", ""),
        ),
        default='BOOLEAN'
    )
    value_bool: bpy.props.BoolProperty(name="Value", default=True)
    value_int: bpy.props.IntProperty(name="Value", default=0)
    value_string: bpy.props.StringProperty(name="Value", default="")

class BatchSTLExportPreset(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(name="Preset Name", default="New Preset")
    mappings: bpy.props.CollectionProperty(type=BatchSTLExportItem)
    mapping_index: bpy.props.IntProperty(default=0)
    node_overrides: bpy.props.CollectionProperty(type=BatchSTLNodeOverride)
    node_override_index: bpy.props.IntProperty(default=0)

# --- PRESET OPERATORS ---

class BATCH_STL_OT_add_preset(bpy.types.Operator):
    bl_idname = "batch_stl.add_preset"
    bl_label = "Add Export Preset"

    def execute(self, context):
        scene = context.scene
        preset = scene.batch_stl_presets.add()
        preset.name = f"Preset {len(scene.batch_stl_presets)}"
        scene.batch_stl_preset_index = len(scene.batch_stl_presets) - 1
        return {'FINISHED'}

class BATCH_STL_OT_remove_preset(bpy.types.Operator):
    bl_idname = "batch_stl.remove_preset"
    bl_label = "Remove Export Preset"

    @classmethod
    def poll(cls, context):
        return len(context.scene.batch_stl_presets) > 0

    def execute(self, context):
        scene = context.scene
        scene.batch_stl_presets.remove(scene.batch_stl_preset_index)
        scene.batch_stl_preset_index = min(max(0, scene.batch_stl_preset_index - 1), len(scene.batch_stl_presets) - 1)
        return {'FINISHED'}

# --- MAPPING & OVERRIDE OPERATORS ---

class BATCH_STL_OT_add_item(bpy.types.Operator):
    bl_idname = "batch_stl.add_item"
    bl_label = "Add Export Mapping"

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

    @classmethod
    def poll(cls, context):
        preset = get_active_preset(context.scene)
        return preset is not None and len(preset.mappings) > 0

    def execute(self, context):
        preset = get_active_preset(context.scene)
        preset.mappings.remove(preset.mapping_index)
        preset.mapping_index = min(max(0, preset.mapping_index - 1), len(preset.mappings) - 1)
        return {'FINISHED'}

class BATCH_STL_OT_add_override(bpy.types.Operator):
    bl_idname = "batch_stl.add_override"
    bl_label = "Add Node Override"

    @classmethod
    def poll(cls, context):
        return get_active_preset(context.scene) is not None

    def execute(self, context):
        preset = get_active_preset(context.scene)
        preset.node_overrides.add()
        preset.node_override_index = len(preset.node_overrides) - 1
        return {'FINISHED'}

class BATCH_STL_OT_remove_override(bpy.types.Operator):
    bl_idname = "batch_stl.remove_override"
    bl_label = "Remove Node Override"

    @classmethod
    def poll(cls, context):
        preset = get_active_preset(context.scene)
        return preset is not None and len(preset.node_overrides) > 0

    def execute(self, context):
        preset = get_active_preset(context.scene)
        preset.node_overrides.remove(preset.node_override_index)
        preset.node_override_index = min(max(0, preset.node_override_index - 1), len(preset.node_overrides) - 1)
        return {'FINISHED'}

# --- FAST EXPORT OPERATOR ---

class EXPORT_OT_batch_stl_multi(bpy.types.Operator):
    bl_idname = "export_scene.batch_stl_multi"
    bl_label = "Batch Export STLs"
    bl_options = {"REGISTER"}

    @classmethod
    def poll(cls, context):
        return get_active_preset(context.scene) is not None

    def execute(self, context):
        scene = context.scene
        preset = get_active_preset(scene)

        if not scene.batch_stl_root_dir:
            self.report({'ERROR'}, "Please select a Root Export Directory first.")
            return {"CANCELLED"}

        root_dir = bpy.path.abspath(scene.batch_stl_root_dir)

        if context.active_object and context.mode != "OBJECT":
            bpy.ops.object.mode_set(mode="OBJECT")

        # 1. Target exact node instances and apply overrides
        original_states = []
        for override in preset.node_overrides:
            if not override.parent_group or not override.node_name or not override.input_name:
                continue

            parent_tree = bpy.data.node_groups.get(override.parent_group)
            if not parent_tree:
                continue

            target_node = parent_tree.nodes.get(override.node_name)
            if not target_node:
                self.report({'WARNING'}, f"Node '{override.node_name}' not found in '{override.parent_group}'")
                continue

            socket = target_node.inputs.get(override.input_name)
            if not socket:
                self.report({'WARNING'}, f"Input '{override.input_name}' not found on node '{override.node_name}'")
                continue

            # Save current state
            original_states.append((socket, socket.default_value))

            # Apply override
            if override.override_type == 'BOOLEAN':
                socket.default_value = override.value_bool
            elif override.override_type == 'INT':
                socket.default_value = override.value_int
            elif override.override_type == 'STRING':
                socket.default_value = override.value_string

        if original_states:
            context.view_layer.update()

        total_exported = 0

        try:
            depsgraph = context.evaluated_depsgraph_get()

            # 2. Process Export Loop
            for item in preset.mappings:
                if not item.collection_name:
                    continue

                out_dir = os.path.normpath(os.path.join(root_dir, item.sub_path))
                os.makedirs(out_dir, exist_ok=True)

                root_layer_coll = find_layer_collection(context.view_layer.layer_collection, item.collection_name)
                if not root_layer_coll:
                    continue

                objects_to_export = list(set(get_enabled_objects_recursive(root_layer_coll)))

                for obj in objects_to_export:
                    obj_eval = obj.evaluated_get(depsgraph)
                    try:
                        mesh = obj_eval.to_mesh()
                    except RuntimeError:
                        continue

                    if not mesh:
                        continue

                    filepath = os.path.join(out_dir, f"{bpy.path.clean_name(obj.name)}.stl")
                    write_fast_binary_stl(filepath, mesh, obj.matrix_world)
                    obj_eval.to_mesh_clear()
                    total_exported += 1

        finally:
            # 3. Restore original node instance values
            for socket, original_val in original_states:
                socket.default_value = original_val

            if original_states:
                context.view_layer.update()

        self.report({'INFO'}, f"Successfully exported {total_exported} STLs")
        return {"FINISHED"}

# --- UI LISTS ---

class BATCH_STL_UL_presets(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        row = layout.row(align=True)
        row.prop(item, "name", text="", emboss=False, icon='PRESET')

class BATCH_STL_UL_items(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        if item.collection_name:
            layout.label(text=item.collection_name, icon='OUTLINER_COLLECTION')
            if item.sub_path:
                layout.label(text=f"/{item.sub_path}", icon='FILE_FOLDER')
        else:
            layout.label(text="Assign a Collection", icon='ERROR')

class BATCH_STL_UL_overrides(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        if item.parent_group and item.node_name and item.input_name:
            layout.label(text=f"{item.node_name} -> {item.input_name}", icon='NODETREE')
        else:
            layout.label(text="Unassigned Override", icon='ERROR')

# --- UI PANEL ---

class VIEW3D_PT_batch_export_stl_multi(bpy.types.Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Export"
    bl_label = "Fast Batch STL Export"

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        layout.prop(scene, "batch_stl_root_dir")
        layout.separator()

        layout.label(text="Export Presets:", icon='PRESET')
        row = layout.row()
        row.template_list("BATCH_STL_UL_presets", "", scene, "batch_stl_presets", scene, "batch_stl_preset_index", rows=3)

        col = row.column(align=True)
        col.operator("batch_stl.add_preset", icon='ADD', text="")
        col.operator("batch_stl.remove_preset", icon='REMOVE', text="")

        active_preset = get_active_preset(scene)
        if active_preset is None:
            return

        layout.separator()

        box = layout.box()
        box.label(text=f"Collections to Export:", icon='OUTLINER_COLLECTION')
        row = box.row()
        row.template_list("BATCH_STL_UL_items", "", active_preset, "mappings", active_preset, "mapping_index", rows=3)
        col = row.column(align=True)
        col.operator("batch_stl.add_item", icon='ADD', text="")
        col.operator("batch_stl.remove_item", icon='REMOVE', text="")

        if active_preset.mappings and 0 <= active_preset.mapping_index < len(active_preset.mappings):
            active_item = active_preset.mappings[active_preset.mapping_index]
            sub_box = box.box()
            sub_box.prop_search(active_item, "collection_name", bpy.data, "collections", text="Collection")
            sub_box.prop(active_item, "sub_path")

        layout.separator()

        obox = layout.box()
        obox.label(text=f"Node Instance Overrides:", icon='MODIFIER')
        row = obox.row()
        row.template_list("BATCH_STL_UL_overrides", "", active_preset, "node_overrides", active_preset, "node_override_index", rows=3)
        col = row.column(align=True)
        col.operator("batch_stl.add_override", icon='ADD', text="")
        col.operator("batch_stl.remove_override", icon='REMOVE', text="")

        if active_preset.node_overrides and 0 <= active_preset.node_override_index < len(active_preset.node_overrides):
            active_ovr = active_preset.node_overrides[active_preset.node_override_index]
            sub_obox = obox.box()
            sub_obox.prop_search(active_ovr, "parent_group", bpy.data, "node_groups", text="Parent Group")
            sub_obox.prop(active_ovr, "node_name", text="Node Name")
            sub_obox.prop(active_ovr, "input_name", text="Input Name")
            sub_obox.prop(active_ovr, "override_type", text="Type")

            if active_ovr.override_type == 'BOOLEAN':
                sub_obox.prop(active_ovr, "value_bool")
            elif active_ovr.override_type == 'INT':
                sub_obox.prop(active_ovr, "value_int")
            elif active_ovr.override_type == 'STRING':
                sub_obox.prop(active_ovr, "value_string")

        layout.separator()
        layout.operator(EXPORT_OT_batch_stl_multi.bl_idname, text=f"Export {active_preset.name}", icon="EXPORT")

# --- REGISTRATION ---

classes = (
    BatchSTLExportItem,
    BatchSTLNodeOverride,
    BatchSTLExportPreset,
    BATCH_STL_UL_items,
    BATCH_STL_UL_presets,
    BATCH_STL_UL_overrides,
    BATCH_STL_OT_add_item,
    BATCH_STL_OT_remove_item,
    BATCH_STL_OT_add_preset,
    BATCH_STL_OT_remove_preset,
    BATCH_STL_OT_add_override,
    BATCH_STL_OT_remove_override,
    EXPORT_OT_batch_stl_multi,
    VIEW3D_PT_batch_export_stl_multi,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.batch_stl_root_dir = bpy.props.StringProperty(
        name="Root Export Directory",
        default="//",
        subtype="DIR_PATH",
    )
    bpy.types.Scene.batch_stl_presets = bpy.props.CollectionProperty(type=BatchSTLExportPreset)
    bpy.types.Scene.batch_stl_preset_index = bpy.props.IntProperty(default=0)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    del bpy.types.Scene.batch_stl_root_dir
    del bpy.types.Scene.batch_stl_presets
    del bpy.types.Scene.batch_stl_preset_index
