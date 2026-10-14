#!/usr/bin/env python3
"""Readable change report for blender/tracking.json.

The blender_tracking add-on rewrites tracking.json every time Grip.blend is
saved, so the git history of that file records every preset value change.
This script turns a change of the file into a list people can read: per
controller and preset group, every changed input as "old -> new", added and
removed nodes and inputs, edited basemeshes and a short summary of rewired
node groups.

Usage:
    python tracking_diff.py                 the last commit (HEAD~1 vs HEAD)
    python tracking_diff.py REF             the change made by commit REF
    python tracking_diff.py A..B            from commit A to commit B
    python tracking_diff.py A...B           from the merge base of A and B to B
    python tracking_diff.py OLD NEW         two commits or two files
    python tracking_diff.py FILE            HEAD vs a file (uncommitted changes)
    python tracking_diff.py --log 10        one report per commit, for the last
                                            10 commits that changed the file

Add --markdown for pull requests and GitHub job summaries.
Only the Python standard library is needed (Python 3.8+), so Blender's
bundled Python works too. See README.md next to this file.
"""

import argparse
import difflib
import json
import os
import re
import subprocess
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field

TRACKING_PATH = "blender/tracking.json"

# Friendly headings for the tracked controls panels (keys spelled as in the file).
PANELS = {
    "GripV controls": ("GripV", "custom ergonomic shape"),
    "GripX contols": ("GripX", "classic xbox and dualsense styles"),
}
# What each tracked basemesh is (docs/blender/customize/04-case.md).
MESH_NOTES = {
    "basemesh GripV": "GripV shape",
    "basemesh_X_style": "GripX xbox shape",
    "basemesh_D_style": "GripX dualsense shape",
    "basemesh GripR1": "old GripR1 shape",
    "basemesh GripS": "old GripS shape",
}
# Notes printed after a change of these (node, input) pairs.
HINTS = {
    ("global parameters", "variant"): "working setting, the export presets set their own",
}

# What the first and the deeper levels of a node path are called.
PANEL_WORDS = ("preset group", "node")
MODIFIER_WORDS = ("object", "modifier")

MAX_NAMES = 8           # names listed per line before "and N more" (all with --verbose)
RENAME_RATIO = 0.8      # how alike two names must be to count as a rename (difflib ratio)
LFS_POINTER = "version https://git-lfs.github.com/spec"


class TrackingError(Exception):
    pass


# --------------------------------------------------------------------------
# Tracked inputs
#
# tracked_inputs is {panel: {node key: entry}}, and an entry is
# {"properties": {...}, "inputs": {...}, "nodes": {node key: entry}}, each part
# optional. In Grip the panel level holds the preset groups and their "nodes"
# hold the constructors, but any depth works.


def is_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def same(a, b):
    """Value equality that keeps booleans apart from 0 and 1."""
    if isinstance(a, bool) or isinstance(b, bool):
        return type(a) is type(b) and a == b
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(same(x, y) for x, y in zip(a, b))
    return a == b


def entry_values(entry):
    """{label: value} of one node: its settings ('properties') and its inputs."""
    values = {f"{name} (setting)": value for name, value in (entry.get("properties") or {}).items()}
    values.update(entry.get("inputs") or {})
    return values


def child_nodes(entry):
    nodes = entry.get("nodes")
    return {k: v for k, v in nodes.items() if isinstance(v, dict)} if isinstance(nodes, dict) else {}


def flatten(entry, path=()):
    """[(node path below the entry, label, value)] for an entry and every node inside it."""
    rows = [(path, label, value) for label, value in sorted(entry_values(entry).items())]
    for key, child in sorted(child_nodes(entry).items()):
        rows.extend(flatten(child, path + (key,)))
    return rows


def count_nodes(entry):
    return sum(1 + count_nodes(child) for child in child_nodes(entry).values())


def strip_label(key):
    """Node key without its ' (label)' part."""
    return re.sub(r" \([^()]*\)$", "", key)


def base_name(key):
    """Node key without its label and without a '.001' style suffix."""
    return re.sub(r"\.[^.\s]+$", "", strip_label(key))


def alike(a, b):
    """True for names that differ only in spacing and case, or in a letter or two."""
    return " ".join(a.split()).lower() == " ".join(b.split()).lower() or \
        difflib.SequenceMatcher(None, a, b).ratio() >= RENAME_RATIO


def pair_up(candidates):
    """One-to-one pairing of (score, old, new) candidates, best score first. Returns {new: old}."""
    pairs, used = {}, set()
    for _score, old, new in sorted(candidates, key=lambda c: (-c[0], c[1], c[2])):
        if old not in used and new not in pairs:
            pairs[new] = old
            used.add(old)
    return pairs


@dataclass
class Change:
    """One input that changed: kind is 'changed', 'added', 'removed' or 'renamed'."""
    kind: str
    name: str
    old: object = None
    new: object = None
    old_name: str = None


@dataclass
class NodeDiff:
    """One node that changed. path runs from the preset group down to the node."""
    kind: str               # 'changed', 'added', 'removed' or 'renamed'
    path: tuple
    changes: list = field(default_factory=list)
    old_key: str = None     # renamed: the previous node key
    values: list = None     # added or removed: flatten() of the node
    nodes: int = 0          # added or removed: number of nodes inside it


def diff_values(old, new):
    """[Change] between two {label: value} dicts. A removed and an added input with
    the same value and a similar name count as one input renamed."""
    removed = [k for k in old if k not in new]
    added = [k for k in new if k not in old]
    renames = pair_up((difflib.SequenceMatcher(None, o, n).ratio(), o, n)
                      for o in removed for n in added if same(old[o], new[n]) and alike(o, n))
    renamed_from = set(renames.values())

    changes = []
    for name in sorted(set(old) | set(new)):
        if name in old and name in new:
            if not same(old[name], new[name]):
                changes.append(Change("changed", name, old[name], new[name]))
        elif name in renames:
            changes.append(Change("renamed", name, old[renames[name]], new[name], renames[name]))
        elif name in new:
            changes.append(Change("added", name, new=new[name]))
        elif name not in renamed_from:
            changes.append(Change("removed", name, old=old[name]))
    return changes


def node_renames(old, new):
    """{new key: old key} for removed and added nodes that are probably one node renamed:
    the same base name (or a similar name), the same inputs, at least half the values equal."""
    candidates = []
    for o in (k for k in old if k not in new):
        for n in (k for k in new if k not in old):
            if base_name(o) != base_name(n) and not alike(o, n):
                continue
            ov = {(p, label): v for p, label, v in flatten(old[o])}
            nv = {(p, label): v for p, label, v in flatten(new[n])}
            if set(ov) != set(nv):
                continue
            equal = sum(1 for k in ov if same(ov[k], nv[k]))
            if equal * 2 >= len(ov):
                candidates.append((equal, o, n))
    return pair_up(candidates)


def diff_nodes(old, new, path=()):
    """[NodeDiff] between two {node key: entry} dicts, each node followed by the nodes inside it."""
    old = {k: v for k, v in old.items() if isinstance(v, dict)}
    new = {k: v for k, v in new.items() if isinstance(v, dict)}
    renames = node_renames(old, new)
    renamed_from = set(renames.values())
    result = []
    for key in sorted(set(old) | set(new)):
        here = path + (key,)
        if key in old and key in new:
            changes = diff_values(entry_values(old[key]), entry_values(new[key]))
            if changes:
                result.append(NodeDiff("changed", here, changes))
            result.extend(diff_nodes(child_nodes(old[key]), child_nodes(new[key]), here))
        elif key in renames:
            before = old[renames[key]]
            changes = diff_values(entry_values(before), entry_values(new[key]))
            result.append(NodeDiff("renamed", here, changes, old_key=renames[key]))
            result.extend(diff_nodes(child_nodes(before), child_nodes(new[key]), here))
        elif key in new:
            result.append(NodeDiff("added", here, values=flatten(new[key]), nodes=count_nodes(new[key])))
        elif key not in renamed_from:
            result.append(NodeDiff("removed", here, values=flatten(old[key]), nodes=count_nodes(old[key])))
    return result


def group_by_first(node_diffs):
    """{first path element: [NodeDiff]}, in order."""
    groups = {}
    for d in node_diffs:
        groups.setdefault(d.path[0], []).append(d)
    return groups


# --------------------------------------------------------------------------
# Meshes and node trees


def diff_meshes(old, new):
    """[(object, 'edited' | 'added' | 'removed')] from two {object: hash} dicts."""
    changes = []
    for name in sorted(set(old) | set(new)):
        if name not in old:
            changes.append((name, "added"))
        elif name not in new:
            changes.append((name, "removed"))
        elif old[name] != new[name]:
            changes.append((name, "edited"))
    return changes


# A link line, as blender_tracking writes it: "[from node] output -> input [to node]" + " (muted)"
LINK_RE = re.compile(r"^\[(.*?)\] (.*) -> (.*) \[(.*)\]( \(muted\))?$")


def parse_link(link):
    """(from node, output, input, to node, muted) of a link line, or None."""
    m = LINK_RE.match(link)
    return (m.group(1), m.group(2), m.group(3), m.group(4), bool(m.group(5))) if m else None


def link_nodes(links):
    nodes = set()
    for parts in filter(None, map(parse_link, links)):
        nodes.update((parts[0], parts[3]))
    return nodes


@dataclass
class TreeDiff:
    name: str
    added: list = field(default_factory=list)           # link lines
    removed: list = field(default_factory=list)
    muted: list = field(default_factory=list)
    unmuted: list = field(default_factory=list)
    relabeled: list = field(default_factory=list)       # (old node key, new node key)
    linked_nodes: list = field(default_factory=list)    # nodes without links before
    unlinked_nodes: list = field(default_factory=list)  # nodes without links now

    @property
    def rewired(self):
        return bool(self.added or self.removed or self.muted or self.unmuted)


def take_pairs(removed, added, key):
    """Takes out removed and added links whose parse_link() gives the same key; returns the pairs."""
    waiting = defaultdict(list)
    for link in added:
        parts = parse_link(link)
        if parts:
            waiting[key(parts)].append(link)
    pairs = []
    for link in list(removed):
        parts = parse_link(link)
        if parts and waiting.get(key(parts)):
            new = waiting[key(parts)].pop(0)
            pairs.append((link, new))
            removed.remove(link)
            added.remove(new)
    return pairs


def diff_tree(name, old_links, new_links):
    """TreeDiff of one node group, or None when its links did not change.

    A link that differs only in a node label is a relabel, one that differs only in
    '(muted)' was muted or unmuted, and the rest were added or removed."""
    old_count, new_count = Counter(old_links), Counter(new_links)
    if old_count == new_count:
        return None
    diff = TreeDiff(name)
    diff.removed = sorted((old_count - new_count).elements())
    diff.added = sorted((new_count - old_count).elements())

    relabels = set()
    same_but_labels = lambda p: (strip_label(p[0]), p[1], p[2], strip_label(p[3]), p[4])
    for old, new in take_pairs(diff.removed, diff.added, same_but_labels):
        o, n = parse_link(old), parse_link(new)
        relabels.update((a, b) for a, b in ((o[0], n[0]), (o[3], n[3])) if a != b)
    for _old, new in take_pairs(diff.removed, diff.added, lambda p: p[:4]):
        (diff.muted if parse_link(new)[4] else diff.unmuted).append(new)

    before, after = link_nodes(old_links), link_nodes(new_links)
    linked = after - before - {b for _a, b in relabels}
    unlinked = before - after - {a for a, _b in relabels}
    # A node that lost or got a label and was also rewired is still the same node.
    for a in sorted(unlinked):
        match = [b for b in sorted(linked) if strip_label(b) == strip_label(a)]
        if match:
            relabels.add((a, match[0]))
            linked.discard(match[0])
            unlinked.discard(a)
    diff.relabeled = sorted(relabels)
    diff.linked_nodes, diff.unlinked_nodes = sorted(linked), sorted(unlinked)
    return diff


def diff_trees(old, new):
    """(trees added, trees removed, [TreeDiff]) between two all_node_trees dicts."""
    changed = (diff_tree(name, old[name] or [], new[name] or []) for name in sorted(set(old) & set(new)))
    return sorted(set(new) - set(old)), sorted(set(old) - set(new)), [d for d in changed if d]


# --------------------------------------------------------------------------
# The report


@dataclass
class Section:
    title: str              # "GripV (custom ergonomic shape)"
    panel: str = None       # the panel's name in the file
    note: str = ""          # shown instead of a panel name
    groups: dict = field(default_factory=dict)   # {preset group: [NodeDiff]}


@dataclass
class Report:
    old_label: str
    new_label: str
    note: str = ""          # replaces the comparison (first version, deleted file)
    sections: list = field(default_factory=list)
    modifiers: dict = field(default_factory=dict)   # {object: [NodeDiff]}
    meshes: list = field(default_factory=list)
    trees_added: list = field(default_factory=list)
    trees_removed: list = field(default_factory=list)
    trees: list = field(default_factory=list)       # [TreeDiff]
    old_trees: dict = field(default_factory=dict)
    new_trees: dict = field(default_factory=dict)
    versions: tuple = (None, None)

    @property
    def wiring_count(self):
        return len(self.trees) + len(self.trees_added) + len(self.trees_removed)


def panel_order(panel):
    keys = list(PANELS)
    return (keys.index(panel) if panel in keys else len(keys), panel)


def short_panel(panel):
    return PANELS[panel][0] if panel in PANELS else panel


def compare(old, new, old_label="old", new_label="new"):
    """Report between two parsed tracking files."""
    report = Report(old_label, new_label)
    old_inputs = old.get("tracked_inputs") or {}
    new_inputs = new.get("tracked_inputs") or {}

    per_panel = {}
    for panel in sorted(set(old_inputs) | set(new_inputs), key=panel_order):
        groups = group_by_first(diff_nodes(old_inputs.get(panel) or {}, new_inputs.get(panel) or {}))
        if groups:
            per_panel[panel] = groups

    # A group with the same change in several panels (the shared group 'global') is shown once.
    seen = defaultdict(list)
    for panel, groups in per_panel.items():
        for group, diffs in groups.items():
            seen[group].append((panel, diffs))
    shared, shared_panels = {}, []
    for group, entries in seen.items():
        if len(entries) > 1 and all(diffs == entries[0][1] for _panel, diffs in entries):
            shared[group] = entries[0][1]
            for panel, _diffs in entries:
                del per_panel[panel][group]
                if panel not in shared_panels:
                    shared_panels.append(panel)

    for panel, groups in per_panel.items():
        if groups and panel in PANELS:
            report.sections.append(Section("{} ({})".format(*PANELS[panel]), panel=panel, groups=groups))
        elif groups:
            report.sections.append(Section(show(panel), groups=groups))
    if shared:
        names = [short_panel(p) for p in sorted(shared_panels, key=panel_order)]
        note = "same change in both panels" if len(names) == 2 else "same change in each panel"
        report.sections.append(Section(" and ".join(names), note=note, groups=shared))

    # modifiers is {object: {modifier: entry}}: reported as object > modifier.
    old_mods = {obj: {"nodes": mods} for obj, mods in (old.get("modifiers") or {}).items()}
    new_mods = {obj: {"nodes": mods} for obj, mods in (new.get("modifiers") or {}).items()}
    report.modifiers = group_by_first(diff_nodes(old_mods, new_mods))

    report.meshes = diff_meshes(old.get("meshes") or {}, new.get("meshes") or {})
    report.old_trees = old.get("all_node_trees") or {}
    report.new_trees = new.get("all_node_trees") or {}
    report.trees_added, report.trees_removed, report.trees = diff_trees(report.old_trees, report.new_trees)
    report.versions = (old.get("version"), new.get("version"))
    return report


def snapshot_note(data):
    """One sentence about a whole tracking file, for its first version."""
    parts = []
    for panel, groups in sorted((data.get("tracked_inputs") or {}).items(), key=lambda i: panel_order(i[0])):
        values = sum(len(flatten(entry)) for entry in groups.values() if isinstance(entry, dict))
        parts.append(f"{short_panel(panel)}: {plural(len(groups), 'preset group')}, {plural(values, 'value')}")
    parts.append(plural(len(data.get("meshes") or {}), "mesh", "meshes"))
    parts.append(plural(len(data.get("all_node_trees") or {}), "node group"))
    return "First recorded version of tracking.json (" + "; ".join(parts) + ")."


def plural(n, word, words=None):
    return f"{n} {word if n == 1 else words or word + 's'}"


def summary_line(report):
    """One sentence counting what changed."""
    if report.note:
        return report.note
    c = Counter()
    sources = [(section.groups, PANEL_WORDS) for section in report.sections]
    for groups, words in sources + [(report.modifiers, MODIFIER_WORDS)]:
        for diffs in groups.values():
            for d in diffs:
                if d.kind in ("added", "removed"):
                    c[(words[len(d.path) > 1], d.kind)] += 1
                else:
                    c[(words[len(d.path) > 1], "renamed")] += d.kind == "renamed"
                    c.update(("input", change.kind) for change in d.changes)
    parts = [f"{plural(c[('input', 'changed')], 'value')} changed"] if c[("input", "changed")] else []
    for word in ("input", "node", "preset group", "modifier", "object"):
        for kind in ("added", "removed", "renamed"):
            if c[(word, kind)]:
                parts.append(f"{plural(c[(word, kind)], word)} {kind}")
    if not parts:
        if not (report.meshes or report.wiring_count or report.versions[0] != report.versions[1]):
            return "No changes in tracking.json."
        parts.append("no parameter changes")
    if report.meshes:
        parts.append(f"{plural(len(report.meshes), 'mesh', 'meshes')} changed")
    if report.wiring_count:
        parts.append(f"wiring changed in {plural(report.wiring_count, 'node group')}")
    text = ", ".join(parts)
    return text[0].upper() + text[1:] + "."


# --------------------------------------------------------------------------
# Wording shared by text and Markdown


def show(name):
    """A name as text, quoted when spaces would hide in it (trailing or double spaces)."""
    if name and name == " ".join(name.split()):
        return name
    return json.dumps(name, ensure_ascii=False)


def fmt_number(value):
    if isinstance(value, int):
        return str(value)
    text = f"{value:.4f}".rstrip("0").rstrip(".")
    return "0" if text == "-0" else text


def fmt(value):
    """A tracked value as short text. Strings are quoted so trailing spaces show ("low ")."""
    if isinstance(value, bool):
        return "on" if value else "off"
    if value is None:
        return "none"
    if is_number(value):
        return fmt_number(value)
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, list):
        return "[" + ", ".join(fmt(v) for v in value) + "]"
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def signed(number):
    return ("+" if number > 0 else "") + fmt_number(number if isinstance(number, int) else round(number, 4))


def delta(old, new):
    """The difference of two numbers or two vectors as text, or ''."""
    if is_number(old) and is_number(new):
        return signed(new - old)
    if isinstance(old, list) and isinstance(new, list) and len(old) == len(new) \
            and all(is_number(v) for v in old + new):
        axes = "XYZ" if len(old) == 3 else [f"[{i}]" for i in range(len(old))]
        return ", ".join(f"{axes[i]} {signed(b - a)}" for i, (a, b) in enumerate(zip(old, new)) if not same(a, b))
    return ""


def hint(path, change):
    return HINTS.get((path[-1], change.name), "")


def node_summary(d, words=PANEL_WORDS):
    """'removed node, 12 inputs' for an added or removed node or preset group."""
    what = ("new " if d.kind == "added" else "removed ") + words[len(d.path) > 1]
    if d.nodes:
        return f"{what}, {plural(d.nodes, 'node')}, {plural(len(d.values), 'value')}"
    return f"{what}, {plural(len(d.values), 'input')}"


def path_text(path, sep=" > "):
    return sep.join(show(p) for p in path)


def name_list(names, verbose, code=show):
    shown = names if verbose else names[:MAX_NAMES]
    text = ", ".join(code(n) for n in shown)
    return text + (f" and {len(names) - len(shown)} more" if len(names) > len(shown) else "")


def mesh_text(name, kind, code=show):
    note = MESH_NOTES.get(name)
    return f"{code(name)} was {kind}" + (f" ({note})" if note else "")


def tree_counts(diff):
    parts = []
    if diff.added:
        parts.append(f"{plural(len(diff.added), 'link')} added")
    if diff.removed:
        parts.append(f"{len(diff.removed)} removed" if diff.added else f"{plural(len(diff.removed), 'link')} removed")
    for links, word in ((diff.muted, "muted"), (diff.unmuted, "unmuted")):
        if links:
            parts.append(f"{plural(len(links), 'link')} {word}")
    if diff.relabeled:
        parts.append(f"{plural(len(diff.relabeled), 'node')} relabeled")
    return ", ".join(parts)


def wiring_lines(report, verbose, code=show):
    """(depth, text) lines of the node wiring summary. A raw link list only with verbose."""
    lines = []
    for title, trees, links in (("Node groups added", report.trees_added, report.new_trees),
                                ("Node groups removed", report.trees_removed, report.old_trees)):
        if trees:
            items = [f"{code(t)} ({plural(len(links.get(t) or []), 'link')})" for t in trees]
            lines.append((0, f"{title}: {name_list(items, verbose, str)}"))
    labels_only = []
    for diff in report.trees:
        if not diff.rewired and not verbose:
            labels_only.append(diff.name)
            continue
        lines.append((0, f"{code(diff.name)}: {tree_counts(diff)}"))
        if diff.linked_nodes:
            lines.append((1, f"now linked: {name_list(diff.linked_nodes, verbose, code)}"))
        if diff.unlinked_nodes:
            lines.append((1, f"no longer linked: {name_list(diff.unlinked_nodes, verbose, code)}"))
        if verbose:
            lines.extend((1, f"removed {code(link)}") for link in diff.removed)
            lines.extend((1, f"added {code(link)}") for link in diff.added)
            lines.extend((1, f"muted {code(link)}") for link in diff.muted)
            lines.extend((1, f"unmuted {code(link)}") for link in diff.unmuted)
            lines.extend((1, f"relabeled {code(a)} -> {code(b)}") for a, b in diff.relabeled)
    if labels_only:
        lines.append((0, f"Only node labels changed in {plural(len(labels_only), 'node group')}: "
                         + name_list(labels_only, verbose, code)))
    return lines


def version_line(report, arrow):
    old, new = report.versions
    if old == new:
        return ""
    return f"Format version {old} {arrow} {new}: some changes may come from the tracking add-on, not from the design."


# --------------------------------------------------------------------------
# Plain text


def change_text(change, path):
    name = show(change.name)
    if change.kind == "changed":
        text = f"{name}: {fmt(change.old)} -> {fmt(change.new)}"
        d = delta(change.old, change.new)
        text += f" ({d})" if d else ""
    elif change.kind == "added":
        text = f"{name}: new input, {fmt(change.new)}"
    elif change.kind == "removed":
        text = f"{name}: removed, was {fmt(change.old)}"
    else:
        text = f"{name}: probably renamed from {show(change.old_name)}, value {fmt(change.new)}"
    note = hint(path, change)
    return f"{text}  ({note})" if note else text


def group_text(group, diffs, verbose, words=PANEL_WORDS, indent="  "):
    """Lines for one preset group: its own changes first, then each node below it."""
    lines = [f"{indent}{show(group)}"]
    for d in diffs:
        depth = len(d.path) - 1
        pad = indent + "  " * depth
        if depth == 0:
            if d.kind in ("added", "removed"):
                lines[0] += f": {node_summary(d, words)}"
            elif d.kind == "renamed":
                lines[0] += f": probably renamed from {show(d.old_key)}"
        elif d.kind in ("added", "removed"):
            lines.append(f"{pad}{show(d.path[-1])}: {node_summary(d, words)}")
        elif d.kind == "renamed":
            lines.append(f"{pad}{show(d.path[-1])}: probably renamed from {show(d.old_key)}")
        else:
            lines.append(f"{pad}{show(d.path[-1])}")
        if d.kind in ("added", "removed"):
            if verbose:
                lines.extend(f"{pad}  {path_text(p + (label,))}: {fmt(v)}" for p, label, v in d.values)
        else:
            lines.extend(f"{pad}  {change_text(c, d.path)}" for c in d.changes)
    return lines


def render_text(report, verbose=False):
    lines = [f"tracking.json: {report.old_label} -> {report.new_label}", summary_line(report)]
    if report.note:
        return "\n".join(lines) + "\n"
    lines += [version_line(report, "->")] if version_line(report, "->") else []
    for section in report.sections:
        detail = f"panel {show(section.panel)}" if section.panel else section.note
        lines += ["", f"{section.title}, {detail}" if detail else section.title]
        for group, diffs in section.groups.items():
            lines += group_text(group, diffs, verbose)
    if report.modifiers:
        lines += ["", "Modifier inputs"]
        for obj, diffs in report.modifiers.items():
            lines += group_text(obj, diffs, verbose, MODIFIER_WORDS)
    if report.meshes:
        lines += ["", "Meshes"]
        lines += [f"  {mesh_text(name, kind)}" for name, kind in report.meshes]
    if report.wiring_count:
        lines += ["", "Node wiring"]
        lines += ["  " + "    " * depth + text for depth, text in wiring_lines(report, verbose)]
    return "\n".join(lines) + "\n"


# --------------------------------------------------------------------------
# Markdown


def md_code(text):
    """Inline code that is safe in a table cell: pipes escaped, backticks fenced."""
    text = str(text).replace("|", "\\|")
    if not text:
        return ""
    return f"`` {text} ``" if "`" in text else f"`{text}`"


def md_name(name):
    return md_code(show(name))


def md_text(text):
    """Plain text made safe for one Markdown line."""
    return re.sub(r"([\\`*_\[\]<>|#])", r"\\\1", text)


def md_change_row(change, node, path):
    if change.kind == "changed":
        row = [md_code(fmt(change.old)), md_code(fmt(change.new)), delta(change.old, change.new)]
    elif change.kind == "added":
        row = ["", md_code(fmt(change.new)), "new input"]
    elif change.kind == "removed":
        row = [md_code(fmt(change.old)), "", "removed"]
    else:
        row = [md_code(fmt(change.old)), md_code(fmt(change.new)),
               f"probably renamed from {md_name(change.old_name)}"]
    note = hint(path, change)
    if note:
        row[2] = f"{row[2]}, {note}" if row[2] else note
    return [node, md_name(change.name)] + row


def md_group_table(diffs, verbose, words=PANEL_WORDS):
    rows = []
    for d in diffs:
        below = d.path[1:]
        node = md_code(path_text(below, " › ")) if below else f"*({words[0]})*"
        if d.kind in ("added", "removed"):
            rows.append([node, "", "", "", node_summary(d, words)])
            if verbose:
                for p, label, v in d.values:
                    cell = md_code(fmt(v))
                    rows.append([md_code(path_text(below + p, " › ")) or node, md_name(label),
                                 cell if d.kind == "removed" else "", cell if d.kind == "added" else "", ""])
            continue
        if d.kind == "renamed":
            rows.append([node, "", "", "", f"probably renamed from {md_name(d.old_key)}"])
        rows.extend(md_change_row(c, node, d.path) for c in d.changes)
    lines = ["| Node | Input | Before | After | Change |", "| --- | --- | --- | --- | --- |"]
    return lines + ["| " + " | ".join(row) + " |" for row in rows]


def render_markdown(report, verbose=False, title=None, heading="###"):
    title = title or f"Parameter changes: {md_code(report.old_label)} → {md_code(report.new_label)}"
    lines = [f"{heading} {title}", "", summary_line(report)]
    if report.note:
        return "\n".join(lines) + "\n"
    sub = heading + "#"
    lines += ["", version_line(report, "→")] if version_line(report, "→") else []
    for section in report.sections:
        lines += ["", f"{sub} {section.title}"]
        if section.panel:
            lines += ["", f"Panel {md_code(section.panel)}."]
        elif section.note:
            lines += ["", section.note.capitalize() + "."]
        for group, diffs in section.groups.items():
            lines += ["", f"**{md_name(group)}**", ""] + md_group_table(diffs, verbose)
    if report.modifiers:
        lines += ["", f"{sub} Modifier inputs"]
        for obj, diffs in report.modifiers.items():
            lines += ["", f"**{md_name(obj)}**", ""] + md_group_table(diffs, verbose, MODIFIER_WORDS)
    if report.meshes:
        lines += ["", f"{sub} Meshes", ""]
        lines += [f"- {mesh_text(name, kind, md_name)}" for name, kind in report.meshes]
    if report.wiring_count:
        lines += ["", "<details>",
                  f"<summary>Node wiring: {plural(report.wiring_count, 'node group')} changed</summary>", ""]
        lines += ["  " * depth + "- " + text for depth, text in wiring_lines(report, verbose, md_name)]
        lines += ["", "</details>"]
    return "\n".join(lines) + "\n"


# --------------------------------------------------------------------------
# Loading versions of the file


@dataclass
class Version:
    label: str
    data: dict = None       # None: the file does not exist in this version


def parse(text, label):
    if text.startswith(LFS_POINTER):
        raise TrackingError(f"{label} is a Git LFS pointer, not tracking data")
    try:
        data = json.loads(text)
    except ValueError as e:
        raise TrackingError(f"{label} is not valid JSON: {e}")
    if not isinstance(data, dict):
        raise TrackingError(f"{label} is not a tracking file (expected a JSON object)")
    return data


def run_git(repo, args):
    try:
        return subprocess.run(["git", "-C", repo] + args, capture_output=True, text=True,
                              encoding="utf-8", errors="replace")
    except FileNotFoundError:
        raise TrackingError("git is not installed or not on PATH")


def find_repo():
    """The git work tree of the current folder, else the one this script is in."""
    for start in (os.getcwd(), os.path.dirname(os.path.abspath(__file__))):
        result = run_git(start, ["rev-parse", "--show-toplevel"])
        if result.returncode == 0:
            return result.stdout.strip()
    raise TrackingError("not inside a git repository (compare two files instead)")


def resolve(repo, ref):
    """Full hash of the commit ref names, or None."""
    result = run_git(repo, ["rev-parse", "--verify", "--quiet", ref + "^{commit}"])
    return result.stdout.strip() if result.returncode == 0 else None


def short(repo, commit):
    result = run_git(repo, ["rev-parse", "--short", commit])
    return result.stdout.strip() if result.returncode == 0 else commit[:7]


def load_commit(repo, ref, path, label=None):
    commit = resolve(repo, ref)
    if not commit:
        raise TrackingError(f"unknown revision '{ref}'")
    if label is None:
        abbrev = short(repo, commit)
        label = abbrev if commit.startswith(ref) else f"{ref} ({abbrev})"
    result = run_git(repo, ["show", f"{commit}:{path}"])
    if result.returncode != 0:
        return Version(label)   # the file does not exist in that commit
    return Version(label, parse(result.stdout, f"{path} in {label}"))


def load_parent(repo, ref, path):
    """The version before commit ref (its first parent); a missing one for a root commit."""
    commit = resolve(repo, ref)
    if not commit:
        raise TrackingError(f"unknown revision '{ref}'")
    parent = resolve(repo, commit + "^")
    if not parent:
        return Version("(nothing)")
    label = short(repo, parent) if commit.startswith(ref) else f"{ref}^ ({short(repo, parent)})"
    return load_commit(repo, parent, path, label)


def load_file(path):
    try:
        with open(path, encoding="utf-8") as f:
            return Version(path, parse(f.read(), path))
    except OSError as e:
        raise TrackingError(f"cannot read {path}: {e.strerror}")


def resolve_versions(specs, path):
    """(old Version, new Version) from the command-line versions."""
    if len(specs) > 2:
        raise TrackingError("give at most two versions")
    if len(specs) == 2:
        repo = None if all(os.path.isfile(s) for s in specs) else find_repo()
        return tuple(load_file(s) if os.path.isfile(s) else load_commit(repo, s, path) for s in specs)
    spec = specs[0] if specs else "HEAD"
    repo = find_repo()
    if os.path.isfile(spec):
        return load_commit(repo, "HEAD", path), load_file(spec)
    if "..." in spec:
        a, b = (side or "HEAD" for side in spec.split("...", 1))
        base = run_git(repo, ["merge-base", a, b])
        if base.returncode != 0:
            raise TrackingError(f"no common ancestor for '{spec}'")
        commit = base.stdout.strip()
        return load_commit(repo, commit, path, f"merge base {short(repo, commit)}"), load_commit(repo, b, path)
    if ".." in spec:
        a, b = (side or "HEAD" for side in spec.split("..", 1))
        return load_commit(repo, a, path), load_commit(repo, b, path)
    return load_parent(repo, spec, path), load_commit(repo, spec, path)


def build_report(old, new):
    """Report between two Versions; a missing file on one side gets a one-line note."""
    if old.data is None and new.data is None:
        raise TrackingError(f"no tracking file in {old.label} or in {new.label}")
    if old.data is None:
        return Report(old.label, new.label, note=snapshot_note(new.data))
    if new.data is None:
        return Report(old.label, new.label, note=f"tracking.json does not exist in {new.label}.")
    return compare(old.data, new.data, old.label, new.label)


# --------------------------------------------------------------------------
# Changelog


def log_commits(repo, path, count, rev_range):
    """[(hash, short hash, date, author, subject, first parent or '')], newest first."""
    args = ["log", "--format=%H%x1f%h%x1f%ad%x1f%an%x1f%s%x1f%P", "--date=short"]
    args += [f"-n{count}"] if count else []
    result = run_git(repo, args + [rev_range, "--", path])
    if result.returncode != 0:
        raise TrackingError(result.stderr.strip() or f"git log failed for '{rev_range}'")
    commits = []
    for line in result.stdout.splitlines():
        commit, abbrev, date, author, subject, parents = line.split("\x1f")
        commits.append((commit, abbrev, date, author, subject, parents.split()[0] if parents else ""))
    return commits


def render_log(repo, path, count, rev_range, markdown=False, verbose=False):
    """One report per commit that changed the file, newest first."""
    commits = log_commits(repo, path, count, rev_range)
    if not commits:
        return f"No commit in {rev_range} changed {path}.\n"
    out = []
    for commit, abbrev, date, author, subject, parent in commits:
        new = load_commit(repo, commit, path, abbrev)
        old = load_commit(repo, parent, path, short(repo, parent)) if parent else Version("(nothing)")
        report = build_report(old, new)
        if markdown:
            head, body = render_markdown(report, verbose, f"{md_code(abbrev)} {md_text(subject)}").split("\n", 1)
            since = f", compared with {md_code(old.label)}" if old.data is not None else ""
            out.append(f"{head}\n\n{md_text(author)}, {date}{since}\n{body}")
        else:
            body = render_text(report, verbose).split("\n", 1)[1].rstrip("\n")
            out.append(f"commit {abbrev}  {date}  {author}\n    {subject}\n\n"
                       + "\n".join("    " + line if line else "" for line in body.split("\n")) + "\n")
    return "\n".join(out)


# --------------------------------------------------------------------------


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Readable report of what changed in blender/tracking.json.",
        epilog="A VERSION is a git ref (HEAD~3, a commit, a branch) or a file. No version: the last "
               "commit. One ref: the change that commit made. A..B or two versions: from the first "
               "to the second. A...B: from the merge base, like a pull request. One file: from HEAD "
               "to that file.")
    parser.add_argument("versions", nargs="*", metavar="VERSION",
                        help="REF, A..B, A...B, OLD NEW or FILE (default: HEAD~1 vs HEAD)")
    parser.add_argument("--markdown", action="store_true",
                        help="write Markdown (for pull requests and GitHub job summaries)")
    parser.add_argument("--verbose", action="store_true",
                        help="also list the values of added and removed nodes and every changed link")
    parser.add_argument("--log", type=int, metavar="N",
                        help="one report per commit, for the last N commits that changed the file "
                             "(0: all); a VERSION range limits them, e.g. v1.0..HEAD")
    parser.add_argument("--path", default=TRACKING_PATH,
                        help=f"the tracking file inside the repository (default: {TRACKING_PATH})")
    args = parser.parse_args(argv)
    path = args.path.replace("\\", "/")      # git wants forward slashes, also on Windows

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")   # a Windows console cannot print every name
    try:
        if args.log is not None:
            if args.log < 0 or len(args.versions) > 1:
                raise TrackingError("--log takes a count of 0 or more and at most one revision range")
            text = render_log(find_repo(), path, args.log,
                              args.versions[0] if args.versions else "HEAD", args.markdown, args.verbose)
        else:
            report = build_report(*resolve_versions(args.versions, path))
            text = render_markdown(report, args.verbose) if args.markdown else render_text(report, args.verbose)
    except TrackingError as e:
        print(f"tracking_diff: {e}", file=sys.stderr)
        return 1
    sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
