"""So viewer is hard to test due to being all UI code"""
from unittest import mock

from image_viewer.viewer import ViewerApp


def test_pixel_scaling():
    def mock_set_ratios(self, *_):
        self.height_ratio = 1
        self.width_ratio = 1

    with mock.patch.object(ViewerApp, "__init__", mock_set_ratios):
        mock_viewer = ViewerApp("", "")
        assert mock_viewer._scale_pixels_to_height(1080) == 1080
        assert mock_viewer._scale_pixels_to_width(1920) == 1920
        mock_viewer.height_ratio = 2.21
        mock_viewer.width_ratio = 1.21
        assert mock_viewer._scale_pixels_to_height(1080) == 2386
        assert mock_viewer._scale_pixels_to_width(1920) == 2323
