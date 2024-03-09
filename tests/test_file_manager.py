import os
import tempfile
from unittest.mock import patch

import pytest

from image_viewer.managers.file_manager import ImageFileManager
from image_viewer.util.image import CachedImage
from test_util.mocks import MockActionUndoer, MockImage, MockStatResult


@pytest.fixture
def manager(img_dir: str) -> ImageFileManager:
    return ImageFileManager(os.path.join(img_dir, "a.png"))


def test_image_file_manager(manager: ImageFileManager):
    """Test various functions of the file manager with empty image files"""
    assert len(manager._files) == 1

    manager.find_all_images()
    assert len(manager._files) == 4
    assert manager._binary_search("a.png") == (0, True)

    manager.add_new_image("y.jpeg", False)
    assert len(manager._files) == 5

    # Should not try to rename/convert when file with that name already exists
    with pytest.raises(FileExistsError):
        manager.rename_or_convert_current_image("c.webp")

    # Try to rename a.png mocking the os call away should pass
    with patch("os.rename", lambda *_: None):
        with patch.object(
            ImageFileManager,
            "_ask_to_delete_old_image_after_convert",
            lambda *_: None,
        ):
            manager.rename_or_convert_current_image("example.test")

    # test remove_current_image functionality
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


@patch("image_viewer.managers.file_manager.askyesno", lambda *_: False)
def test_bad_path_for_rename(manager: ImageFileManager, img_dir: str):
    """When calling rename, certain conditions should raise errors"""
    with pytest.raises(OSError):
        manager.rename_or_convert_current_image(
            os.path.join("this/does/not/exist", "asdf.png")
        )
    # If path exists, error when user cancels (mocked in askyesno)
    with pytest.raises(OSError):
        manager.rename_or_convert_current_image(os.path.join(img_dir, "a.png"))


def test_caching(manager: ImageFileManager):
    """Test various caching methods to ensure they act as expected"""
    assert manager.get_current_image_cache() is None
    manager.cache_image(CachedImage(None, 20, 20, "20x20", 0, "RGB"))  # type: ignore
    assert len(manager.cache) == 1
    assert manager.get_current_image_cache() is not None
    assert manager.current_image_cache_still_fresh()
    # clear cache to make it not fresh
    manager.refresh_image_list()
    assert not manager.current_image_cache_still_fresh()


def test_move_index(manager: ImageFileManager):
    """Test moving to an index that's too large"""
    manager.move_index(999)
    assert manager._index == 0


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
    assert manager._index == 0

    # smart adjust should move index
    manager.add_new_image("a.jpg", True)
    assert manager._index == 1


def test_undo(manager: ImageFileManager):
    """Test correct behavior adding/removing with undo"""
    with patch.object(
        ImageFileManager,
        "_ask_undo_last_action",
        return_value=False,
    ):
        assert not manager.undo_rename_or_convert()

    # Mock that undo should add b.png and remove a.png
    manager.action_undoer = MockActionUndoer()
    with patch.object(
        ImageFileManager,
        "_ask_undo_last_action",
        return_value=True,
    ):
        assert manager.undo_rename_or_convert()
        assert len(manager._files) == 1
        assert manager._files[0].name == "b.png"
        assert manager._index == 0


def test_get_and_show_details(manager: ImageFileManager):
    """Should return a string containing details on current cached image and show it"""

    # Will exit if no details in cache
    PIL_image = MockImage()
    PIL_image.info["comment"] = b"test"
    with patch("image_viewer.managers.file_manager.showinfo") as mock_show_info:
        manager.show_image_details(PIL_image)
        mock_show_info.assert_not_called()

    manager.cache[manager.current_image.name] = CachedImage(
        None, 100, 100, "100kb", 9999, "P"  # type: ignore
    )
    # not gonna check the exact string returned, but Palette should be in it
    # since P was passed as the mode and it should get mapped to a more readable name
    assert "Palette" in manager.get_cached_details()

    with patch.object(os, "stat", return_value=MockStatResult(0)):
        with patch("image_viewer.managers.file_manager.showinfo") as mock_show_info:
            manager.show_image_details(PIL_image)
            mock_show_info.assert_called_once()

    # Will not fail on OSError
    with patch.object(os, "stat", side_effect=OSError):
        with patch("image_viewer.managers.file_manager.showinfo") as mock_show_info:
            manager.show_image_details(PIL_image)
            mock_show_info.assert_called_once()


def test_split_with_weird_names(manager: ImageFileManager):
    """Should notice that . and .. are not file names, but part of path"""

    # use join over static var so test works on all OS
    expected_split = (os.path.join("C:/example", ".."), manager.current_image.name)
    assert manager._split_dir_and_name("C:/example/..") == expected_split

    # use join over static var so test works on all OS
    expected_split = ("C:/example", "...")
    assert manager._split_dir_and_name("C:/example/...") == expected_split
