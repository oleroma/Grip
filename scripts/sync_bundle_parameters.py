import bpy

# Map Blender socket types to the Enum used by bundles
SOCKET_TYPE_MAP = {
    "NodeSocketFloat": "FLOAT",
    "NodeSocketInt": "INT",
    "NodeSocketBool": "BOOLEAN",
    "NodeSocketVector": "VECTOR",
    "NodeSocketColor": "RGBA",
    "NodeSocketRotation": "ROTATION",
    "NodeSocketMatrix": "MATRIX",
    "NodeSocketString": "STRING",
    "NodeSocketMenu": "MENU",
    "NodeSocketObject": "OBJECT",
    "NodeSocketImage": "IMAGE",
    "NodeSocketGeometry": "GEOMETRY",
    "NodeSocketCollection": "COLLECTION",
    "NodeSocketTexture": "TEXTURE",
    "NodeSocketMaterial": "MATERIAL",
}


def get_active_gn_tree():
    # Try to find the node tree the user is currently looking at
    if (
        bpy.context.space_data
        and getattr(bpy.context.space_data, "type", "") == "NODE_EDITOR"
    ):
        if bpy.context.space_data.tree_type == "GeometryNodeTree":
            return bpy.context.space_data.edit_tree

    for area in bpy.context.screen.areas:
        if area.type == "NODE_EDITOR":
            space = area.spaces.active
            if space.tree_type == "GeometryNodeTree":
                return space.edit_tree
    return None


def find_matching_separate_bundles(combine_node):
    """Finds Separate Bundles in the entire project that match our Combine Bundle."""
    matching_separates = []

    # Get the names of items currently in the Combine Bundle
    combine_item_names = {item.name for item in combine_node.bundle_items}
    if not combine_item_names:
        return []

    for tree in bpy.data.node_groups:
        if tree.bl_idname != "GeometryNodeTree":
            continue

        for node in tree.nodes:
            if node.bl_idname == "NodeSeparateBundle":
                sep_item_names = {item.name for item in node.bundle_items}

                # If they share at least 1 item, we assume it's the matching Separate Bundle
                # (You can increase this threshold if you have many small bundles)
                intersection = combine_item_names.intersection(sep_item_names)
                if len(intersection) > 0:
                    matching_separates.append(node)

    return matching_separates


def sync_unconnected_parameters():
    tree = get_active_gn_tree()
    if not tree:
        print(
            "Error: No active Geometry Node tree found. Please open it in the Node Editor."
        )
        return

    # 1. Find the Group Input node
    group_ins = [n for n in tree.nodes if n.bl_idname == "NodeGroupInput"]
    if not group_ins:
        print("Error: No Group Input node found in the active tree.")
        return

    # If multiple, grab the leftmost one
    group_ins.sort(key=lambda n: n.location.x)
    group_in = group_ins[0]

    # 2. Find the Combine Bundle
    combines = [n for n in tree.nodes if n.bl_idname == "NodeCombineBundle"]
    if not combines:
        print("Error: No Combine Bundle node found in the active tree.")
        return

    combines.sort(key=lambda n: n.location.x)
    combine = combines[0]

    # 3. Find corresponding Separate Bundles anywhere in the project
    matching_separates = find_matching_separate_bundles(combine)

    added_params = []

    # 4. Process unconnected sockets
    for out_socket in group_in.outputs:
        # Ignore virtual/empty sockets at the bottom of the node
        if (
            not out_socket.identifier
            or out_socket.is_multi_input
            or not out_socket.name
        ):
            continue

        if not out_socket.is_linked:
            bl_type = out_socket.bl_idname
            enum_type = SOCKET_TYPE_MAP.get(
                bl_type, "FLOAT"
            )  # Default to Float if unknown
            socket_name = out_socket.name

            # --- UPDATE COMBINE BUNDLE ---
            # Create item if it doesn't exist
            if socket_name not in [item.name for item in combine.bundle_items]:
                combine.bundle_items.new(socket_type=enum_type, name=socket_name)

            # Create the link (wire)
            if socket_name in combine.inputs:
                tree.links.new(out_socket, combine.inputs[socket_name])
                added_params.append(socket_name)

            # --- UPDATE SEPARATE BUNDLES ---
            for separate in matching_separates:
                if socket_name not in [item.name for item in separate.bundle_items]:
                    separate.bundle_items.new(socket_type=enum_type, name=socket_name)

    if added_params:
        print(f"Success! Wired and synchronized: {', '.join(added_params)}")
        if matching_separates:
            print(
                f" -> Also updated {len(matching_separates)} matching Separate Bundle(s) in the project."
            )
    else:
        print("No unconnected inputs were found.")


if __name__ == "__main__":
    sync_unconnected_parameters()
