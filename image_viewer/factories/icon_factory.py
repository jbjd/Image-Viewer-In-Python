from PIL import ImageOps
from PIL.Image import Image
from PIL.Image import new as new_image
from PIL.ImageDraw import Draw, ImageDraw
from PIL.ImageTk import PhotoImage


# Currently draws symbols at set points, not relative to size of icons
# Monitors other than mine might get wrong size symbols
class IconFactory:
    LINE_RGB: tuple[int, int, int] = (170, 170, 170)
    ICON_RGB: tuple[int, int, int] = (100, 104, 102)
    ICON_HOVERED_RGB: tuple[int, int, int] = (95, 92, 88)

    __slots__ = "icon_size"

    def __init__(self, icon_size: int) -> None:
        self.icon_size: int = icon_size

    def make_topbar(self, screen_width: int) -> PhotoImage:
        TOPBAR_RGBA: tuple = (60, 60, 60, 170)
        return PhotoImage(
            new_image("RGBA", (screen_width, self.icon_size), TOPBAR_RGBA)
        )

    def make_exit_icons(self) -> tuple[PhotoImage, PhotoImage]:
        EXIT_RGB: tuple = (190, 40, 40)
        EXIT_HOVER_RGB: tuple = (180, 25, 20)
        draw = Draw(new_image("RGB", (self.icon_size, self.icon_size), EXIT_HOVER_RGB))
        draw.line((6, 6, 26, 26), width=2, fill=self.LINE_RGB)
        draw.line((6, 26, 26, 6), width=2, fill=self.LINE_RGB)
        return (
            PhotoImage(new_image("RGB", (self.icon_size, self.icon_size), EXIT_RGB)),
            PhotoImage(draw._image),  # type: ignore
        )

    def _make_icon_base(self) -> tuple[ImageDraw, ImageDraw]:
        """Returns tuple of icon and hovered icon base images"""
        return Draw(
            new_image("RGB", (self.icon_size, self.icon_size), self.ICON_RGB)
        ), Draw(
            new_image("RGB", (self.icon_size, self.icon_size), self.ICON_HOVERED_RGB)
        )

    def _draw_minify_symbol(self, draw: ImageDraw) -> PhotoImage:
        draw.line((6, 24, 24, 24), width=2, fill=self.LINE_RGB)
        return PhotoImage(draw._image)  # type: ignore

    def make_minify_icons(self) -> tuple[PhotoImage, PhotoImage]:
        draw, draw_hovered = self._make_icon_base()
        return self._draw_minify_symbol(draw), self._draw_minify_symbol(draw_hovered)

    def _draw_trash_symbol(self, draw: ImageDraw) -> PhotoImage:
        draw.line((9, 9, 9, 22), width=2, fill=self.LINE_RGB)
        draw.line((21, 9, 21, 22), width=2, fill=self.LINE_RGB)
        draw.line((9, 22, 21, 22), width=2, fill=self.LINE_RGB)
        draw.line((7, 9, 24, 9), width=2, fill=self.LINE_RGB)
        draw.line((12, 8, 19, 8), width=3, fill=self.LINE_RGB)
        return PhotoImage(draw._image)  # type: ignore

    def make_trash_icons(self) -> tuple[PhotoImage, PhotoImage]:
        draw, draw_hovered = self._make_icon_base()
        return self._draw_trash_symbol(draw), self._draw_trash_symbol(draw_hovered)

    def _draw_down_arrow(self, draw: ImageDraw) -> Image:
        draw.line((6, 11, 16, 21), width=2, fill=self.LINE_RGB)
        draw.line((16, 21, 26, 11), width=2, fill=self.LINE_RGB)
        return draw._image  # type: ignore

    def make_dropdown_icons(
        self,
    ) -> tuple[PhotoImage, PhotoImage, PhotoImage, PhotoImage]:
        """Return tuple of down arrow default, hovered and up arrow
        default hovered icons in that order"""
        draw, draw_hovered = self._make_icon_base()
        default: Image = self._draw_down_arrow(draw)
        hovered: Image = self._draw_down_arrow(draw_hovered)
        return (
            PhotoImage(default),
            PhotoImage(hovered),
            PhotoImage(ImageOps.flip(default)),
            PhotoImage(ImageOps.flip(hovered)),
        )

    def _draw_rename_symbol(self, draw: ImageDraw) -> PhotoImage:
        draw.rectangle((7, 10, 25, 22), width=1, outline=self.LINE_RGB)
        draw.line((7, 16, 16, 16), width=3, fill=self.LINE_RGB)
        draw.line((16, 8, 16, 24), width=2, fill=self.LINE_RGB)
        return PhotoImage(draw._image)  # type: ignore

    def make_rename_icons(self) -> tuple[PhotoImage, PhotoImage]:
        icon_default_alpha = new_image(
            "RGBA", (self.icon_size, self.icon_size), (0, 0, 0, 0)
        )
        draw, draw_hovered = Draw(icon_default_alpha.copy()), Draw(
            icon_default_alpha.copy()
        )
        draw_hovered.rectangle((4, 5, 28, 27), width=1, fill=self.ICON_HOVERED_RGB)
        return self._draw_rename_symbol(draw), self._draw_rename_symbol(draw_hovered)
