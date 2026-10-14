"""The Grip tab in the 3D Viewport sidebar: panels, the match operator and the preferences.

Panels draw the real node input sockets, so an edit is a node edit: undo works and blender_tracking records it.
Drawing never writes and never raises; anything that cannot be found is shown as a greyed row.
"""
import functools

import bpy

from . import resolve, sync
from .resolve import Field, Selector

HINT_PREVIEW = "Keep both low while editing; the export presets raise them."


def safe_draw(draw):
    """Wraps a draw method so an unexpected error becomes a line in the panel instead of a traceback."""
    @functools.wraps(draw)
    def wrapper(self, context):
        try:
            draw(self, context)
        except Exception as e:
            self.layout.label(text=f"Could not draw: {e}", icon='ERROR')
    return wrapper


def safe_poll(test):
    try:
        return bool(test())
    except Exception:
        return False


def greyed(layout, text, icon='NONE'):
    row = layout.row()
    row.enabled = False
    row.label(text=text, icon=icon)


def split_row(layout):
    """A label column and a value column, like property split. Returns (label row, value layout)."""
    split = layout.split(factor=0.4, align=True)
    split.use_property_split = False
    label = split.row()
    label.alignment = 'RIGHT'
    return label, split


def draw_field(layout, field):
    """One input: an editable socket, or a greyed line when it is linked or missing.

    The label is a flat button whose tooltip is the input's description, so the tooltips written into the file
    show here too.
    """
    if field.socket is None:
        greyed(layout, f"{field.label}: {field.problem}")
    elif field.source:
        greyed(layout, f"{field.label}: set by {field.source}", 'LINKED')
    else:
        socket = field.socket
        label, value = split_row(layout)
        info = label.operator(GRIP_OT_input_info.bl_idname, text=field.label, emboss=False)
        info.tree, info.node, info.socket = socket.id_data.name, socket.node.name, socket.identifier
        value.prop(socket, "default_value", text="")


def draw_selector(layout, selector):
    if selector.data is None:
        greyed(layout, f"{selector.label}: {selector.problem}")
    else:
        label, value = split_row(layout)
        label.label(text=selector.label)
        value.prop(selector.data, selector.prop, text="")


def draw_global(layout, name, label=None):
    draw_field(layout, resolve.global_field(name, label))


def draw_block(layout, resolved):
    box = layout.box()
    box.label(text=resolved.title)
    col = box.column()
    for row in resolved.rows:
        if isinstance(row, Selector):
            draw_selector(col, row)
        elif isinstance(row, Field):
            draw_field(col, row)
    if resolved.where:
        greyed(box, resolved.where, 'NODETREE')


def draw_section(layout, section, variant, style):
    for text, alert in resolve.section_notes(section.key, variant):
        row = layout.row()
        row.alert = alert
        row.label(text=text, icon='ERROR' if alert else 'INFO')
    for block in section.blocks:
        draw_block(layout, resolve.resolve_block(block, variant, style))
    greyed(layout, f"More: {resolve.CONTROLS_PANELS.get(variant, 'controls panel')} > {section.frame}")


class GripPanel:
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Grip"


class GripFilePanel(GripPanel):
    """A panel that only shows in Grip.blend."""

    @classmethod
    def poll(cls, context):
        return safe_poll(resolve.is_grip_file)


class VIEW3D_PT_grip_controller(GripPanel, bpy.types.Panel):
    bl_label = "Controller"

    @safe_draw
    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        if not resolve.is_grip_file():
            col = layout.column(align=True)
            col.label(text="This tab is meant for Grip.blend.", icon='INFO')
            col.label(text="Open blender/Grip.blend from the Grip repository.")
            return

        variant = resolve.current_variant()
        draw_global(layout, "variant")
        row = layout.row()
        row.enabled = variant == "GripX"
        draw_global(row, "style")
        if variant not in resolve.VARIANTS:
            greyed(layout, f"{variant} is legacy; the tab covers GripV and GripX")

        draw_global(layout, "body type")
        body = layout.column()
        for name in resolve.body_inputs(variant, resolve.global_value("body type"), resolve.global_value("hollow top")):
            draw_global(body, name)

        layout.separator()
        target = resolve.variant_for_scene(context.scene.name) if context.scene else None
        col = layout.column()
        if target and target != variant:
            col.alert = True
            col.label(text=f"variant is not {target}, the scene shown", icon='ERROR')
        col.operator(GRIP_OT_match_variant.bl_idname, icon='FILE_REFRESH')
        prefs = sync.addon_prefs(context)
        if prefs is not None:
            layout.prop(prefs, "sync_variant")


class VIEW3D_PT_grip_preview(GripFilePanel, bpy.types.Panel):
    bl_label = "Preview quality"

    @safe_draw
    def draw(self, context):
        layout = self.layout
        for name in resolve.PREVIEW_INPUTS:
            draw_global(layout, name)
        greyed(layout, HINT_PREVIEW, 'INFO')
        body = resolve.global_value("body type")
        if body in ("hollow", "lattice") or (body == "standard" and resolve.global_value("hollow top")):
            greyed(layout, "Shell bodies take seconds to update.", 'TIME')


class VIEW3D_PT_grip_fit(GripFilePanel, bpy.types.Panel):
    bl_label = "Fit"

    @safe_draw
    def draw(self, context):
        layout = self.layout
        for name in resolve.FIT_INPUTS:
            draw_global(layout, name)
        greyed(layout, "Each part decides what tight, default and loose mean.", 'INFO')


class VIEW3D_PT_grip_features(GripFilePanel, bpy.types.Panel):
    bl_label = "Features"
    bl_options = {'DEFAULT_CLOSED'}

    @safe_draw
    def draw(self, context):
        layout = self.layout
        for name in resolve.FEATURE_INPUTS:
            row = layout.row()
            row.alert = name == "horizontal buttons" and resolve.global_value(name) is False
            draw_global(row, name)


class VIEW3D_PT_grip_parts(GripFilePanel, bpy.types.Panel):
    bl_label = "Parts"

    @safe_draw
    def draw(self, context):
        variant = resolve.current_variant()
        if variant not in resolve.VARIANTS:
            greyed(self.layout, f"No quick settings for {variant}.")
            return
        style = resolve.current_style()
        text = f"{variant} presets" + (f", {style} style" if style else "")
        self.layout.label(text=text, icon='PRESET')


class GripSectionPanel(GripPanel):
    bl_parent_id = "VIEW3D_PT_grip_parts"
    bl_options = {'DEFAULT_CLOSED'}
    section = ""

    @classmethod
    def poll(cls, context):
        return safe_poll(lambda: resolve.is_grip_file() and resolve.current_variant() in resolve.VARIANTS)

    @safe_draw
    def draw(self, context):
        section = resolve.SECTIONS_BY_KEY[self.section]
        draw_section(self.layout, section, resolve.current_variant(), resolve.current_style())


class VIEW3D_PT_grip_triggers(GripSectionPanel, bpy.types.Panel):
    bl_label = "Triggers"
    section = "triggers"


class VIEW3D_PT_grip_bumpers(GripSectionPanel, bpy.types.Panel):
    bl_label = "Bumpers"
    section = "bumpers"


class VIEW3D_PT_grip_sticks(GripSectionPanel, bpy.types.Panel):
    bl_label = "Sticks"
    section = "sticks"


class VIEW3D_PT_grip_buttons(GripSectionPanel, bpy.types.Panel):
    bl_label = "Buttons"
    section = "buttons"


class VIEW3D_PT_grip_battery(GripSectionPanel, bpy.types.Panel):
    bl_label = "Battery"
    section = "battery"


class GRIP_OT_match_variant(bpy.types.Operator):
    """Set the global variant to the scene you are looking at (GripV or GripX)"""
    bl_idname = "grip.match_variant"
    bl_label = "Match variant to scene"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        def test():
            target = resolve.variant_for_scene(context.scene.name)
            return resolve.is_grip_file() and target is not None and target != resolve.current_variant()
        return safe_poll(test)

    def execute(self, context):
        if not sync.sync_scene(context.scene):
            self.report({'WARNING'}, "variant not changed")
            return {'CANCELLED'}
        self.report({'INFO'}, f"variant set to {resolve.current_variant()}")
        return {'FINISHED'}


class GRIP_OT_input_info(bpy.types.Operator):
    """What this setting does"""
    bl_idname = "grip.input_info"
    bl_label = "About this setting"
    bl_options = {'INTERNAL'}

    tree: bpy.props.StringProperty()
    node: bpy.props.StringProperty()
    socket: bpy.props.StringProperty()

    @classmethod
    def description(cls, context, properties):
        socket = resolve.find_socket(properties.tree, properties.node, properties.socket)
        text = resolve.socket_description(socket) if socket is not None else ""
        return text or f"{properties.node} > {socket.name if socket else properties.socket}"

    def execute(self, context):
        socket = resolve.find_socket(self.tree, self.node, self.socket)
        text = resolve.socket_description(socket) if socket is not None else ""
        if text:
            self.report({'INFO'}, text)
        return {'FINISHED'}


def sync_toggled(prefs, context):
    """Turning the sync on matches the variant right away (a property update, never a draw)."""
    if prefs.sync_variant:
        try:
            sync.sync_scene(context.scene)
        except Exception as e:
            print(f"Grip Controls: variant sync failed: {e}")


class GripControlsPreferences(bpy.types.AddonPreferences):
    bl_idname = __package__

    sync_variant: bpy.props.BoolProperty(
        name="Keep variant in step with the scene",
        description="When you switch to the GripV or GripX scene, set the global variant to match",
        default=True,
        update=sync_toggled,
    )

    def draw(self, context):
        self.layout.prop(self, "sync_variant")


classes = (
    GripControlsPreferences,
    GRIP_OT_match_variant,
    GRIP_OT_input_info,
    VIEW3D_PT_grip_controller,
    VIEW3D_PT_grip_preview,
    VIEW3D_PT_grip_fit,
    VIEW3D_PT_grip_features,
    VIEW3D_PT_grip_parts,
    VIEW3D_PT_grip_triggers,
    VIEW3D_PT_grip_bumpers,
    VIEW3D_PT_grip_sticks,
    VIEW3D_PT_grip_buttons,
    VIEW3D_PT_grip_battery,
)
