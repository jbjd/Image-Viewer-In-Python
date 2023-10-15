from PIL.ImageTk import PhotoImage
from PIL.Image import fromarray, new
from PIL.ImageDraw import ImageDraw, Draw
from PIL.ImageFont import truetype


# struct for holding cached images
# for some reason this stores less data than a regular tuple based on my tests
class CachedImage:
    __slots__ = ("width", "height", "size_as_text", "image", "bit_size")

    def __init__(self, width, height, size_as_text, image, bit_size) -> None:
        self.width: int = width
        self.height: int = height
        self.size_as_text: str = size_as_text
        self.image: PhotoImage = image
        self.bit_size: int = bit_size


class ImagePath:
    __slots__ = ("suffix", "name")

    def __init__(self, name: str) -> None:
        self.suffix = name[name.rfind(".") :].lower()
        self.name = name


def array_to_photoimage(array) -> PhotoImage:
    return PhotoImage(fromarray(array))


def init_font(font_size: int) -> None:
    ImageDraw.font = truetype("arial.ttf", font_size)
    ImageDraw.fontmode = "L"  # antialiasing


def create_dropdown_image(dimension_text: str, size_text: str) -> PhotoImage:
    text_bbox: tuple = ImageDraw.font.getbbox(dimension_text)

    box_to_draw_on: ImageDraw = Draw(
        new("RGBA", (text_bbox[2] + 20, text_bbox[3] * 5 + 10), (40, 40, 40, 170)),
        "RGBA",
    )
    box_to_draw_on.text((10, text_bbox[3] + 5), dimension_text, fill="white")
    box_to_draw_on.text((10, int(text_bbox[3] * 3)), size_text, fill="white")
    return PhotoImage(box_to_draw_on._image)
