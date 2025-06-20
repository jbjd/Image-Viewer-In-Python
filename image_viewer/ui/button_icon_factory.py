from typing import Final

from PIL import ImageOps
from PIL.Image import Image
from PIL.Image import new as new_image
from PIL.ImageDraw import ImageDraw
from PIL.ImageTk import PhotoImage

from ui.button import IconImages
from util.PIL import resize


class ButtonIconFactory:
    """Creates UI icons scaled to screen size"""

    LINE_RGB: tuple[int, int, int] = (170, 170, 170)
    ICON_RGB: tuple[int, int, int] = (100, 104, 102)
    ICON_HOVERED_RGB: tuple[int, int, int] = (95, 92, 88)

    # Make all icons 32x32 and resize to screen after drawing
    DEFAULT_SIZE: tuple[int, int] = (32, 32)

    __slots__ = ("icon_size", "ratio")

    def __init__(self, icon_size: int) -> None:
        self.icon_size: Final[tuple[int, int]] = (icon_size, icon_size)

    def _resize_icon(self, image: Image) -> Image:
        """Returns copy of image that is icon size"""
        return resize(image, self.icon_size)

    def make_icon_from_draw(self, draw: ImageDraw) -> PhotoImage:
        """Resizes an ImageDraw to icon size and converts to a PhotoImage"""
        return PhotoImage(self._resize_icon(draw._image))

    def _new_rgb_image(self, rgb: tuple[int, int, int]) -> Image:
        """Returns new default sized RGB Image"""
        return new_image("RGB", self.DEFAULT_SIZE, rgb)

    def _make_icon_base(
        self,
        default_rgb: tuple[int, int, int] = ICON_RGB,
        default_hovered_rgb: tuple[int, int, int] = ICON_HOVERED_RGB,
    ) -> tuple[ImageDraw, ImageDraw]:
        """Returns tuple of icon and hovered icon base images"""
        return ImageDraw(self._new_rgb_image(default_rgb)), ImageDraw(
            self._new_rgb_image(default_hovered_rgb)
        )

    def make_topbar_image(self, screen_width: int) -> PhotoImage:
        """Makes partially transparent bar used on the screen"""
        TOPBAR_RGBA: tuple[int, int, int, int] = (60, 60, 60, 170)
        size: tuple[int, int] = (screen_width, self.icon_size[0])
        return PhotoImage(new_image("RGBA", size, TOPBAR_RGBA))

    def _draw_x_symbol(self, draw: ImageDraw) -> PhotoImage:
        """Draws X on provided image"""
        draw.line((6, 6, 26, 26), self.LINE_RGB, 2)
        draw.line((6, 26, 26, 6), self.LINE_RGB, 2)
        return self.make_icon_from_draw(draw)

    def make_exit_icons(self) -> IconImages:
        """Makes red button with an X when hovered"""
        EXIT_RGB: tuple[int, int, int] = (190, 40, 40)
        EXIT_HOVER_RGB: tuple[int, int, int] = (180, 25, 20)
        draw, draw_hovered = self._make_icon_base(EXIT_RGB, EXIT_HOVER_RGB)
        return IconImages(
            self.make_icon_from_draw(draw),
            self._draw_x_symbol(draw_hovered),
        )

    def _draw_minify_symbol(self, draw: ImageDraw) -> PhotoImage:
        """Draws common minify symbol on provided image"""
        draw.line((6, 24, 24, 24), self.LINE_RGB, 2)
        return self.make_icon_from_draw(draw)

    def make_minify_icons(self) -> IconImages:
        draw, draw_hovered = self._make_icon_base()
        return IconImages(
            self._draw_minify_symbol(draw), self._draw_minify_symbol(draw_hovered)
        )

    def _draw_trash_symbol(self, draw: ImageDraw) -> PhotoImage:
        """Draws a trash can on provided image"""
        draw.line((9, 9, 9, 22), self.LINE_RGB, 2)
        draw.line((21, 9, 21, 22), self.LINE_RGB, 2)
        draw.line((9, 22, 21, 22), self.LINE_RGB, 2)
        draw.line((7, 9, 24, 9), self.LINE_RGB, 2)
        draw.line((12, 8, 19, 8), self.LINE_RGB, 3)
        return self.make_icon_from_draw(draw)

    def make_trash_icons(self) -> IconImages:
        draw, draw_hovered = self._make_icon_base()
        return IconImages(
            self._draw_trash_symbol(draw), self._draw_trash_symbol(draw_hovered)
        )

    def _draw_down_and_up_arrow(self, draw: ImageDraw) -> tuple[PhotoImage, PhotoImage]:
        """Draws an arrow on provided image
        Returns tuple of down arrow version and up arrow version"""
        draw.line((6, 11, 16, 21), self.LINE_RGB, 2)
        draw.line((16, 21, 26, 11), self.LINE_RGB, 2)
        resized_img: Image = self._resize_icon(draw._image)
        return PhotoImage(resized_img), PhotoImage(ImageOps.flip(resized_img))

    def make_dropdown_icons(self) -> tuple[IconImages, IconImages]:
        """Return down arrow icons and up arrow icons as a tuple"""
        draw, draw_hovered = self._make_icon_base()
        down, up = self._draw_down_and_up_arrow(draw)
        down_hovered, up_hovered = self._draw_down_and_up_arrow(draw_hovered)
        return IconImages(down, down_hovered), IconImages(up, up_hovered)

    def _draw_rename_symbol(self, draw: ImageDraw) -> PhotoImage:
        draw.rectangle((7, 10, 25, 22), None, self.LINE_RGB, 1)
        draw.line((7, 16, 16, 16), self.LINE_RGB, 3)
        draw.line((16, 8, 16, 24), self.LINE_RGB, 2)
        return self.make_icon_from_draw(draw)

    def make_rename_icons(self) -> IconImages:
        transparent_icon: Image = new_image("RGBA", self.DEFAULT_SIZE)
        draw: ImageDraw = ImageDraw(transparent_icon.copy())
        draw_hovered: ImageDraw = ImageDraw(transparent_icon)
        draw_hovered.rectangle((4, 5, 28, 27), self.ICON_HOVERED_RGB, width=1)
        return IconImages(
            self._draw_rename_symbol(draw), self._draw_rename_symbol(draw_hovered)
        )
