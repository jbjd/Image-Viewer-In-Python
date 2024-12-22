"""
Classes that represent images on a tkinter canvas
"""

from PIL.ImageTk import PhotoImage


class ImageUIElement:
    """Represents an image displayed on a tkinter canvas"""

    def __init__(self, image: PhotoImage | None, id: int) -> None:
        self.image: PhotoImage | None = image
        self.id: int = id

    def update(self, image: PhotoImage | None = None, id: int | None = None):
        """Updates image, id, or both when passed"""
        if image is not None:
            self.image = image
        if id is not None:
            self.id = id


class DropdownImageUIElement:
    """Represents an image that can toggle being shown on a tkinter canvas"""

    __slots__ = ("need_refresh", "show", "ui_image")

    def __init__(self, id: int) -> None:
        self.ui_image: ImageUIElement = ImageUIElement(None, id)
        self.need_refresh: bool = True
        self.show: bool = False

    @property
    def id(self) -> int:
        return self.ui_image.id

    @property
    def image(self) -> PhotoImage | None:
        return self.ui_image.image

    @image.setter
    def image(self, image: PhotoImage) -> None:
        self.ui_image.image = image

    def toggle_display(self) -> None:
        """Flips if showing is true or false"""
        self.show = not self.show
