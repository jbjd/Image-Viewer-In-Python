"""
Contains classes and functions to help with storing and reading images
"""

from PIL.ImageTk import PhotoImage

from util.os import OS_name_cmp


class CachedImageData:
    """Information stored to skip resizing/system calls on repeated opening"""

    __slots__ = ("height", "image", "kb_size", "mode", "size_display", "width")

    def __init__(
        self,
        image: PhotoImage,
        width: int,
        height: int,
        size_display: str,
        kb_size: int,
        mode: str,
    ) -> None:
        self.image: PhotoImage = image
        self.width: int = width
        self.height: int = height
        self.size_display: str = size_display
        self.kb_size: int = kb_size
        self.mode: str = mode


class ImagePath:
    """Full name and suffix of loaded image files"""

    __slots__ = ("name", "suffix")

    def __init__(self, name: str) -> None:
        self.suffix = name[name.rfind(".") + 1 :].lower()
        self.name = name

    def __lt__(self, other: "ImagePath") -> bool:
        return OS_name_cmp(self.name, other.name)


class DropdownImage:
    """The dropdown image containing metadata on the open image file"""

    __slots__ = ("id", "image", "need_refresh", "showing")

    def __init__(self, id: int) -> None:
        self.id: int = id
        self.need_refresh: bool = True
        self.showing: bool = False
        self.image: PhotoImage

    def toggle_display(self) -> None:
        """Flips if showing is true or false"""
        self.showing = not self.showing


def magic_number_guess(magic: bytes) -> tuple[str]:
    """Given bytes, make best guess at file type of image"""
    match magic:
        case b"\x89PNG":
            return ("PNG",)
        case b"RIFF":
            return ("WEBP",)
        case b"GIF8":
            return ("GIF",)
        case _:
            return ("JPEG",)
