from PIL.Image import Image, new
from PIL.ImageDraw import Draw, ImageDraw
from PIL.ImageTk import PhotoImage


# Currently draws symbols at set points, not relative to size of icons
# Monitors other than mine might get wrong size symbols
class IconFactory:
    LINE_RGB: tuple = (170, 170, 170)
    ICON_RGB: tuple = (100, 104, 102)
    ICON_HOVERED_RGB: tuple = (95, 92, 88)
    TOPBAR_RGBA: tuple = (60, 60, 60, 170)

    __slots__ = ("icon_size", "screen_width", "icon_default", "icon_hovered_default")

    def __init__(self, icon_size: int, screen_width: int) -> None:
        self.icon_size: int = icon_size
        self.screen_width: int = screen_width

        self.icon_default: Image = new("RGB", (icon_size, icon_size), self.ICON_RGB)
        self.icon_hovered_default: Image = new(
            "RGB", (icon_size, icon_size), self.ICON_HOVERED_RGB
        )

    def make_topbar(self) -> PhotoImage:
        return PhotoImage(
            new("RGBA", (self.screen_width, self.icon_size), self.TOPBAR_RGBA)
        )

    def make_exit_icon(self) -> PhotoImage:
        EXIT_RGB: tuple = (190, 40, 40)
        return PhotoImage(new("RGB", (self.icon_size, self.icon_size), EXIT_RGB))

    def make_exit_icon_hovered(self) -> PhotoImage:
        EXIT_HOVER_RGB: tuple = (180, 25, 20)
        draw = Draw(new("RGB", (self.icon_size, self.icon_size), EXIT_HOVER_RGB))
        draw.line((6, 6, 26, 26), width=2, fill=self.LINE_RGB)
        draw.line((6, 26, 26, 6), width=2, fill=self.LINE_RGB)
        return PhotoImage(draw._image)

    def _make_icon_base(self) -> tuple[ImageDraw, ImageDraw]:
        return Draw(self.icon_default.copy()), Draw(self.icon_hovered_default.copy())

    def _draw_minify_symbol(self, draw: ImageDraw) -> PhotoImage:
        draw.line((6, 24, 24, 24), width=2, fill=self.LINE_RGB)
        return PhotoImage(draw._image)

    def make_minify_icons(self) -> tuple[PhotoImage, PhotoImage]:
        draw, draw_hovered = self._make_icon_base()
        return self._draw_minify_symbol(draw), self._draw_minify_symbol(draw_hovered)

    def _draw_trash_symbol(self, draw: ImageDraw) -> PhotoImage:
        draw.line((9, 9, 9, 22), width=2, fill=self.LINE_RGB)
        draw.line((21, 9, 21, 22), width=2, fill=self.LINE_RGB)
        draw.line((9, 22, 21, 22), width=2, fill=self.LINE_RGB)
        draw.line((7, 9, 24, 9), width=2, fill=self.LINE_RGB)
        draw.line((12, 8, 19, 8), width=3, fill=self.LINE_RGB)
        return PhotoImage(draw._image)

    def make_trash_icons(self) -> tuple[PhotoImage, PhotoImage]:
        draw, draw_hovered = self._make_icon_base()
        return self._draw_trash_symbol(draw), self._draw_trash_symbol(draw_hovered)

    def _draw_down_arrow(self, draw: ImageDraw) -> PhotoImage:
        draw.line((6, 11, 16, 21), width=2, fill=self.LINE_RGB)
        draw.line((16, 21, 26, 11), width=2, fill=self.LINE_RGB)
        return PhotoImage(draw._image)

    def make_dropdown_hidden_icons(
        self,
    ) -> tuple[PhotoImage, PhotoImage]:
        draw, draw_hovered = self._make_icon_base()
        return self._draw_down_arrow(draw), self._draw_down_arrow(draw_hovered)

    def _draw_up_arrow(self, draw: ImageDraw) -> PhotoImage:
        draw.line((6, 21, 16, 11), width=2, fill=self.LINE_RGB)
        draw.line((16, 11, 26, 21), width=2, fill=self.LINE_RGB)
        draw.line((16, 11, 16, 11), width=1, fill=self.LINE_RGB)
        return PhotoImage(draw._image)

    def make_dropdown_showing_icons(
        self,
    ) -> tuple[PhotoImage, PhotoImage]:
        draw, draw_hovered = self._make_icon_base()
        return self._draw_up_arrow(draw), self._draw_up_arrow(draw_hovered)

    def _draw_rename_symbol(self, draw: ImageDraw) -> PhotoImage:
        draw.rectangle((7, 10, 25, 22), width=1, outline=self.LINE_RGB)
        draw.line((7, 16, 16, 16), width=3, fill=self.LINE_RGB)
        draw.line((16, 8, 16, 24), width=2, fill=self.LINE_RGB)
        return PhotoImage(draw._image)

    def make_rename_icons(self) -> tuple[PhotoImage, PhotoImage]:
        icon_default_alpha = new("RGBA", (self.icon_size, self.icon_size), (0, 0, 0, 0))
        draw, draw_hovered = Draw(icon_default_alpha.copy()), Draw(
            icon_default_alpha.copy()
        )
        draw_hovered.rectangle((4, 5, 28, 27), width=1, fill=self.ICON_HOVERED_RGB)
        return self._draw_rename_symbol(draw), self._draw_rename_symbol(draw_hovered)
