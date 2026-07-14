bl_info = {
    "name": "Batch STL Exporter (Multi-Collection, Presets & Control Node Group)",
    "author": "AI",
    "version": (5, 0),
    "blender": (4, 1, 0),
    "location": "View3D > Sidebar > Export",
    "description": (
        "Export collections to a dynamic root directory with relative sub-paths, switchable via "
        "global presets. Root directory tokens and active preset can be driven entirely by the "
        "exposed inputs of a named 'control' Geometry Nodes node group, independent of scene selection."
    ),
    "category": "Import-Export",
}

import os
import re
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


# --- CONTROL NODE GROUP INTEGRATION ---
#
# A single, named Geometry Nodes node group acts as a central "settings" block.
# Its exposed inputs are read directly from the node group's interface
# (NodeTreeInterfaceSocket.default_value), NOT from any modifier instance on
# any object. This means the values used are completely independent of what
# object (if any) is selected, or whether the node group is even applied to
# an object at all - it only needs to exist in bpy.data.node_groups.
#
# - Any {InputName} token in the Root Directory or a preset's Sub-folder Path
#   is replaced with that input's current default value.
# - One particular input (named via "Preset Selector Input") is used to pick
#   the active preset: a String value is matched against preset names
#   (case-insensitive), a numeric value is used directly as a preset index.

_PATH_TOKEN_RE = re.compile(r"\{([^{}]+)\}")
_INVALID_PATH_CHARS_RE = re.compile(r'[<>:"|?*]')


def get_control_nodegroup(scene):
    """Look up the control node group by name in bpy.data.node_groups. Returns None if unset/missing."""
    name = scene.batch_stl_control_nodegroup_name
    if not name:
        return None
    return bpy.data.node_groups.get(name)


def get_nodegroup_input_items(node_group):
    """Return the exposed INPUT socket interface items of a node group (empty list if none/invalid)."""
    items = []
    if not node_group:
        return items

    interface = getattr(node_group, "interface", None)
    if interface is None:
        return items

    for item in interface.items_tree:
        if item.item_type == 'SOCKET' and item.in_out == 'INPUT':
            items.append(item)

    return items


def get_nodegroup_input_value(node_group, input_name):
    """Return the interface default_value of the named exposed input, or None if not found."""
    for item in get_nodegroup_input_items(node_group):
        if item.name == input_name:
            return getattr(item, "default_value", None)
    return None


def sanitize_path_component(text):
    """Strip characters that are invalid in file/folder names on common filesystems."""
    text = _INVALID_PATH_CHARS_RE.sub("_", text)
    return text.strip()


def format_gn_value(value):
    """Convert a raw node-group input value into a filesystem-friendly string."""
    if value is None:
        return None

    if isinstance(value, bool):
        text = "true" if value else "false"
    elif isinstance(value, float):
        text = f"{value:.4f}".rstrip('0').rstrip('.')
        text = text if text else "0"
    elif isinstance(value, int):
        text = str(value)
    elif isinstance(value, str):
        text = value
    elif hasattr(value, "name"):
        # Object / Collection / Material / Image pointer inputs
        text = value.name
    elif hasattr(value, "__len__"):
        # Vector / Color / array inputs
        text = "_".join(format_gn_value(v) or "0" for v in value)
    else:
        text = str(value)

    return sanitize_path_component(text)


def resolve_path_template(template, node_group):
    """Replace every {InputName} token in template with the control node group's matching input value.

    Tokens with no matching input (or no node group configured) are left
    untouched so a missing/misspelled mapping is obvious rather than silently
    producing a wrong path.
    """
    if not template or "{" not in template:
        return template

    def _replace(match):
        input_name = match.group(1).strip()
        value = get_nodegroup_input_value(node_group, input_name)
        formatted = format_gn_value(value)
        return formatted if formatted is not None else match.group(0)

    return _PATH_TOKEN_RE.sub(_replace, template)


def sync_preset_from_control_nodegroup(scene):
    """Set the active preset index from the control node group's preset-selector input.

    Returns a human-readable status string, or None if there is nothing configured to sync from.
    """
    node_group = get_control_nodegroup(scene)
    if node_group is None:
        return None

    input_name = scene.batch_stl_preset_input_name
    if not input_name:
        return None

    value = get_nodegroup_input_value(node_group, input_name)
    if value is None:
        return f"Input '{input_name}' not found on node group '{node_group.name}'."

    presets = scene.batch_stl_presets
    if not presets:
        return "No presets exist to select."

    if isinstance(value, bool):
        index = 1 if value else 0
    elif isinstance(value, int):
        index = value
    elif isinstance(value, float):
        index = int(round(value))
    elif isinstance(value, str):
        index = next((i for i, p in enumerate(presets) if p.name.lower() == value.strip().lower()), None)
        if index is None:
            return f"No preset named '{value}' found."
    else:
        return f"Unsupported value type for preset selection: {type(value).__name__}"

    index = max(0, min(index, len(presets) - 1))
    scene.batch_stl_preset_index = index
    return f"Active preset set to '{presets[index].name}' (from '{input_name}' = {value})"


# --- PROPERTIES ---

class BatchSTLExportItem(bpy.types.PropertyGroup):
    """Group of properties representing a single collection -> sub-path mapping."""
    collection: bpy.props.PointerProperty(
        name="Collection",
        type=bpy.types.Collection,
        description="Select the root collection to export"
    )
    sub_path: bpy.props.StringProperty(
        name="Sub-folder Path",
        description=(
            "Relative path appended to the Root Directory (e.g., 'parts/gears/'). "
            "Supports {InputName} tokens, replaced with the value of a matching exposed input on "
            "the Control Node Group (e.g. 'parts/{Variant}/')"
        ),
        default="",
    )


class BatchSTLExportPreset(bpy.types.PropertyGroup):
    """A named, self-contained set of collection -> sub-path mappings.

    Presets are stored globally on the Scene, so any collection can be
    exported to a different sub-folder simply by switching the active preset -
    manually, or automatically via the Control Node Group.
    """
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
            new_item.collection = src_item.collection
            new_item.sub_path = src_item.sub_path

        scene.batch_stl_preset_index = len(scene.batch_stl_presets) - 1
        return {'FINISHED'}


class BATCH_STL_OT_sync_preset_from_nodegroup(bpy.types.Operator):
    bl_idname = "batch_stl.sync_preset_from_nodegroup"
    bl_label = "Sync Preset From Node Group"
    bl_description = "Set the active preset from the Control Node Group's preset-selector input right now"

    def execute(self, context):
        message = sync_preset_from_control_nodegroup(context.scene)
        if message is None:
            self.report({'WARNING'}, "No Control Node Group configured.")
        elif message.startswith("Active preset set"):
            self.report({'INFO'}, message)
        else:
            self.report({'WARNING'}, message)
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

    def execute(self, context):
        scene = context.scene

        # Ensure a root directory is set
        if not scene.batch_stl_root_dir:
            self.report({'ERROR'}, "Please select a Root Export Directory first.")
            return {"CANCELLED"}

        # Always re-sync the active preset from the Control Node Group first, so
        # export never depends on whatever was last clicked manually in the UI.
        sync_message = sync_preset_from_control_nodegroup(scene)
        if sync_message and not sync_message.startswith("Active preset set"):
            self.report({'WARNING'}, sync_message)

        preset = get_active_preset(scene)
        if preset is None:
            self.report({'ERROR'}, "No active export preset. Add a preset first.")
            return {"CANCELLED"}

        node_group = get_control_nodegroup(scene)

        # Root directory is resolved ONCE, from the control node group only -
        # never from the selected/active object.
        resolved_root = resolve_path_template(scene.batch_stl_root_dir, node_group)
        root_dir = bpy.path.abspath(resolved_root)

        if context.active_object and context.mode != "OBJECT":
            bpy.ops.object.mode_set(mode="OBJECT")

        total_exported = 0

        for item in preset.mappings:
            if not item.collection:
                continue

            # Sub-path is likewise resolved only from the control node group.
            resolved_sub = resolve_path_template(item.sub_path, node_group)
            out_dir = os.path.normpath(os.path.join(root_dir, resolved_sub))
            os.makedirs(out_dir, exist_ok=True)

            root_layer_coll = find_layer_collection(context.view_layer.layer_collection, item.collection.name)

            if not root_layer_coll:
                self.report({'WARNING'}, f"Collection '{item.collection.name}' not found in View Layer.")
                continue

            objects_to_export = get_enabled_objects_recursive(root_layer_coll)
            objects_to_export = list(set(objects_to_export))

            for obj in objects_to_export:
                bpy.ops.object.select_all(action="DESELECT")
                obj.select_set(True)

                filepath = os.path.join(out_dir, f"{bpy.path.clean_name(obj.name)}.stl")

                bpy.ops.wm.stl_export(filepath=filepath, export_selected_objects=True)
                total_exported += 1

        bpy.ops.object.select_all(action="DESELECT")
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
            if item.collection:
                layout.label(text=item.collection.name, icon='OUTLINER_COLLECTION')
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

        # --- Control Node Group section ---
        cn_box = layout.box()
        cn_box.label(text="Control Node Group:", icon='GEOMETRY_NODES')
        cn_box.prop_search(scene, "batch_stl_control_nodegroup_name", bpy.data, "node_groups", text="Node Group")
        cn_box.prop(scene, "batch_stl_preset_input_name", text="Preset Selector Input")
        cn_box.prop(scene, "batch_stl_auto_sync_preset", text="Auto-sync on Scene Update (best-effort)")

        node_group = get_control_nodegroup(scene)

        if scene.batch_stl_control_nodegroup_name and node_group is None:
            cn_box.label(text=f"Node group '{scene.batch_stl_control_nodegroup_name}' not found.", icon='ERROR')
        elif node_group is not None:
            if node_group.users == 0 and not node_group.use_fake_user:
                cn_box.label(text="0 users: enable Fake User or it may be purged on save!", icon='ERROR')

            input_items = get_nodegroup_input_items(node_group)
            if input_items:
                col = cn_box.column(align=True)
                col.label(text="Exposed inputs (usable as {tokens}):")
                for it in input_items:
                    value = getattr(it, "default_value", None)
                    col.label(text=f"  {{{it.name}}} = {value}")
            else:
                cn_box.label(text="This node group has no exposed inputs.")

            cn_box.operator("batch_stl.sync_preset_from_nodegroup", icon='FILE_REFRESH')

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
            sub_box.prop(active_item, "collection")
            sub_box.prop(active_item, "sub_path")

        layout.separator()
        layout.operator(
            EXPORT_OT_batch_stl_multi.bl_idname,
            text=f"Export Active Preset ({active_preset.name})",
            icon="EXPORT",
        )


# --- OPTIONAL AUTO-SYNC HANDLER ---
# Best-effort: Blender does not always fire depsgraph updates for a plain edit
# of a node group interface's default value (since it isn't evaluated
# geometry). The Sync button above, and the automatic sync that always runs
# right before Export, are the two mechanisms guaranteed to pick up changes.

def _batch_stl_auto_sync_handler(scene, depsgraph):
    try:
        if scene and scene.batch_stl_auto_sync_preset:
            sync_preset_from_control_nodegroup(scene)
    except Exception:
        # Never let a handler error spam the console on every depsgraph update.
        pass


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
    BATCH_STL_OT_sync_preset_from_nodegroup,
    EXPORT_OT_batch_stl_multi,
    VIEW3D_PT_batch_export_stl_multi,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    # Global root directory property (shared across all presets)
    bpy.types.Scene.batch_stl_root_dir = bpy.props.StringProperty(
        name="Root Export Directory",
        description=(
            "The base directory. Preset sub-paths will be added to this. "
            "Supports {InputName} tokens, replaced with the value of a matching exposed input on "
            "the Control Node Group (e.g. '//exports/{ProjectName}/')"
        ),
        default="//",
        subtype="DIR_PATH",
    )

    # Global presets, each holding its own collection -> sub-path mappings
    bpy.types.Scene.batch_stl_presets = bpy.props.CollectionProperty(type=BatchSTLExportPreset)
    bpy.types.Scene.batch_stl_preset_index = bpy.props.IntProperty(name="Active Preset Index", default=0)

    # Control node group settings
    bpy.types.Scene.batch_stl_control_nodegroup_name = bpy.props.StringProperty(
        name="Control Node Group",
        description=(
            "Name of a Geometry Nodes node group used purely as a settings/config source. Its "
            "exposed input default values drive path tokens and preset selection - independent of "
            "any object, modifier, or what is currently selected"
        ),
        default="",
    )
    bpy.types.Scene.batch_stl_preset_input_name = bpy.props.StringProperty(
        name="Preset Selector Input",
        description=(
            "Name of an exposed input on the Control Node Group whose value selects the active "
            "preset (a String input is matched against preset names; a numeric input is used "
            "directly as the preset index)"
        ),
        default="Preset",
    )
    bpy.types.Scene.batch_stl_auto_sync_preset = bpy.props.BoolProperty(
        name="Auto-sync Preset",
        description=(
            "Best-effort: try to keep the active preset in sync with the Control Node Group "
            "whenever the scene updates. Export always re-syncs regardless of this setting"
        ),
        default=False,
    )

    if _batch_stl_auto_sync_handler not in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.append(_batch_stl_auto_sync_handler)

def unregister():
    if _batch_stl_auto_sync_handler in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.remove(_batch_stl_auto_sync_handler)

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    del bpy.types.Scene.batch_stl_root_dir
    del bpy.types.Scene.batch_stl_presets
    del bpy.types.Scene.batch_stl_preset_index
    del bpy.types.Scene.batch_stl_control_nodegroup_name
    del bpy.types.Scene.batch_stl_preset_input_name
    del bpy.types.Scene.batch_stl_auto_sync_preset

if __name__ == "__main__":
    register()
