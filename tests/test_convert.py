import os
from unittest import mock

import pytest

from image_viewer.util.convert import try_convert_file_and_save_new
from image_viewer.util.image import ImagePath


class MockImage:
    """Mocks PIL Image for testing"""

    mode = "P"

    def convert(self, new_mode: str):
        self.mode = new_mode
        return self

    def save(self, *_, **kwargs) -> None:
        pass

    def __enter__(self) -> None:
        return self

    def __exit__(self, *_) -> None:
        pass


def mock_open_image(_: str) -> MockImage:
    return MockImage()


def mock_open_animated_image(_: str) -> MockImage:
    img = MockImage()
    img.n_frames = 8
    return img


def get_vars_for_test(
    dir: str, old_name: str, new_name: str
) -> tuple[str, str, str, str]:
    old_path: str = os.path.join(dir, f"example_images/{old_name}")
    old_data = ImagePath(old_name)
    new_path: str = os.path.join(dir, f"example_images/{new_name}")
    new_data = ImagePath(new_name)
    return (old_path, old_data, new_path, new_data)


def test_animated_to_not_animated():
    with mock.patch("image_viewer.util.convert.open_image", mock_open_animated_image):
        with pytest.raises(ValueError):
            try_convert_file_and_save_new(
                *get_vars_for_test("", "asdf.gif", "hjkl.jpg")
            )


def test_convert_jpeg(working_dir: str):
    with pytest.raises(FileExistsError):
        try_convert_file_and_save_new(*get_vars_for_test(working_dir, "b.jpe", "d.jpg"))

    with mock.patch("image_viewer.util.convert.open_image", mock_open_image):
        # will not covert if jpeg varient
        assert not try_convert_file_and_save_new(
            *get_vars_for_test(working_dir, "old.jpe", "new.jpg")
        )
        # otherwise will succeed
        assert try_convert_file_and_save_new(
            *get_vars_for_test(working_dir, "old.png", "new.jpg")
        )
