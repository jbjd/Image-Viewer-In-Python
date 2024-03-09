"""Viewer is hard to test due to being all UI code, testing what I can here"""

import pytest

from tkinter import Tk
from unittest.mock import patch
from image_viewer.helpers.image_loader import ImageLoader

from image_viewer.viewer import ViewerApp
from test_util.mocks import MockEvent, MockImageFileManager


@pytest.fixture
def viewer(tk_app: Tk) -> ViewerApp:
    def mock_viewer_init(self, *_):
        self.app = tk_app
        self.height_ratio = 1
        self.width_ratio = 1

    with patch.object(ViewerApp, "__init__", mock_viewer_init):
        return ViewerApp("", "")


def test_pixel_scaling(viewer: ViewerApp):
    """Should correctly scale to screen size"""

    assert viewer._scale_pixels_to_height(1080) == 1080
    assert viewer._scale_pixels_to_width(1920) == 1920
    viewer.height_ratio = 2.21  # type: ignore
    viewer.width_ratio = 1.21  # type: ignore
    assert viewer._scale_pixels_to_height(1080) == 2386
    assert viewer._scale_pixels_to_width(1920) == 2323


def test_redraw(viewer: ViewerApp, tk_app: Tk):
    """Should only redraw when necessary"""

    viewer.need_to_redraw = True
    viewer.file_manager = MockImageFileManager()

    # Will immediately exit if widget is not tk app
    with patch.object(
        MockImageFileManager, "current_image_cache_still_fresh"
    ) as mock_check_cache:
        viewer.redraw(MockEvent(widget=None))
        mock_check_cache.assert_not_called()

    correct_event = MockEvent(widget=tk_app)
    with patch.object(ViewerApp, "load_image_unblocking") as mock_refresh:
        # Will not refresh is cache is still fresh
        viewer.redraw(correct_event)
        mock_refresh.assert_not_called()

        # Will refresh when cache is stale
        viewer.need_to_redraw = True
        viewer.file_manager.current_image_cache_still_fresh = lambda: False
        viewer.redraw(correct_event)
        mock_refresh.assert_called_once()


def test_clear_image(viewer: ViewerApp, image_loader: ImageLoader):
    """Should stop animations and ask image loader to also clear data"""

    viewer.image_loader = image_loader
    viewer.animation_id = ""

    with patch.object(Tk, "after_cancel") as mock_after_cancel:
        viewer.clear_image()
        mock_after_cancel.assert_not_called()

        viewer.animation_id = "123"

        with patch.object(ImageLoader, "reset_and_setup") as mock_reset:
            viewer.clear_image()
            mock_after_cancel.assert_called_once()
            mock_reset.assert_called_once()
