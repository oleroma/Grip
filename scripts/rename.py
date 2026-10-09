import bpy

def match_node_name_to_group(node_tree):
    """Iterates through nodes in a tree and renames the ID of group nodes to match their source group."""
    if not node_tree or not hasattr(node_tree, 'nodes'):
        return

    for node in node_tree.nodes:
        # Check if the node is a group node (it will have a 'node_tree' attribute)
        if hasattr(node, 'node_tree') and node.node_tree is not None:
            group_name = node.node_tree.name

            # Change ONLY the internal ID name
            # Blender will automatically append .001, .002 if duplicates exist in the same tree
            node.name = group_name

def main():
    count = 0

    # Update ONLY nodes inside Geometry Node setups
    for group in bpy.data.node_groups:
        # Ensure we are only looking at Geometry Node trees
        if group.bl_idname == 'GeometryNodeTree':
            match_node_name_to_group(group)
            count += 1

    print(f"Successfully processed {count} Geometry Node trees and renamed their internal group IDs.")

# Run the script
if __name__ == "__main__":
    main()
