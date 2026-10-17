"""Tests for the Orca tab in Blender. Run under Blender itself, since the bpy module is only available inside
Blender (Blender 5.2 or newer):

    blender -b -P orca_3mf/tests/test_blender.py

Grip.blend is not opened. Each test builds a box part and writes its STL like Combi Export does (world space), sets
up a project with the tab's operators and properties, and presses Build or Import.
"""
import atexit
import math
import os
import re
import shutil
import sys
import tempfile
import unittest
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
EXT_DIR = os.path.dirname(HERE)
ROOT = os.path.dirname(EXT_DIR)

# Keep Blender's user folders out of the real ones, and no __pycache__ in the repository
_USER = tempfile.mkdtemp(prefix="orca_reload_test_")
atexit.register(shutil.rmtree, _USER, ignore_errors=True)
os.environ["BLENDER_USER_RESOURCES"] = _USER
sys.dont_write_bytecode = True

import bpy  # noqa: E402
import addon_utils  # noqa: E402  (comes with bpy)

sys.path.insert(0, HERE)
import test_reload as fixtures  # noqa: E402
from test_build import make_template  # noqa: E402

REPO_MODULE = "orca_test"
ADDON = f"bl_ext.{REPO_MODULE}.orca_3mf"


def enable_addon():
    """Stages the add-on at the folder name Blender expects and enables it from there.

    Blender finds an extension at <repo>/<id>/. Stage a clean copy there (without __pycache__) so the test
    does not depend on how the checkout is registered in Blender.
    """
    bpy.context.preferences.use_preferences_save = False
    repos = bpy.context.preferences.extensions.repos
    if not any(r.module == REPO_MODULE for r in repos):
        repo_dir = tempfile.mkdtemp(prefix="orca_3mf_repo_")
        atexit.register(shutil.rmtree, repo_dir, ignore_errors=True)
        shutil.copytree(EXT_DIR, os.path.join(repo_dir, "orca_3mf"),
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        repos.new(name=REPO_MODULE, module=REPO_MODULE, custom_directory=repo_dir, source='USER')
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


def list_action(level, action):
    assert bpy.ops.orca_reload.list_action(level=level, action=action) == {'FINISHED'}


class OrcaTabTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        bpy.ops.wm.read_homefile(use_empty=True)
        enable_addon()

    def setUp(self):
        for obj in list(bpy.data.objects):
            bpy.data.objects.remove(obj)
        self.dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.dir)
        # The part: a 10 mm box with its top face at z = 10, exported to stl/GripV/parts/box.stl
        verts, tris = fixtures.box((10, 10, 10), center=(30, -40, 5))
        self.part = mesh_object("box", verts, faces=tris)
        self.stl = os.path.join(self.dir, "stl", "GripV", "parts", "box.stl")
        fixtures.write_stl(self.stl, (verts, tris))
        self.template = os.path.join(self.dir, "printer.3mf")
        make_template(self.template)
        settings = bpy.context.scene.orca_reload
        settings.projects.clear()
        settings.stl_root = os.path.join(self.dir, "stl")
        settings.project_root = os.path.join(self.dir, "orca")
        bpy.context.window_manager.orca_reload_log.clear()

    def add_project(self, name="GripV_parts", plates=1):
        settings = bpy.context.scene.orca_reload
        list_action('PROJECT', 'ADD')
        project = settings.projects[settings.project_index]
        project.name = name
        project.folder = "GripV"
        project.stl_folder = "GripV"
        project.template = self.template
        for _ in range(plates - 1):
            list_action('PLATE', 'ADD')
        return project

    def add_part(self, path="parts/box.stl", **values):
        list_action('PART', 'ADD')  # without the file browser: an empty part
        project = bpy.context.scene.orca_reload.projects[bpy.context.scene.orca_reload.project_index]
        plate = project.plates[project.plate_index]
        part = plate.parts[plate.part_index]
        part.path = path
        part.name = os.path.basename(path)
        for key, value in values.items():
            setattr(part, key, value)
        return part

    def build(self, index=0):
        self.assertEqual(bpy.ops.orca_reload.build(index=index), {'FINISHED'})
        return bpy.data.texts["Orca build report"].as_string()

    def out(self):
        return os.path.join(self.dir, "orca", "GripV", "GripV_parts.3mf")

    def painted_triangles(self):
        with zipfile.ZipFile(self.out()) as z:
            name = [n for n in z.namelist() if n.startswith("3D/Objects/")][0]
            tris = re.findall(r"<triangle ([^>]*)/>", z.read(name).decode())
        return [i for i, t in enumerate(tris) if "paint_seam" in t]

    def top_face(self):
        """Indices of the STL's triangles on the top face (z = 10)."""
        mesh, _ = fixtures.orca_reload.read_stl(self.stl)
        return [t for t in range(mesh.triangle_count)
                if all(abs(mesh.verts[3 * mesh.tris[3 * t + k] + 2] - 10) < 1e-6 for k in range(3))]

    def test_build_writes_the_project_with_its_seam(self):
        self.add_project()
        seam = curve_object("SeamTop", [(26, -40, 10), (30, -40, 10.2), (34, -40, 10)])
        self.add_part(seam=seam, copies=3)
        report = self.build()
        self.assertIn("(new)", report)
        self.assertIn("seam on 2 triangles from SeamTop 100%", report)
        self.assertEqual(self.painted_triangles(), self.top_face())
        with zipfile.ZipFile(self.out()) as z:
            self.assertEqual(z.read("3D/3dmodel.model").decode().count("<item "), 3)
        log = [item.text for item in bpy.context.window_manager.orca_reload_log]
        self.assertTrue(log and log[0].endswith("(new)"))

    def test_build_all_skips_unticked_and_reports_problems(self):
        self.add_project()
        self.add_part()
        other = self.add_project("other")
        other.template = ""  # no printer settings: not written
        self.add_part()
        third = self.add_project("third")
        third.use = False
        self.assertEqual(bpy.ops.orca_reload.build(), {'FINISHED'})
        report = bpy.data.texts["Orca build report"].as_string()
        self.assertTrue(os.path.isfile(self.out()))
        self.assertIn("no printer settings", report)
        self.assertNotIn("third", report)
        self.assertFalse(os.path.exists(os.path.join(self.dir, "orca", "GripV", "other.3mf")))

    def test_marked_edges_hidden_guide_and_edge_attribute(self):
        self.add_project()
        # An edges-only mesh on the front face (y = -45), hidden with the eye icon
        guide = mesh_object("SeamFront", [(26, -45, 5), (34, -45, 5)], edges=[(0, 1)])
        guide.hide_set(True)
        self.add_part(seam=guide)
        # A mesh with faces: only its marked edge counts (a strip along the right face, x = 35)
        strip = mesh_object("SeamRight", [(35, -44, 2), (35, -36, 2), (35, -36, 2.5), (35, -44, 2.5)],
                            faces=[(0, 1, 2, 3)])
        strip.data.edges[0].use_seam = True
        self.add_part(seam=strip)
        # Geometry Nodes style: a boolean edge attribute
        gn = mesh_object("SeamGN", [(35, -44, 2), (35, -36, 2), (35, -36, 2.5), (35, -44, 2.5)],
                         faces=[(0, 1, 2, 3)])
        gn.data.attributes.new("orca_seam", 'BOOLEAN', 'EDGE').data[0].value = True
        self.add_part(seam=gn)
        report = self.build()
        for name in ("SeamFront", "SeamRight", "SeamGN"):
            self.assertIn("from %s 100%%" % name, report)
        self.assertTrue(guide.hide_get())

    def test_seam_problems_stop_the_build(self):
        self.add_project()
        sheet = mesh_object("Sheet", [(35, -44, 2), (35, -36, 2), (35, -36, 8)], faces=[(0, 1, 2)])
        self.add_part(seam=sheet)
        report = self.build()
        self.assertIn("seam Sheet has faces but no edges marked as seam", report)
        self.assertFalse(os.path.exists(self.out()))
        # A line away from the part is written, with a warning
        sheet.data.edges[0].use_seam = True
        stray = curve_object("Stray", [(100, 0, 0), (110, 0, 0)])
        bpy.context.scene.orca_reload.projects[0].plates[0].parts[0].seam = stray
        report = self.build()
        self.assertIn("seam line Stray is not on this part", report)
        self.assertTrue(os.path.exists(self.out()))

    def test_definition_is_saved_in_the_blend_file(self):
        project = self.add_project(plates=2)
        project.plates[1].gap = 8.5
        seam = curve_object("SeamTop", [(26, -40, 10), (34, -40, 10)], bezier=False)
        self.add_part(seam=seam, up=(0, -1, 0), angle=math.radians(45), copies=2)
        bpy.context.scene.orca_reload.seam_width = 0.8
        path = os.path.join(self.dir, "saved.blend")
        bpy.ops.wm.save_as_mainfile(filepath=path)
        bpy.ops.wm.open_mainfile(filepath=path)
        settings = bpy.context.scene.orca_reload
        project = settings.projects[0]
        self.assertEqual([p.name for p in project.plates], ["Plate 1", "Plate 2"])
        self.assertAlmostEqual(project.plates[1].gap, 8.5, places=5)
        part = project.plates[1].parts[0]
        self.assertEqual((part.path, part.copies, part.seam.name), ("parts/box.stl", 2, "SeamTop"))
        self.assertEqual(tuple(round(c, 6) for c in part.up), (0, -1, 0))
        self.assertAlmostEqual(part.angle, math.radians(45), places=5)
        self.assertAlmostEqual(settings.seam_width, 0.8, places=5)

    def test_import_makes_a_project_that_rebuilds_the_file(self):
        self.add_project(plates=2)
        self.add_part(up=(1, 0, 0), angle=math.radians(90), copies=2)
        self.build()
        settings = bpy.context.scene.orca_reload
        self.assertEqual(bpy.ops.orca_reload.import_project(filepath=self.out()), {'FINISHED'})
        imported = settings.projects[settings.project_index]
        self.assertEqual((imported.name, imported.folder, imported.stl_folder), ("GripV_parts.3mf", "GripV",
                                                                               "GripV/parts"))
        self.assertEqual(len(imported.plates), 2)
        part = imported.plates[1].parts[0]
        self.assertEqual((part.name, part.path, part.copies), ("box.stl", "box.stl", 2))
        self.assertEqual(tuple(round(c, 6) for c in part.up), (1, 0, 0))
        self.assertAlmostEqual(part.angle, math.radians(90), places=6)
        self.assertEqual(len(imported.plates[0].parts), 0)
        report = self.build(settings.project_index)
        self.assertIn("(rebuilt)", report)

    def test_stl_root_falls_back_to_combi_export(self):
        from bl_ext.orca_test.orca_3mf import props
        scene = bpy.context.scene
        scene.orca_reload.stl_root = ""
        added = not hasattr(bpy.types.Scene, "batch_stl_root_dir")
        if added:
            bpy.types.Scene.batch_stl_root_dir = bpy.props.StringProperty(subtype='DIR_PATH')
            self.addCleanup(delattr, bpy.types.Scene, "batch_stl_root_dir")
        scene.batch_stl_root_dir = os.path.join(self.dir, "stl")
        self.assertEqual(props.stl_root(scene), os.path.join(self.dir, "stl"))
        self.add_project()
        self.add_part()
        self.assertIn("(new)", self.build())

    def test_copy_paste_and_move(self):
        project = self.add_project()
        self.add_part(copies=4)
        list_action('PLATE', 'COPY')
        list_action('PLATE', 'PASTE')
        self.assertEqual(len(project.plates), 2)
        self.assertEqual(project.plates[1].parts[0].copies, 4)
        project.plates[1].name = "second"
        list_action('PLATE', 'UP')
        self.assertEqual([p.name for p in project.plates], ["second", "Plate 1"])
        list_action('PROJECT', 'ADD')  # a new project takes the settings file of the one before
        settings = bpy.context.scene.orca_reload
        self.assertEqual(settings.projects[1].template, self.template)
        self.assertEqual(len(settings.projects[1].plates), 1)

    def test_panels_draw(self):
        """Draws every panel and list row into a stand-in layout that checks each property, operator and icon."""
        from bl_ext.orca_test.orca_3mf import ui
        icons = set(bpy.types.UILayout.bl_rna.functions["label"].parameters["icon"].enum_items.keys())
        self.assertFalse(set(ui.ICONS.values()) - icons)
        test = self

        class Layout:
            def __init__(self):
                self.drawn = []

            def __getattr__(self, name):
                return lambda *args, **kwargs: self._call(name, args, kwargs)

            def __setattr__(self, name, value):
                object.__setattr__(self, name, value)

            def _call(self, name, args, kwargs):
                icon = kwargs.get("icon")
                if icon:
                    test.assertIn(icon, icons)
                if name == "prop":
                    test.assertIn(args[1], args[0].bl_rna.properties.keys(), args[1])
                elif name == "operator":
                    category, op = args[0].split(".")
                    test.assertTrue(hasattr(getattr(bpy.ops, category), op), args[0])
                    return type("Props", (), {})()
                elif name == "template_list":
                    test.assertIn(args[3], args[2].bl_rna.properties.keys())
                    test.assertIn(args[5], args[4].bl_rna.properties.keys())
                self.drawn.append(name)
                return Layout()

        self.add_project(plates=2)
        self.add_part(seam=curve_object("SeamTop", [(26, -40, 10), (34, -40, 10)]), copies=2)
        self.add_part(path="parts/missing.stl")
        self.build()
        bpy.context.window_manager.orca_reload_tips = True
        context = bpy.context
        for cls in ui.classes:
            if issubclass(cls, bpy.types.Panel):
                if hasattr(cls, "poll"):
                    self.assertTrue(cls.poll(context), cls.__name__)
                panel = type("P", (), {"layout": Layout()})()
                if hasattr(cls, "draw_header"):
                    cls.draw_header(panel, context)
                cls.draw(panel, context)
        project = context.scene.orca_reload.projects[0]
        rows = [(ui.ORCA_UL_projects, context.scene.orca_reload, project),
                (ui.ORCA_UL_plates, project, project.plates[1]),
                (ui.ORCA_UL_parts, project.plates[1], project.plates[1].parts[0]),
                (ui.ORCA_UL_parts, project.plates[1], project.plates[1].parts[1]),
                (ui.ORCA_UL_log, context.window_manager, context.window_manager.orca_reload_log[0])]
        for cls, data, item in rows:
            cls.draw_item(None, context, Layout(), data, item, 0, None, "", 0)

    def test_panels_and_operators_are_registered(self):
        for name in ("VIEW3D_PT_orca_reload", "VIEW3D_PT_orca_reload_info", "VIEW3D_PT_orca_reload_projects",
                     "VIEW3D_PT_orca_reload_plates", "VIEW3D_PT_orca_reload_parts"):
            self.assertTrue(hasattr(bpy.types, name), name)
        for op in ("list_action", "add_parts", "browse_part", "import_project", "build", "clear_log"):
            self.assertTrue(hasattr(bpy.ops.orca_reload, op), op)


if __name__ == "__main__":
    # Run through Blender (`blender -b -P test_blender.py`), whose Python exposes the full command line in
    # sys.argv; pass an explicit argv so unittest does not try to parse Blender's own flags.
    unittest.main(argv=[os.path.abspath(__file__)], verbosity=2)
