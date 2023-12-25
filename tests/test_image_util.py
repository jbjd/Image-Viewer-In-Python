from image_viewer.util.image import ImagePath


def test_image_path():
    """Check that ImagePath correctly finds image suffixes"""
    example_image_path = ImagePath("some_image.1.PNG")
    assert example_image_path.suffix == ".png"
