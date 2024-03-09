"""Viewer is hard to test due to being all UI code, testing what I can here"""

from tkinter import Tk
from unittest.mock import patch

from image_viewer.viewer import ViewerApp
from test_util.mocks import MockEvent, MockImageFileManager


def test_pixel_scaling():
    def mock_viewer_init(self, *_):
        self.height_ratio = 1
        self.width_ratio = 1

    with patch.object(ViewerApp, "__init__", mock_viewer_init):
        mock_viewer = ViewerApp("", "")
        assert mock_viewer._scale_pixels_to_height(1080) == 1080
        assert mock_viewer._scale_pixels_to_width(1920) == 1920
        mock_viewer.height_ratio = 2.21  # type: ignore
        mock_viewer.width_ratio = 1.21  # type: ignore
        assert mock_viewer._scale_pixels_to_height(1080) == 2386
        assert mock_viewer._scale_pixels_to_width(1920) == 2323


def test_redraw(tk_app: Tk):
    """Should only redraw when necessary"""

    def mock_viewer_init(self, *_):
        self.app = tk_app
        self.need_to_redraw = True
        self.file_manager = MockImageFileManager()

    with patch.object(ViewerApp, "__init__", mock_viewer_init):
        mock_viewer = ViewerApp("", "")

        # Will immediately exit if widget is not tk app
        with patch.object(
            MockImageFileManager, "current_image_cache_still_fresh"
        ) as mock_check_cache:
            mock_viewer.redraw(MockEvent(widget=None))
            mock_check_cache.assert_not_called()

        correct_event = MockEvent(widget=tk_app)
        with patch.object(ViewerApp, "load_image_unblocking") as mock_refresh:
            # Will not refresh is cache is still fresh
            mock_viewer.redraw(correct_event)
            mock_refresh.assert_not_called()

            # Will refresh when cache is stale
            mock_viewer.need_to_redraw = True
            mock_viewer.file_manager.current_image_cache_still_fresh = lambda: False
            mock_viewer.redraw(correct_event)
            mock_refresh.assert_called_once()
