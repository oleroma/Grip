"""Check the tooltip table of apply_tooltips.py against blender/tracking.json.

Plain Python, no Blender needed:

    python scripts/check_tooltips.py
    python scripts/check_tooltips.py --cleanup

It checks that every group and input in TOOLTIPS exists in tracking.json, and
prints for every tracked group how many of its inputs have a tooltip. An input
exists when tracking.json records a value for it, or when the group's links
(all_node_trees) read it from the Group Input node. Group names come from the
tracked node names: "screw parameters.001 (BACK)" is the group
"screw parameters".

--cleanup checks against the names as they would be after the planned typo
cleanup (wdith -> width, paramters -> parameters, double spaces, ...) and lists
the entries that then only match through their corrected spelling.

Exit status 1 when an entry is not found or a tracked input has no tooltip.
"""

import argparse
import importlib.util
import json
import re
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TRACKING = ROOT / "blender" / "tracking.json"
GROUP_INPUT_LINK = re.compile(r"\[Group Input(?:\.\d+)?\] (.+?)(?:\[\d+\])? -> ")


def load_table():
    """Import apply_tooltips.py with a stand-in for bpy and return the module."""
    sys.modules.setdefault("bpy", types.ModuleType("bpy"))
    path = Path(__file__).with_name("apply_tooltips.py")
    spec = importlib.util.spec_from_file_location("apply_tooltips", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def group_of(node_key, trees):
    """Group name of a tracked node, or None if all_node_trees has no such group."""
    name = re.sub(r" \(.*\)$", "", node_key)
    stripped = re.sub(r"\.(\d{3,}|\w+)$", "", name)
    # Strip first: "basic stick parameters.001" is a second node of
    # "basic stick parameters", although an older group has that name too.
    for candidate in (stripped, name):
        if candidate in trees:
            return candidate
    return None


def read_tracking(path):
    """Tracked inputs and linked group inputs: ({group: {input: [where]}}, {group: {input}})."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    trees = data["all_node_trees"]
    tracked, unknown = {}, []
    for panel, presets in data["tracked_inputs"].items():
        for preset, entry in presets.items():
            for input_name in entry.get("inputs", {}):
                tracked.setdefault(preset, {}).setdefault(input_name, []).append(f"{panel} > {preset}")
            for node_key, node in entry["nodes"].items():
                group = group_of(node_key, trees)
                if group is None:
                    unknown.append(f"{panel} > {preset} > {node_key}")
                    continue
                for input_name in node["inputs"]:
                    tracked.setdefault(group, {}).setdefault(input_name, []).append(f"{panel} > {preset} > {node_key}")
    linked = {}
    for group, links in trees.items():
        for link in links:
            match = GROUP_INPUT_LINK.match(link)
            if match:
                linked.setdefault(group, set()).add(match.group(1))
    return tracked, linked, unknown


def cleaned_up(tracked, linked, table):
    """tracked and linked with the names the planned typo cleanup would give."""
    def group(name):
        return table.corrected(name, table.GROUP_FIXES)

    def inputs(names):
        return {table.corrected(name, table.INPUT_FIXES): value for name, value in names.items()}

    new_tracked, new_linked = {}, {}
    for name, names in tracked.items():
        new_tracked.setdefault(group(name), {}).update(inputs(names))
    for name, names in linked.items():
        new_linked.setdefault(group(name), set()).update(inputs(dict.fromkeys(names)))
    return new_tracked, new_linked


def resolve_group(name, known, table):
    """The known group for a table key, exactly or by corrected spelling."""
    if name in known:
        return name
    fixed = table.corrected(name, table.GROUP_FIXES)
    matches = [group for group in known if table.corrected(group, table.GROUP_FIXES) == fixed]
    return matches[0] if len(matches) == 1 else None


def check(table, tracked, linked):
    """Compare TOOLTIPS with the tracked data. Returns the findings as lists."""
    known = set(tracked) | set(linked)
    stale, corrected, style = [], [], []
    covered = {}
    for group_name, tooltips in table.TOOLTIPS.items():
        group = resolve_group(group_name, known, table)
        if group is None:
            stale.append(f"group {group_name!r}")
            continue
        if group != group_name:
            corrected.append(f"group {group_name!r} -> {group!r}")
        names = set(tracked.get(group, {})) | linked.get(group, set())
        inputs = {name: [name] for name in names}
        for input_name, text in tooltips.items():
            if not text.strip() or "—" in text:
                style.append(f"{group_name} > {input_name!r}: empty or contains an em-dash")
            _, file_name = table.find_input(inputs, input_name, tooltips)
            if file_name is None:
                stale.append(f"{group_name} > {input_name!r}")
                continue
            covered.setdefault(group, set()).add(file_name)
            if file_name != input_name:
                corrected.append(f"{group_name} > {input_name!r} -> {file_name!r}")
    return stale, corrected, style, covered


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--cleanup", action="store_true", help="check against the names after the planned typo cleanup")
    parser.add_argument("--tracking", default=TRACKING, help="path of tracking.json")
    args = parser.parse_args(argv)

    table = load_table()
    tracked, linked, unknown = read_tracking(args.tracking)
    if args.cleanup:
        tracked, linked = cleaned_up(tracked, linked, table)
    stale, corrected, style, covered = check(table, tracked, linked)

    print("Tooltips vs tracking.json" + (" (names after the typo cleanup)" if args.cleanup else ""))
    print(f"\n{'group':40} {'covered':>9}  missing")
    total = with_tooltip = 0
    gaps = []
    for group in sorted(tracked, key=str.lower):
        names = tracked[group]
        done = covered.get(group, set()) & set(names)
        missing = sorted(set(names) - done)
        total += len(names)
        with_tooltip += len(done)
        gaps += [f"{group} > {name!r}" for name in missing]
        print(f"{group:40} {len(done):>4}/{len(names):<4}  {', '.join(map(repr, missing))}")
    entries = sum(len(tooltips) for tooltips in table.TOOLTIPS.values())
    print(f"\n{len(tracked)} tracked groups, {total} tracked inputs, {with_tooltip} with a tooltip.")
    print(f"{len(table.TOOLTIPS)} groups and {entries} entries in TOOLTIPS, {len(stale)} not found.")

    for title, lines in (
        ("Entries not found in tracking.json", stale),
        ("Tracked inputs without a tooltip", gaps),
        ("Matched through a corrected spelling", corrected),
        ("Style problems", style),
        ("Tracked nodes whose group is not in all_node_trees", unknown),
    ):
        if lines:
            print(f"\n{title} ({len(lines)}):")
            for line in lines:
                print("  " + line)
    return 1 if stale or gaps or style or unknown else 0


if __name__ == "__main__":
    sys.exit(main())
