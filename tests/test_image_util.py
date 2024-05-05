from tkinter import Tk

from PIL import Image
from PIL.ImageTk import PhotoImage

from image_viewer.util.image import ImageName, magic_number_guess
from image_viewer.util.PIL import (
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


def test_PIL_functions(tk_app: Tk):
    """Ensure no error with font and that PIL.Image gets modified"""
    init_PIL(20)
    assert len(Image._plugins) == 0  # type: ignore

    assert isinstance(create_dropdown_image("test\ntest"), PhotoImage)

    # need to test this here since init_PIL must be called first
    example_error = Exception("test")
    placeholder: Image.Image = get_placeholder_for_errored_image(example_error, 10, 10)

    assert type(placeholder) is Image.Image


def test_magic_number_guess():
    """Ensure correct image type guessed"""
    assert magic_number_guess(b"\x89PNG")[0] == "PNG"

    assert magic_number_guess(b"RIFF")[0] == "WEBP"

    assert magic_number_guess(b"GIF8")[0] == "GIF"

    # When nothing else matches, guess jpeg
    assert magic_number_guess(b"ABCD")[0] == "JPEG"


def test_resize():
    """Test a variety of PIL Image resize scenarios"""

    example_image = Image.new("P", (10, 10))

    same_size_image = resize(example_image, (10, 10))

    # Will not resize to the same dimensions
    assert same_size_image == example_image

    new_image = resize(example_image, (20, 20))

    assert new_image.size == (20, 20)
    assert new_image.mode == "RGB"  # P or 1 type images should convert to RGB

    new_image = resize(new_image.convert("RGBA"), (15, 15))

    assert new_image.size == (15, 15)
