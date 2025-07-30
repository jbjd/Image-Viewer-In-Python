from tkinter import Tk
from unittest.mock import MagicMock, patch

from PIL.Image import Image, new

from image_viewer.config import DEFAULT_FONT
from image_viewer.constants import ImageFormats
from image_viewer.image.file import ImageName
from image_viewer.util.PIL import (
    _preinit,
    create_dropdown_image,
    get_placeholder_for_errored_image,
    init_PIL,
    resize,
)


def test_image_path():
    """Check that ImageName correctly finds image suffixes"""
    example_image_path = ImageName("some_image.1.PNG")
    assert example_image_path.suffix == "png"

    example_image_path = ImageName("some_file.")
    assert example_image_path.suffix == ""

    example_image_path = ImageName("some_file")
    assert example_image_path.suffix == ""


def test_init_PIL():
    """Should remove all values from _plugins and set default font"""
    from PIL import Image as _Image
    from PIL.ImageDraw import ImageDraw

    init_PIL(DEFAULT_FONT, 20)
    assert len(_Image._plugins) == 0
    assert ImageDraw.font is not None

    del _Image
    del ImageDraw


def test_create_images(tk_app: Tk):
    init_PIL(DEFAULT_FONT, 20)

    dropdown = create_dropdown_image("test\ntest")
    assert isinstance(dropdown, Image)

    example_error = Exception("test")
    placeholder: Image = get_placeholder_for_errored_image(example_error, 10, 10)

    assert isinstance(placeholder, Image)


def test_resize():
    """Test a variety of PIL Image resize scenarios"""

    example_image = new("P", (10, 10))

    same_size_image = resize(example_image, (10, 10))

    # Will not resize to the same dimensions
    assert same_size_image == example_image

    new_image = resize(example_image, (20, 20))

    assert new_image.size == (20, 20)
    assert new_image.mode == "RGB"  # P or 1 type images should convert to RGB

    new_image = resize(new_image.convert("RGBA"), (15, 15))

    assert new_image.size == (15, 15)


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
