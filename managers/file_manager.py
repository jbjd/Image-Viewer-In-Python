import os
from re import sub
from typing import Callable

from util.os import OS_name_cmp, get_illegal_OS_char_re, OSFileSortKey
from util.rename import try_convert_file_and_save_new, rename_image
from image_classes import ImagePath, CachedImage

from PIL.Image import Image
from PIL.ImageTk import PhotoImage
from send2trash import send2trash


class ImageFileManager:
    VALID_FILE_TYPES: set[str] = {
        ".png",
        ".jpg",
        ".jpeg",
        ".jfif",
        ".jif",
        ".jpe",
        ".webp",
        ".gif",
        ".bmp",
    }

    __slots__ = (
        "_files",
        "_current_index",
        "image_directory",
        "cache",
        "current_image",
        "path_to_current_image",
    )

    def __init__(self, first_image_to_load: str) -> None:
        """Load single file for display before we load the rest"""
        first_image_to_load = first_image_to_load.replace("\\", "/")
        first_image_data = ImagePath(
            first_image_to_load[first_image_to_load.rfind("/") + 1 :]
        )
        if (
            not os.path.isfile(first_image_to_load)
            or first_image_data.suffix not in self.VALID_FILE_TYPES
        ):
            raise Exception("File not a valid image")

        self.image_directory: str = os.path.dirname(first_image_to_load)
        self._files: list[ImagePath] = [first_image_data]
        self._current_index: int = 0
        self._populate_data_attributes()
        self.cache: dict[str, CachedImage] = {}

    def _populate_data_attributes(self) -> None:
        """Sets variables about current image.
        Should be called when lenth of files changes"""
        self.current_image = self._files[self._current_index]
        self.path_to_current_image = f"{self.image_directory}/{self.current_image.name}"

    def fully_load_images(self) -> None:
        """Init only loads one file, load entire directory here"""
        image_to_start_at: str = self._files[self._current_index].name
        self._files.clear()

        for p in next(os.walk(self.image_directory), (None, None, []))[2]:
            fp = ImagePath(p)
            if fp.suffix in self.VALID_FILE_TYPES:
                self._files.append(fp)

        self._files.sort(key=OSFileSortKey)
        self._current_index = self._binary_search(image_to_start_at)
        self._populate_data_attributes()

    def move_current_index(self, amount: int) -> None:
        self._current_index += amount
        if self._current_index < 0:
            self._current_index = len(self._files) - 1
        elif self._current_index >= len(self._files):
            self._current_index = 0

        self._populate_data_attributes()

    def remove_current_image(self, delete_from_disk: bool) -> int:
        # delete image from files array and from cache if present
        if delete_from_disk:
            send2trash(os.path.abspath(self.path_to_current_image))
        self.cache.pop(self._files.pop(self._current_index).name, None)

        remaining_image_count: int = len(self._files)
        if self._current_index >= remaining_image_count:
            self._current_index = remaining_image_count - 1

        self._populate_data_attributes()

        return remaining_image_count

    def rename_or_convert_current_image(
        self,
        image_to_close: Image,
        new_name: str,
        ask_delete_after_convert: Callable[[str], None],
    ) -> None:
        """try to either rename or convert based on user input.
        ask_delete_after_convert lets user choose to delete old file"""
        new_name = sub(get_illegal_OS_char_re(), "", new_name)
        new_image_data = ImagePath(new_name)
        if new_image_data.suffix not in self.VALID_FILE_TYPES:
            new_name += self.current_image.suffix
            new_image_data = ImagePath(new_name)
        new_path: str = f"{self.image_directory}/{new_name}"
        if (
            new_image_data.suffix != self.current_image.suffix
            and try_convert_file_and_save_new(
                image_to_close,
                self.path_to_current_image,
                self.current_image,
                new_path,
                new_image_data,
            )
        ):
            ask_delete_after_convert(new_image_data.suffix)
            self.add_new_image(new_name)
            return

        rename_image(image_to_close, self.path_to_current_image, new_path)
        self.remove_current_image(delete_from_disk=False)
        self.add_new_image(new_name)
        return

    def add_new_image(self, new_name: str) -> None:
        image_data = ImagePath(new_name)
        self._files.insert(self._binary_search(image_data.name), image_data)
        self._populate_data_attributes()

    def cache_current_image(
        self, width: int, height: int, size, photo_image: PhotoImage, bit_size: int
    ):
        self.cache[self.current_image.name] = CachedImage(
            width,
            height,
            size,
            photo_image,
            bit_size,
        )

    def current_image_cache_still_fresh(self) -> bool:
        return os.path.isfile(self.path_to_current_image) and os.path.getsize(
            self.path_to_current_image
        ) == self.cache.get(self.current_image.name, 0)

    def _binary_search(self, target_image: str) -> int:
        """
        find index of image in the sorted list of all images in the directory
        target_image: name of image file to find
        """
        low: int = 0
        mid: int
        high: int = len(self._files) - 1
        while low <= high:
            mid = (low + high) >> 1
            current_image = self._files[mid].name
            if target_image == current_image:
                return mid
            if OS_name_cmp(target_image, current_image):
                high = mid - 1
            else:
                low = mid + 1
        return low
