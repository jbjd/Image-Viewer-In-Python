from cv2 import resize
from cv2.typing import MatLike
from numpy import asarray
from PIL.Image import Image, fromarray
from PIL.ImageTk import PhotoImage


def image_to_array(image: Image):
    """Turns a PIL Image into a Numpy array"""
    return asarray(
        image if image.mode != "P" else image.convert("RGB"),
        order="C",
    )


def array_to_photoimage(
    array: MatLike, dimensions: tuple[int, int], interpolation: int
) -> PhotoImage:
    """Converts and resizes a matrix-like into a PhotoImage fit to the screen"""
    return PhotoImage(fromarray(resize(array, dimensions, interpolation=interpolation)))
