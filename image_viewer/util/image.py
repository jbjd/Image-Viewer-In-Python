"""
Contains classes and functions to help with storing and reading images
"""

from os import stat

from PIL.ImageTk import PhotoImage

from util.os import OS_name_cmp


class CachedImage:
    """Information stored to skip resizing/system calls on repeated opening"""

    __slots__ = "height", "image", "mode", "size_display", "byte_size", "width"

    def __init__(
        self,
        image: PhotoImage,
        dimensions: tuple[int, int],
        size_display: str,
        byte_size: int,
        mode: str,
    ) -> None:
        self.width: int
        self.height: int
        self.width, self.height = dimensions
        self.image: PhotoImage = image
        self.size_display: str = size_display
        self.byte_size: int = byte_size
        self.mode: str = mode


class ImageCache(dict[str, CachedImage]):
    """Dictionary for caching image data using paths as keys"""

    def safe_pop(self, image_path: str) -> None:
        self.pop(image_path, None)

    def image_cache_still_fresh(self, image_path: str) -> bool:
        """Returns True when cached image is the same size of the image on disk.
        Not guaranteed to be correct, but that's not important for this case"""
        try:
            return stat(image_path).st_size == self[image_path].byte_size
        except (OSError, ValueError, KeyError):
            return False


class ImageName:
    """Full name and suffix of loaded image files"""

    __slots__ = "name", "suffix"

    def __init__(self, name: str) -> None:
        index: int = name.rfind(".") + 1
        self.suffix: str = name[index:].lower() if index else ""
        self.name: str = name

    def __lt__(self, other: "ImageName") -> bool:
        return OS_name_cmp(self.name, other.name)


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
