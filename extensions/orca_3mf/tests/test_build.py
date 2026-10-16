"""Tests for layout.py and build3mf.py (placing parts and writing Orca projects). Plain Python, no Blender:

    python -I orca_3mf/tests/test_build.py
"""
import json
import math
import os
import re
import shutil
import sys
import tempfile
import unittest
import zipfile

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
EXT_DIR = os.path.dirname(HERE)
sys.path.insert(0, EXT_DIR)
sys.path.insert(0, os.path.join(os.path.dirname(EXT_DIR), "tools", "orca_reload"))

import build3mf  # noqa: E402
import layout  # noqa: E402
import reload3mf  # noqa: E402
import test_orca_reload as fixtures  # noqa: E402

A1_AREA = ["0x0", "256x0", "256x256", "0x256"]


def make_template(path, area=A1_AREA, version="2.4.2", **extra):
    """The smallest Orca project that carries printer settings."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    cfg = {"printable_area": area, "printer_model": "Bambu Lab A1", "filament_colour": ["#FFFFFF"]}
    cfg.update(extra)
    with zipfile.ZipFile(path, "w") as z:
        z.writestr(reload3mf.ROOT_MODEL, fixtures.HEADER.replace(
            ' <metadata name="BambuStudio:3mfVersion">1</metadata>\n',
            ' <metadata name="Application">BambuStudio-02.06.00.51</metadata>\n'
            ' <metadata name="OrcaSlicer">%s</metadata>\n' % version) + " <resources/>\n <build/>\n</model>\n")
        z.writestr(build3mf.SETTINGS, json.dumps(cfg))
        z.writestr("Metadata/filament_settings_1.config", "{}")


def close(a, b, tol=1e-6):
    return all(abs(x - y) <= tol for x, y in zip(a, b))


class OrientationTest(unittest.TestCase):
    def test_up_axis_ends_on_top(self):
        for up in [(0, 0, 1), (0, 0, -1), (1, 0, 0), (0, -1, 0), (1, 2, 3), (-0.3, 0.1, -0.9)]:
            for angle in (0.0, 0.7, -2.5):
                r = layout.orientation(up, angle)
                n = math.sqrt(sum(c * c for c in up))
                self.assertTrue(close(layout.apply(r, [c / n for c in up]), (0, 0, 1)), (up, angle))
                # A proper rotation
                self.assertAlmostEqual(sum(r[0][k] * r[1][k] for k in range(3)), 0.0, places=9)
                det = (r[0][0] * (r[1][1] * r[2][2] - r[1][2] * r[2][1])
                       - r[0][1] * (r[1][0] * r[2][2] - r[1][2] * r[2][0])
                       + r[0][2] * (r[1][0] * r[2][1] - r[1][1] * r[2][0]))
                self.assertAlmostEqual(det, 1.0, places=9)
                back_up, back_angle = layout.orientation_from_matrix(r)
                self.assertTrue(close(back_up, [c / n for c in up]), (up, back_up))
                self.assertAlmostEqual(math.remainder(back_angle - angle, 2 * math.pi), 0.0, places=9)

    def test_turn_is_around_the_vertical(self):
        r = layout.orientation((0, 0, 1), math.radians(90))
        self.assertTrue(close(layout.apply(r, (1, 0, 0)), (0, 1, 0)))
        # Up = -Y lays the part on its back (+Y) face: its top (+Z) faces the back of the bed (+Y)
        r = layout.orientation((0, -1, 0), 0.0)
        self.assertTrue(close(layout.apply(r, (0, 0, 1)), (0, 1, 0)))
        # Upside down keeps X
        r = layout.orientation((0, 0, -1), 0.0)
        self.assertTrue(close(layout.apply(r, (1, 0, 0)), (1, 0, 0)))

    def test_zero_up_axis_is_refused(self):
        with self.assertRaises(ValueError):
            layout.orientation((0, 0, 0), 0.0)


class NestTest(unittest.TestCase):
    def check(self, sizes, bed, gap):
        positions, left_out = layout.nest(sizes, bed, gap)
        rects = [(p[0], p[1], s[0], s[1]) for p, s in zip(positions, sizes) if p is not None]
        for x, y, w, d in rects:
            self.assertGreaterEqual(x, gap / 2 - 1e-6)
            self.assertGreaterEqual(y, gap / 2 - 1e-6)
            self.assertLessEqual(x + w, bed[0] - gap / 2 + 1e-6)
            self.assertLessEqual(y + d, bed[1] - gap / 2 + 1e-6)
        for i, a in enumerate(rects):
            for b in rects[i + 1:]:
                apart = (a[0] + a[2] + gap <= b[0] + 1e-6 or b[0] + b[2] + gap <= a[0] + 1e-6
                         or a[1] + a[3] + gap <= b[1] + 1e-6 or b[1] + b[3] + gap <= a[1] + 1e-6)
                self.assertTrue(apart, (a, b))
        return positions, left_out

    def test_parts_keep_the_gap_and_stay_on_the_bed(self):
        sizes = [(40, 20), (30, 30), (5, 10)] * 6 + [(100, 60), (12, 80)]
        positions, left_out = self.check(sizes, (256, 256), 5)
        self.assertEqual(left_out, [])

    def test_group_is_centred_and_compact(self):
        positions, _ = self.check([(10, 10)] * 9, (256, 256), 2)
        xs = sorted({round(p[0], 6) for p in positions})
        ys = sorted({round(p[1], 6) for p in positions})
        self.assertEqual((len(xs), len(ys)), (3, 3))
        self.assertAlmostEqual((xs[0] + xs[-1] + 10) / 2, 128)
        self.assertAlmostEqual((ys[0] + ys[-1] + 10) / 2, 128)

    def test_what_does_not_fit_is_left_out(self):
        positions, left_out = self.check([(200, 200), (200, 200), (300, 10)], (256, 256), 5)
        self.assertEqual(sorted(left_out), [1, 2])
        self.assertIsNotNone(positions[0])

    def test_plate_grid_like_orca(self):
        self.assertEqual([layout.plate_columns(n) for n in (1, 2, 4, 5, 9, 10, 36)], [1, 2, 2, 3, 3, 4, 6])
        self.assertEqual(layout.plate_origin(0, 4, (256, 256)), (0, 0))
        self.assertTrue(close(layout.plate_origin(3, 4, (256, 256)), (307.2, -307.2)))
        self.assertTrue(close(layout.plate_origin(5, 9, (256, 256)), (614.4, -307.2)))


class BuildTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.dir)
        self.template = os.path.join(self.dir, "printer.3mf")
        make_template(self.template)
        self.stls = {}
        for name, size, center in (("a", (40, 20, 10), (100, 50, 5)), ("b", (30, 30, 60), (-20, 0, 30)),
                                   ("c", (10, 5, 2), (0, 0, 1))):
            self.stls[name] = self.write(name, size, center)
        self.out = os.path.join(self.dir, "out", "proj.3mf")

    def write(self, name, size, center, folder="stl"):
        path = os.path.join(self.dir, folder, name + ".stl")
        fixtures.write_stl(path, fixtures.box(size, center=center))
        return path

    def spec(self, plates=None, template=None):
        if plates is None:
            plates = [build3mf.PlateSpec("first", 5, [
                build3mf.PartSpec("a.stl", self.stls["a"], (0, -1, 0), math.radians(30), 2),
                build3mf.PartSpec("b.stl", self.stls["b"], (1, 0, 0))]),
                build3mf.PlateSpec("second", 3, [build3mf.PartSpec("c.stl", self.stls["c"], copies=4)])]
        return build3mf.ProjectSpec(self.out, plates, self.template if template is None else template)

    def build(self, spec=None):
        lines, written = build3mf.build(spec or self.spec())
        self.assertTrue(written, "\n".join(lines))
        return lines

    def placed(self):
        """[(object name, plate index from the geometry, world lo, world hi)] of every instance."""
        out = []
        project = reload3mf.Project(self.out)
        try:
            for obj in project.objects.values():
                mesh = project.old_mesh(obj.parts[0])
                for i in obj.items:
                    rows, t = reload3mf.parse_transform(project.items[i][1])
                    lo, hi = layout.footprint(mesh.verts, rows)
                    lo = tuple(a + b for a, b in zip(lo, t))
                    hi = tuple(a + b for a, b in zip(hi, t))
                    plate = None
                    for n in range(2):
                        ox, oy = layout.plate_origin(n, 2, (256, 256))
                        if ox <= lo[0] and hi[0] <= ox + 256 and oy <= lo[1] and hi[1] <= oy + 256:
                            plate = n
                    out.append((obj.name, plate, lo, hi))
        finally:
            project.close()
        return out

    def settings_xml(self):
        with zipfile.ZipFile(self.out) as z:
            return z.read(reload3mf.MODEL_SETTINGS).decode()

    def test_new_project_from_scratch(self):
        lines = self.build()
        self.assertIn("(new)", lines[0])
        placed = self.placed()
        self.assertEqual(sorted((n, p) for n, p, _, _ in placed),
                         [("a.stl", 0), ("a.stl", 0), ("b.stl", 0)] + [("c.stl", 1)] * 4)
        for _, _, lo, _ in placed:
            self.assertAlmostEqual(lo[2], 0.0, places=5)  # on the bed
        sizes = {n: tuple(round(h - l, 4) for h, l in zip(hi, lo)) for n, _, lo, hi in placed}
        self.assertEqual(sizes["b.stl"], (60, 30, 30))  # X up: its 60 mm height lies along the bed's X
        self.assertEqual(sizes["c.stl"], (10, 5, 2))
        with zipfile.ZipFile(self.out) as z:
            names = set(z.namelist())
            self.assertIn("Metadata/filament_settings_1.config", names)
            self.assertEqual(json.loads(z.read(build3mf.SETTINGS))["printable_area"], A1_AREA)
            root = z.read(reload3mf.ROOT_MODEL).decode()
        self.assertIn('<metadata name="OrcaSlicer">2.4.2</metadata>', root)
        self.assertIn('<metadata name="Application">BambuStudio-02.06.00.51</metadata>', root)
        text = self.settings_xml()
        self.assertEqual(re.findall(r'key="plater_name" value="([^"]*)"', text), ["first", "second"])
        self.assertEqual(text.count("<model_instance>"), 7)
        self.assertIn('value="%s"' % self.stls["a"], text)

    def test_imported_layout_reads_back_the_definition(self):
        self.build()
        plates, problems = build3mf.read_layout(self.out, reload3mf.SourceFinder([os.path.join(self.dir, "stl")]))
        self.assertEqual(problems, [])
        got = [(name, [(p.name, p.up, round(math.degrees(p.angle), 6), p.copies, p.stl) for p in parts])
               for name, parts in plates]
        self.assertEqual(got, [
            ("first", [("a.stl", (0.0, -1.0, 0.0), 30.0, 2, self.stls["a"]),
                       ("b.stl", (1.0, 0.0, 0.0), 0.0, 1, self.stls["b"])]),
            ("second", [("c.stl", (0.0, 0.0, 1.0), 0.0, 4, self.stls["c"])])])

    def test_same_file_name_in_several_folders_is_matched_by_shape(self):
        # Tight and loose versions of a part share the file name; Orca kept only the name
        tight = self.write("knob", (10, 10, 10), (0, 0, 5), "tight")
        self.write("knob", (10.4, 10.4, 10), (0, 0, 5), "loose")
        self.build(self.spec([build3mf.PlateSpec("p", 5, [build3mf.PartSpec("knob.stl", tight)])]))
        text = self.settings_xml().replace('value="%s"' % tight, 'value="knob.stl"')
        self.replace_entry(reload3mf.MODEL_SETTINGS, text)
        plates, problems = build3mf.read_layout(self.out, reload3mf.SourceFinder([self.dir]))
        part = plates[0][1][0]
        self.assertEqual(part.stl, tight)
        self.assertIn("matched by shape", part.note)

    def replace_entry(self, name, text):
        tmp = self.out + ".tmp"
        with zipfile.ZipFile(self.out) as src, zipfile.ZipFile(tmp, "w") as dst:
            for info in src.infolist():
                dst.writestr(info, text.encode() if info.filename == name else src.read(info.filename))
        os.replace(tmp, self.out)

    def test_rebuild_keeps_settings_and_painting(self):
        self.build()
        # Settings and painting made in Orca: printer settings, a part setting, a plate setting, support paint
        with zipfile.ZipFile(self.out) as z:
            objects = sorted(n for n in z.namelist() if n.startswith("3D/Objects/a.stl"))
            mesh_text = z.read(objects[0]).decode()
        text = self.settings_xml()
        text = text.replace('<metadata key="name" value="a.stl"/>\n    <metadata key="extruder" value="1"/>',
                            '<metadata key="name" value="a.stl"/>\n    <metadata key="extruder" value="1"/>\n'
                            '    <metadata key="wall_loops" value="5"/>', 1)
        text = text.replace('<metadata key="plater_name" value="second"/>',
                            '<metadata key="plater_name" value="second"/>\n'
                            '    <metadata key="curr_bed_type" value="Textured PEI Plate"/>')
        self.replace_entry(reload3mf.MODEL_SETTINGS, text)
        self.replace_entry(objects[0], re.sub(r'(<triangle v1="\d+" v2="\d+" v3="\d+")/>',
                                              r'\1 paint_supports="4"/>', mesh_text, count=1))
        self.replace_entry(build3mf.SETTINGS, json.dumps({"printable_area": A1_AREA, "layer_height": "0.12"}))

        lines = self.build(self.spec(template=""))
        self.assertIn("(rebuilt)", lines[0])
        text = self.settings_xml()
        self.assertIn('<metadata key="wall_loops" value="5"/>', text)
        self.assertIn('<metadata key="curr_bed_type" value="Textured PEI Plate"/>', text)
        with zipfile.ZipFile(self.out) as z:
            self.assertEqual(json.loads(z.read(build3mf.SETTINGS))["layer_height"], "0.12")
            self.assertIn("Metadata/filament_settings_1.config", z.namelist())  # the project's own settings files
            name = [n for n in z.namelist() if n.startswith("3D/Objects/a.stl")][0]
            self.assertEqual(z.read(name).decode().count('paint_supports="4"'), 1)

        # A new shape loses the painting, and says so
        self.stls["a"] = self.write("a", (42, 20, 10), (100, 50, 5))
        lines = self.build()
        self.assertTrue(any("painting removed" in line for line in lines), lines)
        with zipfile.ZipFile(self.out) as z:
            name = [n for n in z.namelist() if n.startswith("3D/Objects/a.stl")][0]
            self.assertNotIn("paint_supports", z.read(name).decode())

    def test_seams_are_painted_and_replace_old_seams(self):
        calls = []

        def seam(path, mesh):
            calls.append(path)
            return {0: "4", 3: "8"}, "seam on 2 triangles from Line 100%"

        plates = [build3mf.PlateSpec("p", 5, [build3mf.PartSpec("a.stl", self.stls["a"], seam=seam)])]
        lines = self.build(self.spec(plates))
        self.assertTrue(any("seam on 2 triangles" in line for line in lines))
        self.assertEqual(calls, [self.stls["a"]])
        with zipfile.ZipFile(self.out) as z:
            name = [n for n in z.namelist() if n.startswith("3D/Objects/")][0]
            tris = re.findall(r"<triangle ([^>]*)/>", z.read(name).decode())
        self.assertIn('paint_seam="4"', tris[0])
        self.assertIn('paint_seam="8"', tris[3])
        self.assertEqual(sum("paint_seam" in t for t in tris), 2)
        # Without a seam line the seam painting from Orca stays; with one, it is replaced
        plates[0].parts[0].seam = lambda path, mesh: ({5: "4"}, "seam on 1 triangles from Line 100%")
        self.build(self.spec(plates))
        with zipfile.ZipFile(self.out) as z:
            name = [n for n in z.namelist() if n.startswith("3D/Objects/")][0]
            tris = re.findall(r"<triangle ([^>]*)/>", z.read(name).decode())
        self.assertEqual([i for i, t in enumerate(tris) if "paint_seam" in t], [5])

    def test_new_project_without_settings_is_not_written(self):
        lines, written = build3mf.build(self.spec(template=""))
        self.assertFalse(written)
        self.assertTrue(any("no printer settings" in line for line in lines), lines)
        self.assertFalse(os.path.exists(self.out))

    def test_part_too_big_or_missing_stops_the_build(self):
        big = self.write("big", (300, 20, 10), (0, 0, 5))
        plates = [build3mf.PlateSpec("p", 5, [build3mf.PartSpec("big.stl", big),
                                              build3mf.PartSpec("gone.stl", os.path.join(self.dir, "gone.stl"))])]
        lines, written = build3mf.build(self.spec(plates))
        self.assertFalse(written)
        text = "\n".join(lines)
        self.assertIn("big.stl: does not fit on the plate", text)
        self.assertIn("gone.stl:", text)
        # Stood up it fits
        plates[0].parts = [build3mf.PartSpec("big.stl", big, up=(1, 0, 0))]
        self.build(self.spec(plates))

    def test_bed_size_and_offset_come_from_the_settings(self):
        make_template(self.template, area=["-90x-90", "90x-90", "90x90", "-90x90"])
        self.build(self.spec([build3mf.PlateSpec("p", 5, [build3mf.PartSpec("a.stl", self.stls["a"])]),
                              build3mf.PlateSpec("q", 5, [build3mf.PartSpec("c.stl", self.stls["c"])])]))
        placed = {n: (lo, hi) for n, _, lo, hi in self.placed()}
        lo, hi = placed["a.stl"]
        self.assertAlmostEqual((lo[0] + hi[0]) / 2, 0.0, places=4)  # centred on the bed
        lo, hi = placed["c.stl"]
        self.assertAlmostEqual((lo[0] + hi[0]) / 2, 180 * 1.2, places=4)  # second plate, 180 mm bed

    def add_object_setting(self, source, key, value):
        """Adds an object-level metadata key (in the <object> block) to the part whose source_file is `source`,
        as if it had been changed in Orca."""
        text = self.settings_xml()
        si = text.index('source_file" value="%s"' % source)
        oi = text.rindex('<object id=', 0, si)
        ni = text.index('key="name"', oi, si)
        ei = text.index('/>', ni) + 2
        text = text[:ei] + '\n    <metadata key="%s" value="%s"/>' % (key, value) + text[ei:]
        self.replace_entry(reload3mf.MODEL_SETTINGS, text)

    def object_block(self, source):
        text = self.settings_xml()
        si = text.index('source_file" value="%s"' % source)
        oi = text.rindex('<object id=', 0, si)
        return text[oi:text.index('</object>', oi)]

    def test_mirror_survives_import(self):
        plates = [build3mf.PlateSpec("p", 5, [
            build3mf.PartSpec("a.stl", self.stls["a"], (0, 0, 1), 0.0, 1, mirror=True),
            build3mf.PartSpec("b.stl", self.stls["b"], (0, 1, 0), math.radians(90), 1, mirror=False)])]
        self.build(self.spec(plates))
        plates_out, problems = build3mf.read_layout(self.out, reload3mf.SourceFinder([os.path.join(self.dir, "stl")]))
        self.assertEqual(problems, [])
        a = next(p for p in plates_out[0][1] if p.stl == self.stls["a"])
        b = next(p for p in plates_out[0][1] if p.stl == self.stls["b"])
        self.assertTrue(a.mirror)
        self.assertFalse(b.mirror)
        self.assertTrue(close(a.up, (0, 0, 1)))
        self.assertTrue(close(b.up, (0, 1, 0)))
        self.assertAlmostEqual(b.angle, math.radians(90), places=6)

    def test_plate_settings_follow_the_name_when_reordered(self):
        self.build()
        text = self.settings_xml().replace(
            '<metadata key="plater_name" value="first"/>',
            '<metadata key="plater_name" value="first"/>\n'
            '    <metadata key="curr_bed_type" value="Textured PEI Plate"/>')
        self.replace_entry(reload3mf.MODEL_SETTINGS, text)
        plates = self.spec().plates
        self.build(self.spec([plates[1], plates[0]]))
        text = self.settings_xml()
        block = text[text.index('plater_name" value="first"'):text.index('</plate>',
                                                                    text.index('plater_name" value="first"'))]
        self.assertIn('curr_bed_type" value="Textured PEI Plate"', block)

    def test_same_named_parts_keep_settings_by_shape(self):
        tight = self.write("knob", (10, 10, 10), (0, 0, 5), "tight")
        loose = self.write("knob", (10.4, 10.4, 10), (0, 0, 5), "loose")
        self.build(self.spec([build3mf.PlateSpec("p", 5, [build3mf.PartSpec("knob.stl", tight),
                                                          build3mf.PartSpec("knob.stl", loose)])]))
        self.add_object_setting(tight, "wall_loops", "6")
        self.build(self.spec([build3mf.PlateSpec("p", 5, [build3mf.PartSpec("knob.stl", loose),
                                                          build3mf.PartSpec("knob.stl", tight)])]))
        self.assertIn('wall_loops" value="6"', self.object_block(tight))
        self.assertNotIn('wall_loops', self.object_block(loose))

    def test_part_taller_than_printable_height_is_reported(self):
        make_template(self.template, printable_height="30")
        plates = [build3mf.PlateSpec("p", 5, [build3mf.PartSpec("b.stl", self.stls["b"], (0, 0, 1))])]
        lines, written = build3mf.build(self.spec(plates))
        self.assertFalse(written)
        self.assertTrue(any("printable height" in line for line in lines), lines)

    def test_non_rect_bed_and_exclude_area_warn(self):
        make_template(self.template, area=["0x0", "256x0", "180x180", "0x256"], bed_exclude_area="10x10,20x20")
        lines = self.build(self.spec([build3mf.PlateSpec("p", 5, [build3mf.PartSpec("a.stl", self.stls["a"])])]))
        self.assertTrue(any("not a rectangle" in line for line in lines), lines)
        self.assertTrue(any("bed exclude areas" in line for line in lines), lines)

    def rewrite(self, **entries):
        """Rewrite the built zip, replacing or adding the given entries (str or bytes)."""
        tmp = self.out + ".tmp"
        with zipfile.ZipFile(self.out) as src, zipfile.ZipFile(tmp, "w") as dst:
            for info in src.infolist():
                data = entries.pop(info.filename, None)
                if data is None:
                    data = src.read(info.filename)
                elif isinstance(data, str):
                    data = data.encode("utf-8")
                dst.writestr(info, data)
            for name, data in entries.items():
                dst.writestr(name, data.encode("utf-8") if isinstance(data, str) else data)
        os.replace(tmp, self.out)

    def test_extra_volumes_and_index_files_survive_rebuild(self):
        self.build()
        base = self.spec()
        root = zipfile.ZipFile(self.out).read(reload3mf.ROOT_MODEL).decode()
        cfg = self.settings_xml()

        # An extra modifier volume on object "a" (index 1): a second component, a sub-model and a <part>,
        # the way Orca stores a modifier / negative part / support blocker on a normal part.
        extra_model = (fixtures.HEADER + ' <resources>\n  <object id="999" '
                       'p:UUID="99999999-ffff-4c03-9d28-80fed5dfa1dc" type="model">\n'
                       '   <mesh>\n    <vertices>\n     <vertex x="0" y="0" z="0"/>\n'
                       '     <vertex x="1" y="0" z="0"/>\n     <vertex x="0" y="1" z="0"/>\n'
                       '    </vertices>\n    <triangles>\n     <triangle v1="0" v2="1" v3="2"/>\n'
                       '    </triangles>\n   </mesh>\n  </object>\n </resources>\n <build/>\n</model>\n')
        root = root.replace(
            'transform="1 0 0 0 1 0 0 0 1 0 0 0"/>\n   </components>',
            'transform="1 0 0 0 1 0 0 0 1 0 0 0"/>\n'
            '    <component p:path="/3D/Objects/extra.model" objectid="999" '
            'p:UUID="aaaa0001-b206-40ff-9872-83e8017abed1" transform="1 0 0 0 1 0 0 0 1 5 5 5"/>\n'
            '   </components>', 1)
        cfg = cfg.replace(
            '    </part>\n  </object>',
            '    </part>\n'
            '    <part id="999" subtype="modifier_part">\n'
            '      <metadata key="name" value="a.stl"/>\n'
            '      <metadata key="matrix" value="1 0 0 5 0 1 0 5 0 0 1 5 0 0 0 1"/>\n'
            '      <metadata key="wall_loops" value="9"/>\n'
            '      <mesh_stat edges_fixed="0" degenerate_facets="0" facets_removed="0" '
            'facets_reversed="0" backwards_edges="0"/>\n'
            '    </part>\n  </object>', 1)
        self.rewrite(**{
            reload3mf.ROOT_MODEL: root,
            reload3mf.MODEL_SETTINGS: cfg,
            "3D/Objects/extra.model": extra_model,
            "Metadata/layer_heights_profile.txt": "id=2|0.1;0.1;0.1;0.1;0.1;0.1\n",
            "Metadata/layer_config_ranges.xml":
                '<?xml version="1.0" encoding="UTF-8"?>\n<objects>\n'
                ' <object id="2">\n  <range min_z="0" max_z="1">\n'
                '   <option opt_key="layer_height">0.1</option>\n  </range>\n </object>\n</objects>\n',
            "Metadata/brim_ear_points.txt": "brim_points_format_version=0\nobject_id=3|1 2 3 0.5 4 5 6 0.5\n",
            "Metadata/custom_gcode_per_layer.xml":
                '<?xml version="1.0" encoding="UTF-8"?>\n<custom_gcodes_per_layer>\n'
                ' <plate>\n  <plate_info id="2"/>\n'
                '  <layer top_z="1.0" type="2" extruder="1" color="#FFFFFF" extra="" gcode="M600"/>\n'
                '  <mode value="SingleExtruder"/>\n </plate>\n</custom_gcodes_per_layer>\n',
        })

        # Swap the plates: c (old 3) -> 1, a (old 1) -> 2, b (old 2) -> 3; plate "second" -> position 1
        self.build(self.spec([base.plates[1], base.plates[0]]))
        with zipfile.ZipFile(self.out) as z:
            out_root = z.read(reload3mf.ROOT_MODEL).decode()
            out_cfg = z.read(reload3mf.MODEL_SETTINGS).decode()
            layer = z.read("Metadata/layer_heights_profile.txt").decode()
            ranges = z.read("Metadata/layer_config_ranges.xml").decode()
            brim = z.read("Metadata/brim_ear_points.txt").decode()
            gcode = z.read("Metadata/custom_gcode_per_layer.xml").decode()
        self.assertIn('transform="1 0 0 0 1 0 0 0 1 5 5 5"', out_root)
        self.assertEqual(out_root.count('<component '), 4)  # 3 main + 1 extra
        self.assertIn('subtype="modifier_part"', out_cfg)
        self.assertIn('wall_loops" value="9"', out_cfg)
        self.assertEqual(out_cfg.count('<part '), 4)
        self.assertIn("id=3|0.1;0.1;0.1;0.1;0.1;0.1", layer)
        self.assertIn('<object id="3"', ranges)
        self.assertIn("object_id=1|1 2 3 0.5 4 5 6 0.5", brim)
        self.assertIn('<plate_info id="1"', gcode)

    def test_common_folder(self):
        self.assertEqual(build3mf.common_folder(["GripV/parts/a.stl", "GripV/parts/x/b.stl"]), "GripV/parts")
        self.assertEqual(build3mf.common_folder(["a.stl", "GripV/b.stl"]), "")
        self.assertEqual(build3mf.strip_folder("GripV/parts/a.stl", "GripV"), "parts/a.stl")


if __name__ == "__main__":
    unittest.main()
