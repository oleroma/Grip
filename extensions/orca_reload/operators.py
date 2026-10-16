"""Operators of the Orca tab: the list buttons, adding STLs, importing a project and Build."""
import os
import zipfile
import xml.etree.ElementTree as ET

import bpy

from . import blender_seams, build3mf, props, reload3mf, seams

REPORT_TEXT = "Orca build report"

LEVELS = (('PROJECT', "Project", ""), ('PLATE', "Plate", ""), ('PART', "Part", ""))
ACTIONS = (('ADD', "", ""), ('REMOVE', "", ""), ('UP', "", ""), ('DOWN', "", ""), ('COPY', "", ""),
           ('PASTE', "", ""))
_clipboard = {}


def level_list(settings, level):
    """(owner, collection name, index name) of a level's list, or None when its parent is not there."""
    project = props.active_project(settings)
    plate = props.active_plate(project)
    if level == 'PROJECT':
        return settings, "projects", "project_index"
    if level == 'PLATE':
        return (project, "plates", "plate_index") if project else None
    return (plate, "parts", "part_index") if plate else None


class ORCA_OT_list_action(bpy.types.Operator):
    bl_idname = "orca_reload.list_action"
    bl_label = "List Action"
    bl_options = {'UNDO', 'INTERNAL'}
    level: bpy.props.EnumProperty(items=LEVELS)
    action: bpy.props.EnumProperty(items=ACTIONS)
    shift: bpy.props.BoolProperty(options={'HIDDEN', 'SKIP_SAVE'})

    @classmethod
    def description(cls, context, properties):
        what = properties.level.lower()
        return {
            'ADD': "Add STL files to the plate (Shift: an empty part)" if properties.level == 'PART'
            else "Add a %s" % what,
            'REMOVE': "Remove the active %s" % what,
            'UP': "Move the %s up (Shift: to the top)" % what,
            'DOWN': "Move the %s down (Shift: to the bottom)" % what,
            'COPY': "Copy the active %s" % what,
            'PASTE': "Paste the copied %s" % what,
        }[properties.action]

    def invoke(self, context, event):
        self.shift = event.shift
        if self.level == 'PART' and self.action == 'ADD' and not self.shift:
            return bpy.ops.orca_reload.add_parts('INVOKE_DEFAULT')
        return self.execute(context)

    def execute(self, context):
        found = level_list(context.scene.orca_reload, self.level)
        if found is None:
            return {'CANCELLED'}
        owner, name, index_name = found
        lst, index = getattr(owner, name), getattr(owner, index_name)
        new = index
        if self.action == 'ADD':
            item = lst.add()
            if self.level == 'PROJECT':
                _new_project(context.scene, item, props.active(lst, index))
            elif self.level == 'PLATE':
                item.name = "Plate %d" % len(lst)
            new = len(lst) - 1
        elif self.action == 'REMOVE' and 0 <= index < len(lst):
            lst.remove(index)
            new = max(0, min(index, len(lst) - 1))
        elif self.action == 'UP' and 0 < index < len(lst):
            new = 0 if self.shift else index - 1
            lst.move(index, new)
        elif self.action == 'DOWN' and 0 <= index < len(lst) - 1:
            new = len(lst) - 1 if self.shift else index + 1
            lst.move(index, new)
        elif self.action == 'COPY' and 0 <= index < len(lst):
            _clipboard[self.level] = props.to_dict(lst[index])
        elif self.action == 'PASTE' and _clipboard.get(self.level):
            props.from_dict(lst.add(), _clipboard[self.level])
            new = len(lst) - 1
        setattr(owner, index_name, new)
        return {'FINISHED'}


def _new_project(scene, project, previous):
    """A new project starts with one plate and the printer settings of the project before it."""
    project.name = "project_%d" % len(scene.orca_reload.projects)
    project.plates.add().name = "Plate 1"
    if previous is not None:
        project.folder = previous.folder
        project.stl_folder = previous.stl_folder
        if previous.template:
            project.template = previous.template
        elif os.path.isfile(props.project_path(scene, previous)):
            project.template = _blend_relative(props.project_path(scene, previous))


def _blend_relative(path):
    try:
        return bpy.path.relpath(path) if bpy.data.filepath else path
    except ValueError:  # another drive
        return path


def _stl_browser(operator, context, folder):
    operator.directory = folder + os.sep if os.path.isdir(folder) else ""
    context.window_manager.fileselect_add(operator)
    return {'RUNNING_MODAL'}


class ORCA_OT_add_parts(bpy.types.Operator):
    bl_idname = "orca_reload.add_parts"
    bl_label = "Add STL Files"
    bl_description = "Add STL files to the active plate, one part each"
    bl_options = {'UNDO', 'INTERNAL'}
    directory: bpy.props.StringProperty(subtype='DIR_PATH', options={'SKIP_SAVE'})
    files: bpy.props.CollectionProperty(type=bpy.types.OperatorFileListElement, options={'SKIP_SAVE'})
    filter_glob: bpy.props.StringProperty(default="*.stl", options={'HIDDEN'})

    @classmethod
    def poll(cls, context):
        return props.active_plate(props.active_project(context.scene.orca_reload)) is not None

    def invoke(self, context, event):
        settings = context.scene.orca_reload
        project = props.active_project(settings)
        return _stl_browser(self, context, props.plate_folder(context.scene, project, props.active_plate(project)))

    def execute(self, context):
        settings = context.scene.orca_reload
        project = props.active_project(settings)
        plate = props.active_plate(project)
        base = props.plate_folder(context.scene, project, plate)
        names = sorted(f.name for f in self.files if f.name.lower().endswith(".stl"))
        for name in names:
            part = plate.parts.add()
            part.path = props.relative_to(os.path.join(self.directory, name), base)
            part.name = name
        if names:
            plate.part_index = len(plate.parts) - 1
        return {'FINISHED'}


class ORCA_OT_browse_part(bpy.types.Operator):
    bl_idname = "orca_reload.browse_part"
    bl_label = "Pick STL"
    bl_description = "Pick the active part's STL file"
    bl_options = {'UNDO', 'INTERNAL'}
    filepath: bpy.props.StringProperty(subtype='FILE_PATH', options={'SKIP_SAVE'})
    directory: bpy.props.StringProperty(subtype='DIR_PATH', options={'SKIP_SAVE'})
    filter_glob: bpy.props.StringProperty(default="*.stl", options={'HIDDEN'})

    def invoke(self, context, event):
        settings = context.scene.orca_reload
        project = props.active_project(settings)
        plate = props.active_plate(project)
        part = props.active_part(plate)
        if part is None:
            return {'CANCELLED'}
        current = props.part_path(context.scene, project, plate, part) if part.path else ""
        if current:
            self.filepath = current
        return _stl_browser(self, context, os.path.dirname(current) if current else
                            props.plate_folder(context.scene, project, plate))

    def execute(self, context):
        settings = context.scene.orca_reload
        project = props.active_project(settings)
        plate = props.active_plate(project)
        part = props.active_part(plate)
        if part is None or not self.filepath:
            return {'CANCELLED'}
        old_file = os.path.basename(part.path.replace("\\", "/"))
        part.path = props.relative_to(os.path.normpath(self.filepath), props.plate_folder(context.scene, project, plate))
        if not part.name or part.name in {old_file, os.path.splitext(old_file)[0]}:
            part.name = os.path.basename(self.filepath)
        return {'FINISHED'}


class ORCA_OT_import_project(bpy.types.Operator):
    bl_idname = "orca_reload.import_project"
    bl_label = "Import Orca Project"
    bl_description = ("Add a project made from an Orca project (.3mf): its plates, and its parts with their STL "
                      "files and how they stand on the plate. Build then updates that file")
    bl_options = {'UNDO'}
    filepath: bpy.props.StringProperty(subtype='FILE_PATH', options={'SKIP_SAVE'})
    filter_glob: bpy.props.StringProperty(default="*.3mf", options={'HIDDEN'})

    def invoke(self, context, event):
        root = props.project_root(context.scene)
        self.filepath = root + os.sep if os.path.isdir(root) else ""
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        scene = context.scene
        settings = scene.orca_reload
        path = os.path.normpath(self.filepath)
        stl_root = props.stl_root(scene)
        finder = reload3mf.SourceFinder([stl_root] if os.path.isdir(stl_root) else [])
        try:
            plates, problems = build3mf.read_layout(path, finder)
        except (reload3mf.ReloadError, OSError, zipfile.BadZipFile, ET.ParseError) as e:
            self.report({'ERROR'}, "%s: %s" % (os.path.basename(path), e))
            return {'CANCELLED'}

        project = settings.projects.add()
        settings.project_index = len(settings.projects) - 1
        project.name = os.path.splitext(os.path.basename(path))[0]
        root = props.project_root(scene)
        project.folder = props.relative_to(os.path.dirname(path), root)
        if project.folder == ".":
            project.folder = ""
        found = [p.stl for _, parts in plates for p in parts if p.stl]
        rel = {p: props.relative_to(p, stl_root) for p in found}
        project.stl_folder = build3mf.common_folder([r for r in rel.values() if not os.path.isabs(r)])
        lines = ["Imported %s" % path]
        for name, parts in plates:
            plate = project.plates.add()
            plate.name = name
            paths = [build3mf.strip_folder(rel[p.stl], project.stl_folder) for p in parts if p.stl]
            plate.stl_folder = build3mf.common_folder([p for p in paths if not os.path.isabs(p)])
            for p in parts:
                part = plate.parts.add()
                part.name = p.name
                if p.stl:
                    part.path = build3mf.strip_folder(build3mf.strip_folder(rel[p.stl], project.stl_folder),
                                                      plate.stl_folder)
                else:
                    part.path = p.source.replace("\\", "/")
                    problems.append("%s: %s not found below the STL root, %s" % (p.name, p.source, p.note))
                part.up = p.up
                part.angle = p.angle
                part.copies = p.copies
                if p.stl and p.note:
                    lines.append("  %s: %s" % (p.name, p.note))
        lines += ["  problem: %s" % p for p in problems]
        _show_log(context, lines)
        count = sum(len(parts) for _, parts in plates)
        self.report({'WARNING'} if problems else {'INFO'},
                    "Imported %d plates, %d parts%s" % (len(plates), count,
                                                         "; check the Info panel" if problems else ""))
        return {'FINISHED'}


def project_spec(context, project, painted):
    """build3mf.ProjectSpec of a project, and problem lines."""
    scene = context.scene
    settings = scene.orca_reload
    problems = []
    lines = {}
    plates = []
    for plate_no, plate in enumerate(p for p in project.plates if p.use):
        parts = []
        for part in plate.parts:
            if not part.use:
                continue
            if not part.path:
                problems.append("plate %d, %s: no STL file" % (plate_no + 1, part.label()))
                continue
            seam = None
            if part.seam is not None:
                key = part.seam.name
                if key not in lines:
                    lines[key] = blender_seams.seam_line(part.seam, context)
                line, problem = lines[key]
                if problem:
                    problems.append("plate %d, %s: seam %s %s" % (plate_no + 1, part.label(), key, problem))
                else:
                    seam = _seam_function(line, settings, painted)
            parts.append(build3mf.PartSpec(part.label(), props.part_path(scene, project, plate, part), part.up,
                                           part.angle, part.copies, seam))
        plates.append(build3mf.PlateSpec(plate.name, plate.gap, parts))
    template = os.path.normpath(bpy.path.abspath(project.template)) if project.template else ""
    return build3mf.ProjectSpec(props.project_path(scene, project), plates, template), problems


def _seam_function(line, settings, painted):
    painter = seams.SeamPainter([line], width=settings.seam_width, snap=settings.snap_distance, min_share=0.0)

    def paint(path, mesh):
        key = (os.path.normcase(path), line.name, settings.seam_width, settings.snap_distance)
        if key not in painted:
            result = painter.paint(mesh.verts, mesh.tris, label=path)
            painted[key] = (({}, "seam line %s is not on this part (further than the snap distance)" % line.name)
                            if result is None else (result.strings, result.note()))
        return painted[key]
    return paint


def _show_log(context, lines):
    """The lines go to the Info panel and the text REPORT_TEXT."""
    log = context.window_manager.orca_reload_log
    log.clear()
    for text in lines:
        item = log.add()
        item.text = text
        low = text.lower()
        item.icon = ('ERROR' if "problem:" in low or "not written" in low or "not on this part" in low
                     else 'FILE_3D' if not text.startswith(" ") else 'BLANK1')
    block = bpy.data.texts.get(REPORT_TEXT) or bpy.data.texts.new(REPORT_TEXT)
    block.clear()
    block.write("\n".join(lines) + "\n")


class ORCA_OT_build(bpy.types.Operator):
    bl_idname = "orca_reload.build"
    bl_label = "Build Orca Projects"
    bl_options = {'INTERNAL'}
    index: bpy.props.IntProperty(default=-1, options={'SKIP_SAVE'})

    @classmethod
    def description(cls, context, properties):
        if properties.index >= 0:
            return ("Write this project's 3MF: every ticked plate with its ticked parts, nested with the plate's "
                    "gap, seams painted. An existing file keeps its printer settings and each part's own settings")
        return "Build every ticked project"

    def execute(self, context):
        settings = context.scene.orca_reload
        if self.index >= 0:
            projects = [settings.projects[self.index]] if self.index < len(settings.projects) else []
        else:
            projects = [p for p in settings.projects if p.use]
        if not projects:
            self.report({'ERROR'}, "No project to build")
            return {'CANCELLED'}
        stl_cache, painted = {}, {}
        lines, written = [], 0
        for project in projects:
            spec, problems = project_spec(context, project, painted)
            if problems:
                lines += ["%s" % spec.path] + ["  problem: %s" % p for p in problems] + ["  not written", ""]
                continue
            try:
                text, ok = build3mf.build(spec, stl_cache)
            except (reload3mf.ReloadError, OSError, zipfile.BadZipFile, ET.ParseError, ValueError) as e:
                text, ok = ["%s" % spec.path, "  problem: %s" % e, "  not written"], False
            lines += text + [""]
            written += ok
        _show_log(context, lines)
        failed = len(projects) - written
        self.report({'WARNING'} if failed else {'INFO'},
                    "%d of %d projects written%s" % (written, len(projects),
                                                     "; see the Info panel" if failed else ""))
        return {'FINISHED'}


class ORCA_OT_clear_log(bpy.types.Operator):
    bl_idname = "orca_reload.clear_log"
    bl_label = "Clear Log"
    bl_description = "Clear the log of the last build"
    bl_options = {'INTERNAL'}

    def execute(self, context):
        context.window_manager.orca_reload_log.clear()
        return {'FINISHED'}


classes = (ORCA_OT_list_action, ORCA_OT_add_parts, ORCA_OT_browse_part, ORCA_OT_import_project, ORCA_OT_build,
           ORCA_OT_clear_log)
