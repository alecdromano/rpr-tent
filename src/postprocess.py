"""Post-processing and file format conversion utilities using Pillow."""

import logging
import os
from pathlib import Path
import re
from typing import Iterable, List, Optional, Tuple, Union

try:
    from PIL import Image, ImageChops
    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False

logger = logging.getLogger(__name__)

FRAME_NUMBERS_PATTERN = re.compile(r"""(-\d{4})\.\w{3,4}\Z""", re.IGNORECASE)


def clean_frame_numbers(directory: Union[str, Path]) -> int:
    """Strip 4-digit frame suffix (-0001) added by Blender File Output nodes.

    Args:
        directory: Root directory to walk and rename files.

    Returns:
        Number of files renamed.
    """
    root_dir = Path(directory)
    if not root_dir.exists():
        logger.warning("Directory does not exist: %s", root_dir)
        return 0

    renamed_count = 0
    for dirpath, _, filenames in os.walk(root_dir):
        for filename in filenames:
            match = FRAME_NUMBERS_PATTERN.search(filename)
            if match is not None:
                old_path = Path(dirpath) / filename
                new_filename = filename.replace(match.group(1), "")
                new_path = Path(dirpath) / new_filename
                try:
                    old_path.replace(new_path)
                    renamed_count += 1
                except OSError as err:
                    logger.error("Failed to rename %s to %s: %s", old_path, new_path, err)

    logger.info("Cleaned frame numbers from %d file(s) in %s", renamed_count, root_dir)
    return renamed_count


def autocrop_image(image: "Image.Image", background_color: Optional[Tuple[int, ...]] = None) -> "Image.Image":
    """Crop borders that match the top-left corner pixel color (similar to nconvert -autocrop)."""
    if image.mode != "RGBA" and image.mode != "RGB":
        image = image.convert("RGBA")

    if background_color is None:
        # Sample top-left pixel
        background_color = image.getpixel((0, 0))

    bg = Image.new(image.mode, image.size, background_color)
    diff = ImageChops.difference(image, bg)
    bbox = diff.getbbox()
    if bbox:
        return image.crop(bbox)
    return image


def convert_images(
    source_dir: Union[str, Path],
    export_dir: Union[str, Path],
    sizes: Iterable[Union[int, str]] = ("720", "1440", "2160"),
    formats: Iterable[str] = ("jpeg",),
    quality: int = 85,
    autocrop: bool = True,
    bg_color: Tuple[int, int, int] = (255, 255, 255),
    log_file: Optional[Union[str, Path]] = None,
) -> bool:
    """Convert and resize rendered master images (SGI, EXR, PNG, TIFF) to web formats using Pillow.

    Args:
        source_dir: Source folder containing master renders (e.g. IRIS / SGI / EXR).
        export_dir: Root export directory for converted outputs.
        sizes: Target output vertical resolutions in pixels (e.g., 720, 1440, 2160).
        formats: Target output formats ('jpeg', 'png', 'webp').
        quality: Compression quality for lossy formats (0-100).
        autocrop: Whether to autocrop uniform top-left background borders.
        bg_color: RGB background color for alpha composite when saving non-alpha formats like JPEG.
        log_file: Optional log file to append progress information.

    Returns:
        True if all conversions completed successfully, False otherwise.
    """
    if not PILLOW_AVAILABLE:
        logger.error("Pillow is not installed. Run `pip install Pillow` to use image conversions.")
        return False

    src = Path(source_dir)
    exp = Path(export_dir)

    if not src.exists():
        logger.warning("Source directory does not exist: %s", src)
        return False

    # Supported source extensions
    image_files = [
        f for f in src.iterdir()
        if f.is_file() and not f.name.startswith(".")
    ]

    if not image_files:
        logger.info("No source images found in %s to convert.", src)
        return True

    success = True
    log_lines = []

    for img_path in image_files:
        try:
            with Image.open(img_path) as orig:
                base_img = orig.copy()
        except Exception as e:
            logger.warning("Could not open %s: %s", img_path.name, e)
            continue

        # Optional autocrop
        if autocrop:
            try:
                base_img = autocrop_image(base_img)
            except Exception as e:
                logger.warning("Autocrop failed for %s: %s", img_path.name, e)

        orig_w, orig_h = base_img.size

        for fmt in formats:
            fmt_lower = fmt.lower()
            ext = ".jpg" if fmt_lower in ("jpeg", "jpg") else f".{fmt_lower}"

            for size in sizes:
                target_h = int(size)
                scale = target_h / orig_h
                target_w = max(1, int(round(orig_w * scale)))

                out_folder = exp / fmt_lower.upper() / f"{target_h}px"
                out_folder.mkdir(parents=True, exist_ok=True)
                out_file = out_folder / f"{img_path.stem}{ext}"

                try:
                    # High quality Lanczos resampling
                    resized = base_img.resize((target_w, target_h), resample=Image.Resampling.LANCZOS)

                    if fmt_lower in ("jpeg", "jpg"):
                        # Flatten alpha transparency onto white background
                        if resized.mode in ("RGBA", "LA") or (resized.mode == "P" and "transparency" in resized.info):
                            canvas = Image.new("RGB", resized.size, bg_color)
                            canvas.paste(resized, mask=resized.split()[-1])
                            save_img = canvas
                        else:
                            save_img = resized.convert("RGB")

                        save_img.save(out_file, "JPEG", quality=quality, optimize=True)
                    elif fmt_lower == "png":
                        resized.save(out_file, "PNG", optimize=True)
                    elif fmt_lower == "webp":
                        resized.save(out_file, "WEBP", quality=quality)
                    else:
                        logger.warning("Unsupported format: %s", fmt)
                        continue

                    msg = f"Converted {img_path.name} -> {out_file} ({target_w}x{target_h})"
                    logger.info(msg)
                    log_lines.append(msg)

                except Exception as e:
                    err_msg = f"Failed conversion for {img_path.name} to {out_file}: {e}"
                    logger.error(err_msg)
                    log_lines.append(err_msg)
                    success = False

    if log_file and log_lines:
        try:
            with open(log_file, "a", encoding="utf-8") as fp:
                fp.write("\n".join(log_lines) + "\n")
        except OSError as e:
            logger.warning("Could not write to conversion log file: %s", e)

    return success
