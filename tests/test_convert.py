from unittest.mock import mock_open, patch

import pytest

from image_viewer.managers.file_manager import ImageFileManager
from image_viewer.util.convert import try_convert_file_and_save_new
from test_util.mocks import MockImage


def mock_open_image(_: str) -> MockImage:
    return MockImage()


def mock_open_animated_image(_: str) -> MockImage:
    image = MockImage(8)
    return image


@patch("image_viewer.util.convert.open_image", mock_open_animated_image)
@patch("image_viewer.util.convert.magic_number_guess", lambda _: ("gif",))
def test_animated_to_not_animated():
    with patch("builtins.open", mock_open()), pytest.raises(ValueError):
        try_convert_file_and_save_new("asdf.gif", "hjkl.jpg", "jpg")


@patch("image_viewer.util.convert.open_image", mock_open_image)
def test_convert_jpeg():
    with patch("builtins.open", mock_open()):
        # will not convert if jpeg variant
        with patch("image_viewer.util.convert.magic_number_guess", lambda _: ("jpg",)):
            assert not try_convert_file_and_save_new("old.jpg", "new.jpe", "jpe")
        # otherwise will succeed
        with patch("image_viewer.util.convert.magic_number_guess", lambda _: ("png",)):
            assert try_convert_file_and_save_new("old.png", "new.jpg", "jpg")


@patch("image_viewer.util.convert.open_image", mock_open_image)
def test_all_valid_types():
    """Tries to get to Image.save() for all valid types"""
    valid_types: set[str] = ImageFileManager.VALID_FILE_TYPES

    with patch("builtins.open", mock_open()):
        for img_type in valid_types:
            # when img_type == png, try assuming old.png is a webp with incorrect name
            # So function should still return true since old.png -> new.png was
            # technically a conversion
            with patch(
                "image_viewer.util.convert.magic_number_guess",
                lambda _: ("png" if img_type != "png" else "webp",),
            ):
                assert try_convert_file_and_save_new(
                    "old.png", f"new.{img_type}", img_type
                )


@patch("image_viewer.util.convert.open_image", mock_open_image)
@patch("image_viewer.util.convert.magic_number_guess", lambda _: ("jpg",))
def test_convert_to_bad_type():
    """Should return False if an invalid image extension is passed"""
    with patch("builtins.open", mock_open()):
        assert not try_convert_file_and_save_new("old.jpg", "new.txt", "txt")
