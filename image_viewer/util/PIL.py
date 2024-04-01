"""
Functions for manipulating PIL and PIL's image objects
"""

from textwrap import wrap

from PIL import Image as _Image  # avoid name conflicts
from PIL.Image import Image, Resampling, new, register_open
from PIL.ImageDraw import ImageDraw
from PIL.ImageTk import PhotoImage
from PIL.JpegImagePlugin import JpegImageFile

from constants import TEXT_RGB


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
        return image

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


def get_image_draw(image: Image, mode=None) -> ImageDraw:
    """Turns PIL Image into PIL ImageDraw.
    This is a simplified version of PIL's Draw function"""
    return ImageDraw(image, mode)


def _get_longest_line_bbox(input: str) -> tuple[int, int, int, int]:
    """Returns bbox of longest length string in a string with multiple lines"""
    return ImageDraw.font.getbbox(max(input.split("\n"), key=len))


def create_dropdown_image(text: str) -> PhotoImage:
    """Creates a new PhotoImage with current images metadata"""
    text_bbox: tuple[int, int, int, int] = _get_longest_line_bbox(text)

    line_count: int = text.count("\n") + 1
    line_height: int = text_bbox[3] + text_bbox[1]
    line_spacing: int = round(line_height * 0.8)

    x_padding: int = max(int(text_bbox[2] * 0.14), 20)
    y_padding: int = line_spacing * (line_count + 1)

    width: int = text_bbox[2] + x_padding
    height: int = (line_height * line_count) + y_padding

    DROPDOWN_RGBA: tuple[int, int, int, int] = (40, 40, 40, 170)
    image: Image = new("RGBA", (width, height), DROPDOWN_RGBA)

    draw: ImageDraw = get_image_draw(image)
    draw.text((10, line_spacing), text, fill="white", spacing=line_spacing)

    return PhotoImage(draw._image)  # type: ignore


def get_placeholder_for_errored_image(
    error: Exception, screen_width: int, screen_height: int
) -> PhotoImage:
    """Returns a PhotoImage with error message to display"""
    error_title: str = f"{type(error).__name__} occurred while trying to load file"

    # Wrap each individual line, then join to preserve already existing new lines
    formated_error: str = "\n".join(
        ["\n".join(wrap(line, 100)) for line in str(error).split("\n")]
    ).capitalize()

    blank_image: Image = new("RGB", (screen_width, screen_height))
    draw: ImageDraw = get_image_draw(blank_image)
    draw.line((0, 0, screen_width, screen_height), (30, 20, 20), width=100)

    # Write title
    *_, w, h = ImageDraw.font.getbbox(error_title)
    y_offset: int = screen_height - (h * (5 + formated_error.count("\n"))) >> 1
    x_offset: int = (screen_width - w) >> 1
    draw.text((x_offset, y_offset), error_title, TEXT_RGB)

    # Write error body 2 lines of height below title
    *_, w, h = _get_longest_line_bbox(formated_error)
    y_offset += h * 2
    x_offset = (screen_width - w) >> 1
    draw.text((x_offset, y_offset), formated_error, TEXT_RGB)

    return PhotoImage(draw._image)  # type: ignore


def _preinit() -> None:  # pragma: no cover
    """Edited version of PIL's preinit to be used as a replacement"""
    if _Image._initialized > 0:  # type: ignore
        return

    __import__("PIL.JpegImagePlugin", globals(), locals(), ())
    __import__("PIL.GifImagePlugin", globals(), locals(), ())
    __import__("PIL.PngImagePlugin", globals(), locals(), ())
    __import__("PIL.WebPImagePlugin", globals(), locals(), ())

    register_open(
        "JPEG",
        lambda fp=None, filename=None: JpegImageFile(fp, filename),
        lambda prefix: prefix[:3] == b"\xFF\xD8\xFF",
    )

    _Image._initialized = 2  # type: ignore


def _stop_unwanted_PIL_imports() -> None:
    """Edits parts of PIL module to prevent excessive imports"""
    from PIL.JpegImagePlugin import MARKER, Skip

    # Remove calls to "APP" since its only for exif and uses removed Tiff plugin
    # Can't edit APP directly due to PIL storing it in this dict
    for i in range(0xFFE0, 0xFFF0):
        MARKER[i] = ("", "", Skip)
    del MARKER, Skip

    # Edit plugins and preinit to avoid importing many unused image modules
    _Image._plugins = []  # type: ignore
    _Image.preinit = _preinit


def init_PIL(font_size: int) -> None:
    """Sets up font and edit PIL's internal list of plugins to load"""
    from PIL.ImageFont import truetype

    ImageDraw.font = truetype("arial.ttf", font_size)
    ImageDraw.fontmode = "L"  # antialiasing
    del truetype

    _stop_unwanted_PIL_imports()
