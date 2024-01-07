import os
from typing import Callable

from PIL.ImageTk import PhotoImage
from send2trash import send2trash

from util.convert import try_convert_file_and_save_new
from util.image import CachedImageData, ImagePath
from util.os import OS_name_cmp, clean_str_for_OS_path


class ImageFileManager:
    """Manages internal list of images"""

    VALID_FILE_TYPES: frozenset[str] = frozenset(
        {
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
    )

    __slots__ = (
        "_current_index",
        "_files",
        "cache",
        "current_image",
        "image_directory",
        "path_to_current_image",
    )

    def __init__(self, first_image_to_load: str) -> None:
        """Load single file for display before we load the rest"""
        first_image_data = ImagePath(os.path.basename(first_image_to_load))

        if not os.path.isfile(first_image_to_load):
            raise ValueError("Could not find file specified")
        if first_image_data.suffix not in self.VALID_FILE_TYPES:
            raise ValueError("File not a valid image")

        self.image_directory: str = os.path.dirname(first_image_to_load)
        self._files: list[ImagePath] = [first_image_data]
        self._current_index: int = 0
        self._populate_data_attributes()
        self.cache: dict[str, CachedImageData] = {}

    def construct_path_to_image(self, image_name: str) -> str:
        return f"{self.image_directory}/{image_name}"

    def _populate_data_attributes(self) -> None:
        """Sets variables about current image.
        Should be called when lenth of files changes"""
        self.current_image = self._files[self._current_index]
        self.path_to_current_image = self.construct_path_to_image(
            self.current_image.name
        )

    def fully_load_image_data(self) -> None:
        """Init only loads one file, load entire directory here"""
        image_to_start_at: str = self._files[self._current_index].name

        self._files = [
            image_path
            for path in next(os.walk(self.image_directory), (None, None, []))[2]
            if (image_path := ImagePath(path)).suffix in self.VALID_FILE_TYPES
        ]

        self._files.sort()
        self._current_index = self._binary_search(image_to_start_at)
        self._populate_data_attributes()

    def refresh_image_list(self) -> None:
        """Clears cache and updates internal image list with current
        images in direcrory"""
        self.cache.clear()
        self.fully_load_image_data()

    def move_current_index(self, amount: int) -> None:
        self._current_index = (self._current_index + amount) % len(self._files)

        self._populate_data_attributes()

    def _clear_image_data(self) -> None:
        self.cache.pop(self._files.pop(self._current_index).name, None)

    def remove_current_image(self, delete_from_disk: bool) -> None:
        # delete image from files array, cache, and optionally disk
        if delete_from_disk:
            send2trash(os.path.abspath(self.path_to_current_image))
        self._clear_image_data()

        remaining_image_count: int = len(self._files)
        if remaining_image_count == 0:
            raise IndexError()

        if self._current_index >= remaining_image_count:
            self._current_index = remaining_image_count - 1

        self._populate_data_attributes()

    def rename_or_convert_current_image(
        self,
        new_name: str,
        ask_delete_after_convert: Callable[[str], None],
    ) -> None:
        """try to either rename or convert based on user input.
        ask_delete_after_convert lets user choose to delete old file"""
        new_name = clean_str_for_OS_path(new_name)
        new_image_data = ImagePath(new_name)
        if new_image_data.suffix not in self.VALID_FILE_TYPES:
            new_name += self.current_image.suffix
            new_image_data = ImagePath(new_name)

        new_path: str = self.construct_path_to_image(new_name)

        if os.path.isfile(new_path) or os.path.isdir(new_path):
            raise FileExistsError()

        if (
            new_image_data.suffix != self.current_image.suffix
            and try_convert_file_and_save_new(
                self.path_to_current_image,
                self.current_image,
                new_path,
                new_image_data,
            )
        ):
            ask_delete_after_convert(new_image_data.suffix)
        else:
            os.rename(self.path_to_current_image, new_path)
            self._clear_image_data()
        self.add_new_image(new_name)

    def add_new_image(self, new_name: str) -> None:
        """Adds new image to internal list and updates attributes"""
        image_data = ImagePath(new_name)
        self._files.insert(self._binary_search(image_data.name), image_data)
        self._populate_data_attributes()

    def cache_image(
        self,
        width: int,
        height: int,
        dimensions: str,
        photo_image: PhotoImage,
        bit_size: int,
    ) -> None:
        self.cache[self.current_image.name] = CachedImageData(
            width,
            height,
            dimensions,
            photo_image,
            bit_size,
        )

    def get_current_image_cache(self) -> CachedImageData:
        return self.cache[self.current_image.name]

    def current_image_cache_still_fresh(self) -> bool:
        """Returns true when we think the cached image is still accurate.
        Not guaranteed to be correct, but thats not important for this case"""
        return os.path.isfile(self.path_to_current_image) and os.path.getsize(
            self.path_to_current_image
        ) == self.cache.get(self.current_image.name, 0)

    def get_cached_image_data(self) -> CachedImageData | None:
        return self.cache.get(self.current_image.name, None)

    def _binary_search(self, target_image: str) -> int:
        """Finds index of image in the sorted list of all images in the directory.
        target_image: name of image file to find"""
        low: int = 0
        high: int = len(self._files) - 1
        while low <= high:
            mid: int = (low + high) >> 1
            current_image = self._files[mid].name
            if target_image == current_image:
                return mid
            if OS_name_cmp(target_image, current_image):
                high = mid - 1
            else:
                low = mid + 1
        return low
