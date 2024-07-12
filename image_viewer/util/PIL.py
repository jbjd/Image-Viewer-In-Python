"""
Functions for manipulating PIL and PIL's image objects
"""

from textwrap import wrap
from typing import IO

from PIL import Image as _Image  # avoid name conflicts
from PIL.Image import Image, Resampling, new, register_open
from PIL.ImageDraw import ImageDraw
from PIL.ImageTk import PhotoImage
from PIL.JpegImagePlugin import JpegImageFile

from constants import TEXT_RGB, Rotation


def save_image(
    image: Image,
    fp: str | IO[bytes],
    format: str | None = None,
    quality: int = 90,
    is_animated: bool | None = None,
) -> None:
    """Saves a PIL image to disk"""
    save_all: bool = image_is_animated(image) if is_animated is None else is_animated
    image.save(fp, format, optimize=True, method=6, quality=quality, save_all=save_all)


def rotate_image(image: Image, angle: Rotation) -> Image:
    """Rotates an image with the highest quality"""
    return image.rotate(angle, Resampling.LANCZOS, expand=True)


def image_is_animated(image: Image) -> bool:
    """Returns True if PIL Image is animated"""
    return getattr(image, "is_animated", False)


def _resize_new(
    image: Image,
    size: tuple[int, int],
    resample: Resampling,
    box: tuple[int, int, int, int],
) -> Image:
    """Performs image resize and returns the new image"""
    return image._new(image.im.resize(size, resample, box))  # type: ignore


def resize(
    image: Image, size: tuple[int, int], resample: Resampling = Resampling.LANCZOS
) -> Image:
    """Modified version of resize from PIL"""
    image.load()
    if image.size == size:
        return image.copy()

    box: tuple[int, int, int, int] = (0, 0) + image.size
    original_mode: str = image.mode
    modes_to_convert: dict[str, str] = {
        "RGBA": "RGBa",
        "LA": "La",
        "P": "RGB",
        "1": "RGB",
    }

    if original_mode in modes_to_convert:
        new_mode: str = modes_to_convert[original_mode]
        image = image.convert(new_mode)

    resized_image: Image = _resize_new(image, size, resample, box)

    # These mode were temporarily converted to pre-compute alpha and should be reverted
    if original_mode in ("RGBA", "LA"):
        resized_image = resized_image.convert(original_mode)

    return resized_image


def _get_longest_line_dimensions(input: str) -> tuple[int, int]:
    """Returns width and height of longest string in a string with multiple lines"""
    longest_line: str = max(input.split("\n"), key=len)

    width_offset, height_offset, width, height = ImageDraw.font.getbbox(  # type: ignore
        longest_line
    )

    return int(width + width_offset), int(height + height_offset)


def create_dropdown_image(text: str) -> PhotoImage:
    """Creates a new PhotoImage with current images metadata"""
    line_width, line_height = _get_longest_line_dimensions(text)

    line_count: int = text.count("\n") + 1
    line_spacing: int = round(line_height * 0.8)

    x_padding: int = max(int(line_width * 0.14), 20)
    y_padding: int = line_spacing * (line_count + 1)

    width: int = line_width + x_padding
    height: int = (line_height * line_count) + y_padding

    DROPDOWN_RGBA: tuple[int, int, int, int] = (40, 40, 40, 170)
    image: Image = new("RGBA", (width, height), DROPDOWN_RGBA)

    draw: ImageDraw = ImageDraw(image)
    draw.text((10, line_spacing), text, fill="white", spacing=line_spacing)

    return PhotoImage(draw._image)


def get_placeholder_for_errored_image(
    error: Exception, screen_width: int, screen_height: int
) -> Image:
    """Returns an Image with error message"""
    error_type: str = type(error).__name__
    error_title: str = f"{error_type} occurred while trying to load file"

    # Wrap each individual line, then join to preserve already existing new lines
    error_text: str = str(error)
    formated_error: str = "\n".join(
        ["\n".join(wrap(line, 100)) for line in error_text.split("\n")]
    ).capitalize()

    # Placeholder is black with brownish line going diagonally across
    blank_image: Image = new("RGB", (screen_width, screen_height))
    draw: ImageDraw = ImageDraw(blank_image)
    LINE_RGB: tuple[int, int, int] = (30, 20, 20)
    draw.line((0, 0, screen_width, screen_height), LINE_RGB, width=100)

    # Write title
    w: int
    h: int
    *_, w, h = ImageDraw.font.getbbox(error_title)  # type: ignore
    y_offset: int = screen_height - (h * (5 + formated_error.count("\n"))) >> 1
    x_offset: int = (screen_width - w) >> 1
    draw.text((x_offset, y_offset), error_title, TEXT_RGB)

    # Write error body 2 lines of height below title
    w, h = _get_longest_line_dimensions(formated_error)
    y_offset += h * 2
    x_offset = (screen_width - w) >> 1
    draw.text((x_offset, y_offset), formated_error, TEXT_RGB)

    return draw._image


def _preinit() -> None:  # pragma: no cover
    """Edited version of PIL's preinit to be used as a replacement"""
    if _Image._initialized > 0:
        return

    __import__("PIL.JpegImagePlugin", globals(), locals(), ())
    __import__("PIL.GifImagePlugin", globals(), locals(), ())
    __import__("PIL.PngImagePlugin", globals(), locals(), ())
    __import__("PIL.WebPImagePlugin", globals(), locals(), ())

    def new_jpeg_factory(fp=None, filename=None) -> JpegImageFile:
        return JpegImageFile(fp, filename)

    register_open(
        "JPEG",
        new_jpeg_factory,
        lambda prefix: prefix[:3] == b"\xFF\xD8\xFF",
    )

    _Image._initialized = 2


def _stop_unwanted_PIL_imports() -> None:
    """Edits parts of PIL module to prevent excessive imports"""
    from PIL.JpegImagePlugin import MARKER, Skip

    # Remove calls to "APP" since its only for exif and uses removed Tiff plugin
    # Can't edit APP directly due to PIL storing it in this dict
    for i in range(0xFFE0, 0xFFF0):
        MARKER[i] = ("", "", Skip)
    del MARKER, Skip

    # Edit plugins and preinit to avoid importing many unused image modules
    _Image._plugins = []
    _Image.preinit = _preinit


def init_PIL(font_path: str, font_size: int) -> None:
    """Sets up font and edit PIL's internal list of plugins to load"""
    from PIL.ImageFont import truetype

    ImageDraw.font = truetype(font_path, font_size)
    del truetype

    _stop_unwanted_PIL_imports()
