from PIL import Image

from image_viewer.util.image import init_PIL


def test_init_PIL():
    """Ensure no error with font and that PIL.Image gets modified"""
    init_PIL(20)
    assert len(Image._plugins) == 1
