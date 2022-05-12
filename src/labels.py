"""Label loading and packaging mesh plane setup."""

import logging
import os
from pathlib import Path
from typing import Optional, Union

from src.config import TentConfig

logger = logging.getLogger(__name__)


def load_labels(
    config: Optional[TentConfig] = None,
    directory: Optional[Union[str, Path]] = None,
    prefix_filter: str = "RenderLabel__",
    extension: str = ".png",
) -> int:
    """Scan directory for packaging labels, build mesh planes, and assign materials.

    Args:
        config: TentConfig instance for scene, material, and collection settings.
        directory: Directory containing label image files. If None, derived from config.
        prefix_filter: File prefix indicating a packaging label image.
        extension: Image extension filter (default: .png).

    Returns:
        Number of label planes created/updated.
    """
    try:
        import bpy
    except ImportError as e:
        logger.error("Blender's bpy module is not available.")
        raise RuntimeError("load_labels requires Blender Python environment.") from e

    cfg = config or TentConfig()

    # Switch to master objects scene if configured
    master_scene = bpy.data.scenes.get(cfg.master_objects_scene)
    if master_scene:
        bpy.context.window.scene = master_scene
    else:
        logger.warning("Master scene '%s' not found. Using active scene.", cfg.master_objects_scene)

    # Determine directory
    if directory is None:
        blend_path = bpy.path.abspath("//")
        paths = cfg.resolve_paths(Path(blend_path))
        label_dir = paths["labels_path"]
    else:
        label_dir = Path(directory)

    if not label_dir.exists():
        logger.error("Label directory does not exist: %s", label_dir)
        return 0

    files = [
        f for f in os.listdir(label_dir)
        if f.lower().endswith(extension.lower()) and f.startswith(prefix_filter)
    ]

    if not files:
        logger.info("No matching label files found in %s", label_dir)
        return 0

    # Ensure parent collection
    parent_col = bpy.data.collections.get(cfg.parent_label_collection)
    if not parent_col:
        parent_col = bpy.data.collections.new(cfg.parent_label_collection)
        bpy.context.scene.collection.children.link(parent_col)

    # Unhide parent collection in viewport during processing
    for col in bpy.context.view_layer.layer_collection.children:
        if col.name == cfg.parent_label_collection:
            col.hide_viewport = False

    processed_count = 0

    # Reference master material
    master_mat = bpy.data.materials.get(cfg.master_material_name)
    if master_mat is None:
        logger.error("Master material '%s' not found.", cfg.master_material_name)

    for file in files:
        col_name = os.path.splitext(file)[0]
        col = bpy.data.collections.get(col_name)
        if not col:
            col = bpy.data.collections.new(col_name)
            parent_col.children.link(col)

        plane_name = f"{col_name}_plane"
        plane = bpy.data.objects.get(plane_name)

        # If plane exists, remove it and any stale image reference
        if plane:
            bpy.ops.object.select_all(action='DESELECT')
            plane.select_set(True)
            bpy.ops.object.delete()
            old_img = bpy.data.images.get(f"{col_name}.png")
            if old_img:
                bpy.data.images.remove(old_img)

        # Create plane
        bpy.ops.mesh.primitive_plane_add(size=1, align='WORLD', location=(0, 0, 0))
        plane = bpy.context.object
        plane.name = plane_name
        plane.display_type = "WIRE"
        plane.visible_shadow = False
        plane.visible_diffuse = False

        # Move plane into target collection
        if plane.name in bpy.context.collection.objects:
            bpy.context.collection.objects.unlink(plane)
        col.objects.link(plane)

        # Set up material
        mat_name = f"{col_name}_material"
        old_mat = bpy.data.materials.get(mat_name)
        if old_mat:
            bpy.data.materials.remove(old_mat)

        if master_mat:
            new_mat = master_mat.copy()
            new_mat.name = mat_name
            plane.data.materials.append(new_mat)

            if new_mat.use_nodes:
                img_path = str(label_dir / file)
                loaded_img = bpy.data.images.load(img_path)
                width, height = loaded_img.size

                for node in new_mat.node_tree.nodes:
                    if node.type == 'TEX_IMAGE':
                        node.image = loaded_img

                scale_div = cfg.label_scale_divisor
                plane.scale = (width / scale_div, height / scale_div, 1.0)
        else:
            logger.warning("Skipping material assignment for %s (no master material).", plane_name)

        processed_count += 1

    # Re-hide parent collection in viewport
    for col in bpy.context.view_layer.layer_collection.children:
        if col.name == cfg.parent_label_collection:
            col.hide_viewport = True

    logger.info("Successfully loaded %d packaging label(s).", processed_count)
    return processed_count

