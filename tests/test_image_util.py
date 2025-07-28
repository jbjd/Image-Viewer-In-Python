from tkinter import Tk
from unittest.mock import patch

import pytest
from PIL.Image import Image, new

from image_viewer.config import DEFAULT_FONT
from image_viewer.constants import ImageFormats
from image_viewer.image.cache import ImageCache, ImageCacheEntry
from image_viewer.image.file import ImageName, magic_number_guess
from image_viewer.util.PIL import (
    create_dropdown_image,
    get_placeholder_for_errored_image,
    init_PIL,
    resize,
)
from tests.test_util.mocks import MockStatResult


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


@pytest.mark.parametrize(
    "magic_bytes,expected_format",
    [
        (b"\x89PNG", ImageFormats.PNG),
        (b"RIFF", ImageFormats.WEBP),
        (b"GIF8", ImageFormats.GIF),
        (b"DDS ", ImageFormats.DDS),
        (b"\xff\xd8\xff\xe0", ImageFormats.JPEG),
        (b"ABCD", ImageFormats.AVIF),  # default to AVIF
    ],
)
def test_magic_number_guess(magic_bytes: bytes, expected_format: ImageFormats):
    """Ensure correct image type guessed"""
    assert magic_number_guess(magic_bytes) == expected_format


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


def test_image_cache_fresh(image_cache: ImageCache):
    """Should say image cache is fresh if cached byte size
    is the same as size on disk"""

    image = Image()
    byte_size = 99
    entry = ImageCacheEntry(image, (10, 10), "", byte_size, "", "")

    path = "some/path"

    with patch("image_viewer.image.cache.stat", return_value=MockStatResult(byte_size)):
        # Empty
        assert not image_cache.image_cache_still_fresh(path)

        image_cache[path] = entry
        assert image_cache.image_cache_still_fresh(path)

    for error in [FileNotFoundError(), OSError()]:
        with patch("image_viewer.image.cache.stat", side_effect=error):
            assert not image_cache.image_cache_still_fresh(path)
