from PIL.Image import new
from PIL.ImageDraw import Draw, ImageDraw
from PIL.ImageFont import truetype
from PIL.ImageTk import PhotoImage

from util.os import OS_name_cmp


class CachedImageData:
    """Information stored to skip resizing/system calls on repeated opening"""

    __slots__ = ("dimensions", "height", "image", "kb_size", "width")

    def __init__(
        self, image: PhotoImage, width: int, height: int, dimensions: str, kb_size: int
    ) -> None:
        self.image: PhotoImage = image
        self.width: int = width
        self.height: int = height
        self.dimensions: str = dimensions
        self.kb_size: int = kb_size


class ImagePath:
    """Full name and suffix of loaded image files"""

    __slots__ = ("name", "suffix")

    def __init__(self, name: str) -> None:
        self.suffix = name[name.rfind(".") :].lower()
        self.name = name

    def __lt__(self, other: "ImagePath") -> bool:
        return OS_name_cmp(self.name, other.name)


class DropdownImage:
    """The dropdown image containing metadata on the open image file"""

    __slots__ = ("id", "image", "need_refresh", "showing")

    def __init__(self, id: int) -> None:
        self.id: int = id
        self.need_refresh: bool = True
        self.showing: bool = False
        self.image: PhotoImage

    def toggle_display(self) -> None:
        """Flips if showing is true or false"""
        self.showing = not self.showing


def magic_number_guess(magic: bytes) -> tuple[str]:
    """Given bytes, make best guess at file type of image"""
    match magic:
        case b"\x89PNG":
            return ("PNG",)
        case b"RIFF":
            return ("WEBP",)
        case b"GIF8":
            return ("GIF",)
        case _:
            return ("JPEG",)


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
