"""
Functions for manipulating PIL and PIL's image objects
"""

from PIL.ImageTk import PhotoImage
from PIL.Image import Image, Resampling
from PIL.Image import new
from PIL.ImageDraw import Draw, ImageDraw
from PIL.ImageFont import truetype


def _resize_new(
    image: Image,
    size: tuple[int, int],
    resample: Resampling,
    box: tuple[int, int, int, int],
) -> Image:
    """Preforms image resize and returns the new image"""
    return image._new(image.im.resize(size, resample, box))  # type: ignore


def resize(image: Image, size: tuple[int, int], resample: Resampling) -> Image:
    """Modified version of resize from PIL"""
    image.load()
    if image.size == size:
        return image

    box: tuple[int, int, int, int] = (0, 0) + image.size
    match image.mode:
        case "RGBA" | "LA":
            new_mode: str = f"{image.mode[:-1]}a"  # precomputed alpha
            return _resize_new(image.convert(new_mode), size, resample, box).convert(
                image.mode
            )
        case "P" | "1":
            image = image.convert("RGB")

    return _resize_new(image, size, resample, box)


def init_PIL(font_size: int) -> None:
    """Sets up font and PIL's internal list of plugins to load"""
    from PIL import Image

    # setup font
    ImageDraw.font = truetype("arial.ttf", font_size)
    ImageDraw.fontmode = "L"  # antialiasing

    # edit these so PIL will not waste time importing +20 useless modules
    Image._plugins = []  # type: ignore

    def preinit():
        __import__("PIL.JpegImagePlugin", globals(), locals(), ())
        __import__("PIL.GifImagePlugin", globals(), locals(), ())
        __import__("PIL.PngImagePlugin", globals(), locals(), ())
        __import__("PIL.WebPImagePlugin", globals(), locals(), ())
        __import__("PIL.TiffImagePlugin", globals(), locals(), ())

    Image.preinit = preinit


def create_dropdown_image(dimension_text: str, size_text: str) -> PhotoImage:
    """Creates a new photo image with current images metadata"""

    text_bbox: tuple[int, int, int, int] = ImageDraw.font.getbbox(dimension_text)
    x_offset: int = int(text_bbox[2] * 0.07)
    if x_offset < 10:
        x_offset = 10

    box_to_draw_on: ImageDraw = Draw(
        new(
            "RGBA",
            (text_bbox[2] + (x_offset << 1), text_bbox[3] * 5 + 10),
            (40, 40, 40, 170),
        ),
        "RGBA",
    )
    box_to_draw_on.text((10, text_bbox[3] + 5), dimension_text, fill="white")
    box_to_draw_on.text((10, int(text_bbox[3] * 3)), size_text, fill="white")
    return PhotoImage(box_to_draw_on._image)  # type: ignore
