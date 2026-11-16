"""Builds OrcaSlicer projects (.3mf) from projects > plates > parts, each part an STL file with an up axis, a turn
around it and its copies. Each copy stands where the tab says (its spot), or is nested on its plate with the plate's
gap, around the placed ones.

Everything comes from the tab: the meshes from the STLs, seams from seam lines, and the printer, process and
filament settings, each plate's and each part's Orca settings as Import saved them. The old 3MF is never read, so
Orca's painting, modifiers and layer height edits are not carried over. A project that was never imported takes
its settings from a template project: Orca opens a project without settings as bare geometry, without its plates,
so one is needed.

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
    around it (radians), its copies, a mirror across the part's own X axis, an optional seam function
    (stl_path, Mesh) -> None or (paint_seam strings by triangle index, note for the report), the STL path written
    into the project as its source_file (default: the absolute path; relative paths start at the 3MF's folder),
    and the object's and part's own Orca settings ([(key, value)], saved by Import).

    spots: one entry per copy, (x, y, turn) of where it stands (the centre of its footprint from the plate's front
    left corner, mm, and a turn in radians on top of the part's own) or None for a copy without a place yet, which
    Build nests around the placed ones. Build fills spots_out with where every copy went."""

    def __init__(self, name, stl, up=(0.0, 0.0, 1.0), angle=0.0, copies=1, seam=None, mirror=False, source=None,
                 spots=None, object_meta=(), part_meta=()):
        self.name = name or os.path.basename(stl)
        self.stl = stl
        self.source = source or stl
        self.up = tuple(up)
        self.angle = angle
        self.spots = list(spots) if spots else [None] * max(int(copies), 1)
        self.copies = len(self.spots)
        self.seam = seam
        self.mirror = bool(mirror)
        self.object_meta = [(k, v) for k, v in object_meta if k != "name"]
        self.part_meta = [(k, v) for k, v in part_meta if k not in PART_KEYS]
        self.spots_out = []


class PlateSpec:
    """A plate: its name, the gap between its parts, its parts and its own Orca settings ([(key, value)])."""

    def __init__(self, name="", gap=6.0, parts=(), meta=()):
        self.name = name
        self.gap = gap
        self.parts = list(parts)
        self.meta = [(k, v) for k, v in meta if k not in PLATE_KEYS]


class ProjectSpec:
    """A project: its 3MF file (absolute path; Build writes out_path, the same file unless given), its plates, the
    printer, process and filament settings Import saved (profiles: {file in the 3MF: text}, with the 3MF's
    metadata) or else a template project to take them from, the bed size used when there are none, and how the
    report shows a path (default: as it is). The old 3MF itself is never read."""

    def __init__(self, path, plates=(), template="", bed=(256.0, 256.0), shown=None, out_path=None, profiles=None,
                 metadata=None, profiles_from=""):
        self.path = path
        self.out_path = out_path or path  # where Build writes: the project itself, or a numbered build of it
        self.shown = shown or (lambda p: p)
        self.plates = list(plates)
        self.template = template
        self.bed = tuple(bed)
        self.profiles = dict(profiles or {})
        self.metadata = dict(metadata or {})
        self.profiles_from = profiles_from  # the 3MF they were imported from, for the report


def _numbered_builds(path, folder):
    """(builds folder, project stem, {number: file name}) of a project's numbered builds."""
    out_dir = os.path.join(os.path.dirname(os.path.abspath(path)), folder)
    stem = os.path.splitext(os.path.basename(path))[0]
    pattern = re.compile(re.escape(stem) + r"_(\d+)\.3mf$", re.IGNORECASE)
    found = {}
    for name in (os.listdir(out_dir) if os.path.isdir(out_dir) else ()):
        m = pattern.match(name)
        if m:
            found[int(m.group(1))] = name
    return out_dir, stem, found


def next_build_path(path, folder="3mf_builds"):
    """The next build of a project: <its folder>/3mf_builds/<name>.3mf first, then <name>_001.3mf, _002, ...
    after the highest number there."""
    out_dir, stem, found = _numbered_builds(path, folder)
    plain = os.path.join(out_dir, stem + ".3mf")
    if not found and not os.path.isfile(plain):
        return plain
    return os.path.join(out_dir, "%s_%03d.3mf" % (stem, max(found, default=0) + 1))


def latest_build_path(path, folder="3mf_builds"):
    """The newest build of a project, or None."""
    out_dir, stem, found = _numbered_builds(path, folder)
    if found:
        return os.path.join(out_dir, found[max(found)])
    plain = os.path.join(out_dir, stem + ".3mf")
    return plain if os.path.isfile(plain) else None


def _decode(data):
    return data.decode("utf-8", errors="replace") if isinstance(data, bytes) else data


def read_profiles(z):
    """({settings file: text}, {metadata name: value}) of an open 3MF zip: the printer, process and filament
    settings, and the Orca version that wrote them."""
    files = {name: _decode(z.read(name)) for name in z.namelist() if SETTINGS_FILES.match(name)}
    metadata = {}
    try:
        root = ET.fromstring(z.read(reload3mf.ROOT_MODEL))
    except (KeyError, ET.ParseError):
        root = None
    if root is not None:
        for m in root.findall(reload3mf.CORE_NS + "metadata"):
            if m.get("name") in ("Application", "OrcaSlicer") and m.text:
                metadata[m.get("name")] = m.text
    return files, metadata


def read_profiles_file(path):
    """(profiles, metadata) of the 3MF at path: its printer, process and filament settings only (read_profiles).
    Raises ReloadError when it holds none."""
    with zipfile.ZipFile(path) as z:
        files, metadata = read_profiles(z)
    if SETTINGS not in files:
        raise ReloadError("%s holds no printer, process and filament settings" % os.path.basename(path))
    return files, metadata


# Which kind an exported Orca preset is, by the key naming it in the project's settings, and the slot of
# inherits_group (process, filament, printer) that names the preset it builds on
PRESET_KINDS = (("print_settings_id", "process", 0), ("filament_settings_id", "filament", 1),
                ("printer_settings_id", "printer", 2))
PRESET_SKIP = {"name", "from", "inherits", "version", "setting_id", "instantiation", "filament_id", "type",
               "is_custom_defined", "base_id", "user_id", "updated_time", "compatible_printers",
               "compatible_printers_condition", "compatible_prints", "compatible_prints_condition"}


def preset_kind(preset):
    """("process" | "filament" | "printer", settings id key, inherits_group slot) of an exported preset."""
    for key, kind, slot in PRESET_KINDS:
        if key in preset:
            return kind, key, slot
    kind = preset.get("type")
    for key, k, slot in PRESET_KINDS:
        if kind == k or (kind == "machine" and k == "printer"):
            return k, key, slot
    raise ReloadError("not an Orca printer, process or filament preset")


def apply_preset(profiles, preset, filament=0):
    """Lays an exported Orca preset (a dict from its .json: only what it changes, plus the preset it builds on)
    over the saved settings. A filament preset goes into filament slot `filament` (0 = the first). Returns
    (new profiles, notes)."""
    if SETTINGS not in profiles:
        raise ReloadError("no settings to lay the preset over: load profiles from a 3MF first")
    settings = json.loads(profiles[SETTINGS])
    kind, id_key, group_slot = preset_kind(preset)
    name = preset.get("name") or "preset"
    notes = []
    group = settings.get("inherits_group")
    current_id = settings.get(id_key)
    if isinstance(current_id, list):
        current_id = current_id[filament] if filament < len(current_id) else ""
    base = (group[group_slot] if isinstance(group, list) and group_slot < len(group) else "") or current_id
    wanted = preset.get("inherits", "")
    if wanted and base and wanted != base and current_id != wanted:
        notes.append("%s builds on %s, but the loaded settings came from %s: settings it does not change are "
                     "%s's" % (name, wanted, base, base))
    changed = 0
    for key, value in preset.items():
        if key in PRESET_SKIP or key == id_key:
            continue
        old = settings.get(key)
        if kind == "filament" and isinstance(old, list) and isinstance(value, list):
            if filament >= len(old):
                notes.append("%s: no filament %d in the settings" % (key, filament + 1))
                continue
            new = list(old)
            new[filament] = value[0] if value else ""
            value = new
        if old != value:
            changed += 1
        settings[key] = value
    if isinstance(settings.get(id_key), list):
        ids = list(settings[id_key])
        if filament < len(ids):
            ids[filament] = name
        settings[id_key] = ids
    else:
        settings[id_key] = name
    if isinstance(group, list) and group_slot < len(group) and wanted:
        group = list(group)
        group[group_slot] = wanted
        settings["inherits_group"] = group
    out = dict(profiles)
    out[SETTINGS] = json.dumps(settings, indent=4)
    notes.insert(0, "%s preset %s: %d setting%s changed" % (kind, name, changed, "" if changed == 1 else "s"))
    return out, notes


def profile_keys(profiles):
    """The setting names of the saved process and printer settings, sorted (for per-object settings)."""
    try:
        return sorted(json.loads(profiles.get(SETTINGS, "{}")))
    except (ValueError, TypeError):
        return []


class Base:
    """The printer, process and filament settings a build writes: the ones Import saved, else a template
    project's, else none."""

    def __init__(self, profiles=None, template=None, metadata=None, profiles_from=""):
        self.settings_from = None
        self.files = {}  # zip entry -> bytes, written as they are
        self.metadata = {"Application": APPLICATION, "OrcaSlicer": ORCA_VERSION, "BambuStudio:3mfVersion": "1"}
        if profiles and SETTINGS in profiles:
            self.files = {k: v.encode("utf-8") if isinstance(v, str) else v for k, v in profiles.items()}
            self.metadata.update(metadata or {})
            self.settings_from = profiles_from or "the saved settings"
        elif template:
            if not os.path.isfile(template):
                raise ReloadError("settings project not found: %s" % template)
            with zipfile.ZipFile(template) as z:
                files, meta = read_profiles(z)
            if SETTINGS in files:
                self.files = {k: v.encode("utf-8") for k, v in files.items()}
                self.metadata.update(meta)
                self.settings_from = template

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


# --------------------------------------------------------------------------
# Building


class _Object:
    """One object of the written project: a part's mesh and its copies."""

    def __init__(self, spec, plate_no):
        self.spec = spec
        self.plate_no = plate_no
        self.mesh = None  # the STL's mesh, centred on its bounding box like Orca stores it
        self.offset = None  # STL coordinates of the stored mesh's origin
        self.extras = {}  # per-triangle seam painting
        self.rotation = None
        self.lo = self.hi = None
        self.transforms = []  # (rows, translation) of each copy
        self.notes = []
        self.id = None  # the object's <object id> in the root model
        self.sub_id = None  # the main volume's sub-model <object id>


def _load(spec, stl_cache):
    key = os.path.normcase(os.path.abspath(spec.stl))
    if key not in stl_cache:
        stl_cache[key] = reload3mf.read_stl(spec.stl)
    return stl_cache[key]


def _prepare(obj, stl_cache):
    spec = obj.spec
    stl, _ = _load(spec, stl_cache)  # degenerate triangles are dropped, as Orca's own import does
    center = stl.center()
    obj.mesh = stl.translated(tuple(-c for c in center))
    obj.offset = center
    obj.extras = {}
    seam = spec.seam(spec.stl, stl) if spec.seam else None
    if seam is not None:
        strings, note = seam
        for i, value in strings.items():
            obj.extras[i] = {SEAM_ATTR: value}
        obj.notes.append(note)
    obj.rotation = layout.orientation(spec.up, spec.angle)
    if spec.mirror:
        obj.rotation = layout.matmul(obj.rotation, MIRROR)
    obj.lo, obj.hi = layout.footprint(obj.mesh.verts, obj.rotation)


def plan(spec, base, stl_cache=None):
    """Works out every object of the project and where its copies go: a copy with a spot stands there, the
    others are nested around them. Returns (objects, problems, bed)."""
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
                _prepare(obj, stl_cache)
            except (ReloadError, OSError, ValueError) as e:
                problems.append("plate %d, %s: %s" % (plate_no + 1, part.name, e))
                continue
            plate_objects.append(obj)
        ox, oy = layout.plate_origin(plate_no, count, grid)
        blocked, sizes, owners = [], [], []
        for obj in plate_objects:
            spots = obj.spec.spots
            obj.transforms = [None] * len(spots)
            obj.spec.spots_out = [None] * len(spots)
            for k, spot in enumerate(spots):
                if spot is None:
                    sizes.append((obj.hi[0] - obj.lo[0], obj.hi[1] - obj.lo[1]))
                    owners.append((obj, k))
                    continue
                x, y, turn = spot
                rows = layout.matmul(layout.rot_z(turn), obj.rotation) if turn else obj.rotation
                lo, hi = layout.footprint(obj.mesh.verts, rows) if turn else (obj.lo, obj.hi)
                w, d = hi[0] - lo[0], hi[1] - lo[1]
                blocked.append((x - w / 2.0, y - d / 2.0, w, d))
                obj.transforms[k] = (rows, (ox + x0 + x - (lo[0] + hi[0]) / 2.0,
                                            oy + y0 + y - (lo[1] + hi[1]) / 2.0, -lo[2]))
                obj.spec.spots_out[k] = (x, y, turn)
        positions, left_out = layout.nest(sizes, (width, depth), plate.gap, blocked=blocked)
        for i in left_out:
            obj = owners[i][0]
            problems.append("plate %d, %s: does not fit on the plate (%.1f x %.1f mm with a %.1f mm gap)"
                            % (plate_no + 1, obj.spec.name, sizes[i][0], sizes[i][1], plate.gap))
        for i, pos in enumerate(positions):
            if pos is None:
                continue
            obj, k = owners[i]
            obj.transforms[k] = (obj.rotation, (ox + x0 + pos[0] - obj.lo[0], oy + y0 + pos[1] - obj.lo[1],
                                                -obj.lo[2]))
            obj.spec.spots_out[k] = (pos[0] + sizes[i][0] / 2.0, pos[1] + sizes[i][1] / 2.0, 0.0)
        for obj in plate_objects:
            obj.transforms = [t for t in obj.transforms if t is not None]
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


def write(spec, base, objects, out_path):
    """Writes the project to out_path (through a temporary file, so a failed write leaves the old file)."""
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
        comps = ('    <component p:path="/%s" objectid="%d" '
                 'p:UUID="%08x-b206-40ff-9872-83e8017abed1" transform="1 0 0 0 1 0 0 0 1 0 0 0"/>\n'
                 % (escape(main_path), obj.sub_id, obj.sub_id))
        root.append('  <object id="%d" p:UUID="%08x-61cb-4c03-9d28-80fed5dfa1dc" type="model">\n'
                    '   <components>\n%s   </components>\n  </object>\n' % (obj.id, obj.id, comps))
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
    files[reload3mf.MODEL_SETTINGS] = _model_settings(spec, objects)
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
        os.replace(tmp, out_path)
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)


def _model_settings(spec, objects):
    out = ['<?xml version="1.0" encoding="UTF-8"?>\n<config>\n']
    for obj in objects:
        meta = obj.spec.object_meta or [("extruder", "1")]
        out.append('  <object id="%d">\n' % obj.id)
        out.append(_meta_line("    ", "name", obj.spec.name))
        out += [_meta_line("    ", k, v) for k, v in meta]
        out.append('    <part id="%d" subtype="normal_part">\n' % obj.sub_id)
        out.append(_meta_line("      ", "name", obj.spec.name))
        out.append(_meta_line("      ", "matrix", "1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1"))
        out.append(_meta_line("      ", "source_file", obj.spec.source))
        out.append(_meta_line("      ", "source_object_id", "0"))
        out.append(_meta_line("      ", "source_volume_id", "0"))
        for axis, value in zip("xyz", obj.offset):
            out.append(_meta_line("      ", "source_offset_" + axis, repr(float(value))))
        out += [_meta_line("      ", k, v) for k, v in obj.spec.part_meta]
        out.append('      <mesh_stat edges_fixed="0" degenerate_facets="0" facets_removed="0" '
                   'facets_reversed="0" backwards_edges="0"/>\n    </part>\n')
        out.append('  </object>\n')
    identify = 0
    for plate_no, plate in enumerate(spec.plates):
        out.append("  <plate>\n")
        out.append(_meta_line("    ", "plater_id", plate_no + 1))
        out.append(_meta_line("    ", "plater_name", plate.name))
        out += [_meta_line("    ", k, v) for k, v in (plate.meta or [("locked", "false")])]
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
    base = Base(spec.profiles, spec.template, spec.metadata, spec.profiles_from)
    objects, problems, bed = plan(spec, base, stl_cache)
    if os.path.normcase(os.path.abspath(spec.out_path)) == os.path.normcase(os.path.abspath(spec.path)):
        lines = ["%s (%s)" % (spec.shown(spec.path), "new" if created else "rebuilt")]
    else:
        lines = ["%s (new build of %s)" % (spec.shown(spec.out_path), spec.shown(spec.path))]
    if base.settings_from:
        source = base.settings_from if spec.profiles else spec.shown(base.settings_from)
        lines.append("  settings from %s, bed %g x %g mm" % (source, bed[2], bed[3]))
    else:
        problems.append("no printer settings: import an Orca 3MF, or set Settings from to an Orca project made "
                        "for your printer (Orca opens a project without them as bare parts, without plates)")
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
            placed = sum(1 for s in obj.spec.spots if s is not None)
            if placed < len(obj.transforms):
                text += "  (%d placed)" % (len(obj.transforms) - placed)
            if obj.spec.object_meta and any(k != "extruder" for k, _ in obj.spec.object_meta) \
                    or obj.spec.part_meta:
                text += "  (own Orca settings)"
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
        write(spec, base, objects, spec.out_path)
    return lines, not dry_run


# --------------------------------------------------------------------------
# Reading an existing project into projects > plates > parts


class ImportedPart:
    def __init__(self, name, source, up, angle, copies, stl=None, note="", mirror=False, spots=None,
                 object_meta=(), part_meta=()):
        self.name = name
        self.source = source  # source_file as stored in the project
        self.stl = stl  # the STL found for it, or None
        self.up = up
        self.angle = angle
        self.copies = copies
        self.note = note
        self.mirror = mirror
        self.spots = spots or []  # (x, y, turn) of each copy, see PartSpec; empty when not known
        self.object_meta = list(object_meta)
        self.part_meta = list(part_meta)


class ImportedPlate:
    def __init__(self, name, meta, parts):
        self.name = name
        self.meta = list(meta)  # the plate's own Orca settings
        self.parts = parts


class ImportedProject:
    """What Import keeps of an Orca 3MF: its plates and parts with their Orca settings and where each copy stands,
    the printer, process and filament settings, and what it could not keep."""

    def __init__(self):
        self.plates = []
        self.profiles = {}
        self.metadata = {}
        self.dropped = []  # lines about what is not kept (meshes of modifiers, layer heights, ...)


def read_layout(path, finder, stl_cache=None, plate_paths=False, top=None, known=None):
    """[(plate name, [ImportedPart])] of an Orca 3MF, and problem lines (read_project, without the settings)."""
    imported, problems = read_project(path, finder, plate_paths=plate_paths, top=top, known=known)
    return [(p.name, p.parts) for p in imported.plates], problems


def _unit_rows(rows):
    """The rotation of rows with any scale taken out (each column made unit length)."""
    cols = [[rows[r][c] for r in range(3)] for c in range(3)]
    cols = [[v / (math.sqrt(sum(x * x for x in col)) or 1.0) for v in col] for col in cols]
    return tuple(tuple(cols[c][r] for c in range(3)) for r in range(3))


def _strip_mirror(rows):
    return tuple(tuple(-c if k == 0 else c for k, c in enumerate(row)) for row in rows)


def read_project(path, finder, plate_paths=False, top=None, known=None, bed=(256.0, 256.0)):
    """Reads an Orca 3MF into an ImportedProject, and problem lines.

    finder: reload3mf.SourceFinder for the STLs. A file name found in several folders (a part exported with
    several tolerances) is taken from the folder the plate is named after when plate_paths is on (_find_source);
    plate_paths off: plate names are only names. top: the project's STL folder, where looking up stops.
    known(plate name, file name): the STL the tab already links, or None (a re-import). bed: the bed size used
    when the 3MF has no printer settings.

    Each copy (build item) belongs to the plate it stands on; its spot is the centre of its footprint from that
    plate's front left corner, and its turn is around the vertical, on top of the first copy's."""
    project = reload3mf.Project(path)
    problems = []
    out = ImportedProject()
    try:
        z = project.zip
        out.profiles, out.metadata = read_profiles(z)
        names = set(z.namelist())
        if any(n in names for n in INDEX_OBJECT_FILES):
            out.dropped.append("variable layer heights, height ranges and brim ears are not kept (they belong to "
                               "the old meshes)")
        if CUSTOM_GCODE_FILE in names:
            out.dropped.append("custom G-code per layer (pauses, colour changes) is not kept")
        base = Base(out.profiles, profiles_from=path)
        x0, y0, width, depth = base.bed(bed)
        root = ET.fromstring(z.read(reload3mf.MODEL_SETTINGS))
        object_meta = {o.get("id"): [(m.get("key"), m.get("value")) for m in o.findall("metadata")
                                     if m.get("key") and m.get("key") != "name"]
                       for o in root.findall("object")}
        project_dir = os.path.dirname(os.path.abspath(path))
        plates = []
        for plate in root.findall("plate"):
            meta = [(m.get("key"), m.get("value")) for m in plate.findall("metadata") if m.get("key")]
            pmeta = dict(meta)
            ids = [{m.get("key"): m.get("value") for m in inst.findall("metadata")}.get("object_id")
                   for inst in plate.findall("model_instance")]
            plates.append((int(pmeta.get("plater_id") or len(plates) + 1), pmeta.get("plater_name") or "",
                           [(k, v) for k, v in meta if k not in PLATE_KEYS], ids))
        plates.sort(key=lambda p: p[0])
        count = len(plates)
        grid = (int(width), int(depth))
        corners = [layout.plate_origin(i, count, grid) for i in range(count)]
        corners = [(ox + x0, oy + y0) for ox, oy in corners]
        listed_on = {}  # object id -> how many plates list it
        for _, _, _, ids in plates:
            for oid in set(ids):
                listed_on[oid] = listed_on.get(oid, 0) + 1
        folders = {}  # the folders below the STL root, read once
        for plate_no, (_, name, plate_meta, ids) in enumerate(plates):
            parts, seen = [], {}
            for oid in ids:
                if oid in seen:
                    continue
                obj = project.objects.get(oid)
                if obj is None:
                    continue
                models = [p for p in obj.parts if p.is_model_part]
                if len(models) != 1:
                    problems.append("%s: has %d parts, only objects of one STL are taken" % (obj.name, len(models)))
                    continue
                part = models[0]
                if len(obj.parts) > 1:
                    out.dropped.append("%s: %d modifier%s not kept" % (obj.name, len(obj.parts) - 1,
                                                                      "" if len(obj.parts) == 2 else "s"))
                inner = reload3mf.parse_transform(part.transform)
                try:
                    mesh = project.old_mesh(part)
                except ReloadError:
                    mesh = None
                # Each copy, with the plate it stands on (the nearest plate centre)
                copies_here = []
                for item_index in obj.items:
                    rows, t = reload3mf.compose(reload3mf.parse_transform(project.items[item_index][1]), inner)
                    if mesh is not None:
                        lo, hi = layout.footprint(mesh.verts, rows)
                        cx, cy = t[0] + (lo[0] + hi[0]) / 2.0, t[1] + (lo[1] + hi[1]) / 2.0
                        on = min(range(count), key=lambda i: (corners[i][0] + width / 2.0 - cx) ** 2 +
                                 (corners[i][1] + depth / 2.0 - cy) ** 2)
                    else:
                        cx = cy = None
                        on = plate_no if listed_on.get(oid) == 1 else -1
                    if on == plate_no:
                        copies_here.append((rows, cx, cy))
                if not copies_here and obj.items:
                    # Not standing on the plate that lists it: built from scratch there
                    first = project.items[obj.items[0]][1]
                    copies_here = [(reload3mf.compose(reload3mf.parse_transform(first), inner)[0], None, None)]
                if not copies_here:
                    copies_here = [(reload3mf.compose(reload3mf.parse_transform(None), inner)[0], None, None)]
                ref = _unit_rows(copies_here[0][0])
                mirror = layout.det(ref) < 0.0
                if mirror:
                    # Factor out the reflection as a mirror across the part's own X axis (M = R * diag(-1, 1, 1)),
                    # so the ImportedPart keeps the unmirrored up/turn and the mirror flag puts it back on Build.
                    ref = _strip_mirror(ref)
                up, angle = layout.orientation_from_matrix(ref)
                up = tuple(0.0 if abs(c) < 1e-9 else c for c in up)
                angle = math.radians(round(math.degrees(angle), 4))  # drop float noise: 30.0000001 degrees is 30
                spots, tipped = [], 0
                for rows, cx, cy in copies_here:
                    if cx is None:
                        spots.append(None)
                        continue
                    rows = _unit_rows(rows)
                    if mirror:
                        rows = _strip_mirror(rows)
                    turn_rows = layout.matmul(rows, layout.transpose(ref))
                    if abs(turn_rows[2][2] - 1.0) > 1e-3:
                        tipped += 1
                        turn = 0.0
                    else:
                        turn = math.radians(round(math.degrees(math.atan2(turn_rows[1][0], turn_rows[0][0])), 4))
                    spots.append((round(cx - corners[plate_no][0], 4), round(cy - corners[plate_no][1], 4), turn))
                if all(s is None for s in spots):
                    spots = []
                stl, note = _find_source(part, finder, project_dir, name if plate_paths else "", folders, top,
                                         (lambda f, n=name: known(n, f)) if known else None)
                if tipped:
                    out.dropped.append("%s: %d cop%s tipped another way than the first, built standing like it"
                                       % (obj.name, tipped, "y" if tipped == 1 else "ies"))
                imported = ImportedPart(obj.name, part.source, up, angle, len(copies_here), stl, note,
                                        mirror=mirror, spots=spots, object_meta=object_meta.get(oid, ()),
                                        part_meta=[(k, v) for k, v in part.meta.items() if k not in PART_KEYS])
                seen[oid] = imported
                parts.append(imported)
            out.plates.append(ImportedPlate(name, plate_meta, parts))
        return out, problems
    finally:
        project.close()


def plate_dir(top, name):
    """The folder a plate name stands for below top (the project's STL folder): that path, or top itself when the
    name is top's own folder name and top has no folder of that name (a plate of the parts lying in top)."""
    path = os.path.join(top, *_split(name))
    if os.path.isdir(path):
        return path
    if name and name.strip("/\\") == os.path.basename(os.path.normpath(top)) and os.path.isdir(top):
        return top
    return path


def _find_source(part, finder, project_dir, plate_name, folders, top=None, known=None):
    """(STL path or None, note). Only sure links, in this order:
    1. the stored path (absolute, or from the 3MF's folder), when the file is there;
    2. known(file name): the link the tab already had for this part (a re-import), or None;
    3. plate_name read as a folder (only when given): that path below top (the project's STL folder; default the
       STL root), and the folders above it up to top. The file must be in exactly one of them;
    4. the stored path's trailing folders below the STL root (at least one folder);
    5. the file name, when exactly one file has it below top (unique_name_hits). Two or more: red, never the first."""
    stored = part.source
    if stored:
        direct = stored if os.path.isabs(stored) else os.path.join(project_dir, stored)
        if os.path.isfile(direct):
            return direct, ""
    file_name = os.path.basename(stored.replace("\\", "/"))
    if not file_name:
        return None, "no STL path stored"
    if known is not None:
        path = known(file_name)
        if path:
            return path, "kept the tab's link"
    plate_note = ""
    if plate_name:
        tops = [top] if top else finder.search_dirs
        leaf = next((plate_dir(t, plate_name) for t in tops if os.path.isdir(plate_dir(t, plate_name))), None)
        if leaf is not None:
            hits = find_all_up(file_name, leaf, tops)
            if len(hits) == 1:
                return hits[0], "from the plate's folders"
            if hits:
                return None, "%s is in %d of the plate's folders" % (file_name, len(hits))
            plate_note = "%s is not in the plate's folder %s or the folders above it" % (file_name, plate_name)
        else:
            plate_note = "there is no folder %s below the project's STL folder" % plate_name
    path, _ = finder.find(stored, project_dir, by_name=False)
    if path is not None:
        return path, ""
    hits = unique_name_hits(file_name, finder, top)
    if len(hits) == 1:
        return hits[0], "the only %s in the project's STL folder" % file_name
    if "/" in stored.replace("\\", "/"):
        return None, "not found"
    if len(hits) > 1:
        return None, "Orca kept only the name %s, %d files have it in the project's STL folder%s: give each a " \
                     "unique name (a tag in Combi) or use Relink" % (
                         file_name, len(hits), ", and " + plate_note if plate_note else "")
    if plate_note:
        return None, "Orca kept only the name %s, and %s: use Relink" % (file_name, plate_note)
    return None, "Orca kept only the name %s: use Relink" % file_name


def unique_name_hits(file_name, finder, top=None):
    """The files named file_name (any case) below top (the project's STL folder), else below the STL root. Exactly
    one is a sure link: Combi tags every variant (button_loose.stl, button_tight.stl), so a name says which file."""
    hits = sorted(finder.name_hits(file_name))
    if top:
        hits = [h for h in hits if _inside(h, top)]
    return hits


def _inside(path, folder):
    path = os.path.normcase(os.path.abspath(path))
    folder = os.path.normcase(os.path.abspath(folder))
    return path == folder or path.startswith(folder.rstrip(os.sep) + os.sep)


def find_all_up(file_name, folder, roots):
    """Every file_name in folder and in the folders above it, up to the root it is below (any folder of roots,
    itself included), nearest first. Never looks into a sibling."""
    tops = {os.path.normcase(os.path.abspath(r)) for r in roots}
    folder = os.path.abspath(folder)
    hits = []
    while True:
        cand = os.path.join(folder, file_name)
        if os.path.isfile(cand):
            hits.append(cand)
        up = os.path.dirname(folder)
        if os.path.normcase(folder) in tops or up == folder:
            return hits
        folder = up


def find_up(file_name, folder, roots):
    """file_name when it is in exactly one of folder and the folders above it up to the root (find_all_up), else
    None."""
    hits = find_all_up(file_name, folder, roots)
    return hits[0] if len(hits) == 1 else None


def _split(path):
    return [p for p in re.split(r"[\\/]+", path.strip()) if p]


def plate_folders(plate_name, roots, folders=None):
    """The folders below the roots whose path ends in the plate's name ("tight/cap_loose"), or [].
    folders: a dict that keeps the folder list between calls."""
    want = [p.lower() for p in _split(plate_name)]
    if not want:
        return []
    folders = {} if folders is None else folders
    if "all" not in folders:
        folders["all"] = [d for root in roots for d, _, _ in os.walk(root)]
    return [d for d in folders["all"] if [p.lower() for p in _split(d)][-len(want):] == want]


def plate_name_for(folder, roots, folders=None):
    """The shortest end of folder's path ("tight/cap_loose") that no other folder below the roots ends in, with /
    between names; the folder's own name when it is not below a root."""
    folders = {} if folders is None else folders
    pieces = _split(os.path.abspath(folder))
    for k in range(1, len(pieces) + 1):
        name = "/".join(pieces[-k:])
        hits = plate_folders(name, roots, folders)
        if len(hits) <= 1:
            return name
    return "/".join(pieces)


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

