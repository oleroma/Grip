"""Tests for reload3mf.py (the command line reload). Plain Python, no Blender:

    python -I orca_3mf/tests/test_reload.py

The projects are generated here with the same layout OrcaSlicer 2.x writes
(3D/3dmodel.model with components, one 3D/Objects/*.model per part,
Metadata/model_settings.config with parts and plates)."""

import hashlib
import io
import math
import os
import re
import shutil
import struct
import tempfile
import unittest
import sys
import zipfile
from contextlib import redirect_stdout, redirect_stderr

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import reload3mf as orca_reload  # noqa: E402
import seams  # noqa: E402

HEADER = ('<?xml version="1.0" encoding="UTF-8"?>\n<model unit="millimeter" xml:lang="en-US" '
          'xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02" '
          'xmlns:BambuStudio="http://schemas.bambulab.com/package/2021" '
          'xmlns:p="http://schemas.microsoft.com/3dmanufacturing/production/2015/06" requiredextensions="p">\n'
          ' <metadata name="BambuStudio:3mfVersion">1</metadata>\n')


# ---------------------------------------------------------------- geometry helpers

def box(size, center=(0, 0, 0)):
    """Closed box mesh: (list of (x, y, z), list of (a, b, c))."""
    sx, sy, sz = (s / 2 for s in size)
    cx, cy, cz = center
    verts = [(cx + x * sx, cy + y * sy, cz + z * sz)
             for x in (-1, 1) for y in (-1, 1) for z in (-1, 1)]
    tris = [(0, 1, 3), (0, 3, 2), (4, 6, 7), (4, 7, 5), (0, 4, 5), (0, 5, 1),
            (2, 3, 7), (2, 7, 6), (0, 2, 6), (0, 6, 4), (1, 5, 7), (1, 7, 3)]
    return verts, tris


def write_stl(path, mesh, ascii=False):
    verts, tris = mesh
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if ascii:
        lines = ["solid test"]
        for t in tris:
            lines.append(" facet normal 0 0 0\n  outer loop")
            lines += ["   vertex %r %r %r" % verts[i] for i in t]
            lines.append("  endloop\n endfacet")
        lines.append("endsolid test\n")
        with open(path, "w") as f:
            f.write("\n".join(lines))
        return
    with open(path, "wb") as f:
        f.write(b"\0" * 80 + struct.pack("<I", len(tris)))
        for t in tris:
            f.write(struct.pack("<3f", 0, 0, 0))
            for i in t:
                f.write(struct.pack("<3f", *verts[i]))
            f.write(b"\0\0")


def rot_x(deg):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return ((1, 0, 0), (0, c, -s), (0, s, c))


def rot_z(deg):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return ((c, -s, 0), (s, c, 0), (0, 0, 1))


def matmul(a, b):
    return tuple(tuple(sum(a[r][k] * b[k][c] for k in range(3)) for c in range(3)) for r in range(3))


def transform_str(rows, t):
    cols = [rows[r][c] for c in range(3) for r in range(3)]
    return " ".join("%.9g" % v for v in cols + list(t))


def apply(transform, p):
    rows, t = orca_reload.parse_transform(transform)
    return tuple(sum(rows[r][k] * p[k] for k in range(3)) + t[r] for r in range(3))


# ---------------------------------------------------------------- project builder

def imported(stl_mesh):
    """What Orca stores after importing an STL: mesh centred, offset = STL centre."""
    verts, tris = stl_mesh
    lo = [min(v[k] for v in verts) for k in range(3)]
    hi = [max(v[k] for v in verts) for k in range(3)]
    c = tuple((a + b) / 2 for a, b in zip(lo, hi))
    return ([tuple(v[k] - c[k] for k in range(3)) for v in verts], tris), c


def on_bed(rows, plate_xy, stored):
    """Instance transform with the given rotation that sits the stored mesh on the bed."""
    z = min(sum(rows[2][k] * v[k] for k in range(3)) for v in stored[0])
    return transform_str(rows, (plate_xy[0], plate_xy[1], -z))


def make_project(path, objects):
    """objects: dicts with name, source, stl (mesh in STL coordinates), instances
    (transform strings), plate, and optional settings / paint / auto_drop."""
    model_objs, items, settings, plates, files = [], [], [], {}, {}
    rels = []
    next_id = 1
    for obj in objects:
        stored, offset = imported(obj["stl"])
        sub_id, obj_id = next_id, next_id + 1
        next_id += 2
        sub_path = "3D/Objects/%s_%d.model" % (obj["name"], obj_id)
        vtxt = "".join('     <vertex x="%.9g" y="%.9g" z="%.9g"/>\n' % v for v in stored[0])
        paint = ' paint_supports="4"' if obj.get("paint") else ""
        ttxt = "".join('     <triangle v1="%d" v2="%d" v3="%d"%s/>\n' % (t + (paint,)) for t in stored[1])
        files[sub_path] = (HEADER + ' <resources>\n  <object id="%d" p:UUID="0000-%d" type="model">\n'
                           '   <mesh>\n    <vertices>\n%s    </vertices>\n    <triangles>\n%s    </triangles>\n'
                           '   </mesh>\n  </object>\n </resources>\n <build/>\n</model>\n') % (sub_id, sub_id, vtxt, ttxt)
        rels.append(' <Relationship Target="/%s" Id="rel-%d" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>\n'
                    % (sub_path, len(rels) + 1))
        model_objs.append('  <object id="%d" p:UUID="%d-61cb" type="model">\n   <components>\n'
                          '    <component p:path="/%s" objectid="%d" p:UUID="%d-b206" transform="1 0 0 0 1 0 0 0 1 0 0 0"/>\n'
                          '   </components>\n  </object>\n' % (obj_id, obj_id, sub_path, sub_id, obj_id))
        for k, tr in enumerate(obj["instances"]):
            items.append('  <item objectid="%d" p:UUID="%d-%d" transform="%s" printable="1" auto_drop="%s"/>\n'
                         % (obj_id, obj_id, k, tr, obj.get("auto_drop", "1")))
            plates.setdefault(obj["plate"], []).append((obj_id, k))
        extra = "".join('    <metadata key="%s" value="%s"/>\n' % kv for kv in obj.get("settings", {}).items())
        settings.append(
            '  <object id="%d">\n    <metadata key="name" value="%s"/>\n%s    <metadata key="extruder" value="1"/>\n'
            '    <part id="%d" subtype="normal_part">\n      <metadata key="name" value="%s"/>\n'
            '      <metadata key="matrix" value="1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1"/>\n'
            '      <metadata key="source_file" value="%s"/>\n'
            '      <metadata key="source_object_id" value="0"/>\n      <metadata key="source_volume_id" value="0"/>\n'
            '      <metadata key="source_offset_x" value="%r"/>\n      <metadata key="source_offset_y" value="%r"/>\n'
            '      <metadata key="source_offset_z" value="%r"/>\n'
            '      <mesh_stat edges_fixed="0" degenerate_facets="0" facets_removed="0" facets_reversed="0" backwards_edges="0"/>\n'
            '    </part>\n  </object>\n'
            % ((obj_id, obj["name"], extra, sub_id, obj["name"], obj["source"]) + offset))
    plate_txt = ""
    for plate_id, insts in sorted(plates.items()):
        plate_txt += '  <plate>\n    <metadata key="plater_id" value="%d"/>\n    <metadata key="plater_name" value=""/>\n' % plate_id
        for obj_id, k in insts:
            plate_txt += ('    <model_instance>\n      <metadata key="object_id" value="%d"/>\n'
                          '      <metadata key="instance_id" value="%d"/>\n    </model_instance>\n' % (obj_id, k))
        plate_txt += '  </plate>\n'
    files["3D/3dmodel.model"] = (HEADER + ' <metadata name="Title">test</metadata>\n <resources>\n' + "".join(model_objs) +
                                 ' </resources>\n <build p:UUID="build">\n' + "".join(items) + ' </build>\n</model>\n')
    files["3D/_rels/3dmodel.model.rels"] = ('<?xml version="1.0" encoding="UTF-8"?>\n<Relationships xmlns='
                                            '"http://schemas.openxmlformats.org/package/2006/relationships">\n'
                                            + "".join(rels) + '</Relationships>\n')
    files["Metadata/model_settings.config"] = ('<?xml version="1.0" encoding="UTF-8"?>\n<config>\n' + "".join(settings)
                                               + plate_txt + '</config>\n')
    files["Metadata/project_settings.config"] = '{"layer_height": "0.2"}\n'
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("[Content_Types].xml", '<?xml version="1.0" encoding="UTF-8"?>\n<Types/>\n', zipfile.ZIP_DEFLATED)
        z.writestr("Metadata/plate_1.png", b"\x89PNG fake thumbnail", zipfile.ZIP_STORED)
        for name in ("3D/3dmodel.model", "3D/_rels/3dmodel.model.rels"):
            z.writestr(name, files.pop(name), zipfile.ZIP_DEFLATED)
        for name, data in files.items():
            z.writestr(name, data, zipfile.ZIP_DEFLATED)


# ---------------------------------------------------------------- reading results

def items_of(zip_path):
    text = zipfile.ZipFile(zip_path).read("3D/3dmodel.model").decode()
    return re.findall(r'<item objectid="(\d+)"[^>]*transform="([^"]*)"', text)


def world_points(zip_path, obj_index=0, instance=0):
    """World-space vertices of the obj_index-th object's mesh for one instance."""
    z = zipfile.ZipFile(zip_path)
    subs = sorted(n for n in z.namelist() if n.startswith("3D/Objects/"))
    obj_items = {}
    for oid, tr in items_of(zip_path):
        obj_items.setdefault(oid, []).append(tr)
    oid = sorted(obj_items, key=int)[obj_index]
    sub = [s for s in subs if s.endswith("_%s.model" % oid)][0]
    text = z.read(sub).decode()
    verts = [tuple(map(float, v)) for v in re.findall(r'<vertex x="([^"]+)" y="([^"]+)" z="([^"]+)"', text)]
    return [apply(obj_items[oid][instance], v) for v in verts], verts


def center(points):
    return tuple((min(p[k] for p in points) + max(p[k] for p in points)) / 2 for k in range(3))


def sha(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


class ProjectCase(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.dir)

    def path(self, *parts):
        return os.path.join(self.dir, *parts)

    def run_tool(self, *args):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = orca_reload.main(list(args))
        return code, out.getvalue() + err.getvalue()

    def project(self, stl_mesh, rows=rot_x(90), plate_xy=(128, 128), name="button", **extra):
        """One-object project whose part was imported from parts/<name>.stl."""
        stl = self.path("parts", name + ".stl")
        write_stl(stl, stl_mesh)
        stored, _ = imported(stl_mesh)
        obj = dict(name=name, source=stl, stl=stl_mesh, plate=1,
                   instances=[on_bed(rows, plate_xy, stored)], **extra)
        make_project(self.path("proj.3mf"), [obj])
        return self.path("proj.3mf"), stl


class ReloadTest(ProjectCase):

    def test_unchanged_stl_writes_nothing(self):
        proj, _ = self.project(box((10, 20, 5), center=(30, -40, 2.5)))
        code, out = self.run_tool(proj)
        self.assertEqual(code, 0, out)
        self.assertIn("1 unchanged", out)
        self.assertFalse(os.path.exists(self.path("proj_reloaded.3mf")))

    def test_changed_stl_keeps_orientation_plate_and_settings(self):
        proj, stl = self.project(box((10, 20, 5), center=(30, -40, 2.5)), rows=matmul(rot_z(30), rot_x(90)),
                                 plate_xy=(435, 128), settings={"wall_loops": "4"})
        before = sha(proj)
        old_world, _ = world_points(proj)
        old_item = items_of(proj)[0][1]
        # Bigger in every direction and exported around a different origin.
        write_stl(stl, box((14, 26, 9), center=(-7, 12, 40)))
        code, out = self.run_tool(proj)
        self.assertEqual(code, 0, out)
        self.assertIn("updated", out)
        out_path = self.path("proj_reloaded.3mf")
        self.assertEqual(sha(proj), before, "original project must not change")

        new_world, new_stored = world_points(out_path)
        new_item = items_of(out_path)[0][1]
        old_rows, old_t = orca_reload.parse_transform(old_item)
        new_rows, new_t = orca_reload.parse_transform(new_item)
        self.assertEqual(old_rows, new_rows, "orientation must not change")
        self.assertEqual(old_t[:2], new_t[:2], "plate position must not change")
        self.assertAlmostEqual(min(p[2] for p in new_world), 0, places=4)
        # Same centre as before (Orca's reload keeps the bounding-box centre).
        for a, b in zip(center(old_world)[:2], center(new_world)[:2]):
            self.assertAlmostEqual(a, b, places=4)
        # New size, in the part's own frame.
        sizes = [max(v[k] for v in new_stored) - min(v[k] for v in new_stored) for k in range(3)]
        for a, b in zip(sizes, (14, 26, 9)):
            self.assertAlmostEqual(a, b, places=4)

        old_zip, new_zip = zipfile.ZipFile(proj), zipfile.ZipFile(out_path)
        self.assertEqual(old_zip.namelist(), new_zip.namelist())
        for name in ("Metadata/plate_1.png", "Metadata/project_settings.config", "[Content_Types].xml",
                     "3D/_rels/3dmodel.model.rels"):
            self.assertEqual(old_zip.read(name), new_zip.read(name), name)
        old_cfg = old_zip.read("Metadata/model_settings.config").decode()
        new_cfg = new_zip.read("Metadata/model_settings.config").decode()
        self.assertIn('<metadata key="wall_loops" value="4"/>', new_cfg)
        self.assertEqual(old_cfg[old_cfg.find("<plate>"):], new_cfg[new_cfg.find("<plate>"):])
        self.assertIn('key="source_offset_z" value="40.0"', new_cfg)

        # Running again on the result finds nothing left to do.
        code, out = self.run_tool(out_path, "-o", self.path("again.3mf"))
        self.assertIn("1 unchanged", out)

    def test_all_instances_move_together(self):
        stl_mesh = box((10, 10, 4))
        stl = self.path("parts", "cap.stl")
        write_stl(stl, stl_mesh)
        stored, _ = imported(stl_mesh)
        rows = rot_x(0)
        make_project(self.path("proj.3mf"), [dict(
            name="cap", source=stl, stl=stl_mesh, plate=1,
            instances=[on_bed(rows, (50, 50), stored), on_bed(rows, (80, 50), stored)])])
        write_stl(stl, box((10, 10, 10)))
        code, out = self.run_tool(self.path("proj.3mf"))
        self.assertEqual(code, 0, out)
        items = items_of(self.path("proj_reloaded.3mf"))
        self.assertEqual([t.split()[9:11] for _, t in items], [["50", "50"], ["80", "50"]])
        for _, tr in items:
            self.assertAlmostEqual(float(tr.split()[11]), 5.0, places=5)

    def test_sunk_object_stays_where_it_is(self):
        stl_mesh = box((10, 10, 10))
        stl = self.path("parts", "sunk.stl")
        write_stl(stl, stl_mesh)
        make_project(self.path("proj.3mf"), [dict(
            name="sunk", source=stl, stl=stl_mesh, plate=1,
            instances=[transform_str(rot_x(0), (50, 50, 3))])])  # 2 mm below the bed
        write_stl(stl, box((10, 10, 20)))
        self.run_tool(self.path("proj.3mf"))
        self.assertEqual(items_of(self.path("proj_reloaded.3mf"))[0][1].split()[11], "3")

    def test_missing_source_is_reported_and_others_still_update(self):
        a, b = box((5, 5, 5)), box((6, 6, 6))
        stl_a, stl_b = self.path("parts", "a.stl"), self.path("parts", "b.stl")
        write_stl(stl_a, a)
        make_project(self.path("proj.3mf"), [
            dict(name="a", source=stl_a, stl=a, plate=1, instances=[on_bed(rot_x(0), (40, 40), imported(a)[0])]),
            dict(name="b", source=stl_b, stl=b, plate=2, instances=[on_bed(rot_x(0), (350, 40), imported(b)[0])])])
        write_stl(stl_a, box((5, 5, 8)))
        code, out = self.run_tool(self.path("proj.3mf"))
        self.assertEqual(code, orca_reload.EXIT_INCOMPLETE)
        self.assertIn("1 updated, 1 missing", out)
        self.assertTrue(os.path.exists(self.path("proj_reloaded.3mf")))

    def test_finds_moved_sources_from_windows_paths(self):
        mesh = box((5, 5, 5))
        stored = imported(mesh)[0]
        make_project(self.path("proj.3mf"), [
            dict(name="btn", source="D:\\Grip\\orca_slicer\\GripV\\parts\\btn.stl", stl=mesh, plate=1,
                 instances=[on_bed(rot_x(0), (40, 40), stored)]),
            dict(name="pin", source="D:\\old\\pin.stl", stl=mesh, plate=1,
                 instances=[on_bed(rot_x(0), (80, 40), stored)])])
        write_stl(self.path("parts", "btn.stl"), box((5, 5, 7)))  # next to the project, by trailing path
        write_stl(self.path("lib", "a", "pin.stl"), box((5, 5, 9)))  # found by name under --search
        code, out = self.run_tool(self.path("proj.3mf"), "--search", self.path("lib"))
        self.assertEqual(code, 0, out)
        self.assertIn("2 updated", out)
        write_stl(self.path("lib", "b", "pin.stl"), box((5, 5, 9)))
        code, out = self.run_tool(self.path("proj.3mf"), "--search", self.path("lib"), "--dry-run")
        self.assertIn("ambiguous", out)

    def test_ascii_stl(self):
        proj, stl = self.project(box((10, 10, 10)))
        write_stl(stl, box((10, 10, 12)), ascii=True)
        code, out = self.run_tool(proj)
        self.assertEqual(code, 0, out)
        self.assertIn("12 -> 12 triangles", out)

    def test_origin_anchor_follows_stl_origin(self):
        proj, stl = self.project(box((10, 10, 10), center=(0, 0, 5)), rows=rot_z(90), plate_xy=(100, 100))
        write_stl(stl, box((10, 10, 10), center=(3, 0, 5)))  # same shape, exported 3 mm along +X
        code, out = self.run_tool(proj, "--dry-run")
        self.assertIn("1 unchanged", out)  # Orca's behaviour: only the shape matters
        code, out = self.run_tool(proj, "--anchor", "origin")
        self.assertIn("centre moved 3.00 mm", out)
        new_world, _ = world_points(self.path("proj_reloaded.3mf"))
        c = center(new_world)
        self.assertAlmostEqual(c[0], 100, places=4)  # +X in the STL is +Y on the bed after rot_z(90)
        self.assertAlmostEqual(c[1], 103, places=4)

    def test_painted_triangles_are_noted(self):
        proj, stl = self.project(box((10, 10, 10)), paint=True)
        write_stl(stl, box((10, 10, 11)))
        code, out = self.run_tool(proj)
        self.assertIn("painting removed", out)
        text = zipfile.ZipFile(self.path("proj_reloaded.3mf")).read("3D/Objects/button_2.model").decode()
        self.assertNotIn("paint_supports", text)

    def test_never_overwrites_the_original(self):
        proj, stl = self.project(box((10, 10, 10)))
        before = sha(proj)
        write_stl(stl, box((10, 10, 11)))
        code, out = self.run_tool(proj, "-o", proj)
        self.assertEqual(code, orca_reload.EXIT_ERROR)
        self.assertIn("refusing to overwrite", out)
        self.assertEqual(sha(proj), before)

    def test_folder_input_skips_previous_outputs(self):
        proj, stl = self.project(box((10, 10, 10)))
        write_stl(stl, box((10, 10, 11)))
        self.run_tool(self.dir)
        code, out = self.run_tool(self.dir, "--dry-run")
        self.assertNotIn("proj_reloaded.3mf ->", out)
        self.assertEqual(out.count("proj.3mf"), 1)

    def test_stl_reader_merges_vertices_and_drops_degenerate_triangles(self):
        verts, tris = box((2, 2, 2))
        write_stl(self.path("m.stl"), (verts, tris + [(0, 0, 1)]))
        mesh, dropped = orca_reload.read_stl(self.path("m.stl"))
        self.assertEqual((mesh.vertex_count, mesh.triangle_count, dropped), (8, 12, 1))
        # -0.0 and 0.0 are one vertex
        write_stl(self.path("z.stl"), ([(0.0, 0, 0), (1, 0, 0), (0, 1, 0), (-0.0, 0, 0), (0, 0, 1)],
                                       [(0, 1, 2), (3, 2, 4)]))
        mesh, _ = orca_reload.read_stl(self.path("z.stl"))
        self.assertEqual(mesh.vertex_count, 4)


class SeamReloadTest(ProjectCase):
    """The seams hook of reload_project, with the painter the Blender extension uses."""

    BOX = box((10, 10, 10), center=(30, -40, 5))  # top face at z = 10
    LINE = [((26, -40, 10), (34, -40, 10))]

    def reload(self, proj, out=None, lines=None, replace=False):
        painter = seams.SeamPainter([seams.SeamLine("seam", lines or self.LINE)], width=0.6, snap=1.0)

        def paint(part, path, mesh):
            result = painter.paint(mesh.verts, mesh.tris, label=path)
            return None if result is None else (result.strings, result.note())

        out = out or self.path("proj_reloaded.3mf")
        finder = orca_reload.SourceFinder([])
        return orca_reload.process(proj, finder, out, seams=paint, replace=replace)

    def triangles(self, zip_path):
        text = zipfile.ZipFile(zip_path).read("3D/Objects/button_2.model").decode()
        return re.findall(r"<triangle ([^>]*)/>", text)

    def test_seams_on_an_unchanged_part_keep_the_mesh_and_other_painting(self):
        proj, _ = self.project(self.BOX, paint=True)
        before = zipfile.ZipFile(proj).read("3D/Objects/button_2.model").decode()
        lines, code = self.reload(proj)
        self.assertEqual(code, 0)
        self.assertIn("seams", lines[1])
        self.assertIn("seam on 2 triangles from seam 100%", lines[1] + lines[2])
        tris = self.triangles(self.path("proj_reloaded.3mf"))
        self.assertEqual(len(tris), 12)
        self.assertTrue(all('paint_supports="4"' in t for t in tris))
        self.assertEqual(sum('paint_seam="' in t for t in tris), 2)
        after = zipfile.ZipFile(self.path("proj_reloaded.3mf")).read("3D/Objects/button_2.model").decode()
        self.assertEqual(re.findall(r"<vertex [^>]*>", after), re.findall(r"<vertex [^>]*>", before))
        # Same seams again: nothing to write.
        lines, _ = self.reload(self.path("proj_reloaded.3mf"), out=self.path("again.3mf"))
        self.assertIn("1 unchanged", "\n".join(lines))
        self.assertFalse(os.path.exists(self.path("again.3mf")))

    def test_seams_are_painted_again_after_a_shape_change(self):
        proj, stl = self.project(self.BOX, paint=True)
        write_stl(stl, box((10, 10, 12), center=(30, -40, 6)))  # 2 mm taller: top at z = 12
        lines, code = self.reload(proj, lines=[((26, -40, 12), (34, -40, 12))])
        self.assertIn("updated", lines[1])
        self.assertIn("other painting removed", "\n".join(lines))
        tris = self.triangles(self.path("proj_reloaded.3mf"))
        painted = [t for t in tris if "paint_seam" in t]
        self.assertEqual(len(painted), 2)
        self.assertFalse(any("paint_supports" in t for t in tris))
        # The painted triangles are the top face of the new STL.
        new, _ = orca_reload.read_stl(stl)
        for t in painted:
            v = [int(x) for x in re.findall(r'v\d="(\d+)"', t)]
            self.assertTrue(all(abs(new.verts[3 * i + 2] - 12) < 1e-6 for i in v))

    def test_seam_strings_decode_to_a_strip_on_the_line(self):
        proj, stl = self.project(self.BOX)
        self.reload(proj)
        mesh, _ = orca_reload.read_stl(stl)
        enforced = 0
        for i, t in enumerate(self.triangles(self.path("proj_reloaded.3mf"))):
            m = re.search(r'paint_seam="([0-9A-F]+)"', t)
            if not m:
                continue
            corners = [tuple(mesh.verts[3 * mesh.tris[3 * i + k] + j] for j in range(3)) for k in range(3)]
            for state, tri in seams.leaves(seams.decode(m.group(1)), *corners):
                if state == seams.ENFORCER:
                    enforced += 1
                    cen = [sum(p[k] for p in tri) / 3 for k in range(3)]
                    self.assertLess(abs(cen[1] + 40), 0.6)
        self.assertGreater(enforced, 0)

    def test_line_elsewhere_leaves_the_part_alone(self):
        proj, _ = self.project(self.BOX, paint=True)
        lines, _ = self.reload(proj, lines=[((100, 0, 0), (110, 0, 0))])
        self.assertIn("1 unchanged", "\n".join(lines))

    def test_replace_writes_over_the_original(self):
        proj, _ = self.project(self.BOX)
        lines, code = self.reload(proj, out=proj, replace=True)
        self.assertEqual(code, 0)
        self.assertIn("proj.3mf -> " + proj, lines[0])
        self.assertEqual(sum("paint_seam" in t for t in self.triangles(proj)), 2)
        self.assertEqual(sorted(os.listdir(self.dir)), ["parts", "proj.3mf"])  # no copy, no temporary file left


if __name__ == "__main__":
    unittest.main()
