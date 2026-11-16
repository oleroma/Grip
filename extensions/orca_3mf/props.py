"""What the Orca tab saves in the .blend file (Scene.orca_reload): the projects, each a 3MF file with plates, each
plate with the parts it holds. Paths of parts are joined from the STL root, the project's and plate's STL folders and
the part's own path, like Combi Export joins its folders."""
import math
import os

import bpy

from . import combi, paths
from .paths import relative_to  # noqa: F401  (used by the operators)

DEFAULT_GAP = 5.0  # mm between parts on a plate


def _seam_poll(self, obj):
    return obj.type in {'CURVE', 'MESH'}


def _clear_mark(self, context):
    self.mark = 'NONE'
    self.mark_note = ""


MARKS = (('NONE', "None", "Nothing to check"),
         ('WARNING', "Check", "Works, but check it"),
         ('ERROR', "Not sure", "Not sure, so nothing was taken"))


class OrcaCopy(bpy.types.PropertyGroup):
    placed: bpy.props.BoolProperty(
        name="Placed", default=False,
        description="This copy has its spot. Off: the next Build nests it in free space and records where it went")
    x: bpy.props.FloatProperty(
        name="X", subtype='DISTANCE', precision=2,
        description="Where the centre of the copy's footprint stands, from the plate's front left corner")
    y: bpy.props.FloatProperty(
        name="Y", subtype='DISTANCE', precision=2,
        description="Where the centre of the copy's footprint stands, from the plate's front left corner")
    turn: bpy.props.FloatProperty(
        name="Turn", subtype='ANGLE', soft_min=-math.pi, soft_max=math.pi,
        description="Turn of this copy around the vertical, on top of the part's own Turn")


def _get_copies(self):
    n = len(self.instances)
    if n:
        return n
    try:
        return max(1, int(self.get("copies", 1)))  # saved before each copy had its spot
    except (TypeError, ValueError):
        return 1


def _set_copies(self, value):
    value = max(1, int(value))
    if not len(self.instances):
        for _ in range(_get_copies(self)):
            self.instances.add()
    while len(self.instances) < value:
        self.instances.add()
    while len(self.instances) > value:
        self.instances.remove(len(self.instances) - 1)


SETUP_KEYS = ("up", "angle", "mirror", "seam", "orca_object", "orca_part")  # what a part shares with its object


class OrcaSetup(bpy.types.PropertyGroup):
    """How the parts exported from a Blender object stand and print (Object.orca_reload_setup): every linked part
    without "Own setup" uses it, on every plate of every project."""
    has: bpy.props.BoolProperty(options={'HIDDEN'})  # set once a part was linked: the values below are in use
    up: bpy.props.FloatVectorProperty(
        name="Up", size=3, subtype='XYZ', default=(0.0, 0.0, 1.0),
        description="The direction of the object (in Blender, as exported) that points up on the build plate, for "
                    "every part exported from it")
    angle: bpy.props.FloatProperty(
        name="Turn", subtype='ANGLE', default=0.0, soft_min=-math.pi, soft_max=math.pi,
        description="Turn around the up axis once the part stands on the plate")
    mirror: bpy.props.BoolProperty(name="Mirror", default=False,
                                   description="Mirror the parts across their own X axis before standing them up")
    seam: bpy.props.PointerProperty(
        name="Seam", type=bpy.types.Object, poll=_seam_poll,
        description="Curve or mesh that marks the seam of every part exported from this object. It is snapped "
                    "onto each part's surface, so one line serves every tolerance")
    orca_object: bpy.props.StringProperty(options={'HIDDEN'})  # Orca object settings (JSON pairs)
    orca_part: bpy.props.StringProperty(options={'HIDDEN'})  # Orca part settings (JSON pairs)


class OrcaPart(bpy.types.PropertyGroup):
    use: bpy.props.BoolProperty(name="Build", default=True, description="Put this part on its plate")
    name: bpy.props.StringProperty(
        name="Name", description="Name of the part in Orca's object list. Empty: the STL's file name")
    path: bpy.props.StringProperty(
        name="STL", description="The STL file, below the STL root and the project's and plate's STL folders. "
                                "Use / between folders", update=_clear_mark)
    mark: bpy.props.EnumProperty(name="Mark", items=MARKS, default='NONE',
                                 description="What the last Import or Build found about this part")
    mark_note: bpy.props.StringProperty(name="Why", description="Why the part is marked")
    up: bpy.props.FloatVectorProperty(
        name="Up", size=3, subtype='XYZ', default=(0.0, 0.0, 1.0),
        description="The direction of the part (in Blender, as exported) that points up on the build plate. "
                    "0, 0, -1 prints it upside down; 0, 1, 0 lays its front face on the plate")
    angle: bpy.props.FloatProperty(
        name="Turn", subtype='ANGLE', default=0.0, soft_min=-math.pi, soft_max=math.pi,
        description="Turn around the up axis once the part stands on the plate")
    instances: bpy.props.CollectionProperty(type=OrcaCopy)
    instance_index: bpy.props.IntProperty()
    copies: bpy.props.IntProperty(name="Copies", min=1, soft_max=20, get=_get_copies, set=_set_copies,
                                  description="How many of this part go on the plate. A new copy is nested by the "
                                              "next Build, which records its spot")
    orca_object: bpy.props.StringProperty(
        options={'HIDDEN'}, description="The object's own Orca settings, saved by Import (JSON key, value pairs)")
    orca_part: bpy.props.StringProperty(
        options={'HIDDEN'}, description="The part's own Orca settings, saved by Import (JSON key, value pairs)")
    mirror: bpy.props.BoolProperty(
        name="Mirror", default=False,
        description="Mirror the part across its own X axis before standing it up: a part mirrored in Orca "
                    "imports as its original shape with this ticked, and builds back mirrored")
    seam: bpy.props.PointerProperty(
        name="Seam", type=bpy.types.Object, poll=_seam_poll,
        description="Curve or mesh that marks this part's seam: a curve's splines, the edges of a mesh made of edges "
                    "only, or the edges marked as seam of a mesh with faces. Draw it on the part's surface")
    source: bpy.props.PointerProperty(
        name="Object", type=bpy.types.Object,
        description="The Blender object this part's STL is exported from (Combi Export says which). Up, Turn, "
                    "Mirror, Seam and the Orca part settings are then the object's, shared by every part "
                    "exported from it, unless Own setup is ticked")
    own: bpy.props.BoolProperty(
        name="Own setup", default=False,
        description="This part keeps its own Up, Turn, Mirror, Seam and Orca part settings instead of its "
                    "object's")

    def label(self):
        return self.name or os.path.basename(self.path.replace("\\", "/")) or "part"


class OrcaPlate(bpy.types.PropertyGroup):
    use: bpy.props.BoolProperty(name="Build", default=True, description="Put this plate in the project")
    name: bpy.props.StringProperty(
        name="Name", default="Plate",
        description="Name of the plate in Orca. With \"Plate names are folders\" on, also its folder below the "
                    "project's STL folder (tight/cap_loose): renaming it points the plate at another folder, red "
                    "when there is no such folder")
    gap: bpy.props.FloatProperty(
        name="Gap", subtype='DISTANCE', default=DEFAULT_GAP, min=0.0, soft_max=30.0, precision=1,
        description="Space between the parts on this plate, and half of it to the plate's edge")
    stl_folder: bpy.props.StringProperty(
        name="STL folder", description="Folder of this plate's parts, below the project's STL folder. "
                                       "Use / between folders")
    orca_meta: bpy.props.StringProperty(
        options={'HIDDEN'}, description="The plate's own Orca settings, saved by Import (JSON key, value pairs)")
    parts: bpy.props.CollectionProperty(type=OrcaPart)
    part_index: bpy.props.IntProperty()


_combi_items = []  # kept alive here: Blender keeps no copy of the strings an items callback returns


def _combi_preset_items(self, context):
    scene = context.scene if context is not None else bpy.context.scene
    _combi_items[:] = [('NONE', "None", "Not linked to a Combi Export preset", 'BLANK1', 0)]
    _combi_items.extend((key, name, "Combi Export preset " + name, 'PRESET', i + 1)
                        for i, (key, name) in enumerate(combi.presets(scene)))
    if self.combi_preset and not any(item[0] == self.combi_preset for item in _combi_items):
        _combi_items.append((self.combi_preset, "missing preset", "This Combi Export preset is gone", 'ERROR',
                             len(_combi_items)))
    return _combi_items


def _get_combi_preset_pick(self):
    for key, _name, _tip, _icon, number in _combi_preset_items(self, None):
        if key == self.combi_preset:
            return number
    return 0


def _set_combi_preset_pick(self, value):
    for key, _name, _tip, _icon, number in _combi_preset_items(self, None):
        if number == value:
            self.combi_preset = "" if key == 'NONE' else key
            return


class OrcaCombiFile(bpy.types.PropertyGroup):
    """A file a Combi preset writes, in the Add from Combi window (WindowManager, not saved)."""
    pick: bpy.props.BoolProperty(name="Add", description="Add this file to the plate")
    name: bpy.props.StringProperty()  # file name
    path: bpy.props.StringProperty()  # absolute
    shown: bpy.props.StringProperty()  # its folder below Combi's root
    object: bpy.props.StringProperty()  # the Blender object it is exported from
    on_plate: bpy.props.BoolProperty()  # the plate already has it
    exists: bpy.props.BoolProperty()  # written by an export already


class OrcaProject(bpy.types.PropertyGroup):
    use: bpy.props.BoolProperty(name="Build", default=True, description="Build this project with Build all")
    name: bpy.props.StringProperty(name="Name", default="project", description="File name of the project, without .3mf")
    folder: bpy.props.StringProperty(
        name="Folder", description="Folder of the 3MF file, below the 3MF root. Use / between folders")
    stl_folder: bpy.props.StringProperty(
        name="STL folder", description="Folder of this project's parts, below the STL root. Use / between folders")
    template: bpy.props.StringProperty(
        name="Settings from",
        description="An Orca project (.3mf) whose printer, process and filament settings a new project starts "
                    "with; the bed size comes from it too. Not used once Import or Update from 3MF saved the "
                    "project's own settings. "
                    "A relative path (../printer.3mf) starts at the .blend file's folder")
    plate_paths: bpy.props.BoolProperty(
        name="Plate names are folders",
        description="Each plate's name is its folder, below the project's STL folder (tight/cap_loose), and its "
                    "parts' paths start there: renaming a plate points it at another folder. Turning it on names "
                    "each plate after the deepest folder its parts share. When Orca keeps only a part's file name, "
                    "Import takes the file from the plate's folder or a folder above it. Off: plate names are only "
                    "names, and each plate has its own STL folder",
        update=lambda self, context: plate_paths_changed(context.scene, self))
    plate_paths_was: bpy.props.BoolProperty(options={'HIDDEN'})  # what the parts' paths were written for
    overwrite: bpy.props.BoolProperty(
        name="Overwrite",
        description="On: Build writes into the project's 3MF itself. Off: the 3MF is never changed once it "
                    "exists; each Build writes the next file into the 3mf_builds folder next to it "
                    "(project.3mf, then project_001.3mf, project_002.3mf, ...)")
    profiles: bpy.props.StringProperty(
        options={'HIDDEN'},
        description="The printer, process and filament settings saved by Import (JSON: file in the 3MF -> text)")
    profiles_from: bpy.props.StringProperty(
        name="Settings saved from", description="The 3MF the saved printer, process and filament settings came from")
    orca_metadata: bpy.props.StringProperty(options={'HIDDEN'})  # the Orca version that wrote them (JSON)
    combi_preset: bpy.props.StringProperty(options={'HIDDEN'})  # the Combi Export preset's uid (combi.find_preset)
    combi_preset_pick: bpy.props.EnumProperty(
        name="Combi preset", items=_combi_preset_items, get=_get_combi_preset_pick, set=_set_combi_preset_pick,
        description="The Combi Export preset this project's parts come from: Add from Combi lists its files and "
                    "Update from Combi checks the parts against them. Renaming the preset keeps the link")
    plates: bpy.props.CollectionProperty(type=OrcaPlate)
    plate_index: bpy.props.IntProperty()


class OrcaLogLine(bpy.types.PropertyGroup):
    text: bpy.props.StringProperty()
    icon: bpy.props.StringProperty(default='BLANK1')


class OrcaSettings(bpy.types.PropertyGroup):
    stl_root: bpy.props.StringProperty(
        name="STL root",
        description="Folder the parts' STL paths start from. Empty: Combi Export's root. A relative path "
                    "(../stl) starts at the .blend file's folder")
    project_root: bpy.props.StringProperty(
        name="3MF root", default="../orca_slicer",
        description="Folder the projects' 3MF files are saved in. Empty: the .blend file's folder. A relative "
                    "path (../orca_slicer) starts at the .blend file's folder")
    projects: bpy.props.CollectionProperty(type=OrcaProject)
    project_index: bpy.props.IntProperty()
    seam_width: bpy.props.FloatProperty(
        name="Seam width", subtype='DISTANCE', default=0.6, min=0.05, soft_max=3.0, precision=2,
        description="Width of the seam strip painted along each seam line. Orca puts the seam where a "
                    "perimeter crosses the strip, in its middle; about one line width is enough")
    snap_distance: bpy.props.FloatProperty(
        name="Snap", subtype='DISTANCE', default=1.0, min=0.0, soft_max=5.0, precision=2,
        description="How far a seam line may be from its part's surface and still be painted onto it. "
                    "Variants with other tolerances move the surface a little")


# --------------------------------------------------------------------------
# Lookups and paths


def active(collection, index):
    return collection[index] if 0 <= index < len(collection) else None


def active_project(settings):
    return active(settings.projects, settings.project_index)


def active_plate(project):
    return active(project.plates, project.plate_index) if project else None


def active_part(plate):
    return active(plate.parts, plate.part_index) if plate else None


def absolute(path):
    """A saved root or file as an absolute path: // and a relative path (../stl) start at the .blend file's folder."""
    return paths.absolute(path, os.path.dirname(bpy.data.filepath))


def blend_relative(path):
    """A picked folder or file as it is saved: from the .blend file's folder (../stl), or absolute while the .blend
    is not saved or the path is on another drive."""
    return paths.relative_form(path, os.path.dirname(bpy.data.filepath))


def stl_root(scene):
    """The STL root: ours, else Combi Export's (when it is installed), else the .blend file's folder."""
    settings = scene.orca_reload
    if settings.stl_root:
        return absolute(settings.stl_root)
    combi = getattr(scene, "batch_stl_root_dir", "")
    if combi:
        return absolute(combi)
    return absolute("//")


def set_mark(part, level, note):
    """Marks a part (MARKS) with the reason; a red mark is not lowered to yellow."""
    if part.mark == 'ERROR' and level == 'WARNING':
        return
    part.mark = level
    part.mark_note = note


def part_mark(scene, project, plate, part):
    """(level, why) of a part as the tab shows it: red when its STL is missing or the last Import was not sure.
    A file picked by hand is never marked: Update from 3MF keeps the tab's links."""
    path = part_path(scene, project, plate, part) if part.path else ""
    if not path or not os.path.isfile(path):
        return 'ERROR', part.mark_note or ("no STL file" if not path else "STL not found")
    if part.mark != 'NONE':
        return part.mark, part.mark_note
    return 'NONE', ""


def in_plate_folders(scene, project, plate, path):
    """Whether path is in the plate's folder or a folder above it, up to the project's STL folder."""
    rel = paths.relative_form(os.path.dirname(path), plate_folder(scene, project, plate)).replace("\\", "/")
    if rel != "." and any(p != ".." for p in rel.split("/")):
        return False
    top = os.path.normcase(os.path.abspath(project_stl_folder(scene, project)))
    folder = os.path.normcase(os.path.abspath(os.path.dirname(path)))
    return folder == top or folder.startswith(top.rstrip(os.sep) + os.sep)


def project_stl_folder(scene, project):
    """The project's STL folder: the STL root joined with the project's STL folder."""
    return paths.join(stl_root(scene), project.stl_folder)


def plate_folder(scene, project, plate, by_name=None):
    """The plate's folder: its name below the project's STL folder while "Plate names are folders" is on (by_name),
    else its own STL folder."""
    by_name = project.plate_paths if by_name is None else by_name
    if by_name and plate is not None and plate.name:
        from . import build3mf
        return build3mf.plate_dir(project_stl_folder(scene, project), plate.name)
    sub = (plate.name if by_name else plate.stl_folder) if plate else ""
    return paths.join(stl_root(scene), project.stl_folder, sub)


def folder_name(scene, project, folder):
    """The plate name for a folder below (or at) the project's STL folder: its path from there, or the STL
    folder's own name for the STL folder itself."""
    top = project_stl_folder(scene, project)
    rel = paths.relative_form(folder, top)
    if rel == ".":
        return os.path.basename(os.path.normpath(top))
    return rel


def deepest_line_folder(folders):
    """The deepest of the folders when every other one is it or a folder above it, else None."""
    folders = [os.path.normpath(os.path.abspath(f)) for f in folders]
    if not folders:
        return None
    leaf = max(folders, key=len)
    key = os.path.normcase(leaf)
    for f in folders:
        k = os.path.normcase(f)
        if not (key == k or key.startswith(k.rstrip(os.sep) + os.sep)):
            return None
    return leaf


def move_plate(scene, project, plate, folder=None, name=None):
    """Points the plate at another folder (or, with the switch on, gives it another name), keeping the file of
    every part that is there: their paths are written again from the new folder. Marks stay."""
    stls = [part_path(scene, project, plate, p) if p.path else "" for p in plate.parts]
    marks = [(p.mark, p.mark_note) for p in plate.parts]
    if name is not None:
        plate.name = name
    if folder is not None:
        if project.plate_paths:
            plate.name = folder_name(scene, project, folder)
        else:
            rel = paths.relative_form(folder, project_stl_folder(scene, project))
            plate.stl_folder = "" if rel == "." else rel
    for part, stl, (mark, note) in zip(plate.parts, stls, marks):
        if stl and os.path.isfile(stl):  # a missing part keeps what Orca stored (often only its name)
            part.path = part_relative(scene, project, plate, stl)
            part.mark, part.mark_note = mark, note  # changing the path clears them


def name_plate_from_parts(scene, project, plate, fallback=None, whole=False):
    """With "Plate names are folders" on: names the plate after the deepest folder its found parts share, when they
    sit in one line of folders below the project's STL folder (else after fallback, a folder, when given). whole:
    only when none of its parts is missing. Every part keeps its file. True when it was named."""
    if not project.plate_paths:
        return False
    stls = [part_path(scene, project, plate, p) if p.path else "" for p in plate.parts]
    found = [s for s in stls if s and os.path.isfile(s)]
    if not found or (whole and len(found) != len(stls)):
        return False
    leaf = deepest_line_folder([os.path.dirname(s) for s in found])
    top = os.path.normcase(os.path.abspath(project_stl_folder(scene, project)))
    if leaf is not None and (os.path.normcase(leaf) == top
                             or os.path.normcase(leaf).startswith(top.rstrip(os.sep) + os.sep)):
        move_plate(scene, project, plate, folder=leaf)
        return True
    if fallback:
        move_plate(scene, project, plate, folder=fallback)
        return True
    return False


def setup(part):
    """Where the part's Up, Turn, Mirror, Seam and Orca part settings live: its object's setup when it is linked
    to one and not set to Own setup, else the part itself (both have the SETUP_KEYS)."""
    if part.source is not None and not part.own:
        return part.source.orca_reload_setup
    return part


def _setup_values(item):
    return {"up": tuple(round(v, 6) for v in item.up), "angle": round(item.angle, 6), "mirror": item.mirror,
            "seam": item.seam, "orca_object": item.orca_object, "orca_part": item.orca_part}


def copy_setup(source, target):
    for key in SETUP_KEYS:
        setattr(target, key, getattr(source, key))


def link_part(part, obj, fresh=False):
    """Links the part to obj, the Blender object its STL is exported from. An object without a setup yet takes the
    part's values. A fresh part (just added) follows the object's setup; an existing part whose values differ
    from it keeps them as its Own setup and is marked, so nothing it had is lost. Returns True when marked."""
    part.source = obj
    shared = obj.orca_reload_setup
    if not shared.has:
        copy_setup(part, shared)
        shared.has = True
        part.own = False
        return False
    if fresh or _setup_values(part) == _setup_values(shared):
        part.own = False
        return False
    part.own = True
    set_mark(part, 'WARNING', "set up differently from its object %s: kept as its own setup (untick Own setup "
                              "to take the object's)" % obj.name)
    return True


def set_own_setup(part, own):
    """Own setup ticked: the part starts from its object's values. Unticked: it follows the object again."""
    if own and part.source is not None and not part.own:
        copy_setup(part.source.orca_reload_setup, part)
    part.own = own


def sharing(scene, obj):
    """How many parts of the scene's projects follow obj's setup."""
    return sum(1 for project in scene.orca_reload.projects for plate in project.plates for part in plate.parts
               if part.source == obj and not part.own)


def name_untitled_plates(project):
    """Plates without a name get one, Plate 3 for the third plate Build writes (the next free number when that name
    is taken), so Update from 3MF can tell them apart. With "Plate names are folders" on, a name is a folder: left
    alone."""
    if project.plate_paths:
        return
    names = {p.name for p in project.plates}
    number = 0
    for plate in project.plates:
        if not plate.use:
            continue
        number += 1
        if plate.name.strip():
            continue
        n = number
        while "Plate %d" % n in names:
            n += 1
        plate.name = "Plate %d" % n
        names.add(plate.name)


def plate_paths_changed(scene, project):
    """"Plate names are folders" was turned on or off: every part keeps its file. Turned on, each plate is named
    after the deepest folder its parts share, when they all sit in one line of folders below the project's STL
    folder; turned off, each plate's STL folder becomes the folder its name pointed at."""
    on = project.plate_paths
    if on == project.plate_paths_was:  # set to what it was: nothing to move
        return
    project.plate_paths_was = on
    top = project_stl_folder(scene, project)
    for plate in project.plates:
        stls_before = {}
        for part in plate.parts:  # where each part was, read the old way
            if part.path:
                stls_before[part.as_pointer()] = paths.join(plate_folder(scene, project, plate, by_name=not on),
                                                            part.path) if not part.path.startswith("//") else \
                    absolute(part.path)
        found = [s for s in stls_before.values() if os.path.isfile(s)]
        marks = [(p.mark, p.mark_note) for p in plate.parts]
        if on:
            leaf = deepest_line_folder([os.path.dirname(s) for s in found])
            inside = leaf is not None and (os.path.normcase(leaf) == os.path.normcase(os.path.abspath(top)) or
                                           os.path.normcase(leaf).startswith(
                                               os.path.normcase(os.path.abspath(top)).rstrip(os.sep) + os.sep))
            if inside:
                plate.name = folder_name(scene, project, leaf)
        else:
            old = plate_folder(scene, project, plate, by_name=True)
            rel = paths.relative_form(old, top)
            plate.stl_folder = "" if rel == "." else rel
        for part, (mark, note) in zip(plate.parts, marks):
            stl = stls_before.get(part.as_pointer())
            if stl and os.path.isfile(stl):
                part.path = part_relative(scene, project, plate, stl)
                part.mark, part.mark_note = mark, note


def part_path(scene, project, plate, part):
    if part.path.startswith("//"):
        return absolute(part.path)
    return paths.join(plate_folder(scene, project, plate), part.path)


def part_relative(scene, project, plate, path):
    """A part's STL as it is saved: from its plate's folder (../shared/box.stl when outside it), or absolute when there
    is no way there from that folder (the .blend is not saved and the STL root is relative, or another drive)."""
    return paths.relative_form(path, plate_folder(scene, project, plate))


def roots(scene):
    """(3MF root, STL root, .blend file's folder), as paths.shown takes them."""
    return project_root(scene), stl_root(scene), os.path.dirname(bpy.data.filepath)


def shown(scene, path):
    """A path as the tab shows it (paths.shown)."""
    return paths.shown(path, *roots(scene))


def project_root(scene):
    """The 3MF root; empty is the .blend file's folder."""
    return absolute(scene.orca_reload.project_root or "//")


def project_path(scene, project):
    name = project.name if project.name.lower().endswith(".3mf") else project.name + ".3mf"
    return paths.join(project_root(scene), project.folder, name)


def load_json(text, default):
    import json
    try:
        value = json.loads(text) if text else default
    except (ValueError, TypeError):
        return default
    return value if isinstance(value, type(default)) else default


def dump_json(value):
    import json
    return json.dumps(value, separators=(",", ":"))


def pairs(text):
    """[(key, value)] saved as JSON."""
    return [tuple(p) for p in load_json(text, []) if isinstance(p, list) and len(p) == 2]


def spots(part):
    """(x, y, turn) of each copy of the part, None for a copy without its spot."""
    if not len(part.instances):
        return [None] * part.copies
    return [(c.x, c.y, c.turn) if c.placed else None for c in part.instances]


def set_spots(part, values):
    """Records where each copy stands (None: not placed)."""
    part.copies = max(1, len(values))
    for c, spot in zip(part.instances, values):
        c.placed = spot is not None
        if spot is not None:
            c.x, c.y, c.turn = spot


def build_path(scene, project):
    """Where Build writes the project: the 3MF itself while it does not exist or Overwrite is on, else its next
    numbered build in 3mf_builds."""
    from . import build3mf
    path = project_path(scene, project)
    if project.overwrite or not os.path.isfile(path):
        return path
    return build3mf.next_build_path(path)


# --------------------------------------------------------------------------
# Copy and paste between list items


def to_dict(item):
    data = {}
    for prop in item.bl_rna.properties:
        key = prop.identifier
        if key in {"rna_type"}:
            continue
        if prop.type == 'COLLECTION':
            data[key] = [to_dict(sub) for sub in getattr(item, key)]
        elif prop.type == 'POINTER':
            data[key] = getattr(item, key)
        elif getattr(prop, "is_array", False):
            data[key] = tuple(getattr(item, key))
        else:
            data[key] = getattr(item, key)
    return data


def from_dict(item, data):
    for key, value in data.items():
        if isinstance(value, list):
            coll = getattr(item, key)
            coll.clear()
            for sub in value:
                from_dict(coll.add(), sub)
        else:
            try:
                setattr(item, key, value)
            except (AttributeError, TypeError, ReferenceError):
                pass


classes = (OrcaCopy, OrcaSetup, OrcaPart, OrcaPlate, OrcaCombiFile, OrcaProject, OrcaLogLine, OrcaSettings)


BUILD_IDLE, BUILD_ALL = -2, -1  # building(): no build, Build all, else the project's index
_building = {"which": BUILD_IDLE, "cancel": False}  # here, not in the .blend: a restart starts with no build


def building():
    """Which build runs now: BUILD_IDLE, BUILD_ALL or the index of the project."""
    return _building["which"]


def set_building(which):
    _building.update(which=which, cancel=False)


def request_cancel():
    _building["cancel"] = True


def cancel_requested():
    return _building["cancel"]


def register_properties():
    bpy.types.Scene.orca_reload = bpy.props.PointerProperty(type=OrcaSettings)
    bpy.types.Object.orca_reload_setup = bpy.props.PointerProperty(type=OrcaSetup)
    wm = bpy.types.WindowManager
    wm.orca_reload_log = bpy.props.CollectionProperty(type=OrcaLogLine)
    wm.orca_reload_log_index = bpy.props.IntProperty()
    wm.orca_reload_tips = bpy.props.BoolProperty(name="Guide", default=False)
    wm.orca_reload_copies = bpy.props.BoolProperty(name="Show copies", default=False,
                                                   description="Show where each copy of the part stands")
    # How far the build in progress is, and what it does now
    wm.orca_reload_progress = bpy.props.FloatProperty(name="Progress", default=0.0, min=0.0, max=1.0)
    wm.orca_reload_status = bpy.props.StringProperty(default="")
    wm.orca_reload_combi_files = bpy.props.CollectionProperty(type=OrcaCombiFile)
    wm.orca_reload_combi_index = bpy.props.IntProperty()


def unregister_properties():
    wm = bpy.types.WindowManager
    del wm.orca_reload_combi_index
    del wm.orca_reload_combi_files
    del wm.orca_reload_status
    del wm.orca_reload_progress
    del wm.orca_reload_tips
    del wm.orca_reload_copies
    del wm.orca_reload_log_index
    del wm.orca_reload_log
    del bpy.types.Scene.orca_reload
    del bpy.types.Object.orca_reload_setup
