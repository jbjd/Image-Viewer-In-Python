"""
Classes that represent images on a tkinter canvas
"""

from PIL.ImageTk import PhotoImage

from ui.bases import UIElementBase


class ImageUIElement(UIElementBase):
    """Represents an image displayed on a tkinter canvas"""

    __slots__ = ("image",)

    def __init__(self, image: PhotoImage | None, id: int) -> None:
        super().__init__(id)
        self.image: PhotoImage | None = image

    def update(self, image: PhotoImage | None = None, id: int | None = None):
        """Updates image, id, or both when passed"""
        if image is not None:
            self.image = image
        if id is not None:
            self.id = id


class DropdownImageUIElement(ImageUIElement):
    """Represents a lazy loaded drop down image displayed on a tkinter canvas"""

    __slots__ = ("need_refresh", "show")

    def __init__(self, id: int) -> None:
        super().__init__(None, id)
        self.need_refresh: bool = True
        self.show: bool = False

    def toggle_display(self) -> None:
        """Flips if showing is true or false"""
        self.show = not self.show
