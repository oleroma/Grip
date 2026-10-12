"""Merge predictions: BranchScope follows the branch rules of engine.walk_override_branch without enumerating
permutations, for the merge highlights and the upstream suggestions of the naming fields (ARCHITECTURE.md, Merge
Predictions)."""
from .nodes import clean_node_name
from .naming import SCOPE_KINDS, segment_tags, split_path_parts, split_tag_parts, split_value_tag_parts, value_parts
from .engine import MockInput, MockOverride, get_input_value, parse_sweep_values

# --- Merge predictions -------------------------------------------------------------------------------------------
# BranchScope mirrors walk_override_branch for the UI, without enumerating permutations. It records every folder and
# filename token that exists at a point of the override stack together with the branch context it was created in,
# so suggestions and merge highlights only offer names that can actually coexist with the merges made above a field.
#
# - Keys are (kind, name) with kind "dir" (folder) or "tag" (filename token).
# - A branch name is created by a value. Values of one input are alternatives: the names of different values (or
#   sweep steps) of the same input never appear in the same permutation, so they exclude each other. The folder and
#   the token of the *same* value do appear together. A name created by several inputs (e.g. "1" from two number
#   inputs) excludes nothing, since it can come from either.
# - Only the anchors typed in a value field (value_name_parts) merge; names derived from the value are new.
# - A context is the set of branch keys a block is merged into (plus what those names themselves require).
# - A name created inside a merged block exists only in that context, e.g. "X" made under a block merged into "A"
#   is never available inside a block merged into "C".

def block_parts(block, kind):
    """Folder names (sub_path) or filename tokens (tag) a node group / node block adds."""
    return split_path_parts(getattr(block, "sub_path", "")) if kind == "dir" else split_tag_parts(getattr(block, "tag", ""))

def _value_steps(ng_ptr, node, inp, val):
    """(MockInput, [values]) of one UI value: one value unless it is a sweep."""
    target = 'MODIFIER' if not node.name or node.name == "<Modifier Interface>" else 'NODE'
    tmp = MockInput(inp, val, is_temp=True)
    return tmp, parse_sweep_values(MockOverride(target, ng_ptr, node.name, [tmp]), tmp) if tmp.use_sweep else [get_input_value(tmp)]

def _value_step_names(ng_ptr, node, inp, val):
    """[{kind: (anchors, names)}] per step of one UI value (one step unless it is a sweep)."""
    tmp, steps = _value_steps(ng_ptr, node, inp, val)
    return [value_parts(tmp, v) for v in steps]

def _block_where(ng, node=None):
    return ng.group_name if node is None else f"{ng.group_name} › {clean_node_name(node.name) or 'Modifier'}"

def _block_desc(kind, ng, node=None):
    return f"{'Folder' if kind == 'dir' else 'Tag'} · {_block_where(ng, node)}"

def scope_dead(res):
    """Whether a merge result {kind: (hits, dead)} names a branch that cannot exist (the block / value never applies)."""
    return any(res[kind][1] for kind in res)

class BranchScope:
    MAX_WAYS = 64  # ways chain_states() / place() follow at most

    def __init__(self):
        # (kind, name) -> {"desc", "known": bool, "inst": [{"group", "alt", "reqs": frozenset, "pos": int}]}
        # "known": a branch name for the exporter (_known_branch_dirs), i.e. a name some value names. Missing from a
        #   branch, it makes an anchor dead there; a plain block folder / token is created anew instead.
        # "inst": every way the name exists (one per creating block / value step): the value that creates it
        #   (`group` is its input, `alt` the value; None for a block), the context keys it requires (`reqs`), its
        #   creation order (`pos`) and whether it can exist without an earlier instance (`base`). Names of one branch keep that order, and the exporter only merges a chain
        #   whose names appear in order (_place_dir_parts). `needs`: every key a branch with the instance has (`reqs`,
        #   the name itself and the value that makes it).
        # A context is a set of keys the branch contains: names (kind, name) and chosen values ("alt", group, alt).
        #   ("not", keys) says the branch lacks at least one of `keys`: a chain that creates a plain name anew only
        #   does so in branches without the instances it could have merged into (chain_states).
        #   ("any", rests) says the branch has every key of at least one of `rests` (frozensets of keys): a block or
        #   value that can be placed in several ways only exists in the branches of one of them (place).
        self.entries = {}
        self.seq = 0
        # Set when chain_states() dropped ways past MAX_WAYS: the ways left do not cover every branch
        self.cut = False
        # satisfiable() / _keys_fit() results, keyed with `seq`: new instances can make a context possible
        self._sat, self._fit = {}, {}
        # The node group block entered last, until close_group(): the instances of the names it creates and the
        # contexts its nodes apply in
        self._group = None

    def __contains__(self, key): return key in self.entries
    def desc(self, key): return self.entries[key]["desc"]
    def is_branch(self, key): return key in self.entries and self.entries[key]["known"]

    @staticmethod
    def _clash(a, b):
        """Two values of one input never coexist."""
        return a["group"] is not None and a["group"] == b["group"] and a["alt"] != b["alt"]

    def _fits_key(self, inst, key):
        """Whether the instance can exist in a branch that contains `key`."""
        if key[0] == "any": return any(all(self._fits_key(inst, k) for k in rest) for rest in key[1])
        if key[0] == "not": return not key[1] <= inst["needs"]
        if key[0] == "alt": return not (inst["group"] == key[1] and inst["alt"] != key[2])
        e = self.entries.get(key)
        return bool(e) and any(not self._clash(inst, j) for j in e["inst"] if j["base"])

    def _keys_fit(self, a, b, before):
        """Whether a key an instance required when it was made (at position `before`) fits a context key."""
        memo = (a, b, before, self.seq)
        if memo in self._fit: return self._fit[memo]
        if b[0] == "any": result = any(all(self._keys_fit(a, k, before) for k in rest) for rest in b[1])
        elif a[0] == "any": result = any(all(self._keys_fit(k, b, before) for k in rest) for rest in a[1])
        # A required absence only clashes with a context key that is all it excludes
        elif a[0] == "not": result = not a[1] <= {b}
        elif a[0] == "alt": result = self._fits_key({"group": a[1], "alt": a[2], "needs": frozenset((a,))}, b)
        else:
            e = self.entries.get(a)
            result = bool(e) and any(self._fits_key(i, b) for i in e["inst"] if i["base"] and i["pos"] < before)
        self._fit[memo] = result
        return result

    def _fits(self, inst, ctx):
        return all(self._fits_key(inst, k) for k in ctx) and             all(self._keys_fit(r, k, inst["pos"]) for r in inst["reqs"] for k in ctx)

    def candidates(self, key, ctx, after=0):
        """Instances of `key` that can exist in context `ctx` and come after position `after`."""
        e = self.entries.get(key)
        return [i for i in e["inst"] if i["pos"] > after and self._fits(i, ctx)] if e else []

    def available(self, key, ctx): return bool(self.candidates(key, ctx))

    def add(self, key, desc, ctx, group=None, alt=None, alive=True):
        """Record a name created in context `ctx`; with `group` it is a value's name (a branch name). The names of a
        block or value that never applies (`alive` False) never exist, but a value's names still are branch names:
        the exporter knows them, so anchoring to them is dead."""
        e = self.entries.setdefault(key, {"desc": desc, "known": False, "inst": []})
        if group is not None: e["known"] = True
        if not alive: return None
        self.seq += 1
        # An instance made inside a context that already has the name (a value's folder A inside a block merged into
        # A) only exists where an earlier one does: it can be merged into, but does not show the name can exist.
        reqs = frozenset(k for k in ctx if k != key)
        needs = reqs | {key} | ({("alt", group, alt)} if group is not None else set())
        inst = {"group": group, "alt": alt, "reqs": reqs, "needs": needs, "pos": self.seq, "base": key not in ctx}
        e["inst"].append(inst)
        return inst

    def satisfiable(self, ctx, budget=4000):
        """Whether one choice of values gives a branch with every key of `ctx`: each name through one of its instances
        (made before the instance that required it), each with what it requires in turn. _fits only compares keys in
        pairs and misses conflicts between three or more, e.g. a token B from input I0 or I1 next to names that need
        I0=A and I1=C. Past `budget` steps it gives up and says yes, so a prediction is never hidden by a guess.
        A ("not", keys) key fails a choice that gives every one of `keys`; an ("any", rests) key needs every key of
        one of `rests`."""
        memo = (frozenset(ctx), self.seq)
        if memo in self._sat: return self._sat[memo]
        steps = [budget]

        def holds(key, has):
            return key in has or key[0] == "any" and any(all(holds(k, has) for k in rest) for rest in key[1])

        def solve(goals, assign, done, absent):
            if not goals:
                if not absent: return True
                has = set(done | absent | {("alt", g, a) for g, a in assign.items()})
                # The choice also gives every name whose requirements are all there (the value I0=B makes its token B)
                grew = True
                while grew:
                    grew = False
                    for key, e in self.entries.items():
                        if key not in has and any(i["base"] and all(holds(k, has) for k in i["needs"] if k != key)
                                                  for i in e["inst"]):
                            has.add(key); grew = True
                return not any(all(holds(k, has) for k in n[1]) for n in absent)
            steps[0] -= 1
            if steps[0] < 0: return True
            (key, before), rest = goals[0], goals[1:]
            if key[0] == "not": return solve(rest, assign, done, absent | {key})
            if key[0] == "any":
                if key in done: return solve(rest, assign, done, absent)
                return any(solve(rest + [(k, before) for k in r], assign, done | {key}, absent) for r in key[1])
            if key[0] == "alt":
                chosen = assign.get(key[1], key[2])
                return chosen == key[2] and solve(rest, {**assign, key[1]: key[2]}, done, absent)
            if key in done: return solve(rest, assign, done, absent)
            e = self.entries.get(key)
            if not e: return False
            for i in e["inst"]:
                if not i["base"] or i["pos"] >= before: continue
                a = assign
                if i["group"] is not None:
                    if assign.get(i["group"], i["alt"]) != i["alt"]: continue
                    a = {**assign, i["group"]: i["alt"]}
                if solve(rest + [(r, i["pos"]) for r in i["reqs"]], a, done | {key}, absent): return True
            return False

        result = self._sat[memo] = solve([(k, float("inf")) for k in ctx], {}, frozenset(), frozenset())
        return result

    def chain_states(self, kind, parts, ctx):
        """Every way the chain of names `parts` (split into tokens, see segmentation) can be placed in context `ctx`,
        like _place_dir_parts does in each branch: [(ctx, cursor, merged)] with the context the way requires, the
        position of its last merged name and per name (name, whether it merged). Empty when the chain never applies;
        then the second value is the name it got stuck on."""
        states = [(frozenset(ctx), 0, ())]
        for p in parts:
            key = (kind, p)
            branch = self.is_branch(key)
            nxt = {}
            for c, cur, merged in states:
                found = self.candidates(key, c, cur)
                # A name merges into one of its instances, which brings the branches it requires (_merged): a plain
                # name too, so 'Y/Y' only merges into a second Y made under I0=C together with I0=C. A branch name
                # must merge.
                for i in found:
                    k = self._merged(key, i)
                    if (c | k, i["pos"]) not in nxt and self.satisfiable(c | k): nxt[(c | k, i["pos"])] = merged + ((p, True),)
                # A plain folder / token is created anew where the branch has none of its instances. An instance whose
                # requirements the context already has is surely there. Created anew, the branch lacks each instance:
                # the chain 'x/A' on the path 'A/x' cannot go on to merge into A.
                if not branch and not any(i["reqs"] <= c for i in found):
                    c2 = c | {("not", i["reqs"]) for i in found}
                    if c2 == c or self.satisfiable(c2): nxt.setdefault((c2, cur), merged + ((p, False),))
            if not nxt: return [], p
            if len(nxt) > self.MAX_WAYS: self.cut = True
            states = [(c, cur, merged) for (c, cur), merged in list(nxt.items())[:self.MAX_WAYS]]
        return states, None

    def segmentation(self, kind, parts, ctx):
        """Split a chain into names like the exporter does (segment_tag, _place_dir_parts): a tag chain splits at '_'
        with the longest tokens that can exist in `ctx` (the branch's own spelling); when that leaves a name that
        cannot, with the longest recorded tokens. A folder chain is already split."""
        if kind != "tag": return list(parts)
        local = segment_tags(parts, lambda n: self.available((kind, n), ctx))
        if all(self.available((kind, n), ctx) for n in local): return local
        return segment_tags(parts, lambda n: (kind, n) in self.entries)

    def chain_states_any(self, kind, parts, ctx):
        """chain_states() for a chain not split into names yet (see segmentation)."""
        return self.chain_states(kind, self.segmentation(kind, parts, ctx), ctx)

    def place(self, chains, ctx):
        """Place the chains of one block or value together, like the exporter does in each branch: [(kind, names)],
        its folder names, then its tokens. Every way to place a chain goes on into the next, so they must all fit one
        branch (a folder chain using the 1 of input I0 and a tag that needs another value of I0 never do).

        Returns (new_ctx, {kind: (hits, dead)}, {kind: fresh}): `hits` merge into existing names, `dead` the branch
        name a chain that never applies gets stuck on, `fresh` the names it creates, `new_ctx` the branches it is
        placed in (see join)."""
        self.cut = False
        states = [(frozenset(ctx), {})]  # (context, {kind: ((name, merged), ...)})
        for kind, parts in chains:
            nxt, stuck = [], None
            for c, merged in states:
                found, at = self.chain_states_any(kind, parts, c)
                if not found and stuck is None: stuck = at
                nxt += [(c2, {**merged, kind: m}) for c2, _cur, m in found]
            if not nxt:
                res = {k: ([], []) for k, _ps in chains}
                res.update({k: ([p for p, m in ms if m], []) for k, ms in states[0][1].items()})
                res[kind] = ([], [stuck])
                return frozenset(ctx), res, {}
            if len(nxt) > self.MAX_WAYS: self.cut = True
            states = nxt[:self.MAX_WAYS]
        first = states[0][1]
        res = {k: ([p for p, m in first[k] if m], []) for k, _ps in chains}
        fresh = {k: [p for p, m in first[k] if not m] for k, _ps in chains}
        return self.join([c for c, _m in states], not self.cut), res, fresh

    @staticmethod
    def join(ctxs, complete=True):
        """One context for the branches of several ways (contexts `ctxs`): the keys every way requires, plus
        ("any", rests) with what each way requires beyond them. Values of a node 'B/B' placed through I0=B and I1=B
        or through I0=B and I3=B never apply together with I1=C and I3=C; the keys every way shares (I0=B) do not
        show that. A way that requires no more than the shared keys makes `rests` pointless. With ways dropped
        (`complete` False) the others do not cover every branch, so only the shared keys are kept."""
        ctxs = set(ctxs)
        common = frozenset.intersection(*ctxs)
        rests = {c - common for c in ctxs}
        rests = frozenset(r for r in rests if not any(o < r for o in rests))
        return common | {("any", rests)} if complete and len(rests) > 1 else common

    def enter_block(self, block, ctx, ng, node=None, alive=True):
        """Context inside a node group / node block (its sub-folder, then its tag), recording its new names.
        Returns (ctx, {kind: (hits, dead)}).

        A node group's names only go into the branches where one of its nodes applies: walk_override_branch adds them
        with the first such node. Until close_group() they exist wherever the group fits, so its nodes and values
        merge into them; then they are narrowed to the contexts its nodes apply in. A node group block closes the
        one before."""
        if node is None: self.close_group()
        ctx, res, fresh = self.place([(kind, block_parts(block, kind)) for kind in SCOPE_KINDS], ctx)
        # Recorded once both fields are placed: a block whose tag never applies does not create its folders either
        alive = alive and not scope_dead(res)
        made = [((kind, n), self.add((kind, n), _block_desc(kind, ng, node), ctx, alive=alive))
                for kind, names in fresh.items() for n in names]
        if node is None: self._group = {"inst": [(key, inst) for key, inst in made if inst], "ctxs": []}
        elif alive and self._group: self._group["ctxs"].append(ctx)
        return ctx, res

    def close_group(self):
        """End the node group block entered last (see enter_block): each name it creates gets one instance per
        context its nodes apply in, at the group's position (before the names of its nodes). Without a node that can
        apply, its names never exist."""
        g, self._group = self._group, None
        if not g or not g["inst"]: return
        own = {key for key, _inst in g["inst"]}
        # A node's context can hold the group's own names (merged as branch names); they come with the node anyway.
        # A context that holds another adds nothing: the names exist wherever the smaller one does.
        reqs = list(dict.fromkeys(frozenset(c - own) for c in g["ctxs"]))
        reqs = [r for r in reqs if not any(o < r for o in reqs)]
        self.seq += 1
        for key, inst in g["inst"]:
            e = self.entries[key]
            at = next(n for n, i in enumerate(e["inst"]) if i is inst)
            e["inst"][at:at + 1] = [{**inst, "reqs": r, "needs": r | {key}} for r in reqs]

    def resolve_value(self, anchors, ctx):
        """place() for the anchors of one value ({kind: names}, see value_field_anchors) in context `ctx`; names
        derived from the value are always new. Returns (new_ctx, {kind: (hits, dead)})."""
        return self.place([(kind, anchors[kind]) for kind in SCOPE_KINDS], ctx)[:2]

    def add_input(self, ng, ng_ptr, node, inp, ctx, alive=True):
        """Record the folders and tokens an input's values create inside context `ctx` (`alive` False: the block
        around the input never applies)."""
        group = (ng.group_name, clean_node_name(node.name), inp.name)
        descs = {"dir": f"Branch · {ng.group_name} › {inp.name}", "tag": f"Name branch · {ng.group_name} › {inp.name}"}
        # Values of one input are alternatives: each resolves against what exists before the input, never against
        # its siblings (like the exporter's known names, _known_branch_dirs), so resolve them all before recording.
        steps = []
        for v_idx, val in enumerate(inp.values):
            for s_idx, parts in enumerate(_value_step_names(ng_ptr, node, inp, val)):
                steps.append(((v_idx, s_idx), parts) + self.place([(kind, parts[kind][0]) for kind in SCOPE_KINDS], ctx))
        for alt, parts, v_ctx, res, fresh in steps:
            v_ctx = v_ctx | {("alt", group, alt)}  # what this value creates only exists with it
            v_alive = alive and not scope_dead(res)
            for kind in SCOPE_KINDS:
                if v_alive:
                    # The exporter knows every name a value names, merged ones too (value_branch_names)
                    for n in res[kind][0]: self.entries[(kind, n)]["known"] = True
                    for n in fresh[kind]: self.add((kind, n), descs[kind], v_ctx, group, alt)
                else:
                    for n in self.segmentation(kind, parts[kind][0], ctx): self.add((kind, n), descs[kind], v_ctx, group, alt, False)
                # The value's own folder / token is always new, even when it equals an anchor ('B_' on the value B)
                for n in parts[kind][1]: self.add((kind, n), descs[kind], v_ctx, group, alt, v_alive)

    def suggestions(self, kind, states, exclude=frozenset(), fits=lambda ctx: True):
        """{name: description} of the names of `kind` a chain can merge into next, for its placements `states` (see
        chain_states): they can exist in a placement's context, come after its last merged name, and leave a context
        `fits` accepts (the field's other chain must still fit). Keys in `exclude` are left out. In stack order."""
        return {n: e["desc"] for (k, n), e in self.entries.items()
                if k == kind and (k, n) not in exclude
                and any(fits(c2) for c, cur, _m in states for c2 in self._merge_ctxs((k, n), c, cur))}

    def _merge_ctxs(self, key, ctx, cursor):
        """The contexts a chain placed with context `ctx` up to `cursor` can have after merging into `key` next: the
        branches with one of its instances (a plain name is created anew in the others, see chain_states)."""
        out = []
        for i in self.candidates(key, ctx, cursor):
            c = ctx | self._merged(key, i)
            if self.satisfiable(c): out.append(c)
        return out

    def _merged(self, key, inst):
        """Context keys of a branch that merges into instance `inst` of `key`: the branches it requires, and for a
        branch name the name and the value that makes it. A plain name (made by a block) exists wherever its
        requirements hold, like chain_states assumes, so contexts never hold one: they say which branches a field is
        in, and the search leaves those out."""
        if not self.is_branch(key): return inst["reqs"]
        return inst["reqs"] | {key} | ({("alt", inst["group"], inst["alt"])} if inst["group"] is not None else set())

OTHER_KIND = {"dir": "tag", "tag": "dir"}

def naming_completions(scope, ctx, kind, text, current, other_parts, multi_part, quote=lambda name: name):
    """[(chain, description)] completing the chain of folder names (kind "dir") or filename tokens (kind "tag") `text`
    typed in a section with upstream names that can exist in this branch, to merge into. `scope` / `ctx` are the
    BranchScope and context at the field (upstream_scope), `current` the section's stored typed names, and
    `other_parts` the names of the other section, which every suggestion must still fit: a block's or value's folder
    and tag are placed in the same branch. `quote` writes a suggested name as it is typed in the field.

    The suggestion completes the last '\\'- or '/'-separated name (in a tag also '_'-separated) inside the branch
    chosen so far, so 'C\\' offers 'C\\2', 'C\\3', ... but not 'C\\A' (A and C are alternatives of the same input).
    `multi_part` is False for a value section: its chains always end in the separator the value follows ('\\', '_'),
    so the caller writes the value after them. A folder typed with '/' keeps '/'. Once the separator is typed, the next
    link of the chain is offered too: 'B\\' offers 'B\\' and 'B\\1\\', 'B\\2\\', ...; tag 'B_' offers 'B_' and 'B_1_',
    'B_2_', ... (a tag chain is split at '_')."""
    split = split_path_parts if kind == "dir" else split_tag_parts if multi_part else split_value_tag_parts
    other = OTHER_KIND[kind]
    marks = "" if multi_part else ("\\/" if kind == "dir" else "_")
    seps = "/\\_" if kind == "tag" else "/\\"
    typed_mark = ""
    if text[-1:] and text[-1] in marks:
        typed_mark, text = text[-1], text[:-1]
    mark = typed_mark or marks[:1]
    # Opening a field that holds one name lists its alternatives; one that ends in the mark ('A_') goes on with the
    # next link of the chain ('A_C_', 'A_D_') instead
    if text + typed_mark == current and not typed_mark and not any(c in text for c in seps): text = ""
    def fits(c): return not other_parts or bool(scope.chain_states_any(other, other_parts, c)[0])

    def merged_states(prefix):
        """Ways to place the chain typed so far where every name of it merges: only such a chain is completed (after a
        name that does not merge, or a chain that never applies, a suggestion would not merge as a whole)."""
        if not prefix: return [(ctx, 0, ())]
        states = scope.chain_states_any(kind, split(prefix), ctx)[0]
        return [st for st in states if all(m for _p, m in st[2]) and fits(st[0])]

    def complete(text):
        # Complete after the last separator whose prefix merges; '_' may also be part of a name ('a_b'), so a prefix
        # that does not merge falls back to an earlier separator
        for cut in sorted((i for i, c in enumerate(text) if c in seps), reverse=True) + [-1]:
            prefix, query = text[:cut + 1], text[cut + 1:]
            states = merged_states(prefix)
            if states: break
        # Only names the chain can reach next, in its order; the branches the field is already in are left out
        names = scope.suggestions(kind, states, exclude=ctx, fits=fits)
        q = query.lower()
        out = [(prefix + quote(name) + mark, desc) for name, desc in names.items() if not q or q in name.lower()]
        # Text typed after the merged chain that names nothing upstream ('A_B_custom_') keeps the chain on offer, to
        # go back to it
        if prefix and query and not out: out.append((prefix if not multi_part else prefix[:-1], "Merged so far"))
        return out

    items = complete(text)
    if typed_mark and text: items += complete(text + typed_mark)  # the next link of the chain
    return items
