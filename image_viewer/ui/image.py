"""
Classes that represent images in the UI
"""

from PIL.ImageTk import PhotoImage


class ImageUIElement:

    def __init__(self, image: PhotoImage | None, id: int) -> None:
        self.image: PhotoImage | None = image
        self.id: int = id


class DropdownImageUIElement:
    """The dropdown image containing metadata on the open image file"""

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
