"""
Contains classes and functions to help with storing and reading images
"""

from collections import OrderedDict, namedtuple
from os import stat
from typing import Iterable

from PIL.Image import Image

from constants import DEFAULT_MAX_ITEMS_IN_CACHE, ImageFormats
from util.os import OS_name_cmp


class ImageCacheEntry:
    """Information stored to skip resizing/system calls on repeated opening"""

    __slots__ = (
        "format",
        "height",
        "image",
        "mode",
        "size_display",
        "byte_size",
        "width",
    )

    def __init__(
        self,
        image: Image,
        dimensions: tuple[int, int],
        size_display: str,
        byte_size: int,
        mode: str,
        format: str,
    ) -> None:
        self.width: int
        self.height: int
        self.width, self.height = dimensions
        self.image: Image = image
        self.size_display: str = size_display
        self.byte_size: int = byte_size
        # Store original mode since resizing some images converts to RGB
        self.mode: str = mode
        self.format: str = format


class ImageCache(OrderedDict[str, ImageCacheEntry]):
    """Dictionary for caching image data using paths as keys"""

    __slots__ = ("max_items_in_cache",)

    def __init__(self, max_items_in_cache: int = DEFAULT_MAX_ITEMS_IN_CACHE) -> None:
        super().__init__()
        self.max_items_in_cache: int = max_items_in_cache

    def pop_safe(self, image_path: str) -> ImageCacheEntry | None:
        return self.pop(image_path, None)

    def image_cache_still_fresh(self, image_path: str) -> bool:
        """Returns True when cached image is the same size of the image on disk.
        Not guaranteed to be correct, but that's not important for this case"""
        cached_bytes: int = self[image_path].byte_size if image_path in self else -1
        try:
            return stat(image_path).st_size == cached_bytes
        except (FileNotFoundError, OSError):
            return False

    def update_key(self, old_key: str, new_key: str) -> None:
        """Moves value from old_key to new_key deleting old_key
        If new_key does not exist, nothing happens"""
        target: ImageCacheEntry | None = self.pop_safe(old_key)

        if target is not None:
            self[new_key] = target

    def __setitem__(self, key: str, value: ImageCacheEntry) -> None:
        """Adds check for items in the cache and purges LRU if over limit"""
        if self.max_items_in_cache <= 0:
            return

        if self.__len__() >= self.max_items_in_cache:
            self.popitem(last=False)
        super().__setitem__(key, value)


class ImageName:
    """Full name and suffix of loaded image files"""

    __slots__ = ("name", "suffix")

    def __init__(self, name: str) -> None:
        index: int = name.rfind(".") + 1
        self.suffix: str = name[index:].lower() if index else ""
        self.name: str = name

    def __lt__(self, other: "ImageName") -> bool:
        return OS_name_cmp(self.name, other.name)


# TODO: Break ImageNameList into its own file
class ImageSearchResult(namedtuple("ImageSearchResult", ["index", "found"])):
    """Represents a search such that index is where the image is or would be inserted
    and found is True when a match was found"""

    index: int
    found: bool


class ImageNameList(list[ImageName]):
    """Represents list of ImageName objects with extension methods"""

    __slots__ = ("_display_index",)

    def __init__(self, iterable: Iterable[ImageName]) -> None:
        super().__init__(iterable)
        self._display_index: int = 0

    @property
    def display_index(self) -> int:
        return self._display_index

    def get_current_image(self) -> ImageName:
        return self[self._display_index]

    def get_current_image_name(self) -> str:
        return self[self._display_index].name

    def move_index(self, amount: int) -> None:
        """Moves display_index by the provided amount with wraparound"""
        image_count: int = len(self)
        if image_count > 0:
            self._display_index = (self._display_index + amount) % len(self)

    def sort_and_preserve_index(self, image_to_start_at: str) -> None:
        """Sorts and keeps index at the same image"""
        super().sort()
        self._display_index, _ = self.get_index_of_image(image_to_start_at)

    def remove_current_image(self) -> None:
        """Safely removes current index"""
        try:
            super().pop(self._display_index)
        except IndexError:
            pass

        image_count: int = len(self)

        if self._display_index >= image_count:
            self._display_index = image_count - 1

    def get_index_of_image(self, target_image: str) -> ImageSearchResult:
        """Finds index of target_image.
        If no match found, index returned is where image would be inserted."""
        low: int = 0
        high: int = len(self) - 1
        while low <= high:
            mid: int = (low + high) >> 1
            current_image = self[mid].name
            if target_image == current_image:
                return ImageSearchResult(index=mid, found=True)
            if OS_name_cmp(target_image, current_image):
                high = mid - 1
            else:
                low = mid + 1
        return ImageSearchResult(index=low, found=False)

    def move_index_to_image(self, target_image: str) -> ImageSearchResult:
        search_response: ImageSearchResult = self.get_index_of_image(target_image)
        self._display_index = search_response.index
        return search_response


def magic_number_guess(magic: bytes) -> str:
    """Given bytes, make best guess at file type of image"""
    match magic:
        case b"\x89PNG":
            return ImageFormats.PNG
        case b"RIFF":
            return ImageFormats.WEBP
        case b"GIF8":
            return ImageFormats.GIF
        case b"DDS ":
            return ImageFormats.DDS
        case _:
            return ImageFormats.JPEG
