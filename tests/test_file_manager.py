import os
import tempfile
from unittest import mock

import pytest

from image_viewer.managers.file_manager import ImageFileManager


@pytest.fixture
def manager(img_dir: str) -> ImageFileManager:
    return ImageFileManager(os.path.join(img_dir, "a.png"))


def test_image_file_manager(manager: ImageFileManager):
    """Test various functions of the file manager with empty image files"""
    assert len(manager._files) == 1

    manager.fully_load_image_data()
    assert len(manager._files) == 4
    assert manager._binary_search("a.png") == 0

    manager.add_new_image("y.jpeg", False)
    assert len(manager._files) == 5

    # Should not try to rename/convert when file with that name already exists
    with pytest.raises(FileExistsError):
        manager.rename_or_convert_current_image("c.webp")

    # Try to rename a.png mocking the os call away should pass
    with mock.patch("os.rename", lambda *_: None):
        with mock.patch.object(
            ImageFileManager,
            "_ask_delete_after_convert",
            lambda *_: None,
        ):
            manager.rename_or_convert_current_image("example.test")

    # test remove_current_image fuctionality
    for _ in range(4):
        manager.remove_current_image(False)
    assert len(manager._files) == 1

    # Should raise index error after last file removed
    with pytest.raises(IndexError):
        manager.remove_current_image(False)


def test_bad_path(img_dir: str):
    # doesn't exist
    with pytest.raises(ValueError):
        ImageFileManager("bad/path")
    # wrong file type
    with pytest.raises(ValueError):
        ImageFileManager(os.path.join(img_dir, "not_an_image.txt"))


def test_caching(manager: ImageFileManager):
    """Test various caching methods to ensure they act as expected"""
    manager.cache_image(None, 20, 20, "20x20", 0)  # type: ignore
    assert len(manager.cache) == 1
    assert manager.get_current_image_cache() is not None
    assert manager.current_image_cache_still_fresh()
    # clear cache to make it not fresh
    manager.refresh_image_list()
    assert not manager.current_image_cache_still_fresh()


def test_move_current_index(manager: ImageFileManager):
    """Test moving to an index thats too large"""
    manager.move_current_index(999)
    assert manager._current_index == 0


def test_delete_file(manager: ImageFileManager):
    """Tests deleting a file from disk via file manager"""

    # add one extra image so it doesn't error after removing the only file
    manager.add_new_image("Some_image.png", False)

    with tempfile.NamedTemporaryFile() as tmp:
        manager.path_to_current_image = tmp.name
        manager.remove_current_image(True)
        assert len(manager._files) == 1


def test_smart_adjust(manager: ImageFileManager):
    """Should stay on current image when smart_adjust=True"""

    # smart adjust should not kick in
    manager.add_new_image("zzz.png", True)
    assert manager._current_index == 0

    # smart adjust should move index
    manager.add_new_image("a.jpg", True)
    assert manager._current_index == 1
