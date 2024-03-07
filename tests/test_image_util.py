from tkinter import Tk

from PIL import Image
from PIL.ImageTk import PhotoImage

from image_viewer.util.image import ImageName, magic_number_guess
from image_viewer.util.PIL import create_dropdown_image, init_PIL


def test_image_path():
    """Check that ImageName correctly finds image suffixes"""
    example_image_path = ImageName("some_image.1.PNG")
    assert example_image_path.suffix == "png"

    example_image_path = ImageName("some_file.")
    assert example_image_path.suffix == ""

    example_image_path = ImageName("some_file")
    assert example_image_path.suffix == "some_file"


def test_PIL_functions(tk_app: Tk):
    """Ensure no error with font and that PIL.Image gets modified"""
    init_PIL(20)
    assert len(Image._plugins) == 0  # type: ignore

    assert isinstance(create_dropdown_image("test\ntest"), PhotoImage)


def test_magic_number_guess():
    """Ensure correct image type guessed"""
    assert magic_number_guess(b"\x89PNG")[0] == "PNG"

    assert magic_number_guess(b"RIFF")[0] == "WEBP"

    assert magic_number_guess(b"GIF8")[0] == "GIF"

    # When nothing else matches, guess jpeg
    assert magic_number_guess(b"ABCD")[0] == "JPEG"
