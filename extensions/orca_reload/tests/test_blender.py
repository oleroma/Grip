"""Tests for the Orca Reload extension in Blender. Run with a Python that has the bpy module (Blender 5.2 or newer):

    python -I extensions/orca_reload/tests/test_blender.py

Grip.blend is not opened. Each test builds a box part, writes its STL and an Orca project for it (with the
project builder of tools/orca_reload/test_orca_reload.py), adds seam guides, and presses Update Orca projects.
"""
import atexit
import os
import re
import shutil
import sys
import tempfile
import unittest
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
EXT_DIR = os.path.dirname(HERE)
EXTENSIONS = os.path.dirname(EXT_DIR)
REPO = os.path.dirname(EXTENSIONS)

# Keep Blender's user folders out of the real ones, and no __pycache__ in the repository
_USER = tempfile.mkdtemp(prefix="orca_reload_test_")
atexit.register(shutil.rmtree, _USER, ignore_errors=True)
os.environ["BLENDER_USER_RESOURCES"] = _USER
sys.dont_write_bytecode = True

import bpy  # noqa: E402
import addon_utils  # noqa: E402  (comes with bpy)

sys.path.insert(0, os.path.join(REPO, "tools", "orca_reload"))
import test_orca_reload as fixtures  # noqa: E402

REPO_MODULE = "orca_test"
ADDON = f"bl_ext.{REPO_MODULE}.orca_reload"


def enable_addon():
    """Adds the extensions folder as a local repository and enables the add-on from it."""
    bpy.context.preferences.use_preferences_save = False
    repos = bpy.context.preferences.extensions.repos
    if not any(r.module == REPO_MODULE for r in repos):
        repos.new(name=REPO_MODULE, module=REPO_MODULE, custom_directory=EXTENSIONS, source='USER')
    if addon_utils.enable(ADDON, default_set=True, handle_error=None) is None:
        raise RuntimeError(f"could not enable {ADDON}")


def mesh_object(name, verts, edges=(), faces=(), location=(0, 0, 0)):
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, list(edges), list(faces))
    obj = bpy.data.objects.new(name, me)
    obj.location = location
    bpy.context.scene.collection.objects.link(obj)
    return obj


def curve_object(name, points, bezier=True):
    cu = bpy.data.curves.new(name, 'CURVE')
    cu.dimensions = '3D'
    spline = cu.splines.new('BEZIER' if bezier else 'POLY')
    if bezier:
        spline.bezier_points.add(len(points) - 1)
        for bp, p in zip(spline.bezier_points, points):
            bp.co = p
            bp.handle_left_type = bp.handle_right_type = 'VECTOR'
    else:
        spline.points.add(len(points) - 1)
        for sp, p in zip(spline.points, points):
            sp.co = (*p, 1.0)
    obj = bpy.data.objects.new(name, cu)
    bpy.context.scene.collection.objects.link(obj)
    return obj


class OrcaReloadBlenderTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        bpy.ops.wm.read_homefile(use_empty=True)
        enable_addon()

    def setUp(self):
        for obj in list(bpy.data.objects):
            bpy.data.objects.remove(obj)
        self.dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.dir)
        # The part: a 10 mm box with its top face at z = 10, exported to parts/box.stl like combi_export does
        # (world space).
        verts, tris = fixtures.box((10, 10, 10), center=(30, -40, 5))
        self.part = mesh_object("box", verts, faces=tris)
        self.stl = os.path.join(self.dir, "parts", "box.stl")
        fixtures.write_stl(self.stl, (verts, tris))
        stored, _ = fixtures.imported((verts, tris))
        self.project = os.path.join(self.dir, "proj.3mf")
        fixtures.make_project(self.project, [dict(
            name="box", source=self.stl, stl=(verts, tris), plate=1,
            instances=[fixtures.on_bed(fixtures.rot_x(0), (128, 128), stored)])])
        settings = bpy.context.scene.orca_reload
        settings.projects = self.dir
        settings.replace = False

    def update(self):
        result = bpy.ops.orca_reload.update_projects()
        self.assertEqual(result, {'FINISHED'})
        return bpy.data.texts["Orca reload report"].as_string()

    def painted_triangles(self, path=None):
        z = zipfile.ZipFile(path or os.path.join(self.dir, "proj_reloaded.3mf"))
        name = [n for n in z.namelist() if n.startswith("3D/Objects/")][0]
        tris = re.findall(r"<triangle ([^>]*)/>", z.read(name).decode())
        return [i for i, t in enumerate(tris) if "paint_seam" in t]

    def top_face(self):
        """Indices of the STL's triangles on the top face (z = 10)."""
        mesh, _ = fixtures.orca_reload.read_stl(self.stl)
        return [t for t in range(mesh.triangle_count)
                if all(abs(mesh.verts[3 * mesh.tris[3 * t + k] + 2] - 10) < 1e-6 for k in range(3))]

    def test_curve_seam_is_painted_on_the_part_it_lies_on(self):
        curve = curve_object("SeamTop", [(26, -40, 10), (30, -40, 10.2), (34, -40, 10)])
        curve.orca_seam = True
        report = self.update()
        self.assertIn("Seam lines: SeamTop", report)
        self.assertIn("seam on 2 triangles from SeamTop 100%", report)
        self.assertEqual(self.painted_triangles(), self.top_face())

    def test_settings_and_ticks_are_saved_in_the_blend_file(self):
        curve = curve_object("SeamTop", [(26, -40, 10), (34, -40, 10)], bezier=False)
        curve.orca_seam = True
        curve.orca_seam_only = "box"
        bpy.context.scene.orca_reload.seam_width = 0.8
        path = os.path.join(self.dir, "saved.blend")
        bpy.ops.wm.save_as_mainfile(filepath=path)
        bpy.ops.wm.open_mainfile(filepath=path)
        self.assertTrue(bpy.data.objects["SeamTop"].orca_seam)
        self.assertEqual(bpy.data.objects["SeamTop"].orca_seam_only, "box")
        self.assertAlmostEqual(bpy.context.scene.orca_reload.seam_width, 0.8, places=5)

    def test_marked_edges_and_edge_attribute(self):
        # An edges-only mesh on the front face (y = -45), hidden with the eye icon.
        guide = mesh_object("SeamFront", [(26, -45, 5), (34, -45, 5)], edges=[(0, 1)])
        guide.orca_seam = True
        guide.hide_set(True)
        # A mesh with faces: only its marked edge counts (a strip along the right face, x = 35).
        strip = mesh_object("SeamRight", [(35, -44, 2), (35, -36, 2), (35, -36, 2.5), (35, -44, 2.5)],
                            faces=[(0, 1, 2, 3)])
        strip.data.edges[0].use_seam = True
        strip.orca_seam = True
        report = self.update()
        self.assertNotIn("skipped:", report)
        self.assertIn("SeamFront 100%", report)
        self.assertIn("SeamRight 100%", report)
        self.assertTrue(guide.hide_get())
        mesh, _ = fixtures.orca_reload.read_stl(self.stl)

        def face_of(t):
            pts = [[mesh.verts[3 * mesh.tris[3 * t + k] + j] for j in range(3)] for k in range(3)]
            if all(abs(p[1] + 45) < 1e-6 for p in pts):
                return "front"
            if all(abs(p[0] - 35) < 1e-6 for p in pts):
                return "right"
            return "other"
        self.assertEqual(sorted(set(map(face_of, self.painted_triangles()))), ["front", "right"])

    def test_edge_attribute_from_geometry_nodes(self):
        strip = mesh_object("SeamGN", [(35, -44, 2), (35, -36, 2), (35, -36, 2.5), (35, -44, 2.5)],
                            faces=[(0, 1, 2, 3)])
        attr = strip.data.attributes.new("orca_seam", 'BOOLEAN', 'EDGE')
        attr.data[0].value = True
        strip.orca_seam = True
        self.assertIn("SeamGN 100%", self.update())

    def test_guide_without_marked_edges_is_reported(self):
        strip = mesh_object("Sheet", [(35, -44, 2), (35, -36, 2), (35, -36, 8)], faces=[(0, 1, 2)])
        strip.orca_seam = True
        report = self.update()
        self.assertIn("skipped: Sheet has faces but no edges marked as seam", report)

    def test_line_on_no_part_is_reported(self):
        curve = curve_object("Stray", [(100, 0, 0), (110, 0, 0)])
        curve.orca_seam = True
        report = self.update()
        self.assertIn("Seam lines on no part", report)
        self.assertIn("Stray", report)
        self.assertFalse(os.path.exists(os.path.join(self.dir, "proj_reloaded.3mf")))

    def test_only_filter_and_replace(self):
        curve = curve_object("SeamTop", [(26, -40, 10), (34, -40, 10)])
        curve.orca_seam = True
        curve.orca_seam_only = "other_part"
        self.assertIn("Seam lines on no part", self.update())
        curve.orca_seam_only = "parts/BOX"  # case does not matter, \ and / are the same
        bpy.context.scene.orca_reload.replace = True
        self.update()
        self.assertFalse(os.path.exists(os.path.join(self.dir, "proj_reloaded.3mf")))
        self.assertEqual(self.painted_triangles(self.project), self.top_face())

    def test_panels_are_registered(self):
        for name in ("VIEW3D_PT_orca_reload", "VIEW3D_PT_orca_reload_seams"):
            self.assertTrue(hasattr(bpy.types, name), name)


if __name__ == "__main__":
    unittest.main()
