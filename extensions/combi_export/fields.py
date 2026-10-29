"""Syntax of the override table's text fields: a value field ('\\B\\15\\_x_15') read into a value and its naming
templates and written back, a block naming field ('\\C\\2\\_B'), and the naming of new values (ARCHITECTURE.md,
Expression Fields). Text only: the property callbacks that use it are in props."""
import math
import re

from .common import MAX_SWEEP_STEPS
from .naming import SCOPE_KINDS, VALUE_SLOT, value_parts

# --- Value fields ----------------------------------------------------------------------------------------------------
# The override table edits a value and its naming in one text field (BatchSTLValue.expr). '\' starts the folder
# section and '_' the filename section, and the value is written where it goes in the names (see VALUE_SLOT):
#   15            the value only
#   \15           a folder per value: 15/                  _15          a filename token per value: Box_15
#   \big          folder big (the name replaces the value)  _big         token big (the value is not shown)
#   \15_mm        one folder joining value and text         _15_mm       token 15_mm
#   \size_15      size_15/
#   \B\15         folder B, then a folder per value         _B_15        token B, then the value: Box_B_15
#   \15\_15       folder and token ('\' closes the folder)  \big\_15     folder big, token 15
#   \0:1:5  _{a, b}  \*   sweeps: numbers start:step:count, strings {a, b}, menus and booleans *
# - Any other name is typed text: it merges into an upstream folder / token of that name (B in \B\15, big in \big).
# - Without a value written before the sections (15\big also works), the value is read from them (_infer_value): the
#   value the field holds where it is written; a value written in its place instead ('\15' -> '\16' is the value 16),
#   unless that name exists upstream ('\A' merges into A); a sweep or a value with a space; else the value stays and
#   every name is typed.
# - A section that ends in its separator goes on with the value: \B\ = \B\15, _B_ = _B_15, 15\ = \15, 15_ = _15.
#   The search offers each upstream name ending in its separator, so Tab completes it and the next one can be typed.
# - In a folder section '_' belongs to the name (\15_mm), except right after '\' or a space: there the filename
#   section starts. In the value part '_' starts it after the longest text that is a value: '15_big' is 15 with the
#   token big, while the string 'a_b' or the menu item 'Mode_A' stay whole. A space before '_' ends the value: 'a _b'.
# - Double quotes make text literal, never the value or a mark: \"15"\15 is folder 15, then the value 15. In a name
#   not quoted whole, quotes around '{' or '}', or around a '_' that starts a folder name, only keep them chars:
#   \a"{"b can be the value a{b, \"_"x_mm the value _x joined with mm, \"_"a_15 the name _a joined with 15.
# Node group and node blocks use the sections without a value (BatchSTLNodeGroup.naming): \C\2\_B.

def lex_expr(text):
    """[(char, quoted, position in text)] of a field. '""' inside quotes is a quote; a quote left open runs to the end."""
    chars, quoted, i = [], False, 0
    while i < len(text):
        c = text[i]
        if c == '"':
            if quoted and text[i + 1:i + 2] == '"':
                chars.append(('"', True, i))
                i += 1
            else: quoted = not quoted
        else: chars.append((c, quoted, i))
        i += 1
    return chars

def bare(ch, marks): return not ch[1] and ch[0] in marks
def is_space(ch): return not ch[1] and ch[0].isspace()

def expr_strip(chars):
    """Lexed chars without the unquoted spaces at their edges."""
    start, end = 0, len(chars)
    while start < end and is_space(chars[start]): start += 1
    while end > start and is_space(chars[end - 1]): end -= 1
    return chars[start:end]

def expr_text(chars): return "".join(ch[0] for ch in chars)

def _outside_braces(chars):
    """Per lexed char: whether it is outside a '{...}' group (a string sweep), where marks and separators count."""
    out, depth = [], 0
    for ch in chars:
        if bare(ch, "{"): depth += 1
        out.append(depth == 0)
        if bare(ch, "}") and depth: depth -= 1
    return out

def _value_cut(region, value_ok):
    """Length of the value at the start of `region` (lexed chars before any section): the longest text ending at a bare
    '_' (or all of it) that `value_ok` accepts. A quoted value ends at its closing quote ('"a_b"_x') and a string sweep
    '{...}' at its closing brace."""
    free = _outside_braces(region)
    cuts = [k for k in range(len(region) - 1, 0, -1) if free[k] and bare(region[k], "_")]
    cuts = [k for k in cuts if region[k - 1][1]] + [len(region)] + [k for k in cuts if not region[k - 1][1]]
    if bare(region[0], "{"):
        # The group closes where the chars after it are outside braces again
        close = next((k for k in range(len(region)) if bare(region[k], "}") and (k + 1 == len(region) or free[k + 1])), None)
        if close is not None and (close + 1 == len(region) or bare(region[close + 1], "_")): cuts.insert(0, close + 1)
    for cut in cuts:
        if value_ok(expr_strip(region[:cut])): return cut
    return len(region)

def split_field(chars, value_ok=None):
    """(value chars, [(kind, chars, mark index, closed)]) of a lexed field: its value part, then each section with its
    text (edge spaces stripped), the index of its mark in `chars` and, for a folder section, whether a filename section
    closes it ('\\B\\_x': its last '\\' is no separator then). `value_ok(chars)` tells whether text is a value (see
    the comment above); without it (a block field) text before the first mark is a folder section (mark index None).
    Raises ValueError for a section given twice."""
    n, free = len(chars), _outside_braces(chars)
    def mark(k, marks): return free[k] and bare(chars[k], marks)
    def tag_start(k, body, closers):
        # A '_' starts the filename section at the start of the field or a section, after a space, or after the '\'
        # that closes a folder section
        if not mark(k, "_"): return False
        p = k - 1
        while p >= body and is_space(chars[p]): p -= 1
        return p < body or p < k - 1 or mark(p, closers)

    i = 0
    while i < n and is_space(chars[i]): i += 1
    value, sections, k = [], [], i
    if value_ok is not None:
        j = i
        while j < n and not mark(j, "\\") and not tag_start(j, i, ""): j += 1
        cut = _value_cut(chars[i:j], value_ok) if j > i else 0
        value, k = expr_strip(chars[i:i + cut]), i + cut
    implicit = value_ok is None and i < n and not mark(i, "\\_")
    while k < n:
        if is_space(chars[k]) and not implicit:
            k += 1
            continue
        if implicit: kind, start, body = "dir", None, k
        elif mark(k, "\\"): kind, start, body = "dir", k, k + 1
        elif mark(k, "_"): kind, start, body = "tag", k, k + 1
        else: raise ValueError("text between sections")
        implicit, k = False, body
        if kind == "dir":
            while k < n and not tag_start(k, body, "\\/"): k += 1
        else:
            while k < n and not mark(k, "\\"): k += 1
        if any(s[0] == kind for s in sections): raise ValueError("a section is given twice")
        sections.append((kind, expr_strip(chars[body:k]), start, kind == "dir" and k < n))
    return value, sections

_NAME_ERRORS = re.compile(r'[<>:"/\\|?*\x00-\x1f\s]')

def _typed_text(chars, seps=""):
    """Text of typed names (anything but the value). A name is a file name: no space and none of <>:"/\\|?*. `seps`
    may stand between names (bare)."""
    for ch in chars:
        if ch[0] in seps and not ch[1]: continue
        if _NAME_ERRORS.search(ch[0]): raise ValueError(f"a name cannot hold {ch[0]!r}")
    return expr_text(chars)

def _split_bare(chars, seps):
    """[(start, end)] of the stretches of `chars` between bare separators (outside braces)."""
    free = _outside_braces(chars)
    spans, s = [], 0
    for k, ch in enumerate(chars):
        if free[k] and bare(ch, seps):
            spans.append((s, k))
            s = k + 1
    spans.append((s, len(chars)))
    return spans

def _dir_names(chars):
    """Lexed folder names of a folder section."""
    return [nm for nm in (expr_strip(chars[s:e]) for s, e in _split_bare(chars, "\\/")) if nm]

def _is_open(kind, chars, closed):
    """Whether a section ends in its separator, so the value comes after its names ('\\B\\', '_B_')."""
    return bool(chars) and not closed and bare(chars[-1], "\\/" if kind == "dir" else "_/")

def _literal(chars, s, e):
    """Whether chars[s:e] of a name hold quoted text, which is never the value. Quotes around marks in a name that is
    not quoted whole only keep them chars: '{' and '}' ('\\a"{"b' can be the value a{b), and a '_' that starts the
    name ('\\"_"x_mm' can be the value _x joined with mm), see _name_value."""
    quoted = [k for k in range(s, e) if chars[k][1]]
    if not quoted: return False
    if all(ch[1] for ch in chars): return True
    return not all(chars[k][0] in "{}" or (k == 0 and chars[k][0] == "_") for k in quoted)

def _value_runs(chars, accept, seps="_"):
    """[(start, end)] of the runs of whole pieces of `chars` (between bare `seps`) without quoted text (_literal) that
    `accept` takes: the places a value can be written at."""
    spans = _split_bare(chars, seps)
    runs = []
    for a in range(len(spans)):
        for b in range(a, len(spans)):
            s, e = spans[a][0], spans[b][1]
            if e > s and not _literal(chars, s, e) and accept(chars[s:e]): runs.append((s, e))
    return runs

def _value_places(sections):
    """[(kind, chars, separators)] where a value can be written, in the order the value is looked for: the folder
    names from the last one, then the filename section. A section that ends in its separator holds typed names only."""
    places = []
    for kind, chars, _start, closed in sorted(sections, key=lambda s: s[0] != "dir"):
        if _is_open(kind, chars, closed): continue
        if kind == "dir": places += [(kind, nm, "_") for nm in reversed(_dir_names(chars))]
        elif chars: places.append((kind, chars, "_/"))
    return places

def _can_be_typed(chars, seps):
    """Whether text can be a typed name (see _typed_text): a sweep or a value with a space cannot."""
    try: _typed_text(chars, seps.replace("_", ""))
    except ValueError: return False
    return True

def _slot_shape(kind, template):
    """What stays the same when the value written in a name is edited in place: the folder name holding the value (with
    the text around it) and the folders after it, or the text after the value token. None without the value."""
    template = template or VALUE_SLOT
    if VALUE_SLOT not in template: return None
    if kind == "dir":
        names = template.split("/")
        return tuple(names[next(k for k, n in enumerate(names) if VALUE_SLOT in n):])
    return template.split(VALUE_SLOT, 1)[1]

def _slot_run(chars, is_value, seps):
    """(start, end) of the last place in `chars` the value is written at, preferring one that leaves typed text
    around it; None when there is none."""
    runs = sorted(_value_runs(chars, is_value, seps), reverse=True)
    def typeable(run):
        try: _typed_text(chars[:run[0]], "/"); _typed_text(chars[run[1]:], "/")
        except ValueError: return False
        return True
    return next((r for r in runs if typeable(r)), runs[0] if runs else None)

def section_template(kind, chars, closed, is_value):
    """Template (see VALUE_SLOT) of a value field's section: the value goes in the last place `is_value(chars)` takes;
    every other name is typed. An empty section is the value alone, an open one ends with it ('\\B\\'). Raises
    ValueError for a typed name that cannot be a file name."""
    if kind == "dir":
        names = _dir_names(chars)
        if _is_open(kind, chars, closed): return "/".join([_typed_text(nm) for nm in names] + [VALUE_SLOT])
        out, found = [], False
        for nm in reversed(names):
            run = None if found else _slot_run(nm, is_value, "_")
            if run:
                out.append(_typed_text(nm[:run[0]]) + VALUE_SLOT + _typed_text(nm[run[1]:]))
                found = True
            else: out.append(_typed_text(nm))
        return "/".join(reversed(out)) if out else VALUE_SLOT
    if not chars: return VALUE_SLOT
    if _is_open(kind, chars, closed): return _typed_text(chars, "_/") + VALUE_SLOT
    run = _slot_run(chars, is_value, "_/")
    if not run: return _typed_text(chars, "_/")
    return _typed_text(chars[:run[0]], "_/") + VALUE_SLOT + _typed_text(chars[run[1]:], "_/")

def parse_number(text, override_type):
    """The number in a FLOAT / INT field. ValueError for other text, and for nan and inf: a socket set to them gives no
    usable geometry, and no file should be named after them."""
    value = float(text) if override_type == 'FLOAT' else int(text)
    if not math.isfinite(value): raise ValueError(f"{text} is not a finite number")
    return value

def sweep_numbers(start, step, count, override_type):
    """The values of a number sweep start:step:count (floats rounded to 8 decimals)."""
    if override_type == 'FLOAT': return [round(start + i * step, 8) for i in range(count)]
    return [int(start + i * step) for i in range(count)]

def string_sweep_values(sweep_range):
    """The strings of a string sweep '{a, b}' (the text inside the braces), blanks left out."""
    return [s.strip() for s in sweep_range.split(",") if s.strip()]

def steps_differ(values):
    """Whether every step of a sweep is a different, finite value. A step of 0 (or one lost in the rounding) repeats
    the start, and every repeat would write the same files again."""
    return len(set(values)) == len(values) and all(math.isfinite(v) for v in values if isinstance(v, float))

def number_sweep_values(start, step, count, override_type):
    """The values of the number sweep with the texts start:step:count. ValueError when they are not valid: numbers (see
    parse_number), a count from 1 to MAX_SWEEP_STEPS, and values that all differ (steps_differ)."""
    count = int(count)
    if not 1 <= count <= MAX_SWEEP_STEPS: raise ValueError(f"a sweep has 1 to {MAX_SWEEP_STEPS} steps")
    values = sweep_numbers(parse_number(start, override_type), parse_number(step, override_type), count, override_type)
    if not steps_differ(values): raise ValueError("every step of a sweep must be a different finite value")
    return values

def read_expr_value(chars, override_type, items=None):
    """{property: value} the value text (lexed chars) sets on a BatchSTLValue. Raises ValueError when it does not fit
    the input type. `items` are the menu items, when they are known (a menu value is then one of them)."""
    text = expr_text(chars)
    if not text: raise ValueError("no value")
    if override_type in ('FLOAT', 'INT'):
        if "_" in text: raise ValueError("'_' starts a filename section")  # int() and float() would accept '1_0'
        if ":" in text:
            pieces = [p.strip() for p in text.split(":")]
            if len(pieces) != 3: raise ValueError("a number sweep is start:step:count")
            number_sweep_values(*pieces, override_type)
            return {"use_sweep": True, "sweep_start": pieces[0], "sweep_step": pieces[1], "sweep_count": pieces[2]}
        parse_number(text, override_type)
        return {"use_sweep": False, "value_string": text}
    if override_type == 'STRING':
        if len(chars) > 1 and bare(chars[0], "{") and bare(chars[-1], "}"):
            inner = expr_text(chars[1:-1])
            strings = string_sweep_values(inner)
            if not strings: raise ValueError("an empty list")
            if not steps_differ(strings): raise ValueError("a list holds a string twice")
            return {"use_sweep": True, "sweep_range": inner}
        return {"use_sweep": False, "value_string": text}
    if override_type in ('BOOLEAN', 'MENU'):
        if len(chars) == 1 and bare(chars[0], "*"): return {"use_sweep": True}
        if override_type == 'BOOLEAN': items = ['True', 'False']
        if items:
            match = text if text in items else next((i for i in items if i.lower() == text.lower()), None)
            if match is None: raise ValueError(f"'{text}' is not an item")
            text = match
        return {"use_sweep": False, "value_menu": text}
    raise ValueError("unsupported socket type")

def same_value(override_type, a, b):
    if override_type in ('FLOAT', 'INT'):
        try: return float(a) == float(b)
        except ValueError: pass
    return a == b

def same_fields(override_type, a, b):
    """Whether two values in read_expr_value's form are the same value."""
    if a["use_sweep"] != b["use_sweep"]: return False
    if a["use_sweep"]:
        if override_type in ('FLOAT', 'INT'): return all(same_value(override_type, a[k], b[k]) for k in ("sweep_start", "sweep_step", "sweep_count"))
        if override_type == 'STRING': return [s.strip() for s in a["sweep_range"].split(",")] == [s.strip() for s in b["sweep_range"].split(",")]
        return True
    if override_type in ('BOOLEAN', 'MENU'): return a["value_menu"].lower() == b["value_menu"].lower()
    return same_value(override_type, a["value_string"], b["value_string"])

def value_fields(val, override_type):
    """A stored value in read_expr_value's form, or None when it is blank."""
    if val.use_sweep:
        if override_type in ('FLOAT', 'INT'): return {"use_sweep": True, "sweep_start": val.sweep_start, "sweep_step": val.sweep_step, "sweep_count": val.sweep_count}
        if override_type == 'STRING': return {"use_sweep": True, "sweep_range": val.sweep_range}
        return {"use_sweep": True}
    prop = "value_menu" if override_type in ('BOOLEAN', 'MENU') else "value_string"
    text = getattr(val, prop)
    return {"use_sweep": False, prop: text} if text else None

def fields_text(fields, override_type):
    """A value (read_expr_value's form) as written in a field, without quotes."""
    if fields["use_sweep"]:
        if override_type in ('FLOAT', 'INT'): return f"{fields['sweep_start']}:{fields['sweep_step']}:{fields['sweep_count']}"
        if override_type == 'STRING': return "{" + fields["sweep_range"].strip() + "}"
        return "*"
    return fields.get("value_menu", fields.get("value_string", ""))

def _value_readers(override_type, items):
    """(read, readable) of the value text of an input: read(chars) parses it (ValueError when it does not fit)."""
    def read(chars): return read_expr_value(chars, override_type, items)
    def readable(chars):
        try: read(chars)
        except ValueError: return False
        return True
    return read, readable

def _infer_value(sections, read, matches, stored, taken, stored_templates=None, upstream=None):
    """The value (read_expr_value's form) a field without a value part holds (see the comment above lex_expr):
    1. the stored value, where it is written;
    2. a value written where the stored value was (same text around it, same names after it, see _slot_shape; a missing
       section counts as the value alone), unless that name exists upstream (`upstream(kind, name)`): typed, it merges;
    3. text that cannot be a typed name (a sweep, a value with a space), or before the value is set (`stored` None) any
       text that is a value: the last such name, the longest;
    4. else the stored value stays and every name is typed.
    Values another value of the input has (`taken`) are skipped. Raises ValueError when there is no value."""
    places = _value_places(sections)
    if stored is not None and any(_value_runs(ch, lambda r: matches(r, stored), seps) for _k, ch, seps in places): return stored
    def free(chars):
        try: fields = read(chars)
        except ValueError: return None
        return None if taken and taken(fields) else fields
    def runs_in(chars, seps):
        # The rest of the name must be typed text: in '\\mode_*' the value is the sweep '*', not the item 'mode'
        runs = [(s, e) for s, e in _value_runs(chars, lambda r: free(r) is not None, seps)
                if _can_be_typed(chars[:s], seps) and _can_be_typed(chars[e:], seps)]
        return sorted(runs, key=lambda r: (r[1] - r[0], r[0]), reverse=True)

    if stored is not None and stored_templates is not None:
        for kind, chars, _start, closed in sections:
            want = _slot_shape(kind, stored_templates.get(kind) or VALUE_SLOT)
            if want is None or _is_open(kind, chars, closed): continue
            for _kind, place, seps in (p for p in places if p[0] == kind):
                for s, e in runs_in(place, seps):
                    fields = free(place[s:e])
                    try: template = section_template(kind, chars, closed, lambda r: matches(r, fields))
                    except ValueError: continue
                    if _slot_shape(kind, template) != want: continue
                    if upstream and upstream(kind, expr_text(place if kind == "dir" else place[s:e])): continue
                    return fields
    for _kind, place, seps in places:
        runs = [(s, e) for s, e in runs_in(place, seps) if stored is None or not _can_be_typed(place[s:e], seps)]
        if runs: return free(place[runs[0][0]:runs[0][1]])
    if stored is not None: return stored
    raise ValueError("no value")

def parse_value_field(text, override_type, items=None, stored=None, taken=None, stored_templates=None, upstream=None):
    """(fields, {kind: template or None}) of a value field (see the comment above lex_expr): the value in
    read_expr_value's form, and its folder / tag templates (None: no section). `stored` / `stored_templates` are the
    value and naming the field held (value_fields, value_specs), `taken(fields)` whether another value of the input has
    that value, `upstream(kind, name)` whether a folder / token of that name exists upstream (see _infer_value). Raises
    ValueError for text that does not fit the input, a name that cannot be a file name, or a section given twice."""
    read, readable = _value_readers(override_type, items)
    def matches(chars, fields):
        try: return same_fields(override_type, read(chars), fields)
        except ValueError: return False
    value, sections = split_field(lex_expr(text), readable)
    fields = read(value) if value else _infer_value(sections, read, matches, stored, taken, stored_templates, upstream)
    templates = dict.fromkeys(SCOPE_KINDS)
    for kind, chars, _start, closed in sections:
        templates[kind] = section_template(kind, chars, closed, lambda r: matches(r, fields))
    return fields, templates

def _quote(text):
    return '"' + text.replace('"', '""') + '"'

def _render_typed(text, seps, lead=False, always=False):
    """Typed names (separated by bare `seps`) as written in a section: a name is quoted when `always` says so (True, or
    a test of the name), when it would not read back as typed (a space, a quote or a backslash), or as the first of a
    folder name when it would start the filename section ('_') or a sweep ('{')."""
    out, first = [], lead
    for piece in re.split("([" + re.escape(seps) + "])", text) if seps else [text]:
        if piece and piece in seps: out.append(piece)
        elif piece:
            needs = (always(piece) if callable(always) else always) or any(c.isspace() or c in '"\\' for c in piece) or (first and piece[0] in "_{")
            out.append(_quote(piece) if needs else piece)
        first = False
    return "".join(out)

def _render_section(kind, template, vtext, always=False, short=False):
    """Section text (after its mark) of a template with the value written in its place; `always` as in _render_typed.
    `short`: a value alone or at the end is left out (an empty or open section, see the comment above lex_expr), for a
    value that cannot be written in a name."""
    template = template or VALUE_SLOT
    if kind == "dir":
        names = template.split("/")
        if short and names[-1] == VALUE_SLOT:
            return "\\".join(_render_typed(n, "", True, always) for n in names[:-1]) + ("\\" if len(names) > 1 else "")
        out = []
        for name in names:
            if VALUE_SLOT not in name:
                out.append(_render_typed(name, "", True, always))
                continue
            prefix, suffix = name.split(VALUE_SLOT, 1)
            # The '_' next to the value stays bare: it separates the value from the text around it
            pre = _render_typed(prefix[:-1], "_", True, always) + "_" if prefix.endswith("_") else _render_typed(prefix, "_", True, always)
            post = "_" + _render_typed(suffix[1:], "_", False, always) if suffix.startswith("_") else _render_typed(suffix, "_", False, always)
            name = pre + vtext + post
            # A '_' starting the name is quoted, else it would start the filename section (see _literal)
            if name.startswith("_"): name = '"_' + name[2:] if name[1:2] == '"' else _quote("_") + name[1:]
            out.append(name)
        return "\\".join(out)
    if VALUE_SLOT not in template: return _render_typed(template, "_/", False, always)
    prefix, suffix = template.split(VALUE_SLOT, 1)
    if short and not suffix: return _render_typed(prefix, "_/", False, always)
    return _render_typed(prefix, "_/", False, always) + vtext + _render_typed(suffix, "_/", False, always)

def _name_value(vtext, fields):
    """The value as written in a name: '{' and '}' of a value that is no sweep are quoted, else they would start one
    (see _literal)."""
    if fields is None or fields["use_sweep"]: return vtext
    return re.sub(r"[{}]+", lambda m: _quote(m.group()), vtext)

def _quote_value_part(vtext, fields, override_type, always=False):
    """The value written before the sections, quoted when it would not read back as typed."""
    if fields["use_sweep"] or override_type in ('FLOAT', 'INT'): return vtext
    if always or not vtext or vtext != vtext.strip() or vtext.startswith("_") or vtext == "*" or any(c in vtext for c in '"\\{}'):
        return _quote(vtext)
    return vtext

_compose_memo = {}

def compose_value_field(fields, templates, override_type, items=None, current=None, upstream=None):
    """Text of a value field (see the comment above lex_expr): the first of a few ways to write the value and its
    templates that parse_value_field reads back as the same. The naming alone comes first: the value written in the
    names where it has a place, and not shown at all when the names replace it ('\\big'). `current` is the
    (value, templates) the field holds when the text is typed into it (by default the result itself, as the field
    shows it), `upstream` as in parse_value_field: a search suggestion must read back as offered when it is picked."""
    templates = {kind: templates.get(kind) for kind in SCOPE_KINDS}
    if fields is None: vtext = ""
    else: vtext = fields_text(fields, override_type)
    key = None
    if current is None and upstream is None:
        key = (override_type, tuple(sorted(fields.items())) if fields else None, tuple(templates.values()), tuple(items) if items else None)
        text = _compose_memo.get(key)
        if text is not None: return text
    stored, stored_templates = current if current is not None else (fields, templates)

    def sections(always=False, short=False, value=_name_value(vtext, fields)):
        d, t = templates["dir"], templates["tag"]
        out = "\\" + _render_section("dir", d, value, always, short) if d is not None else ""
        if t is not None: out += ("\\" if d is not None and not out.endswith("\\") else "") + "_" + _render_section("tag", t, value, always, short)
        return out
    norm = lambda tpl: None if tpl is None else tpl or VALUE_SLOT
    def reads_back(text):
        try: f, tps = parse_value_field(text, override_type, items, stored, None, stored_templates, upstream)
        except ValueError: return False
        return same_fields(override_type, f, fields) and all(norm(tps[k]) == norm(templates[k]) for k in SCOPE_KINDS)

    candidates = []
    # Typed names that replace the value hide it: the value is written first then ('15\\big'), so the field shows it
    hidden = fields is not None and any(t is not None for t in templates.values()) and \
        not any(VALUE_SLOT in norm(t) for t in templates.values() if t is not None)
    if fields is not None:
        if any(t is not None for t in templates.values()) and not hidden:
            # Typed names that could be read as the value go in quotes: the last one ('\\A\\1\\"3"'), every one, then all
            # names. The test is asked once per name, left to right.
            readable = _value_readers(override_type, items)[1]
            seen = []
            candidates.append(sections(always=lambda name: seen.append(readable(lex_expr(name))) or False))
            def nth(wanted):
                calls = iter(range(len(seen)))
                return lambda name: next(calls, -1) in wanted
            last = max((k for k, ok in enumerate(seen) if ok), default=None)
            if last is not None: candidates.append(sections(always=nth({last})))
            candidates += [sections(always=nth({k for k, ok in enumerate(seen) if ok})), sections(always=True)]
        for always in (False, True):
            head = _quote_value_part(vtext, fields, override_type, always)
            for short in (False, True):
                secs = sections(always, short)
                candidates.append(head + secs)
                if secs.startswith("_"): candidates.append(head + " " + secs)
    text = next((c for c in candidates if reads_back(c)), None)
    if text is None: text = (_quote_value_part(vtext, fields, override_type) if fields else "") + sections(short=True)
    if key is not None:
        if len(_compose_memo) > 20000: _compose_memo.clear()
        _compose_memo[key] = text
    return text

def value_specs(val):
    """{kind: template or None} of a value's folder and tag naming (None: turned off), see VALUE_SLOT."""
    return {"dir": (val.dir_tag or VALUE_SLOT) if val.use_dir else None, "tag": (val.tag or VALUE_SLOT) if val.use_tag else None}

def value_expr(val, override_type, items=None):
    return compose_value_field(value_fields(val, override_type), value_specs(val), override_type, items)

# --- Block naming ----------------------------------------------------------------------------------------------------
# A node group / node row has one naming field with the sections of a value field and no value: '\C\2' folders C/2,
# '_B' token B, '\C\2\_B' both. Text without a mark is a folder ('C/2').

def _block_name_text(chars, seps=""):
    """Text of the names typed in a block field, which has no value a space could belong to: a space inside a name is
    not allowed and becomes '_' (quoted or not). A space before '_' or '\\' is no part of a name, see split_field."""
    return _typed_text([("_", True, ch[2]) if ch[0] == " " else ch for ch in chars], seps)

def parse_block_naming(text):
    """(sub_path, tag) of a block naming field. Raises ValueError for a name that cannot be a file name or a section
    given twice."""
    sub_path, tag = "", ""
    for kind, chars, _start, _closed in split_field(lex_expr(text))[1]:
        if kind == "dir": sub_path = "/".join(_block_name_text(nm) for nm in _dir_names(chars))
        else: tag = _block_name_text(chars, "_/").strip("_")
    return sub_path, tag

def compose_block_naming(sub_path, tag):
    """Text of a block naming field."""
    names = [n for n in re.split(r"[\\/]", sub_path) if n]
    for always in (False, True):
        text = "\\" + "\\".join(_render_typed(n, "", True, always) for n in names) if names else ""
        if tag: text += ("\\" if names else "") + "_" + _render_typed(tag, "_/", False, always)
        try:
            if parse_block_naming(text) == ("/".join(names), tag): return text
        except ValueError: pass
    return text

# --- New values ------------------------------------------------------------------------------------------------------
# A new input starts with a plain value ('15'): one value applies to every export and needs no folder or token. Once
# the input permutes (a second value, or a sweep), values without naming would all write the same file, so they get
# a folder per value ('\15', '\16') or the naming the input already uses ('_15' gives '_16').
FOLDER_PER_VALUE = {"dir": VALUE_SLOT, "tag": None}

def set_value_specs(val, specs):
    """Write a value's folder and tag naming ({kind: template or None}, see value_specs)."""
    val.use_dir, val.dir_tag = specs["dir"] is not None, specs["dir"] or ""
    val.use_tag, val.tag = specs["tag"] is not None, specs["tag"] or ""

def has_naming(val): return val.use_dir or val.use_tag

def names_each_value(val):
    """True when the value's naming gives each value its own folder or token ('\\15', '\\B\\15', '_x_15'); a typed
    name alone ('\\big') or no naming gives every value the same path."""
    return any(names for _anchors, names in value_parts(val, "x").values())

def add_value(values):
    """A new plain value of an input."""
    val = values.add()
    val.use_dir = False  # the RNA default stays True: .blend files and older presets do not store unedited fields
    return val

def name_permutations(values, idx):
    """Name values[idx], a value that just made its input permute (added next to other values, or turned into a sweep).
    While every value is plain, all of them get a folder per value. Otherwise a plain values[idx] takes the naming of
    the last other value that names each value, else a folder per value; naming already set is kept."""
    if not any(has_naming(v) for v in values):
        for v in values: set_value_specs(v, FOLDER_PER_VALUE)
        return
    if has_naming(values[idx]): return
    template = next((v for i, v in reversed(list(enumerate(values))) if i != idx and names_each_value(v)), None)
    set_value_specs(values[idx], value_specs(template) if template else FOLDER_PER_VALUE)
