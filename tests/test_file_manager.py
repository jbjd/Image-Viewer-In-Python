import os
from unittest import mock

import pytest

from image_viewer.managers.file_manager import ImageFileManager


def test_image_file_manager():
    """Test various functions of the file manager with empty image files"""
    manager = ImageFileManager(os.path.abspath("tests/example_images/a.png"))
    assert len(manager._files) == 1

    manager.fully_load_image_data()
    assert len(manager._files) == 4
    assert manager._binary_search("a.png") == 0

    manager.add_new_image("y.jpeg")
    assert len(manager._files) == 5

    # Should not try to rename/convert when file with that name already exists
    with pytest.raises(FileExistsError):
        manager.rename_or_convert_current_image("c.webp", lambda _: None)

    # Try to rename a.png mocking the os call away should pass
    with mock.patch("os.rename", lambda *_: None):
        manager.rename_or_convert_current_image("example.png", lambda _: None)

    # test remove_current_image fuctionality
    for _ in range(4):
        manager.remove_current_image(False)
    assert len(manager._files) == 1

    # Should raise index error after last file removed
    with pytest.raises(IndexError):
        manager.remove_current_image(False)
