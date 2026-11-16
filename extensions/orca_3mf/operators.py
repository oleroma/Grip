"""Operators of the Orca tab: the list buttons, adding STLs, importing a project and Build."""
import os
import time
import zipfile
import xml.etree.ElementTree as ET

import bpy

from . import blender_seams, build3mf, combi, paths, props, reload3mf, seams

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


class ORCA_OT_copy_action(bpy.types.Operator):
    bl_idname = "orca_reload.copy_action"
    bl_label = "Copies"
    bl_options = {'UNDO', 'INTERNAL'}
    action: bpy.props.EnumProperty(items=(('ADD', "", ""), ('REMOVE', "", ""), ('NEST', "", "")))

    @classmethod
    def description(cls, context, properties):
        return {
            'ADD': "Add a copy: the next Build nests it in free space and records where it went",
            'REMOVE': "Remove the active copy",
            'NEST': "Let the next Build nest every copy of this part again, around the plate's other parts",
        }[properties.action]

    @classmethod
    def poll(cls, context):
        project = props.active_project(context.scene.orca_reload)
        return props.active_part(props.active_plate(project)) is not None

    def execute(self, context):
        part = props.active_part(props.active_plate(props.active_project(context.scene.orca_reload)))
        if part is None:
            return {'CANCELLED'}
        part.copies = part.copies  # gives a part saved before spots its rows
        if self.action == 'ADD':
            part.instances.add()
            part.instance_index = len(part.instances) - 1
        elif self.action == 'REMOVE' and len(part.instances) > 1 and 0 <= part.instance_index < len(part.instances):
            part.instances.remove(part.instance_index)
            part.instance_index = max(0, min(part.instance_index, len(part.instances) - 1))
        elif self.action == 'NEST':
            for copy in part.instances:
                copy.placed = False
        return {'FINISHED'}


def _new_project(scene, project, previous):
    """A new project starts with one plate and the printer settings of the project before it."""
    project.name = "project_%d" % len(scene.orca_reload.projects)
    project.plates.add().name = "Plate 1"
    if previous is not None:
        project.folder = previous.folder
        project.stl_folder = previous.stl_folder
        project.profiles, project.orca_metadata = previous.profiles, previous.orca_metadata
        project.profiles_from = previous.profiles_from
        if previous.template:
            project.template = previous.template
        elif os.path.isfile(props.project_path(scene, previous)):
            project.template = props.blend_relative(props.project_path(scene, previous))


def _start_folder(scene, project, folder):
    """Where a file browser opens: the folder if it exists, else the project's STL folder, else the STL root."""
    for f in (folder, props.project_stl_folder(scene, project) if project else "", props.stl_root(scene)):
        if f and os.path.isdir(f):
            return f
    return ""


def _stl_browser(operator, context, folder):
    folder = _start_folder(context.scene, props.active_project(context.scene.orca_reload), folder)
    operator.directory = folder + os.sep if folder else ""
    context.window_manager.fileselect_add(operator)
    return {'RUNNING_MODAL'}


ROOTS = (('STL_ROOT', "STL root", "The folder the parts' STL paths start from"),
         ('PROJECT_ROOT', "3MF root", "The folder the projects' 3MF files are saved in"))
_ROOT_PROPS = {'STL_ROOT': "stl_root", 'PROJECT_ROOT': "project_root"}


class ORCA_OT_browse_root(bpy.types.Operator):
    bl_idname = "orca_reload.browse_root"
    bl_label = "Pick Folder"
    bl_description = "Pick the folder. It is saved from the .blend file's folder (../stl) when the .blend is saved"
    bl_options = {'UNDO', 'INTERNAL'}
    root: bpy.props.EnumProperty(items=ROOTS, options={'SKIP_SAVE'})
    directory: bpy.props.StringProperty(subtype='DIR_PATH', options={'SKIP_SAVE'})
    filter_folder: bpy.props.BoolProperty(default=True, options={'HIDDEN'})

    def invoke(self, context, event):
        scene = context.scene
        folder = props.stl_root(scene) if self.root == 'STL_ROOT' else props.project_root(scene)
        if not os.path.isdir(folder):
            folder = props.absolute("//")
        self.directory = folder + os.sep if os.path.isdir(folder) else ""
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        if not self.directory:
            return {'CANCELLED'}
        setattr(context.scene.orca_reload, _ROOT_PROPS[self.root],
                props.blend_relative(os.path.normpath(self.directory)))
        return {'FINISHED'}


class ORCA_OT_browse_template(bpy.types.Operator):
    bl_idname = "orca_reload.browse_template"
    bl_label = "Pick Orca Project"
    bl_description = ("Pick the Orca project (.3mf) a new project takes its settings from. It is saved from the "
                      ".blend file's folder (../printer.3mf) when the .blend is saved")
    bl_options = {'UNDO', 'INTERNAL'}
    filepath: bpy.props.StringProperty(subtype='FILE_PATH', options={'SKIP_SAVE'})
    filter_glob: bpy.props.StringProperty(default="*.3mf;*.3MF", options={'HIDDEN'})

    @classmethod
    def poll(cls, context):
        return props.active_project(context.scene.orca_reload) is not None

    def invoke(self, context, event):
        project = props.active_project(context.scene.orca_reload)
        current = props.absolute(project.template)
        if current and os.path.isfile(current):
            self.filepath = current
        else:
            root = props.project_root(context.scene)
            self.filepath = root + os.sep if os.path.isdir(root) else ""
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        project = props.active_project(context.scene.orca_reload)
        if project is None or not self.filepath:
            return {'CANCELLED'}
        project.template = props.blend_relative(os.path.normpath(self.filepath))
        return {'FINISHED'}


class ORCA_OT_load_profiles(bpy.types.Operator):
    bl_idname = "orca_reload.load_profiles"
    bl_label = "Load Profiles"
    bl_description = ("Take the printer, process and filament settings from an Orca project (.3mf) and save them "
                      "in the .blend: its parts, plates and part settings are not read. Build then needs no 3MF. "
                      "A small project with no parts, saved in Orca, works as a profile file")
    bl_options = {'UNDO', 'INTERNAL'}
    filepath: bpy.props.StringProperty(subtype='FILE_PATH', options={'SKIP_SAVE'})
    filter_glob: bpy.props.StringProperty(default="*.3mf;*.3MF", options={'HIDDEN'})

    @classmethod
    def poll(cls, context):
        return props.active_project(context.scene.orca_reload) is not None

    def invoke(self, context, event):
        project = props.active_project(context.scene.orca_reload)
        current = props.absolute(project.template) if project.template else ""
        root = props.project_root(context.scene)
        self.filepath = current if current and os.path.isfile(current) else (
            root + os.sep if os.path.isdir(root) else "")
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        scene = context.scene
        project = props.active_project(scene.orca_reload)
        if project is None or not self.filepath:
            return {'CANCELLED'}
        path = os.path.normpath(self.filepath)
        try:
            profiles, metadata = build3mf.read_profiles_file(path)
        except (reload3mf.ReloadError, OSError, zipfile.BadZipFile) as e:
            self.report({'ERROR'}, str(e))
            return {'CANCELLED'}
        project.profiles = props.dump_json(profiles)
        project.orca_metadata = props.dump_json(metadata)
        project.profiles_from = props.shown(scene, path)
        _show_log(context, ["Profiles loaded from %s" % props.shown(scene, path)] +
                  ["  " + line for line in _profile_names(profiles)])
        self.report({'INFO'}, "Profiles loaded from %s" % os.path.basename(path))
        return {'FINISHED'}


def _profile_names(profiles):
    """Lines naming the printer, process and filament presets the saved settings come from."""
    import json
    try:
        settings = json.loads(profiles.get(build3mf.SETTINGS, "{}"))
    except ValueError:
        return []
    lines = []
    for key, kind, _slot in build3mf.PRESET_KINDS:
        value = settings.get(key)
        if value:
            lines.append("%s: %s" % (kind, ", ".join(v.strip() for v in value) if isinstance(value, list)
                                     else value))
    return lines


class ORCA_OT_apply_preset(bpy.types.Operator):
    bl_idname = "orca_reload.apply_preset"
    bl_label = "Apply Preset File"
    bl_description = ("Lay an Orca preset exported as .json (printer, process or filament) over the project's "
                      "saved settings: only the values it holds change. Settings it does not change stay as "
                      "the loaded ones")
    bl_options = {'UNDO', 'INTERNAL'}
    filepath: bpy.props.StringProperty(subtype='FILE_PATH', options={'SKIP_SAVE'})
    filter_glob: bpy.props.StringProperty(default="*.json", options={'HIDDEN'})
    filament: bpy.props.IntProperty(name="Filament", default=1, min=1, max=16,
                                    description="Which filament of the project a filament preset goes into")

    @classmethod
    def poll(cls, context):
        project = props.active_project(context.scene.orca_reload)
        return project is not None and bool(project.profiles)

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        import json
        scene = context.scene
        project = props.active_project(scene.orca_reload)
        if project is None or not self.filepath:
            return {'CANCELLED'}
        path = os.path.normpath(self.filepath)
        try:
            with open(path, encoding="utf-8-sig") as f:
                preset = json.load(f)
            if not isinstance(preset, dict):
                raise reload3mf.ReloadError("not an Orca preset")
            profiles, notes = build3mf.apply_preset(props.load_json(project.profiles, {}), preset,
                                                    self.filament - 1)
        except (reload3mf.ReloadError, OSError, ValueError) as e:
            self.report({'ERROR'}, "%s: %s" % (os.path.basename(path), e))
            return {'CANCELLED'}
        project.profiles = props.dump_json(profiles)
        project.profiles_from = "%s + %s" % (project.profiles_from or "the import", os.path.basename(path))
        _show_log(context, ["Preset %s applied" % props.shown(scene, path)] + ["  " + n for n in notes])
        self.report({'WARNING'} if len(notes) > 1 else {'INFO'}, notes[0])
        return {'FINISHED'}


_key_cache = {"text": None, "keys": []}


def _setting_keys(self, context, edit_text):
    project = props.active_project(context.scene.orca_reload)
    text = project.profiles if project is not None else ""
    if _key_cache["text"] != text:
        _key_cache["text"] = text
        _key_cache["keys"] = build3mf.profile_keys(props.load_json(text, {}))
    needle = edit_text.lower()
    return [k for k in _key_cache["keys"] if needle in k][:200]


class ORCA_OT_object_setting(bpy.types.Operator):
    bl_idname = "orca_reload.object_setting"
    bl_label = "Orca Setting"
    bl_description = ("Set one of Orca's per-object settings (wall_loops, sparse_infill_density, ...) for this "
                      "part: on its object's setup when it follows one, so every part of the object gets it")
    bl_options = {'UNDO', 'INTERNAL'}
    action: bpy.props.EnumProperty(items=(('SET', "Set", ""), ('REMOVE', "Remove", "")), options={'SKIP_SAVE'})
    key: bpy.props.StringProperty(name="Setting", search=_setting_keys, options={'SKIP_SAVE'},
                                  description="Orca's name of the setting, as in its preset files")
    value: bpy.props.StringProperty(name="Value", options={'SKIP_SAVE'},
                                    description="The value as Orca writes it: 3, 25%, 1 for on, 0 for off")

    @classmethod
    def poll(cls, context):
        return props.active_part(props.active_plate(props.active_project(context.scene.orca_reload))) is not None

    def invoke(self, context, event):
        if self.action == 'REMOVE':
            return self.execute(context)
        if self.key and not self.value:
            part = props.active_part(props.active_plate(props.active_project(context.scene.orca_reload)))
            self.value = dict(props.pairs(props.setup(part).orca_object)).get(self.key, "")
        return context.window_manager.invoke_props_dialog(self, width=400)

    def draw(self, context):
        self.layout.prop(self, "key")
        self.layout.prop(self, "value")
        project = props.active_project(context.scene.orca_reload)
        default = _profile_value(project, self.key)
        if default is not None:
            self.layout.label(text="The profile has %s" % default)

    def execute(self, context):
        part = props.active_part(props.active_plate(props.active_project(context.scene.orca_reload)))
        key = self.key.strip()
        if not key or key in build3mf.PART_KEYS:
            return {'CANCELLED'}
        setup = props.setup(part)
        pairs = [(k, v) for k, v in props.pairs(setup.orca_object) if k != key]
        if self.action == 'SET':
            pairs.append((key, self.value.strip()))
        setup.orca_object = props.dump_json(pairs)
        return {'FINISHED'}


def _profile_value(project, key):
    """The value the project's saved process / printer settings give key, as text, or None."""
    import json
    if project is None or not key:
        return None
    try:
        value = json.loads(props.load_json(project.profiles, {}).get(build3mf.SETTINGS, "{}")).get(key)
    except ValueError:
        return None
    if value is None:
        return None
    return ", ".join(value) if isinstance(value, list) else str(value)


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
        names = sorted(f.name for f in self.files if f.name.lower().endswith(".stl"))
        for name in names:
            part = plate.parts.add()
            part.path = props.part_relative(context.scene, project, plate,
                                            os.path.normpath(os.path.join(self.directory, name)))
            part.name = name
        if names:
            plate.part_index = len(plate.parts) - 1
            if not os.path.isdir(props.plate_folder(context.scene, project, plate)):
                # A plate whose name isn't a folder yet takes the folder its parts share once all are found
                props.name_plate_from_parts(context.scene, project, plate, whole=True)
        return {'FINISHED'}


def _combi_preset(operator, scene, project):
    """The project's Combi preset, or None after reporting why."""
    if not combi.available(scene):
        operator.report({'ERROR'}, "Combi Export is not installed")
        return None
    preset = combi.find_preset(scene, project.combi_preset)
    if preset is None:
        operator.report({'ERROR'}, "Pick the project's Combi preset first" if not project.combi_preset
                        else "The project's Combi preset is gone: pick another")
    return preset


class ORCA_OT_own_setup(bpy.types.Operator):
    bl_idname = "orca_reload.own_setup"
    bl_label = "Own Setup"
    bl_description = ("Ticked: this part keeps its own Up, Turn, Mirror, Seam and Orca part settings, starting "
                      "from its object's. Unticked: it follows its object's setup again")
    bl_options = {'UNDO', 'INTERNAL'}

    @classmethod
    def poll(cls, context):
        part = props.active_part(props.active_plate(props.active_project(context.scene.orca_reload)))
        return part is not None and part.source is not None

    def execute(self, context):
        part = props.active_part(props.active_plate(props.active_project(context.scene.orca_reload)))
        props.set_own_setup(part, not part.own)
        if not part.own and part.mark_note.startswith("set up differently"):
            part.mark, part.mark_note = 'NONE', ""
        return {'FINISHED'}


def fill_combi_files(scene, project, plate, found, items):
    """Lists found ([(path, object)] from combi.files) in items (OrcaCombiFile), nothing ticked."""
    on_plate = {os.path.normcase(os.path.normpath(props.part_path(scene, project, plate, p)))
                for p in plate.parts if p.path}
    top = props.project_stl_folder(scene, project) if project.stl_folder else props.stl_root(scene)
    items.clear()
    for path, obj in found:
        item = items.add()
        item.name = os.path.basename(path)
        item.path = path
        folder = paths.relative_form(os.path.dirname(path), top).replace("\\", "/")
        item.shown = "" if folder == "." else folder
        item.object = obj.name
        item.on_plate = os.path.normcase(path) in on_plate
        item.exists = os.path.isfile(path)


class ORCA_OT_add_from_combi(bpy.types.Operator):
    bl_idname = "orca_reload.add_from_combi"
    bl_label = "Add from Combi"
    bl_description = ("Add files the project's Combi preset writes to the active plate: tick them in the list. "
                      "Combi tells which object each file comes from, so give every file its own name (a tag "
                      "per tolerance) and Orca keeps enough to find it again")
    bl_options = {'UNDO', 'INTERNAL'}

    @classmethod
    def poll(cls, context):
        project = props.active_project(context.scene.orca_reload)
        return props.active_plate(project) is not None and bool(project.combi_preset)

    def invoke(self, context, event):
        scene = context.scene
        project = props.active_project(scene.orca_reload)
        plate = props.active_plate(project)
        preset = _combi_preset(self, scene, project)
        if preset is None:
            return {'CANCELLED'}
        found = combi.files(scene, preset)
        if not found:
            self.report({'WARNING'}, "Combi preset %s writes no files" % preset.name)
            return {'CANCELLED'}
        fill_combi_files(scene, project, plate, found, context.window_manager.orca_reload_combi_files)
        context.window_manager.orca_reload_combi_index = 0
        return context.window_manager.invoke_props_dialog(self, width=560, title="Add from Combi: " + preset.name,
                                                          confirm_text="Add")

    def draw(self, context):
        wm = context.window_manager
        layout = self.layout
        layout.template_list("ORCA_UL_combi_files", "", wm, "orca_reload_combi_files", wm,
                             "orca_reload_combi_index", rows=12)
        picked = sum(1 for f in wm.orca_reload_combi_files if f.pick and not f.on_plate)
        layout.label(text="%d file%s to add. Grey: on the plate already; red: not exported yet" % (
            picked, "" if picked == 1 else "s"))

    def execute(self, context):
        scene = context.scene
        project = props.active_project(scene.orca_reload)
        plate = props.active_plate(project)
        items = context.window_manager.orca_reload_combi_files
        picked = [f for f in items if f.pick and not f.on_plate]
        if not picked:
            return {'CANCELLED'}
        if not any(p.parts for p in project.plates) and not project.stl_folder and not project.plate_paths:
            # A project with no parts yet starts its STL folder at the folder the preset's files share
            shared = combi.common_folder([f.path for f in items])
            rel = props.relative_to(shared, props.stl_root(scene)) if shared else ""
            if rel and not os.path.isabs(rel) and rel != "." and not rel.startswith(".."):
                project.stl_folder = rel.replace("\\", "/")
        for f in picked:
            part = plate.parts.add()
            part.path = props.part_relative(scene, project, plate, os.path.normpath(f.path))
            part.name = f.name
            obj = bpy.data.objects.get(f.object)
            if obj is not None:
                props.link_part(part, obj, fresh=True)
        plate.part_index = len(plate.parts) - 1
        items.clear()
        self.report({'INFO'}, "Added %d part%s" % (len(picked), "" if len(picked) == 1 else "s"))
        return {'FINISHED'}


class ORCA_OT_update_from_combi(bpy.types.Operator):
    bl_idname = "orca_reload.update_from_combi"
    bl_label = "Update from Combi"
    bl_description = ("Check every part of the project against the files its Combi preset writes: a part whose "
                      "file is gone is linked again when exactly one file of the preset has its name; parts Combi "
                      "no longer writes, or has not exported yet, are marked. No plate or part is added or removed")
    bl_options = {'UNDO', 'INTERNAL'}

    @classmethod
    def poll(cls, context):
        project = props.active_project(context.scene.orca_reload)
        return project is not None and bool(project.combi_preset)

    def execute(self, context):
        scene = context.scene
        project = props.active_project(scene.orca_reload)
        preset = _combi_preset(self, scene, project)
        if preset is None:
            return {'CANCELLED'}
        lines, counts = update_from_combi(scene, project, combi.files(scene, preset))
        lines.insert(0, "Update from Combi preset %s: %s" % (preset.name, props.shown(
            scene, props.project_path(scene, project))))
        _show_log(context, lines)
        self.report({'WARNING'} if counts["marked"] else {'INFO'},
                    "%d parts checked, %d linked again, %d marked%s" % (
                        counts["checked"], counts["linked"], counts["marked"],
                        "; check the Info panel" if counts["marked"] else ""))
        return {'FINISHED'}


def update_from_combi(scene, project, files):
    """Checks the project's parts against files ([(absolute path, Blender object)] a Combi preset writes) and links
    each part to the object its file comes from: (log lines, counts)."""
    objects = {os.path.normcase(os.path.normpath(p)): obj for p, obj in files}
    files = [p for p, _obj in files]
    written = {os.path.normcase(os.path.normpath(p)): p for p in files}
    by_name = {}
    for p in written.values():
        by_name.setdefault(os.path.basename(p).lower(), []).append(p)
    lines = []
    counts = {"checked": 0, "linked": 0, "marked": 0}
    for plate_no, plate in enumerate(project.plates):
        for part in plate.parts:
            if not part.path:
                continue
            counts["checked"] += 1
            path = props.part_path(scene, project, plate, part)
            where = "plate %s, %s" % (plate.name or plate_no + 1, part.label())
            key = os.path.normcase(os.path.normpath(path))
            if key in written:
                if os.path.isfile(path):
                    part.mark, part.mark_note = 'NONE', ""
                else:
                    note = "Combi writes this file but it is not exported yet: export in Combi first"
                    part.mark, part.mark_note = 'WARNING', note
                    counts["marked"] += 1
                    lines.append("  %s: %s" % (where, note))
                _link(part, objects[key], where, lines, counts)
                continue
            same = by_name.get(os.path.basename(path).lower(), [])
            if not os.path.isfile(path) and len(same) == 1:
                part.path = props.part_relative(scene, project, plate, os.path.normpath(same[0]))
                part.mark, part.mark_note = ('NONE', "") if os.path.isfile(same[0]) else (
                    'WARNING', "Combi writes this file but it is not exported yet: export in Combi first")
                counts["linked"] += 1
                lines.append("  %s: linked to %s" % (where, props.shown(scene, same[0])))
                _link(part, objects[os.path.normcase(os.path.normpath(same[0]))], where, lines, counts)
                continue
            if os.path.isfile(path):
                note = "Combi no longer writes this file; the one on disk is old"
                part.mark, part.mark_note = 'WARNING', note
            elif len(same) > 1:
                note = "STL not found, and %d files of the Combi preset have its name: use Relink" % len(same)
                part.mark, part.mark_note = 'ERROR', note
            else:
                note = "STL not found, and the Combi preset writes no file of that name"
                part.mark, part.mark_note = 'ERROR', note
            counts["marked"] += 1
            lines.append("  %s: %s" % (where, note))
    if not lines:
        lines.append("  every part is a file Combi writes")
    return lines, counts


def _link(part, obj, where, lines, counts):
    """Links a part to the object Combi exports its file from, once (a part already linked to it is left as is)."""
    if obj is None or part.source == obj:
        return
    if props.link_part(part, obj):
        counts["marked"] += 1
        lines.append("  %s: %s" % (where, part.mark_note))
    else:
        lines.append("  %s: follows the setup of object %s" % (where, obj.name))


class ORCA_OT_browse_part(bpy.types.Operator):
    bl_idname = "orca_reload.browse_part"
    bl_label = "Pick STL"
    bl_description = "Pick the part's STL file: any file, also one with another name"
    bl_options = {'UNDO', 'INTERNAL'}
    filepath: bpy.props.StringProperty(subtype='FILE_PATH', options={'SKIP_SAVE'})
    directory: bpy.props.StringProperty(subtype='DIR_PATH', options={'SKIP_SAVE'})
    filter_glob: bpy.props.StringProperty(default="*.stl", options={'HIDDEN'})
    part: bpy.props.IntProperty(default=-1, options={'HIDDEN', 'SKIP_SAVE'})  # from a part row: that part

    def _pick(self, context):
        plate = props.active_plate(props.active_project(context.scene.orca_reload))
        if plate is not None and 0 <= self.part < len(plate.parts):
            plate.part_index = self.part

    def invoke(self, context, event):
        self._pick(context)
        settings = context.scene.orca_reload
        project = props.active_project(settings)
        plate = props.active_plate(project)
        part = props.active_part(plate)
        if part is None:
            return {'CANCELLED'}
        current = props.part_path(context.scene, project, plate, part) if part.path else ""
        if current and os.path.isfile(current):
            self.filepath = current
        return _stl_browser(self, context, os.path.dirname(current) if current else
                            props.plate_folder(context.scene, project, plate))

    def execute(self, context):
        self._pick(context)
        settings = context.scene.orca_reload
        project = props.active_project(settings)
        plate = props.active_plate(project)
        part = props.active_part(plate)
        if part is None or not self.filepath:
            return {'CANCELLED'}
        old_file = os.path.basename(part.path.replace("\\", "/"))
        part.path = props.part_relative(context.scene, project, plate, os.path.normpath(self.filepath))
        if not part.name or part.name in {old_file, os.path.splitext(old_file)[0]}:
            part.name = os.path.basename(self.filepath)
        if not os.path.isdir(props.plate_folder(context.scene, project, plate)):
            # A plate whose name isn't a folder yet takes the folder its parts share once all are found
            props.name_plate_from_parts(context.scene, project, plate, whole=True)
        return {'FINISHED'}


def missing_parts(scene, project, plate):
    """The plate's parts whose STL file is not there."""
    return [p for p in plate.parts if not p.path or not os.path.isfile(props.part_path(scene, project, plate, p))]


class ORCA_OT_relink(bpy.types.Operator):
    bl_idname = "orca_reload.relink"
    bl_label = "Relink Missing Parts"
    bl_description = ("Pick the folder of this plate's parts. Each part whose STL is missing is looked for by its "
                      "file name in that folder only. With \"Plate names are folders\" on, also in the folders "
                      "above it up to the project's STL folder (never a sibling), and the plate is named after the "
                      "folder (tight/cap_loose), so Import finds its parts again even when Orca keeps only their "
                      "file names. A file found in two of those folders is not taken")
    bl_options = {'UNDO', 'INTERNAL'}
    directory: bpy.props.StringProperty(subtype='DIR_PATH', options={'SKIP_SAVE'})
    filter_folder: bpy.props.BoolProperty(default=True, options={'HIDDEN'})
    plate: bpy.props.IntProperty(default=-1, options={'HIDDEN', 'SKIP_SAVE'})  # from a plate row: that plate

    @classmethod
    def poll(cls, context):
        return props.active_plate(props.active_project(context.scene.orca_reload)) is not None

    def invoke(self, context, event):
        scene = context.scene
        project = props.active_project(scene.orca_reload)
        if 0 <= self.plate < len(project.plates):
            project.plate_index = self.plate
        folder = _start_folder(scene, project, props.plate_folder(scene, project, props.active_plate(project)))
        self.directory = folder + os.sep if folder else ""
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        scene = context.scene
        project = props.active_project(scene.orca_reload)
        if 0 <= self.plate < len(project.plates):
            project.plate_index = self.plate
        plate = props.active_plate(project)
        if plate is None or not self.directory:
            return {'CANCELLED'}
        folder = os.path.normpath(self.directory)
        top = props.project_stl_folder(scene, project)
        if project.plate_paths and os.path.isdir(top) and build3mf._inside(folder, top):
            roots = [top]  # the folder and the folders above it, up to the project's STL folder
        else:
            roots = [folder]  # the folder only
        missing = missing_parts(scene, project, plate)
        found = 0
        for part in missing:
            file_name = os.path.basename(part.path.replace("\\", "/")) or part.name
            hit = build3mf.find_up(file_name, folder, roots) if file_name else None
            if hit:
                part.path = props.part_relative(scene, project, plate, hit)
                found += 1
        # The plate's name: the deepest folder its parts share, else the picked folder
        props.name_plate_from_parts(scene, project, plate, fallback=folder)
        left = len(missing) - found
        self.report({'WARNING'} if left else {'INFO'},
                    "Plate %s: %d of %d missing parts found%s" % (plate.name, found, len(missing),
                                                                 "; %d still missing" % left if left else ""))
        return {'FINISHED'}


class ORCA_OT_overwrite(bpy.types.Operator):
    bl_idname = "orca_reload.overwrite"
    bl_label = "Overwrite"
    bl_description = ("On: Build writes into the project's 3MF itself. Off: the 3MF is never changed once it exists; "
                      "each Build writes the next numbered file into the 3mf_builds folder next to it")
    bl_options = {'UNDO', 'INTERNAL'}

    @classmethod
    def poll(cls, context):
        return props.active_project(context.scene.orca_reload) is not None

    def invoke(self, context, event):
        project = props.active_project(context.scene.orca_reload)
        if project.overwrite:
            return self.execute(context)
        name = os.path.basename(props.project_path(context.scene, project))
        return context.window_manager.invoke_confirm(
            self, event, title="Overwrite %s?" % name,
            message="From now on Build changes %s directly. No backup is kept." % name, confirm_text="Overwrite",
            icon='WARNING')

    def execute(self, context):
        project = props.active_project(context.scene.orca_reload)
        project.overwrite = not project.overwrite
        return {'FINISHED'}


class ORCA_OT_import_project(bpy.types.Operator):
    bl_idname = "orca_reload.import_project"
    bl_label = "Import Orca Project"
    bl_description = ("Add a project made from an Orca project (.3mf): its plates, and its parts with their STL "
                      "files and how they stand on the plate. A 3MF that is already a project in the tab updates "
                      "that project and keeps its links. Build then updates that file")
    bl_options = {'UNDO'}
    filepath: bpy.props.StringProperty(subtype='FILE_PATH', options={'SKIP_SAVE'})
    filter_glob: bpy.props.StringProperty(default="*.3mf;*.3MF", options={'HIDDEN'})
    plate_paths: bpy.props.BoolProperty(
        name="Plate names are folders", default=False,
        description="Each plate's name is its folder below the STL folder set here (tight/cap_loose): a part Orca "
                    "kept only the file name of is taken from that folder or a folder above it, up to the STL "
                    "folder, when exactly one of them holds it")
    stl_folder: bpy.props.StringProperty(
        name="STL folder",
        description="The project's STL folder, below the STL root (GripV/buttons). With Plate names are folders, "
                    "plate names are read as paths below it, and looking up stops there. Empty: the STL root (the "
                    "project's STL folder then becomes the folder all found parts share). A project already in the "
                    "tab keeps its own")

    def invoke(self, context, event):
        root = props.project_root(context.scene)
        self.filepath = root + os.sep if os.path.isdir(root) else ""
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        scene = context.scene
        path = os.path.normpath(self.filepath)
        old = next((p for p in scene.orca_reload.projects
                    if os.path.normcase(props.project_path(scene, p)) == os.path.normcase(path)), None)
        return import_3mf(self, context, path, old, self.plate_paths, self.stl_folder)


class ORCA_OT_update_from_3mf(bpy.types.Operator):
    bl_idname = "orca_reload.update_from_3mf"
    bl_label = "Update from 3MF"
    bl_description = ("Take what you changed in Orca back into this project: pick a 3MF (it starts at the newest "
                      "build) and its plates, parts, where each copy stands, and the printer, plate and part "
                      "settings replace the tab's. Links, seams and Build ticks are kept. The project's own 3MF "
                      "path does not change")
    bl_options = {'UNDO'}
    filepath: bpy.props.StringProperty(subtype='FILE_PATH', options={'SKIP_SAVE'})
    filter_glob: bpy.props.StringProperty(default="*.3mf;*.3MF", options={'HIDDEN'})

    @classmethod
    def poll(cls, context):
        return props.active_project(context.scene.orca_reload) is not None

    def invoke(self, context, event):
        scene = context.scene
        project = props.active_project(scene.orca_reload)
        path = props.project_path(scene, project)
        latest = build3mf.latest_build_path(path)
        start = latest or path
        if os.path.isfile(start):
            self.filepath = start
        else:
            folder = os.path.dirname(start)
            self.filepath = folder + os.sep if os.path.isdir(folder) else ""
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        project = props.active_project(context.scene.orca_reload)
        if project is None:
            return {'CANCELLED'}
        return import_3mf(self, context, os.path.normpath(self.filepath), project, project.plate_paths, "")


def import_3mf(operator, context, path, old, plate_paths, stl_folder):
    """Imports the Orca 3MF at path: into the project old (keeping its links, seams and ticks), else as a new
    project. Everything Build needs is saved in the tab, so the 3MF is not read again."""
    scene = context.scene
    settings = scene.orca_reload
    stl_root = props.stl_root(scene)
    finder = reload3mf.SourceFinder([stl_root] if os.path.isdir(stl_root) else [])
    plate_paths = plate_paths or (old is not None and old.plate_paths)
    if old is not None:
        top = props.project_stl_folder(scene, old)
    elif stl_folder:
        top = paths.join(stl_root, stl_folder)
    else:
        top = None
    links = _tab_links(scene, old) if old is not None else {}
    try:
        imported, problems = build3mf.read_project(
            path, finder, plate_paths=plate_paths, top=top if top and os.path.isdir(top) else None,
            known=lambda plate, name: links.get((plate, name.lower())))
    except (reload3mf.ReloadError, OSError, zipfile.BadZipFile, ET.ParseError) as e:
        operator.report({'ERROR'}, "%s: %s" % (os.path.basename(path), e))
        return {'CANCELLED'}
    plates = imported.plates

    kept = {}  # (plate name, STL) -> what only the tab holds: Build ticks, gap, seams
    if old is not None:
        project = old
        settings.project_index = list(settings.projects).index(old)
        for plate in project.plates:
            for part in plate.parts:
                kept[(plate.name, os.path.normcase(os.path.normpath(props.part_path(scene, project, plate, part))))] = (
                    plate.use, plate.gap, part.use, part.seam, part.source, part.own)
        project.plates.clear()
    else:
        project = settings.projects.add()
        settings.project_index = len(settings.projects) - 1
        project.name = os.path.basename(path)
        root = props.project_root(scene)
        project.folder = paths.relative_form(os.path.dirname(path), root)  # ../other when outside the root
        if project.folder == ".":
            project.folder = ""
    project.plate_paths = plate_paths
    if imported.profiles:
        project.profiles = props.dump_json(imported.profiles)
        project.orca_metadata = props.dump_json(imported.metadata)
        project.profiles_from = props.shown(scene, path)
    found = [p.stl for plate in plates for p in plate.parts if p.stl]
    rel = {p: props.relative_to(p, stl_root) for p in found}
    if old is None:
        if stl_folder:
            project.stl_folder = stl_folder.replace("\\", "/").strip("/")
        elif plate_paths:
            project.stl_folder = ""  # the plate names were read from the STL root
        else:
            project.stl_folder = build3mf.common_folder([r for r in rel.values() if not os.path.isabs(r)])
    lines = ["%s %s" % ("Updated from" if old is not None else "Imported", props.shown(scene, path))]
    if not imported.profiles:
        lines.append("  no printer settings in it: Build takes them from Settings from")
    for imported_plate in plates:
        name = imported_plate.name
        plate = project.plates.add()
        plate.name = name
        plate.orca_meta = props.dump_json(imported_plate.meta)
        below = [build3mf.strip_folder(rel[p.stl], project.stl_folder) for p in imported_plate.parts if p.stl]
        plate.stl_folder = build3mf.common_folder([p for p in below if not os.path.isabs(p)])
        for p in imported_plate.parts:
            part = plate.parts.add()
            part.name = p.name
            if p.stl:
                part.path = props.part_relative(scene, project, plate, p.stl)
                same = kept.get((name, os.path.normcase(os.path.normpath(p.stl))))
                if same is not None:
                    plate.use, plate.gap, part.use, part.seam, part.source, part.own = same
            else:
                part.path = _source_path(scene, project, plate, p.source, os.path.dirname(path))
                problems.append("%s: %s not found below the STL root, %s" % (p.name, p.source, p.note))
                props.set_mark(part, 'ERROR', p.note)
            part.up = p.up
            part.angle = p.angle
            props.set_spots(part, p.spots or [None] * p.copies)
            part.mirror = p.mirror
            part.orca_object = props.dump_json(p.object_meta)
            part.orca_part = props.dump_json(p.part_meta)
            if p.stl and p.note:
                lines.append("  %s: %s" % (p.name, p.note))
    lines += _settings_to_objects(project)
    lines += ["  not kept: %s" % d for d in imported.dropped]
    lines += ["  problem: %s" % p for p in problems]
    _show_log(context, lines)
    count = sum(len(p.parts) for p in plates)
    operator.report({'WARNING'} if problems else {'INFO'},
                    "%s %d plates, %d parts%s" % ("Updated" if old is not None else "Imported", len(plates), count,
                                                   "; check the Info panel" if problems else ""))
    return {'FINISHED'}


def _settings_to_objects(project):
    """After Update from 3MF: the parts that follow an object's setup came back with what Orca has. When all of an
    object's parts in the project agree, that becomes the object's setup (its seam stays); otherwise those parts
    keep what they came back with as their Own setup, marked. Returns log lines."""
    groups = {}
    for plate in project.plates:
        for part in plate.parts:
            if part.source is not None and not part.own:
                groups.setdefault(part.source.name, (part.source, []))[1].append(part)
    lines = []
    for obj, parts in groups.values():
        shared = obj.orca_reload_setup
        values = {(tuple(round(v, 4) for v in p.up), round(p.angle, 4), p.mirror, p.orca_object, p.orca_part)
                  for p in parts}
        if len(values) == 1:
            for key in ("up", "angle", "mirror", "orca_object", "orca_part"):
                setattr(shared, key, getattr(parts[0], key))
            shared.has = True
            continue
        for p in parts:
            p.seam = shared.seam
            p.own = True
            props.set_mark(p, 'WARNING', "came back from Orca set up differently from the other parts of object "
                                         "%s: kept as its own setup" % obj.name)
        lines.append("  object %s: its %d parts came back set up differently, each kept as its own setup"
                     % (obj.name, len(parts)))
    return lines


def _tab_links(scene, project):
    """{(plate name, file name in lower case): STL} of the project's parts whose STL is there, for the file names
    found once on their plate; a plate name used twice gives nothing."""
    names = [p.name for p in project.plates]
    links = {}
    for plate in project.plates:
        if names.count(plate.name) != 1:
            continue
        by_name = {}
        for part in plate.parts:
            stl = props.part_path(scene, project, plate, part)
            by_name.setdefault(os.path.basename(stl).lower(), []).append(stl)
        for file_name, stls in by_name.items():
            stls = {os.path.normcase(os.path.normpath(p)): p for p in stls}  # parts split from one STL: one link
            if len(stls) == 1:
                stl = next(iter(stls.values()))
                if os.path.isfile(stl):
                    links[(plate.name, file_name)] = stl
    return links


def _source_path(scene, project, plate, source, project_dir):
    """A part whose STL was not found keeps the path Orca stored, saved from its plate's folder like any other part
    when it is a path on this system (a relative one starts at the 3MF file's folder, as in Orca)."""
    if not source:
        return ""
    if os.path.isabs(source) or not paths.is_absolute(source):
        return props.part_relative(scene, project, plate, os.path.normpath(os.path.join(project_dir, source)))
    return source.replace("\\", "/")  # a path from the other system (C:\\... on Linux): kept as Orca stored it


def project_spec(context, project, painted):
    """build3mf.ProjectSpec of a project, and problem lines."""
    scene = context.scene
    settings = scene.orca_reload
    problems = []
    lines = {}
    plates = []
    used = [(i, p) for i, p in enumerate(project.plates) if p.use]
    for plate_no, (plate_index, plate) in enumerate(used):
        parts = []
        for part_index, part in enumerate(plate.parts):
            if not part.use:
                continue
            if not part.path:
                problems.append("plate %d, %s: no STL file" % (plate_no + 1, part.label()))
                continue
            seam = None
            setup = props.setup(part)  # the object's setup, or the part's own
            if setup.seam is not None:
                who = setup.seam.as_pointer()
                if who not in lines:
                    lines[who] = blender_seams.seam_line(setup.seam, context)
                line, problem = lines[who]
                if problem:
                    problems.append("plate %d, %s: seam %s %s" % (plate_no + 1, part.label(), setup.seam.name,
                                                                  problem))
                else:
                    seam = _seam_function(line, settings, painted, who)
            stl = props.part_path(scene, project, plate, part)
            parts.append(build3mf.PartSpec(part.label(), stl, setup.up, setup.angle, part.copies, seam,
                                           mirror=setup.mirror, source=_source_file(scene, project, stl),
                                           spots=props.spots(part), object_meta=props.pairs(setup.orca_object),
                                           part_meta=props.pairs(setup.orca_part)))
            parts[-1].where = (plate_index, part_index)  # to mark the tab's part after the build
        plates.append(build3mf.PlateSpec(plate.name, plate.gap, parts, meta=props.pairs(plate.orca_meta)))
    template = props.absolute(project.template)
    roots = props.roots(scene)
    return build3mf.ProjectSpec(props.project_path(scene, project), plates, template,
                                shown=lambda p: paths.shown(p, *roots),
                                out_path=props.build_path(scene, project),
                                profiles=props.load_json(project.profiles, {}),
                                metadata=props.load_json(project.orca_metadata, {}),
                                profiles_from="the import of " + project.profiles_from), problems


def _record_spots(project, spec):
    """Writes where each copy went into the tab's parts, so the next Build puts it there again."""
    for plate in spec.plates:
        for part_spec in plate.parts:
            plate_index, part_index = getattr(part_spec, "where", (-1, -1))
            if 0 <= plate_index < len(project.plates) and 0 <= part_index < len(project.plates[plate_index].parts):
                if part_spec.spots_out:
                    props.set_spots(project.plates[plate_index].parts[part_index], part_spec.spots_out)


def _source_file(scene, project, stl):
    """The STL path written into the 3MF: from the 3MF's folder when the STL is below the STL root (Orca reads a
    relative source_file from there), else the full path."""
    if paths.relative_to(stl, props.stl_root(scene)) == stl:
        return stl
    return paths.relative_form(stl, os.path.dirname(props.project_path(scene, project)))


def _seam_function(line, settings, painted, who):
    width, snap = settings.seam_width, settings.snap_distance  # now: the build may paint later, in steps
    painter = seams.SeamPainter([line], width=width, snap=snap, min_share=0.0)

    def paint(path, mesh):
        key = (os.path.normcase(path), who, line.name, width, snap)
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

    def _projects(self, context):
        settings = context.scene.orca_reload
        if self.index >= 0:
            return [settings.projects[self.index]] if self.index < len(settings.projects) else []
        return [p for p in settings.projects if p.use]

    def execute(self, context):
        """Builds at once (from a script, or with no window to show the progress in)."""
        projects = self._projects(context)
        if not projects:
            self.report({'ERROR'}, "No project to build")
            return {'CANCELLED'}
        for _ in _build_steps(self, context, projects):
            pass
        return {'FINISHED'}

    def invoke(self, context, event):
        """Builds one part per step, with a progress bar at the end of the row; the row's Build button turns into
        a Cancel button."""
        projects = self._projects(context)
        if not projects:
            self.report({'ERROR'}, "No project to build")
            return {'CANCELLED'}
        wm = context.window_manager
        if context.window is None:  # no window to show the progress in
            return self.execute(context)
        if props.building() != props.BUILD_IDLE:
            self.report({'WARNING'}, "A build is running")
            return {'CANCELLED'}
        self._steps = _build_steps(self, context, projects)
        props.set_building(self.index if self.index >= 0 else props.BUILD_ALL)
        wm.orca_reload_progress = 0.0
        wm.orca_reload_status = "Starting... (0.0s)"
        self._start = time.monotonic()
        self._timer = wm.event_timer_add(0.01, window=context.window)
        wm.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        try:
            return self._step(context, event)
        except Exception:  # never leave the Build buttons greyed out
            self._steps.close()
            self._finish(context)
            raise

    def _step(self, context, event):
        wm = context.window_manager
        if props.cancel_requested():
            self._steps.close()  # writes the log of what was built so far
            self._finish(context)
            self.report({'WARNING'}, "Build cancelled")
            return {'CANCELLED'}
        if event.type != 'TIMER':
            return {'PASS_THROUGH'}
        try:
            done, total, status = next(self._steps)
        except StopIteration:
            self._finish(context)
            return {'FINISHED'}
        wm.orca_reload_progress = done / max(1, total)
        wm.orca_reload_status = "%s | %.1fs" % (status, time.monotonic() - self._start)
        _redraw(context)
        return {'PASS_THROUGH'}

    def _finish(self, context):
        wm = context.window_manager
        wm.event_timer_remove(self._timer)
        props.set_building(props.BUILD_IDLE)
        wm.orca_reload_progress = 0.0
        wm.orca_reload_status = ""
        _redraw(context)


def _redraw(context):
    for window in context.window_manager.windows:
        for area in window.screen.areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()


def _build_steps(operator, context, projects):
    """Builds the projects, one part per step: yields (steps done, steps in all, what comes next: Part 3/12, or
    3MF 1/2 for writing a project). Everything is
    taken from the scene before the first step, so editing the tab while it builds does not change the build.
    Each project then reads its parts' STLs and paints their seams one per step, and writes its 3MF in a step of
    its own. Stopped early (closed), it still writes the log of what it built."""
    scene = context.scene
    stl_cache, painted = {}, {}
    by_path = {}
    for project in projects:
        key = os.path.normcase(os.path.abspath(props.project_path(scene, project)))
        by_path.setdefault(key, []).append(project)
    jobs = []  # (project, ProjectSpec or None, report lines when it cannot be built); the project only as a name
    for project in projects:
        key = os.path.normcase(os.path.abspath(props.project_path(scene, project)))
        if len(by_path[key]) > 1:
            others = ", ".join(sorted(p.name or os.path.basename(key) for p in by_path[key] if p is not project))
            jobs.append((project.name, None, [props.shown(scene, props.project_path(scene, project)),
                                       "  problem: same 3MF file as %s" % others, "  not written"]))
            continue
        props.name_untitled_plates(project)
        spec, problems = project_spec(context, project, painted)
        if problems:
            jobs.append((project.name, None, [spec.shown(spec.path)] + ["  problem: %s" % p for p in problems] +
                         ["  not written"]))
        else:
            jobs.append((project.name, spec, []))
    total = sum(sum(len(plate.parts) for plate in spec.plates) + 1 for _, spec, _ in jobs if spec)
    part_total = sum(len(plate.parts) for _, spec, _ in jobs if spec for plate in spec.plates)
    project_total = sum(1 for _, spec, _ in jobs if spec)
    lines, written, done, stopped = [], 0, 0, True
    part_no = project_no = 0
    try:
        for _, spec, problem_lines in jobs:
            if spec is None:
                lines += problem_lines + [""]
                continue
            for plate in spec.plates:
                for part in plate.parts:
                    part_no += 1
                    yield done, total, "Part %d/%d" % (part_no, part_total)
                    try:  # read and paint now, so the build below finds them ready; it reports any problem
                        mesh, _ = build3mf._load(part, stl_cache)
                        if part.seam:
                            part.seam(part.stl, mesh)
                    except (reload3mf.ReloadError, OSError, ValueError):
                        pass
                    done += 1
            project_no += 1
            yield done, total, "3MF %d/%d" % (project_no, project_total)
            try:
                text, ok = build3mf.build(spec, stl_cache)
            except (reload3mf.ReloadError, OSError, zipfile.BadZipFile, ET.ParseError, ValueError) as e:
                text, ok = [spec.shown(spec.path), "  problem: %s" % e, "  not written"], False
            # Looked up again: the tab may have changed while it built
            now = [p for p in scene.orca_reload.projects
                   if os.path.normcase(os.path.abspath(props.project_path(scene, p))) ==
                   os.path.normcase(os.path.abspath(spec.path))]
            if len(now) == 1 and ok:
                _record_spots(now[0], spec)
            lines += text + [""]
            written += ok
            done += 1
        stopped = False
    finally:
        if stopped:
            lines.append("Stopped: %d of %d projects written" % (written, len(projects)))
        _show_log(context, lines)
        failed = len(projects) - written
        operator.report({'WARNING'} if failed else {'INFO'},
                        "%d of %d projects written%s" % (written, len(projects),
                                                         "; see the Info panel" if failed else ""))


class ORCA_OT_cancel_build(bpy.types.Operator):
    bl_idname = "orca_reload.cancel_build"
    bl_label = "Cancel Build"
    bl_description = "Stop the build. The projects written so far are kept"
    bl_options = {'INTERNAL'}

    def execute(self, context):
        props.request_cancel()
        return {'FINISHED'}


class ORCA_OT_clear_log(bpy.types.Operator):
    bl_idname = "orca_reload.clear_log"
    bl_label = "Clear Log"
    bl_description = "Clear the log of the last build"
    bl_options = {'INTERNAL'}

    def execute(self, context):
        context.window_manager.orca_reload_log.clear()
        return {'FINISHED'}


classes = (ORCA_OT_list_action, ORCA_OT_copy_action, ORCA_OT_add_parts, ORCA_OT_browse_part, ORCA_OT_relink,
           ORCA_OT_overwrite, ORCA_OT_browse_root, ORCA_OT_browse_template, ORCA_OT_import_project,
           ORCA_OT_update_from_3mf, ORCA_OT_add_from_combi, ORCA_OT_update_from_combi, ORCA_OT_own_setup,
           ORCA_OT_load_profiles, ORCA_OT_apply_preset, ORCA_OT_object_setting, ORCA_OT_build,
           ORCA_OT_cancel_build, ORCA_OT_clear_log)
