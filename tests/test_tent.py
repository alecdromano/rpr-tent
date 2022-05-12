"""Unit tests for RPR Tent pure-Python utilities."""

from pathlib import Path
import tempfile
import unittest

from src.config import TentConfig, RPRSettings
from src.postprocess import clean_frame_numbers, FRAME_NUMBERS_PATTERN


class TestConfig(unittest.TestCase):
    def test_default_config_paths(self):
        cfg = TentConfig()
        blend_path = Path("/mock/project")
        paths = cfg.resolve_paths(blend_path)
        self.assertEqual(paths["root"], Path("/mock/project"))
        self.assertEqual(paths["export_path"], Path("/mock/project/Product Renderings"))
        self.assertEqual(paths["exr_path"], Path("/mock/project/Product Renderings/EXR"))
        self.assertEqual(paths["labels_path"], Path("/mock/project/deleteme"))

    def test_rpr_settings_defaults(self):
        rpr = RPRSettings()
        self.assertEqual(rpr.engine, "RPR")
        self.assertEqual(rpr.render_percentage, 60)
        self.assertEqual(rpr.max_samples, 256)


class TestPostprocess(unittest.TestCase):
    def test_frame_regex_matching(self):
        self.assertIsNotNone(FRAME_NUMBERS_PATTERN.search("shot1-0001.exr"))
        self.assertIsNotNone(FRAME_NUMBERS_PATTERN.search("Beauty_Front-0042.png"))
        self.assertIsNone(FRAME_NUMBERS_PATTERN.search("shot1.exr"))
        self.assertIsNone(FRAME_NUMBERS_PATTERN.search("shot-01.png"))

    def test_clean_frame_numbers(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file1 = Path(tmpdir) / "Render_Cam1-0001.png"
            test_file2 = Path(tmpdir) / "Subdir" / "Render_Cam2-0010.exr"
            test_file3 = Path(tmpdir) / "AlreadyClean.png"

            test_file1.touch()
            test_file2.parent.mkdir(parents=True, exist_ok=True)
            test_file2.touch()
            test_file3.touch()

            renamed = clean_frame_numbers(tmpdir)
            self.assertEqual(renamed, 2)
            self.assertTrue((Path(tmpdir) / "Render_Cam1.png").exists())
            self.assertTrue((Path(tmpdir) / "Subdir" / "Render_Cam2.exr").exists())
            self.assertTrue(test_file3.exists())

    def test_pillow_convert_images(self):
        from PIL import Image
        from src.postprocess import convert_images

        with tempfile.TemporaryDirectory() as tmpdir:
            src = Path(tmpdir) / "source"
            exp = Path(tmpdir) / "export"
            src.mkdir()
            exp.mkdir()

            # Create test dummy image (100x100 RGBA)
            img = Image.new("RGBA", (100, 100), (255, 0, 0, 255))
            test_img_path = src / "TestProduct.png"
            img.save(test_img_path)

            ok = convert_images(
                source_dir=src,
                export_dir=exp,
                sizes=(50,),
                formats=("jpeg", "png", "webp"),
            )
            self.assertTrue(ok)
            self.assertTrue((exp / "JPEG" / "50px" / "TestProduct.jpg").exists())
            self.assertTrue((exp / "PNG" / "50px" / "TestProduct.png").exists())
            self.assertTrue((exp / "WEBP" / "50px" / "TestProduct.webp").exists())


if __name__ == "__main__":
    unittest.main()

