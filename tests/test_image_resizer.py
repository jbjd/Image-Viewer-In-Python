from tkinter import Tk
from unittest.mock import patch

import pytest
from PIL.Image import Image, Resampling
from PIL.Image import new as new_image
from turbojpeg import TurboJPEG

from image_viewer.constants import ImageFormats
from image_viewer.image.resizer import ImageResizer
from tests.test_util.mocks import MockImage


def test_jpeg_scale_factor(image_resizer: ImageResizer):
    """Should return correct ratios for a 1080x1920 screen"""
    assert image_resizer._get_jpeg_scale_factor(9999, 9999) == (1, 4)
    assert image_resizer._get_jpeg_scale_factor(3000, 3000) == (1, 2)
    assert image_resizer._get_jpeg_scale_factor(1, 1) is None


@pytest.mark.parametrize(
    "dimensions,expected_dimensions,expected_interpolation",
    [
        ((600, 800), (810, 1080), Resampling.LANCZOS),
        ((2000, 800), (1920, 768), Resampling.BICUBIC),
        ((2000, 2000), (1080, 1080), Resampling.HAMMING),
    ],
)
def test_fit_dimensions_to_screen_and_get_interpolation(
    image_resizer: ImageResizer,
    dimensions: tuple[int, int],
    expected_dimensions: tuple[int, int],
    expected_interpolation: Resampling,
):
    """Should return correct dimensions and interpolation for a 1920x1080 screen"""
    width, height = dimensions
    dimensions = image_resizer.fit_dimensions_to_screen(width, height)
    interpolation = image_resizer.get_resampling(width, height)
    assert interpolation == expected_interpolation
    assert dimensions == expected_dimensions


def test_get_fit_to_screen(image_resizer: ImageResizer):
    """Should delegate resize to correct function based on image type"""

    # JPEG is special case
    with patch.object(ImageResizer, "_get_jpeg_fit_to_screen") as mock_jpeg_fit:
        image_resizer.get_image_fit_to_screen(MockImage(format=ImageFormats.JPEG))
        mock_jpeg_fit.assert_called_once()

    # Any other type should use generic resize functions
    with patch.object(
        ImageResizer, "_get_image_fit_to_screen_with_PIL"
    ) as mock_generic_fit:
        image_resizer.get_image_fit_to_screen(MockImage(format=ImageFormats.PNG))
        mock_generic_fit.assert_called_once()


@patch.object(ImageResizer, "_get_image_fit_to_screen_with_PIL")
def test_jpeg_fit_to_screen_small_image(tk_app: Tk, image_resizer: ImageResizer):
    """When fitting a small jpeg, should fallback to generic fit function"""
    image: Image = new_image("RGB", (1000, 1000))  # smaller than screen

    with patch.object(TurboJPEG, "decode") as mock_decode:
        image_resizer._get_jpeg_fit_to_screen(image)
        mock_decode.assert_not_called()


def test_generic_fit_to_screen(tk_app: Tk, image_resizer: ImageResizer):
    """Should resize and return PIL image"""
    image: Image = new_image("RGB", (10, 10))

    with patch("image_viewer.image.resizer.resize", return_value=image) as mock_resize:
        assert type(image_resizer._get_image_fit_to_screen_with_PIL(image)) is Image
        mock_resize.assert_called_once()


def test_scale_dimensions(image_resizer: ImageResizer):
    """Should scale a tuple of width height by provided ratio"""
    assert image_resizer._scale_dimensions((1920, 1080), 1.5) == (2880, 1620)


def test_get_zoomed_image_cap(tk_app: Tk, image_resizer: ImageResizer):
    """Should determine when zoom cap hit"""
    image: Image = new_image("RGB", (1920, 1080))

    # Mock zoom factor above min zoom when image is already the size of the screen
    with patch("image_viewer.image.resizer.resize", return_value=image):
        with patch.object(
            ImageResizer,
            "_calc_zoom_factor",
            return_value=2.25,
        ):
            _, hit_cap = image_resizer.get_zoomed_image(image, 2)
            assert hit_cap

            # With a smaller image, the same zoom factor should not hit cap
            image = new_image("RGB", (800, 1080))
            _, hit_cap = image_resizer.get_zoomed_image(image, 2)
            assert not hit_cap
