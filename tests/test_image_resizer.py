from image_viewer.helpers.image_resizer import ImageResizer


def test_jpeg_scale_factor(image_resizer: ImageResizer):
    """Test that correct ratios returns for a 1080x1920 screen"""
    assert image_resizer._get_jpeg_scale_factor(9999, 9999) == (1, 4)
    assert image_resizer._get_jpeg_scale_factor(3000, 3000) == (1, 2)
    assert image_resizer._get_jpeg_scale_factor(1, 1) is None
