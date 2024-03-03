"""
Functions for manipulating PIL and PIL's image objects
"""

from textwrap import wrap

from PIL import Image as _Image  # avoid name conflicts
from PIL.Image import Image, Resampling, new, register_open
from PIL.ImageDraw import Draw, ImageDraw
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
    match image.mode:
        case "RGBA" | "LA":
            new_mode: str = f"{image.mode[:-1]}a"  # precomputed alpha
            return _resize_new(image.convert(new_mode), size, resample, box).convert(
                image.mode
            )
        case "P" | "1":
            image = image.convert("RGB")

    return _resize_new(image, size, resample, box)


def _get_longest_line_bbox(input: str) -> tuple[int, int, int, int]:
    """Returns bbox of longest length string in a string with multiple lines"""
    return ImageDraw.font.getbbox(max(input.split("\n"), key=len))


def create_dropdown_image(text: str) -> PhotoImage:
    """Creates a new photo image with current images metadata"""
    text_bbox: tuple[int, int, int, int] = _get_longest_line_bbox(text)

    x_offset: int = max(int(text_bbox[2] * 0.07), 10)
    line_height: int = text_bbox[3] + text_bbox[1]
    spacing: int = int(line_height * 0.8)
    line_count: int = text.count("\n") + 1

    width: int = text_bbox[2] + x_offset + x_offset
    height: int = (line_height * line_count) + (spacing * (line_count + 1))
    DROPDOWN_RGBA: tuple[int, int, int, int] = (40, 40, 40, 170)

    draw: ImageDraw = Draw(new("RGBA", (width, height), DROPDOWN_RGBA))
    draw.text((10, spacing), text, fill="white", spacing=spacing)

    return PhotoImage(draw._image)  # type: ignore


def _write_placeholder_text(
    draw: ImageDraw, x_offset: int, y_offset: int, text: str
) -> None:
    """Curried function for writing placeholder text"""
    draw.text(
        (
            x_offset,
            y_offset,
        ),
        text,
        TEXT_RGB,
    )


def get_placeholder_for_errored_image(
    error: Exception, screen_width: int, screen_height: int
) -> PhotoImage:
    """Returns a PhotoImage with error message to display"""
    error_title: str = f"{type(error).__name__} occurred while trying to load file"

    # Wrap each individual line, then join to preserve already existing new lines
    formated_error: str = "\n".join(
        ["\n".join(wrap(line, 100)) for line in str(error).split("\n")]
    ).capitalize()

    draw: ImageDraw = Draw(new("RGB", (screen_width, screen_height)))
    draw.line((0, 0, screen_width, screen_height), (30, 20, 20), width=100)

    # Write title
    *_, w, h = ImageDraw.font.getbbox(error_title)
    y_offset: int = screen_height - (h * (5 + formated_error.count("\n"))) >> 1
    x_offset: int = (screen_width - w) >> 1
    _write_placeholder_text(draw, x_offset, y_offset, error_title)

    # Write error body 2 lines of height below title
    *_, w, h = _get_longest_line_bbox(formated_error)
    y_offset += h * 2
    x_offset = (screen_width - w) >> 1
    _write_placeholder_text(draw, x_offset, y_offset, formated_error)

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
    from PIL import ImageDraw as _ImageDraw  # avoid name conflicts
    from PIL.ImageFont import truetype

    ImageDraw.font = truetype("arial.ttf", font_size)
    ImageDraw.fontmode = "L"  # antialiasing
    _ImageDraw.Draw = lambda im, mode=None: ImageDraw(im, mode)
    del _ImageDraw, truetype

    _stop_unwanted_PIL_imports()
