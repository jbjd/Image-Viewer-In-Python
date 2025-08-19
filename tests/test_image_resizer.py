from tkinter import Tk
from unittest.mock import patch

import pytest
from PIL.Image import Image, Resampling
from PIL.Image import new as new_image

from image_viewer.image.resizer import ImageResizer

_MODULE_PATH: str = "image_viewer.image.resizer"


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


# TODO: Functional test of large JPEG
def test_jpeg_fit_to_screen_small_image(tk_app: Tk, image_resizer: ImageResizer):
    """When fitting a small jpeg, should fallback to generic fit function"""
    image: Image = new_image("RGB", (1000, 1000))  # smaller than screen

    with (
        patch.object(ImageResizer, "get_image_fit_to_screen"),
        patch(f"{_MODULE_PATH}.decode_scaled_jpeg") as mock_decode_scaled_jpeg,
    ):
        image_resizer.get_jpeg_fit_to_screen(image, "")
        mock_decode_scaled_jpeg.assert_not_called()


def test_get_image_fit_to_screen(tk_app: Tk, image_resizer: ImageResizer):
    """Should resize and return PIL image"""
    image: Image = new_image("RGB", (10, 10))

    with patch("image_viewer.image.resizer.resize", return_value=image) as mock_resize:
        assert isinstance(image_resizer.get_image_fit_to_screen(image), Image)
        mock_resize.assert_called_once()


def test_scale_dimensions(image_resizer: ImageResizer):
    """Should scale a tuple of width height by provided ratio"""
    assert image_resizer._scale_dimensions((1920, 1080), 1.5) == (2880, 1620)


def test_get_zoomed_image_cap(tk_app: Tk, image_resizer: ImageResizer):
    """Should determine when zoom cap hit"""
    image: Image = new_image("RGB", (1920, 1080))

    # Mock zoom factor above min zoom when image is already the size of the screen
    with patch(f"{_MODULE_PATH}.resize", return_value=image):
        with patch.object(
            ImageResizer,
            "_calculate_zoom_factor",
            return_value=2.25,
        ):
            zoomed_result = image_resizer.get_zoomed_image(image, 2)
            assert zoomed_result.hit_max_zoom

            # With a smaller image, the same zoom factor should not hit cap
            image = new_image("RGB", (800, 1080))
            zoomed_result = image_resizer.get_zoomed_image(image, 2)
            assert not zoomed_result.hit_max_zoom
