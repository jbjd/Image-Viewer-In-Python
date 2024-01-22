from PIL import Image

from image_viewer.util.image import ImagePath, init_PIL


def test_image_path():
    """Check that ImagePath correctly finds image suffixes"""
    example_image_path = ImagePath("some_image.1.PNG")
    assert example_image_path.suffix == ".png"


def test_init_PIL():
    """Ensure no error with font and that PIL.Image gets modified"""
    init_PIL(20)
    assert len(Image._plugins) == 1
