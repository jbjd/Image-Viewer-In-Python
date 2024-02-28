"""
Functions for manipulating PIL and PIL's image objects
"""

from PIL.Image import Image, Resampling, new, register_open
from PIL.ImageDraw import Draw, ImageDraw
from PIL.ImageTk import PhotoImage


def _resize_new(
    image: Image,
    size: tuple[int, int],
    resample: Resampling,
    box: tuple[int, int, int, int],
) -> Image:
    """Preforms image resize and returns the new image"""
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


def init_PIL(font_size: int) -> None:
    """Sets up font and edit PIL's internal list of plugins to load"""
    from PIL import Image as _Image  # avoid name conflicts
    from PIL import ImageDraw as _ImageDraw
    from PIL import JpegImagePlugin
    from PIL.ImageFont import truetype
    from PIL.JpegImagePlugin import JpegImageFile

    ImageDraw.font = truetype("arial.ttf", font_size)
    ImageDraw.fontmode = "L"  # antialiasing
    _ImageDraw.Draw = lambda im, mode=None: ImageDraw(im, mode)
    del truetype

    # Remove calls to "APP" since its only for exif and uses removed Tiff plugin
    for i in range(0xFFE0, 0xFFF0):
        JpegImagePlugin.MARKER[i] = ("", "", None)
    del JpegImagePlugin

    # edit these so PIL will not waste time importing +20 useless modules
    _Image._plugins = []  # type: ignore

    def preinit() -> None:  # pragma: no cover
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

    _Image.preinit = preinit
    del _ImageDraw


def create_dropdown_image(text: str) -> PhotoImage:
    """Creates a new photo image with current images metadata"""
    split_text: list[str] = text.split("\n")
    text_bbox: tuple[int, int, int, int] = ImageDraw.font.getbbox(
        max(split_text, key=len)
    )

    x_offset: int = max(int(text_bbox[2] * 0.07), 10)
    height: int = text_bbox[3] + text_bbox[1]
    spacing: int = int(height * 0.8)
    count: int = len(split_text)

    box_to_draw_on: ImageDraw = Draw(
        new(
            "RGBA",
            (text_bbox[2] + (x_offset << 1), height * count + spacing * (count + 1)),
            (40, 40, 40, 170),
        ),
        "RGBA",
    )
    box_to_draw_on.text((10, spacing), text, fill="white", spacing=spacing)

    return PhotoImage(box_to_draw_on._image)  # type: ignore
