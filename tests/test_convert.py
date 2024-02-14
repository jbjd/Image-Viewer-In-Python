from __future__ import annotations

from unittest import mock

import pytest

from image_viewer.managers.file_manager import ImageFileManager
from image_viewer.util.convert import try_convert_file_and_save_new


class MockFilePointer:
    """Mocks whats returned by builtin open"""

    def __enter__(self) -> MockFilePointer:
        return self

    def __exit__(self, *_) -> None:
        pass

    def read(self, _) -> str:
        return ""


class MockImage:
    """Mocks PIL Image for testing"""

    mode = "P"
    info: dict = {}

    def __init__(self, n_frames: int = 1) -> None:
        self.n_frames: int = n_frames

    def convert(self, new_mode: str) -> MockImage:
        self.mode = new_mode
        return self

    def save(self, *_, **kwargs) -> None:
        pass

    def __enter__(self) -> MockImage:
        return self

    def __exit__(self, *_) -> None:
        pass


def mock_open(*_) -> MockFilePointer:
    return MockFilePointer()


def mock_open_image(_: str) -> MockImage:
    return MockImage()


def mock_open_animated_image(_: str) -> MockImage:
    image = MockImage(8)
    # is_animated only exists on file types that can be animated in PIL module
    image.is_animated = True  # type: ignore
    return image


@mock.patch("image_viewer.util.convert.open_image", mock_open_animated_image)
@mock.patch("image_viewer.util.convert.open", mock_open)
@mock.patch("image_viewer.util.convert.magic_number_guess", lambda _: ("gif",))
def test_animated_to_not_animated():
    with pytest.raises(ValueError):
        try_convert_file_and_save_new("asdf.gif", "hjkl.jpg", "jpg")


@mock.patch("image_viewer.util.convert.open_image", mock_open_image)
@mock.patch("image_viewer.util.convert.open", mock_open)
def test_convert_jpeg(img_dir: str):
    # will not covert if jpeg varient
    with mock.patch("image_viewer.util.convert.magic_number_guess", lambda _: ("jpg",)):
        assert not try_convert_file_and_save_new("old.jpg", "new.jpe", "jpe")
    # otherwise will succeed
    with mock.patch("image_viewer.util.convert.magic_number_guess", lambda _: ("png",)):
        assert try_convert_file_and_save_new("old.png", "new.jpg", "jpg")


@mock.patch("image_viewer.util.convert.open_image", mock_open_image)
@mock.patch("image_viewer.util.convert.open", mock_open)
def test_all_valid_types():
    """Tries to get to Image.save() for all valid types"""
    valid_types: set[str] = ImageFileManager.VALID_FILE_TYPES

    for img_type in valid_types:
        # when img_type == png, try assuming old.png is a webp with incorrect name
        # So function should still return true since old.png -> new.png was technially
        # a convertion
        with mock.patch(
            "image_viewer.util.convert.magic_number_guess",
            lambda _: ("png" if img_type != "png" else "webp",),
        ):
            assert try_convert_file_and_save_new("old.png", f"new.{img_type}", img_type)


@mock.patch("image_viewer.util.convert.open_image", mock_open_image)
@mock.patch("image_viewer.util.convert.open", mock_open)
@mock.patch("image_viewer.util.convert.magic_number_guess", lambda _: ("jpg",))
def test_convert_to_bad_type(img_dir: str):
    """Should return False if an invalid image extension is passed"""
    assert not try_convert_file_and_save_new("old.jpg", "new.txt", "txt")
