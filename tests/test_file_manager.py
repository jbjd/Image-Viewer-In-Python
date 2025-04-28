import os
import tempfile
from unittest.mock import patch

import pytest

from image_viewer.actions.undoer import ActionUndoer, UndoResponse
from image_viewer.constants import ImageFormats
from image_viewer.files.file_manager import ImageFileManager, _ShouldPreserveIndex
from image_viewer.image.cache import ImageCache, ImageCacheEntry
from image_viewer.image.file import ImageName, ImageNameList
from tests.conftest import IMG_DIR, mock_load_dll_from_path
from tests.test_util.exception import safe_wrapper
from tests.test_util.mocks import MockImage, MockStatResult


@pytest.fixture
def manager(image_cache: ImageCache) -> ImageFileManager:
    return ImageFileManager(os.path.join(IMG_DIR, "a.png"), image_cache)


@pytest.fixture
def manager_with_3_images(image_cache: ImageCache) -> ImageFileManager:
    manager = ImageFileManager(os.path.join(IMG_DIR, "a.png"), image_cache)
    manager._files = ImageNameList(
        [ImageName(name) for name in ["a.png", "c.jpb", "e.webp"]]
    )
    return manager


def test_image_file_manager(manager: ImageFileManager):
    """Test various functions of the file manager with empty image files"""
    assert len(manager._files) == 1

    with patch("util.os._UtilsDllFactory._load_dll_from_path", mock_load_dll_from_path):
        manager.find_all_images()
    assert len(manager._files) == 4
    assert manager._files.get_index_of_image("a.png") == (0, True)

    manager.add_new_image("y.jpeg", _ShouldPreserveIndex.NO)
    assert len(manager._files) == 5

    # Should not try to rename/convert when file with that name already exists
    with pytest.raises(FileExistsError):
        manager.rename_or_convert_current_image("c.webp")

    # Try to rename a.png mocking the os call away should pass
    with patch("os.rename", lambda *_: None):
        with (
            patch.object(
                ImageFileManager,
                "_ask_to_delete_old_image_after_convert",
                lambda *_: None,
            ),
            patch(
                "image_viewer.files.file_manager.askyesno",
                lambda *_: True,
            ),
        ):
            manager.rename_or_convert_current_image("example.test")

    # test remove_current_image functionality
    for _ in range(4):
        manager.remove_current_image()
    assert len(manager._files) == 1

    # Should raise index error after last file removed
    with pytest.raises(IndexError):
        manager.remove_current_image()


def test_bad_path(image_cache: ImageCache):
    # doesn't exist
    with pytest.raises(ValueError):
        file_manager = ImageFileManager("bad/path", image_cache)
        file_manager.validate_current_path()
    # wrong file type
    with pytest.raises(ValueError):
        file_manager = ImageFileManager(
            os.path.join(IMG_DIR, "not_an_image.txt"), image_cache
        )
        file_manager.validate_current_path()


@patch("image_viewer.files.file_manager.askyesno", lambda *_: False)
def test_bad_path_for_rename(manager: ImageFileManager):
    """When calling rename, certain conditions should raise errors"""
    with pytest.raises(OSError):
        manager.rename_or_convert_current_image(
            os.path.join("this/does/not/exist", "asdf.png")
        )
    # If path exists, error when user cancels (mocked in askyesno)
    with pytest.raises(OSError):
        manager.rename_or_convert_current_image(os.path.join(IMG_DIR, "a.png"))


def test_move_index(manager: ImageFileManager):
    """Test moving to an index that's too large"""
    manager.move_index(999)
    assert manager._files.display_index == 0


def test_delete_file(manager: ImageFileManager):
    """Tests deleting a file from disk via file manager"""

    # add one extra image so it doesn't error after removing the only file
    manager.add_new_image("Some_image.png", _ShouldPreserveIndex.NO)

    tempfile._TemporaryFileWrapper.close = safe_wrapper(  # type: ignore
        tempfile._TemporaryFileWrapper.close
    )

    with tempfile.NamedTemporaryFile() as tmp:
        manager.path_to_image = tmp.name
        manager.delete_current_image()
        assert len(manager._files) == 1


@pytest.mark.parametrize(
    "starting_display_index,preserve_index,insertion_index,expected_display_index",
    [
        (1, _ShouldPreserveIndex.NO, 1, 1),
        (1, _ShouldPreserveIndex.IF_INSERTED_AT_OR_BEFORE, 1, 2),
        (1, _ShouldPreserveIndex.YES, 1, 2),
        (2, _ShouldPreserveIndex.NO, 3, 2),
        (2, _ShouldPreserveIndex.IF_INSERTED_AT_OR_BEFORE, 3, 2),
        (2, _ShouldPreserveIndex.YES, 3, 3),
    ],
)
def test_add_new_image_adjusts_index(
    manager_with_3_images: ImageFileManager,
    starting_display_index: int,
    preserve_index: _ShouldPreserveIndex,
    insertion_index: int,
    expected_display_index: int,
):
    """Should stay on current image by moving one forward
    when respective preserve_index value passed"""

    manager_with_3_images._files._display_index = starting_display_index
    manager_with_3_images.add_new_image(
        "test.png", preserve_index=preserve_index, index=insertion_index
    )
    assert manager_with_3_images._files.display_index == expected_display_index


def test_undo(manager: ImageFileManager):
    """Test correct behavior adding/removing with undo"""
    with patch.object(
        ImageFileManager,
        "_ask_to_confirm_undo",
        return_value=False,
    ):
        assert not manager.undo_most_recent_action()

    file_to_restore = "b.png"
    file_to_remove = manager._files[0].name
    mock_undo_response = UndoResponse(file_to_restore, file_to_remove)
    with (
        patch.object(ImageFileManager, "_ask_to_confirm_undo", return_value=True),
        patch.object(
            ActionUndoer, "undo", return_value=mock_undo_response
        ) as mock_undo,
    ):
        manager.action_undoer = ActionUndoer()
        assert manager.undo_most_recent_action()
        assert len(manager._files) == 1
        assert manager._files[0].name == file_to_restore
        assert manager._files.display_index == 0

        mock_undo.assert_called_once()


def test_get_and_show_details(manager: ImageFileManager):
    """Should return a string containing details on current cached image and show it"""

    # Will exit if no details in cache
    PIL_image = MockImage()
    PIL_image.info["comment"] = b"test"

    details = manager.get_image_details(PIL_image)
    assert details is None

    for mode in ("P", "L", "1", "ANYTHING_ELSE"):
        manager.image_cache[manager.path_to_image] = ImageCacheEntry(
            PIL_image, (100, 100), "100kb", 9999, mode, ImageFormats.PNG
        )
        readable_mode = {"P": "Palette", "L": "Grayscale", "1": "Black And White"}.get(
            mode, mode
        )
        metadata: str = manager.get_cached_metadata()
        assert " bpp " + readable_mode in metadata
        assert ImageFormats.PNG in metadata

        metadata = manager.get_cached_metadata(get_all_details=False)
        assert metadata.count("\n") == 1
        assert " bpp " + readable_mode not in metadata
        assert ImageFormats.PNG not in metadata

    with patch.object(os, "stat", return_value=MockStatResult(0)):
        details = manager.get_image_details(PIL_image)
        assert details is not None
        assert "Created" in details
        assert "Comment" in details

    # Will not fail getting file metadata
    with patch.object(os, "stat", side_effect=OSError):
        details = manager.get_image_details(PIL_image)
        assert details is not None
        assert "Created" not in details


def test_split_with_weird_names(manager: ImageFileManager):
    """Should notice that . and .. are not file names, but part of path"""

    # use join over static var so test works on all OS
    expected_split = (os.path.normpath("C:/"), manager.current_image.name)
    assert manager._split_dir_and_name("C:/example/..") == expected_split

    # use join over static var so test works on all OS
    expected_split = (os.path.normpath("C:/example"), "...")
    assert manager._split_dir_and_name("C:/example/...") == expected_split


def test_move_to_new_file_cancelled(manager: ImageFileManager):
    """When user closes file dialog, function exits immediately"""
    with patch(
        "image_viewer.files.file_manager.FileDialogAsker.ask_open_image",
        return_value="",
    ):
        assert not manager.move_to_new_file()
