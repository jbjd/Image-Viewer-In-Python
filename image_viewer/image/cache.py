"""Classes for caching image data"""

from collections import OrderedDict
from os import stat

from PIL.Image import Image


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

    __slots__ = ("_max_items_in_cache",)

    def __init__(self, max_items_in_cache: int) -> None:
        super().__init__()
        self._max_items_in_cache: int = max(max_items_in_cache, 0)

    @property
    def max_items_in_cache(self) -> int:
        return self._max_items_in_cache

    @max_items_in_cache.setter
    def max_items_in_cache(self, max_items_in_cache: int) -> None:
        """Also removes entries if max shrunk below previous size"""
        self._max_items_in_cache = max(max_items_in_cache, 0)

        while self.__len__() >= max_items_in_cache:
            self.popitem(last=False)

    def pop_safe(self, image_path: str) -> ImageCacheEntry | None:
        return self.pop(image_path, None)

    def image_cache_still_fresh(self, image_path: str) -> bool:
        """Returns True when cached image is the same size of the image on disk.
        Not guaranteed to be correct, but that's not important for this case"""
        if image_path not in self:
            return False

        try:
            return stat(image_path).st_size == self[image_path].byte_size
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
