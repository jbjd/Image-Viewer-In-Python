from tkinter import Tk
from unittest.mock import patch

from PIL.Image import Image, Resampling
from PIL.Image import new as new_image
from turbojpeg import TurboJPEG

from image_viewer.constants import ImageFormats
from image_viewer.helpers.image_resizer import ImageResizer
from tests.test_util.mocks import MockImage


def test_jpeg_scale_factor(image_resizer: ImageResizer):
    """Should return correct ratios for a 1080x1920 screen"""
    assert image_resizer._get_jpeg_scale_factor(9999, 9999) == (1, 4)
    assert image_resizer._get_jpeg_scale_factor(3000, 3000) == (1, 2)
    assert image_resizer._get_jpeg_scale_factor(1, 1) is None


def test_dimension_finder(image_resizer: ImageResizer):
    """Should return correct interpolation and fit provided dimensiosn to the screen"""
    # Test uses 1920x1080 as screen size, set in resizer's constructor
    dimensions: tuple[int, int]
    interpolation: int

    # Neither dimension larger than screen, so use LANCZOS
    # 800 / 1080 is larger than 600 / 1920 so should fit to height
    dimensions, interpolation = image_resizer.dimension_finder(600, 800)
    assert interpolation == Resampling.LANCZOS
    assert dimensions[1] == 1080

    # One dimension larger than screen, so use BICUBIC and fit to width
    dimensions, interpolation = image_resizer.dimension_finder(2000, 800)
    assert interpolation == Resampling.BICUBIC
    assert dimensions[0] == 1920

    # When both dimensions are large, HAM it
    dimensions, interpolation = image_resizer.dimension_finder(2000, 2000)
    assert interpolation == Resampling.HAMMING


def test_get_fit_to_screen(image_resizer: ImageResizer):
    """Should delegate resize to correct function based on image type"""

    # JPEG is special case
    with patch.object(ImageResizer, "_get_jpeg_fit_to_screen") as mock_jpeg_fit:
        image_resizer.get_image_fit_to_screen(MockImage(format=ImageFormats.JPEG))
        mock_jpeg_fit.assert_called_once()

    # Any other type should use generic resize functions
    with patch.object(ImageResizer, "_fit_to_screen") as mock_generic_fit:
        image_resizer.get_image_fit_to_screen(MockImage(format=ImageFormats.PNG))
        mock_generic_fit.assert_called_once()


@patch.object(ImageResizer, "_fit_to_screen")
def test_jpeg_fit_to_screen_small_image(tk_app: Tk, image_resizer: ImageResizer):
    """When fitting a small jpeg, should fallback to generic fit function"""
    image: Image = new_image("RGB", (1000, 1000))  # smaller than screen

    with patch.object(TurboJPEG, "decode") as mock_decode:
        image_resizer._get_jpeg_fit_to_screen(image)
        mock_decode.assert_not_called()


def test_generic_fit_to_screen(tk_app: Tk, image_resizer: ImageResizer):
    """Should resize and return PIL image"""
    image: Image = new_image("RGB", (10, 10))

    with patch(
        "image_viewer.helpers.image_resizer.resize", return_value=image
    ) as mock_resize:
        assert type(image_resizer._fit_to_screen(image)) is Image
        mock_resize.assert_called_once()


def test_scale_dimensions(image_resizer: ImageResizer):
    """Should scale a tuple of width height by provided ratio"""
    assert image_resizer._scale_dimensions((1920, 1080), 1.5) == (2880, 1620)


def test_get_zoomed_image_cap(tk_app: Tk, image_resizer: ImageResizer):
    """Should determine when zoom cap hit"""
    image: Image = new_image("RGB", (1920, 1080))

    # Mock zoom factor above min zoom when image is already the size of the screen
    with patch("image_viewer.helpers.image_resizer.resize", return_value=image):
        with patch.object(
            ImageResizer,
            "_calc_zoom_factor",
            return_value=image_resizer.ZOOM_MIN + 0.25,
        ):
            _, hit_cap = image_resizer.get_zoomed_image(image, 2)
            assert hit_cap

            # With a smaller image, the same zoom factor should not hit cap
            image = new_image("RGB", (800, 1080))
            _, hit_cap = image_resizer.get_zoomed_image(image, 2)
            assert not hit_cap
