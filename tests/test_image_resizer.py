from tkinter import Tk
from unittest.mock import patch

from PIL.Image import Image, Resampling
from PIL.Image import new as new_image
from PIL.ImageTk import PhotoImage

from image_viewer.helpers.image_resizer import ImageResizer
from test_util.mocks import MockImage


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
        image_resizer.get_image_fit_to_screen(MockImage(format="JPEG"))
        mock_jpeg_fit.assert_called_once()

    # Any other type should use generic resize functions
    with patch.object(ImageResizer, "_fit_to_screen") as mock_generic_fit:
        image_resizer.get_image_fit_to_screen(MockImage(format="PNG"))
        mock_generic_fit.assert_called_once()


def test_generic_fit_to_screen(tk_app: Tk, image_resizer: ImageResizer):
    """Should resize and return PIL image as PhotoImage"""
    image: Image = new_image("RGB", (10, 10))

    with patch(
        "image_viewer.helpers.image_resizer.resize", return_value=image
    ) as mock_resize:
        assert type(image_resizer._fit_to_screen(image)) is PhotoImage
        mock_resize.assert_called_once()


def test_scale_dimensions(image_resizer: ImageResizer):
    """Should scale a tuple of width height by provided ratio"""
    assert image_resizer._scale_dimensions((1920, 1080), 1.5) == (2880, 1620)
