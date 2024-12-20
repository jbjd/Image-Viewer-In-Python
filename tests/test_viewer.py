"""Viewer is hard to test due to being all UI code, testing what I can here"""

from tkinter import Tk
from unittest.mock import MagicMock, patch

import pytest

from image_viewer.constants import Key
from image_viewer.helpers.image_loader import ImageLoader
from image_viewer.ui.canvas import CustomCanvas
from image_viewer.viewer import ViewerApp
from tests.test_util.mocks import MockEvent, MockImage, MockImageFileManager


@pytest.fixture
def viewer(tk_app: Tk, image_loader: ImageLoader) -> ViewerApp:
    def mock_viewer_init(self, *_):
        self.app = tk_app
        self.height_ratio = 1
        self.width_ratio = 1
        self.image_loader = image_loader
        self.animation_id = ""

    with patch.object(ViewerApp, "__init__", mock_viewer_init):
        return ViewerApp("", "")


@pytest.fixture
def focused_event(tk_app: Tk) -> MockEvent:
    return MockEvent(tk_app)


@pytest.fixture
def unfocused_event() -> MockEvent:
    return MockEvent()


def test_pixel_scaling(viewer: ViewerApp):
    """Should correctly scale to screen size"""

    assert viewer._scale_pixels_to_height(1080) == 1080
    assert viewer._scale_pixels_to_width(1920) == 1920
    viewer.height_ratio = 2.21
    viewer.width_ratio = 1.21
    assert viewer._scale_pixels_to_height(1080) == 2386
    assert viewer._scale_pixels_to_width(1920) == 2323


def test_redraw(
    viewer: ViewerApp, focused_event: MockEvent, unfocused_event: MockEvent
):
    """Should only redraw when necessary"""

    viewer.need_to_redraw = True
    viewer.file_manager = MockImageFileManager()

    # Will immediately exit if widget is not tk app
    with patch.object(
        MockImageFileManager, "current_image_cache_still_fresh"
    ) as mock_check_cache:
        viewer.redraw(unfocused_event)
        mock_check_cache.assert_not_called()

    with patch.object(ViewerApp, "load_image_unblocking") as mock_refresh:
        # Will not refresh is cache is still fresh
        viewer.redraw(focused_event)
        mock_refresh.assert_not_called()

        # Will refresh when cache is stale
        viewer.need_to_redraw = True
        with patch.object(
            MockImageFileManager,
            "current_image_cache_still_fresh",
            side_effect=lambda: False,
        ) as mock_refresh:
            viewer.redraw(focused_event)
            mock_refresh.assert_called_once()


def test_clear_image(viewer: ViewerApp):
    """Should stop animations and ask image loader to also clear data"""
    with patch.object(Tk, "after_cancel") as mock_after_cancel:
        viewer.clear_image()
        mock_after_cancel.assert_not_called()

        viewer.animation_id = "123"

        with patch.object(ImageLoader, "reset_and_setup") as mock_reset:
            viewer.clear_image()
            mock_after_cancel.assert_called_once()
            mock_reset.assert_called_once()


def test_handle_key(
    viewer: ViewerApp, focused_event: MockEvent, unfocused_event: MockEvent
):
    """Should only accept input when user focused on main app"""

    with patch.object(ViewerApp, "toggle_show_rename_window") as mock_rename_window:
        focused_event.keycode = Key.R
        viewer.handle_key(unfocused_event)
        mock_rename_window.assert_not_called()

        viewer.handle_key(focused_event)
        mock_rename_window.assert_called_once()

    with patch.object(ViewerApp, "handle_lr_arrow") as mock_lr_arrow:
        focused_event.keycode = Key.LEFT
        viewer.handle_key(focused_event)
        mock_lr_arrow.assert_called_once()

    with patch.object(ViewerApp, "load_zoomed_image_unblocking") as mock_zoom:
        focused_event.keycode = Key.MINUS
        viewer.handle_key(focused_event)
        mock_zoom.assert_called_once()

        focused_event.keycode = Key.EQUALS
        viewer.handle_key(focused_event)
        assert mock_zoom.call_count == 2


def test_exit(viewer: ViewerApp, canvas: CustomCanvas):
    """Should clean up and exit"""
    viewer.canvas = canvas
    canvas.file_name_text_id = 0

    with patch.object(CustomCanvas, "delete") as mock_delete:
        with pytest.raises(SystemExit) as exception_cm:
            viewer.exit()
        assert exception_cm.value.code == 0
        mock_delete.assert_called_once()


def test_remove_image(viewer: ViewerApp):
    """Should remove image and exit when none left"""

    viewer.file_manager = MockImageFileManager()

    # When remove successful, does not call exit
    with (
        patch.object(MockImageFileManager, "remove_current_image") as mock_remove,
        patch.object(ViewerApp, "exit") as mock_exit,
    ):
        viewer.remove_current_image()
        mock_remove.assert_called_once()
        mock_exit.assert_not_called()

    # Removed last image, calls exit
    with patch.object(
        MockImageFileManager, "remove_current_image", side_effect=IndexError
    ):
        with patch.object(ViewerApp, "exit") as mock_exit:
            viewer.remove_current_image()
            mock_exit.assert_called_once()


def test_handle_rotate_animated_image(viewer: ViewerApp):
    """Should exit if animating. Should close the image if not currently animating,
    but the underlying image itself is an animation"""
    mock_event = MockEvent()
    viewer.file_manager = MockImageFileManager()

    with (
        patch.object(ViewerApp, "_currently_animating", lambda _: True),
        patch.object(ImageLoader, "read_image") as mock_read_image,
    ):
        viewer.handle_rotate_image(mock_event)
        mock_read_image.assert_not_called()

    with (
        patch.object(ImageLoader, "read_image", return_value=None) as mock_read_image,
        patch.object(
            MockImageFileManager, "rotate_image_and_save"
        ) as mock_rotate_image_and_save,
    ):
        viewer.handle_rotate_image(mock_event)
        mock_read_image.assert_called_once()
        mock_rotate_image_and_save.assert_not_called()

    mock_image = MockImage(n_frames=3)
    mock_image_response = MagicMock()
    mock_image_response.image = mock_image

    with patch.object(
        ImageLoader, "read_image", return_value=mock_image_response
    ) as mock_read_image:
        viewer.handle_rotate_image(mock_event)
        mock_read_image.assert_called_once()
        assert mock_image.closed
