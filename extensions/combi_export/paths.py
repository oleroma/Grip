"""Folder and file settings as paths: the Root folder, the Preset Root Directory, the collection / object Sub-folders
and the JSON file paths. Runs without Blender, so tests/test_paths.py checks it with plain Python, under the path rules
of Windows (ntpath) and Linux (posixpath) whatever the machine (every function takes `flavor`, os.path by default).

  - A relative path (`../dir/x`, `dir`) starts at the .blend file's folder (`base_dir`), like Blender's `//../dir/x`.
  - `/` and `\\` are both separators on every OS, so a file set up on Windows (`//..\\stl\\`) works on Linux.
  - Absolute paths stay as they are: `/home/me/stl`, `D:\\stl`, `D:/stl`, `\\\\server\\share\\stl`. A path starting
    with a single separator (`\\stl`) is the top of the drive of the folder it is below (the root of the file system on
    Linux).
  - A setting below another folder (resolve_below) may also use `../`; an absolute one replaces the folder above it.
"""
import os
import ntpath
import posixpath
import re

_DRIVE = re.compile(r"[A-Za-z]:")
_SEPARATORS = re.compile(r"[\\/]")

def path_kind(text):
    """How a path setting starts: "blend" (Blender's `//`), "network" (`\\\\server\\share`; also with `/` once the
    first character is `\\`), "drive" (`D:\\x`, `D:/x`), "top" (a single separator: the top of the drive) or
    "relative". A path starting with `//` is always Blender's prefix: `//server/x` is the folder `server/x` next to the
    .blend file, which is how Blender reads it too."""
    if text.startswith("//"): return "blend"
    if text[:1] == "\\" and text[1:2] in ("\\", "/"): return "network"
    if _DRIVE.match(text): return "drive"
    if text[:1] in ("\\", "/"): return "top"
    return "relative"

def is_absolute(text):
    """True for a setting that does not start at the folder above it (see path_kind)."""
    return path_kind(text) != "relative"

def _native(text, flavor):
    """`text` with the separators of `flavor`."""
    return text.replace("\\", "/") if flavor is posixpath else text.replace("/", "\\")

def resolve_below(parent, text, base_dir, flavor=os.path):
    """Absolute folder (or file) a setting `text` names below the folder `parent`: relative paths (`x`, `../x`) start at
    `parent`, `//x` at `base_dir` (the .blend file's folder), a single separator at the top of `parent`'s drive, and
    other absolute paths replace `parent`. An empty setting is `parent` itself."""
    if not text: return parent
    kind = path_kind(text)
    if kind == "blend":
        parent, text = base_dir, text[2:].lstrip("\\/")
    elif kind == "top" and flavor is ntpath:
        text = flavor.splitdrive(parent)[0] + _native(text, flavor)  # the drive (or share) the folder above is on
    elif kind != "relative":
        return flavor.normpath(_native(text, flavor))
    return flavor.normpath(flavor.join(parent, _native(text, flavor))) if text else flavor.normpath(parent)

def resolve_path(text, base_dir, flavor=os.path):
    """Absolute folder (or file) of a top-level setting (the Root folder, a JSON file): relative paths and `//` start at
    `base_dir`, the .blend file's folder (the current folder while the file is not saved). Empty stays empty."""
    return resolve_below(base_dir, text, base_dir, flavor) if text else ""

def portable_setting(text):
    """A setting as it is stored so it reads the same on every OS: a relative or `//` path (what Blender's file browser
    gives with *Relative Path* on, `//..\\stl\\` on Windows) with `/` between folders. Absolute paths are left as they
    are: they only exist on one machine anyway, and `\\\\server\\share` must stay a network path."""
    return text.replace("\\", "/") if path_kind(text) in ("blend", "relative") else text

def picked_setting(folder, base_dir, relative=True, flavor=os.path):
    """How a folder picked in the file browser is stored: `//` and its path from `base_dir` (the .blend file's folder),
    with `/` between folders and at the end like Blender's own (`//../stl/`), or the absolute folder when `relative` is
    off (Blender's *Relative Paths* preference, or a file that is not saved) or it is on another drive."""
    folder = flavor.normpath(_native(folder, flavor))
    if not relative: return folder
    try: rel = flavor.relpath(folder, flavor.normpath(_native(base_dir, flavor)))
    except ValueError: return folder
    return "//" if rel == flavor.curdir else "//" + rel.replace(flavor.sep, "/") + "/"

def nearest_existing_dir(folder, isdir=os.path.isdir, flavor=os.path):
    """`folder`, or the closest folder above it that exists (where a file browser can open), or "" when none does."""
    while folder and not isdir(folder):
        parent = flavor.dirname(folder)
        if parent == folder: return ""
        folder = parent
    return folder

def split_relative(text):
    """The folder names of a relative setting, separated by `/` or `\\`: `..` is kept (one folder up), empty names and
    `.` are dropped. A folder starting with dots (`..hidden`) is a name like any other."""
    return [p for p in _SEPARATORS.split(text) if p and p != "."]

def parts_below(root, path, flavor=os.path):
    """Folder names from `root` down to `path`, or None when `path` is outside `root` (or on another drive). `..hidden`
    below the root is inside it, only `..` itself leaves it."""
    root, path = flavor.normpath(_native(root, flavor)), flavor.normpath(_native(path, flavor))
    try: rel = flavor.relpath(path, root)
    except ValueError: return None  # another drive, or a network share next to a drive
    parts = [] if rel == flavor.curdir else rel.split(flavor.sep)
    return None if parts[:1] == [flavor.pardir] else parts

def relative_below(root, path, flavor=os.path):
    """`path` as it is stored below `root`: its folder names joined with `/` on every OS, or `path` itself (absolute)
    when it is outside `root` or on another drive."""
    parts = parts_below(root, path, flavor)
    return flavor.normpath(_native(path, flavor)) if parts is None else "/".join(parts)
