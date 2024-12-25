from collections import namedtuple
from tkinter import Event
from typing import Callable

from PIL.ImageTk import PhotoImage

from constants import ButtonName
from ui.bases import ButtonUIElementBase
from ui.canvas import CustomCanvas


class IconImages(namedtuple("IconImages", ["default", "hovered"])):
    """Tuple with default and hovered icons for on-screen buttons"""

    default: PhotoImage
    hovered: PhotoImage


class HoverableButtonUIElement(ButtonUIElementBase):
    """Button with different icons when its hovered"""

    __slots__ = ("canvas", "function_to_bind", "icon", "icon_hovered")

    def __init__(
        self,
        canvas: CustomCanvas,
        icon: IconImages,
        function_to_bind: Callable[[Event | None], None],
    ) -> None:
        super().__init__()
        self.canvas: CustomCanvas = canvas
        self.icon: PhotoImage = icon.default
        self.icon_hovered: PhotoImage = icon.hovered
        self.function_to_bind: Callable[[Event | None], None] = function_to_bind

    def add_to_canvas(
        self, name: ButtonName, x_offset: int = 0, y_offset: int = 0
    ) -> None:
        """Adds self to canvas"""
        id = self.canvas.create_button(
            self,
            name,
            x_offset,
            y_offset,
            image=self.icon,
        )
        self.update(id=id)

        self.canvas.tag_bind(id, "<Enter>", self.on_enter)
        self.canvas.tag_bind(id, "<Leave>", self.on_leave)
        self.canvas.tag_bind(id, "<ButtonRelease-1>", self.on_click)

    def on_click(self, event: Event | None = None) -> None:
        self.function_to_bind(event)

    def on_enter(self, _: Event | None = None) -> None:
        self.canvas.itemconfigure(self.id, image=self._get_hovered_icon())

    def on_leave(self, _: Event | None = None) -> None:
        self.canvas.itemconfigure(self.id, image=self._get_default_icon())

    def _get_hovered_icon(self) -> PhotoImage:
        return self.icon_hovered

    def _get_default_icon(self) -> PhotoImage:
        return self.icon


class ToggleableButtonUIElement(HoverableButtonUIElement):
    """Extends HoverableButtonUIElement by allowing an active/inactive state"""

    __slots__ = ("active_icon", "active_icon_hovered", "is_active")

    def __init__(
        self,
        canvas: CustomCanvas,
        icon: IconImages,
        active_icon: IconImages,
        function_to_bind: Callable[[Event | None], None],
    ) -> None:
        super().__init__(canvas, icon, function_to_bind)
        self.active_icon: PhotoImage = active_icon.default
        self.active_icon_hovered: PhotoImage = active_icon.hovered
        self.is_active: bool = False

    def on_click(self, event: Event | None = None) -> None:
        self.is_active = not self.is_active
        self.on_enter()  # fake mouse hover
        self.function_to_bind(event)

    def _get_hovered_icon(self) -> PhotoImage:
        return self.active_icon_hovered if self.is_active else self.icon_hovered

    def _get_default_icon(self) -> PhotoImage:
        return self.active_icon if self.is_active else self.icon
