"""Main pipeline execution for RPR Tent."""

import logging
from pathlib import Path
from typing import Optional

from src.config import TentConfig
from src.labels import load_labels
from src.outliner import sort_scene_collections
from src.textures import reload_images
from src.renderer import batch_render
from src.postprocess import clean_frame_numbers, convert_images

logger = logging.getLogger(__name__)


def run_pipeline(
    config: Optional[TentConfig] = None,
    load_new_labels: bool = False,
    sort_collections: bool = True,
    do_render: bool = True,
    do_clean_frames: bool = True,
    do_convert: bool = True,
) -> None:
    """Run the complete end-to-end studio pipeline.

    Args:
        config: Custom TentConfig or defaults.
        load_new_labels: If True, scans and builds/updates packaging label planes.
        sort_collections: If True, alphabetizes scene collection outliner.
        do_render: If True, batch renders all filtered cameras.
        do_clean_frames: If True, strips Blender frame numbers from rendered outputs.
        do_convert: If True, runs multi-resolution format conversions via NConvert.
    """
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    cfg = config or TentConfig()

    try:
        import bpy
        blend_dir = Path(bpy.path.abspath("//"))
    except ImportError:
        blend_dir = Path.cwd()

    paths = cfg.resolve_paths(blend_dir)

    if load_new_labels:
        logger.info("--- Step: Loading Packaging Labels ---")
        load_labels(cfg)

    if sort_collections:
        logger.info("--- Step: Sorting Outliner Collections ---")
        sort_scene_collections(case_sensitive=True)

    if do_render:
        logger.info("--- Step: Batch Rendering Cameras ---")
        batch_render(cfg, reload_before_render=True)

    if do_clean_frames:
        logger.info("--- Step: Cleaning Frame Numbers ---")
        clean_frame_numbers(paths["export_path"])

    if do_convert:
        logger.info("--- Step: Converting Formats via Pillow ---")
        convert_images(
            source_dir=paths["sgi_path"],
            export_dir=paths["export_path"],
            sizes=("720", "1440", "2160"),
            formats=("jpeg",),
            log_file=paths["log_file"]
        )

    logger.info("Pipeline run complete.")


if __name__ == "__main__":
    run_pipeline()

