"""Configuration settings and defaults for RPR Tent."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


@dataclass
class RPRSettings:
    """Radeon ProRender specific scene and engine settings."""
    engine: str = "RPR"
    render_percentage: int = 60
    resolution_x: int = 7756
    resolution_y: int = 7756
    film_transparent: bool = False
    use_border: bool = True
    use_crop_to_border: bool = True
    file_format: str = "OPEN_EXR"
    color_mode: str = "RGBA"
    color_depth: str = "32"
    use_file_extension: bool = True
    use_render_cache: bool = False

    # RPR-specific attributes
    use_tile_render: int = 1
    tile_x: int = 256
    tile_y: int = 256
    tile_order: str = "CENTER_SPIRAL"
    min_samples: int = 128
    max_samples: int = 256
    noise_threshold: float = 0.0
    render_quality: str = "FULL2"
    texture_compression: int = 0
    max_ray_depth: int = 8
    diffuse_depth: int = 3
    glossy_depth: int = 5
    refraction_depth: int = 5
    glossy_refraction_depth: int = 5
    shadow_depth: int = 5
    ray_cast_epsilon: float = 0.02
    pixel_filter: str = "BLACKMANHARRIS"
    pixel_filter_width: float = 1.50


@dataclass
class TentConfig:
    """Top-level configuration for project paths and rendering pipeline."""
    base_dir: Optional[Path] = None
    export_dir_name: str = "Product Renderings"
    exr_subdir: str = "EXR"
    sgi_subdir: str = "IRIS"
    labels_subdir: str = "deleteme"
    log_filename: str = "BatchConversion.log"

    foreground_collection: str = "Photos"
    camera_prefix_filter: str = "!"
    master_objects_scene: str = "$ Master-Objects"
    parent_label_collection: str = "RenderLabel"
    master_material_name: str = "origin_material"
    label_scale_divisor: float = 23622.0

    rpr: RPRSettings = field(default_factory=RPRSettings)

    def resolve_paths(self, blend_dir: Path) -> dict:
        """Resolve full output paths relative to blend directory or explicit base directory."""
        root = Path(self.base_dir) if self.base_dir else Path(blend_dir)
        export_path = root / self.export_dir_name
        return {
            "root": root,
            "export_path": export_path,
            "exr_path": export_path / self.exr_subdir,
            "sgi_path": export_path / self.sgi_subdir,
            "labels_path": root / self.labels_subdir,
            "log_file": root / self.log_filename,
        }

