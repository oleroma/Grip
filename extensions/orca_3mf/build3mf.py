"""Builds OrcaSlicer projects (.3mf) from projects > plates > parts, each part an STL file with an up axis, a turn
around it and a number of copies. Each part is stood up, nested on its plate with the plate's gap and put on the bed.

Building over an existing project keeps what only Orca holds: the printer, process and filament settings, each
part's own settings (matched by name), each plate's settings (by position), and the painting of a part whose shape
did not change (its seams are replaced when it has a seam line). A new project takes its settings from a template
project: Orca opens a project without settings as bare geometry, without its plates, so one is needed.

Only the Python standard library is used, so it runs inside and outside Blender.
"""

import json
import math
import os
import re
import tempfile
import zipfile
import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape, quoteattr

try:
    from . import layout, reload3mf
except ImportError:  # run outside the add-on
    import layout
    import reload3mf

ReloadError = reload3mf.ReloadError
SEAM_ATTR = reload3mf.SEAM_ATTR

SETTINGS = "Metadata/project_settings.config"
APPLICATION = "BambuStudio-02.06.00.51"  # what OrcaSlicer 2.4 writes; it marks the file as an Orca project
ORCA_VERSION = "2.4.2"
MAX_PLATES = 36  # Orca's MAX_PLATE_COUNT
BUILD_UUID = "2c7c17d8-22b5-4d84-8835-1976022ea369"
# Mirror across a part's own X axis: the reflection factored out of a mirrored Orca transform on Import and
# written back on Build.
MIRROR = ((-1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))


def _axis_aligned_rectangle(points):
    """True when all polygon corners are the four corners of an axis-aligned rectangle."""
    if len(points) < 3:
        return False
    lo_x = min(p[0] for p in points)
    hi_x = max(p[0] for p in points)
    lo_y = min(p[1] for p in points)
    hi_y = max(p[1] for p in points)
    corners = {(lo_x, lo_y), (lo_x, hi_y), (hi_x, lo_y), (hi_x, hi_y)}
    return len(corners) == 4 and all(p in corners for p in points)
# Settings files that travel with the printer, process and filament settings
SETTINGS_FILES = re.compile(r"Metadata/(project_settings\.config|print_profile\.config|"
                            r"(print_setting|process_settings|filament_settings|machine_settings)_.*)$")
# Files of an existing project that are kept as they are
KEPT_FILES = re.compile(r"(Metadata/custom_gcode_per_layer\.xml|Auxiliaries/(?!\.thumbnails/).*)$")
# Part settings Orca writes itself; the others are the part's own settings and are kept
PART_KEYS = {"name", "matrix", "source_file", "source_object_id", "source_volume_id", "source_offset_x",
             "source_offset_y", "source_offset_z", "source_in_inches", "source_in_meters"}
PLATE_KEYS = {"plater_id", "plater_name", "thumbnail_file", "thumbnail_no_light_file", "top_file", "pick_file",
              "pattern_file", "pattern_bbox_file"}
# Files keyed by position (not by the <object id> or <plate plater_id> attribute) that Build re-keys on rebuild:
# layer_heights_profile.txt and brim_ear_points.txt use id=<n>/object_id=<n>, layer_config_ranges.xml uses
# <object id="n">, all with the object's 1-based position in the model; custom_gcode_per_layer.xml uses one
# <plate><plate_info id="n"> per plate's 1-based position.
INDEX_OBJECT_FILES = ("Metadata/layer_heights_profile.txt", "Metadata/layer_config_ranges.xml",
                     "Metadata/brim_ear_points.txt")
CUSTOM_GCODE_FILE = "Metadata/custom_gcode_per_layer.xml"


class PartSpec:
    """One part: the STL file (absolute path), the direction of the part that points up on the plate, the turn
    around it (radians), how many copies, a mirror across the part's own X axis, and an optional seam function
    (stl_path, Mesh) -> None or (paint_seam strings by triangle index, note for the report)."""

    def __init__(self, name, stl, up=(0.0, 0.0, 1.0), angle=0.0, copies=1, seam=None, mirror=False):
        self.name = name or os.path.basename(stl)
        self.stl = stl
        self.up = tuple(up)
        self.angle = angle
        self.copies = max(int(copies), 1)
        self.seam = seam
        self.mirror = bool(mirror)


class PlateSpec:
    def __init__(self, name="", gap=6.0, parts=()):
        self.name = name
        self.gap = gap
        self.parts = list(parts)


class ProjectSpec:
    """A project: the 3MF file to write (absolute path), its plates, a template project for the settings of a new
    project, and the bed size used when no settings come with it."""

    def __init__(self, path, plates=(), template="", bed=(256.0, 256.0)):
        self.path = path
        self.plates = list(plates)
        self.template = template
        self.bed = tuple(bed)


# --------------------------------------------------------------------------
# What an existing project or a template brings


class _OldObject:
    def __init__(self, oid, name, meta, part, plates=(), extras=(), index=0):
        self.id = oid
        self.name = name
        self.meta = meta  # object settings, [(key, value)] without the name
        self.part = part  # reload3mf.Part of its one model part, or None
        self.plates = frozenset(plates)  # plate names it sits on
        self.extras = list(extras)  # reload3mf.Parts of its extra volumes (modifiers, negatives, blockers, ...)
        self.index = index  # 1-based position in the old model


def _same_source(a, b):
    """Whether two source_file paths point at the same STL (absolute, or at least the same file name)."""
    a = os.path.normcase(a.replace("\\", "/"))
    b = os.path.normcase(b.replace("\\", "/"))
    return a == b or os.path.basename(a) == os.path.basename(b)


class Base:
    """The settings a build starts from: an existing project (everything below), else a template (its settings
    files only), else nothing."""

    def __init__(self, path=None, template=None):
        self.settings_from = None
        self.files = {}  # zip entry -> bytes, written as they are
        self.metadata = {"Application": APPLICATION, "OrcaSlicer": ORCA_VERSION, "BambuStudio:3mfVersion": "1"}
        self.objects = []  # [_OldObject], in file order
        self.plates = []  # [(name, [(key, value)])] of each plate, in file order
        self._plate_taken = set()
        self.project = None
        if path and os.path.isfile(path):
            self._read_project(path)
            if SETTINGS not in self.files and template:
                # An existing file without printer settings still needs them: take them from Settings from,
                # keeping the file's own metadata.
                if not os.path.isfile(template):
                    raise ReloadError("settings project not found: %s" % template)
                with zipfile.ZipFile(template) as z:
                    self._take_settings(z, template, update_metadata=False)
        elif template:
            if not os.path.isfile(template):
                raise ReloadError("settings project not found: %s" % template)
            with zipfile.ZipFile(template) as z:
                self._take_settings(z, template)

    def _take_settings(self, z, path, update_metadata=True):
        for name in z.namelist():
            if SETTINGS_FILES.match(name):
                self.files[name] = z.read(name)
        if SETTINGS not in self.files:
            return
        self.settings_from = path
        if not update_metadata:
            return
        # The settings were written by this Orca version: say so, or Orca may warn about a newer file
        try:
            root = ET.fromstring(z.read(reload3mf.ROOT_MODEL))
        except (KeyError, ET.ParseError):
            return
        for m in root.findall(reload3mf.CORE_NS + "metadata"):
            if m.get("name") in ("Application", "OrcaSlicer") and m.text:
                self.metadata[m.get("name")] = m.text

    def _read_project(self, path):
        project = reload3mf.Project(path)
        self.project = project
        z = project.zip
        self._take_settings(z, path)
        for name in z.namelist():
            if KEPT_FILES.match(name) or name in INDEX_OBJECT_FILES:
                self.files[name] = z.read(name)
        root = ET.fromstring(z.read(reload3mf.ROOT_MODEL))
        for m in root.findall(reload3mf.CORE_NS + "metadata"):
            if m.get("name") in ("Title", "Designer", "Description", "Copyright", "License", "Origin",
                                 "CreationDate"):
                self.metadata[m.get("name")] = m.text or ""
        settings = ET.fromstring(z.read(reload3mf.MODEL_SETTINGS))
        plate_names = {}
        for plate in settings.findall("plate"):
            pmeta = {m.get("key"): m.get("value") for m in plate.findall("metadata") if m.get("key")}
            name = pmeta.get("plater_name") or ""
            self.plates.append((name, [(k, v) for k, v in pmeta.items() if k not in PLATE_KEYS]))
            try:
                plate_names[int(pmeta["plater_id"])] = name
            except (KeyError, ValueError):
                pass
        model_order = {oid: i + 1 for i, oid in enumerate(getattr(project, "model_order", ()))}
        for o in settings.findall("object"):
            obj = project.objects.get(o.get("id"))
            meta = [(m.get("key"), m.get("value")) for m in o.findall("metadata")
                    if m.get("key") and m.get("key") != "name"]
            models = [p for p in obj.parts if p.is_model_part] if obj else []
            part = models[0] if len(models) == 1 else None
            extras = [p for p in obj.parts if not p.is_model_part] if obj else []
            name = obj.name if obj else o.get("id")
            on = (plate_names[i] for i in getattr(obj, "plates", ()) if i in plate_names) if obj else ()
            self.objects.append(_OldObject(o.get("id"), name, meta, part, on, extras,
                                           model_order.get(o.get("id"), 0)))

    def take_plate(self, name, position):
        """The old plate settings for `name` (once each), else by position (as before), else a fresh plate."""
        for i in range(len(self.plates)):
            if i not in self._plate_taken and self.plates[i][0] == name:
                self._plate_taken.add(i)
                return self.plates[i][1]
        if 0 <= position < len(self.plates) and position not in self._plate_taken:
            self._plate_taken.add(position)
            return self.plates[position][1]
        return [("locked", "false")]

    def take_part(self, spec, plate_name, new_mesh):
        """The old object that best matches the part: by shape, then source file, then plate, then name."""
        center = new_mesh.center()
        best, best_score = None, -1
        for o in self.objects:
            score = 0
            old_mesh = None
            if o.part is not None:
                if o.part.source and _same_source(o.part.source, spec.stl):
                    score += 4
                try:
                    old_mesh = self.project.old_mesh(o.part)
                except ReloadError:
                    old_mesh = None
            if old_mesh is not None:
                shift = tuple(a - b for a, b in zip(old_mesh.center(), center))
                if reload3mf.same_shape(old_mesh, new_mesh, (0.0, 0.0, 0.0), shift):
                    score += 8
            if plate_name and o.plates and plate_name in o.plates:
                score += 2
            if o.name == spec.name:
                score += 1
            if score > best_score:
                best, best_score = o, score
        if best is None or best_score <= 0:
            return None
        self.objects.remove(best)
        return best

    def settings(self):
        if SETTINGS not in self.files:
            return None
        try:
            return json.loads(self.files[SETTINGS].decode("utf-8"))
        except ValueError:
            raise ReloadError("the printer settings of %s cannot be read" % self.settings_from)

    def area_points(self):
        """[(x, y)] of the printable area polygon, which may be empty or not a rectangle."""
        settings = self.settings() or {}
        points = []
        for p in settings.get("printable_area") or []:
            try:
                x, y = p.lower().split("x")
                points.append((float(x), float(y)))
            except ValueError:
                pass
        return points

    def bed(self, fallback):
        """(x0, y0, width, depth) of the printable area's bounding box."""
        points = self.area_points()
        if len(points) >= 3:
            xs, ys = [p[0] for p in points], [p[1] for p in points]
            return min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys)
        return 0.0, 0.0, float(fallback[0]), float(fallback[1])

    def bed_warnings(self):
        """Warnings about printer settings this build cannot honour."""
        settings = self.settings() or {}
        warnings = []
        if settings.get("bed_exclude_area"):
            warnings.append("bed exclude areas are not checked; parts may be nested onto them")
        points = self.area_points()
        if points and not _axis_aligned_rectangle(points):
            warnings.append("the printable area is not a rectangle; parts are nested on its bounding box")
        return warnings

    def close(self):
        if self.project is not None:
            self.project.close()


# --------------------------------------------------------------------------
# Building


class _Object:
    """One object of the written project: a part's mesh and its copies."""

    def __init__(self, spec, plate_no):
        self.spec = spec
        self.plate_no = plate_no
        self.mesh = None  # stored mesh, centred on its bounding box like Orca stores it
        self.offset = None  # STL coordinates of the stored mesh's origin
        self.extras = {}  # per-triangle painting
        self.old = None
        self.rotation = None
        self.lo = self.hi = None
        self.transforms = []  # (rows, translation) of each copy
        self.notes = []
        self.id = None  # the object's <object id> in the root model
        self.sub_id = None  # the main volume's sub-model <object id>
        self.extra_volumes = []  # _ExtraVolume list (modifiers, negatives, blockers carried over)


class _ExtraVolume:
    """One extra volume of an object, copied over from its old project."""

    def __init__(self, part, transform, mesh_text, raw_part):
        self.part = part
        self.transform = transform  # (rows, translation), re-anchored to the new main volume
        self.mesh_text = mesh_text  # <mesh>...</mesh> from the old sub-model
        self.raw_part = raw_part  # old <part id=... subtype=...>...</part>, with its id not re-numbered yet
        self.sub_id = None  # new sub-model <object id>


def _load(spec, stl_cache):
    key = os.path.normcase(os.path.abspath(spec.stl))
    if key not in stl_cache:
        stl_cache[key] = reload3mf.read_stl(spec.stl)
    return stl_cache[key]


def _carry_extras(base, old_obj, anchor):
    """Copies the old object's extra volumes (modifiers, negatives, blockers, ...) for the rebuilt object.

    anchor is the transform to re-anchor each volume's component transform onto the new main volume
    (Cm^-1 * Cn: the old main volume's component transform inverted, then the new one applied; our new one is
    always identity, so this is the old main's inverse)."""
    project = base.project
    settings_text = project.text(reload3mf.MODEL_SETTINGS)
    try:
        o_start, o_end = reload3mf._block(settings_text, "object", old_obj.id, 0, len(settings_text))
    except ReloadError:
        return []
    out = []
    for part in old_obj.extras:
        if part.model_path is None:
            continue
        try:
            model_text = project.text(part.model_path)
            m_start, m_end = reload3mf.find_mesh(model_text, part.sub_id)
            p_start, p_end = reload3mf._block(settings_text, "part", part.id, o_start, o_end)
        except (ReloadError, KeyError):
            continue
        transform = reload3mf.compose(anchor, reload3mf.parse_transform(part.transform))
        out.append(_ExtraVolume(part, transform, model_text[m_start:m_end], settings_text[p_start:p_end]))
    return out


def _prepare(obj, base, stl_cache, plate_name):
    spec = obj.spec
    stl, _ = _load(spec, stl_cache)  # degenerate triangles are dropped, as Orca's own import does
    seam = spec.seam(spec.stl, stl) if spec.seam else None
    obj.old = base.take_part(spec, plate_name, stl)
    obj.extra_volumes = []
    if obj.old is not None and obj.old.extras and obj.old.part is not None:
        try:
            anchor = reload3mf.invert(reload3mf.parse_transform(obj.old.part.transform))
            obj.extra_volumes = _carry_extras(base, obj.old, anchor)
        except ReloadError:
            obj.extra_volumes = []
    center = stl.center()
    old_part = obj.old.part if obj.old else None
    old = None
    if old_part is not None:
        try:
            old = base.project.old_mesh(old_part)
        except ReloadError:
            old = None
    if old is not None and reload3mf.same_shape(old, stl, (0.0, 0.0, 0.0),
                                                tuple(o - s for o, s in zip(old.center(), center))):
        # Same shape, so the same triangles in the same order: keep the stored mesh and its painting.
        obj.mesh = old
        obj.extras = {i: dict(a) for i, a in old_part.extras.items()}
        obj.offset = tuple(c - o for c, o in zip(center, old.center()))
    else:
        obj.mesh = stl.translated(tuple(-c for c in center))
        obj.offset = center
        if old_part is not None and old_part.extras:
            obj.notes.append("painting removed, the shape changed")
    if seam is not None:
        strings, note = seam
        for a in obj.extras.values():
            a.pop(SEAM_ATTR, None)
        for i, value in strings.items():
            obj.extras.setdefault(i, {})[SEAM_ATTR] = value
        obj.notes.append(note)
    obj.extras = {i: a for i, a in obj.extras.items() if a}
    obj.rotation = layout.orientation(spec.up, spec.angle)
    if spec.mirror:
        obj.rotation = layout.matmul(obj.rotation, MIRROR)
    obj.lo, obj.hi = layout.footprint(obj.mesh.verts, obj.rotation)


def plan(spec, base, stl_cache=None):
    """Works out every object of the project and where its copies go. Returns (objects, problems, bed)."""
    stl_cache = {} if stl_cache is None else stl_cache
    bed = base.bed(spec.bed)
    x0, y0, width, depth = bed
    objects, problems = [], []
    count = len(spec.plates)
    if count > MAX_PLATES:
        problems.append("%d plates; Orca takes at most %d" % (count, MAX_PLATES))
    # Orca spaces the plates by the bed size in whole millimetres
    grid = (int(width), int(depth))
    for plate_no, plate in enumerate(spec.plates):
        plate_objects = []
        for part in plate.parts:
            obj = _Object(part, plate_no)
            try:
                _prepare(obj, base, stl_cache, plate.name)
            except (ReloadError, OSError, ValueError) as e:
                problems.append("plate %d, %s: %s" % (plate_no + 1, part.name, e))
                continue
            plate_objects.append(obj)
        sizes, owners = [], []
        for obj in plate_objects:
            size = (obj.hi[0] - obj.lo[0], obj.hi[1] - obj.lo[1])
            for _ in range(obj.spec.copies):
                sizes.append(size)
                owners.append(obj)
        positions, left_out = layout.nest(sizes, (width, depth), plate.gap)
        for i in left_out:
            obj = owners[i]
            problems.append("plate %d, %s: does not fit on the plate (%.1f x %.1f mm with a %.1f mm gap)"
                            % (plate_no + 1, obj.spec.name, sizes[i][0], sizes[i][1], plate.gap))
        ox, oy = layout.plate_origin(plate_no, count, grid)
        for i, pos in enumerate(positions):
            if pos is None:
                continue
            obj = owners[i]
            t = (ox + x0 + pos[0] - obj.lo[0], oy + y0 + pos[1] - obj.lo[1], -obj.lo[2])
            obj.transforms.append((obj.rotation, t))
        objects += [obj for obj in plate_objects if obj.transforms]
    return objects, problems, bed


def _transform_text(transform):
    rows, t = transform
    values = [rows[r][c] for c in range(3) for r in range(3)] + list(t)
    return " ".join("%.9g" % (0.0 if abs(v) < 1e-12 else v) for v in values)


def _file_name(name, number):
    safe = re.sub(r"[^\w.\-]+", "_", name).strip("_") or "part"
    return "3D/Objects/%s_%d.model" % (safe, number)


def _model_head():
    return ('<?xml version="1.0" encoding="UTF-8"?>\n<model unit="millimeter" xml:lang="en-US" '
            'xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02" '
            'xmlns:BambuStudio="http://schemas.bambulab.com/package/2021" '
            'xmlns:p="http://schemas.microsoft.com/3dmanufacturing/production/2015/06" requiredextensions="p">\n')


def _meta_line(indent, key, value):
    return '%s<metadata key=%s value=%s/>\n' % (indent, quoteattr(key), quoteattr(str(value)))


def _xml_text(root):
    return '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(root, encoding="unicode")


def _remap_txt_object_ids(data, remap):
    out = []
    for line in data.split("\n"):
        m = re.match(r"\s*(?:id|object_id)=(\d+)(\|.*)?$", line)
        if m and int(m.group(1)) in remap:
            key = "id" if line.lstrip().startswith("id=") else "object_id"
            line = "%s=%d%s" % (key, remap[int(m.group(1))], m.group(2) or "")
        out.append(line)
    return "\n".join(out)


def _remap_positioned_files(files, remap_obj, plate_remap):
    """Re-keys the position-addressed files (object index for the layer/profile/brim files, plate index for
    custom G-code) to the new object and plate order, in place."""
    for name in INDEX_OBJECT_FILES:
        if name not in files:
            continue
        if name.endswith(".xml"):
            try:
                root = ET.fromstring(files[name])
            except (ET.ParseError, ValueError):
                continue
            for obj in root.findall("object"):
                oid = obj.get("id")
                if oid and int(oid) in remap_obj:
                    obj.set("id", str(remap_obj[int(oid)]))
            files[name] = _xml_text(root)
        else:
            files[name] = _remap_txt_object_ids(files[name].decode("utf-8"), remap_obj)
    if CUSTOM_GCODE_FILE in files:
        try:
            root = ET.fromstring(files[CUSTOM_GCODE_FILE])
            for plate in root.findall("plate"):
                info = plate.find("plate_info")
                if info is not None:
                    pid = info.get("id")
                    if pid and int(pid) in plate_remap:
                        info.set("id", str(plate_remap[int(pid)]))
            files[CUSTOM_GCODE_FILE] = _xml_text(root)
        except (ET.ParseError, ValueError):
            pass


def write(spec, base, objects, out_path):
    """Writes the project to out_path (through a temporary file, so a failed write leaves the old file)."""
    remap_obj = {}
    for i, obj in enumerate(objects, 1):
        if obj.old is not None and obj.old.index:
            remap_obj[obj.old.index] = i
    new_plate_pos = {}
    for i, plate in enumerate(spec.plates, 1):
        new_plate_pos.setdefault(plate.name, i)
    plate_remap = {}
    for old_pos, (name, _) in enumerate(base.plates, 1):
        if name in new_plate_pos:
            plate_remap[old_pos] = new_plate_pos[name]

    files = {}
    root = [_model_head()]
    for key, value in base.metadata.items():
        root.append(' <metadata name=%s>%s</metadata>\n' % (quoteattr(key), escape(value)))
    root.append(" <resources>\n")
    sub_paths = []
    next_id = 1
    for n, obj in enumerate(objects, 1):
        obj.sub_id = next_id
        next_id += 1
        obj.id = next_id
        next_id += 1
        main_path = _file_name(obj.spec.name, n)
        sub_paths.append(main_path)
        sub = [_model_head(), ' <metadata name="BambuStudio:3mfVersion">1</metadata>\n <resources>\n',
               '  <object id="%d" p:UUID="%08x-81cb-4c03-9d28-80fed5dfa1dc" type="model">\n' % (obj.sub_id, obj.sub_id),
               "   ", reload3mf.mesh_xml(obj.mesh, "   ", obj.extras), "\n  </object>\n </resources>\n"
               " <build/>\n</model>\n"]
        files[main_path] = "".join(sub)
        comps = ['    <component p:path="/%s" objectid="%d" '
                 'p:UUID="%08x-b206-40ff-9872-83e8017abed1" transform="1 0 0 0 1 0 0 0 1 0 0 0"/>\n'
                 % (escape(main_path), obj.sub_id, obj.sub_id)]
        for k, extra in enumerate(obj.extra_volumes):
            extra.sub_id = next_id
            next_id += 1
            extra_path = _file_name("%s_extra%d" % (obj.spec.name, k), n)
            sub_paths.append(extra_path)
            esub = [_model_head(), ' <metadata name="BambuStudio:3mfVersion">1</metadata>\n <resources>\n',
                    '  <object id="%d" p:UUID="%08x-8cb0-4c03-9d28-80fed5dfa1dc" type="model">\n' % (extra.sub_id, extra.sub_id),
                    "   ", extra.mesh_text, "\n  </object>\n </resources>\n <build/>\n</model>\n"]
            files[extra_path] = "".join(esub)
            comps.append('    <component p:path="/%s" objectid="%d" '
                         'p:UUID="%08x-b206-40ff-9872-83e8017abed1" transform="%s"/>\n'
                         % (escape(extra_path), extra.sub_id, extra.sub_id, _transform_text(extra.transform)))
        root.append('  <object id="%d" p:UUID="%08x-61cb-4c03-9d28-80fed5dfa1dc" type="model">\n'
                    '   <components>\n%s   </components>\n  </object>\n' % (obj.id, obj.id, "".join(comps)))
    root.append(' </resources>\n <build p:UUID="%s">\n' % BUILD_UUID)
    item = 0
    for obj in objects:
        for transform in obj.transforms:
            item += 1
            root.append('  <item objectid="%d" p:UUID="%08x-b1ec-4553-aec9-835e5b724bb4" transform="%s" '
                        'printable="1"/>\n' % (obj.id, item, _transform_text(transform)))
    root.append(" </build>\n</model>\n")
    files[reload3mf.ROOT_MODEL] = "".join(root)
    files["3D/_rels/3dmodel.model.rels"] = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">\n'
        + "".join(' <Relationship Target="/%s" Id="rel-%d" '
                  'Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>\n'
                  % (escape(path), i) for i, path in enumerate(sub_paths, 1))
        + "</Relationships>\n")
    files["_rels/.rels"] = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">\n'
        ' <Relationship Target="/3D/3dmodel.model" Id="rel-1" '
        'Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>\n</Relationships>\n')
    files["[Content_Types].xml"] = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">\n'
        ' <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>\n'
        ' <Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>\n'
        ' <Default Extension="png" ContentType="image/png"/>\n'
        ' <Default Extension="gcode" ContentType="text/x.gcode"/>\n</Types>\n')
    files[reload3mf.MODEL_SETTINGS] = _model_settings(spec, base, objects)
    files["Metadata/slice_info.config"] = (
        '<?xml version="1.0" encoding="UTF-8"?>\n<config>\n  <header>\n'
        '    <header_item key="X-BBL-Client-Type" value="slicer"/>\n'
        '    <header_item key="X-BBL-Client-Version" value="%s"/>\n  </header>\n</config>\n'
        % escape(base.metadata.get("Application", APPLICATION).split("-")[-1]))
    files["Metadata/filament_sequence.json"] = json.dumps(
        {"plate_%d" % (i + 1): {"nozzle_sequence": [], "optimal_assignment": [], "sequence": []}
         for i in range(len(spec.plates))}, separators=(",", ":"))
    for name, data in base.files.items():
        files.setdefault(name, data)
    _remap_positioned_files(files, remap_obj, plate_remap)

    out_dir = os.path.dirname(os.path.abspath(out_path))
    os.makedirs(out_dir, exist_ok=True)
    fd, tmp = tempfile.mkstemp(suffix=".3mf", dir=out_dir)
    os.close(fd)
    try:
        with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED, allowZip64=True) as z:
            for name in ("[Content_Types].xml", "_rels/.rels"):
                z.writestr(name, files.pop(name))
            for name, data in files.items():
                z.writestr(name, data if isinstance(data, bytes) else data.encode("utf-8"))
        _check(tmp, objects)
        os.chmod(tmp, 0o644)
        base.close()  # Windows cannot replace a file that is still open
        os.replace(tmp, out_path)
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)


def _model_settings(spec, base, objects):
    out = ['<?xml version="1.0" encoding="UTF-8"?>\n<config>\n']
    for obj in objects:
        meta = obj.old.meta if obj.old else [("extruder", "1")]
        part_meta = []
        if obj.old and obj.old.part:
            part_meta = [(k, v) for k, v in obj.old.part.meta.items() if k not in PART_KEYS]
        out.append('  <object id="%d">\n' % obj.id)
        out.append(_meta_line("    ", "name", obj.spec.name))
        out += [_meta_line("    ", k, v) for k, v in meta]
        out.append('    <part id="%d" subtype="normal_part">\n' % obj.sub_id)
        out.append(_meta_line("      ", "name", obj.spec.name))
        out.append(_meta_line("      ", "matrix", "1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1"))
        out.append(_meta_line("      ", "source_file", obj.spec.stl))
        out.append(_meta_line("      ", "source_object_id", "0"))
        out.append(_meta_line("      ", "source_volume_id", "0"))
        for axis, value in zip("xyz", obj.offset):
            out.append(_meta_line("      ", "source_offset_" + axis, repr(float(value))))
        out += [_meta_line("      ", k, v) for k, v in part_meta]
        out.append('      <mesh_stat edges_fixed="0" degenerate_facets="0" facets_removed="0" '
                   'facets_reversed="0" backwards_edges="0"/>\n    </part>\n')
        for extra in obj.extra_volumes:
            out.append(re.sub(r'\bid="[^"]*"', 'id="%d"' % extra.sub_id, extra.raw_part, count=1) + "\n")
        out.append('  </object>\n')
    identify = 0
    for plate_no, plate in enumerate(spec.plates):
        out.append("  <plate>\n")
        out.append(_meta_line("    ", "plater_id", plate_no + 1))
        out.append(_meta_line("    ", "plater_name", plate.name))
        kept = base.take_plate(plate.name, plate_no)
        out += [_meta_line("    ", k, v) for k, v in kept]
        for obj in objects:
            if obj.plate_no != plate_no:
                continue
            for instance in range(len(obj.transforms)):
                identify += 1
                out.append("    <model_instance>\n")
                out.append(_meta_line("      ", "object_id", obj.id))
                out.append(_meta_line("      ", "instance_id", instance))
                out.append(_meta_line("      ", "identify_id", identify))
                out.append("    </model_instance>\n")
        out.append("  </plate>\n")
    out.append("  <assemble>\n")
    for obj in objects:
        for instance, transform in enumerate(obj.transforms):
            out.append('   <assemble_item object_id="%d" instance_id="%d" transform="%s" offset="0 0 0" />\n'
                       % (obj.id, instance, _transform_text(transform)))
    out.append("  </assemble>\n</config>\n")
    return "".join(out)


def _check(path, objects):
    """Re-reads the written file: the zip is sound, every XML file parses, meshes are complete."""
    with zipfile.ZipFile(path) as z:
        bad = z.testzip()
        if bad:
            raise ReloadError("written file is damaged at %s" % bad)
        for name in z.namelist():
            if name.endswith((".model", ".rels", ".xml")) or name == reload3mf.MODEL_SETTINGS:
                ET.fromstring(z.read(name))
        for n, obj in enumerate(objects, 1):
            text = z.read(_file_name(obj.spec.name, n)).decode("utf-8")
            if (text.count("<vertex ") != obj.mesh.vertex_count
                    or text.count("<triangle ") != obj.mesh.triangle_count):
                raise ReloadError("written mesh of %s does not match" % obj.spec.name)


def build(spec, stl_cache=None, dry_run=False):
    """Builds one project. Returns (report lines, written)."""
    created = not os.path.isfile(spec.path)
    base = Base(spec.path, spec.template)
    try:
        objects, problems, bed = plan(spec, base, stl_cache)
        lines = ["%s (%s)" % (spec.path, "new" if created else "rebuilt")]
        if base.settings_from:
            source = "the project" if os.path.normcase(os.path.abspath(base.settings_from)) == \
                os.path.normcase(os.path.abspath(spec.path)) else base.settings_from
            lines.append("  settings from %s, bed %g x %g mm" % (source, bed[2], bed[3]))
        else:
            problems.append("no printer settings: set Settings from to an Orca project made for your printer "
                            "(Orca opens a project without them as bare parts, without plates)")
        warnings = base.bed_warnings()
        height = (base.settings() or {}).get("printable_height")
        if height is not None:
            try:
                height = float(height)
            except (TypeError, ValueError):
                warnings.append("the printer's printable_height cannot be read")
                height = None
            if height is not None:
                for obj in objects:
                    tall = obj.hi[2] - obj.lo[2]
                    if tall > height + 1e-6:
                        problems.append("%s: %.1f mm tall, above the printer's %.1f mm printable height"
                                        % (obj.spec.name, tall, height))
        for plate_no, plate in enumerate(spec.plates):
            on = [o for o in objects if o.plate_no == plate_no]
            copies = sum(len(o.transforms) for o in on)
            lines.append("  plate %d %s: %d part%s, %d cop%s" % (plate_no + 1, plate.name or "", len(on),
                                                                "" if len(on) == 1 else "s", copies,
                                                                "y" if copies == 1 else "ies"))
            for obj in on:
                size = tuple(h - l for h, l in zip(obj.hi, obj.lo))
                text = "    %s  %s  %.1f x %.1f x %.1f mm" % (obj.spec.name, os.path.basename(obj.spec.stl), *size)
                if len(obj.transforms) > 1:
                    text += "  x%d" % len(obj.transforms)
                if obj.old is not None and any(k != "extruder" for k, _ in obj.old.meta):
                    text += "  (kept its Orca settings)"
                if obj.notes:
                    text += "  " + "; ".join(obj.notes)
                lines.append(text)
        lines += ["  problem: %s" % p for p in problems]
        lines += ["  warning: %s" % w for w in warnings]
        if problems:
            lines.append("  not written")
            return lines, False
        if not objects:
            lines.append("  no parts, not written")
            return lines, False
        if not dry_run:
            write(spec, base, objects, spec.path)
        return lines, not dry_run
    finally:
        base.close()


# --------------------------------------------------------------------------
# Reading an existing project into projects > plates > parts


class ImportedPart:
    def __init__(self, name, source, up, angle, copies, stl=None, note="", mirror=False):
        self.name = name
        self.source = source  # source_file as stored in the project
        self.stl = stl  # the STL found for it, or None
        self.up = up
        self.angle = angle
        self.copies = copies
        self.note = note
        self.mirror = mirror


def read_layout(path, finder, stl_cache=None):
    """Plates of an existing project: [(plate name, [ImportedPart])], and problem lines.

    finder: reload3mf.SourceFinder for the STLs. A file name found in several folders (a part exported with
    several tolerances) is matched by its shape."""
    stl_cache = {} if stl_cache is None else stl_cache
    project = reload3mf.Project(path)
    problems = []
    try:
        root = ET.fromstring(project.zip.read(reload3mf.MODEL_SETTINGS))
        project_dir = os.path.dirname(os.path.abspath(path))
        plates = []
        for plate in root.findall("plate"):
            meta = {m.get("key"): m.get("value") for m in plate.findall("metadata")}
            ids = [{m.get("key"): m.get("value") for m in inst.findall("metadata")}.get("object_id")
                   for inst in plate.findall("model_instance")]
            plates.append((int(meta.get("plater_id") or len(plates) + 1), meta.get("plater_name") or "", ids))
        plates.sort(key=lambda p: p[0])
        out = []
        for _, name, ids in plates:
            parts, seen = [], {}
            for oid in ids:
                if oid in seen:
                    seen[oid].copies += 1
                    continue
                obj = project.objects.get(oid)
                if obj is None:
                    continue
                models = [p for p in obj.parts if p.is_model_part]
                if len(obj.parts) != 1 or len(models) != 1:
                    problems.append("%s: has %d parts, only objects of one STL are taken" % (obj.name, len(obj.parts)))
                    continue
                part = models[0]
                transform = project.items[obj.items[0]][1] if obj.items else None
                rows, _ = reload3mf.compose(reload3mf.parse_transform(transform),
                                            reload3mf.parse_transform(part.transform))
                mirror = layout.det(rows) < 0.0
                if mirror:
                    # Factor out the reflection as a mirror across the part's own X axis (M = R * diag(-1, 1, 1)),
                    # so the ImportedPart keeps the unmirrored up/turn and the mirror flag puts it back on Build.
                    rows = tuple(tuple(-c if k == 0 else c for k, c in enumerate(row)) for row in rows)
                up, angle = layout.orientation_from_matrix(rows)
                up = tuple(0.0 if abs(c) < 1e-9 else c for c in up)
                stl, note = _find_source(project, part, finder, project_dir, stl_cache)
                angle = math.radians(round(math.degrees(angle), 4))  # drop float noise: 30.0000001 degrees is 30
                imported = ImportedPart(obj.name, part.source, up, angle, 1, stl, note, mirror=mirror)
                seen[oid] = imported
                parts.append(imported)
            out.append((name, parts))
        return out, problems
    finally:
        project.close()


def _find_source(project, part, finder, project_dir, stl_cache):
    path, problem = finder.find(part.source, project_dir)
    if path is not None:
        return path, ""
    names = finder._name_index().get(os.path.basename(part.source.replace("\\", "/")).lower(), ())
    if not names:
        return None, problem or "STL not found"
    try:
        old = project.old_mesh(part)
    except ReloadError as e:
        return None, str(e)
    same = []
    for cand in sorted(names):
        try:
            key = os.path.normcase(os.path.abspath(cand))
            if key not in stl_cache:
                stl_cache[key] = reload3mf.read_stl(cand)
            stl = stl_cache[key][0]
        except (ReloadError, OSError):
            continue
        shift = tuple(o - s for o, s in zip(old.center(), stl.center()))
        if reload3mf.same_shape(old, stl, (0.0, 0.0, 0.0), shift):
            same.append(cand)
    if len(same) == 1:
        return same[0], "matched by shape among %d files named %s" % (len(names), os.path.basename(same[0]))
    return None, problem or "STL not found"


def common_folder(paths):
    """The folder (with / between names) that all the relative paths start with, or ''."""
    split = [p.replace("\\", "/").split("/")[:-1] for p in paths]
    if not split:
        return ""
    common = split[0]
    for s in split[1:]:
        n = 0
        while n < len(common) and n < len(s) and common[n] == s[n]:
            n += 1
        common = common[:n]
    return "/".join(common)


def strip_folder(path, folder):
    path = path.replace("\\", "/")
    return path[len(folder) + 1:] if folder and path.startswith(folder + "/") else path

