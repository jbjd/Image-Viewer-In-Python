from tkinter import Tk

from PIL import Image
from PIL.ImageTk import PhotoImage

from image_viewer.util.image import DropdownImage, ImagePath
from image_viewer.util.PIL import create_dropdown_image, init_PIL


def test_image_path():
    """Check that ImagePath correctly finds image suffixes"""
    example_image_path = ImagePath("some_image.1.PNG")
    assert example_image_path.suffix == "png"

    example_image_path = ImagePath("some_file.")
    assert example_image_path.suffix == ""

    example_image_path = ImagePath("some_file")
    assert example_image_path.suffix == "some_file"


def test_PIL_functions():
    """Ensure no error with font and that PIL.Image gets modified"""
    init_PIL(20)
    assert len(Image._plugins) == 0  # type: ignore

    # create_dropdown_image needs Tk to be initialized before calling
    _ = Tk()
    assert isinstance(create_dropdown_image("test", "test"), PhotoImage)


def test_dropdown_image():
    """Ensures basic functionality of dropdown image container"""
    dropdown = DropdownImage(123)
    dropdown.toggle_display()
    assert dropdown.showing
