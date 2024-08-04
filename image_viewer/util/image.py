"""
Contains classes and functions to help with storing and reading images
"""

from collections import OrderedDict
from os import stat
from typing import Iterable

from PIL.Image import Image

from constants import MAX_ITEMS_IN_CACHE
from util.os import OS_name_cmp


class CachedImage:
    """Information stored to skip resizing/system calls on repeated opening"""

    __slots__ = "height", "image", "mode", "size_display", "byte_size", "width"

    def __init__(
        self,
        image: Image,
        dimensions: tuple[int, int],
        size_display: str,
        byte_size: int,
        mode: str,
    ) -> None:
        self.width: int
        self.height: int
        self.width, self.height = dimensions
        self.image: Image = image
        self.size_display: str = size_display
        self.byte_size: int = byte_size
        self.mode: str = mode


class ImageCache(OrderedDict[str, CachedImage]):
    """Dictionary for caching image data using paths as keys"""

    def pop_safe(self, image_path: str) -> CachedImage | None:
        return self.pop(image_path, None)

    def image_cache_still_fresh(self, image_path: str) -> bool:
        """Returns True when cached image is the same size of the image on disk.
        Not guaranteed to be correct, but that's not important for this case"""
        try:
            return stat(image_path).st_size == self[image_path].byte_size
        except (OSError, ValueError, KeyError):
            return False

    def update_key(self, old_key: str, new_key: str) -> None:
        """Moves value from old_key to new_key deleting old_key
        If new_key does not exist, nothing happens"""
        target: CachedImage | None = self.pop_safe(old_key)

        if target is not None:
            self[new_key] = target

    def __setitem__(self, key: str, value: CachedImage) -> None:
        """Adds check for items in the cache and purges LRU if over limit"""
        if self.__len__() >= MAX_ITEMS_IN_CACHE:
            self.popitem(last=False)
        super().__setitem__(key, value)


class ImageName:
    """Full name and suffix of loaded image files"""

    __slots__ = "name", "suffix"

    def __init__(self, name: str) -> None:
        index: int = name.rfind(".") + 1
        self.suffix: str = name[index:].lower() if index else ""
        self.name: str = name

    def __lt__(self, other: "ImageName") -> bool:
        return OS_name_cmp(self.name, other.name)


class ImageNameList(list[ImageName]):

    __slots__ = "display_index"

    def __init__(self, iterable: Iterable[ImageName]) -> None:
        super().__init__(iterable)
        self.display_index: int = 0

    def get_current_image(self) -> ImageName:
        return self[self.display_index]

    def get_current_image_name(self) -> str:
        return self[self.display_index].name

    def move_index(self, amount: int) -> None:
        image_count: int = len(self)
        if image_count > 0:
            self.display_index = (self.display_index + amount) % len(self)

    def sort_and_preserve_index(self, image_to_start_at: str) -> None:
        """Sorts and keeps index at the same image"""
        super().sort()
        self.display_index, _ = self.binary_search(image_to_start_at)

    def remove_current_image(self) -> None:
        """Safely removes current index"""
        try:
            super().pop(self.display_index)
        except IndexError:
            pass

        image_count: int = len(self)

        if self.display_index >= image_count:
            self.display_index = image_count - 1

    def binary_search(self, target_image: str) -> tuple[int, bool]:
        """Finds index of target_image.
        Returns tuple of index and if match was found"""
        low: int = 0
        high: int = len(self) - 1
        while low <= high:
            mid: int = (low + high) >> 1
            current_image = self[mid].name
            if target_image == current_image:
                return mid, True
            if OS_name_cmp(target_image, current_image):
                high = mid - 1
            else:
                low = mid + 1
        return low, False


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
