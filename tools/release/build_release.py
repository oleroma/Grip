#!/usr/bin/env python3
"""Build the release zips of Grip's printed parts, or check that they can be built.

Everything comes from the files combi_export saves next to Grip.blend,
blender/<scene>_preset.json: their `exports` list every file the presets of
that scene write, below its export folder (orca_slicer/GripV/,
orca_slicer/GripX/). Each top folder of an export folder other than parts/
and tolerance folders is one release: GripV-standard from case_standard/,
GripX-xbox from xbox_style/. A release holds that folder and parts/ at one
tolerance, the OrcaSlicer projects named after it, a PRINT_LIST.md and the
license. The quantities and notes in PRINT_LIST.md are the scene's print list
in orca_slicer/README.md.

Usage:
    python build_release.py --check
    python build_release.py [--shape ID ...] [--tolerance LEVEL | --all-tolerances] [--full-paths]
    python build_release.py --print-list ID

A build with one tolerance leaves the tolerance folders out of the paths:
parts/buttons/default/cap_default/ becomes parts/buttons/cap/, and
parts/bumpers/press_default/ becomes parts/bumpers/. --full-paths keeps the
paths of orca_slicer/.

--check works on Git LFS pointer files too, so it runs on a clone without the
models. Building needs the real files. Only the Python standard library is
needed (Python 3.8+). See README.md next to this file.
"""

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_REPO = os.path.dirname(os.path.dirname(HERE))

# Where things are in the repository
ROOT = "orca_slicer"            # the folder the presets export to
PRESETS = "blender"             # combi_export saves <scene>_preset.json here, next to Grip.blend
PRESET_SUFFIX = "_preset.json"
SHARED = "parts"                # the export folder that every release of a scene takes
PRINT_LISTS = ROOT + "/README.md"  # holds a "## Print list: ..." section per scene

# The tolerance folders: tight/, default/, loose/, or a word before them (cap_default/, press_loose/)
LEVELS = ("tight", "default", "loose")
DEFAULT_LEVEL = "default"
TOL_DIR = re.compile(r"^(?:([A-Za-z]+)_)?(%s)$" % "|".join(LEVELS))

# Written into every release
REPO_URL = "https://github.com/oleroma/Grip"
BRANCH = "main"
LICENSE = "LICENSE"
LICENSE_NAME = "Creative Commons BY-NC-SA 4.0"
CREDITS = "Oleroma, Milwud"
NOTICE = ("Grip is an independent project, not affiliated with or endorsed by Microsoft or Sony. Xbox and "
          "DualSense are trademarks of their owners; the names only describe the case shapes.")
GUIDES = [
    ("Print list and tolerances", PRINT_LISTS),
    ("Printing guide", "docs/print-guide.md"),
    ("Customize and export your own parts", "docs/blender/customize/README.md"),
    ("Report how your print fit", REPO_URL + "/issues/new?template=fit-report.yml"),
]

ALL = "all-tolerances"
LFS_PREFIX = b"version https://git-lfs.github.com/spec/"
LFS_MAX = 1024  # pointer files are always smaller than this
PART_EXTS = (".stl", ".3mf")
SAFE_NAME = re.compile(r"^[A-Za-z0-9._-]+$")
WINDOWS_BAD = set('<>:"|?*\\')
ZIP_DATE = (1980, 1, 1, 0, 0, 0)  # fixed, so the same files give the same zip
MARKER = "PRINT_LIST.md"  # a folder holding this was made by this script

EXIT_OK, EXIT_ERROR = 0, 1


class BuildError(Exception):
    pass


# --------------------------------------------------------------------------
# The presets


class Scene:
    """One scene's exports: folder is its export folder below ROOT (GripV),
    files maps each exported file below it to the preset that writes it,
    sources lists the preset files it was read from."""

    def __init__(self, folder):
        self.folder = folder
        self.files = {}
        self.sources = []


def scene_folder(root_dir):
    """The export folder below ROOT that a combi_export root folder points at:
    GripV for D:\\Grip\\orca_slicer\\GripV\\ or //../orca_slicer/GripV/, whatever
    the drive or folders above. None when ROOT is not in it, or is its end."""
    parts = [p for p in re.split(r"[\\/]+", root_dir) if p not in ("", ".")]
    lower = [p.lower() for p in parts]
    if ROOT.lower() not in lower:
        return None
    rest = parts[len(lower) - lower[::-1].index(ROOT.lower()):]
    return "/".join(rest) or None


def disk_folder(root, folder):
    """folder with the spelling of the folders on disk below root, which can
    differ in case from a root folder typed on Windows."""
    out, cur = [], root
    for part in folder.split("/"):
        try:
            names = os.listdir(cur)
        except OSError:
            names = []
        same = [n for n in names if n.lower() == part.lower()]
        if part not in names and len(same) == 1:
            part = same[0]
        out.append(part)
        cur = os.path.join(cur, part)
    return "/".join(out)


def load_scenes(repo):
    """Read every blender/*_preset.json. Returns ([Scene], [(level, text)],
    [export folders of the preset files that could not be used]), level being
    "error" or "info". Two files with the same export folder are one scene."""
    scenes, notes, skipped = {}, [], []
    try:
        names = sorted(n for n in os.listdir(os.path.join(repo, PRESETS)) if n.endswith(PRESET_SUFFIX))
    except OSError:
        names = []
    if not names:
        notes.append(("error", "no %s/*%s: combi_export writes one per scene when Grip.blend is saved"
                      % (PRESETS, PRESET_SUFFIX)))
    for name in names:
        full = os.path.join(repo, PRESETS, name)
        path = PRESETS + "/" + name
        try:
            with open(full, encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, ValueError) as e:
            notes.append(("error", "%s is not valid JSON: %s" % (path, e)))
            continue
        root_dir = data.get("root_dir") if isinstance(data, dict) else None
        folder = scene_folder(root_dir) if isinstance(root_dir, str) else None
        if folder is None:
            notes.append(("error", "%s: its root folder %r is not a folder in %s/" % (path, root_dir, ROOT)))
            continue
        spelt = disk_folder(os.path.join(repo, ROOT), folder)
        if spelt != folder:
            notes.append(("info", "%s: its root folder names %s/%s/, the folder on disk is %s/%s/"
                          % (path, ROOT, folder, ROOT, spelt)))
            folder = spelt
        listing = data.get("exports")
        presets = listing.get("presets") if isinstance(listing, dict) else None
        if not isinstance(presets, list) or not all(
                isinstance(p, dict) and isinstance(p.get("files"), list) for p in presets):
            notes.append(("error", "%s has no list of the exported files: it was saved by an older "
                          "combi_export. Update the add-on from extensions/combi_export and save Grip.blend "
                          "with its \"Save JSON with File\" tick on" % path))
            skipped.append(folder)
            continue
        if listing.get("complete") is not True:
            notes.append(("error", "%s lists only part of the exported files (combi_export stops at 5000)"
                          % path))
            skipped.append(folder)
            continue
        scene = scenes.setdefault(folder, Scene(folder))
        scene.sources.append(path)
        count = 0
        for preset in presets:
            for rel in preset["files"]:
                if isinstance(rel, str) and rel:
                    scene.files.setdefault(rel, str(preset.get("name", "?")))
                    count += 1
        notes.append(("info", "%s: %s write%s %s to %s/%s/." % (
            path, plural(len(presets), "preset"), "s" if len(presets) == 1 else "", plural(count, "file"),
            ROOT, folder)))
    for folder in sorted(scenes):
        if not scenes[folder].files:
            notes.append(("error", "%s: the presets export no files to %s/%s/"
                          % (", ".join(scenes[folder].sources), ROOT, folder)))
    return [scenes[k] for k in sorted(scenes)], notes, skipped


def plural(n, word):
    return "%d %s%s" % (n, word, "" if n == 1 else "s")


# --------------------------------------------------------------------------
# Releases


class Release:
    """One zip: a scene's shape folder (case_standard) with its parts/ folder."""

    def __init__(self, scene, shape, files, projects, label=None, others=()):
        self.scene = scene
        self.shape = shape  # None for a scene without a shape folder
        self.files = files  # exported files below the scene folder, every tolerance
        self.projects = projects
        self.others = others  # the other shape folders of the scene
        name = os.path.basename(scene.folder)
        self.id = "-".join(p for p in (name, label) if p)
        self.title = " ".join(p for p in (name, label) if p)


def shape_label(shape):
    """case_standard -> standard, xbox_style -> xbox."""
    label = shape[len("case_"):] if shape.startswith("case_") and len(shape) > 5 else shape
    return label[:-len("_style")] if label.endswith("_style") and len(label) > 6 else label


def releases(scenes, tree):
    """The releases of the scenes. tree is scan() of ROOT, for the projects:
    <scene>_<shape folder>.3mf and <scene>_parts.3mf in the scene folder go with
    a release."""
    def top(rel):
        """The shape folder a file is in, or None for files every shape takes:
        parts/, tolerance folders and the scene folder itself."""
        head = rel.split("/")[0] if "/" in rel else SHARED
        return None if head == SHARED or TOL_DIR.match(head) else head

    out = []
    have = set(tree)
    for scene in scenes:
        if not scene.files:
            continue
        shapes = sorted(set(top(rel) for rel in scene.files) - {None})
        labels = dict((shape, shape_label(shape)) for shape in shapes)
        taken = [label.lower() for label in labels.values()]
        for shape, label in list(labels.items()):
            if taken.count(label.lower()) > 1:
                labels[shape] = shape  # case_xbox and xbox_style keep their folder names
        name = os.path.basename(scene.folder)
        for shape in shapes or [None]:
            files = sorted(rel for rel in scene.files if top(rel) in (shape, None))
            projects = [p for p in ("%s_%s.3mf" % (name, shape) if shape else None, "%s_%s.3mf" % (name, SHARED))
                        if p and scene.folder + "/" + p in have]
            out.append(Release(scene, shape, files, projects, labels.get(shape),
                               tuple(s for s in shapes if s != shape)))
    return out


def duplicate_ids(rels):
    """The release ids that several releases share, ignoring case: two scene
    folders with the same name."""
    seen = {}
    for release in rels:
        seen.setdefault(release.id.lower(), []).append(release.id)
    return sorted(ids[0] for ids in seen.values() if len(ids) > 1)


def find_release(rels, release_id):
    for release in rels:
        if release.id.lower() == release_id.lower():
            return release
    raise BuildError("unknown shape %r; known: %s" % (release_id, ", ".join(r.id for r in rels) or "none"))


def levels_of(rel):
    """The tolerance levels in the folders of a path: ['default', 'default']."""
    return [m.group(2) for m in (TOL_DIR.match(p) for p in rel.split("/")[:-1]) if m]


def any_level(parts):
    """A folder path with its tolerance folders made alike: tight/ and
    default/ are both *, cap_tight/ and cap_loose/ both cap*."""
    out = []
    for part in parts:
        m = TOL_DIR.match(part)
        out.append((m.group(1) or "") + "*" if m else part)
    return tuple(out)


def flat_folders(parts, holds_files):
    """The folders of a path without its tolerance folders. A bare one
    (default/) goes. One with a word (cap_default/) becomes the word (cap/)
    when holds_files says the folder it is in has files of its own, so the
    caps stay apart from the button.stl next to them; otherwise it goes too."""
    kept = []
    for i, part in enumerate(parts):
        m = TOL_DIR.match(part)
        if not m:
            kept.append(part)
        elif m.group(1) and holds_files(parts[:i]):
            kept.append(m.group(1))
    return kept


def folders_with_files(rels):
    """The folders that hold the files, in any_level() form."""
    return set(any_level(rel.split("/")[:-1]) for rel in rels)


def layout(release, mode, flat=False):
    """{file below the scene folder: its path in the release}, sorted. A build
    with one tolerance takes the files whose tolerance folders all name it.
    flat leaves those folders out, see flat_folders(). The projects go only
    into builds with the default tolerance, which they were laid out with
    (probably)."""
    files = [rel for rel in release.files if mode == ALL or all(l == mode for l in levels_of(rel))]
    out = {}
    if flat and mode != ALL:
        with_files = folders_with_files(files)
        for rel in files:
            parts = rel.split("/")
            out[rel] = "/".join(flat_folders(parts[:-1], lambda head: any_level(head) in with_files) + parts[-1:])
    else:
        out = {rel: rel for rel in files}
    if mode == DEFAULT_LEVEL:
        for project in release.projects:
            out.setdefault(project, project)
    return out


def missing_levels(release, mode):
    """The parts that have tolerance variants, but none at mode, so a build at
    mode leaves them out: [the part with * for its tolerance folders]."""
    have = {}
    for rel in release.files:
        levels = levels_of(rel)
        if levels:
            key = "/".join(_wild(p) for p in rel.split("/"))
            have.setdefault(key, set()).add(all(l == mode for l in levels))
    return sorted(key for key, found in have.items() if True not in found)


def clashes(paths):
    """[(release path, [files])] where several files would land on one path."""
    by_dest = {}
    for src, dest in paths.items():
        by_dest.setdefault(dest.lower(), []).append(src)
    return [(paths[srcs[0]], srcs) for srcs in by_dest.values() if len(srcs) > 1]


def check_mode(mode):
    if mode != ALL and mode not in LEVELS:
        raise BuildError("unknown tolerance %r; use one of %s" % (mode, ", ".join(LEVELS)))


# --------------------------------------------------------------------------
# Files


def lfs_oid(head):
    """The sha256 from Git LFS pointer text, or None if head is not a pointer."""
    if not head.startswith(LFS_PREFIX) or len(head) >= LFS_MAX:
        return None
    for line in head.decode("ascii", "replace").splitlines():
        if line.startswith("oid sha256:"):
            oid = line[len("oid sha256:"):].strip().lower()
            if re.fullmatch(r"[0-9a-f]{64}", oid):
                return oid
    return None


def fingerprint(path):
    """(sha256 of the content, is_pointer). For an LFS pointer the sha256 is its
    oid, which is the sha256 of the real file, so pointers and real files compare."""
    with open(path, "rb") as f:
        head = f.read(LFS_MAX)
        oid = lfs_oid(head)
        if oid:
            return oid, True
        h = hashlib.sha256(head)
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest(), False


def is_pointer(path):
    with open(path, "rb") as f:
        return lfs_oid(f.read(LFS_MAX)) is not None


def scan(root):
    """Every file under root as a sorted list of '/'-separated relative paths."""
    out = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames.sort()
        rel_dir = os.path.relpath(dirpath, root).replace(os.sep, "/")
        for name in filenames:
            out.append(name if rel_dir == "." else rel_dir + "/" + name)
    return sorted(out)


def native(root, rel):
    return os.path.join(root, *rel.split("/"))


def tracked(repo, root_rel):
    """The files git tracks under root_rel, relative to it; None without git.
    On Windows and macOS the disk holds only one of two names that differ by
    case, but git's list still has both."""
    try:
        out = subprocess.run(["git", "-C", repo, "ls-files", "-z", "--", root_rel],
                             capture_output=True, check=True).stdout
    except (OSError, subprocess.CalledProcessError):
        return None
    prefix = root_rel.strip("/") + "/"
    paths = (p.decode("utf-8", "replace") for p in out.split(b"\0") if p)
    return [p[len(prefix):] for p in paths if p.startswith(prefix)]


def missing_files(tree, rels):
    """[(rel, the spelling on disk or None)] for each rel that tree does not
    hold with exactly that spelling. A case-blind disk (Windows, macOS) finds
    such a file, but a clone on Linux would not."""
    by_lower = {}
    for rel in tree:
        by_lower.setdefault(rel.lower(), rel)
    have = set(tree)
    return [(rel, by_lower.get(rel.lower())) for rel in rels if rel not in have]


def name_problems(rel_paths):
    """(errors, warnings) about file and folder names that break somewhere."""
    errors, warnings = [], []
    names = set()
    for rel in rel_paths:
        parts = rel.split("/")
        names.update("/".join(parts[:i + 1]) for i in range(len(parts)))
    for path in sorted(names):
        part = path.rsplit("/", 1)[-1]
        if " " in part:
            errors.append("space in name: %s" % path)
        elif WINDOWS_BAD & set(part) or part.endswith("."):
            errors.append("name not allowed on Windows: %s" % path)
        elif not SAFE_NAME.match(part):
            odd = " ".join(sorted(set(c for c in part if not SAFE_NAME.match(c))))
            warnings.append("unusual characters %s (awkward in links and shells): %s" % (odd, path))
    by_case = {}
    for path in names:
        by_case.setdefault(path.lower(), []).append(path)
    for paths in sorted(by_case.values()):
        if len(paths) > 1:
            errors.append("names differ only by case: %s" % ", ".join(sorted(paths)))
    return errors, warnings


def identical_siblings(digests):
    """Tolerance variants in sibling folders that hold the same file.
    digests maps relative path -> sha256.
    Returns sorted (folder pattern, which levels are equal, files, files in the pattern)."""
    order = {l: i for i, l in enumerate(LEVELS)}
    groups = {}
    for rel, digest in digests.items():
        parts = rel.split("/")
        for i, part in enumerate(parts[:-1]):
            m = TOL_DIR.match(part)
            if m:
                key = (tuple(parts[:i]), m.group(1) or "", tuple(parts[i + 1:]))
                groups.setdefault(key, {})[m.group(2)] = digest
    found, totals = {}, {}
    for (head, prefix, tail), levels in groups.items():
        if len(levels) < 2:
            continue
        axis = "<%s_*>" % prefix if prefix else "<tolerance>"
        pattern = "/".join([_wild(p) for p in head] + [axis] + [_wild(p) for p in tail[:-1]]) + "/"
        totals[pattern] = totals.get(pattern, 0) + 1
        same = {}
        for level, digest in levels.items():
            same.setdefault(digest, []).append(level)
        classes = [sorted(c, key=order.get) for c in same.values() if len(c) > 1]
        if not classes:
            continue
        name = (prefix + "_") if prefix else ""
        summary = "; ".join(" = ".join(name + l for l in c) for c in sorted(classes, key=lambda c: order[c[0]]))
        found.setdefault((pattern, summary), []).append("/".join(list(head) + [name + "*"] + list(tail)))
    return sorted((p, s, sorted(files), totals[p]) for (p, s), files in found.items())


def _folders(rel):
    """The folders a file is in: a/b/c.stl -> a, a/b."""
    parts = rel.split("/")
    return ["/".join(parts[:i]) for i in range(1, len(parts))]


def _wild(part):
    m = TOL_DIR.match(part)
    if not m:
        return part
    return (m.group(1) + "_*") if m.group(1) else "*"


# --------------------------------------------------------------------------
# Print lists


def link(path):
    """A repository path or a full URL as a link that works outside the repository."""
    return path if "://" in path else "%s/blob/%s/%s" % (REPO_URL, BRANCH, path)


MD_LINK = re.compile(r"(\]\()([^)\s]+)(\))")


def absolute_links(text, base):
    """Markdown links of a file at `base` (a repository path) as full URLs, so
    they still work in a zip: (#tolerances) and (../docs/print-guide.md)."""
    folder = base.rpartition("/")[0]

    def fix(m):
        target = m.group(2)
        if "://" in target or target.startswith("mailto:"):
            return m.group(0)
        if target.startswith("#"):
            return m.group(1) + link(base) + target + m.group(3)
        path, _, anchor = target.partition("#")
        full = os.path.normpath(os.path.join(folder, path)).replace(os.sep, "/")
        return m.group(1) + link(full) + ("#" + anchor if anchor else "") + m.group(3)
    return MD_LINK.sub(fix, text)


def print_section(repo, scene, title=None):
    """A section of orca_slicer/README.md, up to the next "## " heading: the
    first "## Print list" heading that names the release title (GripV hollow),
    else the first that names the scene (GripV). None when no heading names it.
    Its links still point into the repository, see absolute_links()."""
    try:
        with open(os.path.join(repo, *PRINT_LISTS.split("/")), encoding="utf-8") as f:
            lines = f.read().splitlines()
    except OSError:
        return None
    starts = [i for i, line in enumerate(lines) if line.startswith("## Print list")]
    for name in (title, os.path.basename(scene.folder)):
        if not name:
            continue
        words = re.compile(r"(?<![\w-])%s(?![\w-])" % r"[\s-]+".join(map(re.escape, name.split())), re.I)
        start = next((i for i in starts if words.search(lines[i])), None)
        if start is not None:
            end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith("## ")), len(lines))
            return "\n".join(lines[start + 1:end]).strip("\n")
    return None


CODE = re.compile(r"`([^`\s]+)`")


def section_paths(section, scene):
    """The paths in backticks in a print list that name files or folders of the
    scene: `parts/buttons/default/button.stl`, `<style>/bumpers/`. Only paths
    that start with a folder the presets export to, or a <placeholder>, so not
    `blender/...` or the scene folder itself, nor names without a folder, nor
    paths made of placeholders only (`<style>/`)."""
    tops = set(rel.split("/")[0] for rel in scene.files if "/" in rel)
    out = []
    for m in CODE.finditer(section or ""):
        path = m.group(1)
        parts = [p for p in path.split("/") if p]
        if "/" in path and (parts[0] in tops or parts[0].startswith("<")) and any("<" not in p for p in parts):
            out.append(path)
    return out


def path_pattern(path):
    """A regex for a print-list path, <placeholder> standing for any name part."""
    parts = re.split(r"(<[^>/]*>)", path.rstrip("/"))
    return re.compile("".join("[^/]+" if p.startswith("<") else re.escape(p) for p in parts) + "$", re.I)


def matches(path, files):
    """Whether a print-list path names one of the files below the scene folder,
    or a folder holding one."""
    pattern = path_pattern(path)
    for rel in files:
        names = _folders(rel) + ([] if path.endswith("/") else [rel])
        if any(pattern.match(name) for name in names):
            return True
    return False


def unexported_paths(section, scene):
    """The print-list paths that name nothing the presets export, so no zip
    has them."""
    return [path for path in section_paths(section, scene) if not matches(path, scene.files)]


def release_section(section, release, flat):
    """The print list of one release: without the table rows that only name
    the other shapes of the scene (case_hollow/ in GripV standard), and with
    flat, the paths in backticks without their tolerance folders, as they are
    in the zip."""
    with_files = folders_with_files(release.files)

    def holds_files(head):
        key = any_level(head)
        return any(len(k) == len(key) and all(a == b or "<" in a for a, b in zip(key, k)) for k in with_files)

    def flatten(m):
        path = m.group(1)
        if "/" not in path or not any(TOL_DIR.match(p) for p in path.split("/")):
            return m.group(0)
        parts = path.rstrip("/").split("/")
        name = [] if path.endswith("/") or TOL_DIR.match(parts[-1]) else parts[-1:]
        folders = parts[:len(parts) - len(name)]
        kept = flat_folders(folders, holds_files) + name
        return "`%s`" % ("/".join(kept) + ("/" if not name else "")) if kept else m.group(0)

    out = []
    for line in section.split("\n"):
        paths = section_paths(line, release.scene) if line.startswith("|") else []
        if paths and all(p.split("/")[0] in release.others for p in paths):
            continue
        out.append(CODE.sub(flatten, line) if flat else line)
    return "\n".join(out)


def file_lines(paths):
    """The release paths grouped by folder: - `parts/buttons/`: `button.stl`"""
    by_dir = {}
    for path in sorted(paths):
        folder, _, name = path.rpartition("/")
        by_dir.setdefault(folder, []).append(name)
    return ["- %s: %s" % ("`%s/`" % d if d else "top folder", ", ".join("`%s`" % n for n in names))
            for d, names in sorted(by_dir.items())]


def print_list(release, mode, paths, section=None, source=None, flat=False):
    """The PRINT_LIST.md text of one release. paths is layout(), section is
    print_section(), source says what it was built from."""
    flat = flat and mode != ALL
    folder = "`%s/%s/`" % (ROOT, release.scene.folder)
    out = ["# %s: print list" % release.title, ""]
    if mode == ALL:
        out.append("Every tolerance variant is included. Start with `%s` everywhere." % DEFAULT_LEVEL)
    else:
        out.append("Fit: `%s`." % mode)
    if source:
        out.append("Built from %s." % source)
    others = " or ".join("`%s`" % l for l in LEVELS if l != (DEFAULT_LEVEL if mode == ALL else mode))
    tol_link = link(PRINT_LISTS) + "#tolerances"
    refit = "If a part does not fit, reprint only that part from %s tolerance (%s) in the repository; " \
            "the case stays. See [tolerances](%s)." % ("another" if flat else "the neighbouring", others, tol_link)
    if flat:
        moved = sorted(set((s.rpartition("/")[0], d.rpartition("/")[0]) for s, d in paths.items()))
        moved = [(s, d) for s, d in moved if s != d]
        out += ["", "Every fit part here is the `%s` one, so the paths leave out the tolerance folders that "
                    "%s in the repository has%s" % (mode, folder, ":" if moved else ".")]
        if moved:
            out += [""] + ["- `%s/` there is %s here" % (s, "`%s/`" % d if d else "the top folder")
                           for s, d in moved]
        out += ["", refit]
    else:
        out += ["", "The paths are the same as in %s in the repository, so the folder names show the "
                    "tolerance of each part. %s" % (folder, refit)]
    out += ["", "## What to print", ""]
    if section:
        kept = release_section(section, release, False)
        out += ["From the print list in the repository%s." % (", with the paths as they are in this zip"
                                                                if flat else ""),
                "", absolute_links(release_section(section, release, flat), PRINT_LISTS)]
        lost = unexported_paths(kept, release.scene)
        if lost:
            out += ["", "**Not in this zip:** %s. The print list names %s, but no preset exports %s."
                    % (", ".join("`%s`" % p for p in lost), "them" if len(lost) > 1 else "it",
                       "them" if len(lost) > 1 else "it")]
    else:
        out.append("See the [print list](%s) for how many of each part to print." % link(PRINT_LISTS))
    parts = [p for s, p in paths.items() if s not in release.projects]
    out += ["", "## Files in this zip", ""] + file_lines(parts)
    if any(s in release.projects for s in paths):
        out += ["", "## OrcaSlicer projects", ""]
        out += ["- `%s`" % p for p in release.projects]
        out += ["", "The parts laid out on plates, probably with the `%s` files. If a part was exported "
                    "again after a project was saved, the STL is the newer one." % DEFAULT_LEVEL]
    out += ["", "## Guides", ""] + ["- [%s](%s)" % (title, link(path)) for title, path in GUIDES]
    out += ["", "## License", "", "Licensed under %s, see `LICENSE`. Credits: %s." % (LICENSE_NAME, CREDITS),
            "", NOTICE]
    return "\n".join(out) + "\n"


# --------------------------------------------------------------------------
# --check


def check(repo, verbose=False):
    """Check that the releases can be built. Returns (exit code, report text)."""
    root = os.path.join(repo, ROOT)
    lines, errors, warnings = [], [], []

    def section(title):
        lines.append("")
        lines.append(title)

    def error(text):
        errors.append(text)
        lines.append("  ERROR    " + text)

    def warn(text):
        warnings.append(text)
        lines.append("  warning  " + text)

    def info(text):
        lines.append("  " + text)

    def result():
        lines.append("")
        lines.append("Result: %s, %s." % (plural(len(errors), "error"), plural(len(warnings), "warning")))
        return (EXIT_ERROR if errors else EXIT_OK), "\n".join(lines)

    lines.append("Checking %s/ against the combi_export presets" % ROOT)
    if not os.path.isdir(root):
        error("folder not found: %s" % root)
        return result()
    tree = scan(root)
    parts = [rel for rel in tree if rel.lower().endswith(PART_EXTS)]

    section("Presets")
    scenes, notes, skipped = load_scenes(repo)
    for level, text in notes:
        (error if level == "error" else info)(text)

    section("Releases")
    rels = releases(scenes, tree)
    exported = {}  # path below ROOT -> (scene, preset)
    for scene in scenes:
        for rel, preset in scene.files.items():
            exported[scene.folder + "/" + rel] = preset
    for release in rels:
        files = layout(release, DEFAULT_LEVEL, flat=True)
        projects = len(release.projects)
        info("%-20s %s at `%s`%s" % (release.id, plural(len(files) - projects, "file"), DEFAULT_LEVEL,
                                     ", with " + ", ".join(release.projects) if projects else ""))
        for dest, srcs in clashes(files):
            error("%s land on the same path %s in the %s release without tolerance folders"
                  % (" and ".join(release.scene.folder + "/" + s for s in srcs), dest, release.title))
        for level in LEVELS:
            lost = missing_levels(release, level)
            if lost:
                (error if level == DEFAULT_LEVEL else warn)(
                    "%s: %s no `%s` variant, so a %s build leaves %s out: %s" % (
                        release.id, plural(len(lost), "part") + (" has" if len(lost) == 1 else " have"), level,
                        "plain" if level == DEFAULT_LEVEL else "`--tolerance %s`" % level,
                        "it" if len(lost) == 1 else "them",
                        ", ".join(release.scene.folder + "/" + k for k in lost[:3]) + (", ..." if len(lost) > 3 else "")))
    for release_id in duplicate_ids(rels):
        error("several releases are called %s: rename one of their scene folders" % release_id)
    if not rels and not skipped:
        error("no releases: the presets export nothing")
    if not os.path.isfile(os.path.join(repo, LICENSE)):
        error("missing %s (copied into every release)" % LICENSE)
    for title, path in GUIDES:
        if "://" not in path and not os.path.isfile(os.path.join(repo, *path.split("/"))):
            warn("missing %s (linked from every print list)" % path)
    asked = {}  # path below ROOT -> the print list names it
    for scene in scenes:
        text = print_section(repo, scene)
        if text is None:
            warn("%s has no \"## Print list\" section that names %s, so its print lists only list the files"
                 % (PRINT_LISTS, os.path.basename(scene.folder)))
            continue
        texts = [print_section(repo, scene, r.title) for r in rels if r.scene is scene]
        for path in sorted(set(p for t in texts for p in unexported_paths(t, scene))):
            warn("the %s print list asks for `%s`, but no preset exports it, so no zip has it: add it to "
                 "a preset and export it, or take it out of %s" % (os.path.basename(scene.folder), path,
                                                                   PRINT_LISTS))
        paths = set(p for t in texts for p in section_paths(t, scene))
        for rel in tree:
            if rel.startswith(scene.folder + "/") and any(matches(p, [rel[len(scene.folder) + 1:]]) for p in paths):
                asked[rel] = True

    section("Exported files")
    missing = missing_files(tree, sorted(exported))
    for rel, other in missing:
        if other:
            error("case differs: preset %r exports %s, the file is %s" % (exported[rel], rel, other))
        else:
            error("missing %s: preset %r exports it, so export it again" % (rel, exported[rel]))
    if exported and not missing:
        info("all %d exported files are in %s/." % (len(exported), ROOT))

    section("Files no preset exports")
    folders = [scene.folder + "/" for scene in scenes]
    unread = [folder + "/" for folder in skipped]
    projects = set(release.scene.folder + "/" + p for release in rels for p in release.projects)
    stale = [rel for rel in parts if rel not in exported and rel not in projects
             and any(rel.startswith(f) for f in folders)]
    for rel in stale:
        if not rel.lower().endswith(".stl"):
            info("%s: an OrcaSlicer project that no release takes (name it <scene>_<folder>.3mf)" % rel)
        elif rel in asked:
            warn("%s: in no release, though the print list asks for it; add it to a preset and export it" % rel)
        else:
            warn("%s: in no release; delete it, or add it to a preset and export it" % rel)
    for folder in unread:
        count = len([rel for rel in parts if rel.startswith(folder)])
        info("%s: %s not checked, because its preset file could not be read" % (folder, plural(count, "file")))
    others = [rel for rel in parts if not any(rel.startswith(f) for f in folders + unread)]
    for rel in others:
        info("%s: outside the export folders" % rel)
    if not stale and not others and not unread:
        info("none.")

    section("File and folder names")
    name_errors, name_warnings = name_problems(sorted(set(tree) | set(tracked(repo, ROOT) or [])))
    for text in name_errors:
        error(text)
    for text in name_warnings:
        warn(text)
    if not name_errors and not name_warnings:
        info("%d files: no spaces, no names that differ only by case." % len(tree))

    digests, pointers = {}, 0
    for rel in parts:
        digests[rel], pointer = fingerprint(native(root, rel))
        pointers += pointer

    section("Tolerance variants that are the same file")
    found = identical_siblings({rel: d for rel, d in digests.items() if rel in exported})
    for pattern, summary, files, total in found:
        warn("%s: %s (%d of %d files)" % (pattern, summary, len(files), total))
        if verbose:
            for rel in files:
                info("           %s" % rel)
    if not found:
        info("every tolerance variant differs from its neighbours.")

    section("Git LFS")
    info("%d pointer files, %d real files." % (pointers, len(parts) - pointers))
    if pointers:
        info("Pointer files are fine for --check; run git lfs pull before building.")
    return result()


# --------------------------------------------------------------------------
# Building


def source_label(repo):
    """'commit `abc1234`', noting uncommitted changes to the parts or the preset
    files, which say what goes into the zips; None without git."""
    try:
        commit = subprocess.run(["git", "-C", repo, "rev-parse", "--short", "HEAD"],
                                capture_output=True, text=True, check=True).stdout.strip()
        dirty = [folder for folder in (ROOT, PRESETS) if subprocess.run(
            ["git", "-C", repo, "status", "--porcelain", "--", folder],
            capture_output=True, text=True, check=True).stdout.strip()]
    except (OSError, subprocess.CalledProcessError):
        return None
    if not commit:
        return None
    label = "commit `%s`" % commit
    if dirty:
        label += " with uncommitted changes in %s" % " and ".join("`%s/`" % d for d in dirty)
    return label


def release_name(release, mode, tag=None, flat=False):
    """GripV-standard, GripV-standard-tight, GripV-standard-all-tolerances: the
    default tolerance gets no suffix in a flat build. --full-paths names it."""
    shown = None if flat and mode == DEFAULT_LEVEL else mode
    return "-".join(p for p in (release.id, tag, shown) if p)


def prepare_folder(path):
    """Remove the folder and zip of an earlier build, refusing any other folder."""
    if os.path.exists(path):
        if not os.path.isfile(os.path.join(path, MARKER)):
            raise BuildError("%s exists and was not made by this script; remove it or use --out" % path)
        shutil.rmtree(path)
    if os.path.isfile(path + ".zip"):
        os.remove(path + ".zip")
    os.makedirs(path)


def write_zip(folder, zip_path):
    """Zip folder with its own name as the top folder, the same bytes for the same files."""
    base = os.path.basename(folder)
    tmp = zip_path + ".tmp"
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for rel in scan(folder):
            info = zipfile.ZipInfo(base + "/" + rel, ZIP_DATE)
            info.external_attr = 0o644 << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            with open(native(folder, rel), "rb") as f:
                z.writestr(info, f.read(), compresslevel=9)
    os.replace(tmp, zip_path)


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def update_sums(out_dir):
    """SHA256SUMS.txt for every zip in out_dir."""
    zips = sorted(n for n in os.listdir(out_dir) if n.endswith(".zip"))
    with open(os.path.join(out_dir, "SHA256SUMS.txt"), "w", encoding="utf-8", newline="\n") as f:
        for name in zips:
            f.write("%s  %s\n" % (sha256_file(os.path.join(out_dir, name)), name))


def build(repo, chosen, mode, out_dir, tag=None, make_zip=True, allow_pointers=False, log=print,
          flat=True):
    """Build a folder (and zip) per release. Returns the exit code. flat leaves the
    tolerance folders out of the paths, except with every tolerance."""
    flat = flat and mode != ALL
    root = os.path.join(repo, ROOT)
    tree = scan(root) if os.path.isdir(root) else []
    plans, missing, pointers, clashing, lacking = [], set(), set(), [], []
    for release in chosen:
        files = layout(release, mode, flat)
        clashing += [(release, dest, srcs) for dest, srcs in clashes(files)]
        if mode != ALL:
            lacking += [(release, part) for part in missing_levels(release, mode)]
        paths = [release.scene.folder + "/" + rel for rel in files]
        lost = set(rel for rel, _ in missing_files(tree, paths))
        missing |= lost
        for path in paths:
            if path not in lost and not allow_pointers and is_pointer(native(root, path)):
                pointers.add(path)
        plans.append((release, files))
    license_path = os.path.join(repo, LICENSE)
    if not os.path.isfile(license_path):
        missing.add(LICENSE)
    for path in sorted(missing):
        log("ERROR  missing %s" % path)
    for release, dest, srcs in clashing:
        log("ERROR  %s: %s land on the same path %s; build with --full-paths"
            % (release.id, " and ".join(srcs), dest))
    for release, part in lacking:
        log("ERROR  %s: %s/%s has no `%s` variant; export it, or build another tolerance"
            % (release.id, release.scene.folder, part, mode))
    if pointers:
        shown = sorted(pointers)[:5]
        one = len(pointers) == 1
        log("ERROR  %d file%s %s Git LFS pointer%s, not the model%s: %s%s" % (
            len(pointers), "" if one else "s", "is a" if one else "are", "" if one else "s", "" if one else "s",
            ", ".join(shown), ", ..." if len(pointers) > len(shown) else ""))
        log("Run git lfs pull to download the models first.")
    if missing or pointers or clashing or lacking:
        return EXIT_ERROR

    if not os.path.isdir(out_dir):
        os.makedirs(out_dir)
        # A new output folder inside the repository ignores itself, so builds never show in git.
        if os.path.normcase(os.path.abspath(out_dir)).startswith(os.path.normcase(os.path.abspath(repo)) + os.sep):
            with open(os.path.join(out_dir, ".gitignore"), "w", encoding="utf-8") as f:
                f.write("# Release builds, made by tools/release/build_release.py\n*\n")
    source = source_label(repo)

    for release, files in plans:
        name = release_name(release, mode, tag, flat)
        dest = os.path.join(out_dir, name)
        prepare_folder(dest)
        src_root = native(root, release.scene.folder)
        for rel, to in files.items():
            target = native(dest, to)
            os.makedirs(os.path.dirname(target), exist_ok=True)
            shutil.copyfile(native(src_root, rel), target)
        section = print_section(repo, release.scene, release.title)
        with open(os.path.join(dest, MARKER), "w", encoding="utf-8", newline="\n") as f:
            f.write(print_list(release, mode, files, section, source, flat))
        shutil.copyfile(license_path, os.path.join(dest, "LICENSE"))
        size = sum(os.path.getsize(native(dest, to)) for to in files.values())
        line = "%-32s %4d files, %6.1f MB" % (name, len(files), size / 1e6)
        if make_zip:
            write_zip(dest, dest + ".zip")
            line += " -> %s.zip" % name
        log(line)
        if section is None:
            log("    warning: %s has no print list for %s, so PRINT_LIST.md only lists the files"
                % (PRINT_LISTS, os.path.basename(release.scene.folder)))
        else:
            for path in unexported_paths(release_section(section, release, False), release.scene):
                log("    warning: the print list asks for `%s`, but no preset exports it" % path)
    if make_zip:
        update_sums(out_dir)
    log("Output: %s" % out_dir)
    return EXIT_OK


# --------------------------------------------------------------------------
# Command line


def main(argv=None):
    p = argparse.ArgumentParser(
        description="Build the release zips of the printed parts, or check that they can be built.",
        epilog="See README.md next to this script.")
    p.add_argument("--check", action="store_true",
                   help="check files and names only; works on Git LFS pointer files")
    p.add_argument("--list", action="store_true", help="list the releases and exit")
    p.add_argument("--print-list", metavar="SHAPE", help="print the PRINT_LIST.md of one release and exit")
    p.add_argument("--shape", action="append", metavar="ID", help="only this release (repeatable); default: all")
    which = p.add_mutually_exclusive_group()
    which.add_argument("--tolerance", metavar="LEVEL",
                       help="the tolerance of the included parts: tight, default or loose (default: default)")
    which.add_argument("--all-tolerances", action="store_true", help="include every tolerance variant")
    p.add_argument("--full-paths", action="store_true",
                   help="keep the tolerance folders and names of orca_slicer/ in the release, "
                        "for example parts/buttons/default/cap_default/ (always on with --all-tolerances)")
    p.add_argument("--out", metavar="DIR", help="output folder (default: dist/ in the repository)")
    p.add_argument("--tag", metavar="TEXT", help="added to folder and zip names, for example v0.1")
    p.add_argument("--no-zip", action="store_true", help="build the folders only")
    p.add_argument("--repo", metavar="DIR", default=DEFAULT_REPO, help="repository root (default: %(default)s)")
    p.add_argument("-v", "--verbose", action="store_true", help="--check: list every identical file")
    p.add_argument("--allow-pointers", action="store_true",
                   help="build even from Git LFS pointer files (only to try the script; the zips hold no models)")
    args = p.parse_args(argv)

    repo = os.path.abspath(args.repo)
    mode = ALL if args.all_tolerances else (args.tolerance or DEFAULT_LEVEL)
    flat = not args.full_paths and mode != ALL

    try:
        check_mode(mode)
        if args.check:
            code, text = check(repo, args.verbose)
            print(text)
            return code
        scenes, notes, _ = load_scenes(repo)
        problems = [text for level, text in notes if level == "error"]
        if problems:
            for text in problems:
                print("ERROR  %s" % text, file=sys.stderr)
            return EXIT_ERROR
        root = os.path.join(repo, ROOT)
        rels = releases(scenes, scan(root) if os.path.isdir(root) else [])
        same = duplicate_ids(rels)
        if same:
            raise BuildError("several releases are called %s: rename one of their scene folders" % ", ".join(same))
        if args.list:
            for release in rels:
                print("%-20s %s/%s/%s + %s/" % (release.id, ROOT, release.scene.folder,
                                                release.shape or "", SHARED))
            return EXIT_OK
        if args.print_list:
            release = find_release(rels, args.print_list)
            sys.stdout.write(print_list(release, mode, layout(release, mode, flat),
                                        print_section(repo, release.scene, release.title), None, flat))
            return EXIT_OK
        chosen = [find_release(rels, s) for s in args.shape] if args.shape else rels
        if not chosen:
            raise BuildError("no releases: the presets export nothing")
        out_dir = os.path.abspath(args.out) if args.out else os.path.join(repo, "dist")
        return build(repo, chosen, mode, out_dir, args.tag, not args.no_zip, args.allow_pointers, flat=flat)
    except BuildError as e:
        print("ERROR  %s" % e, file=sys.stderr)
        return EXIT_ERROR


if __name__ == "__main__":
    sys.exit(main())
