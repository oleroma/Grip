"""Seam lines to OrcaSlicer seam painting.

A seam line is a set of line segments in the STL's own coordinates (Blender world space, millimetres in Grip).
SeamPainter finds the lines that lie on a part's surface, snaps them onto it and paints a thin strip along them as
seam enforcer, in the format Orca stores in a 3MF: one paint_seam string per triangle.

The format (Orca's TriangleSelector, the same in PrusaSlicer and Bambu Studio) is a subdivision tree per triangle,
written as hex digits, one per node. A leaf is its state shifted left by two (0 none, 4 enforcer, 8 blocker). A
split into four is "3" after its four children, child 0 first: (v0, m01, m20), (m01, v1, m12), (m12, v2, m20),
(m01, m12, m20), where mXY is the midpoint of edge X-Y. Orca reads the string from the end, root first.

Only the Python standard library is used, so this runs inside and outside Blender.
"""

import math

NONE, ENFORCER, BLOCKER = 0, 1, 2

# A split triangle stops splitting when its longest edge is at most this share of the strip width, or at this depth.
LEAF_SHARE = 0.5
MAX_DEPTH = 10


class SeamLine:
    """One seam guide: a name for the report, its segments, and an optional filter.

    only: the line is used only on parts whose label (the STL path) contains this text, ignoring case;
    \\ and / are the same.
    """

    def __init__(self, name, segments, only=""):
        self.name = name
        self.segments = [(tuple(map(float, a)), tuple(map(float, b))) for a, b in segments]
        self.only = _plain(only or "").strip()

    def applies_to(self, label):
        return not self.only or self.only in _plain(label)


def _plain(text):
    return text.replace("\\", "/").lower()


class SeamResult:
    """paint_seam strings by triangle index, and the lines used with the share of each that lies on the part."""

    def __init__(self, strings, lines):
        self.strings = strings
        self.lines = lines

    def note(self):
        names = ", ".join("%s %d%%" % (name, round(100 * share)) for name, share in self.lines)
        return "seam on %d triangles from %s" % (len(self.strings), names)


# --------------------------------------------------------------------------
# Small vector helpers on tuples (fast enough in plain Python, no numpy needed)


def _sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _mid(a, b):
    return ((a[0] + b[0]) * 0.5, (a[1] + b[1]) * 0.5, (a[2] + b[2]) * 0.5)


def _dist2(p, q):
    dx, dy, dz = p[0] - q[0], p[1] - q[1], p[2] - q[2]
    return dx * dx + dy * dy + dz * dz


class _Segment:
    __slots__ = ("a", "d", "dd", "lo", "hi")

    def __init__(self, a, b):
        self.a = a
        self.d = _sub(b, a)
        self.dd = _dot(self.d, self.d)
        self.lo = (min(a[0], b[0]), min(a[1], b[1]), min(a[2], b[2]))
        self.hi = (max(a[0], b[0]), max(a[1], b[1]), max(a[2], b[2]))

    def dist2(self, p):
        a, d = self.a, self.d
        px, py, pz = p[0] - a[0], p[1] - a[1], p[2] - a[2]
        t = 0.0
        if self.dd > 0.0:
            t = (px * d[0] + py * d[1] + pz * d[2]) / self.dd
            t = 0.0 if t < 0.0 else 1.0 if t > 1.0 else t
        ex, ey, ez = px - t * d[0], py - t * d[1], pz - t * d[2]
        return ex * ex + ey * ey + ez * ez


def closest_point_on_triangle(p, a, b, c):
    """Closest point to p on triangle abc (Ericson, Real-Time Collision Detection, 5.1.5)."""
    ab, ac, ap = _sub(b, a), _sub(c, a), _sub(p, a)
    d1, d2 = _dot(ab, ap), _dot(ac, ap)
    if d1 <= 0.0 and d2 <= 0.0:
        return a
    bp = _sub(p, b)
    d3, d4 = _dot(ab, bp), _dot(ac, bp)
    if d3 >= 0.0 and d4 <= d3:
        return b
    vc = d1 * d4 - d3 * d2
    if vc <= 0.0 and d1 >= 0.0 and d3 <= 0.0:
        v = d1 / (d1 - d3) if d1 != d3 else 0.0
        return (a[0] + v * ab[0], a[1] + v * ab[1], a[2] + v * ab[2])
    cp = _sub(p, c)
    d5, d6 = _dot(ab, cp), _dot(ac, cp)
    if d6 >= 0.0 and d5 <= d6:
        return c
    vb = d5 * d2 - d1 * d6
    if vb <= 0.0 and d2 >= 0.0 and d6 <= 0.0:
        w = d2 / (d2 - d6) if d2 != d6 else 0.0
        return (a[0] + w * ac[0], a[1] + w * ac[1], a[2] + w * ac[2])
    va = d3 * d6 - d5 * d4
    if va <= 0.0 and d4 - d3 >= 0.0 and d5 - d6 >= 0.0:
        den = (d4 - d3) + (d5 - d6)
        w = (d4 - d3) / den if den else 0.0
        return (b[0] + w * (c[0] - b[0]), b[1] + w * (c[1] - b[1]), b[2] + w * (c[2] - b[2]))
    den = va + vb + vc
    if not den:
        return a
    v, w = vb / den, vc / den
    return (a[0] + ab[0] * v + ac[0] * w, a[1] + ab[1] * v + ac[1] * w, a[2] + ab[2] * v + ac[2] * w)


# --------------------------------------------------------------------------
# Paint strings


def encode(node):
    """Paint string of a tree: an int leaf state, or a tuple of four child trees in Orca's child order."""
    if isinstance(node, int):
        return "%X" % (node << 2)
    return "".join(encode(child) for child in node) + "3"


def decode(text):
    """Tree of a paint string (the inverse of encode, for split-into-four trees and states below 3)."""
    digits = [int(ch, 16) for ch in reversed(text)]
    pos = [0]

    def node():
        code = digits[pos[0]]
        pos[0] += 1
        if code & 0b11 == 0:
            return code >> 2
        if code != 3:
            raise ValueError("only splits into four are supported, got %X" % code)
        # Root first, children last to first.
        kids = [node() for _ in range(4)]
        return tuple(reversed(kids))

    tree = node()
    if pos[0] != len(digits):
        raise ValueError("%d digits left over" % (len(digits) - pos[0]))
    return tree


def leaves(tree, a, b, c):
    """(state, (a, b, c)) of every leaf of a tree on triangle abc."""
    if isinstance(tree, int):
        yield tree, (a, b, c)
        return
    m01, m12, m20 = _mid(a, b), _mid(b, c), _mid(c, a)
    for child, tri in zip(tree, ((a, m01, m20), (m01, b, m12), (m12, c, m20), (m01, m12, m20))):
        for leaf in leaves(child, *tri):
            yield leaf


# --------------------------------------------------------------------------
# Painter


class _Grid:
    """Uniform grid of items by bounding box, for finding the items near a triangle."""

    def __init__(self, size):
        self.size = size
        self.cells = {}

    def _range(self, lo, hi):
        s = self.size
        return [range(int(math.floor(lo[k] / s)), int(math.floor(hi[k] / s)) + 1) for k in range(3)]

    def add(self, item, lo, hi):
        rx, ry, rz = self._range(lo, hi)
        for i in rx:
            for j in ry:
                for k in rz:
                    self.cells.setdefault((i, j, k), []).append(item)

    def near(self, lo, hi):
        """Items whose cells overlap the box lo..hi, each once."""
        rx, ry, rz = self._range(lo, hi)
        found = {}
        if len(rx) * len(ry) * len(rz) > len(self.cells):
            for (i, j, k), items in self.cells.items():
                if i in rx and j in ry and k in rz:
                    for item in items:
                        found[id(item)] = item
        else:
            cells = self.cells
            for i in rx:
                for j in ry:
                    for k in rz:
                        for item in cells.get((i, j, k), ()):
                            found[id(item)] = item
        return list(found.values())


class _Sample:
    __slots__ = ("p", "line", "best", "best_d2")

    def __init__(self, p, line):
        self.p = p
        self.line = line
        self.best = None
        self.best_d2 = None


class SeamPainter:
    """Paints seam lines onto meshes as Orca seam enforcers.

    width: width of the painted strip on the surface. Orca counts a perimeter point as enforced when painting is
        within one line width of it, so a strip about one line wide is enough.
    snap: how far a line may be from the surface and still be snapped onto it (variants with other tolerances
        move the surface a little).
    min_share: a line is used on a part only when at least this share of it is within snap of the part, so a line
        drawn on one part does not paint the part next to it where they touch.
    """

    def __init__(self, lines, width=0.6, snap=1.0, min_share=0.5):
        if width <= 0 or snap < 0:
            raise ValueError("width must be above 0 and snap 0 or more")
        self.lines = [line for line in lines if line.segments]
        self.radius = width / 2.0
        self.snap = snap
        self.min_share = min_share
        self.step = min(0.25, self.radius)
        self.leaf2 = (LEAF_SHARE * width) ** 2
        self.used = {line.name: 0 for line in self.lines}  # parts each line was painted on

    def _samples(self, lines):
        samples, runs = [], []
        for line in lines:
            for a, b in line.segments:
                n = max(1, int(math.ceil(math.sqrt(_dist2(a, b)) / self.step)))
                run = []
                for k in range(n + 1):
                    t = k / n
                    run.append(_Sample((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t,
                                        a[2] + (b[2] - a[2]) * t), line))
                samples += run
                runs.append(run)
        return samples, runs

    def paint(self, verts, tris, label=""):
        """Seam painting for an indexed mesh (flat x, y, z list and flat triangle index list).

        Returns a SeamResult, or None when no seam line lies on this mesh."""
        lines = [line for line in self.lines if line.applies_to(label)]
        if not lines or not tris:
            return None
        samples, runs = self._samples(lines)
        reach = self.snap + self.radius
        grid = _Grid(max(2.0 * reach, 1.0))
        for s in samples:
            grid.add(s, s.p, s.p)
        glo = tuple(min(s.p[k] for s in samples) - reach for k in range(3))
        ghi = tuple(max(s.p[k] for s in samples) + reach for k in range(3))

        # 1. Snap every sample to its closest point on the surface, and keep the triangles near any sample.
        snap2 = self.snap * self.snap
        near_tris = []
        v = verts
        for t in range(len(tris) // 3):
            i0, i1, i2 = 3 * tris[3 * t], 3 * tris[3 * t + 1], 3 * tris[3 * t + 2]
            a = (v[i0], v[i0 + 1], v[i0 + 2])
            b = (v[i1], v[i1 + 1], v[i1 + 2])
            c = (v[i2], v[i2 + 1], v[i2 + 2])
            lo = (min(a[0], b[0], c[0]), min(a[1], b[1], c[1]), min(a[2], b[2], c[2]))
            hi = (max(a[0], b[0], c[0]), max(a[1], b[1], c[1]), max(a[2], b[2], c[2]))
            if (hi[0] < glo[0] or hi[1] < glo[1] or hi[2] < glo[2]
                    or lo[0] > ghi[0] or lo[1] > ghi[1] or lo[2] > ghi[2]):
                continue
            found = grid.near((lo[0] - reach, lo[1] - reach, lo[2] - reach),
                              (hi[0] + reach, hi[1] + reach, hi[2] + reach))
            if not found:
                continue
            near_tris.append((t, a, b, c, lo, hi))
            for s in found:
                q = closest_point_on_triangle(s.p, a, b, c)
                d2 = _dist2(s.p, q)
                if d2 <= snap2 and (s.best_d2 is None or d2 < s.best_d2):
                    s.best, s.best_d2 = q, d2

        # 2. Lines that lie on this mesh, and the snapped segments of each.
        share = {}
        for line in lines:
            mine = [s for s in samples if s.line is line]
            share[line.name] = sum(1 for s in mine if s.best is not None) / float(len(mine))
        used = [line for line in lines if share[line.name] >= self.min_share and share[line.name] > 0]
        if not used:
            return None
        used_ids = {id(line) for line in used}
        segments = []
        for run in runs:
            if id(run[0].line) not in used_ids:
                continue
            # Neighbouring snapped samples make a segment; a snapped sample next to an unsnapped one a dot.
            for s0, s1 in zip(run, run[1:]):
                if s0.best is not None:
                    segments.append(_Segment(s0.best, s1.best if s1.best is not None else s0.best))
            if run[-1].best is not None and run[-2].best is None:
                segments.append(_Segment(run[-1].best, run[-1].best))
        r = self.radius
        sgrid = _Grid(max(4.0 * r, 1.0))
        for seg in segments:
            sgrid.add(seg, seg.lo, seg.hi)

        # 3. Paint a strip of the strip width along the snapped segments.
        strings = {}
        for t, a, b, c, lo, hi in near_tris:
            cand = sgrid.near((lo[0] - r, lo[1] - r, lo[2] - r), (hi[0] + r, hi[1] + r, hi[2] + r))
            if not cand:
                continue
            tree = self._node(a, b, c, cand, 0)
            if tree != NONE:
                strings[t] = encode(tree)
        for line in used:
            self.used[line.name] += 1
        return SeamResult(strings, [(line.name, share[line.name]) for line in used])

    def _node(self, a, b, c, segs, depth):
        r2 = self.radius * self.radius
        for s in segs:
            if s.dist2(a) <= r2 and s.dist2(b) <= r2 and s.dist2(c) <= r2:
                return ENFORCER  # a capsule is convex: the whole triangle is inside it
        cen = ((a[0] + b[0] + c[0]) / 3.0, (a[1] + b[1] + c[1]) / 3.0, (a[2] + b[2] + c[2]) / 3.0)
        reach = math.sqrt(max(_dist2(cen, a), _dist2(cen, b), _dist2(cen, c))) + self.radius
        reach2 = reach * reach
        near = [s for s in segs if s.dist2(cen) <= reach2]
        if not near:
            return NONE
        if depth >= MAX_DEPTH or max(_dist2(a, b), _dist2(b, c), _dist2(c, a)) <= self.leaf2:
            return ENFORCER if any(s.dist2(cen) <= r2 for s in near) else NONE
        m01, m12, m20 = _mid(a, b), _mid(b, c), _mid(c, a)
        kids = (self._node(a, m01, m20, near, depth + 1),
                self._node(m01, b, m12, near, depth + 1),
                self._node(m12, c, m20, near, depth + 1),
                self._node(m01, m12, m20, near, depth + 1))
        if isinstance(kids[0], int) and all(k == kids[0] for k in kids):
            return kids[0]
        return kids
