import os
from unittest import mock

import pytest

from image_viewer.managers.file_manager import ImageFileManager
from image_viewer.util.convert import try_convert_file_and_save_new
from image_viewer.util.image import ImagePath


class MockImage:
    """Mocks PIL Image for testing"""

    mode = "P"
    info: dict = {}

    def __init__(self, n_frames: int = 1) -> None:
        self.n_frames: int = n_frames

    def convert(self, new_mode: str) -> "MockImage":
        self.mode = new_mode
        return self

    def save(self, *_, **kwargs) -> None:
        pass

    def __enter__(self) -> "MockImage":
        return self

    def __exit__(self, *_) -> None:
        pass


def mock_open_image(_: str) -> MockImage:
    return MockImage()


def mock_open_animated_image(_: str) -> MockImage:
    return MockImage(8)


def get_vars_for_test(
    dir: str, old_name: str, new_name: str
) -> tuple[str, ImagePath, str, ImagePath]:
    old_path: str = os.path.join(dir, f"{old_name}")
    old_data = ImagePath(old_name)
    new_path: str = os.path.join(dir, f"{new_name}")
    new_data = ImagePath(new_name)
    return (old_path, old_data, new_path, new_data)


def test_animated_to_not_animated():
    with mock.patch("image_viewer.util.convert.open_image", mock_open_animated_image):
        with pytest.raises(ValueError):
            try_convert_file_and_save_new(
                *get_vars_for_test("", "asdf.gif", "hjkl.jpg")
            )


def test_convert_jpeg(img_dir: str):
    with pytest.raises(FileExistsError):
        try_convert_file_and_save_new(*get_vars_for_test(img_dir, "b.jpe", "d.jpg"))

    with mock.patch("image_viewer.util.convert.open_image", mock_open_image):
        # will not covert if jpeg varient
        assert not try_convert_file_and_save_new(
            *get_vars_for_test(img_dir, "old.jpe", "new.jpg")
        )
        # otherwise will succeed
        assert try_convert_file_and_save_new(
            *get_vars_for_test(img_dir, "old.png", "new.jpg")
        )


def test_all_valid_types():
    """Tries to get to Image.save() for all valid types"""
    valid_types: set[str] = ImageFileManager.VALID_FILE_TYPES

    with mock.patch("image_viewer.util.convert.open_image", mock_open_image):
        for type in valid_types:
            result = try_convert_file_and_save_new(
                *get_vars_for_test("", "old.png", f"new.{type}")
            )
            assert result
