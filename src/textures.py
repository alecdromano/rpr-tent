"""Utilities for reloading images and external assets in Blender."""

import logging
from typing import List

logger = logging.getLogger(__name__)


def reload_images() -> List[str]:
    """Reload all external images loaded into Blender data.

    Returns:
        List of names of the reloaded images.
    """
    try:
        import bpy
    except ImportError as e:
        logger.error("Blender's bpy module is not available.")
        raise RuntimeError("reload_images requires Blender Python environment.") from e

    reloaded = []
    for image in bpy.data.images:
        try:
            image.reload()
            reloaded.append(image.name)
        except Exception as exc:
            logger.warning("Failed to reload image %s: %s", image.name, exc)

    logger.info("Reloaded %d image(s)", len(reloaded))
    return reloaded

