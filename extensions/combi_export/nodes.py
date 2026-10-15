"""Reading node trees and Geometry Nodes modifiers: interface sockets, modifier inputs, menu items, the nodes and sockets
an override can target, and socket defaults."""
import contextlib
import re

import bpy

from .common import bump_revision

def clean_node_name(name):
    if not name: return ""
    return name.split(" [")[0].strip()

def find_interface_input(node_group, socket_name):
    """The node group's interface input socket named `socket_name` (older API: node_group.inputs), or None."""
    if not node_group: return None
    if hasattr(node_group, "interface"):
        for item in node_group.interface.items_tree:
            if getattr(item, "item_type", "") == 'SOCKET' and getattr(item, "in_out", "INPUT") == 'INPUT' and item.name == socket_name:
                return item
    elif hasattr(node_group, "inputs"):
        return node_group.inputs.get(socket_name)
    return None

def get_modifier_socket_identifier(node_group, socket_name):
    item = find_interface_input(node_group, socket_name)
    return item.identifier if item else None

def get_modifier_socket_default(node_group, socket_name):
    return getattr(find_interface_input(node_group, socket_name), "default_value", None)

# Menu items come from scanning node trees, which the panels would otherwise repeat several times per menu value on
# every redraw. Inside cached_menu_items() the results are reused; node trees cannot change during that scope.
_menu_items_cache = None

@contextlib.contextmanager
def cached_menu_items():
    global _menu_items_cache
    if _menu_items_cache is not None:  # nested: the outer scope owns the cache
        yield
        return
    _menu_items_cache = {}
    try: yield
    finally: _menu_items_cache = None

def get_menu_switch_items(node_group, node_name, input_name):
    """Item names of the menu behind a menu socket. The returned list may be shared: do not modify it."""
    if _menu_items_cache is None: return _scan_menu_switch_items(node_group, node_name, input_name)
    key = (getattr(node_group, "name_full", None), node_name, input_name)
    items = _menu_items_cache.get(key)
    if items is None: items = _menu_items_cache[key] = _scan_menu_switch_items(node_group, node_name, input_name)
    return items

def _scan_menu_switch_items(node_group, node_name, input_name):
    if not node_group: return []
    if not node_name or node_name == "<Modifier Interface>":
        items = modifier_menu_items(node_group, input_name)
        return items if items is not None else _linked_menu_switch_items(node_group.nodes, input_name)
    target_n = node_group.nodes.get(clean_node_name(node_name))
    if not target_n: return []
    if target_n.type == 'MENU_SWITCH' and hasattr(target_n, 'enum_items'):
        return [getattr(item, 'identifier', getattr(item, 'name', '')) for item in target_n.enum_items]
    sock = target_n.inputs.get(input_name)
    items = socket_menu_items(target_n, sock) if sock else None
    if items is None and target_n.type == 'GROUP' and getattr(target_n, 'node_tree', None):
        items = _linked_menu_switch_items(target_n.node_tree.nodes, input_name)
    return items or []

def _linked_menu_switch_items(nodes, input_name):
    """Items of a Menu Switch fed directly by the group input `input_name` (no reroutes, no nested groups)."""
    for node in nodes:
        if node.type == 'MENU_SWITCH' and hasattr(node, 'enum_items'):
            for sock in node.inputs:
                for link in sock.links:
                    if link.from_node.type == 'GROUP_INPUT' and link.from_socket.name == input_name:
                        return [getattr(item, 'identifier', getattr(item, 'name', '')) for item in node.enum_items]
    return []

def modifier_menu_items(node_group, input_name):
    """Items of a menu on the modifier interface, read from a modifier that uses the group: the interface socket does
    not list them, the modifier input does (also through reroutes and nested groups). None when no object uses it."""
    ident = get_modifier_socket_identifier(node_group, input_name)
    if not ident: return None
    for obj in bpy.data.objects:
        for mod in obj.modifiers:
            if mod.type == 'NODES' and mod.node_group == node_group:
                prop_input = modifier_input(mod, ident)
                if prop_input is not None:
                    return [e.identifier for e in prop_input.bl_rna.properties["value"].enum_items]
    return None

# Last items found per node menu socket, for draw code (see socket_menu_items).
_socket_menu_memo = {}

def socket_menu_items(node, sock):
    """Items of a node's menu socket (built-in nodes, group nodes). Blender has no API that lists them, but assigning
    an unknown name is rejected, without changing anything, by an error that lists them. Draw code may not write
    data, so it gets the last list found (the UI cache rebuild refreshes it), or None."""
    if sock.type != 'MENU': return None
    key = (node.id_data.name_full, node.name, sock.identifier)
    try: sock.default_value = "\x01"
    except TypeError as e:
        listed = re.search(r"not found in \((.*)\)\s*$", str(e))
        if listed:
            items = re.findall(r"'([^']*)'", listed.group(1))
            if _socket_menu_memo.get(key) != items: bump_revision()  # the merge predictions drawn with the old items
            _socket_menu_memo[key] = items
            return items
    except (AttributeError, RuntimeError): pass  # drawing, or linked (read-only) data
    return _socket_menu_memo.get(key)

def modifier_input(mod, ident):
    """The input struct of a Geometry Nodes modifier for a group socket identifier (`.value` holds the value)."""
    inputs = getattr(getattr(mod, "properties", None), "inputs", None)
    return getattr(inputs, ident, None) if inputs is not None else None

def get_modifier_input(mod, ident):
    prop_input = modifier_input(mod, ident)
    return prop_input.value if prop_input is not None else None

def set_modifier_input(mod, ident, value):
    prop_input = modifier_input(mod, ident)
    if prop_input is not None: prop_input.value = value

SUPPORTED_OVERRIDE_TYPES = ('FLOAT', 'INT', 'BOOLEAN', 'STRING', 'MENU')

def classify_socket_type(socket_type):
    """Map a node socket / interface socket type to an override type; 'UNSUPPORTED' for vectors, colors, objects, ..."""
    if socket_type in ('VALUE', 'FLOAT') or 'Float' in socket_type: return 'FLOAT'
    if socket_type == 'INT' or socket_type.startswith('NodeSocketInt') and 'Vector' not in socket_type: return 'INT'
    if socket_type == 'BOOLEAN' or 'Bool' in socket_type: return 'BOOLEAN'
    if socket_type == 'STRING' or 'String' in socket_type: return 'STRING'
    if socket_type == 'MENU' or 'Menu' in socket_type: return 'MENU'
    return 'UNSUPPORTED'

def infer_input_type(group_ptr, node_name, input_name):
    if not group_ptr or not input_name: return 'FLOAT'
    if not node_name or node_name == "<Modifier Interface>":
        item = find_interface_input(group_ptr, input_name)
        if item:
            return classify_socket_type(getattr(item, "socket_type", "") if hasattr(group_ptr, "interface") else item.type)
    else:
        node = group_ptr.nodes.get(clean_node_name(node_name))
        if node and input_name in node.inputs:
            return classify_socket_type(node.inputs[input_name].type)
    return 'FLOAT'

def get_supported_inputs(group_ptr, node_name):
    """Names of the sockets that can be overridden. Overrides are identified by name, so repeated names count once."""
    supported = []
    for name in _supported_socket_names(group_ptr, node_name):
        if name not in supported: supported.append(name)
    return supported

def _supported_socket_names(group_ptr, node_name):
    if not group_ptr: return []
    supported = []
    if not node_name or node_name == "<Modifier Interface>":
        if hasattr(group_ptr, "interface"):
            for it in group_ptr.interface.items_tree:
                if getattr(it, "item_type", "") == 'SOCKET' and getattr(it, "in_out", "INPUT") == 'INPUT':
                    if classify_socket_type(getattr(it, "socket_type", "")) != 'UNSUPPORTED':
                        supported.append(it.name)
        elif hasattr(group_ptr, "inputs"):
            for inp in group_ptr.inputs:
                if classify_socket_type(inp.type) != 'UNSUPPORTED':
                    supported.append(inp.name)
    else:
        node = group_ptr.nodes.get(clean_node_name(node_name))
        if node:
            for inp in node.inputs:
                if not getattr(inp, "is_unavailable", False) and not getattr(inp, "hide", False):
                    if classify_socket_type(inp.type) != 'UNSUPPORTED':
                        supported.append(inp.name)
    return supported

def get_target_node_names(group_ptr, exclude=(), fallback=True):
    """Node targets of a node group that have overridable sockets, as shown in the node field, skipping `exclude`
    (clean names). '<Modifier Interface>' comes last, and with `fallback` it is offered when nothing else is, even
    without overridable sockets."""
    targets = list(_iter_targets(group_ptr, exclude))
    if fallback and not targets and "<Modifier Interface>" not in exclude:
        targets.append("<Modifier Interface>")
    return targets

def has_free_target(group_ptr, exclude):
    """Whether a node group has a target with overridable sockets that is not in `exclude` (clean names): stops at the
    first one."""
    return next(_iter_targets(group_ptr, exclude), None) is not None

def _iter_targets(group_ptr, exclude):
    if group_ptr:
        # Group Input has no input sockets. Group Output is a valid target (its unlinked inputs set the group's
        # outputs) but goes after the regular nodes, so it never becomes the default target of a new override.
        for n in sorted(group_ptr.nodes, key=lambda n: n.type == 'GROUP_OUTPUT'):
            if n.type != 'GROUP_INPUT' and clean_node_name(n.name) not in exclude:
                if get_supported_inputs(group_ptr, n.name):
                    yield f"{n.name} [{n.node_tree.name if n.type == 'GROUP' and getattr(n, 'node_tree', None) else n.type}]"
    if "<Modifier Interface>" not in exclude and get_supported_inputs(group_ptr, "<Modifier Interface>"):
        yield "<Modifier Interface>"

def get_socket_default_value(group_ptr, node_name, input_name):
    if not group_ptr: return None
    if not node_name or node_name == "<Modifier Interface>":
        return get_modifier_socket_default(group_ptr, input_name)
    else:
        node = group_ptr.nodes.get(clean_node_name(node_name))
        if node and input_name in node.inputs:
            return getattr(node.inputs[input_name], "default_value", None)
    return None

def default_value_text(override_type, default_val, menu_items):
    """Text for a value field holding a socket's default, or None when there is no usable default. A menu default
    that is not one of the items (the modifier interface reports '') falls back to the first item."""
    try:
        if override_type == 'FLOAT': return str(round(float(default_val), 4))
        if override_type == 'INT': return str(int(default_val))
        if override_type == 'BOOLEAN': return str(bool(default_val))
        if override_type == 'STRING': return None if default_val is None else str(default_val)
        if override_type == 'MENU':
            if default_val and str(default_val) in menu_items: return str(default_val)
            return menu_items[0] if menu_items else None
    except (TypeError, ValueError): pass
    return None
