from PIL import Image, ImageTk, ImageDraw


class IconFactory:
	LINE_RGB: tuple = (170, 170, 170)
	ICON_RGB: tuple = (100, 104, 102)
	ICON_HOVERED_RGB: tuple = (95, 92, 88)
	TOPBAR_RGBA: tuple = (60, 60, 60, 170)

	EXIT_RGB = (190, 40, 40)
	EXIT_HOVER_RGB = (180, 25, 20)

	FONT: str = 'arial 11'

	__slots__ = ("icon_size", "screen_width", "icon_default", "icon_hovered_default")

	def __init__(self, icon_size: int, screen_width: int) -> None:
		self.icon_size: int = icon_size
		self.screen_width: int = screen_width

		self.icon_default = Image.new("RGB", (icon_size, icon_size), self.ICON_RGB)
		self.icon_hovered_default = Image.new("RGB", (icon_size, icon_size), self.ICON_HOVERED_RGB)

	def make_topbar(self) -> ImageTk.PhotoImage:
		return ImageTk.PhotoImage(Image.new("RGBA", (self.screen_width, self.icon_size), self.TOPBAR_RGBA))

	def make_exit_icon(self) -> ImageTk.PhotoImage:
		return ImageTk.PhotoImage(Image.new("RGB", (self.icon_size, self.icon_size), self.EXIT_RGB))

	def make_exit_icon_hovered(self) -> ImageTk.PhotoImage:
		draw = ImageDraw.Draw(Image.new("RGB", (self.icon_size, self.icon_size), self.EXIT_HOVER_RGB))
		draw.line((6, 6, 26, 26), width=2, fill=self.LINE_RGB)
		draw.line((6, 26, 26, 6), width=2, fill=self.LINE_RGB)
		return ImageTk.PhotoImage(draw._image)

	def _draw_minify_symbol(self, draw: ImageDraw.ImageDraw) -> ImageTk.PhotoImage:
		draw.line((6, 24, 24, 24), width=2, fill=self.LINE_RGB)
		return ImageTk.PhotoImage(draw._image)

	def make_minify_icon(self) -> ImageTk.PhotoImage:
		draw = ImageDraw.Draw(self.icon_default.copy())
		return self._draw_minify_symbol(draw)

	def make_minify_icon_hovered(self) -> ImageTk.PhotoImage:
		draw = ImageDraw.Draw(self.icon_hovered_default.copy())
		return self._draw_minify_symbol(draw)

	def _draw_trash_symbol(self, draw: ImageDraw.ImageDraw) -> ImageTk.PhotoImage:
		draw.line((9, 9, 9, 22), width=2, fill=self.LINE_RGB)
		draw.line((21, 9, 21, 22), width=2, fill=self.LINE_RGB)
		draw.line((9, 22, 21, 22), width=2, fill=self.LINE_RGB)
		draw.line((7, 9, 24, 9), width=2, fill=self.LINE_RGB)
		draw.line((12, 8, 19, 8), width=3, fill=self.LINE_RGB)
		return ImageTk.PhotoImage(draw._image)

	def make_trash_icon(self) -> ImageTk.PhotoImage:
		draw = ImageDraw.Draw(self.icon_default.copy())
		return self._draw_trash_symbol(draw)

	def make_trash_icon_hovered(self) -> ImageTk.PhotoImage:
		draw = ImageDraw.Draw(self.icon_hovered_default.copy())
		return self._draw_trash_symbol(draw)

	def _draw_down_arrow(self, draw: ImageDraw.ImageDraw) -> ImageTk.PhotoImage:
		draw.line((6, 11, 16, 21), width=2, fill=self.LINE_RGB)
		draw.line((16, 21, 26, 11), width=2, fill=self.LINE_RGB)
		return ImageTk.PhotoImage(draw._image)

	def make_dropdown_hidden_icon(self) -> ImageTk.PhotoImage:
		draw = ImageDraw.Draw(self.icon_default.copy())
		draw.line((6, 11, 16, 21), width=2, fill=self.LINE_RGB)
		draw.line((16, 21, 26, 11), width=2, fill=self.LINE_RGB)
		return self._draw_down_arrow(draw)

	def make_dropdown_hidden_icon_hovered(self) -> ImageTk.PhotoImage:
		draw = ImageDraw.Draw(self.icon_hovered_default.copy())
		draw.line((6, 11, 16, 21), width=2, fill=self.LINE_RGB)
		draw.line((16, 21, 26, 11), width=2, fill=self.LINE_RGB)
		return self._draw_down_arrow(draw)

	def _draw_up_arrow(self, draw: ImageDraw.ImageDraw) -> ImageTk.PhotoImage:
		draw.line((6, 21, 16, 11), width=2, fill=self.LINE_RGB)
		draw.line((16, 11, 26, 21), width=2, fill=self.LINE_RGB)
		draw.line((16, 11, 16, 11), width=1, fill=self.LINE_RGB)
		return ImageTk.PhotoImage(draw._image)

	def make_dropdown_showing_icon(self) -> ImageTk.PhotoImage:
		draw = ImageDraw.Draw(self.icon_default.copy())
		return self._draw_up_arrow(draw)

	def make_dropdown_showing_icon_hovered(self) -> ImageTk.PhotoImage:
		draw = ImageDraw.Draw(self.icon_hovered_default.copy())
		return self._draw_up_arrow(draw)

	def _draw_rename_symbol(self, draw: ImageDraw.ImageDraw) -> ImageTk.PhotoImage:
		draw.rectangle((7, 10, 25, 22), width=1, outline=self.LINE_RGB)
		draw.line((7, 16, 16, 16), width=3, fill=self.LINE_RGB)
		draw.line((16, 8, 16, 24), width=2, fill=self.LINE_RGB)
		return ImageTk.PhotoImage(draw._image)

	def make_rename_icon(self, hovered: bool) -> ImageTk.PhotoImage:
		icon_default_alpha = Image.new("RGBA", (self.icon_size, self.icon_size), (0, 0, 0, 0))
		draw = ImageDraw.Draw(icon_default_alpha.copy())
		if hovered:
			draw.rectangle((4, 5, 28, 27), width=1, fill=self.ICON_HOVERED_RGB)

		return self._draw_rename_symbol(draw)
