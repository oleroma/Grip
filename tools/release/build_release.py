#!/usr/bin/env python3
"""Build the release zips of Grip's printed parts, or check that they can be built.

Each released shape (GripV standard, GripV hollow, GripX xbox, GripX dualsense)
has a print set in print_sets.json: which files from orca_slicer/ to print and
how many of each. From it this script builds one folder and one zip per shape
with those files, a PRINT_LIST.md and the license.

Usage:
    python build_release.py --check
    python build_release.py [--shape ID ...] [--tolerance LEVEL | --all-tolerances]
    python build_release.py --print-list ID

--check works on Git LFS pointer files too, so it runs on a clone without the
models. Building needs the real files. Only the Python standard library is
needed (Python 3.8+). See README.md next to this file.
"""

import argparse
import hashlib
import itertools
import json
import os
import re
import shutil
import subprocess
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_SETS = os.path.join(HERE, "print_sets.json")
DEFAULT_REPO = os.path.dirname(os.path.dirname(HERE))

ALL = "all-tolerances"
LFS_PREFIX = b"version https://git-lfs.github.com/spec/"
LFS_MAX = 1024  # pointer files are always smaller than this
PART_EXTS = (".stl", ".3mf")
PLACEHOLDER = re.compile(r"\{(\w+)\}")
SAFE_NAME = re.compile(r"^[A-Za-z0-9._-]+$")
WINDOWS_BAD = set('<>:"|?*\\')
ZIP_DATE = (1980, 1, 1, 0, 0, 0)  # fixed, so the same files give the same zip
MARKER = "PRINT_LIST.md"  # a folder holding this was made by this script

EXIT_OK, EXIT_ERROR = 0, 1


class SetError(Exception):
    """print_sets.json does not describe valid print sets."""


class BuildError(Exception):
    pass


# --------------------------------------------------------------------------
# Print sets


def load_sets(path):
    with open(path, encoding="utf-8") as f:
        sets = json.load(f)
    validate(sets)
    return sets


def fill(template, values):
    """Replace the {placeholders} that values knows, leave the others."""
    return PLACEHOLDER.sub(lambda m: str(values.get(m.group(1), m.group(0))), template)


def expand(template, choices):
    """Every path a template gives, with choices mapping placeholder -> values."""
    names = list(dict.fromkeys(PLACEHOLDER.findall(template)))
    out = []
    for combo in itertools.product(*(choices[n] for n in names)):
        values = dict(zip(names, combo))
        out.append(PLACEHOLDER.sub(lambda m: values[m.group(1)], template))
    return out


def templates(item):
    if "files" in item:
        return list(item["files"])
    if "file" in item:
        return [item["file"]]
    return []


def validate(sets):
    """Raise SetError listing every problem in the print sets."""
    problems = []
    for key in ("root", "repo_url", "license", "tolerance_levels", "default_tolerance",
                "tolerance_placeholders", "groups", "shapes"):
        if key not in sets:
            problems.append("missing top-level key %r" % key)
    if problems:
        raise SetError("\n".join(problems))
    levels = sets["tolerance_levels"]
    if sets["default_tolerance"] not in levels:
        problems.append("default_tolerance %r is not one of %s" % (sets["default_tolerance"], levels))
    if ALL in levels:
        problems.append("%r cannot be a tolerance level" % ALL)
    tol_names = set(sets["tolerance_placeholders"])
    seen = set()
    for shape in sets["shapes"]:
        sid = shape.get("id", "?")
        where = "shape %s" % sid
        if sid in seen:
            problems.append("%s: id used twice" % where)
        seen.add(sid)
        for key in ("id", "title", "folder", "groups"):
            if key not in shape:
                problems.append("%s: missing %r" % (where, key))
        shape_vars = shape.get("vars", {})
        for gid in shape.get("groups", []):
            group = sets["groups"].get(gid)
            if group is None:
                problems.append("%s: unknown group %r" % (where, gid))
                continue
            for item in group.get("items", []):
                problems += _item_problems(item, "%s, group %s" % (where, gid), shape_vars, tol_names)
        for project in shape.get("projects", []):
            if PLACEHOLDER.search(project) or " " in project:
                problems.append("%s: project name %r has a placeholder or a space" % (where, project))
    if problems:
        raise SetError("\n".join(problems))


def _item_problems(item, where, shape_vars, tol_names):
    name = item.get("name")
    where = "%s, item %r" % (where, name)
    problems = []
    if not name:
        problems.append("%s: item without a name" % where)
    qty = item.get("qty")
    if not isinstance(qty, int) or isinstance(qty, bool) or qty < 1:
        problems.append("%s: qty must be a whole number of at least 1" % where)
    kinds = [k for k in ("file", "files", "missing") if k in item]
    if len(kinds) != 1:
        problems.append("%s: needs exactly one of file, files or missing" % where)
    choose = item.get("choose", {})
    if choose and "file" not in item:
        problems.append("%s: choose only works with file" % where)
    for t in templates(item):
        t = fill(t, shape_vars)
        if " " in t:
            problems.append("%s: space in path %r" % (where, t))
        unknown = set(PLACEHOLDER.findall(t)) - tol_names - set(choose)
        if unknown:
            problems.append("%s: unknown placeholder %s in %r" % (where, ", ".join(sorted(unknown)), t))
        unused = set(choose) - set(PLACEHOLDER.findall(t))
        if unused:
            problems.append("%s: choose %s not used in %r" % (where, ", ".join(sorted(unused)), t))
    for key, values in choose.items():
        if not values or not all(isinstance(v, str) for v in values):
            problems.append("%s: choose %r needs a list of strings" % (where, key))
    return problems


def find_shape(sets, shape_id):
    for shape in sets["shapes"]:
        if shape["id"].lower() == shape_id.lower():
            return shape
    raise BuildError("unknown shape %r; known: %s" % (shape_id, ", ".join(s["id"] for s in sets["shapes"])))


def resolve(sets, shape):
    """The groups of a shape with its folder variables filled in: [(group, items)]."""
    shape_vars = shape.get("vars", {})
    out = []
    for gid in shape["groups"]:
        group = sets["groups"][gid]
        items = []
        for item in group["items"]:
            item = dict(item)
            if "file" in item:
                item["file"] = fill(item["file"], shape_vars)
            if "files" in item:
                item["files"] = [fill(t, shape_vars) for t in item["files"]]
            items.append(item)
        out.append((group, items))
    return out


def tolerance_combos(sets, item, mode):
    """Each tolerance assignment an item needs in this mode: {placeholder: level}."""
    used = [p for p in sets["tolerance_placeholders"]
            if any("{%s}" % p in t for t in templates(item))]
    levels = sets["tolerance_levels"] if mode == ALL else [mode]
    for combo in itertools.product(levels, repeat=len(used)):
        yield dict(zip(used, combo))


def alternatives(item, tol):
    """The files an item offers for one tolerance assignment, one per choice."""
    if "files" in item:
        return [fill(t, tol) for t in item["files"]]
    if "file" in item:
        return expand(fill(item["file"], tol), item.get("choose", {}))
    return []


def item_files(sets, item, mode):
    out = []
    for tol in tolerance_combos(sets, item, mode):
        out += alternatives(item, tol)
    return list(dict.fromkeys(out))


def shape_files(sets, shape, mode):
    """Every file a shape's release needs, relative to its folder, in list order."""
    out = []
    for _, items in resolve(sets, shape):
        for item in items:
            out += item_files(sets, item, mode)
    if mode == sets["default_tolerance"]:
        out += shape.get("projects", [])
    return list(dict.fromkeys(out))


def check_mode(sets, mode):
    if mode != ALL and mode not in sets["tolerance_levels"]:
        raise BuildError("unknown tolerance %r; use one of %s" % (mode, ", ".join(sets["tolerance_levels"])))


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


def tolerance_dir(sets):
    levels = "|".join(re.escape(l) for l in sets["tolerance_levels"])
    return re.compile(r"^(?:([A-Za-z]+)_)?(%s)$" % levels)


def identical_siblings(sets, digests):
    """Tolerance variants in sibling folders that hold the same file.
    digests maps relative path -> sha256.
    Returns sorted (folder pattern, which levels are equal, files, files in the pattern)."""
    tol_dir = tolerance_dir(sets)
    order = {l: i for i, l in enumerate(sets["tolerance_levels"])}
    labels = sets["tolerance_placeholders"]
    groups = {}
    for rel, digest in digests.items():
        parts = rel.split("/")
        for i, part in enumerate(parts[:-1]):
            m = tol_dir.match(part)
            if m:
                key = (tuple(parts[:i]), m.group(1) or "", tuple(parts[i + 1:]))
                groups.setdefault(key, {})[m.group(2)] = digest
    found, totals = {}, {}
    for (head, prefix, tail), levels in groups.items():
        if len(levels) < 2:
            continue
        axis = "<%s>" % _axis_label(prefix, labels)
        pattern = "/".join([_wild(p, tol_dir) for p in head] + [axis] +
                           [_wild(p, tol_dir) for p in tail[:-1]]) + "/"
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


def _axis_label(prefix, labels):
    """Folder prefix -> setting name: cap -> cap tolerance, press and the GripX
    spelling pres -> press tolerance, no prefix -> tolerance."""
    if not prefix:
        return labels.get("tolerance", "tolerance")
    for key, label in labels.items():
        if key.startswith(prefix):
            return label
    return prefix + " tolerance"


def _wild(part, tol_dir):
    m = tol_dir.match(part)
    if not m:
        return part
    return (m.group(1) + "_*") if m.group(1) else "*"


def identical_alternatives(sets, shape, digest_of):
    """Files offered as a choice in one item that are the same file.
    digest_of(rel path under the shape folder) -> sha256 or None.
    Returns [(item name, [paths that are the same]), ...]."""
    out = []
    for _, items in resolve(sets, shape):
        for item in items:
            for tol in tolerance_combos(sets, item, ALL):
                same = {}
                for rel in alternatives(item, tol):
                    digest = digest_of(rel)
                    if digest:
                        same.setdefault(digest, []).append(rel)
                for paths in same.values():
                    if len(paths) > 1:
                        out.append((item["name"], paths))
    return out


# --------------------------------------------------------------------------
# --check


def check(repo, sets, verbose=False):
    """Check that the release can be built. Returns (exit code, report text)."""
    root = os.path.join(repo, sets["root"])
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

    lines.append("Checking %s/ against the print sets" % sets["root"])
    if not os.path.isdir(root):
        error("folder not found: %s" % root)
        return EXIT_ERROR, "\n".join(lines + ["", "Result: 1 error."])
    tree = scan(root)
    parts = [rel for rel in tree if rel.lower().endswith(PART_EXTS)]

    section("Print sets")
    needed = {}  # path under root -> shape titles
    for shape in sets["shapes"]:
        for rel in shape_files(sets, shape, ALL) + shape.get("projects", []):
            needed.setdefault(shape["folder"] + "/" + rel, []).append(shape["title"])
    missing = missing_files(tree, sorted(needed))
    for rel, other in missing:
        shapes = ", ".join(dict.fromkeys(needed[rel]))
        if other:
            error("case differs: the print sets name %s, the file is %s (%s)" % (rel, other, shapes))
        else:
            error("missing %s (%s)" % (rel, shapes))
    if not missing:
        info("%d shapes need %d files at all tolerances: all found." % (len(sets["shapes"]), len(needed)))
    for path in [sets["license"]] + [g["path"] for g in sets.get("guides", []) if "path" in g]:
        if not os.path.isfile(os.path.join(repo, *path.split("/"))):
            (error if path == sets["license"] else warn)("missing %s (linked from every print list)" % path)

    section("File and folder names")
    name_errors, name_warnings = name_problems(sorted(set(tree) | set(tracked(repo, sets["root"]) or [])))
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
    found = identical_siblings(sets, digests)
    for pattern, summary, files, total in found:
        warn("%s: %s (%d of %d files)" % (pattern, summary, len(files), total))
        if verbose:
            for rel in files:
                info("           %s" % rel)
    if not found:
        info("every tolerance variant differs from its neighbours.")

    section("Choices that are the same file")
    seen = {}
    for shape in sets["shapes"]:
        folder = shape["folder"]
        for name, paths in identical_alternatives(
                sets, shape, lambda rel: digests.get(folder + "/" + rel)):
            key = tuple(folder + "/" + p for p in paths)
            seen.setdefault(key, [name, []])[1].append(shape["title"])
    for key, (name, shapes) in sorted(seen.items()):
        warn("%s (%s; %s)" % (" = ".join(key), name, ", ".join(dict.fromkeys(shapes))))
    if not seen:
        info("every choice offers different files.")

    section("Not exported yet (listed in the print sets)")
    gaps = {}
    for shape in sets["shapes"]:
        for group, items in resolve(sets, shape):
            for item in items:
                if "missing" in item:
                    gaps.setdefault((group["title"], item["name"], item["qty"]), []).append(shape["title"])
    for (title, name, qty), shapes in gaps.items():
        warn("%d x %s (%s): %s" % (qty, name, title, ", ".join(shapes)))
    if not gaps:
        info("nothing.")

    section("Files no print set uses")
    unused = [rel for rel in parts if rel not in needed]
    for rel in unused:
        info(rel)
    if not unused:
        info("none.")

    section("Git LFS")
    info("%d pointer files, %d real files." % (pointers, len(parts) - pointers))
    if pointers:
        info("Pointer files are fine for --check; run git lfs pull before building.")

    lines.append("")
    lines.append("Result: %d error%s, %d warning%s." % (
        len(errors), "" if len(errors) == 1 else "s", len(warnings), "" if len(warnings) == 1 else "s"))
    return (EXIT_ERROR if errors else EXIT_OK), "\n".join(lines)


# --------------------------------------------------------------------------
# PRINT_LIST.md


def link(sets, guide):
    if "url" in guide:
        return guide["url"]
    return "%s/blob/%s/%s" % (sets["repo_url"], sets.get("branch", "main"), guide["path"])


def show_path(sets, template, mode):
    """A path template as printed: tolerance levels filled in, choices as <name>."""
    if mode == ALL:
        labels = {k: "<%s>" % v for k, v in sets["tolerance_placeholders"].items()}
    else:
        labels = {k: mode for k in sets["tolerance_placeholders"]}
    shown = fill(template, labels)
    return PLACEHOLDER.sub(lambda m: "<%s>" % m.group(1), shown)


def print_list(sets, shape, mode, source=None, same_files=()):
    """The PRINT_LIST.md text of one shape. source says what it was built from,
    same_files is identical_alternatives()."""
    folder = shape["folder"]
    out = ["# %s: print list" % shape["title"], ""]
    if shape.get("about"):
        out += [shape["about"], ""]
    names = ["`%s`" % v for v in sets["tolerance_placeholders"].values()]
    names = " and ".join([", ".join(names[:-1]), names[-1]]) if len(names) > 1 else names[0]
    if mode == ALL:
        out.append("Every tolerance variant is included. Start with `%s` in every place "
                   "a path says `<...tolerance>`." % sets["default_tolerance"])
    else:
        out.append("Fit: `%s` for %s." % (mode, names))
    if source:
        out.append("Built from %s." % source)
    tol_link = link(sets, {"path": sets["root"] + "/README.md"}) + "#tolerances"
    out += ["",
            "The paths are the same as in `%s/%s/` in the repository, so the folder names show the "
            "tolerance of each part. If a part does not fit, reprint only that part from the "
            "neighbouring tolerance (`tight` or `loose`); the case stays. See [tolerances](%s)."
            % (sets["root"], folder, tol_link)]

    groups = resolve(sets, shape)
    gaps = sum(1 for _, items in groups for item in items if "missing" in item)
    notes = list(shape.get("notes", []))
    for name, paths in same_files:
        notes.append("%s: %s are the same file in this release, so one of them was probably exported "
                     "with the wrong setting." % (name, " and ".join("`%s`" % p for p in paths)))
    if gaps:
        notes.insert(0, "Not complete yet: %d part%s %s not exported (marked **not exported yet** below)."
                     % (gaps, "" if gaps == 1 else "s", "is" if gaps == 1 else "are"))
    if notes:
        out.append("")
        out += ["> %s" % n if i == 0 else ">\n> %s" % n for i, n in enumerate(notes)]

    for group, items in groups:
        out += ["", "## " + group["title"], ""]
        intro = (["Only %s." % group["when"]] if group.get("when") else []) + \
            ([group["note"]] if group.get("note") else [])
        if intro:
            out += [" ".join(intro), ""]
        for item in items:
            out += _item_lines(sets, item, mode)

    projects = shape.get("projects", [])
    if projects and mode == sets["default_tolerance"]:
        out += ["", "## OrcaSlicer projects", ""]
        for p in projects:
            out.append("- `%s`" % p)
        out += ["", "The parts laid out on plates, probably with the `%s` files. If a part was "
                    "exported again after a project was saved, the STL is the newer one."
                    % sets["default_tolerance"]]

    if shape.get("hardware"):
        out += ["", "## Not printed", "", shape["hardware"]]
    if sets.get("guides"):
        out += ["", "## Guides", ""]
        out += ["- [%s](%s)" % (g["title"], link(sets, g)) for g in sets["guides"]]
    out += ["", "## License", ""]
    text = "Licensed under %s, see `LICENSE`." % sets.get("license_name", "the license in `LICENSE`")
    if sets.get("credits"):
        text += " Credits: %s." % sets["credits"]
    out.append(text)
    if sets.get("notice"):
        out += ["", sets["notice"]]
    return "\n".join(out) + "\n"


def _item_lines(sets, item, mode):
    head = "- %d x %s" % (item["qty"], item["name"])
    if item.get("optional"):
        head += " (optional)"
    tail = ["Only %s." % item["when"]] if item.get("when") else []
    if "missing" in item:
        tail.append(item["missing"])
    if item.get("note"):
        tail.append(item["note"])
    if item.get("unconfirmed"):
        tail.append("Not confirmed: %s" % item["unconfirmed"])
    if "missing" in item:
        return [head + ": **not exported yet.** " + " ".join(tail)]
    if "files" in item:
        lines = [head + ", one of:"]
        lines += ["  - `%s`" % show_path(sets, t, mode) for t in item["files"]]
        if tail:
            lines.append("  " + " ".join(tail))
        return lines
    line = head + ": `%s`" % show_path(sets, item["file"], mode)
    choose = item.get("choose", {})
    if choose:
        line += ", with " + "; ".join("%s one of %s" % (k, ", ".join("`%s`" % v for v in vals))
                                     for k, vals in choose.items())
    return [line + ("." if choose or tail else "") + (" " + " ".join(tail) if tail else "")]


# --------------------------------------------------------------------------
# Building


def source_label(repo, root):
    """'commit `abc1234`', noting uncommitted changes under root; None without git."""
    try:
        commit = subprocess.run(["git", "-C", repo, "rev-parse", "--short", "HEAD"],
                                capture_output=True, text=True, check=True).stdout.strip()
        dirty = subprocess.run(["git", "-C", repo, "status", "--porcelain", "--", root],
                               capture_output=True, text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None
    if not commit:
        return None
    label = "commit `%s`" % commit
    if dirty:
        label += " with uncommitted changes in `%s/`" % os.path.basename(os.path.normpath(root))
    return label


def release_name(shape, mode, tag=None):
    return "-".join(p for p in (shape["id"], tag, mode) if p)


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


def build(repo, sets, shapes, mode, out_dir, tag=None, make_zip=True, allow_pointers=False, log=print):
    """Build a folder (and zip) per shape. Returns the exit code."""
    root = os.path.join(repo, sets["root"])
    tree = scan(root) if os.path.isdir(root) else []
    plans, missing, pointers = [], set(), set()
    for shape in shapes:
        files = shape_files(sets, shape, mode)
        paths = [shape["folder"] + "/" + rel for rel in files]
        lost = set(rel for rel, _ in missing_files(tree, paths))
        missing |= lost
        for path in paths:
            if path not in lost and not allow_pointers and is_pointer(native(root, path)):
                pointers.add(path)
        plans.append((shape, files))
    license_path = os.path.join(repo, *sets["license"].split("/"))
    if not os.path.isfile(license_path):
        missing.add(sets["license"])
    for path in sorted(missing):
        log("ERROR  missing %s" % path)
    if pointers:
        shown = sorted(pointers)[:5]
        log("ERROR  %d file%s %s Git LFS pointer%s, not the model%s: %s%s" % (
            len(pointers), "" if len(pointers) == 1 else "s", "is a" if len(pointers) == 1 else "are",
            "" if len(pointers) == 1 else "s", "" if len(pointers) == 1 else "s",
            ", ".join(shown), ", ..." if len(pointers) > len(shown) else ""))
        log("Run git lfs pull to download the models first.")
    if missing or pointers:
        return EXIT_ERROR

    if not os.path.isdir(out_dir):
        os.makedirs(out_dir)
        # A new output folder inside the repository ignores itself, so builds never show in git.
        if os.path.normcase(os.path.abspath(out_dir)).startswith(os.path.normcase(os.path.abspath(repo)) + os.sep):
            with open(os.path.join(out_dir, ".gitignore"), "w", encoding="utf-8") as f:
                f.write("# Release builds, made by tools/release/build_release.py\n*\n")
    source = source_label(repo, root)

    for shape, files in plans:
        name = release_name(shape, mode, tag)
        dest = os.path.join(out_dir, name)
        prepare_folder(dest)
        src_root = native(root, shape["folder"])
        for rel in files:
            target = native(dest, rel)
            os.makedirs(os.path.dirname(target), exist_ok=True)
            shutil.copyfile(native(src_root, rel), target)
        same = identical_alternatives(
            sets, shape, lambda rel: fingerprint(native(dest, rel))[0] if os.path.isfile(native(dest, rel)) else None)
        with open(os.path.join(dest, MARKER), "w", encoding="utf-8", newline="\n") as f:
            f.write(print_list(sets, shape, mode, source, same))
        shutil.copyfile(license_path, os.path.join(dest, "LICENSE"))
        size = sum(os.path.getsize(native(dest, rel)) for rel in files)
        line = "%-32s %4d files, %6.1f MB" % (name, len(files), size / 1e6)
        if make_zip:
            write_zip(dest, dest + ".zip")
            line += " -> %s.zip" % name
        log(line)
        gaps = [i["name"] for _, items in resolve(sets, shape) for i in items if "missing" in i]
        if gaps:
            log("    not exported yet: %s" % ", ".join(gaps))
        for item_name, paths in same:
            log("    warning: %s: %s are the same file" % (item_name, " = ".join(paths)))
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
    p.add_argument("--list", action="store_true", help="list the shapes and exit")
    p.add_argument("--print-list", metavar="SHAPE", help="print the PRINT_LIST.md of one shape and exit")
    p.add_argument("--shape", action="append", metavar="ID", help="only this shape (repeatable); default: all")
    which = p.add_mutually_exclusive_group()
    which.add_argument("--tolerance", metavar="LEVEL",
                       help="the tolerance of the included parts: tight, default or loose (default: default)")
    which.add_argument("--all-tolerances", action="store_true", help="include every tolerance variant")
    p.add_argument("--out", metavar="DIR", help="output folder (default: dist/ in the repository)")
    p.add_argument("--tag", metavar="TEXT", help="added to folder and zip names, for example v0.1")
    p.add_argument("--no-zip", action="store_true", help="build the folders only")
    p.add_argument("--repo", metavar="DIR", default=DEFAULT_REPO, help="repository root (default: %(default)s)")
    p.add_argument("--sets", metavar="FILE", default=DEFAULT_SETS, help="print sets file (default: %(default)s)")
    p.add_argument("-v", "--verbose", action="store_true", help="--check: list every identical file")
    p.add_argument("--allow-pointers", action="store_true",
                   help="build even from Git LFS pointer files (only to try the script; the zips hold no models)")
    args = p.parse_args(argv)

    try:
        sets = load_sets(args.sets)
    except (OSError, ValueError) as e:
        print("ERROR  cannot read %s: %s" % (args.sets, e), file=sys.stderr)
        return EXIT_ERROR
    except SetError as e:
        print("ERROR  %s is not valid:\n%s" % (args.sets, e), file=sys.stderr)
        return EXIT_ERROR
    repo = os.path.abspath(args.repo)
    mode = ALL if args.all_tolerances else (args.tolerance or sets["default_tolerance"])

    try:
        check_mode(sets, mode)
        if args.list:
            for shape in sets["shapes"]:
                print("%-18s %s" % (shape["id"], shape.get("about", "")))
            return EXIT_OK
        if args.check:
            code, text = check(repo, sets, args.verbose)
            print(text)
            return code
        if args.print_list:
            shape = find_shape(sets, args.print_list)
            root = native(os.path.join(repo, sets["root"]), shape["folder"])
            same = identical_alternatives(
                sets, shape, lambda rel: fingerprint(native(root, rel))[0]
                if os.path.isfile(native(root, rel)) else None)
            sys.stdout.write(print_list(sets, shape, mode, None, same))
            return EXIT_OK
        shapes = [find_shape(sets, s) for s in args.shape] if args.shape else sets["shapes"]
        out_dir = os.path.abspath(args.out) if args.out else os.path.join(repo, "dist")
        return build(repo, sets, shapes, mode, out_dir, args.tag, not args.no_zip, args.allow_pointers)
    except BuildError as e:
        print("ERROR  %s" % e, file=sys.stderr)
        return EXIT_ERROR


if __name__ == "__main__":
    sys.exit(main())
