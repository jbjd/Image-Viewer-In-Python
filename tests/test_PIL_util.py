from unittest.mock import MagicMock, patch

from image_viewer.util.PIL import _preinit
from image_viewer.constants import ImageFormats


def test_preinit():
    """Should import supported formats and set PIL as initialized"""

    supported_formats: set[str] = {
        "PIL.AvifImagePlugin",
        "PIL.JpegImagePlugin",
        "PIL.GifImagePlugin",
        "PIL.PngImagePlugin",
        "PIL.WebPImagePlugin",
        "PIL.DdsImagePlugin",
    }

    assert len(supported_formats) == len(
        ImageFormats
    ), "Test not accounting for all supported formats"

    mock_import = MagicMock()
    mock_register_open = MagicMock()
    mock_image_module = MagicMock()
    mock_image_module._initialized = 0

    with (
        patch("builtins.__import__", mock_import),
        patch("image_viewer.util.PIL._Image", mock_image_module),
        patch("image_viewer.util.PIL.register_open", mock_register_open),
    ):
        _preinit()

    mock_register_open.assert_called_once()

    # 2 is PIL's marker for everything initialized
    assert mock_image_module._initialized == 2

    # Throw out irrelevant imports since some others happen during the call
    imported_formats: set[str] = set(
        imported_format
        for inputs in mock_import.call_args_list
        if (imported_format := inputs[0][0]) in supported_formats
    )

    assert supported_formats == imported_formats


def test_preinit_already_initialized():
    """Should do nothing since already initialized"""

    mock_register_open = MagicMock()
    mock_image_module = MagicMock()
    mock_image_module._initialized = 2

    with (
        patch("image_viewer.util.PIL._Image", mock_image_module),
        patch("image_viewer.util.PIL.register_open", mock_register_open),
    ):
        _preinit()

    mock_register_open.assert_not_called()
