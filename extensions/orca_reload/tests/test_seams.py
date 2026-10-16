"""Tests for seams.py (seam lines to Orca seam painting). Plain Python, no Blender:

    python -I extensions/orca_reload/tests/test_seams.py
"""
import math
import os
import random
import sys
import unittest

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import seams  # noqa: E402
from seams import ENFORCER, NONE, SeamLine, SeamPainter  # noqa: E402


def plate(size=20.0, top=0.0, split=1):
    """A flat square at z=top made of 2*split*split triangles: (flat verts, flat tris)."""
    n = split + 1
    step = size / split
    verts = []
    for j in range(n):
        for i in range(n):
            verts += [-size / 2 + i * step, -size / 2 + j * step, top]
    tris = []
    for j in range(split):
        for i in range(split):
            a, b, c, d = j * n + i, j * n + i + 1, (j + 1) * n + i, (j + 1) * n + i + 1
            tris += [a, b, d, a, d, c]
    return verts, tris


def triangle(verts, tris, t):
    return tuple(tuple(verts[3 * tris[3 * t + k] + m] for m in range(3)) for k in range(3))


def seg_dist(p, a, b):
    d = [b[k] - a[k] for k in range(3)]
    dd = sum(x * x for x in d)
    t = 0.0 if dd == 0 else max(0.0, min(1.0, sum((p[k] - a[k]) * d[k] for k in range(3)) / dd))
    return math.sqrt(sum((p[k] - a[k] - t * d[k]) ** 2 for k in range(3)))


def painted_state(result, verts, tris, point):
    """State of the leaf that holds point (a point on the mesh), or None if no triangle holds it."""
    for t in range(len(tris) // 3):
        a, b, c = triangle(verts, tris, t)
        if not inside(point, a, b, c):
            continue
        text = result.strings.get(t)
        if text is None:
            return NONE
        for state, (x, y, z) in seams.leaves(seams.decode(text), a, b, c):
            if inside(point, x, y, z):
                return state
    return None


def inside(p, a, b, c, eps=1e-7):
    """Point in triangle, in the XY plane (the test meshes are flat)."""
    def side(p, q, r):
        return (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])
    s1, s2, s3 = side(a, b, p), side(b, c, p), side(c, a, p)
    return (s1 >= -eps and s2 >= -eps and s3 >= -eps) or (s1 <= eps and s2 <= eps and s3 <= eps)


class FormatTest(unittest.TestCase):
    def test_leaves_and_split(self):
        self.assertEqual(seams.encode(ENFORCER), "4")
        self.assertEqual(seams.encode(seams.BLOCKER), "8")
        # Children first, child 0 first, then "3": Orca reads it from the end, so child 3 comes first there.
        self.assertEqual(seams.encode((ENFORCER, NONE, NONE, NONE)), "40003")
        self.assertEqual(seams.encode((NONE, (ENFORCER, NONE, NONE, ENFORCER), NONE, NONE)), "040043003")

    def test_round_trip(self):
        rnd = random.Random(4)

        def tree(depth):
            if depth == 0 or rnd.random() < 0.4:
                return rnd.choice((NONE, ENFORCER, seams.BLOCKER))
            return tuple(tree(depth - 1) for _ in range(4))

        for _ in range(200):
            t = tree(5)
            self.assertEqual(seams.decode(seams.encode(t)), t)

    def test_children_follow_orca_split(self):
        # Orca's perform_split, 3 split sides: (v0, m01, m20), (m01, v1, m12), (m12, v2, m20), (m01, m12, m20).
        a, b, c = (0, 0, 0), (4, 0, 0), (0, 4, 0)
        got = [tri for _, tri in seams.leaves((1, 2, 0, 1), a, b, c)]
        self.assertEqual(got, [((0, 0, 0), (2, 0, 0), (0, 2, 0)), ((2, 0, 0), (4, 0, 0), (2, 2, 0)),
                               ((2, 2, 0), (0, 4, 0), (0, 2, 0)), ((2, 0, 0), (2, 2, 0), (0, 2, 0))])


class PainterTest(unittest.TestCase):
    def test_strip_follows_the_line(self):
        verts, tris = plate(split=1)  # two big 20 mm triangles
        line = SeamLine("seam", [((-10, 3, 0), (10, 3, 0))])
        result = SeamPainter([line], width=0.6, snap=1.0).paint(verts, tris)
        self.assertEqual(sorted(result.strings), [0, 1])
        for x in (-9.5, -5, 0, 4.2, 9.5):
            self.assertEqual(painted_state(result, verts, tris, (x, 3.0, 0)), ENFORCER, x)
            self.assertEqual(painted_state(result, verts, tris, (x, 4.0, 0)), NONE, x)
            self.assertEqual(painted_state(result, verts, tris, (x, 2.0, 0)), NONE, x)
        for t, text in result.strings.items():
            for state, tri in seams.leaves(seams.decode(text), *triangle(verts, tris, t)):
                if state == ENFORCER:
                    cen = tuple(sum(p[k] for p in tri) / 3 for k in range(3))
                    size = max(math.dist(tri[i], tri[(i + 1) % 3]) for i in range(3))
                    self.assertLessEqual(seg_dist(cen, (-10, 3, 0), (10, 3, 0)), 0.3 + size)

    def test_line_off_the_surface_is_snapped(self):
        verts, tris = plate(split=4)
        line = SeamLine("seam", [((-6, 0, 0.4), (6, 0, 0.4))])
        result = SeamPainter([line], width=0.6, snap=1.0).paint(verts, tris)
        self.assertEqual(painted_state(result, verts, tris, (1.0, 0.0, 0)), ENFORCER)
        self.assertEqual(painted_state(result, verts, tris, (8.0, 0.0, 0)), NONE)
        self.assertIsNone(SeamPainter([line], width=0.6, snap=0.2).paint(verts, tris))

    def test_line_mostly_elsewhere_is_left_out(self):
        verts, tris = plate(split=2)
        # Only the first 2 mm of a 20 mm line touch the plate's edge.
        line = SeamLine("seam", [((10, 0, 0), (30, 0, 0))])
        self.assertIsNone(SeamPainter([line], width=0.6, snap=0.5).paint(verts, tris))
        self.assertIsNotNone(SeamPainter([line], width=0.6, snap=0.5, min_share=0.0).paint(verts, tris))

    def test_only_filter(self):
        verts, tris = plate()
        line = SeamLine("seam", [((-5, 0, 0), (5, 0, 0))], only="Case_Standard")
        painter = SeamPainter([line])
        self.assertIsNone(painter.paint(verts, tris, label="D:/Grip/GripV/case_hollow/top.stl"))
        self.assertIsNotNone(painter.paint(verts, tris, label="D:/Grip/GripV/case_standard/top.stl"))
        self.assertEqual(painter.used["seam"], 1)

    def test_note(self):
        verts, tris = plate()
        result = SeamPainter([SeamLine("SeamR4", [((-5, 0, 0), (5, 0, 0))])]).paint(verts, tris)
        self.assertEqual(result.note(), "seam on 2 triangles from SeamR4 100%")


if __name__ == "__main__":
    unittest.main()
