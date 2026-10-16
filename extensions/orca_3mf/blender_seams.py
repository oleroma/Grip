"""Seam lines from Blender objects, in world space (the STL files' coordinates).

A part's seam is a curve or mesh object picked in the part's Seam field:
- curve: its splines (Bezier at the curve's resolution; poly and NURBS by their points). Modifiers are ignored.
- mesh: the evaluated mesh, so Geometry Nodes output works. A mesh with faces gives the edges marked as seam
  (Edge > Mark Seam) or the edges of a boolean edge attribute named "orca_seam"; a mesh of only edges gives all.
"""
import contextlib

import bpy  # noqa: F401  (the add-on runs in Blender)
from mathutils.geometry import interpolate_bezier

from .seams import SeamLine

EDGE_ATTRIBUTE = "orca_seam"


def curve_polylines(obj):
    """World-space point lists of the object's splines."""
    mw = obj.matrix_world
    result = []
    for spline in obj.data.splines:
        if spline.type == 'BEZIER':
            pts = spline.bezier_points
            n = len(pts)
            if n < 2:
                continue
            res = max(spline.resolution_u, 1) + 1
            line = []
            for i in range(n if spline.use_cyclic_u else n - 1):
                a, b = pts[i], pts[(i + 1) % n]
                seg = interpolate_bezier(a.co, a.handle_right, b.handle_left, b.co, res)
                line += seg if not line else seg[1:]
            result.append([mw @ p for p in line])
        else:
            line = [mw @ p.co.xyz for p in spline.points]
            if spline.use_cyclic_u and len(line) > 2:
                line.append(line[0])
            if len(line) > 1:
                result.append(line)
    return result


@contextlib.contextmanager
def eye_unhidden(obj, view_layer):
    """Temporarily unhide an object hidden with the eye icon: the depsgraph does not evaluate it otherwise."""
    hidden = obj.name in view_layer.objects and obj.hide_get(view_layer=view_layer)
    if not hidden:
        yield
        return
    try:
        obj.hide_set(False, view_layer=view_layer)
        view_layer.update()
        yield
    finally:
        obj.hide_set(True, view_layer=view_layer)
        view_layer.update()


def mesh_segments(obj, context):
    """World-space segments of a seam mesh object, and a problem text or None."""
    with eye_unhidden(obj, context.view_layer):
        depsgraph = context.evaluated_depsgraph_get()
        ob = obj.evaluated_get(depsgraph)
        mesh = ob.to_mesh()
        try:
            mw = ob.matrix_world
            co = [mw @ v.co for v in mesh.vertices]
            edges = [tuple(e.vertices) for e in mesh.edges]
            if len(mesh.polygons):
                flags = [False] * len(edges)
                attr = mesh.attributes.get(EDGE_ATTRIBUTE)
                if attr is not None and attr.domain == 'EDGE' and attr.data_type == 'BOOLEAN':
                    attr.data.foreach_get("value", flags)
                marked = [False] * len(edges)
                mesh.edges.foreach_get("use_seam", marked)
                edges = [e for e, a, b in zip(edges, flags, marked) if a or b]
                if not edges:
                    return [], "has faces but no edges marked as seam"
        finally:
            ob.to_mesh_clear()
    return [(tuple(co[a]), tuple(co[b])) for a, b in edges], None


def seam_line(obj, context):
    """(SeamLine, None) of a seam object, or (None, problem text)."""
    if obj.type == 'CURVE':
        segs = [(tuple(a), tuple(b)) for line in curve_polylines(obj) for a, b in zip(line, line[1:])]
        problem = None if segs else "has no spline with two points"
    elif obj.type == 'MESH':
        segs, problem = mesh_segments(obj, context)
        if not segs and not problem:
            problem = "has no edges"
    else:
        return None, "is not a curve or a mesh"
    if problem:
        return None, problem
    return SeamLine(obj.name, segs), None
