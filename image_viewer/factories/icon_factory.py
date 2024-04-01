from typing import Final

from PIL import ImageOps
from PIL.Image import Image
from PIL.Image import new as new_image
from PIL.ImageDraw import ImageDraw
from PIL.ImageTk import PhotoImage

from util.PIL import resize, get_image_draw


class IconFactory:
    """Creates UI icons scaled to screen size"""

    LINE_RGB: tuple[int, int, int] = (170, 170, 170)
    ICON_RGB: tuple[int, int, int] = (100, 104, 102)
    ICON_HOVERED_RGB: tuple[int, int, int] = (95, 92, 88)

    # Make all icons 32x32 and resize to screen after drawing
    DEFAULT_SIZE: tuple[int, int] = (32, 32)

    __slots__ = "icon_size", "ratio"

    def __init__(self, icon_size: int) -> None:
        self.icon_size: Final[tuple[int, int]] = (icon_size, icon_size)

    def _resize_icon(self, image: Image) -> Image:
        return resize(image, self.icon_size)

    def make_icon_from_draw(self, draw: ImageDraw) -> PhotoImage:
        """Resizes an ImageDraw to icon size and converts to a PhotoImage"""
        return PhotoImage(self._resize_icon(draw._image))  # type: ignore

    def _new_rgb_image(self, rgb: tuple[int, int, int]):
        return new_image("RGB", self.DEFAULT_SIZE, rgb)

    def _make_icon_base(self) -> tuple[ImageDraw, ImageDraw]:
        """Returns tuple of icon and hovered icon base images"""
        return get_image_draw(self._new_rgb_image(self.ICON_RGB)), get_image_draw(
            self._new_rgb_image(self.ICON_HOVERED_RGB)
        )

    def make_topbar(self, screen_width: int) -> PhotoImage:
        TOPBAR_RGBA: tuple[int, int, int, int] = (60, 60, 60, 170)
        size: tuple[int, int] = (screen_width, self.icon_size[0])
        return PhotoImage(new_image("RGBA", size, TOPBAR_RGBA))

    def make_exit_icons(self) -> tuple[PhotoImage, PhotoImage]:
        EXIT_RGB: tuple[int, int, int] = (190, 40, 40)
        EXIT_HOVER_RGB: tuple[int, int, int] = (180, 25, 20)
        draw = get_image_draw(self._new_rgb_image(EXIT_HOVER_RGB))
        draw.line((6, 6, 26, 26), self.LINE_RGB, 2)
        draw.line((6, 26, 26, 6), self.LINE_RGB, 2)
        return (
            PhotoImage(self._resize_icon(self._new_rgb_image(EXIT_RGB))),
            self.make_icon_from_draw(draw),
        )

    def _draw_minify_symbol(self, draw: ImageDraw) -> PhotoImage:
        draw.line((6, 24, 24, 24), self.LINE_RGB, 2)
        return self.make_icon_from_draw(draw)

    def make_minify_icons(self) -> tuple[PhotoImage, PhotoImage]:
        draw, draw_hovered = self._make_icon_base()
        return self._draw_minify_symbol(draw), self._draw_minify_symbol(draw_hovered)

    def _draw_trash_symbol(self, draw: ImageDraw) -> PhotoImage:
        draw.line((9, 9, 9, 22), self.LINE_RGB, 2)
        draw.line((21, 9, 21, 22), self.LINE_RGB, 2)
        draw.line((9, 22, 21, 22), self.LINE_RGB, 2)
        draw.line((7, 9, 24, 9), self.LINE_RGB, 2)
        draw.line((12, 8, 19, 8), self.LINE_RGB, 3)
        return self.make_icon_from_draw(draw)

    def make_trash_icons(self) -> tuple[PhotoImage, PhotoImage]:
        draw, draw_hovered = self._make_icon_base()
        return self._draw_trash_symbol(draw), self._draw_trash_symbol(draw_hovered)

    def _draw_down_arrow(self, draw: ImageDraw) -> tuple[PhotoImage, PhotoImage]:
        draw.line((6, 11, 16, 21), self.LINE_RGB, 2)
        draw.line((16, 21, 26, 11), self.LINE_RGB, 2)
        resised_img: Image = self._resize_icon(draw._image)  # type: ignore
        return PhotoImage(resised_img), PhotoImage(ImageOps.flip(resised_img))

    def make_dropdown_icons(
        self,
    ) -> tuple[PhotoImage, PhotoImage, PhotoImage, PhotoImage]:
        """Return tuple of down arrow default, hovered and up arrow
        default hovered icons in that order"""
        draw, draw_hovered = self._make_icon_base()
        return self._draw_down_arrow(draw) + self._draw_down_arrow(draw_hovered)

    def _draw_rename_symbol(self, draw: ImageDraw) -> PhotoImage:
        draw.rectangle((7, 10, 25, 22), None, self.LINE_RGB, 1)
        draw.line((7, 16, 16, 16), self.LINE_RGB, 3)
        draw.line((16, 8, 16, 24), self.LINE_RGB, 2)
        return self.make_icon_from_draw(draw)

    def make_rename_icons(self) -> tuple[PhotoImage, PhotoImage]:
        transparent_icon: Image = new_image("RGBA", self.DEFAULT_SIZE)
        draw: ImageDraw = get_image_draw(transparent_icon.copy())
        draw_hovered: ImageDraw = get_image_draw(transparent_icon)
        draw_hovered.rectangle((4, 5, 28, 27), self.ICON_HOVERED_RGB, width=1)
        return self._draw_rename_symbol(draw), self._draw_rename_symbol(draw_hovered)
