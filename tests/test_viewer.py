"""Viewer is hard to test due to being all UI code, testing what I can here"""

from tkinter import Tk
from unittest.mock import patch

import pytest

from image_viewer.constants import Key
from image_viewer.files.file_manager import ImageFileManager
from image_viewer.image.loader import ImageLoader
from image_viewer.ui.canvas import CustomCanvas
from image_viewer.viewer import ViewerApp
from tests.test_util.mocks import MockEvent


def test_pixel_scaling(partial_viewer: ViewerApp):
    """Should correctly scale to screen size"""

    partial_viewer.height_ratio = 1
    partial_viewer.width_ratio = 1
    assert partial_viewer._scale_pixels_to_height(1080) == 1080
    assert partial_viewer._scale_pixels_to_width(1920) == 1920

    partial_viewer.height_ratio = 2.21
    partial_viewer.width_ratio = 1.21
    assert partial_viewer._scale_pixels_to_height(1080) == 2386
    assert partial_viewer._scale_pixels_to_width(1920) == 2323


def test_redraw(
    partial_viewer: ViewerApp, focused_event: MockEvent, unfocused_event: MockEvent
):
    """Should only redraw when necessary"""

    partial_viewer.need_to_redraw = True

    # Will immediately exit if widget is not tk app
    with patch.object(
        ImageFileManager, "current_image_cache_still_fresh"
    ) as mock_check_cache:
        partial_viewer.redraw(unfocused_event)
        mock_check_cache.assert_not_called()

    with patch.object(ViewerApp, "load_image_unblocking") as mock_refresh:
        with patch.object(
            ImageFileManager,
            "current_image_cache_still_fresh",
            side_effect=lambda: True,
        ):
            partial_viewer.redraw(focused_event)
            mock_refresh.assert_not_called()

        partial_viewer.need_to_redraw = True
        with patch.object(
            ImageFileManager,
            "current_image_cache_still_fresh",
            side_effect=lambda: False,
        ):
            partial_viewer.redraw(focused_event)
            mock_refresh.assert_called_once()


def test_clear_image(partial_viewer: ViewerApp):
    """Should stop animations and ask image loader to also clear data"""
    with patch.object(Tk, "after_cancel") as mock_after_cancel:
        partial_viewer.clear_image()
        mock_after_cancel.assert_not_called()

        partial_viewer.animation_id = "123"

        with patch.object(ImageLoader, "reset_and_setup") as mock_reset:
            partial_viewer.clear_image()
            mock_after_cancel.assert_called_once()
            mock_reset.assert_called_once()


def test_handle_key(partial_viewer: ViewerApp, focused_event: MockEvent):
    """Should only accept input when user focused on main app"""

    with patch.object(ViewerApp, "handle_lr_arrow") as mock_lr_arrow:
        focused_event.keysym_num = Key.LEFT
        partial_viewer.handle_key(focused_event)
        mock_lr_arrow.assert_called_once()

    with patch.object(
        ViewerApp, "load_zoomed_or_rotated_image_unblocking"
    ) as mock_zoom:
        focused_event.keysym_num = Key.MINUS
        partial_viewer.handle_key(focused_event)
        mock_zoom.assert_called_once()

        focused_event.keysym_num = Key.EQUALS
        partial_viewer.handle_key(focused_event)
        assert mock_zoom.call_count == 2


def test_exit(partial_viewer: ViewerApp, canvas: CustomCanvas):
    """Should clean up and exit"""

    # Cleans up properly when not fully initialized
    with pytest.raises(SystemExit) as exception_cm:
        partial_viewer.exit(exit_code=1)
    assert exception_cm.value.code == 1

    partial_viewer.canvas = canvas
    canvas.file_name_text_id = 0

    with patch.object(CustomCanvas, "delete") as mock_delete:
        with pytest.raises(SystemExit) as exception_cm:
            partial_viewer.exit()
        assert exception_cm.value.code == 0
        mock_delete.assert_called_once()


def test_remove_image(partial_viewer: ViewerApp):
    """Should remove image and exit when none left"""

    # When remove successful, does not call exit
    with (
        patch.object(ImageFileManager, "remove_current_image") as mock_remove,
        patch.object(ViewerApp, "exit") as mock_exit,
    ):
        partial_viewer.remove_current_image()
        mock_remove.assert_called_once()
        mock_exit.assert_not_called()

    # Removed last image, calls exit
    with patch.object(ImageFileManager, "remove_current_image", side_effect=IndexError):
        with patch.object(ViewerApp, "exit") as mock_exit:
            partial_viewer.remove_current_image()
            mock_exit.assert_called_once()


def test_minimize(partial_viewer: ViewerApp):
    """Should mark that app needs to be redrawn and
    cancel scheduled moved functions"""

    with (
        patch.object(Tk, "after_cancel") as mock_after_cancel,
        patch.object(Tk, "iconify") as mock_iconify,
    ):
        partial_viewer.minimize()
        assert partial_viewer.need_to_redraw
        assert mock_iconify.call_count == 1
        assert mock_after_cancel.call_count == 0

        partial_viewer.need_to_redraw = False
        partial_viewer.move_id = "12"
        partial_viewer.minimize()
        assert partial_viewer.need_to_redraw
        assert mock_iconify.call_count == 2
        assert mock_after_cancel.call_count == 1
