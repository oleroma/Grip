"""Placing parts on Orca plates: orientation from an up axis and a turn around it, footprints, nesting with a gap,
and where Orca puts each plate.

Rotations are 3x3 row lists that turn a part's own coordinates (the STL's, Blender world space) into bed
coordinates. Only the Python standard library is used, so this runs inside and outside Blender.
"""

import math

IDENTITY = ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))
EPS = 1e-9


def _norm(v):
    length = math.sqrt(sum(c * c for c in v))
    if length < EPS:
        raise ValueError("the up axis must not be zero")
    return tuple(c / length for c in v)


def matmul(a, b):
    return tuple(tuple(sum(a[r][k] * b[k][c] for k in range(3)) for c in range(3)) for r in range(3))


def transpose(m):
    return tuple(tuple(m[c][r] for c in range(3)) for r in range(3))


def apply(m, v):
    return tuple(m[r][0] * v[0] + m[r][1] * v[1] + m[r][2] * v[2] for r in range(3))


def det(m):
    """Determinant of a 3x3 row list. Negative: a reflection (mirror) is baked in."""
    return (m[0][0] * (m[1][1] * m[2][2] - m[1][2] * m[2][1])
            - m[0][1] * (m[1][0] * m[2][2] - m[1][2] * m[2][0])
            + m[0][2] * (m[1][0] * m[2][1] - m[1][1] * m[2][0]))


def rot_z(angle):
    c, s = math.cos(angle), math.sin(angle)
    return ((c, -s, 0.0), (s, c, 0.0), (0.0, 0.0, 1.0))


def rotation_to_up(up):
    """The smallest rotation that turns the direction `up` (in the part's coordinates) to +Z.

    Upside down (up = -Z) is a half turn around X, so the part's X axis stays X."""
    ux, uy, uz = _norm(up)
    if uz > 1.0 - EPS:
        return IDENTITY
    if uz < -1.0 + EPS:
        return ((1.0, 0.0, 0.0), (0.0, -1.0, 0.0), (0.0, 0.0, -1.0))
    # Axis up x Z = (uy, -ux, 0), angle acos(uz): Rodrigues' formula.
    s = math.sqrt(ux * ux + uy * uy)
    kx, ky = uy / s, -ux / s
    c, sn, t = uz, s, 1.0 - uz
    return ((t * kx * kx + c, t * kx * ky, sn * ky),
            (t * kx * ky, t * ky * ky + c, -sn * kx),
            (-sn * ky, sn * kx, c))


def orientation(up, angle):
    """Rotation that puts `up` on top, then turns the part by `angle` (radians) around the bed's vertical axis."""
    return matmul(rot_z(angle), rotation_to_up(up))


def orientation_from_matrix(m):
    """(up, angle) of a rotation, the inverse of orientation(). Scale is removed first."""
    cols = [_norm([m[r][c] for r in range(3)]) for c in range(3)]
    m = tuple(tuple(cols[c][r] for c in range(3)) for r in range(3))
    up = tuple(m[2])  # the part direction that ends up on +Z
    turn = matmul(m, transpose(rotation_to_up(up)))
    return up, math.atan2(turn[1][0], turn[0][0])


def footprint(verts, rotation):
    """(lo, hi) corners of the bounding box of flat x, y, z vertices after the rotation."""
    (a, b, c), (d, e, f), (g, h, i) = rotation
    v = verts
    xs = [a * x + b * y + c * z for x, y, z in zip(v[0::3], v[1::3], v[2::3])]
    ys = [d * x + e * y + f * z for x, y, z in zip(v[0::3], v[1::3], v[2::3])]
    zs = [g * x + h * y + i * z for x, y, z in zip(v[0::3], v[1::3], v[2::3])]
    return (min(xs), min(ys), min(zs)), (max(xs), max(ys), max(zs))


# --------------------------------------------------------------------------
# Nesting: rectangles on a bed (MaxRects free space), each put where the group stays most compact


def nest(sizes, bed, gap, margin=None):
    """Places rectangles (width, depth) on a bed (width, depth) with `gap` between them and `margin` from the
    edges (default: gap / 2). Largest first, each where the bounding box of the group grows least (relative to
    the bed's shape), so the parts end up in a compact block; the block is centred on the bed.

    Returns (positions, left_out): positions[i] is the (x, y) of rectangle i's lower left corner, or None when
    it did not fit; left_out lists those indices."""
    margin = gap / 2.0 if margin is None else margin
    width, depth = bed[0] - 2 * margin + gap, bed[1] - 2 * margin + gap
    free = [(0.0, 0.0, width, depth)] if width > 0 and depth > 0 else []
    order = sorted(range(len(sizes)), key=lambda i: (-max(sizes[i]), -sizes[i][0] * sizes[i][1], i))
    placed = [None] * len(sizes)
    group = (0.0, 0.0, 0.0, 0.0)  # extent of the placed rectangles
    for i in order:
        w, d = sizes[i][0] + gap, sizes[i][1] + gap
        best = None
        for fx, fy, fw, fd in free:
            if w <= fw + EPS and d <= fd + EPS:
                gx, gy = max(group[2], fx + w), max(group[3], fy + d)
                score = (round(max(gx / width, gy / depth), 9), round(gx * gy, 6), min(fw - w, fd - d), fy, fx)
                if best is None or score < best[0]:
                    best = (score, fx, fy)
        if best is None:
            continue
        x, y = best[1], best[2]
        placed[i] = (x, y)
        group = (0.0, 0.0, max(group[2], x + w), max(group[3], y + d))
        free = _split_free(free, (x, y, w, d))
    used = [i for i, p in enumerate(placed) if p is not None]
    if used:
        lo_x = min(placed[i][0] for i in used)
        lo_y = min(placed[i][1] for i in used)
        hi_x = max(placed[i][0] + sizes[i][0] for i in used)
        hi_y = max(placed[i][1] + sizes[i][1] for i in used)
        dx = (bed[0] - (hi_x - lo_x)) / 2.0 - lo_x
        dy = (bed[1] - (hi_y - lo_y)) / 2.0 - lo_y
        for i in used:
            placed[i] = (placed[i][0] + dx, placed[i][1] + dy)
    return placed, [i for i, p in enumerate(placed) if p is None]


def _split_free(free, rect):
    x, y, w, d = rect
    out = []
    for fx, fy, fw, fd in free:
        if x >= fx + fw - EPS or x + w <= fx + EPS or y >= fy + fd - EPS or y + d <= fy + EPS:
            out.append((fx, fy, fw, fd))
            continue
        if x > fx + EPS:
            out.append((fx, fy, x - fx, fd))
        if x + w < fx + fw - EPS:
            out.append((x + w, fy, fx + fw - x - w, fd))
        if y > fy + EPS:
            out.append((fx, fy, fw, y - fy))
        if y + d < fy + fd - EPS:
            out.append((fx, y + d, fw, fy + fd - y - d))
    # Drop free rectangles inside others.
    keep = []
    for i, a in enumerate(out):
        inside = False
        for j, b in enumerate(out):
            if i != j and a[0] >= b[0] - EPS and a[1] >= b[1] - EPS and a[0] + a[2] <= b[0] + b[2] + EPS \
                    and a[1] + a[3] <= b[1] + b[3] + EPS and (a != b or j < i):
                inside = True
                break
        if not inside:
            keep.append(a)
    return keep


# --------------------------------------------------------------------------
# Plates

# Orca's LOGICAL_PART_PLATE_GAP: plates sit a fifth of the bed apart.
PLATE_GAP = 1.0 / 5.0


def plate_columns(count):
    """How many columns Orca lays `count` plates out in."""
    cols = int(math.sqrt(count))
    if cols * cols < count:
        cols += 1
    return max(cols, 1)


def plate_origin(index, count, bed):
    """World (x, y) of the front left corner of plate `index` (0 based) of `count`; rows go towards -Y."""
    cols = plate_columns(count)
    row, col = divmod(index, cols)
    return col * bed[0] * (1.0 + PLATE_GAP), -row * bed[1] * (1.0 + PLATE_GAP)

