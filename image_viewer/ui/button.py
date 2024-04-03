from typing import Callable
from PIL.ImageTk import PhotoImage
from tkinter import Canvas, Event


class HoverableButton:
    """Decorates a Button on the UI that has a different image when hovered"""

    __slots__ = "canvas", "function_to_bind", "icon", "icon_hovered", "id"

    def __init__(
        self,
        canvas: Canvas,
        icon: PhotoImage,
        icon_hovered: PhotoImage,
        function_to_bind: Callable[[Event], None],
    ) -> None:
        self.canvas: Canvas = canvas
        self.icon: PhotoImage = icon
        self.icon_hovered: PhotoImage = icon_hovered
        self.function_to_bind: Callable[[Event], None] = function_to_bind
        self.id: int = -1

    def add_self_to_canvas(self, anchor: str, x_offset: int) -> int:
        """Uses canvas to create itself on the screen"""
        self.id = self.canvas.create_image(
            x_offset,
            0,
            image=self.icon,
            anchor=anchor,
            tag="topbar",
            state="hidden",
        )

        self.canvas.tag_bind(self.id, "<Enter>", self.on_enter)
        self.canvas.tag_bind(self.id, "<Leave>", self.on_leave)
        self.canvas.tag_bind(self.id, "<ButtonRelease-1>", self.on_click)

        return self.id

    def on_enter(self, _: Event | None = None) -> None:
        self.canvas.itemconfigure(self.id, image=self._get_hovered_icon())

    def on_leave(self, _: Event | None = None) -> None:
        self.canvas.itemconfigure(self.id, image=self._get_default_icon())

    def on_click(self, event: Event) -> None:
        self.function_to_bind(event)

    def _get_hovered_icon(self) -> PhotoImage:
        return self.icon_hovered

    def _get_default_icon(self) -> PhotoImage:
        return self.icon


class ToggleButton(HoverableButton):
    """Extends HoverableButton by allowing an active/inactive state"""

    __slots__ = "active", "active_icon", "active_icon_hovered", "hovered_button"

    def __init__(
        self,
        canvas: Canvas,
        icon: PhotoImage,
        active_icon: PhotoImage,
        icon_hovered: PhotoImage,
        active_icon_hovered: PhotoImage,
        function_to_bind: Callable[[Event], None],
    ) -> None:
        super().__init__(canvas, icon, icon_hovered, function_to_bind)
        self.active_icon: PhotoImage = active_icon
        self.active_icon_hovered: PhotoImage = active_icon_hovered
        self.active: bool = False

    def _get_hovered_icon(self) -> PhotoImage:
        return self.active_icon_hovered if self.active else self.icon_hovered

    def _get_default_icon(self) -> PhotoImage:
        return self.active_icon if self.active else self.icon

    def on_click(self, event: Event) -> None:
        self.active = not self.active
        self.on_enter()  # fake mouse hover
        self.function_to_bind(event)
