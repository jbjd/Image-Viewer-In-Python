from unittest.mock import mock_open, patch

import pytest

from image_viewer.constants import ImageFormats
from image_viewer.util.convert import try_convert_file_and_save_new
from tests.test_util.mocks import MockImage


def mock_open_image(_: str) -> MockImage:
    return MockImage()


def mock_open_animated_image(_: str) -> MockImage:
    image = MockImage(8)
    return image


@patch("image_viewer.util.convert.open_image", mock_open_animated_image)
@patch("image_viewer.util.convert.magic_number_guess", lambda _: "GIF")
def test_animated_to_not_animated():
    with patch("builtins.open", mock_open()), pytest.raises(ValueError):
        try_convert_file_and_save_new("asdf.gif", "hjkl.jpg", "jpg")


@patch("image_viewer.util.convert.open_image", mock_open_image)
def test_convert_jpeg():
    with patch("builtins.open", mock_open()):
        # will not convert if jpeg variant
        with patch(
            "image_viewer.util.convert.magic_number_guess", lambda _: ImageFormats.JPEG
        ):
            assert not try_convert_file_and_save_new("old.jpg", "new.jpe", "jpe")
        # otherwise will succeed
        with patch(
            "image_viewer.util.convert.magic_number_guess", lambda _: ImageFormats.PNG
        ):
            assert try_convert_file_and_save_new("old.png", "new.jpg", "jpg")


@pytest.mark.parametrize(
    "true_file_extension,target_format",
    [
        (ImageFormats.WEBP, ImageFormats.PNG),
        (ImageFormats.PNG, ImageFormats.JPEG),
        (ImageFormats.PNG, ImageFormats.WEBP),
        (ImageFormats.PNG, ImageFormats.GIF),
        (ImageFormats.PNG, ImageFormats.DDS),
        (ImageFormats.PNG, ImageFormats.PNG),
        (ImageFormats.JPEG, ImageFormats.JPEG),
    ],
)
@patch("image_viewer.util.convert.open_image", mock_open_image)
@patch("builtins.open", mock_open())
def test_convert_between_types(true_file_extension: str, target_format: str):
    """Should attempt conversion unless image is already target format, ignoring
    the file format in the path and using the format in the files magic bytes"""
    with patch(
        "image_viewer.util.convert.magic_number_guess", return_value=true_file_extension
    ):
        converted: bool = try_convert_file_and_save_new(
            "old.png", f"new.{target_format}", target_format
        )
        if true_file_extension == target_format:
            assert not converted
        else:
            assert converted


@patch("image_viewer.util.convert.open_image", mock_open_image)
@patch("image_viewer.image.file.magic_number_guess", lambda _: "JPEG")
def test_convert_to_bad_type():
    """Should return False if an invalid image extension is passed"""
    with patch("builtins.open", mock_open()):
        assert not try_convert_file_and_save_new("old.jpg", "new.txt", "txt")
