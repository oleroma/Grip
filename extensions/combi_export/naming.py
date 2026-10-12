"""File and folder names: sanitizing, value naming templates (VALUE_SLOT), splitting tags into tokens, and assembling
the folders and file name of an exported file (ARCHITECTURE.md, Filename Assembly)."""
import os
import re
import sys

# Spaces are not allowed in names: they become '_' like the characters a file name cannot hold
_INVALID_NAME_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f ]')
# Device names Windows reserves (COM¹ etc. with superscript digits too), also with any extension: 'CON.stl', 'nul.txt'
_WINDOWS_RESERVED = {"con", "prn", "aux", "nul"} | {port + n for port in ("com", "lpt") for n in "0123456789¹²³"}

def sanitize_name(text):
    """Make text safe to use inside a single file or folder name on every OS."""
    s = _INVALID_NAME_CHARS.sub("_", str(text))
    if s.split('.')[0].lower() in _WINDOWS_RESERVED:
        s = f"_{s}"
    return s

def sanitize_whole_name(text):
    """A whole file-safe folder name or file name stem: edge spaces and dots dropped (Windows drops them itself), then
    sanitized, so the reserved-name check sees the final name ('CON ' is the device CON)."""
    return sanitize_name(str(text).strip(" ."))

def underscore_spaces(text):
    """A name field's text without spaces, as the names will be written: a space inside a name becomes '_'. Spaces at
    the edges and around a '/' or '\\' only separated names, so they are dropped (sanitize_whole_name does the same)."""
    return re.sub(r" *([\\/]) *", r"\1", str(text).strip(" ")).replace(" ", "_")

def split_path_parts(path_text):
    """Split a user-typed sub-path into safe folder names; empty, '.' and '..' parts are dropped."""
    if not path_text: return []
    parts = (sanitize_whole_name(p) for p in re.split(r"[\\/]", path_text))
    return [p for p in parts if p]

def clash_key(path):
    """Key for output-path collision checks; Windows and macOS file systems are case-insensitive by default."""
    norm = os.path.normpath(path)
    return norm.casefold() if sys.platform in ("win32", "darwin") else norm

# --- Value naming ----------------------------------------------------------------------------------------------------
# A value's folder and filename naming are templates (BatchSTLValue.dir_tag / tag, DATA_VERSION 3): the names the
# value adds, with VALUE_SLOT where the value goes. Folder names are separated by '/', filename tokens by '_' (or '/').
#   folder  '*'         15/                       tag  '*'        Box_15
#   folder  'big'       big/  (replaces it)       tag  'big'      Box_big
#   folder  'B/*'       B/15/                     tag  'B_*'      Box_B_15
#   folder  'size_*'    size_15/                  tag  '*_mm'     Box_15_mm
#   folder  '*_mm/x'    15_mm/x/
# The names typed before the value are anchors: one that exists upstream merges into it (_place_dir_parts). The value
# and what follows it are always new. An empty template is the value alone (fields that were never edited).
VALUE_SLOT = "*"

# The two kinds of names: folders ("dir") and filename tokens ("tag")
SCOPE_KINDS = ("dir", "tag")

def value_name_parts(val, template, kind):
    """(anchors, names) the folder template (kind "dir") or filename-tag template (kind "tag") of a value gives, see
    VALUE_SLOT. `anchors` are the names typed before the value: one that is already in the branch merges into it (see
    _place_dir_parts). `names` are the value's own folder / token (with the text around the value in that name) and
    the folders after it. They are always new: two independent inputs that happen to share a value (1, True, a menu
    item) must multiply, not merge into each other. A template without the value only has anchors (they replace it).
    A tag anchor may hold '_' ('B_2', split into a chain by segment_tag)."""
    template = template or VALUE_SLOT
    if kind == "dir":
        parts = template.split("/")
        slot = next((i for i, p in enumerate(parts) if VALUE_SLOT in p), None)
        if slot is None: return split_path_parts(template), []
        prefix, suffix = parts[slot].split(VALUE_SLOT, 1)
        name = value_name(val, kind, prefix, suffix)
        return split_path_parts("/".join(parts[:slot])), ([name] if name else []) + split_path_parts("/".join(parts[slot + 1:]))
    at = template.find(VALUE_SLOT)
    if at < 0: return split_value_tag_parts(template), []
    name = value_name(val, kind, "", template[at + 1:])
    return split_value_tag_parts(template[:max(at - 1, 0)]), [name] if name else []

def value_name(val, kind, prefix="", suffix=""):
    """File-safe folder name (kind "dir") or filename token of a value, between `prefix` and `suffix`."""
    name = prefix + (f"{val:.10g}" if isinstance(val, float) else str(val).replace(" ", "_")) + suffix
    return sanitize_whole_name(name) if kind == "dir" else sanitize_name(name)

def legacy_naming_template(spec, kind):
    """Template (see VALUE_SLOT) of a value's folder / tag field as stored before DATA_VERSION 3: blank = the value,
    'x' replaces it, folder 'B\\' (or 'B/') and tag 'B_' = B, then the value, folder 'size_' = one folder 'size_15'."""
    spec = spec.replace(VALUE_SLOT, "_")  # an invalid file name character, which names turned into '_' anyway
    if kind == "tag": return spec + VALUE_SLOT if not spec or spec.endswith("_") else spec
    if spec.endswith("_"):
        parts = split_path_parts(spec)
        prefix = parts.pop() if parts else ""
        return "/".join(parts + [prefix + VALUE_SLOT])
    if not spec or spec[-1] in "\\/": return "/".join(split_path_parts(spec) + [VALUE_SLOT])
    return "/".join(split_path_parts(spec)) or "."  # names that are all dropped ('.') give no folder, not the value

def split_value_tag_parts(text):
    """Split a value tag field into filename tokens: '/' separates tokens. Unlike split_tag_parts, '_' at the edges is
    kept, so a token like 'x_' (made by the value 'x_') can be named."""
    if not text: return []
    parts = (sanitize_name(p.strip(" ")) for p in re.split(r"[\\/]", text))
    return [p for p in parts if p]

def segment_tag(name, is_known):
    """Split a typed token at '_' into a chain of tokens: 'B_2_X' -> ['B', '2', 'X'], so a tag merges into branch B,
    then into its branch 2, then adds X. Longest known tokens win: with a token 'a_b' upstream, 'a_b_X' is
    ['a_b', 'X'], and 'x_' (field 'x__') stays one token when it is known."""
    pieces = name.split("_")
    out, i = [], 0
    while i < len(pieces):
        j = len(pieces)
        while j > i + 1 and not is_known("_".join(pieces[i:j])): j -= 1
        token = "_".join(pieces[i:j])
        if token: out.append(token)
        i = j
    return out

def segment_tags(parts, is_known):
    return [t for p in parts for t in segment_tag(p, is_known)]

def value_parts(inp, val):
    """{kind: (anchors, names)} of one value step, honouring the folder / tag toggles."""
    return {kind: value_name_parts(val, getattr(inp, field), kind) if getattr(inp, use) else ([], [])
            for kind, use, field in (("dir", "use_dir", "dir_tag"), ("tag", "use_tag", "tag"))}

def value_field_anchors(inp):
    """{kind: anchors} of a value. Anchors only depend on the fields, never on the value itself."""
    return {kind: anchors for kind, (anchors, _names) in value_parts(inp, "").items()}

def split_tag_parts(text):
    """Split a literal tag field into filename tokens: '/' separates tokens, edge spaces and '_' are dropped."""
    if not text: return []
    parts = (sanitize_name(p).strip(" _") for p in re.split(r"[\\/]", text))
    return [p for p in parts if p]

# --- Export paths -----------------------------------------------------------------------------------------------------

def join_name_segments(segments):
    """Concatenate (names, is_fixed) segments of folders or filename tokens. Fixed segments come from plain fields
    (preset prefix, collection / object sub-folder or tag) that the override walker does not see, so a fixed name equal
    to its neighbour collapses into it. Two neighbouring override names stay: the walker already merged what merges,
    and A=1, B=1 must give 1/1, not 1."""
    out, out_fixed = [], []
    for names, fixed in segments:
        for n in names:
            if out and out[-1] == n and (fixed or out_fixed[-1]): continue
            out.append(n); out_fixed.append(fixed)
    return out

def format_export_filename(bl_obj_name, obj_tag, col_use_tag, col_tag, tags_by_level=None):
    """Object name followed by every filename token in hierarchy order:
    Global overrides, Preset overrides, Collection tag, Collection overrides, Object tag, Object overrides."""
    if tags_by_level is None: tags_by_level = {}
    tokens = join_name_segments([
        (tags_by_level.get("GLOBAL", []), False),
        (tags_by_level.get("PRESET", []), False),
        (split_tag_parts(col_tag) if col_use_tag else [], True),
        (tags_by_level.get("COLLECTION", []), False),
        (split_tag_parts(obj_tag), True),
        (tags_by_level.get("OBJECT", []), False),
        (tags_by_level.get("NONE", []), False),
    ])
    safe_name = sanitize_whole_name(bl_obj_name)
    return safe_name + "".join(f"_{t}" for t in tokens) + ".stl"

def build_export_dir_parts(preset_prefix, col_sub_path, obj_sub_path, paths_by_level=None):
    if paths_by_level is None: paths_by_level = {}
    return join_name_segments([
        (paths_by_level.get("GLOBAL", []), False),
        (split_path_parts(preset_prefix), True),
        (paths_by_level.get("PRESET", []), False),
        (split_path_parts(col_sub_path), True),
        (paths_by_level.get("COLLECTION", []), False),
        (split_path_parts(obj_sub_path), True),
        (paths_by_level.get("OBJECT", []), False),
        (paths_by_level.get("NONE", []), False),
    ])
