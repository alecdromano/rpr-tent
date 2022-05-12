"""Outliner and collection organization utilities."""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


def sort_collection(collection, case_sensitive: bool = False) -> None:
    """Recursively sort child collections within a collection alphabetically.

    Args:
        collection: A Blender bpy.types.Collection object.
        case_sensitive: Whether sorting should be case-sensitive.
    """
    if not hasattr(collection, "children") or collection.children is None:
        return

    children = sorted(
        collection.children,
        key=lambda c: c.name if case_sensitive else c.name.lower()
    )

    for child in children:
        collection.children.unlink(child)
        collection.children.link(child)
        sort_collection(child, case_sensitive=case_sensitive)


def sort_scene_collections(case_sensitive: bool = False, scene_name: Optional[str] = None) -> None:
    """Sort collection hierarchies alphabetically for specified or all scenes.

    Args:
        case_sensitive: Whether to use case-sensitive ordering.
        scene_name: Optional specific scene name to sort. If None, sorts all scenes.
    """
    try:
        import bpy
    except ImportError as e:
        logger.error("Blender's bpy module is not available.")
        raise RuntimeError("sort_scene_collections requires Blender Python environment.") from e

    if scene_name:
        scene = bpy.data.scenes.get(scene_name)
        if scene:
            sort_collection(scene.collection, case_sensitive=case_sensitive)
            logger.info("Sorted collection hierarchy for scene: %s", scene_name)
        else:
            logger.warning("Scene not found: %s", scene_name)
    else:
        for scene in bpy.data.scenes:
            sort_collection(scene.collection, case_sensitive=case_sensitive)
        logger.info("Sorted collection hierarchy across all %d scene(s)", len(bpy.data.scenes))

