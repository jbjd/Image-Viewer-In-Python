"""Classes representing metadata of image files and functions for reading them"""

from collections import namedtuple
from typing import Iterable

from constants import ImageFormats
from util.os import os_name_cmp


class ImageName:
    """Full name and suffix of loaded image files"""

    __slots__ = ("name", "suffix")

    def __init__(self, name: str) -> None:
        index: int = name.rfind(".") + 1
        self.suffix: str = name[index:].lower() if index else ""
        self.name: str = name

    def __lt__(self, other: "ImageName") -> bool:
        return os_name_cmp(self.name, other.name)


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
            if os_name_cmp(target_image, current_image):
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
            return (
                ImageFormats.JPEG if magic[:3] == b"\xff\xd8\xff" else ImageFormats.AVIF
            )
