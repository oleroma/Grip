"""The Orca tab in the 3D Viewport sidebar, laid out like Combi Export's: the roots, the Info panel, then one list
per level (projects, plates, parts), each with its buttons on the right, its counts below and the active item's
settings under that."""
import os

import bpy

from . import props

ICONS = {
    'PROJECT': 'FILE_3D', 'PLATE': 'MESH_GRID', 'PART': 'OBJECT_DATA', 'COPIES': 'DUPLICATE',
    'DIR': 'FILE_FOLDER', 'STL': 'MESH_DATA', 'BUILD': 'EXPORT', 'IMPORT': 'IMPORT', 'SEAM': 'CURVE_DATA',
    'GAP': 'ARROW_LEFTRIGHT', 'SETTINGS': 'PREFERENCES', 'INFO': 'INFO', 'CHECK_ON': 'CHECKBOX_HLT',
    'CHECK_OFF': 'CHECKBOX_DEHLT', 'ADD': 'ADD', 'DEL': 'TRASH', 'UP': 'TRIA_UP', 'DOWN': 'TRIA_DOWN',
    'COPY': 'COPYDOWN', 'PASTE': 'PASTEDOWN', 'RIGHT': 'TRIA_RIGHT', 'OPEN': 'TRIA_DOWN', 'ERROR': 'ERROR',
    'BLANK': 'BLANK1', 'TURN': 'DRIVER_ROTATIONAL_DIFFERENCE', 'UPAXIS': 'EMPTY_SINGLE_ARROW',
}

# Rows of a list: tall enough for its six buttons (the list scrolls beyond)
LIST_ROWS = 6
# Width of the labels before the root folder fields, in UI units
ROOT_LABEL_UNITS = 3.5
# Gap between a project row's Build button and its fields, in UI units
BUILD_BUTTON_GAP = 1.0


def draw_list_controls(layout, level):
    """The buttons of a list, as a column on its right: put it in the row that holds the template_list."""
    col = layout.column(align=True)
    col.operator_context = 'INVOKE_DEFAULT'
    for button in (('ADD', 'ADD'), ('REMOVE', 'DEL'), None, ('UP', 'UP'), ('DOWN', 'DOWN'), None,
                   ('COPY', 'COPY'), ('PASTE', 'PASTE')):
        if button is None:
            col.separator()
            continue
        op = col.operator("orca_reload.list_action", text="", icon=ICONS[button[1]])
        op.level, op.action = level, button[0]


def draw_stats(layout, stats):
    """A box with the counts of a level, centred."""
    row = layout.box().row()
    row.alignment = 'CENTER'
    for i, (value, icon) in enumerate(stats):
        if i:
            row.separator(factor=2.0)
        row.label(text=str(value), icon=ICONS[icon])


def draw_label_row(layout, label, units=ROOT_LABEL_UNITS):
    """A row with a right-aligned label of fixed width, for a field that follows."""
    row = layout.row()
    label_row = row.row()
    label_row.ui_units_x = units
    label_row.alignment = 'RIGHT'
    label_row.label(text=label)
    return row


def counts(projects):
    plates = [pl for pr in projects for pl in pr.plates]
    parts = [pa for pl in plates for pa in pl.parts]
    return len(plates), len(parts), sum(pa.copies for pa in parts if pa.use)


class ORCA_UL_projects(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        row = layout.row(align=True)
        row.operator("orca_reload.build", text="", icon=ICONS['BUILD']).index = index
        row.separator(factor=BUILD_BUTTON_GAP)
        row.prop(item, "use", text="", icon=ICONS['CHECK_ON'] if item.use else ICONS['CHECK_OFF'], emboss=False)
        row.prop(item, "name", text="", emboss=False)
        row.prop(item, "folder", text="", emboss=False, icon=ICONS['DIR'])


class ORCA_UL_plates(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        split = layout.split(factor=0.45)
        row = split.row(align=True)
        row.prop(item, "use", text="", icon=ICONS['CHECK_ON'] if item.use else ICONS['CHECK_OFF'], emboss=False)
        row.label(text="%d" % (index + 1))
        row.prop(item, "name", text="", emboss=False)
        tools = split.row(align=True)
        tools.label(text="", icon=ICONS['GAP'])
        tools.prop(item, "gap", text="", emboss=False)
        tools.separator(factor=0.5)
        tools.prop(item, "stl_folder", text="", emboss=False, icon=ICONS['DIR'])


class ORCA_UL_parts(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        settings = context.scene.orca_reload
        project = props.active_project(settings)
        plate = data
        split = layout.split(factor=0.45)
        row = split.row(align=True)
        row.prop(item, "use", text="", icon=ICONS['CHECK_ON'] if item.use else ICONS['CHECK_OFF'], emboss=False)
        row.prop(item, "name", text="", emboss=False)
        tools = split.row(align=True)
        if item.copies > 1:
            tools.label(text="x%d" % item.copies)
        tools.label(text="", icon=ICONS['SEAM'] if item.seam else ICONS['BLANK'])
        path = tools.row(align=True)
        path.alert = bool(item.path) and not os.path.isfile(props.part_path(context.scene, project, plate, item))
        path.prop(item, "path", text="", emboss=False, icon=ICONS['STL'])


class ORCA_UL_log(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        layout.label(text=item.text, icon=item.icon or ICONS['BLANK'])


class _OrcaPanel:
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Orca"


class VIEW3D_PT_orca_reload(_OrcaPanel, bpy.types.Panel):
    bl_label = "Orca Projects"

    def draw_header(self, context):
        self.layout.label(text="", icon=ICONS['BUILD'])

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        settings = scene.orca_reload

        row = draw_label_row(layout, "STL root:")
        row.prop(settings, "stl_root", text="")
        if not settings.stl_root:
            hint = draw_label_row(layout, "")
            hint.label(text=("Combi Export's root" if getattr(scene, "batch_stl_root_dir", "")
                             else "the .blend file's folder") + ": " + props.stl_root(scene))

        row = draw_label_row(layout, "3MF root:")
        row.prop(settings, "project_root", text="")
        buttons = row.row(align=True)
        buttons.operator("orca_reload.import_project", text="", icon=ICONS['IMPORT'])
        buttons.operator("orca_reload.build", text="", icon=ICONS['BUILD']).index = -1

        row = draw_label_row(layout, "Seams:")
        sub = row.row(align=True)
        sub.prop(settings, "seam_width", text="Width")
        sub.prop(settings, "snap_distance", text="Snap")


class VIEW3D_PT_orca_reload_info(_OrcaPanel, bpy.types.Panel):
    bl_label = "Info"
    bl_options = {'DEFAULT_CLOSED'}

    def draw_header(self, context):
        self.layout.label(text="", icon=ICONS['INFO'])

    def draw(self, context):
        layout = self.layout
        wm = context.window_manager
        row = layout.row()
        if len(wm.orca_reload_log):
            row.template_list("ORCA_UL_log", "", wm, "orca_reload_log", wm, "orca_reload_log_index", rows=8)
            tools = row.column(align=True)
            tools.operator("orca_reload.clear_log", text="", icon=ICONS['DEL'])
        else:
            row.label(text="No build yet. The log of the last build or import shows here.", icon=ICONS['INFO'])

        layout.separator()
        box = layout.box()
        header = box.row()
        header.prop(wm, "orca_reload_tips", text="", icon=ICONS['OPEN'] if wm.orca_reload_tips else ICONS['RIGHT'],
                    emboss=False)
        header.label(text="EXTENSION GUIDE", icon=ICONS['INFO'])
        if not wm.orca_reload_tips:
            return
        col = box.column()
        for title, icon, tips in GUIDE:
            col.label(text=title, icon=ICONS[icon])
            split = col.split(factor=0.05)
            split.column()
            child = split.column()
            for tip in tips:
                child.label(text="  • " + tip)
            col.separator()


GUIDE = (
    ("Projects › Plates › Parts:", 'PROJECT', (
        "A project is one 3MF file: 3MF root / Folder / Name.3mf",
        "Each ticked plate becomes an Orca plate, each ticked part goes on it",
        "A part's STL: STL root / project's STL folder / plate's STL folder / its path",
        "Red path: the STL is not there (export it with Combi Export first)",
    )),
    ("Placing:", 'UPAXIS', (
        "Up: the part's direction (in Blender) that points up on the plate; 0, 0, -1 flips it",
        "Turn: then turns it around that axis; Copies puts more of it on the plate",
        "Parts are nested by their footprint, largest first, Gap apart, centred on the plate",
    )),
    ("Building:", 'BUILD', (
        "Build (row button) writes that project, the Build button by the 3MF root all ticked ones",
        "A new project takes the printer, process and filament settings from Settings from",
        "An existing project keeps its settings, each part's settings (by name) and each plate's",
        "A part whose shape did not change keeps its painting from Orca",
        "Import: makes a project from an Orca 3MF, so Build updates that file",
    )),
    ("Seams:", 'SEAM', (
        "Pick a curve or mesh in a part's Seam field, drawn on the part's surface",
        "Curve: its splines · Mesh: edges marked as seam, or all edges of an edges-only mesh",
        "The line snaps onto the part within Snap, so one line serves tight, default and loose",
        "Orca puts the seam on the painted strip, Width wide, on every layer it crosses",
    )),
)


class VIEW3D_PT_orca_reload_projects(_OrcaPanel, bpy.types.Panel):
    bl_label = "Projects"

    def draw_header(self, context):
        self.layout.label(text="", icon=ICONS['PROJECT'])

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        settings = scene.orca_reload
        col = layout.column(align=True)
        row = col.box().row()
        row.template_list("ORCA_UL_projects", "", settings, "projects", settings, "project_index",
                          rows=LIST_ROWS, maxrows=LIST_ROWS)
        draw_list_controls(row, 'PROJECT')
        plates, parts, copies = counts(settings.projects)
        draw_stats(col, [(len(settings.projects), 'PROJECT'), (plates, 'PLATE'), (parts, 'PART'),
                         (copies, 'COPIES')])

        project = props.active_project(settings)
        if project is None:
            return
        box = layout.box()
        box.label(text=props.project_path(scene, project), icon=ICONS['PROJECT'])
        row = draw_label_row(box, "STL folder:")
        row.prop(project, "stl_folder", text="", icon=ICONS['DIR'])
        row = draw_label_row(box, "Settings from:")
        exists = os.path.isfile(props.project_path(scene, project))
        sub = row.row()
        sub.active = not exists
        sub.alert = not exists and not project.template
        sub.prop(project, "template", text="")
        if exists:
            draw_label_row(box, "").label(text="The project exists: its own settings are kept")


class VIEW3D_PT_orca_reload_plates(_OrcaPanel, bpy.types.Panel):
    bl_label = "Plates"

    @classmethod
    def poll(cls, context):
        return props.active_project(context.scene.orca_reload) is not None

    def draw_header(self, context):
        self.layout.label(text="", icon=ICONS['PLATE'])

    def draw(self, context):
        layout = self.layout
        project = props.active_project(context.scene.orca_reload)
        col = layout.column(align=True)
        row = col.box().row()
        row.template_list("ORCA_UL_plates", "", project, "plates", project, "plate_index",
                          rows=LIST_ROWS, maxrows=LIST_ROWS)
        draw_list_controls(row, 'PLATE')
        plates, parts, copies = counts([project])
        draw_stats(col, [(plates, 'PLATE'), (parts, 'PART'), (copies, 'COPIES')])


class VIEW3D_PT_orca_reload_parts(_OrcaPanel, bpy.types.Panel):
    bl_label = "Parts"

    @classmethod
    def poll(cls, context):
        return props.active_plate(props.active_project(context.scene.orca_reload)) is not None

    def draw_header(self, context):
        self.layout.label(text="", icon=ICONS['PART'])

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        project = props.active_project(scene.orca_reload)
        plate = props.active_plate(project)
        col = layout.column(align=True)
        row = col.box().row()
        row.template_list("ORCA_UL_parts", "", plate, "parts", plate, "part_index",
                          rows=LIST_ROWS, maxrows=LIST_ROWS)
        draw_list_controls(row, 'PART')
        used = [p for p in plate.parts if p.use]
        draw_stats(col, [(len(plate.parts), 'PART'), (sum(p.copies for p in used), 'COPIES'),
                         (sum(1 for p in used if p.seam), 'SEAM')])

        part = props.active_part(plate)
        if part is None:
            return
        box = layout.box()
        path = props.part_path(scene, project, plate, part) if part.path else ""
        row = box.row()
        row.alert = bool(path) and not os.path.isfile(path)
        row.label(text=path or "No STL file", icon=ICONS['STL'])
        row = draw_label_row(box, "STL:")
        row.prop(part, "path", text="")
        row.operator("orca_reload.browse_part", text="", icon=ICONS['DIR'])
        row = draw_label_row(box, "Up:")
        row.prop(part, "up", text="")
        row = draw_label_row(box, "Turn:")
        row.prop(part, "angle", text="")
        row.prop(part, "copies")
        row = draw_label_row(box, "Mirror:")
        row.prop(part, "mirror", text="")
        row = draw_label_row(box, "Seam:")
        row.prop(part, "seam", text="")


# Panels show in registration order
classes = (ORCA_UL_projects, ORCA_UL_plates, ORCA_UL_parts, ORCA_UL_log, VIEW3D_PT_orca_reload,
           VIEW3D_PT_orca_reload_info, VIEW3D_PT_orca_reload_projects, VIEW3D_PT_orca_reload_plates,
           VIEW3D_PT_orca_reload_parts)
