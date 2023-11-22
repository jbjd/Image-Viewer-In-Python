from PIL.Image import new
from PIL.ImageDraw import Draw, ImageDraw
from PIL.ImageFont import truetype
from PIL.ImageTk import PhotoImage


# struct for holding cached images
# for some reason this stores less data than a regular tuple based on my tests
class CachedInfo:
    __slots__ = ("width", "height", "dimensions")

    def __init__(self, width, height, dimensions) -> None:
        self.width: int = width
        self.height: int = height
        self.dimensions: str = dimensions


class CachedInfoAndImage(CachedInfo):
    __slots__ = ("image", "bit_size")

    def __init__(self, width, height, dimensions, image, bit_size) -> None:
        super().__init__(width, height, dimensions)
        self.image: PhotoImage = image
        self.bit_size: int = bit_size


class ImagePath:
    __slots__ = ("suffix", "name")

    def __init__(self, name: str) -> None:
        self.suffix = name[name.rfind(".") :].lower()
        self.name = name


def init_font(font_size: int) -> None:
    ImageDraw.font = truetype("arial.ttf", font_size)
    ImageDraw.fontmode = "L"  # antialiasing


def create_dropdown_image(dimension_text: str, size_text: str) -> PhotoImage:
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
