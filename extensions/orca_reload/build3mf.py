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


class PartSpec:
    """One part: the STL file (absolute path), the direction of the part that points up on the plate, the turn
    around it (radians), how many copies, and an optional seam function (stl_path, Mesh) -> None or
    (paint_seam strings by triangle index, note for the report)."""

    def __init__(self, name, stl, up=(0.0, 0.0, 1.0), angle=0.0, copies=1, seam=None):
        self.name = name or os.path.basename(stl)
        self.stl = stl
        self.up = tuple(up)
        self.angle = angle
        self.copies = max(int(copies), 1)
        self.seam = seam


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
    def __init__(self, oid, name, meta, part):
        self.id = oid
        self.name = name
        self.meta = meta  # object settings, [(key, value)] without the name
        self.part = part  # reload3mf.Part of its one model part, or None


class Base:
    """The settings a build starts from: an existing project (everything below), else a template (its settings
    files only), else nothing."""

    def __init__(self, path=None, template=None):
        self.settings_from = None
        self.files = {}  # zip entry -> bytes, written as they are
        self.metadata = {"Application": APPLICATION, "OrcaSlicer": ORCA_VERSION, "BambuStudio:3mfVersion": "1"}
        self.objects = {}  # name -> [_OldObject], in file order
        self.plates = []  # [(key, value)] of each plate, by position
        self.project = None
        if path and os.path.isfile(path):
            self._read_project(path)
        elif template:
            if not os.path.isfile(template):
                raise ReloadError("settings project not found: %s" % template)
            with zipfile.ZipFile(template) as z:
                self._take_settings(z, template)

    def _take_settings(self, z, path):
        for name in z.namelist():
            if SETTINGS_FILES.match(name):
                self.files[name] = z.read(name)
        if SETTINGS not in self.files:
            return
        self.settings_from = path
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
            if KEPT_FILES.match(name):
                self.files[name] = z.read(name)
        root = ET.fromstring(z.read(reload3mf.ROOT_MODEL))
        for m in root.findall(reload3mf.CORE_NS + "metadata"):
            if m.get("name") in ("Title", "Designer", "Description", "Copyright", "License", "Origin",
                                 "CreationDate"):
                self.metadata[m.get("name")] = m.text or ""
        settings = ET.fromstring(z.read(reload3mf.MODEL_SETTINGS))
        for o in settings.findall("object"):
            obj = project.objects.get(o.get("id"))
            meta = [(m.get("key"), m.get("value")) for m in o.findall("metadata")
                    if m.get("key") and m.get("key") != "name"]
            parts = [p for p in obj.parts if p.is_model_part] if obj else []
            part = parts[0] if len(parts) == 1 and len(obj.parts) == 1 else None
            name = obj.name if obj else o.get("id")
            self.objects.setdefault(name, []).append(_OldObject(o.get("id"), name, meta, part))
        for plate in settings.findall("plate"):
            self.plates.append([(m.get("key"), m.get("value")) for m in plate.findall("metadata")
                                if m.get("key") and m.get("key") not in PLATE_KEYS])

    def take_object(self, name):
        """The existing object of that name, once each."""
        found = self.objects.get(name)
        return found.pop(0) if found else None

    def settings(self):
        if SETTINGS not in self.files:
            return None
        try:
            return json.loads(self.files[SETTINGS].decode("utf-8"))
        except ValueError:
            raise ReloadError("the printer settings of %s cannot be read" % self.settings_from)

    def bed(self, fallback):
        """(x0, y0, width, depth) of the printable area."""
        settings = self.settings() or {}
        points = []
        for p in settings.get("printable_area") or []:
            try:
                x, y = p.lower().split("x")
                points.append((float(x), float(y)))
            except ValueError:
                pass
        if len(points) >= 3:
            xs, ys = [p[0] for p in points], [p[1] for p in points]
            return min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys)
        return 0.0, 0.0, float(fallback[0]), float(fallback[1])

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
        self.id = None


def _load(spec, stl_cache):
    key = os.path.normcase(os.path.abspath(spec.stl))
    if key not in stl_cache:
        stl_cache[key] = reload3mf.read_stl(spec.stl)
    return stl_cache[key]


def _prepare(obj, base, stl_cache):
    spec = obj.spec
    stl, _ = _load(spec, stl_cache)  # degenerate triangles are dropped, as Orca's own import does
    seam = spec.seam(spec.stl, stl) if spec.seam else None
    obj.old = base.take_object(spec.name)
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
                _prepare(obj, base, stl_cache)
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


def write(spec, base, objects, out_path):
    """Writes the project to out_path (through a temporary file, so a failed write leaves the old file)."""
    files = {}
    root = [_model_head()]
    for key, value in base.metadata.items():
        root.append(' <metadata name=%s>%s</metadata>\n' % (quoteattr(key), escape(value)))
    root.append(" <resources>\n")
    rels = []
    for n, obj in enumerate(objects, 1):
        obj.id = 2 * n
        path = _file_name(obj.spec.name, n)
        sub = [_model_head(), ' <metadata name="BambuStudio:3mfVersion">1</metadata>\n <resources>\n',
               '  <object id="%d" p:UUID="%08x-81cb-4c03-9d28-80fed5dfa1dc" type="model">\n' % (2 * n - 1, n),
               "   ", reload3mf.mesh_xml(obj.mesh, "   ", obj.extras), "\n  </object>\n </resources>\n"
               " <build/>\n</model>\n"]
        files[path] = "".join(sub)
        root.append('  <object id="%d" p:UUID="%08x-61cb-4c03-9d28-80fed5dfa1dc" type="model">\n'
                    '   <components>\n    <component p:path="/%s" objectid="%d" '
                    'p:UUID="%04x0000-b206-40ff-9872-83e8017abed1" transform="1 0 0 0 1 0 0 0 1 0 0 0"/>\n'
                    '   </components>\n  </object>\n' % (obj.id, n, escape(path), 2 * n - 1, n))
        rels.append(' <Relationship Target="/%s" Id="rel-%d" '
                    'Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>\n' % (escape(path), n))
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
        + "".join(rels) + "</Relationships>\n")
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
        out.append('    <part id="%d" subtype="normal_part">\n' % (obj.id - 1))
        out.append(_meta_line("      ", "name", obj.spec.name))
        out.append(_meta_line("      ", "matrix", "1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1"))
        out.append(_meta_line("      ", "source_file", obj.spec.stl))
        out.append(_meta_line("      ", "source_object_id", "0"))
        out.append(_meta_line("      ", "source_volume_id", "0"))
        for axis, value in zip("xyz", obj.offset):
            out.append(_meta_line("      ", "source_offset_" + axis, repr(float(value))))
        out += [_meta_line("      ", k, v) for k, v in part_meta]
        out.append('      <mesh_stat edges_fixed="0" degenerate_facets="0" facets_removed="0" '
                   'facets_reversed="0" backwards_edges="0"/>\n    </part>\n  </object>\n')
    identify = 0
    for plate_no, plate in enumerate(spec.plates):
        out.append("  <plate>\n")
        out.append(_meta_line("    ", "plater_id", plate_no + 1))
        out.append(_meta_line("    ", "plater_name", plate.name))
        kept = base.plates[plate_no] if plate_no < len(base.plates) else [("locked", "false")]
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
            lines.append("  settings from %s, bed %g x %g mm" % (
                "the project" if not created else base.settings_from, bed[2], bed[3]))
        else:
            problems.append("no printer settings: set Settings from to an Orca project made for your printer "
                            "(Orca opens a project without them as bare parts, without plates)")
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
    def __init__(self, name, source, up, angle, copies, stl=None, note=""):
        self.name = name
        self.source = source  # source_file as stored in the project
        self.stl = stl  # the STL found for it, or None
        self.up = up
        self.angle = angle
        self.copies = copies
        self.note = note


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
                up, angle = layout.orientation_from_matrix(rows)
                up = tuple(0.0 if abs(c) < 1e-9 else c for c in up)
                stl, note = _find_source(project, part, finder, project_dir, stl_cache)
                angle = math.radians(round(math.degrees(angle), 4))  # drop float noise: 30.0000001 degrees is 30
                imported = ImportedPart(obj.name, part.source, up, angle, 1, stl, note)
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

