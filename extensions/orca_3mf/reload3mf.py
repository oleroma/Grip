#!/usr/bin/env python3
"""Reload every STL part of OrcaSlicer 3MF projects from disk, in one run.

Gives the same result as Orca's "Reload from disk" on every part, for any
number of project files, without opening Orca. Orientation, plate placement
and per-object settings are kept. The command line never overwrites the
original project: the result is written to a new file (PROJECT_reloaded.3mf
by default).

The Orca Reload Blender extension (this folder) runs the same code and also
paints seam lines from Blender onto the parts, see seams.py. The command line
is tools/orca_reload/orca_reload.py:
    python tools/orca_reload/orca_reload.py PROJECT.3mf [MORE.3mf | FOLDER ...] [options]

Only the Python standard library is needed (Python 3.8+), so Blender's
bundled Python works too. See README.md next to this file.
"""

import argparse
import os
import re
import struct
import sys
import tempfile
import zipfile
import xml.etree.ElementTree as ET
import xml.parsers.expat
from array import array

CORE_NS = "{http://schemas.microsoft.com/3dmanufacturing/core/2015/02}"
PROD_NS = "{http://schemas.microsoft.com/3dmanufacturing/production/2015/06}"
ROOT_MODEL = "3D/3dmodel.model"
MODEL_SETTINGS = "Metadata/model_settings.config"
CUT_INFO = "Metadata/cut_information.xml"
DEFAULT_SUFFIX = "_reloaded"

# Orca's SINKING_Z_THRESHOLD: an object whose lowest point is below this was
# deliberately sunk into the bed, so Orca does not drop it back after a reload.
SINKING_Z = -0.001
# Geometry that matches the stored mesh within this distance (mm) is unchanged.
SAME_TOL = 1e-4

EXIT_OK, EXIT_ERROR, EXIT_INCOMPLETE = 0, 1, 2

# Part statuses that change the project: a new mesh, or the same mesh with new seam painting.
CHANGED = ("updated", "seams")
SEAM_ATTR = "paint_seam"


class ReloadError(Exception):
    pass


# --------------------------------------------------------------------------
# Meshes


class Mesh:
    """Indexed triangle mesh: flat x,y,z vertex coordinates and flat indices."""

    def __init__(self, verts, tris):
        self.verts = verts
        self.tris = tris

    @property
    def vertex_count(self):
        return len(self.verts) // 3

    @property
    def triangle_count(self):
        return len(self.tris) // 3

    def bbox(self):
        v = self.verts
        lo = (min(v[0::3]), min(v[1::3]), min(v[2::3]))
        hi = (max(v[0::3]), max(v[1::3]), max(v[2::3]))
        return lo, hi

    def center(self):
        lo, hi = self.bbox()
        return tuple((a + b) / 2 for a, b in zip(lo, hi))

    def size(self):
        lo, hi = self.bbox()
        return tuple(b - a for a, b in zip(lo, hi))

    def translated(self, d):
        """Copy moved by d, rounded to float32 like Orca stores it."""
        dx, dy, dz = d
        v = self.verts
        moved = array("d", v)
        moved[0::3] = array("d", (x + dx for x in v[0::3]))
        moved[1::3] = array("d", (y + dy for y in v[1::3]))
        moved[2::3] = array("d", (z + dz for z in v[2::3]))
        return Mesh(array("f", moved), self.tris)


def _float32_array(raw):
    a = array("f")
    a.frombytes(raw)
    if sys.byteorder == "big":
        a.byteswap()
    return a


_NEG_ZERO = b"\x00\x00\x00\x80"


def _vertex_key(key):
    # -0.0 and 0.0 are the same point; give them the same key.
    return b"".join(b"\x00\x00\x00\x00" if key[i:i + 4] == _NEG_ZERO else key[i:i + 4]
                    for i in (0, 4, 8))


def _index_corners(corners):
    """Merge identical corner positions (12-byte little-endian float32 keys)
    into shared vertices and drop degenerate triangles, like Orca's STL import.
    Returns (Mesh, dropped_triangle_count)."""
    index = {}
    raw = bytearray()
    tris = array("I")
    dropped = 0
    tri = [0, 0, 0]
    for n, key in enumerate(corners):
        if _NEG_ZERO in key:
            key = _vertex_key(key)
        i = index.get(key)
        if i is None:
            i = index[key] = len(index)
            raw += key
        tri[n % 3] = i
        if n % 3 == 2:
            if tri[0] == tri[1] or tri[1] == tri[2] or tri[0] == tri[2]:
                dropped += 1
            else:
                tris.extend(tri)
    return Mesh(_float32_array(bytes(raw)), tris), dropped


def read_stl(path):
    """Read a binary or ASCII STL. Returns (Mesh, dropped_triangle_count)."""
    with open(path, "rb") as f:
        data = f.read()
    if data.startswith(b"version https://git-lfs"):
        raise ReloadError("this is a Git LFS pointer, not the STL; run git lfs pull")
    binary = False
    if len(data) >= 84:
        (count,) = struct.unpack_from("<I", data, 80)
        expected = 84 + 50 * count
        if len(data) == expected:
            binary = True
        elif len(data) > expected and not data[:5].lower() == b"solid":
            binary = True  # tolerate trailing bytes after the last facet
    if binary:
        def corners():
            for i in range(count):
                base = 96 + 50 * i
                yield data[base:base + 12]
                yield data[base + 12:base + 24]
                yield data[base + 24:base + 36]
        mesh, dropped = _index_corners(corners())
    else:
        text = data.decode("ascii", errors="replace")
        if not text.lstrip()[:5].lower() == "solid":
            raise ReloadError("not a valid STL file")
        coords = re.findall(r"vertex\s+(\S+)\s+(\S+)\s+(\S+)", text)
        if not coords or len(coords) % 3:
            raise ReloadError("ASCII STL has no complete facets")
        pack = struct.Struct("<3f").pack
        mesh, dropped = _index_corners(pack(float(x), float(y), float(z)) for x, y, z in coords)
    if mesh.triangle_count == 0:
        raise ReloadError("STL has no triangles")
    return mesh, dropped


_OBJECT_TAG = re.compile(r"<object\b[^>]*>")
_ID_ATTR = re.compile(r'(?<![\w:])id="([^"]*)"')
_ATTR = re.compile(r'([\w:]+)="([^"]*)"')
_QUOTED = re.compile(r'"([^"]*)"')


def find_object(text, object_id):
    """Span (start, end) of <object id="object_id"> ... </object> in model XML."""
    for m in _OBJECT_TAG.finditer(text):
        found = _ID_ATTR.search(m.group(0))
        if found and found.group(1) == object_id:
            end = text.find("</object>", m.end())
            if end < 0:
                break
            return m.start(), end + len("</object>")
    raise ReloadError("object id %s not found in model file" % object_id)


def find_mesh(text, object_id):
    """Span (start, end) of the <mesh> element of an object, start at '<mesh'."""
    start, end = find_object(text, object_id)
    m_start = text.find("<mesh", start, end)
    m_end = text.find("</mesh>", start, end)
    if m_start < 0 or m_end < 0:
        raise ReloadError("object id %s has no mesh" % object_id)
    return m_start, m_end + len("</mesh>")


def parse_mesh(mesh_text):
    """Parse a 3MF <mesh> element. Returns (Mesh, extras): extras maps the index of
    each triangle that has attributes besides v1, v2, v3 (painting: paint_color,
    paint_seam, paint_supports, ...) to those attributes, as written in the file."""
    v_start = mesh_text.find("<vertices")
    v_end = mesh_text.find("</vertices>")
    t_start = mesh_text.find("<triangles")
    t_end = mesh_text.find("</triangles>")
    if min(v_start, v_end, t_start, t_end) < 0:
        raise ReloadError("mesh without vertices or triangles")
    vtext = mesh_text[v_start:v_end]
    ttext = mesh_text[t_start:t_end]
    n_verts = len(re.findall(r"<vertex\b", vtext))
    n_tris = len(re.findall(r"<triangle\b", ttext))

    # Orca writes exactly x, y, z and v1, v2, v3: grab every quoted value.
    values = _QUOTED.findall(vtext)
    if len(values) != 3 * n_verts:
        values = []
        for tag in re.findall(r"<vertex\b([^>]*)>", vtext):
            attrs = dict(_ATTR.findall(tag))
            values += (attrs["x"], attrs["y"], attrs["z"])
    verts = array("d", map(float, values))

    extras = {}
    values = _QUOTED.findall(ttext)
    if len(values) != 3 * n_tris:
        # Painting (supports, seams, colours) or other per-triangle data.
        values = []
        for i, tag in enumerate(re.findall(r"<triangle\b([^>]*)>", ttext)):
            attrs = dict(_ATTR.findall(tag))
            values += (attrs.pop("v1"), attrs.pop("v2"), attrs.pop("v3"))
            if attrs:
                extras[i] = attrs
    tris = array("I", map(int, values))
    return Mesh(verts, tris), extras


def mesh_xml(mesh, indent, extras=None):
    """<mesh> element text in Orca's layout; indent is the <mesh> line's indent.
    extras: attributes to add to triangles, by triangle index (see parse_mesh)."""
    i1, i2 = indent + " ", indent + "  "
    vfmt = i2 + '<vertex x="%.9g" y="%.9g" z="%.9g"/>\n'
    tfmt = i2 + '<triangle v1="%d" v2="%d" v3="%d"/>\n'
    it_v = iter(mesh.verts)
    it_t = iter(mesh.tris)
    if extras:
        tlines = []
        for i, tri in enumerate(zip(it_t, it_t, it_t)):
            attrs = extras.get(i)
            if attrs:
                tlines.append(i2 + '<triangle v1="%d" v2="%d" v3="%d"' % tri
                              + "".join(' %s="%s"' % kv for kv in attrs.items()) + "/>\n")
            else:
                tlines.append(tfmt % tri)
        triangles = "".join(tlines)
    else:
        triangles = "".join(map(tfmt.__mod__, zip(it_t, it_t, it_t)))
    return "".join((
        "<mesh>\n", i1, "<vertices>\n",
        "".join(map(vfmt.__mod__, zip(it_v, it_v, it_v))),
        i1, "</vertices>\n", i1, "<triangles>\n",
        triangles,
        i1, "</triangles>\n", indent, "</mesh>",
    ))


def same_shape(old, new, old_shift, new_shift):
    """True when both meshes describe the same triangles once moved by their shifts."""
    if old.triangle_count != new.triangle_count:
        return False
    extent = max(max(old.size()), max(new.size()), 1.0)
    tol = max(SAME_TOL, 2e-6 * extent)
    if old.vertex_count == new.vertex_count and old.tris == new.tris:
        pairs = ((old.verts, new.verts),)
    else:
        # Same triangles, different vertex numbering: compare triangle corners.
        ov, nv = old.verts, new.verts
        pairs = ((array("d", (ov[3 * i + k] for i in old.tris for k in range(3))),
                  array("d", (nv[3 * i + k] for i in new.tris for k in range(3)))),)
    for a, b in pairs:
        for k in range(3):
            d = old_shift[k] - new_shift[k]
            if max(map(lambda x, y: abs(x + d - y), a[k::3], b[k::3])) > tol:
                return False
    return True


# --------------------------------------------------------------------------
# Transforms (3MF stores 3x4 matrices column by column)


def parse_transform(text):
    """3MF transform string -> (rows of the 3x3 part, translation)."""
    if not text:
        return ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)), (0.0, 0.0, 0.0)
    m = [float(x) for x in text.split()]
    if len(m) != 12:
        raise ReloadError("bad transform %r" % text)
    rows = tuple((m[r], m[3 + r], m[6 + r]) for r in range(3))
    return rows, (m[9], m[10], m[11])


def compose(outer, inner):
    """outer(inner(p)) for (rows, translation) transforms."""
    (ra, ta), (rb, tb) = outer, inner
    rows = tuple(tuple(sum(ra[r][k] * rb[k][c] for k in range(3)) for c in range(3)) for r in range(3))
    t = tuple(sum(ra[r][k] * tb[k] for k in range(3)) + ta[r] for r in range(3))
    return rows, t


def _inverse3(m):
    a, b, c = m[0]
    d, e, f = m[1]
    g, h, i = m[2]
    det = a * (e * i - f * h) - b * (d * i - f * g) + c * (d * h - e * g)
    if abs(det) < 1e-12:
        raise ReloadError("singular transform")
    return (((e * i - f * h) / det, (c * h - b * i) / det, (b * f - c * e) / det),
            ((f * g - d * i) / det, (a * i - c * g) / det, (c * d - a * f) / det),
            ((d * h - e * g) / det, (b * g - a * h) / det, (a * e - b * d) / det))


def invert(transform):
    """Inverse of a (rows, translation) transform."""
    rows, t = transform
    inv = _inverse3(rows)
    return inv, tuple(-sum(inv[r][k] * t[k] for k in range(3)) for r in range(3))


def min_z(mesh, transform):
    (rows, t) = transform
    a, b, c = rows[2]
    v = mesh.verts
    return min(map(lambda x, y, z: a * x + b * y + c * z, v[0::3], v[1::3], v[2::3])) + t[2]


def set_transform_z(text, dz):
    m = (text or "1 0 0 0 1 0 0 0 1 0 0 0").split()
    m[11] = "%.9g" % (float(m[11]) + dz)
    return " ".join(m)


# --------------------------------------------------------------------------
# Finding source files


def _split_path(path):
    return [p for p in re.split(r"[\\/]+", path) if p]


class SourceFinder:
    """Finds the STL a part was loaded from, even if the project or the STLs moved."""

    def __init__(self, search_dirs):
        self.search_dirs = [os.path.abspath(d) for d in search_dirs]
        self._names = None

    def _name_index(self):
        if self._names is None:
            self._names = {}
            for root in self.search_dirs:
                for dirpath, _, files in os.walk(root):
                    for f in files:
                        self._names.setdefault(f.lower(), set()).add(os.path.join(dirpath, f))
        return self._names

    def find(self, stored, project_dir):
        """Returns (path or None, problem or None)."""
        direct = stored if os.path.isabs(stored) else os.path.join(project_dir, stored)
        if os.path.isfile(direct):
            return direct, None
        parts = [p for p in _split_path(stored) if not p.endswith(":")]
        if not parts:
            return None, "no source path stored"
        # Trailing pieces of the stored path, longest first, under the project's
        # folder and each search folder ("...\GripV\parts\R4.stl" -> "parts/R4.stl").
        for root in [project_dir] + self.search_dirs:
            for k in range(len(parts), 0, -1):
                cand = os.path.join(root, *parts[-k:])
                if os.path.isfile(cand):
                    return cand, None
        # Same file name anywhere under the search folders.
        if self.search_dirs:
            hits = sorted(self._name_index().get(parts[-1].lower(), ()))
            if len(hits) == 1:
                return hits[0], None
            if hits:
                return None, "ambiguous, %d files named %s: %s" % (
                    len(hits), parts[-1], ", ".join(hits[:4]) + (", ..." if len(hits) > 4 else ""))
        return None, "file not found"


# --------------------------------------------------------------------------
# Project


class Part:
    def __init__(self, obj, part_id, subtype, meta, component):
        self.obj = obj
        self.id = part_id
        self.subtype = subtype
        self.meta = meta
        self.model_path, self.sub_id, self.transform = component
        self.name = meta.get("name") or obj.name
        self.source = meta.get("source_file", "")
        self.status = None
        self.detail = ""
        self.old_mesh = None
        self.new_mesh = None
        self.new_offset = None
        self.extras = {}  # per-triangle attributes of the stored mesh (painting)
        self.new_extras = None

    @property
    def is_model_part(self):
        return self.subtype in (None, "", "normal_part")


class Obj:
    def __init__(self, obj_id, name):
        self.id = obj_id
        self.name = name
        self.parts = []
        self.items = []  # indices into Project.items, instance order
        self.plates = set()
        self.cut = False
        self.z_shift = 0.0


class Project:
    def __init__(self, path):
        self.path = path
        self.zip = zipfile.ZipFile(path)
        names = set(self.zip.namelist())
        if ROOT_MODEL not in names or MODEL_SETTINGS not in names:
            raise ReloadError("not an OrcaSlicer/Bambu Studio project (no %s)" % MODEL_SETTINGS)
        self.edited = {}  # zip entry -> new text
        self._read = {}
        self.objects = {}
        self.items = []  # [object id, transform text, auto_drop]
        self._read_model()
        self._read_settings()
        self._read_cut_info()

    def text(self, name):
        """Current text of a zip entry, including edits made so far."""
        if name in self.edited:
            return self.edited[name]
        if name not in self._read:
            self._read[name] = self.zip.read(name).decode("utf-8")
        return self._read[name]

    def _read_model(self):
        root = ET.fromstring(self.zip.read(ROOT_MODEL))
        self.model_order = []
        components = {}
        for obj in root.iter(CORE_NS + "object"):
            comps = obj.find(CORE_NS + "components")
            if comps is None:
                continue
            components[obj.get("id")] = [
                ((c.get(PROD_NS + "path") or "/" + ROOT_MODEL).lstrip("/"), c.get("objectid"), c.get("transform"))
                for c in comps.findall(CORE_NS + "component")]
            self.model_order.append(obj.get("id"))
        self.components = components
        build = root.find(CORE_NS + "build")
        for item in (build.findall(CORE_NS + "item") if build is not None else []):
            self.items.append([item.get("objectid"), item.get("transform"), item.get("auto_drop", "1") != "0"])

    def _read_settings(self):
        root = ET.fromstring(self.zip.read(MODEL_SETTINGS))
        for o in root.findall("object"):
            oid = o.get("id")
            meta = {m.get("key"): m.get("value") for m in o.findall("metadata") if m.get("key")}
            obj = Obj(oid, meta.get("name", "object %s" % oid))
            comps = {c[1]: c for c in self.components.get(oid, [])}
            for p in o.findall("part"):
                pmeta = {m.get("key"): m.get("value") for m in p.findall("metadata") if m.get("key")}
                comp = comps.get(p.get("id"))
                part = Part(obj, p.get("id"), p.get("subtype"), pmeta, comp or (None, None, None))
                if comp is None:
                    part.status, part.detail = "skipped", "no mesh found for this part"
                obj.parts.append(part)
            self.objects[oid] = obj
        for plate in root.findall("plate"):
            pmeta = {m.get("key"): m.get("value") for m in plate.findall("metadata")}
            for inst in plate.findall("model_instance"):
                imeta = {m.get("key"): m.get("value") for m in inst.findall("metadata")}
                obj = self.objects.get(imeta.get("object_id"))
                if obj is not None and pmeta.get("plater_id"):
                    obj.plates.add(int(pmeta["plater_id"]))
        for i, item in enumerate(self.items):
            if item[0] in self.objects:
                self.objects[item[0]].items.append(i)

    def _read_cut_info(self):
        # Cut objects are listed by their 1-based position in the model.
        if CUT_INFO not in self.zip.namelist():
            return
        root = ET.fromstring(self.zip.read(CUT_INFO))
        for o in root.iter("object"):
            try:
                oid = self.model_order[int(o.get("id")) - 1]
            except (TypeError, ValueError, IndexError):
                continue
            if oid in self.objects:
                self.objects[oid].cut = True

    def parts(self):
        for obj in self.objects.values():
            for part in obj.parts:
                yield part

    def old_mesh(self, part):
        if part.old_mesh is None:
            text = self.text(part.model_path)
            start, end = find_mesh(text, part.sub_id)
            part.old_mesh, part.extras = parse_mesh(text[start:end])
        return part.old_mesh

    def close(self):
        self.zip.close()


def reload_project(project, finder, anchor="center", drop=True, stl_cache=None, seams=None):
    """Work out the new mesh of every reloadable part. Edits are kept in memory.

    seams: optional function (part, stl_path, stl_mesh) -> None, or (paint_seam
    strings by triangle index of stl_mesh, note for the report). None leaves the
    part's painting as the plain reload does: kept while the shape is unchanged,
    removed when it changed. A result replaces the part's seam painting."""
    stl_cache = {} if stl_cache is None else stl_cache
    project_dir = os.path.dirname(os.path.abspath(project.path))
    for part in project.parts():
        if part.status:
            continue
        if part.obj.cut:
            part.status, part.detail = "skipped", "object was cut in Orca; reloading would undo the cut"
            continue
        if not part.source:
            part.status, part.detail = "skipped", "no source file recorded"
            continue
        if not part.source.lower().endswith(".stl"):
            part.status, part.detail = "skipped", "only STL sources are supported"
            continue
        if part.meta.get("source_in_inches") == "1" or part.meta.get("source_in_meters") == "1":
            part.status, part.detail = "skipped", "converted from inches/meters in Orca; not supported"
            continue
        path, problem = finder.find(part.source, project_dir)
        if path is None:
            part.status, part.detail = "missing", "%s (%s)" % (part.source, problem)
            continue
        part.detail = path
        try:
            key = os.path.normcase(os.path.abspath(path))
            if key not in stl_cache:
                stl_cache[key] = read_stl(path)
            stl, dropped = stl_cache[key]
            old = project.old_mesh(part)
        except (ReloadError, OSError, ValueError, KeyError) as e:
            part.status, part.detail = "error", "%s: %s" % (path, e)
            continue
        old_c = old.center()
        stl_c = stl.center()
        notes = []
        if anchor == "origin":
            # Keep the STL's own origin where it was. A fresh import stores the
            # mesh centred, with the STL's centre in source_offset.
            try:
                offset = tuple(float(part.meta["source_offset_" + k]) for k in "xyz")
            except (KeyError, ValueError):
                part.status, part.detail = "error", "no source offset stored; use --anchor center"
                continue
            shift = tuple(o - s for o, s in zip(old_c, offset))
            moved = sum((s - o) ** 2 for s, o in zip(stl_c, offset)) ** 0.5
            if moved > 0.01:
                notes.append("centre moved %.2f mm" % moved)
        else:
            # Orca's own behaviour: the new mesh takes the old one's bounding-box centre.
            shift = tuple(o - s for o, s in zip(old_c, stl_c))
        seam = seams(part, path, stl) if seams else None
        if same_shape(old, stl, (0.0, 0.0, 0.0), shift):
            if seam is None:
                part.status = "unchanged"
                continue
            # Same shape means the same triangles in the same order (same_shape),
            # so keep the stored mesh and its other painting and swap the seams.
            strings, note = seam
            old_seams = {i: a[SEAM_ATTR] for i, a in part.extras.items() if SEAM_ATTR in a}
            if old_seams == strings:
                part.status = "unchanged"
                continue
            extras = {i: {k: v for k, v in a.items() if k != SEAM_ATTR} for i, a in part.extras.items()}
            for i, value in strings.items():
                extras.setdefault(i, {})[SEAM_ATTR] = value
            part.new_mesh = old
            part.new_extras = {i: a for i, a in extras.items() if a}
            part.status = "seams"
            part.detail += " (" + "; ".join([note] + notes) + ")"
            continue
        part.new_mesh = stl.translated(shift)
        part.new_offset = stl_c
        part.status = "updated"
        if dropped:
            notes.append("%d degenerate triangles dropped" % dropped)
        if seam is not None:
            strings, note = seam
            part.new_extras = {i: {SEAM_ATTR: value} for i, value in strings.items()}
            notes.append(note)
            if any(k != SEAM_ATTR for a in part.extras.values() for k in a):
                notes.append("other painting removed, geometry changed")
        elif part.extras:
            notes.append("painting removed, geometry changed")
        if notes:
            part.detail += " (" + "; ".join(notes) + ")"

    if drop:
        _drop_to_bed(project)
    _apply_edits(project)


def _drop_to_bed(project):
    """Like Orca: unless an object was sunk into the bed, put its lowest point on it."""
    for obj in project.objects.values():
        if not any(p.status == "updated" for p in obj.parts) or not obj.items:
            continue
        instance = parse_transform(project.items[obj.items[0]][1])
        old_z, new_z = [], []
        for part in obj.parts:
            if not part.is_model_part or part.model_path is None:
                continue
            try:
                old = project.old_mesh(part)
            except ReloadError:
                continue
            transform = compose(instance, parse_transform(part.transform))
            old_z.append(min_z(old, transform))
            new_z.append(min_z(part.new_mesh or old, transform))
        if not old_z or min(old_z) < SINKING_Z:
            continue
        obj.z_shift = -min(new_z)
        if abs(obj.z_shift) < 1e-7:
            obj.z_shift = 0.0
            continue
        for i in obj.items:
            if project.items[i][2]:
                project.items[i][1] = set_transform_z(project.items[i][1], obj.z_shift)


def _apply_edits(project):
    # New meshes and painting, in the sub-model files.
    for part in project.parts():
        if part.status not in CHANGED:
            continue
        text = project.text(part.model_path)
        start, end = find_mesh(text, part.sub_id)
        indent = text[text.rfind("\n", 0, start) + 1:start]
        project.edited[part.model_path] = (text[:start] + mesh_xml(part.new_mesh, indent, part.new_extras)
                                           + text[end:])

    # Build item heights, in the root model.
    shifted = {i for obj in project.objects.values() if obj.z_shift for i in obj.items}
    if shifted:
        text = project.text(ROOT_MODEL)
        build = text.find("<build")
        out, pos = [text[:build]], build
        for i, m in enumerate(re.finditer(r"<item\b[^>]*>", text[build:])):
            if i in shifted:
                tag = m.group(0)
                if ' transform="' not in tag:
                    tag = re.sub(r"\s*/?>$", lambda e: ' transform=""' + e.group(0), tag)
                tag = re.sub(r'(\stransform=")[^"]*(")',
                             lambda t: t.group(1) + project.items[i][1] + t.group(2), tag)
                out += [text[pos:build + m.start()], tag]
                pos = build + m.end()
        out.append(text[pos:])
        project.edited[ROOT_MODEL] = "".join(out)

    # Source offsets, in model_settings.config: where a fresh import of the new
    # STL would put them, so later reloads and "Replace with STL" line up.
    updated = [p for p in project.parts() if p.status == "updated"]
    if updated:
        text = project.text(MODEL_SETTINGS)
        for part in updated:
            o_start, o_end = _block(text, "object", part.obj.id, 0, len(text))
            p_start, p_end = _block(text, "part", part.id, o_start, o_end)
            block = text[p_start:p_end]
            for axis, value in zip("xyz", part.new_offset):
                block = re.sub(r'(<metadata key="source_offset_%s" value=")[^"]*(")' % axis,
                               lambda m: m.group(1) + repr(value) + m.group(2), block)
            text = text[:p_start] + block + text[p_end:]
        project.edited[MODEL_SETTINGS] = text


def _block(text, tag, block_id, start, end):
    m = re.compile(r'<%s\s+id="%s"[^>]*>' % (tag, re.escape(block_id))).search(text, start, end)
    if not m:
        raise ReloadError("%s id %s not found in %s" % (tag, block_id, MODEL_SETTINGS))
    close = text.find("</%s>" % tag, m.end(), end)
    if close < 0:
        raise ReloadError("%s id %s is not closed in %s" % (tag, block_id, MODEL_SETTINGS))
    return m.start(), close + len(tag) + 3


def write_project(project, out_path, replace=False):
    """Copy the project to out_path with the edited entries swapped in.
    Writing over the original needs replace=True; the project is closed then."""
    same = os.path.exists(out_path) and os.path.samefile(out_path, project.path)
    if same and not replace:
        raise ReloadError("refusing to overwrite the original project")
    out_dir = os.path.dirname(os.path.abspath(out_path))
    fd, tmp = tempfile.mkstemp(suffix=".3mf", dir=out_dir)
    os.close(fd)
    try:
        with zipfile.ZipFile(tmp, "w", allowZip64=True) as out:
            for info in project.zip.infolist():
                if info.filename in project.edited:
                    data = project.edited[info.filename].encode("utf-8")
                else:
                    data = project.zip.read(info.filename)
                copy = zipfile.ZipInfo(info.filename, date_time=info.date_time)
                copy.compress_type = info.compress_type
                copy.external_attr = info.external_attr
                copy.create_system = info.create_system
                out.writestr(copy, data)
        _check_output(tmp, project)
        os.chmod(tmp, 0o644)
        if same:
            project.close()  # Windows cannot replace a file that is still open
        os.replace(tmp, out_path)
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)


def _check_output(path, project):
    """Re-read the written file: the zip is sound, edited XML parses, meshes match."""
    with zipfile.ZipFile(path) as z:
        bad = z.testzip()
        if bad:
            raise ReloadError("written file is damaged at %s" % bad)
        for name in project.edited:
            xml.parsers.expat.ParserCreate().Parse(z.read(name), True)
        for part in project.parts():
            if part.status in CHANGED:
                text = z.read(part.model_path).decode("utf-8")
                start, end = find_mesh(text, part.sub_id)
                if (text.count("<vertex ", start, end) != part.new_mesh.vertex_count
                        or text.count("<triangle ", start, end) != part.new_mesh.triangle_count):
                    raise ReloadError("written mesh for %s does not match" % part.name)


# --------------------------------------------------------------------------
# Command line


def _fmt_size(size):
    return "x".join("%.2f" % s for s in size)


def report_lines(project, out_path, written):
    """The report of one project, as lines of text."""
    lines = []
    counts = {}
    for obj in project.objects.values():
        plates = ", ".join(str(p) for p in sorted(obj.plates)) or "-"
        for part in obj.parts:
            counts[part.status] = counts.get(part.status, 0) + 1
            if part.status == "unchanged":
                continue
            label = part.name if part.name == obj.name else "%s / %s" % (obj.name, part.name)
            line = "  %-9s %-34s plate %-6s" % (part.status, label, plates)
            if part.status == "seams":
                line += " shape unchanged\n            from %s" % part.detail
            elif part.status == "updated":
                old, new = part.old_mesh, part.new_mesh
                line += " %d -> %d triangles, size %s -> %s mm" % (
                    old.triangle_count, new.triangle_count, _fmt_size(old.size()), _fmt_size(new.size()))
                if obj.z_shift:
                    line += ", moved %+.3f mm in Z to sit on the bed" % obj.z_shift
                line += "\n            from %s" % part.detail
            else:
                line += " " + part.detail
            lines.append(line)
    names = {"seams": "with new seams"}
    summary = ", ".join("%d %s" % (counts[k], names.get(k, k)) for k in
                        ("updated", "seams", "unchanged", "missing", "skipped", "error") if counts.get(k))
    head = os.path.basename(project.path)
    if written:
        head += " -> " + out_path
    elif counts.get("updated") or counts.get("seams"):
        head += " (dry run, nothing written)"
    else:
        head += " (no changes, nothing written)"
    return [head] + lines + ["  " + (summary or "no parts"), ""]


def report(project, out_path, written):
    for line in report_lines(project, out_path, written):
        print(line)


def process(path, finder, out_path, anchor="center", drop=True, stl_cache=None, seams=None,
            dry_run=False, replace=False):
    """Reload one project and write the result to out_path unless nothing changed.
    Returns (report lines, exit status). Raises on a project that cannot be read."""
    project = Project(path)
    try:
        reload_project(project, finder, anchor=anchor, drop=drop, stl_cache=stl_cache, seams=seams)
        changed = any(p.status in CHANGED for p in project.parts())
        if changed and not dry_run:
            write_project(project, out_path, replace=replace)
        lines = report_lines(project, out_path, changed and not dry_run)
        incomplete = any(p.status in ("missing", "error") for p in project.parts())
        return lines, EXIT_INCOMPLETE if incomplete else EXIT_OK
    finally:
        project.close()


def collect_projects(inputs, suffix):
    found = []
    for item in inputs:
        if os.path.isdir(item):
            for dirpath, _, files in os.walk(item):
                for f in sorted(files):
                    if f.lower().endswith(".3mf") and not f[:-4].endswith(suffix):
                        found.append(os.path.join(dirpath, f))
        else:
            found.append(item)
    return found


def output_path(project_path, args=None, suffix=DEFAULT_SUFFIX):
    if args is not None and args.output:
        return args.output
    suffix = args.suffix if args is not None else suffix
    base = os.path.splitext(os.path.basename(project_path))[0] + suffix + ".3mf"
    out_dir = args.out_dir if args is not None else None
    return os.path.join(out_dir or os.path.dirname(os.path.abspath(project_path)), base)


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Reload every STL part of OrcaSlicer 3MF projects from disk, keeping "
                    "orientation, plate placement and settings. Originals are never overwritten.")
    parser.add_argument("projects", nargs="+", metavar="PROJECT",
                        help="3MF project file, or a folder to scan for them")
    parser.add_argument("-o", "--output", help="output file (only with a single project)")
    parser.add_argument("--out-dir", help="folder for the output files (default: next to each project)")
    parser.add_argument("--suffix", default=DEFAULT_SUFFIX,
                        help="added to the file name of each output (default: %(default)s)")
    parser.add_argument("--search", action="append", default=[], metavar="FOLDER",
                        help="where to look for STLs that are not at their stored path "
                             "(repeatable; searched by trailing path, then by file name)")
    parser.add_argument("--anchor", choices=("center", "origin"), default="center",
                        help="center (default, same as Orca): a changed part keeps its bounding-box "
                             "centre. origin: it keeps the STL's own coordinate origin")
    parser.add_argument("--no-drop", action="store_true",
                        help="do not move objects down or up so they sit on the bed")
    parser.add_argument("--dry-run", action="store_true", help="only report, write nothing")
    args = parser.parse_args(argv)

    projects = collect_projects(args.projects, args.suffix)
    if not projects:
        parser.error("no .3mf projects found")
    if args.output and len(projects) > 1:
        parser.error("--output works with a single project; use --out-dir")
    if args.out_dir:
        os.makedirs(args.out_dir, exist_ok=True)

    finder = SourceFinder(args.search)
    stl_cache = {}
    status = EXIT_OK
    for path in projects:
        try:
            lines, code = process(path, finder, output_path(path, args), anchor=args.anchor,
                                  drop=not args.no_drop, stl_cache=stl_cache, dry_run=args.dry_run)
            print("\n".join(lines))
            status = max(status, code)
        except (ReloadError, OSError, zipfile.BadZipFile, ET.ParseError) as e:
            print("%s: %s\n" % (path, e), file=sys.stderr)
            status = EXIT_ERROR
    return status


if __name__ == "__main__":
    sys.exit(main())
