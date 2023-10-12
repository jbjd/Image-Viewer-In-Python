import os
from re import sub

from helpers.os import OS_name_cmp, get_illegal_OS_char_re, OSFileSortKey
from image_classes import ImagePath, CachedImage

from PIL import Image
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
        self.current_image = self._files[self._current_index]
        self.path_to_current_image = f"{self.image_directory}/{self.current_image.name}"

    def fully_load_images(self) -> None:
        image_to_start_at: str = self._files[self._current_index].name
        self._files.clear()

        for p in next(os.walk(self.image_directory), (None, None, []))[2]:
            fp = ImagePath(p)
            if fp.suffix in self.VALID_FILE_TYPES:
                self._files.append(fp)

        self._files.sort(key=OSFileSortKey)
        self._current_index = self.binary_search(image_to_start_at)
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

    def _convert_file_and_save_new(self, image_to_close: Image, new_name: str) -> bool:
        new_image_path: str = f"{self.image_directory}/{new_name}"
        if os.path.isfile(new_image_path) or os.path.isdir(new_image_path):
            raise FileExistsError()

        image_to_close.close()
        with open(self.path_to_current_image, mode="rb") as fp:
            with Image.open(fp) as temp_img:
                new_image_data = ImagePath(new_name)
                # refuse to convert animations for now
                if (
                    getattr(temp_img, "n_frames", 1) > 1
                    and new_image_data.suffix != ".webp"
                ):
                    raise ValueError()

                match new_image_data.suffix:
                    case ".webp":
                        temp_img.save(
                            new_image_path, "WebP", quality=100, method=6, save_all=True
                        )
                    case ".png":
                        temp_img.save(new_image_path, "PNG", optimize=True)
                    case ".bmp":
                        temp_img.save(new_image_path, "BMP")
                    case ".jpg" | ".jpeg" | ".jif" | ".jfif" | ".jpe":
                        # if two different JPEG varients
                        if self.current_image.suffix[1] == "j":
                            return False
                        temp_img.save(
                            new_image_path, "JPEG", optimize=True, quality=100
                        )
                    case _:
                        return False

                fp.flush()

        return True

    def _rename_current_image(self, image_to_close: Image, new_name: str) -> None:
        new_image_path: str = f"{self.image_directory}/{new_name}"
        if os.path.isfile(new_image_path) or os.path.isdir(new_image_path):
            raise FileExistsError()
        image_to_close.close()
        os.rename(self.path_to_current_image, new_image_path)

    def rename_or_convert_current_image(
        self, image_to_close: Image, new_name: str
    ) -> bool:
        new_name = sub(get_illegal_OS_char_re(), "", new_name)
        new_image_data = ImagePath(new_name)
        if new_image_data.suffix != self.current_image.suffix:
            if new_image_data.suffix not in self.VALID_FILE_TYPES:
                new_name += self.current_image.suffix
            elif self._convert_file_and_save_new(image_to_close, new_name):
                self.add_new_image(new_name)
                return True

        self._rename_current_image(image_to_close, new_name)
        self.remove_current_image(delete_from_disk=False)
        self.add_new_image(new_name)
        return False

    def add_new_image(self, new_name: str) -> None:
        image_data = ImagePath(new_name)
        self._files.insert(self.binary_search(image_data.name), image_data)
        self._populate_data_attributes()

    def image_cache_still_fresh(self) -> bool:
        return os.path.isfile(self.path_to_image) and os.path.getsize(
            self.path_to_image
        ) == self.cache.get(self.current_image.name, 0)

    def binary_search(self, target_image: str) -> int:
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
