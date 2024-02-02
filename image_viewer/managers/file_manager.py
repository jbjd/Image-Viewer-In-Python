import os
from tkinter.messagebox import askyesno

from PIL.ImageTk import PhotoImage

from util.convert import try_convert_file_and_save_new
from util.image import CachedImageData, ImagePath
from util.os import OS_name_cmp, clean_str_for_OS_path, walk_dir

if os.name == "nt":
    from send2trash.win.legacy import send2trash
else:
    from send2trash import send2trash


class ImageFileManager:
    """Manages internal list of images"""

    VALID_FILE_TYPES: set[str] = {
        ".gif",
        ".jpg",
        ".jpeg",
        ".jpe",
        ".jfif",
        ".jif",
        ".png",
        ".webp",
    }

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

        if not os.path.isfile(first_image_to_load):
            raise ValueError("File doesn't exist or is a directory")

        first_image_data = ImagePath(os.path.basename(first_image_to_load))
        if first_image_data.suffix not in self.VALID_FILE_TYPES:
            raise ValueError("File extension not supported")

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

        VALID_FILE_TYPES = self.VALID_FILE_TYPES
        self._files = [
            image_path
            for path in walk_dir(self.image_directory)
            if (image_path := ImagePath(path)).suffix in VALID_FILE_TYPES
        ]

        self._files.sort()
        self._current_index = self._binary_search(image_to_start_at)
        self._populate_data_attributes()

    def refresh_image_list(self) -> None:
        """Clears cache and updates internal image list with current
        images in direcrory"""
        self.cache = {}
        self.fully_load_image_data()

    def move_current_index(self, amount: int) -> None:
        """Moves internal index with safe wrap around"""
        self._current_index = (self._current_index + amount) % len(self._files)

        self._populate_data_attributes()

    def _clear_image_data(self) -> None:
        self.cache.pop(self._files.pop(self._current_index).name, None)

    def remove_current_image(self, delete_from_disk: bool) -> None:
        # delete image from files array, cache, and optionally disk
        if delete_from_disk:
            send2trash(os.path.normpath(self.path_to_current_image))
        self._clear_image_data()

        remaining_image_count: int = len(self._files)

        if self._current_index >= remaining_image_count:
            self._current_index = remaining_image_count - 1

        # This needs to be after index check if we catch IndexError and add
        # a new image, we can safely increment index from -1 -> 0
        if remaining_image_count == 0:
            raise IndexError()

        self._populate_data_attributes()

    def _ask_delete_after_convert(self, new_format: str) -> None:
        """Used as callback function for after a succecssful file conversion"""
        if askyesno(
            "Confirm deletion",
            f"Converted file to {new_format}, delete old file?",
        ):
            try:
                self.remove_current_image(True)
            except IndexError:
                pass  # even if no images left, a new one will be added after this

    def rename_or_convert_current_image(self, new_name: str) -> None:
        """Try to either rename or convert based on user input.
        ask_delete_after_convert lets user choose to delete old file"""
        new_name = clean_str_for_OS_path(new_name)
        new_image_data = ImagePath(new_name)
        if new_image_data.suffix not in self.VALID_FILE_TYPES:
            new_name += self.current_image.suffix
            new_image_data = ImagePath(new_name)

        new_path: str = self.construct_path_to_image(new_name)

        if (
            new_image_data.suffix != self.current_image.suffix
            and try_convert_file_and_save_new(
                self.path_to_current_image,
                self.current_image,
                new_path,
                new_image_data,
            )
        ):
            was_last_image: bool = self._current_index == len(self._files) - 1
            self._ask_delete_after_convert(new_image_data.suffix)
            # weird case, previous function can reduce index by one
            # when image was the last file in list due to temp removal
            if was_last_image:
                self._current_index += 1
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
        kb_size: int,
    ) -> None:
        self.cache[self.current_image.name] = CachedImageData(
            width,
            height,
            dimensions,
            photo_image,
            kb_size,
        )

    def current_image_cache_still_fresh(self) -> bool:
        """Returns true when it seems the cached image is still accurate.
        Not guaranteed to be correct, but thats not important for this case"""
        try:
            return (
                os.stat(self.path_to_current_image).st_size
                == self.cache[self.current_image.name].kb_size
            )
        except Exception:
            return False

    def get_current_image_cache(self) -> CachedImageData | None:
        return self.cache.get(self.current_image.name, None)

    def _binary_search(self, target_image: str) -> int:
        """Finds index of target_image in internal list"""
        files = self._files
        low: int = 0
        high: int = len(files) - 1
        while low <= high:
            mid: int = (low + high) >> 1
            current_image = files[mid].name
            if target_image == current_image:
                return mid
            if OS_name_cmp(target_image, current_image):
                high = mid - 1
            else:
                low = mid + 1
        return low
