"""Batch rendering engine for Radeon ProRender in Blender."""

import logging
import os
from pathlib import Path
from typing import Callable, Iterable, List, Optional

from src.config import TentConfig, RPRSettings
from src.textures import reload_images

logger = logging.getLogger(__name__)


def apply_rpr_settings(scene, settings: RPRSettings) -> None:
    """Apply rendering and Radeon ProRender specific attributes to a Blender scene."""
    render = scene.render
    render.engine = settings.engine
    render.resolution_x = settings.resolution_x
    render.resolution_y = settings.resolution_y
    render.resolution_percentage = settings.render_percentage
    render.film_transparent = settings.film_transparent
    render.use_border = settings.use_border
    render.use_crop_to_border = settings.use_crop_to_border

    render.image_settings.file_format = settings.file_format
    render.image_settings.color_mode = settings.color_mode
    render.image_settings.color_depth = settings.color_depth
    render.use_file_extension = settings.use_file_extension
    render.use_render_cache = settings.use_render_cache

    if hasattr(scene, "rpr"):
        rpr = scene.rpr
        rpr.use_tile_render = settings.use_tile_render
        rpr.tile_x = settings.tile_x
        rpr.tile_y = settings.tile_y
        rpr.tile_order = settings.tile_order
        rpr.render_quality = settings.render_quality
        rpr.texture_compression = settings.texture_compression
        rpr.max_ray_depth = settings.max_ray_depth
        rpr.diffuse_depth = settings.diffuse_depth
        rpr.glossy_depth = settings.glossy_depth
        rpr.refraction_depth = settings.refraction_depth
        rpr.glossy_refraction_depth = settings.glossy_refraction_depth
        rpr.shadow_depth = settings.shadow_depth
        rpr.ray_cast_epsilon = settings.ray_cast_epsilon
        rpr.pixel_filter = settings.pixel_filter
        rpr.pixel_filter_width = settings.pixel_filter_width

        if hasattr(rpr, "limits"):
            rpr.limits.min_samples = settings.min_samples
            rpr.limits.max_samples = settings.max_samples
            rpr.limits.noise_threshold = settings.noise_threshold
    else:
        logger.warning("RPR addon attributes (scene.rpr) not present on scene.")


def isolate_objects_for_camera(objects: Iterable, keeper_collections: Iterable) -> None:
    """Hide renderability for objects not part of the active camera's collection(s)."""
    keeper_set = frozenset(keeper_collections)
    for obj in objects:
        if obj.type == "CAMERA":
            continue
        obj_collections = frozenset(obj.users_collection)
        obj.hide_render = len(keeper_set & obj_collections) == 0


def restore_object_visibility(objects: Iterable) -> None:
    """Restore render visibility for all objects."""
    for obj in objects:
        obj.hide_render = False


def batch_render(
    config: Optional[TentConfig] = None,
    reload_before_render: bool = True,
    camera_filter: Optional[Callable[[str], bool]] = None,
) -> List[str]:
    """Execute batch render of all filtered cameras in the foreground collection.

    Args:
        config: TentConfig settings object.
        reload_before_render: Whether to reload all external textures first.
        camera_filter: Optional predicate function f(cam_name) -> bool. If None,
                       defaults to checking whether config.camera_prefix_filter is in name.

    Returns:
        List of rendered output file paths.
    """
    try:
        import bpy
    except ImportError as e:
        logger.error("Blender's bpy module is not available.")
        raise RuntimeError("batch_render requires Blender Python environment.") from e

    cfg = config or TentConfig()

    if reload_before_render:
        reload_images()

    blend_dir = Path(bpy.path.abspath("//"))
    paths = cfg.resolve_paths(blend_dir)
    exr_dir = paths["exr_path"]
    export_dir = paths["export_path"]
    exr_dir.mkdir(parents=True, exist_ok=True)

    fg_col = bpy.data.collections.get(cfg.foreground_collection)
    if not fg_col:
        raise ValueError(f"Foreground collection '{cfg.foreground_collection}' not found.")

    objects_of_interest = [o for o in fg_col.all_objects if not o.hide_render]

    # Find target cameras
    is_valid_camera = camera_filter or (lambda name: cfg.camera_prefix_filter in name)
    cameras = [
        o for o in objects_of_interest
        if o.type == "CAMERA" and is_valid_camera(o.name)
    ]

    logger.info("Found %d camera(s) matching filter for rendering.", len(cameras))
    rendered_files = []

    scene = bpy.context.scene
    apply_rpr_settings(scene, cfg.rpr)

    for cam in cameras:
        file_name = cam.name.replace(f"{cfg.camera_prefix_filter} ", "").replace(cfg.camera_prefix_filter, "")
        output_filepath = str(exr_dir / file_name)

        logger.info("Rendering camera '%s' -> %s", cam.name, output_filepath)

        # Isolate foreground collection objects for this camera
        isolate_objects_for_camera(objects_of_interest, cam.users_collection)

        scene.camera = cam
        scene.render.filepath = output_filepath

        # Configure compositor File Output nodes if present
        if scene.use_nodes and scene.node_tree:
            file_pre_replace = f"{file_name}-"
            for node in scene.node_tree.nodes:
                if node.type == "OUTPUT_FILE":
                    format_name = getattr(node.format, "file_format", "OUTPUT")
                    node.base_path = str(export_dir / format_name)
                    if node.file_slots:
                        node.file_slots[0].path = file_pre_replace

        # Execute render
        bpy.ops.render.render(write_still=True)
        rendered_files.append(output_filepath)

        # Restore visibility
        restore_object_visibility(objects_of_interest)

    return rendered_files

