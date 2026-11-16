"""The Orca tab in the 3D Viewport sidebar, laid out like Combi Export's: the roots, the Info panel, then one list
per level (projects, plates, parts), each with its buttons on the right, its counts below and the active item's
settings under that."""
import os

import bpy

from . import combi, operators, props
from .props import BUILD_ALL, BUILD_IDLE

ICONS = {
    'PROJECT': 'FILE_3D', 'PLATE': 'MESH_GRID', 'PART': 'OBJECT_DATA', 'COPIES': 'DUPLICATE',
    'DIR': 'FILE_FOLDER', 'STL': 'MESH_DATA', 'BUILD': 'EXPORT', 'IMPORT': 'IMPORT', 'SEAM': 'CURVE_DATA',
    'GAP': 'ARROW_LEFTRIGHT', 'SETTINGS': 'PREFERENCES', 'INFO': 'INFO', 'CHECK_ON': 'CHECKBOX_HLT',
    'CHECK_OFF': 'CHECKBOX_DEHLT', 'ADD': 'ADD', 'DEL': 'TRASH', 'UP': 'TRIA_UP', 'DOWN': 'TRIA_DOWN',
    'COPY': 'COPYDOWN', 'PASTE': 'PASTEDOWN', 'RIGHT': 'TRIA_RIGHT', 'OPEN': 'TRIA_DOWN', 'ERROR': 'ERROR',
    'BLANK': 'BLANK1', 'CANCEL': 'CANCEL', 'TURN': 'DRIVER_ROTATIONAL_DIFFERENCE', 'UPAXIS': 'EMPTY_SINGLE_ARROW',
}

# Width of the copies column in the parts list (room for "x999"), in UI units
COPIES_UNITS = 1.8
PART_NAME_SPLIT = 0.3  # share of the row the part name gets; the rest is copies + path
# Width of the gap column in the plates list (icon and "12.5 mm"), in UI units
GAP_UNITS = 3.5
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


def draw_build_button(layout, index):
    """A Build button, or Cancel while this build runs (like Combi Export's export button); greyed out while
    another build runs."""
    if props.building() == index:
        layout.operator("orca_reload.cancel_build", text="", icon=ICONS['CANCEL'])
    else:
        sub = layout.row(align=True)
        sub.enabled = props.building() == BUILD_IDLE
        sub.operator("orca_reload.build", text="", icon=ICONS['BUILD']).index = index


def draw_progress(layout, wm):
    """The build's progress bar at the end of a row, like Combi Export's: Part 3/12 | 4.2s."""
    layout.prop(wm, "orca_reload_progress", text=wm.orca_reload_status, slider=True)


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
        # The build / cancel button leads the row, set apart from the project's fields by a gap
        draw_build_button(row, index)
        row.separator(factor=BUILD_BUTTON_GAP)
        fields = row.row(align=True)
        fields.enabled = props.building() == BUILD_IDLE
        fields.prop(item, "use", text="", icon=ICONS['CHECK_ON'] if item.use else ICONS['CHECK_OFF'], emboss=False)
        fields.prop(item, "name", text="", emboss=False)
        fields.prop(item, "folder", text="", emboss=False, icon=ICONS['DIR'])
        if props.building() == index:
            draw_progress(row, context.window_manager)


class ORCA_UL_plates(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        project = data
        # With plate names as folders the name takes all the room the narrow gap leaves; else it shares it with
        # the plate's STL folder
        split = layout if project.plate_paths else layout.split(factor=0.45)
        row = split.row(align=True)
        row.prop(item, "use", text="", icon=ICONS['CHECK_ON'] if item.use else ICONS['CHECK_OFF'], emboss=False)
        row.label(text="%d" % (index + 1))
        scene = context.scene
        no_folder = project.plate_paths and not os.path.isdir(props.plate_folder(scene, project, item))
        name = row.row(align=True)
        name.alert = no_folder
        if no_folder or operators.missing_parts(scene, project, item):
            # The warning is the plate's Relink button
            name.operator("orca_reload.relink", text="", icon='ERROR', emboss=False).plate = index
        elif project.plate_paths:  # the name is the plate's folder
            name.label(text="", icon=ICONS['DIR'])
        name.prop(item, "name", text="", emboss=False)
        tools = split.row(align=True)
        gap = tools.row(align=True)  # narrow: a gap is a short number
        gap.ui_units_x = GAP_UNITS
        gap.label(text="", icon=ICONS['GAP'])
        gap.prop(item, "gap", text="", emboss=False)
        if not project.plate_paths:
            tools.separator(factor=0.5)
            tools.prop(item, "stl_folder", text="", emboss=False, icon=ICONS['DIR'])


class ORCA_UL_parts(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        settings = context.scene.orca_reload
        project = props.active_project(settings)
        plate = data
        split = layout.split(factor=PART_NAME_SPLIT)
        row = split.row(align=True)
        row.prop(item, "use", text="", icon=ICONS['CHECK_ON'] if item.use else ICONS['CHECK_OFF'], emboss=False)
        row.prop(item, "name", text="", emboss=False)
        tools = split.row(align=True)
        copies = tools.row(align=True)  # a column of its own, so the paths line up
        copies.ui_units_x = COPIES_UNITS
        copies.alignment = 'RIGHT'
        copies.label(text="x%d" % item.copies if item.copies > 1 else "")
        tools.label(text="", icon=ICONS['SEAM'] if props.setup(item).seam else ICONS['BLANK'])
        level, _ = props.part_mark(context.scene, project, plate, item)
        path = tools.row(align=True)
        path.alert = level == 'ERROR'
        if level != 'NONE':  # the warning picks the part's file
            path.operator("orca_reload.browse_part", text="", icon='ERROR', emboss=False).part = index
            path.prop(item, "path", text="", emboss=False)
        else:
            path.prop(item, "path", text="", emboss=False, icon=ICONS['STL'])


class ORCA_UL_copies(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        row = layout.row(align=True)
        row.label(text="%d" % (index + 1))
        if not item.placed:
            row.label(text="placed by the next Build", icon=ICONS['BLANK'])
            return
        row.prop(item, "x", text="X", emboss=False)
        row.prop(item, "y", text="Y", emboss=False)
        row.prop(item, "turn", text="Turn", emboss=False)


class ORCA_UL_combi_files(bpy.types.UIList):
    """The files of a Combi preset in the Add from Combi window: tick, file name, its folder, its object."""

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        row = layout.row(align=True)
        sub = row.row(align=True)
        sub.enabled = not item.on_plate
        sub.prop(item, "pick", text="")
        sub.alert = not item.exists
        sub.label(text=item.name, icon=ICONS['STL'])
        folder = row.row()
        folder.enabled = False
        folder.label(text=item.shown or "-", icon=ICONS['DIR'])
        folder.label(text=item.object, icon='OBJECT_DATA')

    def filter_items(self, context, data, propname):
        # The filter field matches the file name or its folder; sorted as Combi lists them (by path)
        items = getattr(data, propname)
        flags = [self.bitflag_filter_item] * len(items)
        if self.filter_name:
            needle = self.filter_name.lower()
            flags = [self.bitflag_filter_item if needle in (i.shown + "/" + i.name).lower() else 0 for i in items]
        return flags, []


class ORCA_UL_log(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        layout.label(text=item.text, icon=item.icon or ICONS['BLANK'])


class _OrcaPanel:
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Orca3mf"


class VIEW3D_PT_orca_reload(_OrcaPanel, bpy.types.Panel):
    bl_label = "Orca Projects"

    def draw_header(self, context):
        self.layout.label(text="", icon=ICONS['BUILD'])

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        settings = scene.orca_reload

        row = draw_label_row(layout, "STL root:")
        field = row.row(align=True)
        field.prop(settings, "stl_root", text="")
        field.operator("orca_reload.browse_root", text="", icon=ICONS['DIR']).root = 'STL_ROOT'
        if not settings.stl_root:
            hint = draw_label_row(layout, "")
            where = props.blend_relative(props.stl_root(scene))  # from the .blend file's folder, like a root
            hint.label(text="Combi Export's root: " + where if getattr(scene, "batch_stl_root_dir", "")
                       else "the .blend file's folder" + ("" if where == "." else ": " + where))

        row = draw_label_row(layout, "3MF root:")
        field = row.row(align=True)
        field.enabled = props.building() == BUILD_IDLE
        field.prop(settings, "project_root", text="")
        field.operator("orca_reload.browse_root", text="", icon=ICONS['DIR']).root = 'PROJECT_ROOT'
        buttons = row.row(align=True)
        importing = buttons.row(align=True)
        importing.enabled = props.building() == BUILD_IDLE
        importing.operator("orca_reload.import_project", text="", icon=ICONS['IMPORT'])
        draw_build_button(buttons, BUILD_ALL)
        if props.building() == BUILD_ALL:
            draw_progress(row, context.window_manager)

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
        "Turn: then turns it around that axis",
        "Copies: each copy keeps its spot (X, Y, Turn), read on Import and recorded by Build",
        "A new copy or part is nested in free space, Gap apart, then keeps that spot",
    )),
    ("Building:", 'BUILD', (
        "Build (row button) writes that project, the Build button by the 3MF root all ticked ones",
        "While it builds, a progress bar ends the row; its Build button turns into Cancel",
        "Import saves the printer, plate and part settings in the .blend: the 3MF is not read again",
        "Update from 3MF: takes changes made in Orca back (start: the newest build)",
        "Without an import, the settings come from Settings from",
        "Meshes come from the STLs: Orca's painting, modifiers and layer heights are not kept",
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
        box.label(text=props.shown(scene, props.project_path(scene, project)), icon=ICONS['PROJECT'])
        row = draw_label_row(box, "STL folder:")
        row.prop(project, "stl_folder", text="", icon=ICONS['DIR'])
        row = draw_label_row(box, "Settings from:")
        exists = os.path.isfile(props.project_path(scene, project))
        sub = row.row(align=True)
        sub.prop(project, "template", text="")
        sub.operator("orca_reload.browse_template", text="", icon=ICONS['DIR'])
        sub.active = not project.profiles
        sub.alert = not project.profiles and not project.template
        if project.profiles:
            draw_label_row(box, "").label(text="Saved from " + (project.profiles_from or "the import"))
        row = draw_label_row(box, "Profiles:")
        row.operator("orca_reload.load_profiles", text="Load from 3MF", icon=ICONS['IMPORT'])
        row.operator("orca_reload.apply_preset", text="Apply preset", icon='PRESET')
        row = draw_label_row(box, "")
        row.operator("orca_reload.update_from_3mf", icon=ICONS['IMPORT'])
        if combi.available(scene) or project.combi_preset:
            row = draw_label_row(box, "Combi preset:")
            row.alert = bool(project.combi_preset) and combi.find_preset(scene, project.combi_preset) is None
            row.prop(project, "combi_preset_pick", text="")
            row = draw_label_row(box, "")
            row.enabled = bool(project.combi_preset)
            row.operator("orca_reload.update_from_combi", icon='FILE_REFRESH')
        row = draw_label_row(box, "")
        row.prop(project, "plate_paths")
        row = draw_label_row(box, "")
        row.operator("orca_reload.overwrite", text="Overwrite the 3MF", icon='CHECKBOX_HLT' if project.overwrite
                     else 'CHECKBOX_DEHLT', emboss=False)
        if exists and not project.overwrite:
            draw_label_row(box, "").label(text="Builds go to 3mf_builds, numbered")


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
                         (sum(1 for p in used if props.setup(p).seam), 'SEAM')])
        if project.combi_preset and combi.available(scene):
            layout.operator("orca_reload.add_from_combi", icon=ICONS['ADD'])
        missing = len(operators.missing_parts(scene, project, plate))
        if missing:
            row = layout.row()
            row.alert = True
            row.operator("orca_reload.relink", text="Relink %d missing part%s" % (missing, "" if missing == 1 else "s"),
                         icon=ICONS['DIR'])

        part = props.active_part(plate)
        if part is None:
            return
        box = layout.box()
        path = props.part_path(scene, project, plate, part) if part.path else ""
        level, why = props.part_mark(scene, project, plate, part)
        row = box.row()
        row.alert = level == 'ERROR'
        row.label(text=props.shown(scene, path) or "No STL file", icon=ICONS['STL'])
        if level != 'NONE':
            row = box.row()
            row.alert = level == 'ERROR'
            row.label(text=why, icon='ERROR')
        row = draw_label_row(box, "STL:")
        row.prop(part, "path", text="")
        row.operator("orca_reload.browse_part", text="", icon=ICONS['DIR'])
        setup = props.setup(part)
        if part.source is not None:
            row = draw_label_row(box, "Object:")
            row.label(text=part.source.name, icon='OBJECT_DATA')
            row.operator("orca_reload.own_setup", text="Own setup",
                         icon='CHECKBOX_HLT' if part.own else 'CHECKBOX_DEHLT', emboss=False)
            if not part.own:
                shared = props.sharing(scene, part.source)
                draw_label_row(box, "").label(text="Setup of %s, shared by %d part%s" % (
                    part.source.name, shared, "" if shared == 1 else "s"))
        row = draw_label_row(box, "Up:")
        row.prop(setup, "up", text="")
        row = draw_label_row(box, "Turn:")
        row.prop(setup, "angle", text="")
        row = draw_label_row(box, "Mirror:")
        row.prop(setup, "mirror", text="")
        row = draw_label_row(box, "Seam:")
        row.prop(setup, "seam", text="")
        row = draw_label_row(box, "Orca:")
        op = row.operator("orca_reload.object_setting", text="Add setting", icon=ICONS['ADD'])
        op.action = 'SET'
        for key, value in props.pairs(setup.orca_object):
            if key == "extruder":
                continue
            row = draw_label_row(box, "")
            op = row.operator("orca_reload.object_setting", text="%s = %s" % (key, value), emboss=False)
            op.action, op.key = 'SET', key
            op = row.operator("orca_reload.object_setting", text="", icon='X', emboss=False)
            op.action, op.key = 'REMOVE', key

        wm = context.window_manager
        header = box.row(align=True)
        header.prop(wm, "orca_reload_copies", text="", emboss=False,
                    icon=ICONS['OPEN'] if wm.orca_reload_copies else ICONS['RIGHT'])
        header.prop(part, "copies", text="Copies")
        header.operator("orca_reload.copy_action", text="", icon=ICONS['ADD']).action = 'ADD'
        header.operator("orca_reload.copy_action", text="", icon='REMOVE').action = 'REMOVE'
        header.operator("orca_reload.copy_action", text="", icon='FILE_REFRESH').action = 'NEST'
        if wm.orca_reload_copies:
            if not len(part.instances):
                box.label(text="Placed by the next Build")
            else:
                box.template_list("ORCA_UL_copies", "", part, "instances", part, "instance_index",
                                  rows=min(max(len(part.instances), 2), 8))


# Panels show in registration order
classes = (ORCA_UL_projects, ORCA_UL_plates, ORCA_UL_parts, ORCA_UL_copies, ORCA_UL_combi_files,
           ORCA_UL_log, VIEW3D_PT_orca_reload,
           VIEW3D_PT_orca_reload_info, VIEW3D_PT_orca_reload_projects, VIEW3D_PT_orca_reload_plates,
           VIEW3D_PT_orca_reload_parts)
