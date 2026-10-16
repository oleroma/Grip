"""The Orca tab in the 3D Viewport sidebar: where the projects are, the seam settings, the seam guides and the
Update button. The settings are saved in the .blend file (Scene.orca_reload), the seam tick on each object."""
import os
import zipfile
import xml.etree.ElementTree as ET

import bpy

from . import blender_seams, reload3mf, seams

REPORT_TEXT = "Orca reload report"


class OrcaReloadSettings(bpy.types.PropertyGroup):
    projects: bpy.props.StringProperty(
        name="Projects", subtype='FILE_PATH', default="//../orca_slicer/",
        description="An Orca project (.3mf), or a folder: every project under it is updated. "
                    "STLs that moved are searched for under this folder too")
    seam_width: bpy.props.FloatProperty(
        name="Seam width", subtype='DISTANCE', default=0.6, min=0.05, soft_max=3.0, precision=2,
        description="Width of the seam strip painted along each seam line. Orca puts the seam where a "
                    "perimeter crosses the strip, in its middle; about one line width is enough")
    snap_distance: bpy.props.FloatProperty(
        name="Snap distance", subtype='DISTANCE', default=1.0, min=0.0, soft_max=5.0, precision=2,
        description="How far a seam line may be from a part's surface and still be painted onto it. "
                    "Variants with other tolerances move the surface a little")
    replace: bpy.props.BoolProperty(
        name="Replace projects", default=False,
        description="Save over the original projects. Off: save next to each one as NAME_reloaded.3mf, "
                    "to check in Orca first")


class ORCA_OT_update_projects(bpy.types.Operator):
    bl_idname = "orca_reload.update_projects"
    bl_label = "Update Orca projects"
    bl_description = ("Reload every part of the Orca projects from its STL file and paint the seam lines onto "
                      "the parts they lie on. The full report goes to the text \"%s\"" % REPORT_TEXT)

    def execute(self, context):
        settings = context.scene.orca_reload
        target = os.path.normpath(bpy.path.abspath(settings.projects))
        if not settings.projects or not os.path.exists(target):
            self.report({'ERROR'}, "Projects not found: %s" % target)
            return {'CANCELLED'}
        projects = reload3mf.collect_projects([target], reload3mf.DEFAULT_SUFFIX)
        if not projects:
            self.report({'ERROR'}, "No .3mf projects in %s" % target)
            return {'CANCELLED'}

        lines, problems = blender_seams.collect(context)
        painter = seams.SeamPainter(lines, width=settings.seam_width, snap=settings.snap_distance)
        painted = {}  # STL path -> result, so an STL used by several parts is painted once

        def paint(part, path, mesh):
            key = os.path.normcase(os.path.abspath(path))
            if key not in painted:
                result = painter.paint(mesh.verts, mesh.tris, label=path)
                painted[key] = None if result is None else (result.strings, result.note())
            return painted[key]

        finder = reload3mf.SourceFinder([target if os.path.isdir(target) else os.path.dirname(target)])
        report = ["Seam lines: %s" % (", ".join(line.name for line in lines) or "none")]
        report += ["  skipped: %s" % p for p in problems]
        report.append("")
        stl_cache, changed, failed = {}, 0, 0
        for path in projects:
            out = path if settings.replace else reload3mf.output_path(path)
            try:
                text, code = reload3mf.process(path, finder, out, stl_cache=stl_cache, seams=paint,
                                               replace=settings.replace)
            except (reload3mf.ReloadError, OSError, zipfile.BadZipFile, ET.ParseError) as e:
                text, code = ["%s: %s" % (path, e), ""], reload3mf.EXIT_ERROR
            report += text
            changed += " -> " in text[0]
            failed += code != reload3mf.EXIT_OK
        unused = [name for name, n in painter.used.items() if n == 0]
        if unused:
            report.append("Seam lines on no part (further than the snap distance, or filtered out): "
                          + ", ".join(unused))

        block = bpy.data.texts.get(REPORT_TEXT) or bpy.data.texts.new(REPORT_TEXT)
        block.clear()
        block.write("\n".join(report) + "\n")

        summary = "%d of %d projects updated" % (changed, len(projects))
        if failed or unused or problems:
            summary += "; check the text \"%s\"" % REPORT_TEXT
        self.report({'WARNING'} if failed or unused or problems else {'INFO'}, summary)
        return {'FINISHED'}


class VIEW3D_PT_orca_reload(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Orca"
    bl_label = "Orca Reload"

    def draw(self, context):
        layout = self.layout
        settings = context.scene.orca_reload
        layout.use_property_split = True
        layout.use_property_decorate = False
        layout.prop(settings, "projects")
        layout.prop(settings, "seam_width")
        layout.prop(settings, "snap_distance")
        layout.prop(settings, "replace")
        layout.operator(ORCA_OT_update_projects.bl_idname, icon='FILE_REFRESH')


class VIEW3D_PT_orca_reload_seams(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Orca"
    bl_label = "Seam lines"
    bl_parent_id = "VIEW3D_PT_orca_reload"

    def draw(self, context):
        layout = self.layout
        obj = context.active_object
        if obj is not None and obj.type in {'CURVE', 'MESH'}:
            col = layout.column()
            col.prop(obj, "orca_seam", text="%s is a seam line" % obj.name)
            row = col.row()
            row.active = obj.orca_seam
            row.prop(obj, "orca_seam_only")
        else:
            layout.label(text="Select a curve or mesh to make it a seam line")
        guides = blender_seams.seam_objects(context.scene)
        if guides:
            col = layout.column(align=True)
            for guide in guides:
                text = guide.name + ("  (only %s)" % guide.orca_seam_only if guide.orca_seam_only else "")
                col.label(text=text, icon='CURVE_DATA' if guide.type == 'CURVE' else 'MESH_DATA')


classes = (OrcaReloadSettings, ORCA_OT_update_projects, VIEW3D_PT_orca_reload, VIEW3D_PT_orca_reload_seams)


def register_properties():
    bpy.types.Scene.orca_reload = bpy.props.PointerProperty(type=OrcaReloadSettings)
    bpy.types.Object.orca_seam = bpy.props.BoolProperty(
        name="Orca seam", default=False,
        description="Use this curve (its splines) or mesh (edges marked as seam, or all edges of an edges-only "
                    "mesh) as a seam line: Orca Reload paints the seam onto the parts it lies on")
    bpy.types.Object.orca_seam_only = bpy.props.StringProperty(
        name="Only for",
        description="Paint this seam line only on parts whose STL path contains this text, for example "
                    "case_standard. Empty: every part it lies on")


def unregister_properties():
    del bpy.types.Object.orca_seam_only
    del bpy.types.Object.orca_seam
    del bpy.types.Scene.orca_reload
