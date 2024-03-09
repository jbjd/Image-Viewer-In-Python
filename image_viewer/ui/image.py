"""
Classes that represent images in the UI
"""

from PIL.ImageTk import PhotoImage


class DropdownImage:
    """The dropdown image containing metadata on the open image file"""

    __slots__ = "id", "image", "need_refresh", "showing"

    def __init__(self, canvas_id: int) -> None:
        self.id: int = canvas_id
        self.need_refresh: bool = True
        self.showing: bool = False
        self.image: PhotoImage

    def toggle_display(self) -> None:
        """Flips if showing is true or false"""
        self.showing = not self.showing
