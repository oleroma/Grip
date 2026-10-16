"""What the Orca tab saves in the .blend file (Scene.orca_reload): the projects, each a 3MF file with plates, each
plate with the parts it holds. Paths of parts are joined from the STL root, the project's and plate's STL folders and
the part's own path, like Combi Export joins its folders."""
import math
import os

import bpy

DEFAULT_GAP = 5.0  # mm between parts on a plate


def _seam_poll(self, obj):
    return obj.type in {'CURVE', 'MESH'}


class OrcaPart(bpy.types.PropertyGroup):
    use: bpy.props.BoolProperty(name="Build", default=True, description="Put this part on its plate")
    name: bpy.props.StringProperty(
        name="Name", description="Name of the part in Orca's object list. Empty: the STL's file name")
    path: bpy.props.StringProperty(
        name="STL", description="The STL file, below the STL root and the project's and plate's STL folders. "
                                "Use / between folders")
    up: bpy.props.FloatVectorProperty(
        name="Up", size=3, subtype='XYZ', default=(0.0, 0.0, 1.0),
        description="The direction of the part (in Blender, as exported) that points up on the build plate. "
                    "0, 0, -1 prints it upside down; 0, 1, 0 lays its front face on the plate")
    angle: bpy.props.FloatProperty(
        name="Turn", subtype='ANGLE', default=0.0, soft_min=-math.pi, soft_max=math.pi,
        description="Turn around the up axis once the part stands on the plate")
    copies: bpy.props.IntProperty(name="Copies", default=1, min=1, soft_max=20,
                                  description="How many of this part go on the plate")
    seam: bpy.props.PointerProperty(
        name="Seam", type=bpy.types.Object, poll=_seam_poll,
        description="Curve or mesh that marks this part's seam: a curve's splines, the edges of a mesh made of edges "
                    "only, or the edges marked as seam of a mesh with faces. Draw it on the part's surface")

    def label(self):
        return self.name or os.path.basename(self.path.replace("\\", "/")) or "part"


class OrcaPlate(bpy.types.PropertyGroup):
    use: bpy.props.BoolProperty(name="Build", default=True, description="Put this plate in the project")
    name: bpy.props.StringProperty(name="Name", default="Plate", description="Name of the plate in Orca")
    gap: bpy.props.FloatProperty(
        name="Gap", subtype='DISTANCE', default=DEFAULT_GAP, min=0.0, soft_max=30.0, precision=1,
        description="Space between the parts on this plate, and half of it to the plate's edge")
    stl_folder: bpy.props.StringProperty(
        name="STL folder", description="Folder of this plate's parts, below the project's STL folder. "
                                       "Use / between folders")
    parts: bpy.props.CollectionProperty(type=OrcaPart)
    part_index: bpy.props.IntProperty()


class OrcaProject(bpy.types.PropertyGroup):
    use: bpy.props.BoolProperty(name="Build", default=True, description="Build this project with Build all")
    name: bpy.props.StringProperty(name="Name", default="project", description="File name of the project, without .3mf")
    folder: bpy.props.StringProperty(
        name="Folder", description="Folder of the 3MF file, below the 3MF root. Use / between folders")
    stl_folder: bpy.props.StringProperty(
        name="STL folder", description="Folder of this project's parts, below the STL root. Use / between folders")
    template: bpy.props.StringProperty(
        name="Settings from", subtype='FILE_PATH',
        description="An Orca project (.3mf) whose printer, process and filament settings a new project starts "
                    "with; the bed size comes from it too. Once the project exists, its own settings are kept")
    plates: bpy.props.CollectionProperty(type=OrcaPlate)
    plate_index: bpy.props.IntProperty()


class OrcaLogLine(bpy.types.PropertyGroup):
    text: bpy.props.StringProperty()
    icon: bpy.props.StringProperty(default='BLANK1')


class OrcaSettings(bpy.types.PropertyGroup):
    stl_root: bpy.props.StringProperty(
        name="STL root", subtype='DIR_PATH',
        description="Folder the parts' STL paths start from. Empty: Combi Export's root")
    project_root: bpy.props.StringProperty(
        name="3MF root", subtype='DIR_PATH', default="//../orca_slicer/",
        description="Folder the projects' 3MF files are saved in. Empty: the .blend file's folder")
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


def _abs(path):
    return os.path.normpath(bpy.path.abspath(path)) if path else ""


def stl_root(scene):
    """The STL root: ours, else Combi Export's (when it is installed), else the .blend file's folder."""
    settings = scene.orca_reload
    if settings.stl_root:
        return _abs(settings.stl_root)
    combi = getattr(scene, "batch_stl_root_dir", "")
    if combi:
        return _abs(combi)
    return _abs("//")


def _join(base, *subs):
    """base joined with folders written with / (or \\) between names; an absolute folder starts over."""
    path = base
    for sub in subs:
        sub = sub.replace("\\", "/")
        if os.path.isabs(sub) or sub[1:2] == ":":
            path = sub
        else:
            path = os.path.join(path, *[p for p in sub.split("/") if p])
    return os.path.normpath(path) if path else path


def plate_folder(scene, project, plate):
    return _join(stl_root(scene), project.stl_folder, plate.stl_folder if plate else "")


def part_path(scene, project, plate, part):
    path = part.path.replace("\\", "/")
    if os.path.isabs(path) or path.startswith("//"):
        return _abs(path)
    return _join(plate_folder(scene, project, plate), path)


def project_root(scene):
    """The 3MF root; empty is the .blend file's folder."""
    return _abs(scene.orca_reload.project_root or "//")


def project_path(scene, project):
    name = project.name if project.name.lower().endswith(".3mf") else project.name + ".3mf"
    return _join(_join(project_root(scene), project.folder), name)


def relative_to(path, base):
    """`path` below `base` with / between folders, or the absolute path when it is not below it."""
    try:
        rel = os.path.relpath(path, base)
    except ValueError:  # another drive
        return path
    return path if rel.startswith("..") else rel.replace("\\", "/")


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


classes = (OrcaPart, OrcaPlate, OrcaProject, OrcaLogLine, OrcaSettings)


def register_properties():
    bpy.types.Scene.orca_reload = bpy.props.PointerProperty(type=OrcaSettings)
    wm = bpy.types.WindowManager
    wm.orca_reload_log = bpy.props.CollectionProperty(type=OrcaLogLine)
    wm.orca_reload_log_index = bpy.props.IntProperty()
    wm.orca_reload_tips = bpy.props.BoolProperty(name="Guide", default=False)


def unregister_properties():
    wm = bpy.types.WindowManager
    del wm.orca_reload_tips
    del wm.orca_reload_log_index
    del wm.orca_reload_log
    del bpy.types.Scene.orca_reload
