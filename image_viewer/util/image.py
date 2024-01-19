from PIL.Image import new
from PIL.ImageDraw import Draw, ImageDraw
from PIL.ImageFont import truetype
from PIL.ImageTk import PhotoImage

from util.os import OS_name_cmp


class CachedImageData:
    __slots__ = ("dimensions", "height", "image", "kb_size", "width")

    def __init__(self, width, height, dimensions, image, kb_size) -> None:
        self.width: int = width
        self.height: int = height
        self.dimensions: str = dimensions
        self.image: PhotoImage = image
        self.kb_size: int = kb_size


class ImagePath:
    __slots__ = ("name", "suffix")

    def __init__(self, name: str) -> None:
        self.suffix = name[name.rfind(".") :].lower()
        self.name = name

    def __lt__(self, other) -> bool:
        return OS_name_cmp(self.name, other.name)


class DropdownImage:
    """The dropdown image containing metadata on the open image file"""

    __slots__ = "id", "image", "refresh"

    def __init__(self, id: int) -> None:
        self.id: int = id
        self.refresh: bool = True
        self.image: PhotoImage


def init_PIL(font_size: int) -> None:
    ImageDraw.font = truetype("arial.ttf", font_size)
    ImageDraw.fontmode = "L"  # antialiasing
    from PIL import Image

    # edit this so PIL will not waste time importing +20 useless modules
    Image._plugins = [
        "WebPImagePlugin",
    ]


def create_dropdown_image(dimension_text: str, size_text: str) -> PhotoImage:
    """Creates a new photo image with current images metadata"""

    text_bbox: tuple = ImageDraw.font.getbbox(dimension_text)
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
