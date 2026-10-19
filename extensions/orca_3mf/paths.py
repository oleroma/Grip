"""The tab's folders and files as absolute paths. No Blender needed.

A path may be written with / or \\ between folders, whichever system it was typed or saved on, so a .blend file
set up on Windows works on Linux and the other way round. A root that is not absolute starts at the .blend file's
folder: ../stl and Blender's //../stl are the same folder. A folder below a root starts at that root.
"""
import os.path as ospath


def is_absolute(path):
    """Absolute on Windows or Linux: starts with / or \\ (a Linux root, a Windows network share) or a drive (C:)."""
    return path[:1] in ("/", "\\") or path[1:2] == ":"


def join(base, *subs):
    """base joined with folders written with / or \\ between names; an absolute folder starts over."""
    path = base
    for sub in subs:
        sub = sub.replace("\\", "/")
        if sub[1:2] == ":":
            path = sub
        elif is_absolute(sub):
            path = ospath.join(path, sub)  # Windows: a lone / or \ starts at the top of the drive `path` is on
        else:
            path = ospath.join(path, *[p for p in sub.split("/") if p])
    return ospath.normpath(path) if path else path


def absolute(path, blend_dir):
    """A saved root or file as an absolute path. Blender's // and a relative path both start at `blend_dir`, the
    .blend file's folder (empty while the file is not saved: then the current folder). Empty stays empty."""
    if not path:
        return ""
    if path.startswith("//"):
        path = path[2:]
    return join(blend_dir, path) or ospath.curdir


def relative_to(path, base):
    """`path` below `base` with / between folders, or the absolute path when it is not below it."""
    try:
        rel = ospath.relpath(path, base)
    except ValueError:  # another drive
        return path
    return path if rel == ".." or rel.startswith(".." + ospath.sep) else rel.replace("\\", "/")


def relative_form(path, base):
    """`path` written from `base` with / between folders (../stl/GripV), as a picked folder or file is saved; the
    absolute path when there is no way there from `base` (no base, or another drive)."""
    if not base:
        return path
    try:
        rel = ospath.relpath(path, base)
    except ValueError:  # another drive
        return path
    return rel.replace("\\", "/")
